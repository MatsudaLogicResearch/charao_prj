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
"""gen_udp.py — 実回路(SPICE)の挙動を測って Verilog UDP を生成する

【目的】
charao が生成する .v は UDP を固定端子 (Q, C, P, CK, D, N, VPWR, VGND) でインスタンス化する
(docs/SPEC_primitives.md の契約)。端子が固定なので検証すべき状態空間も固定でき、
テストベンチは 1 本で済む。セル依存部は「インスタンス行」と「端子の極性」だけ。

本ツールは対象セルの SPICE netlist と端子対応を受け取り、ngspice で実回路を
動かして挙動を判定し、対応する UDP を標準出力へ書き出す。

【何を測り、何を測らないか】
  測る   : (a) 取り込みエッジ (posedge / negedge)
           (b) clear 単独 / preset 単独での Q
           (c) clear と preset の同時アサート時にどちらが勝つか
           (d) 保持 (クロックエッジ無し) で Q が保たれるか
  測らない: UDP 表中の x / (?0) 等のエッジ記法。解析シミュレーションでは観測でき
           ないため、測定結果に対応する「正準表」を選んで出力する。

【使い方】
  # OSU035 (素の .include だけで済む PDK)
  python3 tools/gen_udp.py \\
      --model   sample_src/OSU035/TT/nmos.sp \\
      --model   sample_src/OSU035/TT/pmos.sp \\
      --netlist sample_src/OSU035/std/NORMAL/V02.00/spice/DFFARAS_1X.spi \\
      --subckt  DFFARAS_1X \\
      --ports   "CLK DATA NRST NSET Q VDD VSS VNW VPW" \\
      --map     "CK=CLK,D=DATA,C=NRST:L,P=NSET:L,Q=Q" \\
      --power   "VDD=VDD,VSS=VSS,VNW=VNW,VPW=VPW" \\
      --vdd 3.3 --kind ff --name udp_iq_ff_n

  # gf180 (コーナーをセクションで選ぶ PDK) は .lib を --raw で渡す
      --raw ".inc design.ngspice" \\
      --raw ".lib sm141064.ngspice typical"

  --map の書式 : <UDP端子>=<セルピン>[:L]
     :L を付けると active-low とみなし、TB が反転した波形を与える。
     C / P を持たないセルは省略してよい (非活性レベルで固定される)。

【出力】
  標準出力  : primitive 定義 (そのまま <target>/std_primitives.v へ貼れる)
  標準エラー: 測定値と判定根拠
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile

# ---------------------------------------------------------------------------
# 刺激波形 : UDP 座標 (active-H) での (時刻[ns], レベル)
#   フェーズ
#     0-3n    C=1                     : 初期化（DC 動作点を確定させる）
#     5-10n   CK 立上り, D=1          : posedge 取り込みの確認
#     10-15n  CK 立下り, D=1->0       : negedge 取り込みの確認
#     20-24n  エッジ無し              : 保持の確認
#     24-30n  C=1 単独                : clear
#     33-39n  P=1 単独                : preset
#     42-52n  C=1 かつ P=1            : ★同時アサート（優先度の判定）
#     52-56n  C だけ解除 (P=1 のまま) : 解除順の依存
# ---------------------------------------------------------------------------
TR = 0.1  # 遷移時間 [ns]

WAVE_CK = [(0, 0), (5, 0), (5.1, 1), (10, 1), (10.1, 0),
           (15, 0), (15.1, 1), (20, 1), (20.1, 0),
           (25, 0), (25.1, 1), (30, 1), (30.1, 0),
           (35, 0), (35.1, 1), (40, 1), (40.1, 0), (60, 0)]
WAVE_D = [(0, 1), (12, 1), (12.1, 0), (22, 0), (22.1, 1), (60, 1)]
WAVE_C = [(0, 1), (3, 1), (3.1, 0),
          (24, 0), (24.1, 1), (30, 1), (30.1, 0),
          (42, 0), (42.1, 1), (52, 1), (52.1, 0), (60, 0)]
WAVE_P = [(0, 0), (33, 0), (33.1, 1), (39, 1), (39.1, 0),
          (42, 0), (42.1, 1), (56, 1), (56.1, 0), (60, 0)]

# 測定点 : 名前 -> (時刻[ns], 説明)
PROBES = {
    "m_cap1":   (9.0,  "CK 立上り後 (D=1)"),
    "m_capf":   (14.0, "CK 立下り後 (D=1->0)"),
    "m_cap0":   (19.0, "CK 立上り後 (D=0)"),
    "m_hold":   (23.0, "エッジ無し (保持)"),
    "m_clear":  (29.0, "C=1 単独"),
    "m_preset": (38.0, "P=1 単独"),
    "m_both":   (50.0, "C=1 かつ P=1"),
    "m_relc":   (55.0, "C 解除 / P=1 継続"),
}

# ---------------------------------------------------------------------------
# 正準 UDP 表
#   priority: "preset"=同時で Q=1 / "clear"=同時で Q=0 / "none"=同時は未定義(x)
# ---------------------------------------------------------------------------
_FF_HEAD = """\
   0  0  {ne} ?  ?  :  ?  :  -;
   ?  0  {pe} 0  ?  :  ?  :  0;
   ?  0  {ie} 0  ?  :  0  :  0;
   1  0  ?  ?  ?  :  ?  :  0;
   0  ?  {pe} 1  ?  :  ?  :  1;
   0  ?  {ie} 1  ?  :  1  :  1;
