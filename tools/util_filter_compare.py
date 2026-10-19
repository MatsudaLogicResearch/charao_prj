#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###############################################################################
# This file is part of charao.
#
# Copyright (C) 2025-2026 MATSUDA Masahiro
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
###############################################################################
"""util_filter_compare.py — compare の出力 CSV を when 一致の点だけで読み直す

【目的】
util_compare_csv.py が出す compare_*.csv には、orig に when が無く charao が when を
付けている点 (ISS-00233 のフォールバックで対応付けた点) が混ざっている。
orig の 1 本の arc に charao の複数 arc が対応しているだけで、同じ条件どうしの比較では
ないため、その差をそのまま charao の誤差として読んではいけない。

本ツールは when_mismatch 列が空の点 (= orig と charao の when が完全一致) だけを残し、
差の分布と最悪点を出し直す。これが「本当の誤差」になる (ISS-00335 の手順 (1)(2))。

【入力】
compare_*.csv (util_compare_csv.py の --out_csv 出力)
  列: cell_name, pin, related_pin, when, when_new, when_mismatch, timing_type,
      kind, index1 (ns), index2 (pF), value_orig, value_new, abs_diff
  ※ abs_diff 列は名前に反して符号付きの差 (value_new - value_orig)。本ツールは
     絶対値を取り直して使う。

【出力】
  (1) カバレッジ  : 全点 / when 一致点 / 割合 (kind 別と合計)
  (2) 差の分布    : |差| のビン別件数。timing (ns) と power (pJ) を別表で出す
  (3) 最悪点      : kind 別の |差| 最大の点を、orig 実値と併記して 1 行で出す
  (4) 上位明細    : |差| 上位 N 点の明細 (--top、既定 20)

平均・中央値などの集約統計と、比 (%, 倍率) は出さない。判定は ns / pJ の絶対値と
orig 実値の併記で行う (docs/prompts.md の確定ルール)。

【使い方】
  nice -n 19 python3 tools/util_filter_compare.py \\
      --csv compare_cmp_gf_20260911.csv --when_match_only

  # セル・kind で絞り、結果をファイルにも残す
  nice -n 19 python3 tools/util_filter_compare.py \\
      --csv compare_cmp_sky_20260914.csv --when_match_only \\
      --cell sky130_fd_sc_hd__dfrtp_2 --kind cell_rise \\
      --top 50 --out tmp/filter_sky_dfrtp_2.txt
"""

import argparse
import csv
import sys

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

# kind の系統。単位もビン境界も系統ごとに違う。
POWER_KINDS = ("rise_power", "fall_power")          # 単位 pJ
LEAKAGE_KINDS = ("leakage",)                        # 単位 uW
# 上記以外は timing 系 (単位 ns)

# |差| のビン境界。timing / power は charao_prj.md の 2026-09-18 分布表と
# 直接比べられる区切り。leakage は値そのものが 1e-6〜1e-4 uW のオーダーなので
# 4 桁下げた区切りを使う (同じ境界だと全点が最小ビンに入って判別できない)。
BINS = (0.001, 0.01, 0.1, 0.5)
BIN_LABELS = ("<= 0.001", "0.001-0.01", "0.01-0.1", "0.1-0.5", "> 0.5")
LEAK_BINS = (1e-8, 1e-7, 1e-6, 1e-5)
LEAK_BIN_LABELS = ("<= 1e-8", "1e-8-1e-7", "1e-7-1e-6", "1e-6-1e-5", "> 1e-5")

# const の判定基準 (2026-05-14 ダーマツ判断、STA の set_clock_uncertainty が絶対値指定)
CONST_CRITERION_NS = 0.1


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description="compare の出力 CSV を when 一致の点だけで集計し直す",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", required=True, action="append", metavar="FILE",
                    help="compare_*.csv (複数指定可)")
    ap.add_argument("--when_match_only", action="store_true",
                    help="when_mismatch が空の点だけを対象にする (本当の誤差)")
    ap.add_argument("--cell", metavar="NAME", action="append",
                    help="対象セル名 (完全一致、複数指定可)")
    ap.add_argument("--kind", metavar="KIND", action="append",
                    help="対象 kind (cell_rise 等、複数指定可)")
    ap.add_argument("--top", type=int, default=20, metavar="N",
                    help="|差| 上位 N 点の明細を出す (既定 20、0 で抑止)")
    ap.add_argument("--out", metavar="FILE",
                    help="標準出力と同じ内容をこのファイルにも書く")
    return ap.parse_args(argv)


def bins_of(kind):
    """kind の系統に応じた (境界, ラベル) を返す"""
    if kind in LEAKAGE_KINDS:
        return LEAK_BINS, LEAK_BIN_LABELS
    return BINS, BIN_LABELS


