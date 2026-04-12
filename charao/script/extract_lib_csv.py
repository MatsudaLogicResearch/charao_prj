#!/usr/bin/env python3
"""
extract_lib_csv.py — Liberty .lib から leakage.csv / power.csv / timing.csv を抽出

【使い方】

# ① GF180 参照 .lib（全コーナー）→ デフォルトパスへ出力
python -m charao.script.extract_lib_csv

# ② 任意の .lib ディレクトリ → 任意の出力先（コーナーごとにサブディレクトリ）
python -m charao.script.extract_lib_csv --lib_dir <dir> --out_dir <dir>

# ③ charao 出力など単一 .lib → 指定ディレクトリへ直接出力（サブディレクトリなし）
python -m charao.script.extract_lib_csv --lib <file.lib> --out <dir>

【出力 CSV】
  leakage.csv : cell_name, leakage_power_uW, when
  power.csv   : cell_name, pin, related_pin, rise_fall, index1_ns, index2_pF, value_fJ
  timing.csv  : cell_name, pin, related_pin, table_type, index1_ns, index2_pF, value

【比較方針】
  charao 出力 .lib との比較は本スクリプトで両者を CSV 化し、CSV 同士で比較すること。
  (.lib を直接パースしない / numpy.interp で index 補間)
"""

import argparse
import re
import csv
from pathlib import Path

# デフォルトパス（GF180 参照 .lib）
_SCRIPT_DIR = Path(__file__).resolve().parent          # charao/script/
_REPO_ROOT   = _SCRIPT_DIR.parent.parent               # charao_prj/
DEFAULT_LIB_DIR = (_REPO_ROOT
                   / "sample" / "src" / "gf180mcuC"
                   / "libs.ref" / "gf180mcu_fd_sc_mcu7t5v0" / "lib")
DEFAULT_OUT_DIR = (_REPO_ROOT
                   / "tmp" / "gf180_fd_mcuC7t20240817")


class LibertyParser:
    """Liberty .lib ファイルの行リストを受け取り 3 種の CSV 行リストを返すパーサー。"""

    def __init__(self, lines):
        self.lines = lines
        self.n = len(lines)
        self.i = 0
        self.leakage_rows = []
        self.power_rows = []
        self.timing_rows = []

    # ── 基本操作 ───────────────────────────���──────────────────────────────

    def peek(self):
        return self.lines[self.i].strip() if self.i < self.n else ""

    def advance(self):
        line = self.lines[self.i].strip() if self.i < self.n else ""
        self.i += 1
        return line

    def collect_values(self, first_line):
        """values("...",\\ 形式の複数行を収集してフラットなリストを返す。"""
        parts = [first_line]
        while parts[-1].rstrip().endswith("\\"):
            parts.append(self.advance())
        joined = " ".join(parts)
        m = re.search(r'values\s*\((.*?)\)\s*;', joined, re.DOTALL)
        if not m:
            return []
        raw = m.group(1).replace('"', "").replace("\\", "")
        return [v.strip() for v in raw.split(",") if v.strip()]

    @staticmethod
    def parse_index(line, num):
        m = re.match(rf'index_{num}\s*\("([^"]*)"\)', line)
        return [v.strip() for v in m.group(1).split(",")] if m else []

    def _emit_table(self, index1, index2, values_flat, template, dest, value_key):
        ni2 = len(index2)
        for ri, i1 in enumerate(index1):
            for ci, i2 in enumerate(index2):
                idx = ri * ni2 + ci
                if idx < len(values_flat):
                    row = dict(template)
                    row["index1_ns"] = i1
                    row["index2_pF"] = i2
                    row[value_key] = values_flat[idx]
                    dest.append(row)

    # ── ブロックパーサー ──────────────────────────────────────────���───────

    def parse_2d_table(self):
        """index_1 / index_2 / values ブロックを解析。(index1, index2, values_flat) を返す。"""
        index1 = []
        index2 = []
        values_flat = []
        while self.i < self.n:
            line = self.advance()
            if re.match(r'index_1\s*\(', line):
                index1 = self.parse_index(line, 1)
            elif re.match(r'index_2\s*\(', line):
                index2 = self.parse_index(line, 2)
            elif re.match(r'values\s*\(', line):
                values_flat = self.collect_values(line)
            elif "}" in line and "{" not in line:
                break
        return index1, index2, values_flat

    def parse_leakage_power(self, cell_name):
        when = ""
        value = None
        while self.i < self.n:
            line = self.advance()
            m = re.search(r'when\s*:\s*"([^"]*)"', line)
            if m:
                when = m.group(1)
            m = re.search(r'value\s*:\s*"?([^";\s]+)"?\s*;', line)
            if m:
                value = m.group(1)
            if "}" in line and "{" not in line:
                break
        if value is not None:
            self.leakage_rows.append({
                "cell_name": cell_name,
                "leakage_power_uW": value,
                "when": when,
            })

    def parse_internal_power(self, cell_name, pin_name):
        related_pin = None
        while self.i < self.n:
            line = self.peek()
            m = re.match(r'(fall_power|rise_power)\s*\(\S+\)\s*\{', line)
            if m:
                pt_type = m.group(1)
                self.advance()
                i1, i2, vals = self.parse_2d_table()
                self._emit_table(i1, i2, vals,
                                 {"cell_name": cell_name, "pin": pin_name,
                                  "related_pin": related_pin, "rise_fall": pt_type},
                                 self.power_rows, "value_fJ")
                continue
            line = self.advance()
            m = re.search(r'related_pin\s*:\s*"([^"]*)"', line)
            if m:
                related_pin = m.group(1)
            if "}" in line and "{" not in line:
                break

    def parse_timing(self, cell_name, pin_name):
        related_pin = None
        timing_tables = {"cell_rise", "cell_fall", "rise_transition", "fall_transition"}
        while self.i < self.n:
            line = self.peek()
            m = re.match(r'(\w+)\s*\(\S+\)\s*\{', line)
            if m and m.group(1) in timing_tables:
                tt_type = m.group(1)
                self.advance()
                i1, i2, vals = self.parse_2d_table()
                self._emit_table(i1, i2, vals,
                                 {"cell_name": cell_name, "pin": pin_name,
                                  "related_pin": related_pin, "table_type": tt_type},
                                 self.timing_rows, "value")
                continue
            line = self.advance()
            m = re.search(r'related_pin\s*:\s*"([^"]*)"', line)
            if m:
                related_pin = m.group(1)
            if "}" in line and "{" not in line:
                break

    def parse_pin(self, cell_name, pin_name):
        depth = 1
        while self.i < self.n:
            line = self.peek()
            if re.match(r'internal_power\s*\(\)\s*\{', line):
                self.advance()
                self.parse_internal_power(cell_name, pin_name)
                continue
            if re.match(r'timing\s*\(\)\s*\{', line):
                self.advance()
                self.parse_timing(cell_name, pin_name)
                continue
            line = self.advance()
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                break

    def parse_cell(self, cell_name):
        depth = 1
        while self.i < self.n:
            line = self.peek()
            if re.match(r'leakage_power\s*\(\)\s*\{', line):
                self.advance()
                self.parse_leakage_power(cell_name)
                continue
            m = re.match(r'pin\s*\((\S+)\)\s*\{', line)
            if m:
                self.advance()
                self.parse_pin(cell_name, m.group(1))
                continue
            line = self.advance()
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                break

    def parse(self):
        """ライブラリ全体を解析。(leakage_rows, power_rows, timing_rows) を返す。"""
        while self.i < self.n:
            line = self.peek()
            m = re.match(r'cell\s*\((\S+)\)\s*\{', line)
            if m:
                self.advance()
                self.parse_cell(m.group(1))
                continue
            self.advance()
        return self.leakage_rows, self.power_rows, self.timing_rows