"""
_FF_TAIL = """\
   ?  ?  ?  ?  *  :  ?  :  x;
   0  0  ?  *  ?  :  ?  :  -;
   0  n  ?  ?  ?  :  ?  :  -;
   n  0  ?  ?  ?  :  ?  :  -;
   0  p  ?  ?  ?  :  ?  :  -;
"""
_FF_PRI = {
    "preset": "   ?  1  ?  ?  ?  :  ?  :  1;\n",
    "none":   "   0  1  ?  ?  ?  :  ?  :  1;\n",
    "clear":  "   0  1  ?  ?  ?  :  ?  :  1;\n   1  ?  ?  ?  ?  :  ?  :  0;\n",
}

_LAT_HEAD = """\
   0    0    {la}    *    ?  :  ?  :  -;
   0    0    (?{lo}) ?    ?  :  ?  :  -;
   0    (?0) {la}    ?    ?  :  ?  :  -;
   (?0) 0    {la}    ?    ?  :  ?  :  -;
   ?    0    {le}    0    ?  :  ?  :  0;
   ?    0    ?       (?0) ?  :  0  :  0;
   ?    (?0) ?       0    ?  :  0  :  0;
   1    0    ?       ?    ?  :  ?  :  0;
   0    ?    {le}    1    ?  :  ?  :  1;
   0    ?    ?       (?1) ?  :  1  :  1;
   (?0) ?    ?       1    ?  :  1  :  1;
