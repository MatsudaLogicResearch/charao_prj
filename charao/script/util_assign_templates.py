#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
util_assign_templates.py — std_*.jsonc の template_kgn を per-cell 最適 d?? へ再割り当て

【目的】
オリジナル .lib のセルごとの max(index_2)（最大出力負荷）に対して、
config_lib.jsonc に定義された d?? template の中から最も近いものを選び、
std_*.jsonc の template_kgn[delay] / [power] を更新する。

【使い方】

# orig CSV を入力（推奨・高速）。先に extract_lib_csv で抽出しておく
python -m charao.script.util_assign_templates \\
    --orig_csv tmp/gf180_fd_mcuC7t20240817/tt_025C_5v00 \\
    --config sample/target/gf180/fd/mcuC7t20240817/config_lib.jsonc \\
    --jsonc sample/target/gf180/fd/mcuC7t20240817/std_comb.jsonc

# orig .lib を直接パース
python -m charao.script.util_assign_templates \\
    --orig_lib sample/src/.../gf180mcu_fd_sc_mcu7t5v0__tt_025C_5v00.lib \\
    --config sample/target/gf180/fd/mcuC7t20240817/config_lib.jsonc \\
    --jsonc sample/target/gf180/fd/mcuC7t20240817/std_comb.jsonc

# 書き換えずレポートのみ
python -m charao.script.util_assign_templates --dry_run ...

【動作仕様】
1. orig 側から per-cell max(index_2) を取得
2. config_lib.jsonc の kind=delay の d?? エントリから各 template の max(index_2) を取得
3. 各セルについて `|charao_max/orig_max - 1|` が最小の d?? を選定
4. std_*.jsonc の template_kgn 行（cell エントリの直前にある）の delay / power の d??
   を新しい値に置換（grid 表記はそのまま保持）
