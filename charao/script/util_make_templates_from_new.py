#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
util_make_templates_from_new.py — orig .lib 不要で config_lib.jsonc の templates を生成

【目的】
オリジナル Liberty が無いプロセス向けに、Cin-fanout 方式で index_2（load）と
physical/geometric curve で index_1（slew）を生成し、config_lib.jsonc の
templates セクションに書き出す。現状は単一 Cin 固定 → 単一グループ d000 のみ生成。
将来 LEF / SPICE から Cin を自動抽出して複数グループに拡張予定。

【使い方】

# デフォルト値（10x10、Cin=0.003 pF、gf180 相当の slew range）
python -m charao.script.util_make_templates_from_new \
    --config sample/target/<pdk>/.../config_lib.jsonc \
    --cin 0.003

# 7x7 グリッド
python -m charao.script.util_make_templates_from_new \
    --config .../config_lib.jsonc --cin 0.003 \
    --index1_count 7 --index2_count 7 \
    --fanout "0.25,1,3,8,16,32"

# dry_run（書き換えせず生成値のみ表示）
python -m charao.script.util_make_templates_from_new \
    --config .../config_lib.jsonc --cin 0.003 --dry_run

# 別ファイルへ出力（in-place しない）
python -m charao.script.util_make_templates_from_new \
    --config .../config_lib.jsonc --cin 0.003 --output new_config.jsonc

