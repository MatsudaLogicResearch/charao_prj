#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
util_make_template4json.py — 実測から config_lib.jsonc の templates を決める（ISS-00189）

【考え方】

orig .lib が無い PDK でも template を作れるようにする。SKY130 orig を解析した結果、
template の構造は次のとおりだった（経緯は ISS-00189、確定仕様は SPEC_config_lib.md）。

  * index_1 / index_2 とも **完全な等比級数**（SKY130 orig 1,261 arc でズレ 0.000%）
    → min / max / 点数が決まれば軸全体が一意に決まる
  * **セル依存なのは index_2 の max だけ**。それは max_capacitance ＝
    「出力 transition が max_transition になる負荷」で、駆動能力（出力抵抗）で決まる
  * 他の kind は delay から派生できる
      power_tout : delay と同一（kind は分けないと measure が走らないので別エントリで出す）
      power_tin  : index_1 のみ、1 種
      passive    : index_1 のみ、1 種
      const      : index_1 x index_1、1 種
      mpw        : index_1 の [0],[3],[6]、1 種
      leakage    : index なし、1 種

【使い方（4 stage。 sim は charao 本体に通すので tb の作り方が本番と完全に一致する）】

  # ① 探索用の暫定 template を書く（幅広の 1 種）
  python -m charao.script.util_make_template4json --stage 1.probe \\
      --config sample_target/sky130/fd/sc_hd/config_lib.jsonc

  # → charao を inv_1 だけ実行（リモート）
  #   CELLS="inv_1" bash debug_run.sh run_all

  # ② 結果を見る（in_cap と、fanout ごとの cell_rise transition）
  python -m charao.script.util_make_template4json --stage 2.report \\
      --lib run_x/rslt/xxx.lib --cell sky130_fd_sc_hd__inv_1 --fanout 80,100,200

  # ③ ユーザが決めた値で全セル測定用の暫定 template を書く
  python -m charao.script.util_make_template4json --stage 3.scan \\
      --jsonc_in <in> --jsonc_out <out> --slew_in 1.5 --load_out 0.16 --load_limit 5.0

  # → charao を全セル実行（リモート）

  # ④ 各セル/出力ピンの max_cap を求めてグループ化し、本番 template を書く
  python -m charao.script.util_make_template4json --stage 4.build \\
      --lib run_y/rslt/xxx.lib --jsonc_in <in> --jsonc_out <out> \\
      --slew_min_max_num 0.01,1.5,7 --load_min_max_num 0.0005,5.0,7 --tolerance 0.05

【決めごと（2026-08-01 ダーマツ判断）】

  * 基準セルは inv_1、**cell_rise のみ**で max_cap を決める
  * step ③ の入力 slew は **max slew**（index_1[max]）。orig の max_cap もこの条件
  * index_1[0] / index_1[max] / index_2[0] は **絶対値でユーザが指定**する
    （in_cap は判断材料として表示するだけ）
  * template 名は **index_2 の max 値（有効 3 桁）**。小数点は 'p' に置換
      0.0211 pF -> d0p0211 ／ 0.178 pF -> d0p178 ／ 5.0 pF -> d5
    値が同じなら名前も同じになるので、**セルを追加して再生成しても既存の割当が動かない**
    （通し番号 dXX は再生成で総入れ替えになるため採らない）
