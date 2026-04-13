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

【単位の正規化】
  .lib ヘッダの time_unit / voltage_unit / current_unit / leakage_power_unit /
  capacitive_load_unit / energy_unit を読み取り、CSV 出力値はすべて以下の
  canonical 単位に正規化される（`UNITS_IN_CSV` が単一情報源）。

    時間       → ns
    容量       → pF
    電圧       → V
    電流       → mA
    leakage    → uW
    energy     → pJ

  energy_unit が未宣言の .lib では energy = voltage_unit × current_unit × time_unit
  から推定する（例：1V × 1mA × 1ns = 1pJ）。

  実行時に `units_in_lib`（.lib の生宣言）と `units_in_csv`（CSV の canonical 単位）
  を標準出力に表示する。

【出力 CSV（列名に括弧付き単位）】
  leakage.csv : cell_name, leakage_power (uW), when
  power.csv   : cell_name, pin, related_pin, rise_fall, index1 (ns), index2 (pF), value (pJ)
  timing.csv  : cell_name, pin, related_pin, table_type, index1 (ns), index2 (pF), value (ns)

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


# ── 単位スキャン／正規化 ──────────────────────────────────────────────────

_SI_PREFIX = {
    "f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6,
    "m": 1e-3, "": 1.0, "k": 1e3, "M": 1e6,
}

# canonical 単位（CSV 出力の単位を SI 絶対値で表したもの）
_CANONICAL_SI = {
    "time_unit":            1e-9,   # ns
    "capacitive_load_unit": 1e-12,  # pF
    "voltage_unit":         1.0,    # V
    "current_unit":         1e-3,   # mA
    "leakage_power_unit":   1e-6,   # uW
    "energy_unit":          1e-12,  # pJ
}

# CSV の canonical 単位を文字列で表した参照（列名・表示の単一情報源）
UNITS_IN_CSV = {
    "time_unit":            "1ns",
    "capacitive_load_unit": "1pF",
    "voltage_unit":         "1V",
    "current_unit":         "1mA",
    "leakage_power_unit":   "1uW",
    "energy_unit":          "1pJ",
}

# CSV 列名の括弧付き単位表記（"1ns" → "ns" を抽出）
_U_TIME    = UNITS_IN_CSV["time_unit"][1:]
_U_CAP     = UNITS_IN_CSV["capacitive_load_unit"][1:]
_U_LEAK    = UNITS_IN_CSV["leakage_power_unit"][1:]
_U_ENERGY  = UNITS_IN_CSV["energy_unit"][1:]

COL_INDEX1       = f"index1 ({_U_TIME})"
COL_INDEX2       = f"index2 ({_U_CAP})"
COL_TIMING_VALUE = f"value ({_U_TIME})"
COL_POWER_VALUE  = f"value ({_U_ENERGY})"
COL_LEAKAGE      = f"leakage_power ({_U_LEAK})"


def _parse_si(s, base):
    """"1ns" / "1pF" / "1mA" など単一宣言を SI 絶対値に変換。base は末尾文字（'s','F','A','V','W','J'）。"""
    s = s.strip().strip('"').strip()
    m = re.match(r"([\d.]+)\s*([a-zA-Zµ]*)$", s)
    if not m:
        return None
    mag = float(m.group(1))
    unit = m.group(2)
    if not unit or unit[-1:].lower() != base.lower():
        return None
    prefix = unit[:-1]
    if prefix and prefix not in _SI_PREFIX:
        # 大文字小文字の揺れ吸収（"M"は mega のまま、"ohm" 等は別扱い）
        prefix = prefix.lower() if prefix.lower() in _SI_PREFIX else prefix
    return mag * _SI_PREFIX.get(prefix, 1.0)


def _scan_units(content):
    """.lib 本文から単位宣言を抽出し、{key: {'raw': '1ns', 'si': 1e-9}} を返す。"""
    units = {}
    for key, base in [
        ("time_unit",          "s"),
        ("voltage_unit",       "V"),
        ("current_unit",       "A"),
        ("leakage_power_unit", "W"),
        ("energy_unit",        "J"),
    ]:
        m = re.search(rf'{key}\s*:\s*"?([^";\n]+?)"?\s*;', content)
        if m:
            raw = m.group(1).strip().strip('"').strip()
            si = _parse_si(raw, base)
            if si is not None:
                units[key] = {"raw": raw, "si": si}
    # capacitive_load_unit (1, pF);   ← 独自構文
    m = re.search(r"capacitive_load_unit\s*\(\s*([\d.]+)\s*,\s*([a-zA-Z]+)\s*\)", content)
    if m:
        mag = float(m.group(1))
        unit = m.group(2)
        if unit[-1:].lower() == "f":
            prefix = unit[:-1]
            si = mag * _SI_PREFIX.get(prefix.lower(), 1.0)
            raw = f"{int(mag) if mag == int(mag) else mag}{unit[:-1]}F"
            units["capacitive_load_unit"] = {"raw": raw, "si": si}
    return units


