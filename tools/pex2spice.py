#!/usr/bin/env python3
"""kpex（KLayout-PEX）の RC 抽出ネットリストを charao で使える形へ整形する。

kpex の出力はそのままでは ngspice / charao に渡せない（ISS-00203）。
本スクリプトは以下の 5 点を機械的に整形する。

  (1) 基板ポート名の置換     : sky130_gnd -> VNB（--sub_alias / --sub_port）
  (2) .SUBCKT のポート順序   : 元の spice ネットリスト（--ref）の順に並べ替える
  (3) デバイス行の書式変換   : M -> X、W/L/AS/AD/PS/PD を scale 前提の値へ換算
  (4) 抵抗行のモデル名削除   : "Rext_1 A B 24.5 R" -> "Rext_1 A B 24.5"
  (5) 0Ω 抵抗の置換          : 0 -> --rmin（既定 1e-6。0 のままだと ngspice の行列が壊れる）

  加えて、浮いている基板ノード（VSUBS）を基板ポートへ結線する
  （kpex は VSUBS を生成するだけで結線しないため、基板容量が宙に浮く）。

Input  : kpex の出力 .spice（--in、複数指定可）
Process: 上記の整形
Output : 連結した .spice（--out）＋ 整形サマリ（標準出力）

使用例:
  python3 tools/pex2spice.py \\
    --in  run_kpex_inv16/kpex_out/inv_16_pex.spice \\
    --ref sample_src/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice \\
    --out sample_src/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd_pex.spice

詳細は docs/HOWTO_kpex.md を参照。
"""

import argparse
import os
import re
import sys
from collections import defaultdict

# --- SPICE の単位接尾辞（大文字小文字は区別しない） ---
#     MEG は M より先に判定すること
SUFFIX = [
    ("MEG", 1e6),
    ("T", 1e12), ("G", 1e9), ("K", 1e3),
    ("M", 1e-3), ("U", 1e-6), ("N", 1e-9),
    ("P", 1e-12), ("F", 1e-15), ("A", 1e-18),
]

# デバイス行のパラメータ : 名前 -> (出力名, 次元)
#   len  : 長さ（scale の 1 乗で割る）
#   area : 面積（scale の 2 乗で割る）
DEV_PARAMS = {
    "W": ("w", "len"), "L": ("l", "len"),
    "AS": ("as", "area"), "AD": ("ad", "area"),
    "PS": ("ps", "len"), "PD": ("pd", "len"),
}
# 出力する順序（元の spice ネットリストに合わせて w, l を先頭に置く）
DEV_PARAM_ORDER = ["w", "l", "as", "ad", "ps", "pd"]


def parse_value(text):
    """SPICE の数値表記（例 "0.65U"）を SI 値へ変換する。"""
    s = text.strip()
    for suf, mul in SUFFIX:
        if s.upper().endswith(suf):
            head = s[: -len(suf)]
            try:
                return float(head) * mul
            except ValueError:
                break
    return float(s)


def fmt_len(param):
    """長さパラメータを元 spice と同じ表記（例 0.65 -> "650000u"）で書く。"""
    return "%gu" % (param * 1e6)


def fmt_plain(param):
    return "%.6g" % param


def join_continuations(lines):
    """継続行（行頭 '+'）を論理行へ畳み込む。戻り値は論理行のリスト。"""
    out = []
    for raw in lines:
        line = raw.rstrip("\n")
        if line.startswith("+"):
            if not out:
                raise ValueError("継続行がファイル先頭に現れた: %r" % line)
            out[-1] = out[-1].rstrip() + " " + line[1:].strip()
        else:
            out.append(line)
    return out


def wrap_line(line, width=100):
    """長い論理行を '+' 継続行へ折り返す。"""
    if len(line) <= width:
        return [line]
    tokens = line.split()
    out, cur = [], tokens[0]
    for tok in tokens[1:]:
        if len(cur) + 1 + len(tok) > width:
            out.append(cur)
            cur = "+ " + tok
        else:
            cur += " " + tok
    out.append(cur)
    return out


def read_ref_ports(ref_path):
    """元の spice ネットリストから {subckt 名: [ポート順]} を読む。"""
    ports = {}
    with open(ref_path, encoding="utf-8", errors="replace") as fp:
        for line in join_continuations(fp.readlines()):
            if line.lower().startswith(".subckt"):
                tok = line.split()
                if len(tok) >= 2:
                    ports[tok[1]] = tok[2:]
    return ports


