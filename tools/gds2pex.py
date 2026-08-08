#!/usr/bin/env python3
"""kpex（KLayout-PEX）を複数セルに対してまとめて実行する。

kpex の CLI は `--cell` を 1 つしか取らないため、セルごとに lrPymRPC を呼ぶと
**1 セルあたり約 38 秒**（pip install ＋ GDS 転送のオーバーヘッド）かかる。
抽出そのものはセルあたり約 2 秒なので、本スクリプトを**サーバ側で 1 回だけ**動かし、
その中でセルを回すことでオーバーヘッドを 1 回に畳む。

Input  : GDS ＋ セル名リスト（--cells / --cells_file）
Process: セルごとに `python3 -m klayout_pex ... --cell <name>` を実行
Output : <out_dir>/<cell>_pex.spice（＋ kpex 既定の <lib>__<cell>/ 一式）とサマリ

使用例（lrPymRPC 経由。--SOURCE に tools を足し、--SOURCE_INCLUDE に .py を足すこと）:
  python3 -m lrPymRPC --SERVER_IP 192.168.168.103 \\
    --REPO_URL klayout-pex=klayout-pex \\
    --SOURCE sample_src tools --SOURCE_INCLUDE .gds .py \\
    --SOURCE_MATCH sky130_fd_sc_hd tools \\
    --RUN_NAME run_kpex_all --RESULT kpex_out \\
    --CMD "python3 tools/gds2pex.py --gds sample_src/sky130A/libs.ref/sky130_fd_sc_hd/gds/sky130_fd_sc_hd.gds --pdk sky130A --prefix sky130_fd_sc_hd__ --out_dir kpex_out --cells inv_1 inv_2 inv_4"

  # セル名をファイルで渡す（--cells_file は 1 行 1 セル、# 以降はコメント）
  ... --CMD "python3 tools/gds2pex.py ... --cells_file tools/kpex_cells.txt"

生成した .spice は `tools/pex2spice.py` へまとめて渡せる（--in は複数指定可）:
  python3 tools/pex2spice.py --in kpex_out/*_pex.spice --ref <spice> \\
    --zero_mode merge --reconnect --out <lib>_pex.spice

詳細は docs/HOWTO_kpex.md を参照。
"""

import argparse
import os
import subprocess
import sys
import time


def load_cells(args):
    cells = list(args.cells or [])
    if args.cells_file:
        with open(args.cells_file, encoding="utf-8") as fp:
            for line in fp:
                name = line.split("#", 1)[0].strip()
                if name:
                    cells.append(name)
    #--- 重複を落としつつ順序は保つ
    seen, out = set(), []
    for c in cells:
        full = c if c.startswith(args.prefix) else args.prefix + c
        if full not in seen:
            seen.add(full)
            out.append(full)
    return out


#--- ISS-00207: 内部ネット（無名ネット）の抵抗が抽出されない上流バグへの当て木。
#    klayout_pex/klayout/lvsdb_extractor.py の shapes_of_net() は
#      requested_net_name = net.name
#    としてネット名の文字列一致で形状を拾うが、形状側のプロパティには
#    build_all_nets(netname_prop="net") が **expanded_name**（無名なら "$2"）を書く。
#    無名ネットは net.name が空文字なので 1 つも一致せず、regions が空 →
#    抵抗網が生成されない（容量側は影響を受けない）。
#    ここでは net.expanded_name() を渡すよう差し替えてから kpex の CLI を起動する。
PATCH_CODE = r'''
import sys, runpy
import klayout_pex.klayout.lvsdb_extractor as _m

_C = _m.KLayoutExtractionContext
_orig = _C.shapes_of_net

def _patched(self, gds_pair, net):
    if not isinstance(net, str) and not net.name:
        net = net.expanded_name()      # 無名ネットは "$<cluster_id>" で引く
    return _orig(self, gds_pair, net)

_C.shapes_of_net = _patched
sys.argv[0] = "klayout_pex"
runpy.run_module("klayout_pex", run_name="__main__")
'''


