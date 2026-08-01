#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sky130_fd_sc_hd の std_comb.jsonc / std_seq.jsonc を生成する（ISS-00181 Step 1）

対象は「既存の charao logic でそのまま通るセル」のみ。
ports_dict は subckt のピン順どおりに並べる（chk_ports が挿入順で厳密照合するため）。
"""
import re
import json
from collections import OrderedDict

SPICE = "sample_src/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice"
LIB   = "sample_src/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
PFX   = "sky130_fd_sc_hd__"

# 電源ピン -> logic 名
PWR = {"VPWR": "vdd", "VGND": "vss", "VPB": "nwell", "VNB": "pwell"}
# charao の logic 側電源名（config の *_name に対応）
#--- ISS-00181: 電源/ウェルピンは「実ピン名」を値にする。
#    "vdd"/"vss" 等の論理名にすると [Error] not used port name=vss in XDUT になる。
PWR_LOGIC = {"VPWR": "VPWR", "VGND": "VGND", "VPB": "VPB", "VNB": "VNB"}

# セル base 名 -> (charao logic, 信号ピン -> logic ポート)
#   出力は o0（第 2 出力は o1）、入力は i0.. / クロック c0 / reset r0 / set s0
MAP = {
    # --- 基本ゲート ---
    "inv":    ("INV",   {"A": "i0", "Y": "o0"}),
    "clkinv": ("INV",   {"A": "i0", "Y": "o0"}),
    "clkinvlp": ("INV", {"A": "i0", "Y": "o0"}),
    "buf":    ("BUF",   {"A": "i0", "X": "o0"}),
    "bufbuf": ("BUF",   {"A": "i0", "X": "o0"}),   # function : (A)
    "bufinv": ("INV",   {"A": "i0", "Y": "o0"}),   # function : (!A)
    "clkbuf": ("BUF",   {"A": "i0", "X": "o0"}),
    # 遅延セル（1 入力 1 出力、 追加端子なし＝BUF として扱う）
    "dlygate4sd1": ("BUF", {"A": "i0", "X": "o0"}),
    "dlygate4sd2": ("BUF", {"A": "i0", "X": "o0"}),
    "dlygate4sd3": ("BUF", {"A": "i0", "X": "o0"}),
    "dlymetal6s2s": ("BUF", {"A": "i0", "X": "o0"}),
    "dlymetal6s4s": ("BUF", {"A": "i0", "X": "o0"}),
    "dlymetal6s6s": ("BUF", {"A": "i0", "X": "o0"}),
    "clkdlybuf4s15": ("BUF", {"A": "i0", "X": "o0"}),
    "clkdlybuf4s18": ("BUF", {"A": "i0", "X": "o0"}),
    "clkdlybuf4s25": ("BUF", {"A": "i0", "X": "o0"}),
    "clkdlybuf4s50": ("BUF", {"A": "i0", "X": "o0"}),

    "and2":  ("AND2",  {"A": "i0", "B": "i1", "X": "o0"}),
    "and3":  ("AND3",  {"A": "i0", "B": "i1", "C": "i2", "X": "o0"}),
    "and4":  ("AND4",  {"A": "i0", "B": "i1", "C": "i2", "D": "i3", "X": "o0"}),
    "or2":   ("OR2",   {"A": "i0", "B": "i1", "X": "o0"}),
    "or3":   ("OR3",   {"A": "i0", "B": "i1", "C": "i2", "X": "o0"}),
    "or4":   ("OR4",   {"A": "i0", "B": "i1", "C": "i2", "D": "i3", "X": "o0"}),
    "nand2": ("NAND2", {"A": "i0", "B": "i1", "Y": "o0"}),
    "nand3": ("NAND3", {"A": "i0", "B": "i1", "C": "i2", "Y": "o0"}),
    "nand4": ("NAND4", {"A": "i0", "B": "i1", "C": "i2", "D": "i3", "Y": "o0"}),
    "nor2":  ("NOR2",  {"A": "i0", "B": "i1", "Y": "o0"}),
    "nor3":  ("NOR3",  {"A": "i0", "B": "i1", "C": "i2", "Y": "o0"}),
    "nor4":  ("NOR4",  {"A": "i0", "B": "i1", "C": "i2", "D": "i3", "Y": "o0"}),
    "xor2":  ("XOR2",  {"A": "i0", "B": "i1", "X": "o0"}),
    "xor3":  ("XOR3",  {"A": "i0", "B": "i1", "C": "i2", "X": "o0"}),
    "xnor2": ("XNOR2", {"A": "i0", "B": "i1", "Y": "o0"}),
    "xnor3": ("XNOR3", {"A": "i0", "B": "i1", "C": "i2", "X": "o0"}),   # 出力は X（Y ではない）
    "mux2":  ("MUX2",  {"A0": "i0", "A1": "i1", "S": "i2", "X": "o0"}),
    "mux4":  ("MUX4",  {"A0": "i0", "A1": "i1", "A2": "i2", "A3": "i3",
                        "S0": "i4", "S1": "i5", "X": "o0"}),
    #--- 加算器: charao は o0=SUM / o1=COUT（ADDF: o0=i0^i1^i2, o1=多数決）。
    #    gf180 も "S":"o0" / "CO":"o1" と定義している。 逆に割り当てると
    #    COUT 側で遷移が起きず .meas が "out of interval" で失敗する。
    "ha":    ("ADDH",  {"A": "i0", "B": "i1", "COUT": "o1", "SUM": "o0"}),
    "fa":    ("ADDF",  {"A": "i0", "B": "i1", "CIN": "i2", "COUT": "o1", "SUM": "o0"}),
    # --- 複合ゲート（反転出力のみ charao に対応あり）---
    "a21oi":  ("AOI21",  {"A1": "i0", "A2": "i1", "B1": "i2", "Y": "o0"}),
    "a22oi":  ("AOI22",  {"A1": "i0", "A2": "i1", "B1": "i2", "B2": "i3", "Y": "o0"}),
    "a211oi": ("AOI211", {"A1": "i0", "A2": "i1", "B1": "i2", "C1": "i3", "Y": "o0"}),
    "a221oi": ("AOI221", {"A1": "i0", "A2": "i1", "B1": "i2", "B2": "i3", "C1": "i4", "Y": "o0"}),
    "a222oi": ("AOI222", {"A1": "i0", "A2": "i1", "B1": "i2", "B2": "i3",
                          "C1": "i4", "C2": "i5", "Y": "o0"}),
    "o21ai":  ("OAI21",  {"A1": "i0", "A2": "i1", "B1": "i2", "Y": "o0"}),
    "o22ai":  ("OAI22",  {"A1": "i0", "A2": "i1", "B1": "i2", "B2": "i3", "Y": "o0"}),
    "o211ai": ("OAI211", {"A1": "i0", "A2": "i1", "B1": "i2", "C1": "i3", "Y": "o0"}),
    "o221ai": ("OAI221", {"A1": "i0", "A2": "i1", "B1": "i2", "B2": "i3", "C1": "i4", "Y": "o0"}),
    "o31ai":  ("OAI31",  {"A1": "i0", "A2": "i1", "A3": "i2", "B1": "i3", "Y": "o0"}),
    "o32ai":  ("OAI32",  {"A1": "i0", "A2": "i1", "A3": "i2", "B1": "i3", "B2": "i4", "Y": "o0"}),
    # --- 順序（Q のみ出力のもの）---
    "dfxtp":  ("DFF_PC",        {"CLK": "c0", "D": "i0", "Q": "o0"}),
    "dfrtp":  ("DFF_PC_NR",     {"CLK": "c0", "D": "i0", "RESET_B": "r0", "Q": "o0"}),
    "dfstp":  ("DFF_PC_NS",     {"CLK": "c0", "D": "i0", "SET_B": "s0", "Q": "o0"}),
    "dfrtn":  ("DFF_NC_NR",     {"CLK_N": "c0", "D": "i0", "RESET_B": "r0", "Q": "o0"}),
    "sdfxtp": ("SDFF_PC",       {"CLK": "c0", "D": "i0", "SCD": "i1", "SCE": "i2", "Q": "o0"}),
    "sdfrtp": ("SDFF_PC_NR",    {"CLK": "c0", "D": "i0", "RESET_B": "r0",
                                 "SCD": "i1", "SCE": "i2", "Q": "o0"}),
    "sdfstp": ("SDFF_PC_NS",    {"CLK": "c0", "D": "i0", "SET_B": "s0",
                                 "SCD": "i1", "SCE": "i2", "Q": "o0"}),
    "dlxtp":  ("LATCH_PE",      {"D": "i0", "GATE": "c0", "Q": "o0"}),
    "dlrtp":  ("LATCH_PE_NR",   {"D": "i0", "GATE": "c0", "RESET_B": "r0", "Q": "o0"}),
    #--- ICG: charao の ICG_PC は data_in=(i0|i1) ＝ enable 2 本前提（gf180 icgtp の E/TE と同形）。
    #    TE 無しの dlclkp は 1 本しか無いため対象外（新 logic が必要）。
    "sdlclkp": ("ICG_PC", {"CLK": "c0", "GATE": "i0", "SCE": "i1", "GCLK": "o0"}),
    # --- 物理セル ---
    "fill":   ("PHYSICAL", {}),
    "decap":  ("PHYSICAL", {}),
    "tap":    ("PHYSICAL", {}),
    "tapvgnd":     ("PHYSICAL", {}),
    "tapvgnd2":    ("PHYSICAL", {}),
    "tapvpwrvgnd": ("PHYSICAL", {}),
}
SEQ_LOGIC = {"DFF_PC", "DFF_PC_NR", "DFF_PC_NS", "DFF_NC_NR", "ICG_PC",
             "SDFF_PC", "SDFF_PC_NR", "SDFF_PC_NS",
             "LATCH_PE", "LATCH_PE_NR"}

KGN_COMB = '[["leakage","0x0","d000"],["delay","7x7","d000"],["power_tout","7x7","d000"],["power_tin","7x0","d000"]]'
KGN_SEQ  = ('[["leakage","0x0","d000"],["const","7x7","d000"],["delay","7x7","d000"],'
            '["power_tout","7x7","d000"],["power_tin","7x0","d000"],'
            '["passive","7x0","d000"],["mpw","3x0","d000"]]')
KGN_PHYS = '[["leakage","0x0","d000"]]'


def load_subckts():
    d = OrderedDict()
    for line in open(SPICE, errors="ignore"):
        m = re.match(r"^\.subckt\s+(\S+)\s+(.*)$", line, re.I)
        if m:
            d[m.group(1)] = m.group(2).split()
    return d


def load_areas():
    """orig .lib から area を拾う"""
    txt = open(LIB, errors="ignore").read()
    return {m.group(1): float(m.group(2))
            for m in re.finditer(r'cell \("(\S+?)"\) \{\s*\n\s*area\s*:\s*([0-9.]+)', txt)}


def main():
    subck = load_subckts()
    areas = load_areas()
    comb, seq, phys, skipped = [], [], [], []
    for full, pins in subck.items():
        if not full.startswith(PFX):
            continue
        short = full[len(PFX):]
        base = re.sub(r"_\d+(_\d+)*$", "", short)
        if base not in MAP:
            skipped.append(short); continue
        logic, sigmap = MAP[base]
        pd = OrderedDict()
        ok = True
        for p in pins:
            if p in PWR_LOGIC:
                pd[p] = PWR_LOGIC[p]
            elif p in sigmap:
                pd[p] = sigmap[p]
            else:
                ok = False; break
        if not ok or len(pd) != len(pins):
            skipped.append(short + "(pin不一致)"); continue
        #--- ISS-00184: PHYSICAL は std_physical.jsonc へ分離し measure を持たない
        #    （gf180 の std_physical.jsonc と同じ扱い）。 model_section は
        #    「このセル群だけが r+c モデルを要する」ことの記録。
        if logic == "PHYSICAL":
            ent = (f'  {{"template_kgn":[],\n'
                   f'   "spice":"sky130_fd_sc_hd.spice","cell":"{full}","logic":"PHYSICAL",'
                   f'"area":{areas.get(full, 1.0)},\n'
                   f'   "model_section":["mos","rc"],\n'
                   f'   "ports_dict":{json.dumps(pd, ensure_ascii=False)}}},')
            phys.append(ent)
            continue
        kgn = KGN_SEQ if logic in SEQ_LOGIC else KGN_COMB
        ent = (f'  {{"template_kgn":{kgn},\n'
               f'    "spice":"sky130_fd_sc_hd.spice", "cell":"{full}","logic":"{logic}",'
               f'"area":{areas.get(full, 1.0)},\n'
               f'    "ports_dict":{json.dumps(pd, ensure_ascii=False)}}},')
        (seq if logic in SEQ_LOGIC else comb).append(ent)

    hdr = ('//===================================================================\n'
           '// This file is associated with the charao project.\n'
           '// Copyright (C) 2026 MATSUDA Masahiro\n'
           '//\n'
           '// This configuration file is licensed under the MIT License.\n'
           '//===================================================================\n'
           '// SKY130 / sky130_fd_sc_hd  (ISS-00181 Step 1、 2026-07-30 自動生成)\n'
           '//   既存の charao logic でそのまま通るセルのみを登録\n'
           '//   ports_dict は subckt のピン順どおり（chk_ports が挿入順で厳密照合するため）\n'
           '{\n'
           '"spice_path":"./sample_src/sky130A/libs.ref/sky130_fd_sc_hd/spice",\n\n'
           '"cell_info": [\n')
    for path, rows in (("std_comb.jsonc", comb), ("std_seq.jsonc", seq),
                       ("std_physical.jsonc", sorted(phys))):
        with open(f"sample_target/sky130/fd/sc_hd/{path}", "w", encoding="utf-8") as f:
            f.write(hdr + "\n".join(rows) + "\n]\n}\n")
        print(f"  {path}: {len(rows)} セル")
    print(f"  未対応でスキップ: {len(skipped)} セル")


if __name__ == "__main__":
    main()