class Stats:
    def __init__(self):
        self.subckt = []          # (cell, reordered?)
        self.dev = 0              # M -> X
        self.res = 0              # 抵抗行
        self.res_zero = 0         # 0Ω 置換
        self.cap = 0              # 容量行
        self.subs_fix = []        # VSUBS を結線したセル
        self.renamed = 0          # 基板ノード名の置換箇所
        self.reconnect = []       # (net, layer, kind, 端子数)
        self.reconnect_terms = 0  # 張り替えた端子の総数
        self.merged = 0           # 統合した 0Ω 抵抗の本数
        self.merged_nodes = 0     # 統合で消えたノード数
        self.merged_selfloop = 0  # 統合の結果 両端が同じになって落とした素子
        self.no_mesh = []         # (net, 端子数) メッシュが無く再接続できなかったネット


def convert_device(line, args, stats):
    """M 行を X 行（.subckt 呼び出し）へ変換する。"""
    tok = line.split()
    name, rest = tok[0], tok[1:]

    # ノード群 + モデル名 + パラメータ（name=value）に分解する
    nodes = []
    model = None
    params = {}
    for item in rest:
        if "=" in item:
            key, val = item.split("=", 1)
            params[key.upper()] = val
        elif model is None and len(nodes) >= 4:
            model = item
        else:
            nodes.append(item)
    if model is None:
        raise ValueError("モデル名を特定できない: %r" % line)

    out_params = {}
    for key, val in params.items():
        if key not in DEV_PARAMS:
            raise ValueError("未知のデバイスパラメータ %s: %r" % (key, line))
        out_name, dim = DEV_PARAMS[key]
        si = parse_value(val)
        scale = args.scale ** (2 if dim == "area" else 1)
        param = si / scale
        out_params[out_name] = fmt_len(param) if out_name in ("w", "l") else fmt_plain(param)

    body = " ".join(["X" + name[1:]] + nodes + [model])
    for key in DEV_PARAM_ORDER:
        if key in out_params:
            body += " %s=%s" % (key, out_params[key])
    stats.dev += 1
    return body


def convert_resistor(line, args, stats):
    """抵抗行の末尾モデル名を削り、0Ω を rmin へ置換する。"""
    tok = line.split()
    # 末尾がモデル名（数値でない）なら削る
    if len(tok) >= 5:
        try:
            float(tok[-1])
        except ValueError:
            tok = tok[:-1]
    if len(tok) < 4:
        raise ValueError("抵抗行を解釈できない: %r" % line)
    if float(tok[3]) == 0.0:
        #--- merge モードでは値 0 のまま残し、後段の union-find でノードを統合する
        tok[3] = "0" if args.zero_mode == "merge" else args.rmin
        stats.res_zero += 1
    stats.res += 1
    return " ".join(tok[:4])


def merge_zero_nodes(lines, stats):
    """値 0 の抵抗を「ノードの同一視」として扱い、union-find で統合して行を削除する。

    1e-6Ω 等の微小抵抗で代用すると、メッシュが導通したときに
    抵抗値レンジが 9 桁になって ngspice の行列が硬くなる（`Timestep too small`）。
    短絡は短絡として畳むのが正しい。
    """
    parent = {}
    ports = set()
    for line in lines:
        tok = line.split()
        if tok and tok[0].lower() == ".subckt":
            ports.update(tok[2:])

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def rank(n):
        """代表に選ぶ優先度（大きいほど優先）：ポート名 > 主ネット名 > サブノード名。"""
        return (2 if n in ports else 0) + (1 if "." not in n else 0)

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if rank(rb) > rank(ra):
            ra, rb = rb, ra
        parent[rb] = ra

    zeros = []
    for i, line in enumerate(lines):
        tok = line.split()
        if tok and tok[0][0].upper() == "R" and len(tok) >= 4:
            try:
                if float(tok[3]) == 0.0:
                    zeros.append(i)
                    union(tok[1], tok[2])
            except ValueError:
                pass
    if not zeros:
        return lines

    out = []
    drop = set(zeros)
    for i, line in enumerate(lines):
        if i in drop:
            continue
        tok = line.split()
        if tok and tok[0][0].upper() in ("R", "C", "X", "M") and not line.startswith("*"):
            end = 4 if tok[0][0].upper() in ("R", "C") else len(tok)
            for j in range(1, min(end, len(tok))):
                if "=" in tok[j]:
                    break
                if tok[j] in parent:
                    tok[j] = find(tok[j])
            line = " ".join(tok)
        out.append(line)
    #--- 統合で両端が同じになった抵抗・容量を落とす
    kept = []
    for line in out:
        tok = line.split()
        if tok and tok[0][0].upper() in ("R", "C") and len(tok) >= 4 and tok[1] == tok[2]:
            stats.merged_selfloop += 1
            continue
        kept.append(line)
    stats.merged += len(zeros)
    stats.merged_nodes += len({n for n in parent if find(n) != n})
    return kept