"""
_LAT_TAIL = "   ?    ?    ?       ?    *  :  ?  :  x;\n"
_LAT_PRI = {
    "preset": "   ?    1    ?       ?    ?  :  ?  :  1;\n",
    "none":   "   0    1    ?       ?    ?  :  ?  :  1;\n",
    "clear":  "   0    1    ?       ?    ?  :  ?  :  1;\n   1    ?    ?       ?    ?  :  ?  :  0;\n",
}


def build_udp(name, kind, edge, priority):
    if kind == "ff":
        s = dict(ne="n", pe="r", ie="p") if edge == "pos" else dict(ne="p", pe="f", ie="n")
        body = _FF_HEAD.format(**s) + _FF_PRI[priority] + _FF_TAIL
        hdr = "// C  P  CK D  N  :  Q  :  Q"
    else:
        s = dict(la="0", lo="0", le="1") if edge == "pos" else dict(la="1", lo="1", le="0")
        body = _LAT_HEAD.format(**s) + _LAT_PRI[priority] + _LAT_TAIL
        hdr = "// C    P    CK      D    N  :  Q  :  Q"
    # 2026-07-30: 契約を 8 端子へ拡張（VPWR/VGND）。
    #   通常行は VPWR=1 / VGND=0 を要求し、 末尾に電源変化 -> Q=x の 2 行を置く。
    #   詳細は docs/SPEC_primitives.md 「電源ポート（VPWR / VGND）について」
    rows = []
    for ln in body.splitlines():
        s = ln.rstrip()
        if s.endswith(";") and s.count(":") == 2:
            i = s.rindex(":", 0, s.rindex(":"))   # 入力列の終端
            rows.append(f"{s[:i].rstrip()}  1    0   {s[i:]}")
        else:
            rows.append(s)
    body = "\n".join(rows) + "\n"
    body += ("//--- 電源が変化したら Q は不定（パワーカット時の x 伝播）\n"
             "   ?  ?  ?  ?  ?  *  ?  :  ?  :  x;\n"
             "   ?  ?  ?  ?  ?  ?  *  :  ?  :  x;\n")
    hdr = hdr.replace("N  :", "N  VPWR VGND :")
    return (f"primitive {name} ( Q, C, P, CK, D, N, VPWR, VGND );\n"
            f"output Q;\nreg Q;\ninput C, P, CK, D, N, VPWR, VGND;\ntable\n"
            f"{hdr}\n{body}endtable\nendprimitive\n")


TRAMP = 1.0  # 電源・入力の立ち上げ時間 [ns]


def pwl(src_name, net, wave, invert, vdd):
    """UDP 座標の波形を、必要なら反転して PWL 電圧源にする（挙動ソースは使わない）。

    先頭に 0V -> 初期値 のランプ(TRAMP)を挿入する。電源を 0 から立ち上げる方式に
    合わせ、 t=0 で「全ノード 0V なのに入力だけ VDD」という不整合を作らないため。
    """
    v0 = ((1 - wave[0][1]) if invert else wave[0][1]) * vdd
    pts = [f"0n 0", f"{TRAMP}n {v0:g}"]
    for t, lv in wave:
        if t <= TRAMP:
            continue
        v = (1 - lv) if invert else lv
        pts.append(f"{t}n {v * vdd:g}")
    return f"V{src_name} {net} 0 PWL(" + "  ".join(pts) + ")"


def parse_kv(s):
    out = {}
    for item in (s or "").split(","):
        item = item.strip()
        if not item:
            continue
        k, _, v = item.partition("=")
        pin, _, pol = v.partition(":")
        out[k.strip().upper()] = (pin.strip(), pol.strip().upper() == "L")
    return out


def run(args):
    pmap = parse_kv(args.map)
    power = {k: v[0] for k, v in parse_kv(args.power).items()}
    for req in ("CK", "D", "Q"):
        if req not in pmap:
            sys.exit(f"[ERR] --map に {req} がありません")
    vdd = float(args.vdd)
    q_pin = pmap["Q"][0]

    # 電源は 0 から立ち上げる（power-up 解析）。 これで t=0 の初期状態が自明になり、
    # 双安定ラッチでも DC 動作点を解かずに済む（uic と併用）。
    ramp = f"PWL(0n 0  {TRAMP}n {vdd:g}  60n {vdd:g})"
    lines = []
    lines.append(f"VVDD {power.get('VDD','VDD')} 0 {ramp}")
    lines.append(f"VVSS {power.get('VSS','VSS')} 0 DC 0")
    if "VNW" in power:
        lines.append(f"VVNW {power['VNW']} 0 {ramp}")
    if "VPW" in power:
        lines.append(f"VVPW {power['VPW']} 0 DC 0")

    waves = {"CK": WAVE_CK, "D": WAVE_D, "C": WAVE_C, "P": WAVE_P}
    driven = {}
    for udp_pin, w in waves.items():
        if udp_pin not in pmap:
            continue
        cell_pin, act_low = pmap[udp_pin]
        lines.append(pwl(cell_pin, cell_pin, w, act_low, vdd))
        driven[cell_pin] = True

    # C / P を持たないセル: 非活性レベルで固定（UDP 座標 0）
    inst = []
    for p in args.ports.split():
        inst.append(p)
    for p in inst:
        if p in driven or p == q_pin or p in power.values():
            continue
        lines.append(f"* {p} : --map に無いため 0V 固定")
        lines.append(f"V{p} {p} 0 DC 0")

    inc = [f".include {m if args.raw_path else os.path.abspath(m)}"
           for m in args.model + args.netlist]
    meas = [f".meas tran {k} FIND v({q_pin}) AT={t}n  $ {d}" for k, (t, d) in PROBES.items()]

    tb = "\n".join([
        f"* gen_udp.py auto-generated testbench ({args.subckt})",
        *inc, *args.raw,
        "* ラッチのクロスカップルは DC 動作点が不定になりやすいので保険をかける",
        ".option rshunt=1e9",
        *lines,
        f"X_DUT {' '.join(inst)} {args.subckt}",
        "* uic : DC 動作点を解かずに過渡解析へ入る。",
        "*       FF のクロスカップル・ラッチは双安定で DC 解が一意に決まらず収束しない。",
        "*       刺激の 0-3n で C(clear) をアサートしているので、 初期状態は sim 内で確定する。",
        ".tran 20p 60n uic",
        *meas, ".end", ""])

    tbdir = args.tb_out or tempfile.mkdtemp(prefix="gen_udp_")
    os.makedirs(tbdir, exist_ok=True)
    tbf = os.path.join(tbdir, "udp_tb.sp")
    open(tbf, "w").write(tb)
    print(f"[INF] testbench = {tbf}", file=sys.stderr)
    if args.tb_only:
        print("[INF] --tb-only のため sim は実行しません", file=sys.stderr)
        return

    if args.lis:
        out = open(args.lis).read()
        print(f"[INF] 測定値を {args.lis} から読みます (sim は実行しません)", file=sys.stderr)
    else:
        r = subprocess.run([args.ngspice, "-b", tbf], capture_output=True, text=True,
                           cwd=os.path.dirname(os.path.abspath(tbf)))
        out = r.stdout + r.stderr

    got = {}
    for line in out.splitlines():
        m = re.match(r"^(m_\w+)\s*=\s*(\S+)", line)
        if m:
            got.setdefault(m.group(1), float(m.group(2)))
    if len(got) < len(PROBES):
        print(out[-3000:], file=sys.stderr)
        sys.exit(f"[ERR] 測定に失敗しました (取得 {sorted(got)})")

    # Q に :L を付けると「UDP の Q は実セル出力の反転」とみなす。
    #   UDP は汎用表（P 側が優先）で、どちらの信号が物理的に優先かは配線で決まる。
    #   実 PDK は優先させたい信号を P へ渡し、出力を反転して取り出す（gf180 dffrsnq_func と同型）。
    q_inv = pmap["Q"][1]
    if q_inv:
        print("[INF] Q は反転して評価します（UDP の Q = 実セル出力の反転）", file=sys.stderr)
    lvl = lambda v: (0 if v > vdd * 0.5 else 1) if q_inv else (1 if v > vdd * 0.5 else 0)
    print("[INF] 測定値:", file=sys.stderr)
    for k, (t, d) in PROBES.items():
        print(f"        {k:<9} {got[k]:8.4f} V -> {lvl(got[k])}   ({d})", file=sys.stderr)

    edge = "pos" if lvl(got["m_cap1"]) == 1 else "neg"
    c1, p1, both = lvl(got["m_clear"]), lvl(got["m_preset"]), lvl(got["m_both"])
    if c1 == 0 and p1 == 1:
        priority = "preset" if both == 1 else "clear"
    else:
        priority = "none"
        print(f"[WARN] clear/preset の単独動作が想定外 (clear->{c1}, preset->{p1})。"
              f"--map の極性を確認してください。", file=sys.stderr)
    print(f"[INF] 判定: edge={edge} / clear={c1} / preset={p1} / 同時={both}"
          f" -> priority={priority}", file=sys.stderr)
    if priority == "clear":
        print("[WARN] clear 優先型です。charao 既存の *_n / *_hn では表現できません"
              " (新しい UDP が必要)。", file=sys.stderr)

    sys.stdout.write(build_udp(args.name, args.kind, edge, priority))


def main():
    p = argparse.ArgumentParser(description="実回路(SPICE)の挙動から Verilog UDP を生成する")
    p.add_argument("--model", action="append", default=[], help="SPICE モデル (複数可)")
    p.add_argument("--netlist", action="append", default=[], required=True, help="セル netlist (複数可)")
    p.add_argument("--subckt", required=True, help="対象 subckt 名")
    p.add_argument("--ports", required=True, help='subckt のピン順')
    p.add_argument("--map", required=True, help='UDP端子=セルピン[:L]')
    p.add_argument("--power", default="", help='電源端子 (VDD=/VSS=/VNW=/VPW=)')
    p.add_argument("--vdd", default="3.3", help="電源電圧 [V]")
    p.add_argument("--kind", choices=["ff", "latch"], default="ff", help="セル種別")
    p.add_argument("--name", required=True, help="出力する primitive 名")
    p.add_argument("--ngspice", default="ngspice", help="simulator コマンド")
    p.add_argument("--tb-out", default="", help="TB の出力先 dir (指定時は残す)")
    p.add_argument("--raw", action="append", default=[],
                   help='TB 冒頭へそのまま挿入する行。複数可。'
                        'コーナーをセクションで選ぶ PDK は .lib をここで渡す')
    p.add_argument("--raw-path", action="store_true",
                   help="--model/--netlist を絶対パス化しない (リモート実行用)")
    p.add_argument("--tb-only", action="store_true", help="TB を書き出すだけで sim しない")
    p.add_argument("--lis", default="", help="既存の ngspice 出力から測定値を読む")
    run(p.parse_args())


if __name__ == "__main__":
    main()