"""

import argparse
import math
import sys
import re
import shutil
from pathlib import Path

from charao.script.util_liberty import parse_lib_file


# ── 数値ユーティリティ ────────────────────────────────────────────────────

def sig3(x, digits=3):
    """有効 <digits> 桁へ丸める（SPEC_config_lib.md 3.3）。"""
    x = float(x)
    if x == 0:
        return 0.0
    d = digits - int(math.floor(math.log10(abs(x)))) - 1
    v = round(x, d)
    return int(v) if v == int(v) and abs(v) >= 1 else v


def geom(vmin, vmax, n):
    """min→max の等比 n 点（有効 3 桁）。"""
    if n < 2:
        return [sig3(vmin)]
    r = (vmax / vmin) ** (1.0 / (n - 1))
    return [sig3(vmin * (r ** i)) for i in range(n)]


def tname(index2_max):
    """template 名 = index_2 の max（有効 3 桁）。小数点は 'p'。"""
    v = sig3(index2_max)
    return "d" + ("%g" % v).replace(".", "p").replace("-", "m")


def _fmt(vals):
    return ",".join("%g" % v for v in vals)


# ── .lib から実測値を読む ─────────────────────────────────────────────────

def load_measured(lib_path):
    """charao 出力 .lib から (in_cap, transition テーブル) を読む。

    返り値:
      caps  : {cell: {pin: capacitance(pF)}}
      trans : {(cell, pin): {(slew, load): rise_transition}}
    """
    _units, _scales, _leak, _power, timing_rows = parse_lib_file(Path(lib_path))
    trans = {}
    for r in timing_rows:
        if r.get("table_type") != "rise_transition":
            continue
        i1, i2 = r.get("index1 (ns)"), r.get("index2 (pF)")
        if i1 == "NaN" or i2 == "NaN":
            continue
        try:
            k = (r["cell_name"], r["pin"])
            trans.setdefault(k, {})[(float(i1), float(i2))] = float(r["value (ns)"])
        except (TypeError, ValueError):
            continue

    # capacitance は .lib を直接読む（CSV 化の対象外のため）
    caps = {}
    cell = pin = None
    for ln in Path(lib_path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r'\s*cell \(([^)]+)\)', ln)
        if m:
            cell = m.group(1).strip().strip('"')
            pin = None
            continue
        m = re.match(r'\s*pin \(([^)]+)\)', ln)
        if m:
            pin = m.group(1).strip().strip('"')
            continue
        if cell and pin:
            m = re.match(r'\s*capacitance\s*:\s*"?([0-9.eE+-]+)"?', ln)
            if m:
                caps.setdefault(cell, {})[pin] = float(m.group(1))
    return caps, trans


def cap_at_transition(rows, slew, target):
    """入力 slew を固定した行から、transition == target となる load を求める。

    transition は load にほぼ線形（SKY130 inv_1 で load 11 倍 → transition 11 倍）なので
    直近 2 点の線形フィットで内挿／外挿する。
    """
    pts = sorted((l, v) for (s, l), v in rows.items() if abs(s - slew) < 1e-12)
    if len(pts) < 2:
        return None
    # target を挟む区間があればそこで内挿、無ければ末尾 2 点で外挿
    seg = None
    for i in range(len(pts) - 1):
        if (pts[i][1] - target) * (pts[i + 1][1] - target) <= 0:
            seg = (pts[i], pts[i + 1])
            break
    if seg is None:
        seg = (pts[-2], pts[-1])
    (x0, y0), (x1, y1) = seg
    if y1 == y0:
        return None
    return x0 + (target - y0) * (x1 - x0) / (y1 - y0)


# ── templates セクションの生成 ────────────────────────────────────────────

def build_templates(index_1, groups, indent="    ", names=None,
                    index_1s=None, limits=None):
    """index_1 と groups（index_2 のリスト）から templates 本体を組む。

    groups は index_2 リストの列。delay / power_tout が同数、他は 1 種。

    ISS-00191: `--scan_spec` でセル別 `slew_in`（＝ max_transition）を指定できるため、
    delay / power_tout の index_1 はグループごとに変わりうる。`index_1s` にグループ別の
    index_1 を渡すとそれを使う（None なら全グループ共通の `index_1`）。
    delay / power_tout **以外**の kind（leakage / passive / mpw / const / power_tin）は
    従来どおりライブラリ共通で、既定側の `index_1` を使う。

    `limits` を渡すとグループごとの load_limit を `//@limit` コメントで書き残す。
    4.analyze が再指定なしで読めるようにするため（Y 案）。
    """
    i1 = _fmt(index_1)
    n1 = len(index_1)
    n2 = len(groups[0]) if groups else 0
    L = ["\n"]
    a = lambda s: L.append(indent + s + "\n")

    a('//---- index_1 は delay / power_tout のみセル別になりうる（ISS-00191 の --scan_spec）。')
    a('//     他の kind はライブラリ共通。 index_2 は delay / power_tout のみセル別（ISS-00189）')
    a('{"kind":"leakage"   ,"grid":"0x0","name":"d000","index_1":[], "index_2":[]}')
    a(',{"kind":"passive"   ,"grid":"%dx0","name":"d000","index_1":[%s], "index_2":[]}' % (n1, i1))
    mp = [index_1[0], index_1[len(index_1) // 2], index_1[-1]]
    a(',{"kind":"mpw"       ,"grid":"3x0","name":"d000","index_1":[%s], "index_2":[]}' % _fmt(mp))
    a(',{"kind":"const"     ,"grid":"%dx%d","name":"d000","index_1":[%s],"index_2":[%s]}' % (n1, n1, i1, i1))
    a(',{"kind":"power_tin" ,"grid":"%dx0","name":"d000","index_1":[%s], "index_2":[]}' % (n1, i1))
    L.append("\n")

    nm = names if names else [tname(g[-1]) for g in groups]
    g_i1 = index_1s if index_1s else [index_1] * len(groups)
    g_lim = limits if limits else [None] * len(groups)

    def _emit(kind, label):
        a(label)
        for g, t, gi1, lim in zip(groups, nm, g_i1, g_lim):
            note = ""
            if lim is not None:
                #--- Y 案: load_limit を config に書き残す。 4.analyze が読む
                note = '   //@limit=%s' % _fmt([lim])
            a(',{"kind":"%s","grid":"%dx%d","name":"%s","index_1":[%s],"index_2":[%s]}%s'
              % (kind, len(gi1), n2, t, _fmt(gi1), _fmt(g), note))

    _emit("delay     ", '//---- delay : %d groups' % len(groups))
    L.append("\n")
    _emit("power_tout",
          '//---- power_tout : delay と同一（kind を分けないと measure が走らないため別エントリ）')
    L.append(indent + "  ")
    return "".join(L)


def parse_scan_spec(specs):
    """--scan_spec のリストを解釈する（ISS-00191）。

    書式 : slew_in/load_out/load_limit[/cell]

      slew_in    … 目標 transition（＝ max_transition）。 index_1 の上端になる
      load_out   … index_2 の初期 load
      load_limit … 探索の上限（空文字なら無制限）
      cell       … 適用するセル名（**1 つだけ**）。 省略するとデフォルト

    セル名を省いたエントリが **デフォルト**で、必ず 1 つ必要。
    セル名付きのエントリはそのセルだけに効く（同じセルの重複指定はエラー）。

    戻り値 : (default_spec, {cell: spec})   spec = dict(slew_in, load_out, load_limit)
    """
    default = None
    per_cell = {}
    for s in specs:
        f = [x.strip() for x in str(s).split("/")]
        if len(f) < 3 or len(f) > 4:
            raise SystemExit(
                "--scan_spec は slew_in/load_out/load_limit[/cell] の形式"
                "（指定: %s）" % s)
        try:
            d = dict(slew_in=float(f[0]), load_out=float(f[1]),
                     load_limit=(float(f[2]) if f[2] else None))
        except ValueError:
            raise SystemExit("--scan_spec の数値が読めない（指定: %s）" % s)
        if d["slew_in"] <= 0 or d["load_out"] <= 0:
            raise SystemExit("--scan_spec の slew_in / load_out は正の数（指定: %s）" % s)
        if len(f) == 3 or not f[3]:
            if default is not None:
                raise SystemExit("--scan_spec のデフォルト（セル名なし）が 2 つ以上ある")
            default = d
        else:
            cell = f[3]
            if "," in cell:
                raise SystemExit(
                    "--scan_spec のセル指定は 1 つだけ。 複数指定するときは "
                    "--scan_spec を繰り返す（指定: %s）" % s)
            if cell in per_cell:
                raise SystemExit("--scan_spec で同じセルが 2 回指定されている: %s" % cell)
            per_cell[cell] = d
    if default is None:
        raise SystemExit("--scan_spec にデフォルト（セル名なしのエントリ）が要る")
    return default, per_cell


def spec_of(cell, default, per_cell):
    """セル名から spec を引く。 フル名・短縮名のどちらでも当たるようにする。"""
    if cell in per_cell:
        return per_cell[cell]
    short = cell.split("__")[-1]
    return per_cell.get(short, default)


#--- config に書き残した load_limit を読む（Y 案。 4.analyze が再指定なしで使う）
_LIMIT_RE = re.compile(r'"kind":"delay\s*"[^}]*?"name":"([^"]*)"[^}]*?\}\s*//@limit=([0-9.eE+-]+)')


def read_limits(config_text):
    """{template 名: load_limit} を config のコメントから読む。"""
    return {m.group(1): float(m.group(2)) for m in _LIMIT_RE.finditer(config_text)}


def read_index1(config_text):
    """{template 名: index_1 の最大値} を delay エントリから読む。"""
    out = {}
    for m in re.finditer(r'"kind":"delay\s*"[^}]*?"name":"([^"]*)"[^}]*?"index_1":\[([^\]]*)\]',
                         config_text):
        vals = [float(x) for x in m.group(2).split(",") if x.strip()]
        if vals:
            out[m.group(1)] = max(vals)
    return out


def write_templates(config_path, body, backup=False):
    """config_lib.jsonc の "templates" :[ ... ] を差し替える。"""
    p = Path(config_path)
    s = p.read_text(encoding="utf-8")
    m = re.search(r'("templates"\s*:\s*)\[', s)
    if not m:
        raise ValueError('"templates" が見つからない: %s' % config_path)
    i = m.end() - 1
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "[":
            depth += 1
        elif s[j] == "]":
            depth -= 1
            if depth == 0:
                break
    else:
        raise ValueError("templates の ] が見つからない")
    if backup:
        shutil.copy(p, str(p) + ".bak")
    p.write_text(s[:i + 1] + body + s[j:], encoding="utf-8")




# ── std_*.jsonc の template_kgn 書き換え ──────────────────────────────────

_KGN_RE = re.compile(r'"template_kgn"\s*:\s*\[(.*?)\]\s*,\s*$')
_CELL_RE = re.compile(r'"cell"\s*:\s*"([^"]+)"')
_PORTS_RE = re.compile(r'"ports_dict"\s*:\s*\{([^}]*)\}')


def _cell_of(lines, i):
    """template_kgn 行 i の近傍から cell 名を拾う（cell は次行にあるため）。"""
    for j in range(i, min(i + 4, len(lines))):
        m = _CELL_RE.search(lines[j])
        if m:
            return m.group(1)
    return None


def _ports_of(lines, i):
    """cell 行 i の近傍から ports_dict を拾い、{pin: logic_port} を返す。"""
    for j in range(i, min(i + 4, len(lines))):
        m = _PORTS_RE.search(lines[j])
        if m:
            d = {}
            for kv in re.finditer(r'"([^"]+)"\s*:\s*"([^"]+)"', m.group(1)):
                d[kv.group(1)] = kv.group(2)
            return d
    return {}


def rewrite_kgn(jsonc_path, resolve, n1, n2, dry_run=False, backup=True):
    """std_*.jsonc の template_kgn を書き換える。

    resolve(cell, logic_port) -> template 名 or None
      None を返したら、そのセルは cell 単位（第 4 要素なし）で既定名を使う。
    delay / power_tout 以外は d000 に統一する（1 種しか作らないため）。
    """
    p = Path(jsonc_path)
    lines = p.read_text(encoding="utf-8").splitlines(True)
    out = []
    n_changed = 0
    for i, ln in enumerate(lines):
        mk = _KGN_RE.search(ln.rstrip("\n"))
        cell = _cell_of(lines, i) if mk else None
        if not mk or not cell:
            out.append(ln)
            continue
        kinds = [m.group(1) for m in re.finditer(r'\["([a-z_]+)"', mk.group(1))]
        ports = _ports_of(lines, i)
        oports = sorted({v for v in ports.values() if v.startswith("o")})

        ent = []
        for k in kinds:
            if k in ("delay", "power_tout"):
                grid = "%dx%d" % (n1, n2)
                # 出力 port ごとに template が違うなら第 4 要素を付ける
                names = {op: resolve(cell, op) for op in oports}
                names = {op: nm for op, nm in names.items() if nm}
                if len(set(names.values())) > 1:
                    for op in sorted(names):
                        ent.append('["%s","%s","%s","%s"]' % (k, grid, names[op], op))
                    continue
                nm = next(iter(names.values()), None) or resolve(cell, None) or "d000"
                ent.append('["%s","%s","%s"]' % (k, grid, nm))
            elif k == "leakage":
                ent.append('["leakage","0x0","d000"]')
            elif k == "mpw":
                ent.append('["mpw","3x0","d000"]')
            elif k == "const":
                ent.append('["const","%dx%d","d000"]' % (n1, n1))
            else:                                   # passive / power_tin / その他 1D
                ent.append('["%s","%dx0","d000"]' % (k, n1))

        new = '"template_kgn":[' + ",".join(ent) + '],'
        ln2 = ln[:mk.start()] + new + "\n"
        if ln2 != ln:
            n_changed += 1
        out.append(ln2)
    if not dry_run:
        if backup:
            shutil.copy(p, str(p) + ".bak")
        p.write_text("".join(out), encoding="utf-8")
    return n_changed


# ── stage ────────────────────────────────────────────────────────────────

def _logfile(a):
    """stage の記録先。 jsonc と同じフォルダに置く（すぐ探せるように）。

    1.probe/2.report は 2.report.log、 3.scan/4.analyze は 4.analyze.log、
    5.build は 5.build.log。 1 サイクルぶんだけ残る（先頭 stage が上書きで開始）。
    """
    d = getattr(a, "jsonc_out", None)
    if not d:
        return None
    st = getattr(a, "stage", "")
    if st in ("1.probe", "2.report"):
        name = "2.report.log"
    elif st == "3.scan":
        name = "3.scan.log"
    elif st == "4.analyze":
        #--- 反復ごとにファイルを分ける（--iter で番号を渡す）
        name = "4.analyze_%d.log" % getattr(a, "iter", 1)
    else:
        name = "5.build.log"
    return Path(d) / name


def _log(a, lines, header=None, truncate=False):
    """実行コマンドと結果を jsonc と同じフォルダの 1.report.log に残す。"""
    p = _logfile(a)
    if p is None:
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    cmd = "python -m charao.script.util_make_template4json " + " ".join(
        (x if x.startswith("-") else '"%s"' % x if " " in x else x) for x in sys.argv[1:])
    #--- 1 フロー（1.probe -> charao -> 2.report）ごとに作り直す。
    #    1.probe が上書きで開始し、 2.report が追記する。
    with open(p, "w" if truncate else "a", encoding="utf-8") as f:
        if header:
            f.write("\n" + "=" * 78 + "\n%s\n" % header + "=" * 78 + "\n")
        f.write("[cmd] %s\n" % cmd)
        for ln in lines:
            f.write("      %s\n" % ln)
    print("  記録 : %s" % p)


def _prepare_out(a):
    """--jsonc_in の jsonc 一式を --jsonc_out へ複製し、(config, cell jsonc 群) を返す。

    ISS-00189: **入力フォルダは書き換えない**。 更新結果は --jsonc_out に出し、
    それが次 stage の --jsonc_in になる（1.probe -> 3.scan -> 4.build のパイプライン）。
    charao 本体と同じく config_lib.jsonc と <cell_group>*.jsonc が同居する
    <target>/<fab>/<vendor>/<rev> フォルダを丸ごと扱う。
    """
    src = Path(a.jsonc_in)
    if not src.is_dir():
        raise SystemExit("--jsonc_in がフォルダでない: %s" % a.jsonc_in)
    dst = Path(a.jsonc_out)
    dst.mkdir(parents=True, exist_ok=True)
    cfg, cells = None, []
    for f in sorted(src.iterdir()):
        if not f.is_file():
            continue
        o = dst / f.name
        if f.resolve() != o.resolve():
            shutil.copy(f, o)
        if f.name == "config_lib.jsonc":
            cfg = o
        elif f.suffix == ".jsonc":
            cells.append(o)
    if cfg is None:
        raise SystemExit("config_lib.jsonc が無い: %s" % src)
    return cfg, cells


def _kgn_to_single(cells, name, n1, n2):
    """暫定 template（1 種）を全セルの template_kgn へ割り当てる。

    ISS-00189: templates を 1 種へ書き換えると std_*.jsonc が参照する名前
    （d034 等）が config から消え、 add_template() が
    「[Error] unique template =delay/7x7/d034 is not exist」で落ちるため。
    書き込むのは --jsonc_out 側だけ。
    """
    for j in cells:
        n = rewrite_kgn(j, lambda c, p: name, n1, n2, backup=False)
        print("  template_kgn を %-9s へ統一 : %-28s (%d セル)" % (name, j.name, n))


def _triple(txt, what):
    """"min,max,num" を (float, float, int) で返す。"""
    p = [x for x in str(txt).replace(" ", "").split(",") if x]
    if len(p) != 3:
        raise SystemExit("%s は min,max,num の 3 値で指定する（例 0.01,1.5,7）: %s" % (what, txt))
    try:
        return float(p[0]), float(p[1]), int(p[2])
    except ValueError:
        raise SystemExit("%s の値が数値でない: %s" % (what, txt))


def _numlist(txt, what):
    """カンマ区切りの数値リストを昇順・重複除去で返す（有効 3 桁）。"""
    try:
        v = sorted({sig3(x) for x in txt.replace(" ", "").split(",") if x})
    except ValueError:
        raise SystemExit("%s は数値のカンマ区切りで指定する: %s" % (what, txt))
    if not v:
        raise SystemExit("%s が空" % what)
    return v


def stage_probe(a):
    """指定セルの in_cap と out_transition を測るための template を書く。

    index_1 = --slew_in のリスト／index_2 = --load_out のリスト。
    1 点だけ渡せば「その 1 条件」を、複数渡せばその格子を測る。

      1 フロー目 : --slew_in 0.001 --load_out 0.001
                   → 最速入力・無負荷の transition ＝ index_1[min] の根拠
      2 フロー目 : --slew_in <index_1[min]> --load_out <in_cap x N>
                   → 自分自身を N 個駆動したときの transition ＝ index_1[max] の根拠
    """
    cfg, cells = _prepare_out(a)
    i1 = _numlist(a.slew_in, "--slew_in")
    i2 = _numlist(a.load_out, "--load_out")
    write_templates(cfg, build_templates(i1, [i2]), backup=False)
    print("1.probe : %s" % cfg)
    print("  index_1 = [%s]   （入力 slew。 単位は config の time_unit）" % _fmt(i1))
    print("  index_2 = [%s]   （出力負荷。 単位は config の capacitance_unit）" % _fmt(i2))
    _kgn_to_single(cells, tname(i2[-1]), len(i1), len(i2))
    _log(a, ["cell        = %s" % a.cell,
             "index_1     = [%s]" % _fmt(i1),
             "index_2     = [%s]" % _fmt(i2),
             "jsonc_in    = %s" % a.jsonc_in,
             "jsonc_out   = %s" % a.jsonc_out],
         header="1.probe  %s" % a.cell, truncate=True)
    print()
    print("次: charao を --cells_only %s で実行し、 2.report で in_cap / transition を見る" % a.cell)


def stage_report(a):
    """1.probe の結果から in_cap と out_transition を表示する。"""
    caps, trans = load_measured(a.lib)
    cell = a.cell
    if cell not in caps:
        cand = [c for c in caps if c.endswith("__" + cell)] or \
               [c for c in caps if c.endswith(cell)]
        if len(cand) != 1:
            raise SystemExit("セルを一意に決められない: %s（候補 %s）" % (a.cell, sorted(cand)[:5]))
        cell = cand[0]

    print("2.report : %s" % cell)
    print()
    rec = []
    cin = min(caps[cell].values())
    print("  in_cap  = %.6g pF" % cin)
    rec.append("in_cap         = %.6g" % cin)
    for pin, c in sorted(caps[cell].items()):
        print("      pin %-6s : %.6g pF" % (pin, c))
        rec.append("  pin %-6s   = %.6g" % (pin, c))
    print()
    for k in sorted(k for k in trans if k[0] == cell):
        for (sl, ld), v in sorted(trans[k].items()):
            msg = ("out_transition = %.6g   （出力 %s / 入力 slew %g / 負荷 %g）"
                   % (v, k[1], sl, ld))
            print("  " + msg)
            rec.append(msg)
    rec.append("lib            = %s" % a.lib)
    _log(a, rec, header="2.report  %s" % cell)
    print()
    print("  → index_1[min] はこの out_transition を基準に、 index_1[max] は max_transition を、")
    print("     index_2[min] は in_cap を参考に決めて 3.scan へ渡す")


def _cell_ports(jsonc_files):
    """cell -> [出力 logic port...] を jsonc から拾う。"""
    out = {}
    for j in jsonc_files:
        lines = Path(j).read_text(encoding="utf-8").splitlines()
        for i, ln in enumerate(lines):
            if not _KGN_RE.search(ln.rstrip("\n")):
                continue
            c = _cell_of(lines, i)
            if not c:
                continue
            op = sorted({v for v in _ports_of(lines, i).values() if v.startswith("o")})
            if op:
                out[c] = op
    return out


def stage_scan(a):
    """全セルの max_cap を測る template を書く（3.scan_target）。

    ISS-00189: **セル・出力ピンごとに別の template 名**を割り当てる。
    4.analyze が index_2 を個別に更新して収束させるため。
    名前は通し番号（d000, d001, ...）。 最終的な値ベースの名前は 5.build で振り直す。

      index_1 = [slew_in]                        ＝ max_transition。 1 点でよい
      index_2 = [load, load x load_out_rate]     ＝ 2 点あると傾きが分かる
                                                   （既定 rate=2.0。 --load_out にリストも可）

    **対象は comb だけでなく seq / ff / lat の delay も含む**（全セルの delay measure）。
    """
    cfg, cells = _prepare_out(a)
    i1 = _numlist(a.slew_in, "--slew_in")
    #--- ISS-00189: index_2 は「初期 load」と --load_out_rate（既定 2.0）の 2 点。
    #    --load_out にリストを渡せばそれをそのまま使う。
    i2 = _numlist(a.load_out, "--load_out")
    if len(i2) == 1:
        i2 = [i2[0], sig3(i2[0] * a.load_out_rate)]
    ports = _cell_ports(cells)

    # (cell, oport) -> 通し番号名
    keys = [(c, p) for c in sorted(ports) for p in ports[c]]
    name_of = {k: "d%03d" % i for i, k in enumerate(keys)}

    groups = [list(i2) for _ in keys]
    write_templates(cfg, build_templates(i1, groups, names=[name_of[k] for k in keys]),
                    backup=False)
    for j in cells:
        rewrite_kgn(j, lambda c, p: name_of.get((c, p)), len(i1), len(i2), backup=False)
    print("3.scan : %s" % cfg)
    print("  index_1 = [%s]   （入力 slew ＝ max_transition）" % _fmt(i1))
    print("  index_2 = [%s]   （初期値。 セルごとに 4.analyze が更新する）" % _fmt(i2))
    print("  load_out_rate = %g" % a.load_out_rate)
    if a.load_limit:
        print("  load_limit = %g   （4.analyze はこの範囲内で探索する）" % a.load_limit)
    print("  template : %d 種（セル・出力ピンごとに通し番号）" % len(keys))
    _log(a, ["index_1    = [%s]" % _fmt(i1),
             "index_2    = [%s]（初期値）" % _fmt(i2),
             "load_limit = %s" % a.load_limit,
             "template  = %d 種" % len(keys),
             "jsonc_out = %s" % a.jsonc_out],
         header="3.scan", truncate=True)
    print("\n次: charao を全セル実行してから --stage 4.analyze")


def stage_analyze(a):
    """実測 transition から max_cap を求め、3.scan_target の index_2 を更新する。

    transition は load にほぼ線形なので、 2 点から目標 transition に達する load を
    内挿／外挿して次の index_2 とする。 これを sim と交互に繰り返して収束させる
    （既定 2 回で十分収まる見込み。 足りなければ追加で回す）。
    """
    cfgp = Path(a.jsonc_out) / "config_lib.jsonc"
    if not cfgp.is_file():
        raise SystemExit("config_lib.jsonc が無い: %s" % cfgp)
    cells = [f for f in sorted(Path(a.jsonc_out).glob("*.jsonc"))
             if f.name != "config_lib.jsonc"]
    caps, trans = load_measured(a.lib)

    #--- 目標 transition は 3.scan が config に書いた index_1 から読む（再指定させない）
    ctxt = cfgp.read_text(encoding="utf-8")
    m = re.search(r'"kind":"delay"[^}]*?"index_1":\[([^\]]*)\]', ctxt)
    if not m:
        raise SystemExit("config から delay の index_1 が読めない: %s" % cfgp)
    target = max(float(x) for x in m.group(1).split(",") if x.strip())

    # (cell, pin) -> template 名 は jsonc の template_kgn から引く
    tpl = {}
    for j in cells:
        lines = Path(j).read_text(encoding="utf-8").splitlines()
        for i, ln in enumerate(lines):
            mk = _KGN_RE.search(ln.rstrip("\n"))
            c = _cell_of(lines, i) if mk else None
            if not c:
                continue
            p2l = {p: l for p, l in _ports_of(lines, i).items() if l.startswith("o")}
            ent = re.findall(r'\["delay","[^"]*","([^"]*)"(?:,"(o\d+)")?\]', mk.group(1))
            for nm, op in ent:
                for pin, lp in p2l.items():
                    if (not op) or lp == op:
                        tpl[(c, pin)] = nm

    upd, rep, clamped = {}, [], []
    for k, rows in sorted(trans.items()):
        nm = tpl.get(k)
        if not nm:
            continue
        sl = max(s_ for s_, _ in rows)
        pts = sorted((l, v) for (s_, l), v in rows.items() if s_ == sl)
        #--- ISS-00189: 収束判定は index_2[0] の点で行う。
        #    index_2 = [a, a*rate] なので末尾は目標より rate 倍ぶん大きく出る。
        #    補正（次の load）は 2 点の傾きで内挿／外挿する（cap_at_transition）。
        cur = pts[0][0]
        cur_tr = pts[0][1]
        new = cap_at_transition(rows, sl, target)
        if not new or new <= 0:
            rep.append((k, nm, cur, None, cur_tr)); continue
        #--- ISS-00189: --load_limit 以内で探索する。 超えたら頭打ちにする
        if a.load_limit and new > a.load_limit:
            new = a.load_limit
            clamped.append(k)
        upd[nm] = new
        rep.append((k, nm, cur, new, cur_tr))

    #--- config の index_2 を更新（比は初期リストの比を保つ）
    txt = cfgp.read_text(encoding="utf-8")
    n_up = 0
    for nm, new in upd.items():
        pat = re.compile(r'("kind":"(?:delay|power_tout)"[^}]*?"name":"%s"[^}]*?"index_2":)\[[^\]]*\]' % re.escape(nm))
        def _sub(m):
            #--- 2 点目は --load_out_rate 倍（既定 1.1）。 傾きを見るための組み合わせ
            vals = [sig3(new), sig3(new * a.load_out_rate)]
            return m.group(1) + "[" + _fmt(vals) + "]"
        txt, n = pat.subn(_sub, txt)
        n_up += n
    cfgp.write_text(txt, encoding="utf-8")

    ok = sum(1 for _, _, _, n, v in rep if n and abs(v - target) / target <= 0.05)
    print("4.analyze (iter %d) : target transition = %g（config の index_1 から取得）"
          % (a.iter, target))
    print("  load_out_rate = %g%s" % (a.load_out_rate,
          ("  / load_limit = %g（頭打ち %d arc）" % (a.load_limit, len(clamped)))
          if a.load_limit else ""))
    print("  対象 arc %d / index_2 更新 %d エントリ" % (len(rep), n_up))
    print("  transition が target ±5%% に入っている arc : %d / %d" % (ok, len(rep)))
    print()
    print("  %-30s %-6s %10s %10s %10s" % ("cell", "tpl", "load[0]", "Tr@load[0]", "次 load"))
    for k, nm, cur, new, v in sorted(rep, key=lambda x: (x[3] or 0)):
        print("  %-30s %-6s %10.4g %10.4g %10s"
              % (k[0].split("__")[-1] + "/" + k[1], nm, cur, v,
                 ("%.4g" % new) if new else "-"))
    tbl = ["target transition = %g（config の index_1 から取得）" % target,
           "load_out_rate     = %g" % a.load_out_rate,
           "load_limit        = %s（頭打ち %d arc）" % (a.load_limit, len(clamped)),
           "arc = %d / index_2 更新 %d エントリ" % (len(rep), n_up),
           "target +-5%% 到達 : %d / %d" % (ok, len(rep)),
           "lib = %s" % a.lib,
           "",
           "%-30s %-6s %10s %10s %10s" % ("cell/pin", "tpl", "load[0]", "Tr@load[0]", "次 load")]
    for k, nm, cur, new_, v in sorted(rep, key=lambda x: (x[3] or 0)):
        tbl.append("%-30s %-6s %10.4g %10.4g %10s"
                   % (k[0].split("__")[-1] + "/" + k[1], nm, cur, v,
                      ("%.4g" % new_) if new_ else "-"))
    _log(a, tbl, header="4.analyze (iter %d)" % a.iter, truncate=True)
    print("\n次: 再び charao を実行 → 4.analyze（既定 2 巡）。 収束したら 5.build")


def stage_build(a):
    """max_cap をグループ化して 7x7 などフルの template を書く（5.build_target）。

    測定は 3.scan の結果（--lib）を使う。 最終 template の軸は
    --slew_min_max_num / --load_min_max_num（min,max,num）で指定する。
    """
    cfg, cells = _prepare_out(a)
    caps, trans = load_measured(a.lib)
    #--- 最終 template の軸は --slew_min_max_num / --load_min_max_num で指定する。
    smn, smx, snum = _triple(a.slew_min_max_num, "--slew_min_max_num")
    lmn, _lmx, lnum = _triple(a.load_min_max_num, "--load_min_max_num")
    i1 = geom(smn, smx, snum)
    target = smx                    # transition == max_transition となる負荷を探す
    smax = None                     # 実測にある最大 slew を使う（3.scan は 1 点）

    maxcap = {}
    skipped = []
    for k, rows in sorted(trans.items()):
        sl = smax if smax is not None else max(s_ for s_, _ in rows)
        c = cap_at_transition(rows, sl, target)
        if c is None or c <= 0:
            skipped.append(k)
            continue
        maxcap[k] = c

    # グループ化（max_cap 昇順の greedy first-fit）
    order = sorted(maxcap.items(), key=lambda kv: kv[1])
    reps = []                                   # [(代表 max_cap, [key...])]
    for k, v in order:
        for r in reps:
            if abs(v - r[0]) / r[0] <= a.tolerance:
                r[1].append(k)
                break
        else:
            reps.append((v, [k]))

    groups = [geom(lmn, r[0], lnum) for r in reps]
    write_templates(cfg, build_templates(i1, groups), backup=False)

    print("5.build : %s" % cfg)
    print("  対象 arc        : %d（測定不能でスキップ %d）" % (len(maxcap), len(skipped)))
    print("  グループ        : %d（許容 %.1f%%）" % (len(reps), a.tolerance * 100))
    print("  index_1         : [%s]" % _fmt(i1))
    print()
    print("  %-12s %10s %6s  %s" % ("name", "max_cap", "members", "代表セル"))
    for (v, ks), g in zip(reps, groups):
        cs = sorted({k[0].split("__")[-1] for k in ks})
        print("  %-12s %10.4g %6d  %s" % (tname(g[-1]), v, len(ks),
                                          ", ".join(cs[:3]) + (" …" if len(cs) > 3 else "")))
    if skipped:
        print("\n  スキップした arc（transition が target に届かない等）: %d" % len(skipped))
        for k in skipped[:5]:
            print("    %s / %s" % (k[0], k[1]))

    #--- std_*.jsonc の template_kgn を本番名へ割り当てる（orig 非依存）
    if cells:
        pin2name = {}
        for (v, ks), g in zip(reps, groups):
            for k in ks:
                pin2name[k] = tname(g[-1])
        # 出力 pin 名 -> logic port は jsonc 側の ports_dict で解決するため、
        # ここでは (cell, 出力 pin 名) の対応表を作り、resolve で引き当てる
        def make_resolve(jpath):
            txt = Path(jpath).read_text(encoding="utf-8")
            p2l = {}
            for m in re.finditer(r'"cell"\s*:\s*"([^"]+)"', txt):
                pass
            lines = txt.splitlines()
            cur = None
            for i, ln in enumerate(lines):
                mc = _CELL_RE.search(ln)
                if mc:
                    cur = mc.group(1)
                    for pin, lp in _ports_of(lines, i).items():
                        if lp.startswith("o"):
                            p2l[(cur, lp)] = pin
            def resolve(cell, lport):
                if lport is None:
                    cand = [nm for (c, p), nm in pin2name.items() if c == cell]
                    return cand[0] if cand else None
                pin = p2l.get((cell, lport))
                return pin2name.get((cell, pin)) if pin else None
            return resolve
        print()
        for j in cells:
            n = rewrite_kgn(j, make_resolve(j), snum, lnum, backup=False)
            print("  template_kgn を更新 : %-28s (%d セル)" % (j.name, n))
    else:
        print("\n  [WARN] 対象 jsonc が無い。 template_kgn は未更新")

    #--- 5.build.log へ記録（グループ一覧を含む）
    tbl = ["対象 arc  = %d（測定不能でスキップ %d）" % (len(maxcap), len(skipped)),
           "グループ  = %d（許容 %.1f%%）" % (len(reps), a.tolerance * 100),
           "index_1   = [%s]" % _fmt(i1),
           "lib       = %s" % a.lib,
           "jsonc_in  = %s" % a.jsonc_in,
           "jsonc_out = %s" % a.jsonc_out,
           "",
           "%-12s %10s %8s  %s" % ("name", "max_cap", "members", "代表セル")]
    for (v, ks), g in zip(reps, groups):
        cs = sorted({k[0].split("__")[-1] for k in ks})
        tbl.append("%-12s %10.4g %8d  %s" % (tname(g[-1]), v, len(ks), ", ".join(cs)))
    _log(a, tbl, header="5.build", truncate=True)


# ── main ──────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="実測から config_lib.jsonc の templates を決める（ISS-00189）")
    #--- stage は実行順を名前に含める（1.probe → 2.report → 3.scan → 4.build）。
    #    番号だけ / 名前だけでも受け付ける。
    ap.add_argument("--stage", required=True, metavar="STAGE",
                    help="1.probe / 2.report / 3.scan / 4.analyze / 5.build"
                         "（'1' や 'probe' のような省略形も可）")
    ap.add_argument("--jsonc_in",
                    help="入力フォルダ（config_lib.jsonc と <cell_group>*.jsonc が同居）。 書き換えない")
    ap.add_argument("--jsonc_out",
                    help="出力フォルダ。 更新した jsonc 一式を書く。 次 stage の --jsonc_in になる")
    ap.add_argument("--lib", help="charao 出力 .lib（2.report / 4.build で読む）")
    ap.add_argument("--cell", default="inv_1", help="基準セル。 **フル名**で指定する。 既定 inv_1")
    #--- 1.probe
    ap.add_argument("--slew_in", default="0.001",
                    help="1.probe の入力 slew。 カンマ区切りで複数可（index_1 になる）。"
                         " 単位は config_lib.jsonc の time_unit。 既定 0.001")
    ap.add_argument("--load_limit", type=float, default=None,
                    help="出力負荷の上限。 3.scan で指定し 4.analyze がこの範囲内で探索する"
                         "（超えたら頭打ち）。 単位は config の capacitance_unit")
    ap.add_argument("--iter", type=int, default=1,
                    help="4.analyze の実行番号。 ログを 4.analyze_<番号>.log に分ける。 既定 1")
    #--- 2 点目の倍率。 既定は stage で変える（3.scan=2.0 / 4.analyze=1.5）
    ap.add_argument("--load_out_rate", type=float, default=None,
                    help="index_2 の 2 点目の倍率。 既定 3.scan=2.0 / 4.analyze=1.5")
    ap.add_argument("--load_out", default="0.001",
                    help="1.probe の出力負荷。 カンマ区切りで複数可（index_2 になる）。"
                         " 単位は config_lib.jsonc の capacitance_unit。 既定 0.001")
    #--- 5.build（最終 template の軸。 3.scan/4.analyze は --slew_in/--load_out を使う）
    ap.add_argument("--slew_min_max_num", default="",
                    help="5.build の index_1 を min,max,num のカンマ区切りで指定"
                         "（例 0.01,1.5,7）。 単位は config の time_unit")
    ap.add_argument("--load_min_max_num", default="",
                    help="5.build の index_2 を min,max,num のカンマ区切りで指定"
                         "（例 0.0005,5.0,7）。 max は使わず各グループの max_cap を使う")
    ap.add_argument("--tolerance", type=float, default=0.05,
                    help="4.build のグループ化許容（既定 0.05 = 5%%）")
    a = ap.parse_args()
    if a.load_out_rate is None:
        a.load_out_rate = 2.0 if str(a.stage).endswith("scan") else 1.5

    STAGES = ["1.probe", "2.report", "3.scan", "4.analyze", "5.build"]
    alias = {}
    for full in STAGES:
        num, name = full.split(".")
        alias[full] = alias[num] = alias[name] = full
    if a.stage not in alias:
        raise SystemExit("--stage は %s のいずれか（指定: %s）" % (" / ".join(STAGES), a.stage))
    a.stage = alias[a.stage]

    need = {"1.probe":   ["jsonc_in", "jsonc_out"],
            "2.report":  ["lib"],
            "3.scan":    ["jsonc_in", "jsonc_out"],
            "4.analyze": ["lib", "jsonc_out"],
            "5.build":   ["lib", "jsonc_in", "jsonc_out",
                          "slew_min_max_num", "load_min_max_num"]}
    for n in need[a.stage]:
        if getattr(a, n) in (None, ""):
            raise SystemExit("--stage %s には --%s が要る" % (a.stage, n))

    {"1.probe": stage_probe, "2.report": stage_report, "3.scan": stage_scan,
     "4.analyze": stage_analyze, "5.build": stage_build}[a.stage](a)


if __name__ == "__main__":
    main()
