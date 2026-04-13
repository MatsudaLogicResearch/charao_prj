#!/usr/bin/env python3
"""
compare_lib_csv.py — extract_lib_csv.py 生成 CSV 同士の比較レポート

【使い方】

# 基本：オリジナル vs 新 .lib（同一コーナー）の比較
python -m charao.script.compare_lib_csv --orig <orig_dir> --new <new_dir>

# セル単位で絞る
python -m charao.script.compare_lib_csv --orig <orig_dir> --new <new_dir> --cell gf180mcu_fd_sc_mcu7t5v0__inv_1

# per-point 比較 CSV も出力する
python -m charao.script.compare_lib_csv --orig <orig_dir> --new <new_dir> --out_csv diff.csv

【入力】
  extract_lib_csv.py で生成された 2 ディレクトリ（timing.csv / power.csv を含む）

【比較方法】
  新側の 2D グリッド（index1_ns × index2_pF）を numpy.interp を index2→index1 の
  順に 2 回適用して bilinear 補間し、オリジナル格子点で評価。
  比率 = new / orig を table_type / rise_fall 単位で統計化する。

【出力】
  標準出力：table_type / rise_fall ごとに n, ratio mean/median/min/max, std
  --out_csv 指定時：cell, pin, related_pin, kind, index1_ns, index2_pF,
                   value_orig, value_new, ratio, abs_diff の per-point CSV
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

from charao.script.extract_lib_csv import (
    COL_INDEX1, COL_INDEX2, COL_TIMING_VALUE, COL_POWER_VALUE,
)


# ── CSV 読み込み ──────────────────────────────────────────────────────────

def _load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _group(rows, group_keys, value_key):
    """行を group_keys でグループ化し (index1, index2, value) のリストを保持。"""
    g = defaultdict(list)
    for r in rows:
        key = tuple(r[k] for k in group_keys)
        try:
            i1 = float(r[COL_INDEX1])
            i2 = float(r[COL_INDEX2])
            v = float(r[value_key])
        except (ValueError, KeyError):
            continue
        g[key].append((i1, i2, v))
    return g


def _to_grid(triples):
    """(i1,i2,v) のリストを (xs, ys, grid) の 2D 配列に変換。"""
    xs = sorted({t[0] for t in triples})
    ys = sorted({t[1] for t in triples})
    xi = {v: i for i, v in enumerate(xs)}
    yi = {v: i for i, v in enumerate(ys)}
    grid = np.full((len(xs), len(ys)), np.nan)
    for i1, i2, v in triples:
        grid[xi[i1], yi[i2]] = v
    return np.array(xs), np.array(ys), grid


def _bilinear(xs, ys, grid, x, y):
    """grid 上で (x, y) の値を bilinear 補間。範囲外は端点にクリップされる (np.interp 既定)。"""
    row_at_y = np.array([np.interp(y, ys, grid[i]) for i in range(len(xs))])
    return float(np.interp(x, xs, row_at_y))


# ── 統計計算 ──────────────────────────────────────────────────────────────

def _stat_line(label, ratios, diffs, n):
    r = np.array(ratios)
    d = np.array(diffs)
    return (f"  {label:28s} n={n:4d}  "
            f"ratio mean={r.mean():.4f} median={np.median(r):.4f} "
            f"min={r.min():.4f} max={r.max():.4f} std={r.std():.4f}  "
            f"|diff| max={np.abs(d).max():.3e}")


def _compare_section(orig_rows, new_rows, kind_key, value_key, cell_filter):
    """kind_key（table_type or rise_fall）単位で比較統計を出力。"""
    group_keys = ["cell_name", "pin", "related_pin", kind_key]
    og = _group(orig_rows, group_keys, value_key)
    ng = _group(new_rows, group_keys, value_key)

    per_kind = defaultdict(lambda: {"ratio": [], "diff": []})
    per_point = []
    missing_groups = 0

    for key, o_triples in og.items():
        cell, pin, rpin, kind = key
        if cell_filter and cell != cell_filter:
            continue
        n_triples = ng.get(key)
        if not n_triples:
            missing_groups += 1
            continue
        xs, ys, grid = _to_grid(n_triples)
        if len(xs) < 2 or len(ys) < 2:
            continue
        for i1, i2, vo in o_triples:
            vn = _bilinear(xs, ys, grid, i1, i2)
            if not np.isfinite(vn) or vo == 0:
                continue
            r = vn / vo
            d = vn - vo
            per_kind[kind]["ratio"].append(r)
            per_kind[kind]["diff"].append(d)
            per_point.append({
                "cell_name": cell, "pin": pin, "related_pin": rpin,
                "kind": kind, COL_INDEX1: i1, COL_INDEX2: i2,
                "value_orig": vo, "value_new": vn,
                "ratio": r, "abs_diff": d,
            })

    for kind in sorted(per_kind):
        s = per_kind[kind]
        print(_stat_line(kind, s["ratio"], s["diff"], len(s["ratio"])))
    if missing_groups:
        print(f"  (note: {missing_groups} group(s) missing in new side — skipped)")
    return per_point


# ── メイン ────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="extract_lib_csv.py 生成 CSV を比較してレポートする")
    ap.add_argument("--orig", required=True, metavar="DIR",
                    help="オリジナル側 CSV ディレクトリ")
    ap.add_argument("--new", required=True, metavar="DIR",
                    help="新側 CSV ディレクトリ（charao 出力など）")
    ap.add_argument("--cell", metavar="NAME",
                    help="比較対象セルを 1 つに絞る（省略時は全セル）")
    ap.add_argument("--out_csv", metavar="FILE",
                    help="per-point 比較 CSV の出力先")
    args = ap.parse_args()

    orig = Path(args.orig).resolve()
    new  = Path(args.new).resolve()
    print(f"Orig : {orig}")
    print(f"New  : {new}")
    if args.cell:
        print(f"Cell : {args.cell}")
    print()

    rows_out = []

    for fn, kind_key, value_key, label in [
        ("timing.csv", "table_type", COL_TIMING_VALUE, "=== timing ==="),
        ("power.csv",  "rise_fall",  COL_POWER_VALUE,  "=== power ==="),
    ]:
        op = orig / fn
        np_ = new / fn
        if not (op.exists() and np_.exists()):
            print(f"{label}  (skip: missing {fn})")
            continue
        print(label)
        o_rows = _load_csv(op)
        n_rows = _load_csv(np_)
        rows_out += _compare_section(o_rows, n_rows, kind_key, value_key, args.cell)
        print()

    if args.out_csv and rows_out:
        out_path = Path(args.out_csv).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
            w.writeheader()
            w.writerows(rows_out)
        print(f"per-point CSV : {out_path} ({len(rows_out):,} rows)")


if __name__ == "__main__":
    main()
