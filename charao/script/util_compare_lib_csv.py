#!/usr/bin/env python3
"""
util_compare_lib_csv.py — util_extract_lib_csv.py 生成 CSV 同士の per-point 比較

【使い方】

# 基本：オリジナル vs 新 .lib（同一コーナー）の比較
python -m charao.script.util_compare_lib_csv --orig <orig_dir> --new <new_dir>

# セル単位で絞る
python -m charao.script.util_compare_lib_csv --orig <orig_dir> --new <new_dir> --cell gf180mcu_fd_sc_mcu7t5v0__inv_1

# 出力先を指定
python -m charao.script.util_compare_lib_csv --orig <orig_dir> --new <new_dir> --out_csv diff.csv

【入力】
  extract_lib_csv.py で生成された 2 ディレクトリ（timing.csv / power.csv を含む）

【比較方法】
  両 CSV の (cell, pin, related_pin, kind, index1, index2) を厳密一致で突き合わせ、
  各格子点ごとに value_orig / value_new / abs_diff を出力する。
  集約統計（mean/median 等）は出さない（格子点ごとに条件が異なるため無意味なため）。
  charao の未実行 index は 0.0 で出力されるので、新側の value==0 はデフォルトで除外する。

【出力】
  標準出力：マッチしたグループ数・ポイント数の要約のみ
  CSV：cell_name, pin, related_pin, kind, index1 (ns), index2 (pF),
       value_orig, value_new, abs_diff
       （デフォルト出力先：./compare_result.csv）
"""

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

from bisect import bisect_right

from charao.script.util_extract_lib_csv import (
    COL_INDEX1, COL_INDEX2, COL_TIMING_VALUE, COL_POWER_VALUE,
)


_log_lines: list[str] = []


def _log(*args, **kwargs):
    """Print to stdout and also buffer the line for summary file output."""
    line = " ".join(str(a) for a in args)
    print(line, **kwargs)
    _log_lines.append(line)


# ── CSV 読み込み ──────────────────────────────────────────────────────────

def _load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _group(rows, group_keys, value_key, kind_key,
           drop_zero=False, drop_default_when=False):
    """行を group_keys でグループ化し (index1, index2, value) のリストを保持。

    drop_zero=True: value が 0.0 の行を除外する（charao の未実行 index は 0.0 で
    出力されるため、コーナーのみ実行した結果と比較するときに使用）。

    drop_default_when=True: 同じ `(cell, pin, related_pin, kind)` に sensitization
    付き（when!=""）のエントリが存在する場合のみ、そのグループの default（when==""）
    を除外する。INV など default しか持たないセルは default を残す。
    """
    # Step 1: (cell, pin, related_pin, kind) ごとに sensitization 付きが存在するか判定
    arc_has_sensitized = set()
    if drop_default_when:
        for r in rows:
            if r.get("when", "") != "":
                arc_has_sensitized.add((r["cell_name"], r["pin"], r["related_pin"], r[kind_key]))

    # Step 2: 実際にグルーピング
    g = defaultdict(list)
    for r in rows:
        if drop_default_when and r.get("when", "") == "":
            arc_id = (r["cell_name"], r["pin"], r["related_pin"], r[kind_key])
            if arc_id in arc_has_sensitized:
                continue  # sensitization 付きが別途あるので default は捨てる
        key = tuple(r[k] for k in group_keys)
        try:
            i1 = float(r[COL_INDEX1])
            i2 = float(r[COL_INDEX2])
            v = float(r[value_key])
        except (ValueError, KeyError):
            continue
        if drop_zero and v == 0.0:
            continue
        g[key].append((i1, i2, v))
    return g


# ── 2D bilinear 補間（線形外挿付き）─────────────────────────────────────

def _build_table_2d(triples):
    """(i1, i2, value) リストから (sorted_i1, sorted_i2, 2d_dict) を構築。
    同一 (i1, i2) に複数値がある場合は平均をとる。"""
    pts = defaultdict(list)
    for i1, i2, v in triples:
        pts[(i1, i2)].append(v)
    i1_list = sorted({k[0] for k in pts})
    i2_list = sorted({k[1] for k in pts})
    table = {}
    for (a, b), vs in pts.items():
        table[(a, b)] = sum(vs) / len(vs)
    return i1_list, i2_list, table