5. 元ファイルは `.bak` でバックアップ後、in-place で書き換え（--dry_run 時は書き換えなし）
6. 変更内容の per-cell レポートを stdout に出力
7. --report 指定時は同レポートを CSV として保存
"""

import argparse
import csv
import math
import re
import shutil
from collections import Counter
from pathlib import Path

from charao.script.util_extract_lib_csv import parse_lib_file


# ── load 軸抽出の前処理 ───────────────────────────────────────────────────
# constraint 系（setup/hold/recovery/removal/min_period）の index_2 は被制約ピンの
# slew 軸（0.02..4）であり load 軸ではない。 lump すると seq で長さ不一致 → max-only
# fallback に落ちて誤割当になる（例: dffq の load=0.001..0.24 を slew=0.02..4 の d044 に誤マッチ）。
# よって delay 系（load 軸）だけを抽出する。 comb は timing_type="" のため blacklist 方式で除外する。
_CONSTRAINT_TIMING_TYPES = {
    "setup_rising", "setup_falling", "hold_rising", "hold_falling",
    "recovery_rising", "recovery_falling", "removal_rising", "removal_falling",
    "non_seq_setup_rising", "non_seq_setup_falling",
    "non_seq_hold_rising", "non_seq_hold_falling",
    "minimum_period", "min_pulse_width",
}


def _pick_load_grid(arc_grids):
    """アーク単位の load グリッド群から代表 1 本を返す。

    多アークセル（addf=CO/S、 bufz=comb/three_state）は微妙に異なる 10 点グリッドを
    複数持つ。 lump せずアーク毎に集計し、 最頻グリッド（同数なら max が最大）を採用する。
    """
    grids = [g for g in arc_grids if len(g) > 1]
    if not grids:
        return None
    cnt = Counter(grids)
    return max(cnt.items(), key=lambda kv: (kv[1], max(kv[0])))[0]


# ── orig 側 grid 取得 ─────────────────────────────────────────────────────

def _read_grids_from_csv(csv_dir):
    """timing.csv から per-cell の代表 load グリッド（delay 系のみ）を返す。

    constraint 系（slew 軸）を除外し、 アーク（pin/related_pin/timing_type）単位で
    集計してから代表 1 本を選ぶ（_pick_load_grid）。
    """
    p = Path(csv_dir) / "timing.csv"
    if not p.exists():
        raise FileNotFoundError(f"timing.csv not found in {csv_dir}")
    cell_arc = {}  # cell -> arc_key -> set(load)
    with open(p, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        i2_col = next((c for c in reader.fieldnames if c.startswith("index2")), None)
        if i2_col is None:
            raise ValueError(f"index2 column not found in {p}")
        tt_col = "timing_type" if "timing_type" in reader.fieldnames else None
        for r in reader:
            tt = (r.get(tt_col) or "") if tt_col else ""
            if tt in _CONSTRAINT_TIMING_TYPES:
                continue
            try:
                i2 = float(r[i2_col])
            except (ValueError, KeyError):
                continue
            if math.isnan(i2):
                continue
            cell = r["cell_name"]
            arc = (r.get("pin"), r.get("related_pin"), tt)
            cell_arc.setdefault(cell, {}).setdefault(arc, set()).add(i2)
    out = {}
    for cell, arcs in cell_arc.items():
        g = _pick_load_grid([tuple(sorted(s)) for s in arcs.values()])
        if g:
            out[cell] = g
    return out


def _read_grids_from_lib(lib_path):
    """orig .lib を直接パースして per-cell の代表 load グリッド（delay 系のみ）を返す。

    constraint 系（slew 軸）を除外し、 アーク単位で集計して代表 1 本を選ぶ。
    """
    _units, _scales, _leak, _power, timing = parse_lib_file(Path(lib_path))
    cell_arc = {}  # cell -> arc_key -> set(load)
    for r in timing:
        tt = r.get("timing_type") or ""
        if tt in _CONSTRAINT_TIMING_TYPES:
            continue
        i2_key = next((k for k in r if k.startswith("index2")), None)
        if i2_key is None:
            continue
        try:
            i2 = float(r[i2_key])
        except (ValueError, TypeError):
            continue
        if math.isnan(i2):
            continue
        cell = r["cell_name"]
        arc = (r.get("pin"), r.get("related_pin"), tt)
        cell_arc.setdefault(cell, {}).setdefault(arc, set()).add(i2)
    out = {}
    for cell, arcs in cell_arc.items():
        g = _pick_load_grid([tuple(sorted(s)) for s in arcs.values()])
        if g:
            out[cell] = g
    return out


# ── config_lib.jsonc から template max load 取得 ──────────────────────────

def _read_template_grids(config_path):
    """config_lib.jsonc の kind=delay の d?? から sorted index_2 タプルを返す dict。"""
    text = Path(config_path).read_text(encoding="utf-8")
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

    pattern = re.compile(
        r'"kind"\s*:\s*"delay"\s*,'
        r'\s*"grid"\s*:\s*"[^"]*"\s*,'
        r'\s*"name"\s*:\s*"(d\d+)"\s*,'
        r'\s*"index_1"\s*:\s*\[[^\]]*\]\s*,'
        r'\s*"index_2"\s*:\s*\[([^\]]*)\]'
    )
    template_grids = {}
    for m in pattern.finditer(text):
        name = m.group(1)
        try:
            vals = sorted(float(v.strip()) for v in m.group(2).split(",") if v.strip())
        except ValueError:
            continue
        if vals:
            template_grids[name] = tuple(vals)
    return template_grids


# ── マッチング ───────────────────────────────────────────────────────────

def _best_template(orig_grid, template_grids):
    """全 index 点の最大相対偏差が最小の d?? を返す。

    orig と template の index 数が同じ場合のみ比較。長さ不一致の template はスキップ。
    全テンプレが長さ不一致なら orig の max でフォールバック選定。
    """
    if not template_grids or not orig_grid:
        return None, None
    n = len(orig_grid)
    best_name = None
    best_dev = float("inf")
    for name, vals in template_grids.items():
        if len(vals) != n:
            continue
        devs = [abs(v / o - 1.0) for v, o in zip(vals, orig_grid) if o != 0]
        if not devs:
            continue
        d = max(devs)
        if d < best_dev:
            best_dev = d
            best_name = name
    if best_name is None:
        # フォールバック：max のみで選定
        omax = max(orig_grid)
        best_name = min(template_grids.items(),
                        key=lambda kv: abs(max(kv[1]) / omax - 1.0))[0]
        best_dev = abs(max(template_grids[best_name]) / omax - 1.0)
    return best_name, best_dev


# ── std_*.jsonc 書き換え ──────────────────────────────────────────────────

_RE_TEMPLATE_LINE = re.compile(r'template_kgn')
_RE_CELL = re.compile(r'"cell"\s*:\s*"([^"]+)"')


def _replace_dxx(line, kind, new_d):
    """template_kgn 行内の `["<kind>","<grid>","d??"]` の d?? を new_d に置換。"""
    return re.sub(
        rf'(\["{kind}","[^"]+",")d\d+(?:_\w+)?("\])',
        rf'\g<1>{new_d}\g<2>',
        line,
    )


def _update_jsonc(jsonc_path, mappings, dry_run=False):
    """jsonc の template_kgn を更新。直前の template_kgn 行とその後の cell 行を対応付け。"""
    text = Path(jsonc_path).read_text(encoding="utf-8")
    lines = text.split("\n")
    pending_idx = None
    changed_cells = []

    for i, line in enumerate(lines):
        if _RE_TEMPLATE_LINE.search(line):
            pending_idx = i
            continue
        m = _RE_CELL.search(line)
        if m and pending_idx is not None:
            cell = m.group(1)
            if cell in mappings:
                new_d = mappings[cell]
                old = lines[pending_idx]
                upd = _replace_dxx(old, "delay", new_d)
                # ISS-00080 で power→power_tout/power_tin に分割済。 load(2D) grid は power_tout のみ。
                # power_tin は 10x0 の入力 slew 1D（d000）なので load 再割当の対象外。
                upd = _replace_dxx(upd, "power_tout", new_d)
                if upd != old:
                    lines[pending_idx] = upd
                    changed_cells.append(cell)
            pending_idx = None

    if not dry_run and changed_cells:
        bak = Path(str(jsonc_path) + ".bak")
        shutil.copy(jsonc_path, bak)
        Path(jsonc_path).write_text("\n".join(lines), encoding="utf-8")
    return changed_cells


# ── 既存 d?? を読み取る（レポート用） ────────────────────────────────────

def _read_current_assignment(jsonc_path):
    """jsonc から {cell: current_delay_d??} の dict を返す。"""
    text = Path(jsonc_path).read_text(encoding="utf-8")
    lines = text.split("\n")
    pending = None
    cur = {}
    re_d = re.compile(r'\["delay","[^"]+","(d\d+(?:_\w+)?)"\]')
    for line in lines:
        if _RE_TEMPLATE_LINE.search(line):
            pending = line
            continue
        m = _RE_CELL.search(line)
        if m and pending is not None:
            md = re_d.search(pending)
            if md:
                cur[m.group(1)] = md.group(1)
            pending = None
    return cur


# ── メイン ────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="orig .lib の per-cell max load に合わせて std_*.jsonc の template_kgn を再割り当て")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--orig_csv", metavar="DIR",
                     help="extract_lib_csv 生成 CSV ディレクトリ（推奨）")
    src.add_argument("--orig_lib", metavar="FILE",
                     help="orig .lib ファイルを直接パース")
    ap.add_argument("--config", required=True, metavar="FILE",
                    help="config_lib.jsonc（template d?? 定義）")
    ap.add_argument("--jsonc", required=True, metavar="FILE",
                    help="更新対象 std_*.jsonc")
    ap.add_argument("--report", metavar="FILE",
                    help="変更レポート CSV 出力先（任意）")
    ap.add_argument("--dry_run", action="store_true",
                    help="書き換えずレポートのみ")
    args = ap.parse_args()

    # 1) orig per-cell grid（全 index 点）
    if args.orig_csv:
        cell_orig_grid = _read_grids_from_csv(args.orig_csv)
        src_label = f"csv:{args.orig_csv}"
    else:
        cell_orig_grid = _read_grids_from_lib(args.orig_lib)
        src_label = f"lib:{args.orig_lib}"

    # 2) config_lib templates（全 index 点）
    template_grids = _read_template_grids(args.config)
    if not template_grids:
        print(f"ERROR: no `kind=delay` template found in {args.config}")
        return

    # 3) 現在の割り当て
    current = _read_current_assignment(args.jsonc)

    # 4) per-cell ベストマッチ計算（全 index 点 max 偏差最小）
    mapping_rows = []  # for report
    new_mapping = {}   # for update
    for cell, cur_d in current.items():
        orig_grid = cell_orig_grid.get(cell)
        if orig_grid is None:
            mapping_rows.append({
                "cell_name": cell, "orig_max_pF": "",
                "current_d": cur_d, "current_max_pF": "",
                "new_d": "", "new_max_pF": "", "max_dev": "",
                "note": "skip: orig not found",
            })
            continue
        best_d, best_dev = _best_template(orig_grid, template_grids)
        if best_d is None:
            continue
        orig_max = max(orig_grid)
        new_max = max(template_grids[best_d])
        cur_grid = template_grids.get(cur_d, ())
        cur_max = max(cur_grid) if cur_grid else 0.0
        new_mapping[cell] = best_d
        mapping_rows.append({
            "cell_name": cell,
            "orig_max_pF": f"{orig_max:.4g}",
            "current_d": cur_d,
            "current_max_pF": f"{cur_max:.4g}",
            "new_d": best_d,
            "new_max_pF": f"{new_max:.4g}",
            "max_dev": f"{best_dev:.4f}",
            "note": "changed" if best_d != cur_d else "same",
        })

    # 5) jsonc 書き換え
    changed = _update_jsonc(args.jsonc, new_mapping, dry_run=args.dry_run)

    # 6) レポート出力
    print(f"orig source : {src_label}")
    print(f"config      : {args.config}")
    print(f"jsonc       : {args.jsonc}")
    print(f"templates   : {len(template_grids)} delay templates loaded")
    print(f"cells       : {len(current)} in jsonc, {len(cell_orig_grid)} in orig")
    print(f"changed     : {len(changed)} cells {'(dry_run, NOT written)' if args.dry_run else '(written, .bak created)'}")
    print()

    # diff 表示
    print(f"  {'cell_name':50s} {'orig_max(pF)':>12s} {'cur_d':>8s} {'new_d':>8s} {'new_max(pF)':>12s} {'max_dev':>8s}  note")
    for r in mapping_rows:
        if r["note"] != "same":
            print(f"  {r['cell_name']:50s} {r['orig_max_pF']:>12s} {r['current_d']:>8s} "
                  f"{r['new_d']:>8s} {r['new_max_pF']:>12s} {r['max_dev']:>8s}  {r['note']}")

    if args.report:
        out = Path(args.report).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(mapping_rows[0].keys()))
            w.writeheader()
            w.writerows(mapping_rows)
        print(f"\nreport CSV  : {out}")


if __name__ == "__main__":
    main()