def bin_index(adiff, kind):
    """|差| がどのビンに入るかを返す"""
    edges, _ = bins_of(kind)
    for i, edge in enumerate(edges):
        if adiff <= edge:
            return i
    return len(edges)


def scan(paths, when_match_only, cells, kinds, top_n):
    """CSV を逐次読み、集計値と上位点だけを保持して返す

    317MB 級の CSV を想定するため、行は貯めずにその場で畳む。
    """
    cell_set = set(cells) if cells else None
    kind_set = set(kinds) if kinds else None

    stat = {}      # kind -> dict(total, mismatch, used, bins, worst)
    top = []       # 上位候補 (adiff, row) を貯める。定期的に刈り込む
    n_read = 0
    n_bad = 0

    for path in paths:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                n_read += 1
                kind = row["kind"]
                if kind_set is not None and kind not in kind_set:
                    continue
                if cell_set is not None and row["cell_name"] not in cell_set:
                    continue

                st = stat.setdefault(kind, {"total": 0, "mismatch": 0, "used": 0,
                                            "bins": [0] * (len(BINS) + 1),
                                            "over_criterion": 0, "worst": None})
                st["total"] += 1
                mismatched = row["when_mismatch"].strip() != ""
                if mismatched:
                    st["mismatch"] += 1
                    if when_match_only:
                        continue

                try:
                    diff = float(row["abs_diff"])
                except (TypeError, ValueError):
                    n_bad += 1
                    continue
                adiff = abs(diff)

                st["used"] += 1
                st["bins"][bin_index(adiff, kind)] += 1
                if adiff > CONST_CRITERION_NS:
                    st["over_criterion"] += 1
                if st["worst"] is None or adiff > st["worst"][0]:
                    st["worst"] = (adiff, row)

                if top_n > 0:
                    top.append((adiff, row))
                    if len(top) > top_n * 20:
                        top.sort(key=lambda t: t[0], reverse=True)
                        del top[top_n:]

    top.sort(key=lambda t: t[0], reverse=True)
    del top[top_n:]
    return stat, top, n_read, n_bad


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

class Tee:
    """標準出力と (指定があれば) ファイルの両方へ書く"""

    def __init__(self, path=None):
        self.fp = open(path, "w", encoding="utf-8") if path else None

    def __call__(self, line=""):
        print(line)
        if self.fp:
            self.fp.write(line + "\n")

    def close(self):
        if self.fp:
            self.fp.close()


def unit_of(kind):
    if kind in POWER_KINDS:
        return "pJ"
    if kind in LEAKAGE_KINDS:
        return "uW"
    return "ns"


def fmt_val_u(s, kind):
    """値を系統に応じた桁で整形する (leakage は 1e-6 オーダーなので指数表記)"""
    try:
        v = float(s)
    except (TypeError, ValueError):
        return str(s)
    return "{:.4e}".format(v) if kind in LEAKAGE_KINDS else "{:.4f}".format(v)


def fmt_point(row):
    """1 点を orig 実値・when の両側付きで整形する

    when は orig 側 (when 列) と charao 側 (when_new 列) を必ず併記する。
    when_mismatch が立っている点は「orig の 1 arc に charao の複数 arc が対応している」
    点で、同じ条件どうしの比較ではない。それを明細で見分けられるようにするため。
    """
    kind = row["kind"]
    diff = float(row["abs_diff"])
    u = unit_of(kind)
    mism = row["when_mismatch"].strip() != ""
    if row.get("collapse", "") == "max":
        judge = "max で畳み (候補 {})".format(row.get("n_cands", "?"))
    elif mism:
        judge = "when 違い"
    else:
        judge = "when 一致"
    dfmt = "{:+.4e}" if kind in LEAKAGE_KINDS else "{:+.4f}"
    vmin = row.get("value_new_min", "")
    return ("    cell={cell} pin={pin} rel={rel}\n"
            "      when: orig={when} / charao={when_new}  [{judge}]{minpart}\n"
            "      timing_type={tt} index1={i1} ns index2={i2} pF"
            "  orig={vo} {u} / charao={vn} {u} / 差={d} {u}").format(
        cell=row["cell_name"], pin=row["pin"], rel=row["related_pin"],
        when=(row["when"] or "(なし)"), when_new=(row["when_new"] or "(なし)"),
        judge=judge,
        minpart=("  charao の最小 when 値={}".format(fmt_val_u(vmin, kind)) if vmin else ""),
        tt=(row.get("timing_type") or "-"), i1=row["index1 (ns)"], i2=row["index2 (pF)"],
        vo=fmt_val_u(row["value_orig"], kind), vn=fmt_val_u(row["value_new"], kind),
        d=dfmt.format(diff), u=u)


def _fmt_val(s):
    try:
        return "{:.4f}".format(float(s))
    except (TypeError, ValueError):
        return str(s)