def _interp1d_extrap(x, xp, fp):
    """1D 線形補間 + 線形外挿。xp は昇順リスト、fp は同長リスト。"""
    n = len(xp)
    if n == 0:
        return None
    if n == 1:
        return fp[0]
    if x <= xp[0]:
        slope = (fp[1] - fp[0]) / (xp[1] - xp[0]) if xp[1] != xp[0] else 0.0
        return fp[0] + slope * (x - xp[0])
    if x >= xp[-1]:
        slope = (fp[-1] - fp[-2]) / (xp[-1] - xp[-2]) if xp[-1] != xp[-2] else 0.0
        return fp[-1] + slope * (x - xp[-1])
    idx = bisect_right(xp, x) - 1
    idx = max(0, min(idx, n - 2))
    dx = xp[idx + 1] - xp[idx]
    if dx == 0:
        return fp[idx]
    t = (x - xp[idx]) / dx
    return fp[idx] * (1 - t) + fp[idx + 1] * t


def _interp2d(qi1, qi2, i1_list, i2_list, table):
    """2D bilinear 補間 + 線形外挿。table は {(i1,i2): value} dict。
    i1 方向で 2 本のスライスを i2 補間し、結果を i1 方向で補間。"""
    n1 = len(i1_list)
    n2 = len(i2_list)
    if n1 < 1 or n2 < 1:
        return None
    if n1 == 1:
        fp = [table.get((i1_list[0], b)) for b in i2_list]
        if any(v is None for v in fp):
            return None
        return _interp1d_extrap(qi2, i2_list, fp)
    if n2 == 1:
        fp = [table.get((a, i2_list[0])) for a in i1_list]
        if any(v is None for v in fp):
            return None
        return _interp1d_extrap(qi1, i1_list, fp)
    # i1 方向のブラケット
    if qi1 <= i1_list[0]:
        j = 0
    elif qi1 >= i1_list[-1]:
        j = n1 - 2
    else:
        j = bisect_right(i1_list, qi1) - 1
        j = max(0, min(j, n1 - 2))
    # j と j+1 の 2 スライスを i2 方向で補間
    fp_lo = [table.get((i1_list[j], b)) for b in i2_list]
    fp_hi = [table.get((i1_list[j + 1], b)) for b in i2_list]
    if any(v is None for v in fp_lo) or any(v is None for v in fp_hi):
        return None
    v_lo = _interp1d_extrap(qi2, i2_list, fp_lo)
    v_hi = _interp1d_extrap(qi2, i2_list, fp_hi)
    dx = i1_list[j + 1] - i1_list[j]
    if dx == 0:
        return v_lo
    t = (qi1 - i1_list[j]) / dx
    return v_lo * (1 - t) + v_hi * t


