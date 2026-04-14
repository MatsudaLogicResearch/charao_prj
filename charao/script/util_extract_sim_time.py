#!/usr/bin/env python3
"""
util_extract_sim_time.py — work/ 配下の ngspice .lis から SIM 実行時間を抽出して CSV 化

【使い方】

# デフォルト：./work 配下の全 .lis を走査 → ./rslt/sim_time.csv
python -m charao.script.util_extract_sim_time

# 任意の work ディレクトリ / 出力先を指定
python -m charao.script.util_extract_sim_time --work <dir> --out <file>

【入力ファイル名の前提】
  vt_<vdd>_<temp>_<cell>_<index_no>_<measure>_oir=<oirc>_arc=<arc>[_<load>_<slope>][_energy1|_energy2|_leakage].sp.lis

  例：
    vt_5.0_25.0_gf180mcu_fd_sc_mcu7t5v0__inv_1_0_delay_oir=o0i0i0_arc=frr_0.001_0.02.sp.lis
    vt_5.0_25.0_gf180mcu_fd_sc_mcu7t5v0__inv_1_0_delay_oir=o0i0i0_arc=frr_0.001_0.02_energy1.sp.lis
    vt_5.0_25.0_gf180mcu_fd_sc_mcu7t5v0__inv_1_2_leakage_oir=o0i0i0_arc=sss_leakage.sp.lis

【出力 CSV 列】
  cell, index_no, measure, arc, oirc,
  index1_slope_ns, index2_load_pF,
  sim_time_s, data_rows, autostop, autostop_time_s, errors, file
"""

import argparse
import csv
import re
from pathlib import Path


# ── ファイル名パーサー ────────────────────────────────────────────────────

_FNAME_RE = re.compile(
    r"^vt_(?P<vdd>[\d.]+)_(?P<temp>[\d.]+)_(?P<cell>.+?)"
    r"_(?P<idx>\d+)_(?P<meas>delay|leakage)"
    r"_oir=(?P<oirc>[^_]+)_arc=(?P<arc>[a-z]+)"
    r"(?:_(?P<load>[\d.]+)_(?P<slope>[\d.]+))?"
    r"(?:_(?P<suf>energy1|energy2|leakage))?"
    r"\.sp\.lis$"
)


def parse_filename(name):
    m = _FNAME_RE.match(name)
    if not m:
        return None
    d = m.groupdict()
    # measure: suffix (energy1/energy2) を優先、それ以外は meas
    if d["suf"] in ("energy1", "energy2"):
        measure = d["suf"]
    else:
        measure = d["meas"]
    return {
        "cell":             d["cell"],
        "index_no":         d["idx"],
        "measure":          measure,
        "arc":              d["arc"],
        "oirc":             d["oirc"],
        "index1_slope_ns":  d["slope"] or "",
        "index2_load_pF":   d["load"]  or "",
    }


# ── .lis 解析 ─────────────────────────────────────────────────────────────

_RE_TIME     = re.compile(r"Total analysis time \(seconds\)\s*=\s*([\d.eE+-]+)")
_RE_ROWS     = re.compile(r"No\. of Data Rows\s*:\s*(\d+)")
_RE_AUTOSTOP = re.compile(r"Autostop after\s+([\d.eE+-]+)\s*s")
_RE_ERROR    = re.compile(r"^\s*(Error:|.*\bout of interval\b|.*\bfailed!)")


def parse_lis(path):
    sim_time = ""
    data_rows = ""
    autostop = "0"
    autostop_t = ""
    errors = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if (m := _RE_TIME.search(line)):
                sim_time = m.group(1)
                continue
            if (m := _RE_ROWS.search(line)):
                data_rows = m.group(1)
                continue
            if (m := _RE_AUTOSTOP.search(line)):
                autostop = "1"
                autostop_t = m.group(1)
                continue
            if _RE_ERROR.search(line):
                errors += 1
    return {
        "sim_time_s":      sim_time,
        "data_rows":       data_rows,
        "autostop":        autostop,
        "autostop_time_s": autostop_t,
        "errors":          str(errors),
    }


# ── メイン ────────────────────────────────────────────────────────────────

_FIELDS = [
    "cell", "index_no", "measure", "arc", "oirc",
    "index1_slope_ns", "index2_load_pF",
    "sim_time_s", "data_rows", "autostop", "autostop_time_s", "errors",
    "file",
]


def main():
    ap = argparse.ArgumentParser(
        description="work/*.lis から SIM 時間を抽出して CSV 化する")
    ap.add_argument("--work", default="work", metavar="DIR",
                    help="work ディレクトリ（デフォルト: ./work）")
    ap.add_argument("--out",  default="rslt/sim_time.csv", metavar="FILE",
                    help="出力 CSV パス（デフォルト: ./rslt/sim_time.csv）")
    args = ap.parse_args()

    work = Path(args.work).resolve()
    out  = Path(args.out).resolve()
    if not work.is_dir():
        print(f"ERROR: work ディレクトリが見つかりません: {work}")
        return

    lis_files = sorted(work.rglob("*.sp.lis"))
    print(f"Work  : {work}")
    print(f"Found : {len(lis_files)} .lis files")
    print(f"Out   : {out}")

    rows = []
    skipped = 0
    for p in lis_files:
        info = parse_filename(p.name)
        if info is None:
            skipped += 1
            continue
        info.update(parse_lis(p))
        info["file"] = str(p.relative_to(work))
        rows.append(info)

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_FIELDS)
        w.writeheader()
        w.writerows(rows)

    # 簡易サマリを標準出力へ
    times = [float(r["sim_time_s"]) for r in rows if r["sim_time_s"]]
    err_total = sum(int(r["errors"]) for r in rows)
    print(f"\nParsed : {len(rows)} rows  (skipped filename mismatch: {skipped})")
    if times:
        print(f"sim_time_s : min={min(times):.4f} median={sorted(times)[len(times)//2]:.4f} "
              f"max={max(times):.4f} sum={sum(times):.2f}")
        print(f"  over 1s  : {sum(1 for t in times if t > 1)}")
        print(f"  over 10s : {sum(1 for t in times if t > 10)}")
        print(f"  over 60s : {sum(1 for t in times if t > 60)}")
    print(f"errors total : {err_total}")


if __name__ == "__main__":
    main()