def run_one(cell, args):
    """1 セル分の kpex を実行し (ok, 経過秒, メッセージ) を返す。"""
    out_spice = os.path.join(args.out_dir, "%s_pex.spice" % cell[len(args.prefix):])
    launcher = ["-c", PATCH_CODE] if args.patch_unnamed_nets else ["-m", "klayout_pex"]
    cmd = [sys.executable] + launcher + [
           "--pdk", args.pdk,
           "--gds", args.gds,
           "--cell", cell,
           "--2.5D",
           "--mode", args.mode,
           "--out_dir", args.out_dir,
           "--out_spice", out_spice]
    if args.schematic:
        cmd += ["--schematic", args.schematic]
    if args.halo:
        cmd += ["--halo", args.halo]
    t0 = time.time()
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    dt = time.time() - t0
    if proc.returncode != 0:
        tail = proc.stdout.decode("utf-8", "replace").strip().splitlines()[-3:]
        return False, dt, "rc=%d : %s" % (proc.returncode, " / ".join(tail))
    if not os.path.exists(out_spice):
        return False, dt, "netlist が生成されていない: %s" % out_spice
    #--- 素子数を数えてサマリに出す（空の netlist を見逃さないため）
    kinds = {"M": 0, "X": 0, "R": 0, "C": 0}
    with open(out_spice, encoding="utf-8", errors="replace") as fp:
        for line in fp:
            head = line[:1].upper()
            if head in kinds:
                kinds[head] += 1
    return True, dt, "M=%d R=%d C=%d" % (kinds["M"] + kinds["X"], kinds["R"], kinds["C"])


def main(argv=None):
    ap = argparse.ArgumentParser(description="kpex を複数セルへまとめて適用する")
    ap.add_argument("--gds", required=True, help="ライブラリ GDS")
    ap.add_argument("--pdk", default="sky130A", help="kpex の --pdk（既定 sky130A）")
    ap.add_argument("--prefix", default="", help="セル名の共通 prefix（例 sky130_fd_sc_hd__）")
    ap.add_argument("--cells", nargs="+", help="セル名（prefix は付けても付けなくてもよい）")
    ap.add_argument("--cells_file", help="セル名を 1 行 1 個で並べたファイル（# はコメント）")
    ap.add_argument("--out_dir", default="kpex_out", help="出力先（既定 kpex_out）")
    ap.add_argument("--mode", default="RC", choices=["CC", "RC", "R"],
                    help="kpex の --mode（既定 RC）")
    ap.add_argument("--schematic", help="LVS 比較に使う回路図ネットリスト（cdl 等）。"
                                        "未指定なら kpex が dummy を自動生成する")
    ap.add_argument("--halo", help="kpex の --halo（未指定なら tech 既定）")
    ap.add_argument("--patch_unnamed_nets", action="store_true",
                    help="ISS-00207: 無名ネット（セル内部ネット）の抵抗が抽出されない上流バグを"
                         "実行時に当て木する（shapes_of_net に expanded_name を渡す）。"
                         "上流が直ったら不要になる")
    ap.add_argument("--keep_going", action="store_true",
                    help="失敗しても残りのセルを続ける（既定は最後まで走ってから集計）")
    args = ap.parse_args(argv)

    cells = load_cells(args)
    if not cells:
        print("[ERR] セルが指定されていない（--cells / --cells_file）", file=sys.stderr)
        return 1
    os.makedirs(args.out_dir, exist_ok=True)

    print("[INF] cells   : %d" % len(cells))
    print("[INF] gds     : %s" % args.gds)
    print("[INF] pdk     : %s / mode=%s" % (args.pdk, args.mode))
    print("[INF] out_dir : %s" % args.out_dir)
    if args.schematic:
        print("[INF] schematic: %s（LVS 比較あり）" % args.schematic)

    ok_list, ng_list = [], []
    t0 = time.time()
    for i, cell in enumerate(cells, 1):
        ok, dt, msg = run_one(cell, args)
        print("[%s] %3d/%3d %-40s %6.1fs  %s"
              % ("OK " if ok else "NG ", i, len(cells), cell, dt, msg), flush=True)
        (ok_list if ok else ng_list).append(cell)

    print("")
    print("===== gds2pex summary =====")
    print("  total   : %d cells / %.1f s" % (len(cells), time.time() - t0))
    print("  success : %d" % len(ok_list))
    print("  failed  : %d%s" % (len(ng_list), ("  " + " ".join(ng_list)) if ng_list else ""))
    return 1 if ng_list else 0


if __name__ == "__main__":
    sys.exit(main())