def process_file(path, ref_ports, args, stats):
    with open(path, encoding="utf-8", errors="replace") as fp:
        lines = join_continuations(fp.readlines())

    out = []
    cell = None
    subs_nodes = set()   # 現 subckt 内で見た VSUBS 系ノード
    port_names = []

    for line in lines:
        stripped = line.strip()

        # --- コメント・空行はそのまま ---
        if not stripped or stripped.startswith("*"):
            out.append(line)
            continue

        # --- (1) 基板ポート名の置換（全行が対象） ---
        new_line, n = re.subn(r"(?<![\w.$])%s(?![\w.$])" % re.escape(args.sub_alias),
                              args.sub_port, line)
        stats.renamed += n
        line = new_line
        stripped = line.strip()
        head = stripped.split()[0]

        if stripped.lower().startswith(".subckt"):
            tok = stripped.split()
            cell = tok[1]
            port_names = tok[2:]
            subs_nodes = set()
            # --- (2) ポート順序を元 spice に合わせる ---
            reordered = False
            if cell in ref_ports:
                want = ref_ports[cell]
                if sorted(want) != sorted(port_names):
                    raise ValueError(
                        "ポート集合が元 spice と一致しない\n"
                        "  cell = %s\n  kpex = %s\n  ref  = %s" % (cell, port_names, want))
                if want != port_names:
                    port_names = want
                    reordered = True
            elif not args.allow_missing_ref:
                raise ValueError("元 spice に %s が見つからない（--allow_missing_ref で無視可）" % cell)
            stats.subckt.append((cell, reordered))
            out.append(".SUBCKT %s %s" % (cell, " ".join(port_names)))
            continue

        if stripped.lower().startswith(".ends"):
            # --- 浮いている基板ノードを結線する ---
            floating = sorted(n for n in subs_nodes if n not in port_names)
            for node in floating:
                #--- merge モードでは値 0 で出し、union-find で基板ポートへ畳む
                val = "0" if args.zero_mode == "merge" else args.rmin
                out.append("R%s_fix %s %s %s" % (node.lower(), node, args.sub_port, val))
                stats.subs_fix.append((cell, node))
            out.append(stripped)
            cell = None
            continue

        if head[0].upper() == "M":
            body = convert_device(stripped, args, stats)
        elif head[0].upper() == "R":
            body = convert_resistor(stripped, args, stats)
        elif head[0].upper() == "C":
            stats.cap += 1
            body = stripped
        else:
            body = stripped

        for node in body.split()[1:4]:
            if node.upper().startswith(args.subs_node.upper()):
                subs_nodes.add(node)
        out.append(body)

    return out


#--- ISS-00205: デバイス端子を抵抗メッシュのノードへ張り替える ────────────────
#    kpex はメッシュを正しく作る（`<net>.P<n>.<layer>` がデバイス端子）が、
#    デバイスは元のネット名に付いたままなので、抵抗が電流経路に入らない。

P_NODE = re.compile(r"^(?P<net>[^.]+)\.P(?P<idx>\d+)\.(?P<layer>\d+)$")


def _device_kind(model):
    """モデル名からデバイス種別を推定する（pfet / nfet / その他はモデル名そのまま）。"""
    low = model.lower()
    for kind in ("pfet", "nfet"):
        if kind in low:
            return kind
    return low


