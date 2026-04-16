#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
util_make_templates_from_origin.py — orig .lib から config_lib.jsonc の templates セクションを再生成

【目的】
オリジナル .lib に出現する全 index_2 グリッドを「全 10 点が許容範囲（デフォルト ±5%）
以内」でクラスタリングし、代表値を d000, d001, ... として config_lib.jsonc の
templates セクションに書き出す。これにより charao の per-cell 割り当て後（util_assign_templates）
が orig と全 index 点で精度よく一致するようになる。

【使い方】

# orig CSV を入力（推奨・高速）
python -m charao.script.util_make_templates_from_origin \\
    --orig_csv tmp/gf180_fd_mcuC7t20240817/tt_025C_5v00 \\
    --config sample/target/gf180/fd/mcuC7t20240817/config_lib.jsonc

# orig .lib 直接
python -m charao.script.util_make_templates_from_origin \\
    --orig_lib sample/src/.../gf180mcu_fd_sc_mcu7t5v0__tt_025C_5v00.lib \\
    --config sample/target/gf180/fd/mcuC7t20240817/config_lib.jsonc

# 別ファイルへ出力（in-place しない）
python -m charao.script.util_make_templates_from_origin --output new_config.jsonc ...

# 書き換えずレポートのみ
python -m charao.script.util_make_templates_from_origin --dry_run ...

# 許容を変える（デフォルト 0.05 = 5%）
python -m charao.script.util_make_templates_from_origin --tolerance 0.03 ...

【動作仕様】
1. orig 側から (cell, pin, related_pin, when, table_type) ごとに index_2 リストを収集
2. 同一セル・同一アークでは同じグリッドのはずなので unique 化
3. 全 unique グリッドを max 昇順でソートし、greedy first-fit クラスタリング：
   各グリッドについて既存クラスタの代表値と全 10 点を比較、全点が tolerance 内なら
   そのクラスタに追加、なければ新クラスタを作成
4. クラスタの代表値（最初のメンバー）を d000, d001, ... として命名
5. 既存 config_lib.jsonc の templates セクションのうち kind=delay/power/passive のみを
   再生成（leakage/const は既存維持）
6. 結果を `--output` または in-place（`.bak` バックアップ後）に書き出し

注意：
- 既存の `index_1` は維持（slope は cell common なので変わらない想定）
- d?? の名前が変わるため、`util_assign_templates` を実行して std_*.jsonc の割り当てを
  更新する必要がある