【index_1 / index_2 の決め方】
詳細は 30_projects/charao_prj.md 「参照 .lib が無い場合の index_1 / index_2 設計指針」参照。
"""

import argparse
import re
import shutil
from pathlib import Path


# ── physical curve weights（i=0..n-1 → (slew_max/slew_min) ** w[i]）──
PHYSICAL_CURVE_WEIGHTS = {
    5:  [0.0, 0.3, 0.55, 0.8, 1.0],
    6:  [0.0, 0.24, 0.44, 0.64, 0.84, 1.0],
    7:  [0.0, 0.2, 0.38, 0.55, 0.72, 0.87, 1.0],
    8:  [0.0, 0.18, 0.33, 0.48, 0.62, 0.75, 0.88, 1.0],
    10: [0.0, 0.2, 0.35, 0.5, 0.62, 0.72, 0.81, 0.88, 0.94, 1.0],
}


# ── index 生成 ────────────────────────────────────────────────────────

def _sig3(x, digits=3):
    """有効 <digits> 桁へ丸める（2026-07-31 ダーマツ判断）。

    index は計算で作った値なので下位桁に意味がない。 3 桁で十分（ズレ 0.5% 以下）。
    遅延は slew/load の滑らかな関数なので、 この程度のズレは結果に影響しない。
    """
    import math
    if x == 0:
        return 0.0
    d = digits - int(math.floor(math.log10(abs(x)))) - 1
    v = round(x, d)
    return int(v) if v == int(v) and abs(v) >= 1 else v

def build_index1(slew_min, slew_max, count, curve):
    """index_1（slew, ns）を生成。physical curve は PHYSICAL_CURVE_WEIGHTS を使用。"""
    if curve == "physical" and count in PHYSICAL_CURVE_WEIGHTS:
        w = PHYSICAL_CURVE_WEIGHTS[count]
        return [_sig3(slew_min * ((slew_max / slew_min) ** wi)) for wi in w]
    # geometric fallback
    r = (slew_max / slew_min) ** (1.0 / (count - 1))
    return [_sig3(slew_min * (r ** i)) for i in range(count)]


def build_index2(cin, fanout_list, floor, count):
    """index_2（load, pF）を生成。先頭 1 点は floor、残りは cin×fanout。"""
    pts = [_sig3(floor)] + [_sig3(cin * f) for f in fanout_list]
    if len(pts) != count:
        raise ValueError(
            f"fanout 要素数 {len(fanout_list)} と index2_count-1 ({count - 1}) が不一致")
    return pts


# ── 既存 config_lib.jsonc 解析 ────────────────────────────────────────

def _find_templates_section(text):
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


def _parse_non_dp(inner):
    """leakage / passive / const など delay/power 以外のエントリを文字列で収集。"""
    non_dp = []
    for m in re.finditer(r'\{\s*"kind"\s*:\s*"(?P<kind>[^"]+)"[^{}]*?\}', inner):
        if m.group("kind") not in ("delay", "power"):
            non_dp.append(m.group(0))
    return non_dp


# ── templates セクション生成 ──────────────────────────────────────────

def _fmt(vals, fmt="{:g}"):
    return ",".join(fmt.format(float(v)) for v in vals)


def build_templates_block(index1, index2, non_dp, indent="    "):
    lines = ["\n"]
    if non_dp:
        for i, e in enumerate(non_dp):
            prefix = "" if i == 0 else "   ,"
            lines.append(f"{indent}{prefix}{e}\n")
        lines.append("\n")

    grid = f"{len(index1)}x{len(index2)}"
    i1s = _fmt(index1)
    i2s = _fmt(index2)
    prefix_delay = "    " if not non_dp else "   ,"

    lines.append(f"{indent}//---- delay: 1 group (generated from new: single Cin)\n")
    lines.append(
        f'{indent}{prefix_delay}{{"kind":"delay","grid":"{grid}","name":"d000",'
        f'"index_1":[{i1s}],"index_2":[{i2s}]}}\n')

    lines.append("\n")
    lines.append(f"{indent}//---- power: same as delay\n")
    lines.append(
        f'{indent}   ,{{"kind":"power","grid":"{grid}","name":"d000",'
        f'"index_1":[{i1s}],"index_2":[{i2s}]}}\n')

    lines.append(f"{indent}  ")
    return "".join(lines)


# ── メイン ────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="orig 無しで config_lib.jsonc の templates を生成（Cin-fanout 方式）")
    ap.add_argument("--config", required=True, metavar="FILE",
                    help="既存 config_lib.jsonc（書き換え対象 or 参照元）")
    ap.add_argument("--cin", type=float, required=True,
                    help="入力ピン容量 Cin [pF]（固定値、全セル共通）")
    ap.add_argument("--index1_count", type=int, default=10,
                    help="index_1 点数（デフォルト 10）")
    ap.add_argument("--index2_count", type=int, default=10,
                    help="index_2 点数（デフォルト 10）")
    ap.add_argument("--slew_min", type=float, default=0.02,
                    help="slew 最小値 [ns]（デフォルト 0.02）")
    ap.add_argument("--slew_max", type=float, default=4.0,
                    help="slew 最大値 [ns]（デフォルト 4.0）")
    ap.add_argument("--fanout", default="0.25,1,3,6,10,15,22,30,40",
                    help="カンマ区切り fanout 列（要素数 = index2_count - 1）")
    ap.add_argument("--floor", type=float, default=0.001,
                    help="index_2[0] の固定フロア値 [pF]（デフォルト 0.001）")
    ap.add_argument("--slew_curve", choices=["physical", "geometric"], default="physical",
                    help="index_1 の曲線（physical=非線形 / geometric=等比）")
    ap.add_argument("--output", metavar="FILE",
                    help="出力先 jsonc（省略時は --config を in-place 書き換え）")
    ap.add_argument("--dry_run", action="store_true",
                    help="ファイル書き換えせず生成値のみ表示")
    args = ap.parse_args()

    fanout = [float(x) for x in args.fanout.split(",") if x.strip()]
    if len(fanout) != args.index2_count - 1:
        raise SystemExit(
            f"ERROR: fanout 要素数 {len(fanout)} が index2_count-1 "
            f"({args.index2_count - 1}) と不一致")

    index1 = build_index1(args.slew_min, args.slew_max,
                          args.index1_count, args.slew_curve)
    index2 = build_index2(args.cin, fanout,
                          floor=args.floor, count=args.index2_count)

    print(f"cin             : {args.cin} pF")
    print(f"slew range      : {args.slew_min} - {args.slew_max} ns "
          f"({args.slew_curve})")
    print(f"index_1 ({args.index1_count}pt) : "
          f"[{', '.join(f'{v:g}' for v in index1)}]")
    print(f"index_2 ({args.index2_count}pt) : "
          f"[{', '.join(f'{v:g}' for v in index2)}]")

    if args.dry_run:
        print("\n(dry_run, config_lib.jsonc not modified)")
        return

    config_path = Path(args.config)
    text = config_path.read_text(encoding="utf-8")
    s, e = _find_templates_section(text)
    inner = text[s:e]
    non_dp = _parse_non_dp(inner)

    new_inner = build_templates_block(index1, index2, non_dp)
    new_text = text[:s] + new_inner + text[e:]

    out_path = Path(args.output).resolve() if args.output else config_path
    if out_path == config_path:
        bak = Path(str(config_path) + ".bak")
        shutil.copy(config_path, bak)
        print(f"\nbackup          : {bak}")
    out_path.write_text(new_text, encoding="utf-8")
    print(f"written         : {out_path}")


if __name__ == "__main__":
    main()
