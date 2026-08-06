#!/usr/bin/env python3
"""
util_extract_lib2csv.py — Liberty .lib から leakage.csv / power.csv / timing.csv を抽出

【使い方】

# ① GF180 参照 .lib（全コーナー）→ デフォルトパスへ出力
python -m charao.script.util_extract_lib2csv

# ② 任意の .lib ディレクトリ → 任意の出力先（コーナーごとにサブディレクトリ）
python -m charao.script.util_extract_lib2csv --lib_dir <dir> --out_dir <dir>

# ③ charao 出力など単一 .lib → 指定ディレクトリへ直接出力（サブディレクトリなし）
python -m charao.script.util_extract_lib2csv --lib <file.lib> --out <dir>

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
  timing.csv  : cell_name, pin, related_pin, when, timing_type, table_type,
                index1 (ns), index2 (pF), value (ns)
                * timing_type は Liberty の arc 種別（rising_edge / setup_rising 等、 comb は空文字列）
                * table_type はその中の table 種別（cell_rise / fall_constraint 等）
                * 1D table  : index2 = "NaN"
                * scalar    : index1 = index2 = "NaN"

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


from charao.script.util_liberty import (
    parse_lib_file, UNITS_IN_CSV, _units_in_lib_str,
    COL_INDEX1, COL_INDEX2, COL_TIMING_VALUE, COL_POWER_VALUE, COL_LEAKAGE,
)


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
              ["cell_name", "pin", "related_pin", "when", "rise_fall",
               COL_INDEX1, COL_INDEX2, COL_POWER_VALUE], power)
    write_csv(out_dir / "timing.csv",
              ["cell_name", "pin", "related_pin", "when", "timing_type", "table_type",
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