- 10 点 grid 以外（addf/addh など 19 点や multi-grid セル）はスキップして警告
"""

import argparse
import csv
import re
import shutil
from collections import defaultdict
from pathlib import Path

from charao.script.util_extract_lib_csv import parse_lib_file


# ── orig grid 収集 ────────────────────────────────────────────────────────

def _collect_grids_from_csv(csv_dir):
    """timing.csv から (cell, pin, related_pin, when, table_type) ごとに
    index_2 リストを収集する。同一キーでは unique 化。"""
    p = Path(csv_dir) / "timing.csv"
    if not p.exists():
        raise FileNotFoundError(f"timing.csv not found in {csv_dir}")
    arc_grids = defaultdict(set)
    with open(p, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        i2_col = next((c for c in reader.fieldnames if c.startswith("index2")), None)
        if i2_col is None:
            raise ValueError(f"index2 column not found in {p}")
        for r in reader:
            try:
                i2 = float(r[i2_col])
            except (ValueError, KeyError):
                continue
            key = (r["cell_name"], r["pin"], r["related_pin"], r["when"], r["table_type"])
            arc_grids[key].add(i2)
    # convert to sorted tuples
    return {k: tuple(sorted(s)) for k, s in arc_grids.items()}


def _collect_grids_from_lib(lib_path):
    """orig .lib を直接パースして同形式の dict を返す。"""
    _u, _s, _l, _p, timing = parse_lib_file(Path(lib_path))
    arc_grids = defaultdict(set)
    for r in timing:
        i2_key = next((k for k in r if k.startswith("index2")), None)
        if i2_key is None:
            continue
        try:
            i2 = float(r[i2_key])
        except (ValueError, TypeError):
            continue
        key = (r["cell_name"], r["pin"], r["related_pin"], r.get("when", ""), r["table_type"])
        arc_grids[key].add(i2)
    return {k: tuple(sorted(s)) for k, s in arc_grids.items()}


# ── クラスタリング ───────────────────────────────────────────────────────

def cluster_grids(grids, tolerance, expected_len=10):
    """grids: 全 unique な index_2 タプルのコレクション。

    expected_len 以外の長さは別バケットに分けず、対象外として返す。
    全 expected_len 点が tolerance 内のグリッドを greedy first-fit で同一クラスタにまとめる。
    返値: (clusters, skipped)
      clusters: [(representative_tuple, [member_tuples])]  (max 昇順)
      skipped : [grid_tuple]  (length mismatch)
    """
    valid = []
    skipped = []
    for g in grids:
        if len(g) == expected_len:
            valid.append(g)
        else:
            skipped.append(g)

    valid_unique = sorted(set(valid), key=lambda x: max(x))

    clusters = []  # list of (rep, [members])
    for g in valid_unique:
        placed = False
        for rep, members in clusters:
            if all(abs(a / b - 1.0) <= tolerance for a, b in zip(g, rep) if b != 0):
                members.append(g)
                placed = True
                break
        if not placed:
            clusters.append((g, [g]))
    return clusters, skipped


# ── 既存 config_lib.jsonc 解析 ────────────────────────────────────────────

def _find_templates_section(text):
    """templates 配列の中身（[ から ] まで）の (start, end) インデックスを返す。"""
    m = re.search(r'"templates"\s*:\s*\[', text)
    if not m:
        raise ValueError('"templates" section not found in config')
    start = m.end()
    depth = 1
    i = start
    n = len(text)
    while i < n:
        c = text[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return start, i
        i += 1
    raise ValueError('"templates" section not closed')


def _parse_existing_templates(text):
    """既存 templates の中から index_1（共通）と非 delay/power エントリを取得。"""
    inner = text
    # index_1 は delay 系の最初のもの（共通の想定）
    m = re.search(
        r'"kind"\s*:\s*"delay"[^{]*?"index_1"\s*:\s*\[([^\]]*)\]',
        inner,
    )
    index_1 = []
    if m:
        index_1 = [v.strip() for v in m.group(1).split(",") if v.strip()]

    # 非 delay/power のエントリ全体を保持
    non_dp = []
    for m in re.finditer(
        r'\{\s*"kind"\s*:\s*"(?P<kind>[^"]+)"[^{}]*?\}',
        inner,
    ):
        if m.group("kind") not in ("delay", "power"):
            non_dp.append(m.group(0))
    return index_1, non_dp


# ── 新 templates セクション生成 ───────────────────────────────────────────

def _format_floats(vals, fmt="{:g}"):
    return ",".join(fmt.format(float(v)) if not isinstance(v, str) else v for v in vals)


def _build_templates_section(clusters, index_1, non_dp_entries, indent="    "):
    """新しい templates セクション本体（[...] の中身）を組み立てる。"""
    name_width = max(3, len(str(len(clusters) - 1)))
    fmt = f"d{{:0{name_width}d}}"

    lines = ["\n"]

    # 既存の non-delay/power エントリを先頭に保持（leakage/passive/const）
    if non_dp_entries:
        for i, e in enumerate(non_dp_entries):
            prefix = "" if i == 0 else "   ,"
            lines.append(f"{indent}{prefix}{e}\n")
        lines.append("\n")

    # delay 群
    lines.append(f"{indent}//---- delay: {len(clusters)} groups\n")
    i1_str = _format_floats(index_1)
    for idx, (rep, members) in enumerate(clusters):
        i2_str = _format_floats(rep)
        prefix = "    " if idx == 0 and not non_dp_entries else "   ,"
        name = fmt.format(idx)
        lines.append(
            f'{indent}{prefix}{{"kind":"delay","grid":"10x10","name":"{name}",'
            f'"index_1":[{i1_str}],"index_2":[{i2_str}]}}\n'
        )

    lines.append("\n")
    # power 群（同じ index_2 を使用）
    lines.append(f"{indent}//---- power: same {len(clusters)} groups as delay\n")
    for idx, (rep, members) in enumerate(clusters):
        i2_str = _format_floats(rep)
        name = fmt.format(idx)
        lines.append(
            f'{indent}   ,{{"kind":"power","grid":"10x10","name":"{name}",'
            f'"index_1":[{i1_str}],"index_2":[{i2_str}]}}\n'
        )

    lines.append(f"{indent}  ")
    return "".join(lines)


# ── メイン ────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="orig .lib から config_lib.jsonc の templates セクションを再生成")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--orig_csv", metavar="DIR",
                     help="extract_lib_csv 生成 CSV ディレクトリ（推奨）")
    src.add_argument("--orig_lib", metavar="FILE",
                     help="orig .lib ファイルを直接パース")
    ap.add_argument("--config", required=True, metavar="FILE",
                    help="既存 config_lib.jsonc（書き換え対象 or 参照元）")
    ap.add_argument("--output", metavar="FILE",
                    help="出力先 jsonc（省略時は --config を in-place 書き換え）")
    ap.add_argument("--tolerance", type=float, default=0.05,
                    help="クラスタ統合の許容（デフォルト 0.05 = 5%%）")
    ap.add_argument("--dry_run", action="store_true",
                    help="ファイル書き換えせず統計のみ出力")
    args = ap.parse_args()

    # 1) grids 収集
    if args.orig_csv:
        arc_grids = _collect_grids_from_csv(args.orig_csv)
        src_label = f"csv:{args.orig_csv}"
    else:
        arc_grids = _collect_grids_from_lib(args.orig_lib)
        src_label = f"lib:{args.orig_lib}"

    print(f"orig source     : {src_label}")
    print(f"arcs collected  : {len(arc_grids)}")

    # 2) クラスタリング
    all_grids = list(arc_grids.values())
    clusters, skipped = cluster_grids(all_grids, args.tolerance, expected_len=10)
    unique_count = len(set(all_grids))
    print(f"unique grids    : {unique_count}")
    print(f"length mismatch : {len(set(skipped))} unique (e.g. 19-point cells, multi-grid)")
    print(f"clusters formed : {len(clusters)} (tolerance {args.tolerance:.1%})")

    # クラスタ詳細
    print()
    print(f"  {'name':>6s}  {'max(pF)':>10s}  {'min(pF)':>10s}  {'members':>8s}")
    name_width = max(3, len(str(len(clusters) - 1)))
    fmt = f"d{{:0{name_width}d}}"
    for idx, (rep, members) in enumerate(clusters):
        print(f"  {fmt.format(idx):>6s}  {max(rep):>10.4g}  {min(rep):>10.4g}  {len(members):>8d}")

    if args.dry_run:
        print("\n(dry_run, config_lib.jsonc not modified)")
        return

    # 3) 既存 config を解析
    config_path = Path(args.config)
    text = config_path.read_text(encoding="utf-8")
    s, e = _find_templates_section(text)
    inner = text[s:e]
    index_1, non_dp = _parse_existing_templates(inner)

    if not index_1:
        print("WARN: index_1 not found in existing config; using empty")

    # 4) 新セクション組み立て
    new_inner = _build_templates_section(clusters, index_1, non_dp)

    new_text = text[:s] + new_inner + text[e:]

    # 5) 書き出し
    out_path = Path(args.output).resolve() if args.output else config_path
    if out_path == config_path:
        bak = Path(str(config_path) + ".bak")
        shutil.copy(config_path, bak)
        print(f"\nbackup          : {bak}")
    out_path.write_text(new_text, encoding="utf-8")
    print(f"written         : {out_path}")
    print(f"\nNext: run util_assign_templates to update std_*.jsonc")


if __name__ == "__main__":
    main()