# ── ユーティリティ ────────────────────────��────────────────────────────────

def parse_lib_file(lib_path):
    content = lib_path.read_text(encoding="utf-8")
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    return LibertyParser(content.splitlines()).parse()


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"    {path.name}: {len(rows):,} rows")


def extract_to_dir(lib_path, out_dir):
    """1つの .lib を解析して out_dir に 3 CSV を書き出す。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    leakage, power, timing = parse_lib_file(lib_path)
    write_csv(out_dir / "leakage.csv",
              ["cell_name", "leakage_power_uW", "when"], leakage)
    write_csv(out_dir / "power.csv",
              ["cell_name", "pin", "related_pin", "rise_fall",
               "index1_ns", "index2_pF", "value_fJ"], power)
    write_csv(out_dir / "timing.csv",
              ["cell_name", "pin", "related_pin", "table_type",
               "index1_ns", "index2_pF", "value"], timing)


# ── メイン ──────────────────────────��──────────────────────────────────���──

def main():
    parser = argparse.ArgumentParser(
        description="Liberty .lib から leakage / power / timing CSV を抽出する")
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--lib", metavar="FILE",
                     help="単一 .lib ファイルを指定（charao 出力など）")
    grp.add_argument("--lib_dir", metavar="DIR",
                     help="複数 .lib が入ったディレクトリ（コーナー一括処理）")
    parser.add_argument("--out", metavar="DIR",
                        help="--lib 使用時の出力先ディレクトリ（省略時は .lib と同じ場所）")
    parser.add_argument("--out_dir", metavar="DIR",
                        help="--lib_dir 使用時の出力先ルート（省略時はデフォルト）")
    args = parser.parse_args()

    if args.lib:
        # ── 単一 .lib モード ────────���─────────────────────────────────
        lib_path = Path(args.lib).resolve()
        out_dir  = Path(args.out).resolve() if args.out else lib_path.parent
        print(f"Source : {lib_path}")
        print(f"Output : {out_dir}\n")
        extract_to_dir(lib_path, out_dir)

    else:
        # ── ディレクトリ一括モード ────────────────────────────────────
        lib_dir = Path(args.lib_dir).resolve() if args.lib_dir else DEFAULT_LIB_DIR
        out_dir = Path(args.out_dir).resolve() if args.out_dir else DEFAULT_OUT_DIR
        lib_files = sorted(lib_dir.glob("*.lib"))
        if not lib_files:
            print(f"ERROR: .lib が見つかりません: {lib_dir}")
            return
        print(f"Source : {lib_dir}")
        print(f"Output : {out_dir}")
        print(f"Corners: {len(lib_files)}\n")
        for lib_path in lib_files:
            corner = lib_path.stem.split("__")[-1]
            print(f"[{corner}]")
            extract_to_dir(lib_path, out_dir / corner)

    print("\nDone.")


if __name__ == "__main__":
    main()