def reconnect_devices(lines, args, stats):
    """`.P*` ノードへデバイス端子を割り当て直す。lines は論理行のリスト。"""
    ports = []
    pools = {}          # (net, layer) -> [node, ...]
    devices = []        # (行番号, tokens, model, kind)
    for i, line in enumerate(lines):
        tok = line.split()
        if not tok:
            continue
        if tok[0].lower() == ".subckt":
            ports = tok[2:]
        elif tok[0][0].upper() == "R":
            for node in tok[1:3]:
                m = P_NODE.match(node)
                if m:
                    pools.setdefault((m.group("net"), m.group("layer")), set()).add(node)
        elif tok[0][0].upper() == "X":
            model = next((t for t in tok[5:] if "=" not in t), tok[5])
            devices.append((i, tok, model, _device_kind(model)))
    if not devices:
        return lines
    pools = {k: sorted(v, key=lambda n: int(P_NODE.match(n).group("idx"))) for k, v in pools.items()}

    #--- 端子の要求を集計する。d/g/s の 3 端子のみ（bulk はメッシュを持たない）
    want = defaultdict(list)          # (net, kind) -> [(行番号, 端子位置), ...]
    for i, tok, _model, kind in devices:
        for pos in (1, 2, 3):
            want[(tok[pos], kind)].append((i, pos))

    #--- 層 → デバイス種別の対応を、曖昧さの無いネットから学習する
    #    （例：VPWR には pMOS の端子しか無く、層プールも 1 つ → その層は pMOS 側）
    layer_kind = {}
    for net in {n for n, _k in want}:
        kinds = {k for n, k in want if n == net}
        layers = [l for (nn, l) in pools if nn == net]
        if len(kinds) == 1 and len(layers) == 1:
            layer_kind.setdefault(layers[0], kinds.pop())

    assigned = 0
    for net in sorted({n for n, _k in want}):
        layers = sorted(l for (nn, l) in pools if nn == net)
        if not layers:
            #--- メッシュを持たないネット。bulk（VPB/VNB）のほか、
            #    **kpex がポート以外のネットの抵抗を抽出しない**ため内部ネットが該当する。
            #    黙って飛ばすと「再接続できた」と誤読するので必ず集計して報告する。
            n_term = sum(len(v) for (nn, _k), v in want.items() if nn == net)
            if net not in ports:
                stats.no_mesh.append((net, n_term))
            continue
        kinds = sorted({k for n, k in want if n == net})
        #--- 層が 1 つしか無いネット（ゲート側など）は全種別で 1 プールを共有する
        if len(layers) == 1:
            groups = [(kinds, layers[0], [t for k in kinds for t in want[(net, k)]])]
        else:
            #--- 種別ごとに使う層を決める
            use = {}
            for kind in kinds:
                cand = [l for l in layers if layer_kind.get(l) == kind]
                if len(cand) != 1:
                    #--- 学習で決まらなければ要求数とプール数の一致で決める
                    cand = [l for l in layers
                            if len(pools[(net, l)]) == len(want[(net, kind)])
                            and l not in use.values()]
                if len(cand) != 1:
                    raise ValueError(
                        "端子とメッシュ層の対応を決められない（net=%s kind=%s 層候補=%s）。"
                        "--reconnect を外すか、層の割当を確認すること" % (net, kind, layers))
                use[kind] = cand[0]
            groups = [([k], use[k], want[(net, k)]) for k in kinds]

        for kinds_here, layer, terms in groups:
            pool = list(pools[(net, layer)])
            kind = "+".join(kinds_here)
            if len(pool) != len(terms):
                raise ValueError(
                    "端子数とメッシュノード数が一致しない（net=%s kind=%s 端子=%d ノード=%d）"
                    % (net, kind, len(terms), len(pool)))
            if args.reconnect_order == "reverse":
                pool.reverse()
            for (i, pos), node in zip(terms, pool):
                tok = lines[i].split()
                tok[pos] = node
                lines[i] = " ".join(tok)
                assigned += 1
            stats.reconnect.append((net, layer, kind, len(terms)))
    stats.reconnect_terms += assigned
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description="kpex の RC 抽出ネットリストを charao 用に整形する")
    ap.add_argument("--in", dest="inputs", nargs="+", required=True,
                    help="kpex の出力 .spice（複数指定すると 1 ファイルへ連結する）")
    ap.add_argument("--out", required=True, help="出力 .spice")
    ap.add_argument("--ref", help="元の spice ネットリスト（.SUBCKT のポート順の基準）")
    ap.add_argument("--sub_alias", default="sky130_gnd",
                    help="kpex が付ける基板ポート名（既定 sky130_gnd）")
    ap.add_argument("--sub_port", default="VNB",
                    help="置き換え後の基板ポート名（既定 VNB）")
    ap.add_argument("--subs_node", default="VSUBS",
                    help="kpex が生成する浮いた基板ノード名（既定 VSUBS）")
    ap.add_argument("--rmin", default="1e-6",
                    help="0Ω 抵抗の置換値と結線抵抗の値（既定 1e-6。--zero_mode resistor のとき有効）")
    ap.add_argument("--zero_mode", choices=["resistor", "merge"], default="resistor",
                    help="0Ω 抵抗の扱い。resistor＝--rmin の微小抵抗で代用（既定）／"
                         "merge＝union-find でノードを統合する。"
                         "**--reconnect と併用するときは merge が必須**"
                         "（メッシュが導通すると微小抵抗が行列を硬くし `Timestep too small` になる）")
    ap.add_argument("--scale", type=float, default=1e-6,
                    help="config_lib.jsonc / all.spice の .option scale（既定 1e-6）")
    ap.add_argument("--allow_missing_ref", action="store_true",
                    help="--ref に無い subckt があってもエラーにしない（ポート順は kpex のまま）")
    ap.add_argument("--reconnect", action="store_true",
                    help="デバイス端子を抵抗メッシュの `<net>.P<n>.<layer>` ノードへ張り替える"
                         "（ISS-00205。既定 off ＝ kpex の出力どおり＝抵抗が電流経路に入らない）")
    ap.add_argument("--reconnect_order", choices=["index", "reverse"], default="index",
                    help="--reconnect で端子へノードを割り当てる順序。並び順の任意性が"
                         "結果に効くかを見るために reverse を用意している（既定 index）")
    args = ap.parse_args(argv)

    ref_ports = read_ref_ports(args.ref) if args.ref else {}
    if args.ref and not ref_ports:
        print("[ERR] --ref から .subckt を 1 つも読めなかった: %s" % args.ref, file=sys.stderr)
        return 1
    if not args.ref and not args.allow_missing_ref:
        print("[ERR] --ref が未指定。ポート順を揃えないなら --allow_missing_ref を付けること",
              file=sys.stderr)
        return 1

    stats = Stats()
    body = []
    for path in args.inputs:
        if not os.path.exists(path):
            print("[ERR] 入力が無い: %s" % path, file=sys.stderr)
            return 1
        try:
            lines = process_file(path, ref_ports, args, stats)
            #--- 順序が重要：先に統合すると短絡された `.P*` ノードが畳まれ、
            #    端子とメッシュノードの対応が取れなくなる。再接続してから統合する。
            if args.reconnect:
                lines = reconnect_devices(lines, args, stats)
            if args.zero_mode == "merge":
                lines = merge_zero_nodes(lines, stats)
            body.extend(lines)
        except ValueError as exc:
            print("[ERR] %s: %s" % (path, exc), file=sys.stderr)
            return 1

    wrapped = []
    for line in body:
        wrapped.extend(wrap_line(line) if line.strip() and not line.startswith("*") else [line])
    with open(args.out, "w", encoding="utf-8") as fp:
        fp.write("\n".join(wrapped).rstrip("\n") + "\n")

    # --- 整形サマリ ---
    print("[INF] output          : %s" % args.out)
    print("[INF] scale           : %g (len /scale, area /scale^2)" % args.scale)
    for cell, reordered in stats.subckt:
        print("[INF] subckt          : %s (port order %s)"
              % (cell, "reordered to ref" if reordered else "unchanged"))
    print("[INF] device M -> X   : %d" % stats.dev)
    if args.zero_mode == "merge":
        print("[INF] resistor        : %d (zero-ohm merged : %d -> %d node(s) collapsed, "
              "self-loop dropped : %d)"
              % (stats.res, stats.merged, stats.merged_nodes, stats.merged_selfloop))
    else:
        print("[INF] resistor        : %d (zero-ohm replaced by %s : %d)"
              % (stats.res, args.rmin, stats.res_zero))
    print("[INF] capacitor       : %d" % stats.cap)
    print("[INF] %-6s -> %-6s: %d node(s) renamed" % (args.sub_alias, args.sub_port, stats.renamed))
    if args.reconnect:
        print("[INF] reconnect      : %d terminals (order=%s)"
              % (stats.reconnect_terms, args.reconnect_order))
        for net, layer, kind, n in stats.reconnect:
            print("[INF]   %-6s layer %-3s -> %-5s : %d terminal(s)" % (net, layer, kind, n))
        if stats.no_mesh:
            total = sum(n for _net, n in stats.no_mesh)
            print("[WARN] no resistance mesh : %d net(s) / %d terminal(s) left on the plain net"
                  % (len(stats.no_mesh), total))
            print("[WARN]   %s" % " ".join("%s(%d)" % (net, n) for net, n in stats.no_mesh))
            print("[WARN]   kpex はポート以外のネットの抵抗を抽出しない（内部ネットは寄生 R 無し）")
    if stats.subs_fix:
        for cell, node in stats.subs_fix:
            print("[INF] floating node   : %s.%s tied to %s via %s"
                  % (cell, node, args.sub_port, args.rmin))
    else:
        print("[INF] floating node   : none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