def _compare_section(orig_rows, new_rows, kind_key, value_key, cell_filter,
                     drop_zero_new, drop_default_when, interpolate=False):
    """(cell, pin, related_pin, when, kind, index1, index2) 単位で per-point 比較。
    各点の (orig, new, abs_diff) をリストで返す。

    charao が既存セルの点と同じ (index1, index2) を出力していることを前提に、
    新側の value==0 を drop すれば、新側と原側で同じ格子点が厳密一致で比較できる。
    orig 側の `when==""`（sensitization なし summary block）はデフォルトで除外。
    """
    group_keys = ["cell_name", "pin", "related_pin", "when", kind_key]
    og = _group(orig_rows, group_keys, value_key, kind_key,
                drop_default_when=drop_default_when)
    ng = _group(new_rows, group_keys, value_key, kind_key,
                drop_zero=drop_zero_new, drop_default_when=drop_default_when)

    per_point = []
    matched_groups = 0
    missing_groups = 0
    matched_points = 0

    for key, o_triples in og.items():
        cell, pin, rpin, when, kind = key
        if cell_filter and cell != cell_filter:
            continue
        n_triples = ng.get(key)
        if not n_triples:
            missing_groups += 1
            continue
        matched_groups += 1

        if interpolate:
            i1_arr, i2_arr, table = _build_table_2d(n_triples)
            for i1, i2, vo in o_triples:
                vn = _interp2d(i1, i2, i1_arr, i2_arr, table)
                if vn is None:
                    continue
                matched_points += 1
                per_point.append({
                    "cell_name": cell, "pin": pin, "related_pin": rpin,
                    "when": when, "kind": kind, COL_INDEX1: i1, COL_INDEX2: i2,
                    "value_orig": vo, "value_new": vn,
                    "abs_diff": vn - vo,
                })
        else:
            n_by_idx = {(i1, i2): v for i1, i2, v in n_triples}
            for i1, i2, vo in o_triples:
                vn = n_by_idx.get((i1, i2))
                if vn is None:
                    continue
                matched_points += 1
                per_point.append({
                    "cell_name": cell, "pin": pin, "related_pin": rpin,
                    "when": when, "kind": kind, COL_INDEX1: i1, COL_INDEX2: i2,
                    "value_orig": vo, "value_new": vn,
                    "abs_diff": vn - vo,
                })

    _log(f"  matched groups : {matched_groups}")
    _log(f"  missing groups : {missing_groups} (new side not found)")
    _log(f"  matched points : {matched_points}")

    # ── (kind, index1, index2) ごとの diff 統計を表示 ──
    buckets = defaultdict(list)
    for r in per_point:
        key = (r["kind"], r[COL_INDEX1], r[COL_INDEX2])
        buckets[key].append(r["abs_diff"])

    if buckets:
        _log("")
        header = (f"  {'kind':18s}  {'index1(ns)':>10s}  {'index2(pF)':>10s}  "
                  f"{'n':>4s}  "
                  f"{'diff avg':>10s} {'diff sigma':>11s} {'diff min':>10s} {'diff max':>10s}")
        _log(header)
        for key in sorted(buckets.keys()):
            kind, i1, i2 = key
            ds = buckets[key]
            n = len(ds)
            avg = sum(ds) / n
            var = sum((v - avg) ** 2 for v in ds) / n
            sigma = math.sqrt(var)
            _log(f"  {kind:18s}  {i1:>10.4g}  {i2:>10.4g}  {n:>4d}  "
                 f"{avg:>+10.4f} {sigma:>11.4f} {min(ds):>+10.4f} {max(ds):>+10.4f}")
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
    ap.add_argument("--out_csv", metavar="FILE", default="compare_result.csv",
                    help="per-point 比較 CSV の出力先（デフォルト：./compare_result.csv）")
    ap.add_argument("--keep_zero_new", action="store_true",
                    help="新側の value==0 の行も含める（デフォルトは除外）。"
                         "charao が未実行 index を 0.0 で出力するためデフォルトで除外する。")
    ap.add_argument("--keep_default_when", action="store_true",
                    help="同一アークに sensitization 付き（when!=\"\"）が存在する場合の"
                         "default block（when==\"\"）も比較対象に含める（デフォルトは除外）。"
                         "INV などのように default しか持たないセルは常に保持される。"
                         "モダン STA（OpenSTA / PrimeTime / Tempus）では sensitization "
                         "完全網羅があれば default block は不要。")
    ap.add_argument("--interpolate", action="store_true",
                    help="新側テーブルを 2D bilinear 補間（線形外挿）して orig 側の全"
                         " (index1, index2) 点で比較する。orig/new で load グリッドが"
                         "異なる場合（charao テンプレートが orig と不一致のとき）に使用。")
    args = ap.parse_args()

    orig = Path(args.orig).resolve()
    new  = Path(args.new).resolve()
    _log(f"Orig : {orig}")
    _log(f"New  : {new}")
    if args.cell:
        _log(f"Cell : {args.cell}")
    if args.interpolate:
        _log(f"Mode : interpolate (2D bilinear + linear extrapolation)")
    _log("")

    rows_out = []

    for fn, kind_key, value_key, label in [
        ("timing.csv", "table_type", COL_TIMING_VALUE, "=== timing ==="),
        ("power.csv",  "rise_fall",  COL_POWER_VALUE,  "=== power ==="),
    ]:
        op = orig / fn
        np_ = new / fn
        if not (op.exists() and np_.exists()):
            _log(f"{label}  (skip: missing {fn})")
            continue
        _log(label)
        o_rows = _load_csv(op)
        n_rows = _load_csv(np_)
        rows_out += _compare_section(
            o_rows, n_rows, kind_key, value_key, args.cell,
            drop_zero_new=(not args.keep_zero_new),
            drop_default_when=(not args.keep_default_when),
            interpolate=args.interpolate,
        )
        _log("")

    if args.out_csv and rows_out:
        out_path = Path(args.out_csv).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
            w.writeheader()
            w.writerows(rows_out)
        _log(f"per-point CSV : {out_path} ({len(rows_out):,} rows)")

        sum_path = out_path.with_suffix(".summary.txt")
        with open(sum_path, "w", encoding="utf-8") as f:
            f.write("\n".join(_log_lines) + "\n")
        print(f"summary file  : {sum_path}")


if __name__ == "__main__":
    main()