def _si_of(units, key, default):
    return units[key]["si"] if key in units else default


def _canonical_scales(units):
    """.lib 生値に掛けると CSV canonical 単位（ns / pF / uW / pJ）になる係数を返す。"""
    s = {}
    s["time_scale"]    = _si_of(units, "time_unit",           _CANONICAL_SI["time_unit"])           / _CANONICAL_SI["time_unit"]
    s["cap_scale"]     = _si_of(units, "capacitive_load_unit", _CANONICAL_SI["capacitive_load_unit"]) / _CANONICAL_SI["capacitive_load_unit"]
    s["leakage_scale"] = _si_of(units, "leakage_power_unit",  _CANONICAL_SI["leakage_power_unit"])  / _CANONICAL_SI["leakage_power_unit"]
    if "energy_unit" in units:
        e_si = units["energy_unit"]["si"]
    else:
        # energy = V × I × t から推定
        e_si = (_si_of(units, "voltage_unit", _CANONICAL_SI["voltage_unit"])
                * _si_of(units, "current_unit", _CANONICAL_SI["current_unit"])
                * _si_of(units, "time_unit",    _CANONICAL_SI["time_unit"]))
    s["energy_scale"] = e_si / _CANONICAL_SI["energy_unit"]
    return s


def _units_in_lib_str(units):
    """units dict を 'time=1ns, cap=1pF, ...' 形式の一行文字列に。"""
    order = [
        ("time",    "time_unit"),
        ("cap",     "capacitive_load_unit"),
        ("voltage", "voltage_unit"),
        ("current", "current_unit"),
        ("leakage", "leakage_power_unit"),
        ("energy",  "energy_unit"),
    ]
    parts = []
    for label, key in order:
        if key in units:
            parts.append(f"{label}={units[key]['raw']}")
        elif key == "energy_unit":
            parts.append("energy=(derived from V×A×s)")
    return ", ".join(parts)


# ── Liberty パーサー本体 ──────────────────────────────────────────────────

class LibertyParser:
    """Liberty .lib ファイルの行リストを受け取り 3 種の CSV 行リストを返すパーサー。"""

    def __init__(self, lines, scales):
        self.lines = lines
        self.n = len(lines)
        self.i = 0
        self.s = scales
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

    def _emit_table(self, index1, index2, values_flat, template, dest, value_key, value_scale):
        ni2 = len(index2)
        ts = self.s["time_scale"]
        cs = self.s["cap_scale"]
        for ri, i1 in enumerate(index1):
            for ci, i2 in enumerate(index2):
                idx = ri * ni2 + ci
                if idx < len(values_flat):
                    row = dict(template)
                    try:
                        row[COL_INDEX1] = float(i1) * ts
                        row[COL_INDEX2] = float(i2) * cs
                        row[value_key]  = float(values_flat[idx]) * value_scale
                    except ValueError:
                        row[COL_INDEX1] = i1
                        row[COL_INDEX2] = i2
                        row[value_key]  = values_flat[idx]
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
            try:
                v = float(value) * self.s["leakage_scale"]
            except ValueError:
                v = value
            self.leakage_rows.append({
                "cell_name": cell_name,
                COL_LEAKAGE: v,
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
                                 self.power_rows, COL_POWER_VALUE,
                                 self.s["energy_scale"])
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
                                 self.timing_rows, COL_TIMING_VALUE,
                                 self.s["time_scale"])
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
    units = _scan_units(content)
    scales = _canonical_scales(units)
    leakage, power, timing = LibertyParser(content.splitlines(), scales).parse()
    return units, scales, leakage, power, timing


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"    {path.name}: {len(rows):,} rows")


_CSV_UNITS_LINE = (
    f"time={UNITS_IN_CSV['time_unit']}, "
    f"cap={UNITS_IN_CSV['capacitive_load_unit']}, "
    f"voltage={UNITS_IN_CSV['voltage_unit']}, "
    f"current={UNITS_IN_CSV['current_unit']}, "
    f"leakage={UNITS_IN_CSV['leakage_power_unit']}, "
    f"energy={UNITS_IN_CSV['energy_unit']}"
)


def extract_to_dir(lib_path, out_dir):
    """1つの .lib を解析して out_dir に 3 CSV を書き出す。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    units, scales, leakage, power, timing = parse_lib_file(lib_path)
    print(f"    units_in_lib : {_units_in_lib_str(units)}")
    print(f"    units_in_csv : {_CSV_UNITS_LINE}")
    write_csv(out_dir / "leakage.csv",
              ["cell_name", COL_LEAKAGE, "when"], leakage)
    write_csv(out_dir / "power.csv",
              ["cell_name", "pin", "related_pin", "rise_fall",
               COL_INDEX1, COL_INDEX2, COL_POWER_VALUE], power)
    write_csv(out_dir / "timing.csv",
              ["cell_name", "pin", "related_pin", "table_type",
               COL_INDEX1, COL_INDEX2, COL_TIMING_VALUE], timing)


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