def report(out, args, stat, top, n_read, n_bad):
    out("=" * 100)
    out("util_filter_compare — compare 出力 CSV の再集計")
    out("=" * 100)
    for p in args.csv:
        out("  入力 : {}".format(p))
    out("  条件 : when 一致のみ={}  cell={}  kind={}".format(
        "はい" if args.when_match_only else "いいえ (全点)",
        ",".join(args.cell) if args.cell else "(全セル)",
        ",".join(args.kind) if args.kind else "(全 kind)"))
    out("  読込 : {} 行{}".format(
        n_read, "  (数値として読めず除外 {} 行)".format(n_bad) if n_bad else ""))
    out()

    # ---- (1) カバレッジ ----
    out("-" * 100)
    out("(1) カバレッジ — when が完全一致した点だけが同じ条件どうしの比較")
    out("-" * 100)
    out("  {:<22} {:>12} {:>14} {:>14} {:>10}".format(
        "kind", "全点", "when 違い", "when 一致", "一致割合"))
    t_all = t_mis = 0
    for kind in sorted(stat):
        st = stat[kind]
        match = st["total"] - st["mismatch"]
        t_all += st["total"]
        t_mis += st["mismatch"]
        out("  {:<22} {:>12,} {:>14,} {:>14,} {:>9.1f}%".format(
            kind, st["total"], st["mismatch"], match,
            100.0 * match / st["total"] if st["total"] else 0.0))
    out("  {:<22} {:>12,} {:>14,} {:>14,} {:>9.1f}%".format(
        "合計", t_all, t_mis, t_all - t_mis,
        100.0 * (t_all - t_mis) / t_all if t_all else 0.0))
    out()

    # ---- (2) 差の分布 ----
    def _row(label, bins, over):
        cells = "".join("{:>13,}".format(v) for v in bins)
        tail = "{:>14,}".format(over) if over is not None else ""
        return "  {:<22}{}{}".format(label, cells, tail)

    for title, kinds, labels, unit, show_crit in (
            ("timing (ns)",
             [k for k in sorted(stat)
              if k not in POWER_KINDS and k not in LEAKAGE_KINDS],
             BIN_LABELS, "ns", True),
            ("power (pJ)",
             [k for k in sorted(stat) if k in POWER_KINDS],
             BIN_LABELS, "pJ", False),
            ("leakage (uW)",
             [k for k in sorted(stat) if k in LEAKAGE_KINDS],
             LEAK_BIN_LABELS, "uW", False)):
        if not kinds:
            continue
        out("-" * 100)
        out("(2) |差| の分布 — {}".format(title))
        out("-" * 100)
        hdr = "".join("{:>13}".format(s) for s in labels)
        out("  {:<22}{}{}".format(
            "kind", hdr, "{:>14}".format("|差|>0.1 の数") if show_crit else ""))
        tot = [0] * len(labels)
        tot_over = 0
        for kind in kinds:
            st = stat[kind]
            out(_row(kind, st["bins"], st["over_criterion"] if show_crit else None))
            for i, v in enumerate(st["bins"]):
                tot[i] += v
            tot_over += st["over_criterion"]
        out(_row("小計", tot, tot_over if show_crit else None))
        if show_crit:
            out("  ※ 単位は {}。const (rise/fall_constraint) の判定基準は"
                "絶対値 {} ns".format(unit, CONST_CRITERION_NS))
        else:
            out("  ※ 単位は {}".format(unit))
        out()

    # ---- (3) kind 別の最悪点 ----
    out("-" * 100)
    out("(3) kind 別の最悪点 (|差| 最大) — orig 実値を併記")
    out("-" * 100)
    for kind in sorted(stat):
        st = stat[kind]
        if st["worst"] is None:
            continue
        out("  [{}]  |差| {:.4f} {}".format(kind, st["worst"][0], unit_of(kind)))
        out(fmt_point(st["worst"][1]))
    out()

    # ---- (4) 上位明細 ----
    if args.top > 0 and top:
        out("-" * 100)
        out("(4) |差| 上位 {} 点の明細".format(min(args.top, len(top))))
        out("-" * 100)
        for i, (adiff, row) in enumerate(top, 1):
            out("  #{:<3} [{}]  |差| {:.4f} {}".format(
                i, row["kind"], adiff, unit_of(row["kind"])))
            out(fmt_point(row))
        out()


# ---------------------------------------------------------------------------
# Process
# ---------------------------------------------------------------------------

def main(argv=None):
    args = parse_args(argv)
    stat, top, n_read, n_bad = scan(
        args.csv, args.when_match_only, args.cell, args.kind, args.top)
    if not stat:
        print("[ERROR] 対象となる行がありません (フィルタ条件を確認してください)",
              file=sys.stderr)
        return 1
    out = Tee(args.out)
    try:
        report(out, args, stat, top, n_read, n_bad)
    finally:
        out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
