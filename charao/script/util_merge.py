#!/usr/bin/env python3
"""util_merge.py - rslt ディレクトリ群の .lib/.v/.md を同名ファイル同士で統合する。

charao は実行単位ごとに rslt/（run_each は rslt_<cell>/）へ .lib/.v/.md を出力する。
本スクリプトは複数の rslt を **順次上書き更新**しながら 1 つの rslt にまとめる。

使い方:
    util_merge.py --out_dir <dir> <in_dir>...

  --out_dir    出力ディレクトリ（無ければ作成）。 入力と同じファイル名で出力する
  <in_dir>...  入力ディレクトリ（rslt 等）。 **先頭がベース、以降が順次更新**

ISS-00171: `in_dir1 in_dir2 in_dir3 ...` と与えると、 **in_dir1 をベースに in_dir2, in_dir3 ...
を順次適用**する。 同名 cell は後のディレクトリで **上書き**、 未登場の cell は **追加**。
出力順は in_dir1 の並びを保ち、 新規 cell は末尾へ追加する。 マージは **同じファイル名同士**で
行うため、 PVT 条件でファイル名が変わる場合もそのまま扱える。 1 セルだけ再 sim した結果を
既存の rslt へ差し戻す用途に使う（rslt を渡すと新しい rslt ができる）。

ヘッダは date 行を除いて全ファイルの一致を検証し（不一致は ERROR で停止）、
date は引数リスト末尾のファイルのものを採用する。

入力が 1 ディレクトリだけの場合もそのまま出力する（= コピー相当。 入力にあるファイルは
必ず出力に現れる）。
"""
import argparse
import os
import re
import sys


def read_lines(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.readlines()
    except OSError as e:
        fail(f"ファイルを開けません: {path} ({e})")


def fail(msg):
    sys.exit(f"util_merge: ERROR: {msg}")


# --- date 行判定（ヘッダ照合の除外対象）---
def is_date_lib(line):
    return re.match(r"\s*date\s", line) is not None


def is_date_v(line):
    return line.startswith("// Build Date")


def is_date_md(line):
    return line.startswith("date:")


# --- ファイル分割: (header_lines, [cell_block_lines, ...]) ---
def split_lib(path):
    lines = read_lines(path)
    header, cells, cur = [], [], None
    i, n = 0, len(lines)
    while i < n and not lines[i].startswith("  cell "):
        header.append(lines[i])
        i += 1
    while i < n:
        line = lines[i]
        if line.startswith("  cell "):
            if cur is not None:
                cells.append(cur)
            cur = [line]
        elif line.rstrip() == "}":
            break
        elif cur is not None:
            cur.append(line)
        i += 1
    if cur is not None:
        cells.append(cur)
    if not cells:
        fail(f"cell ブロックが見つかりません: {path}")
    return header, cells


def split_v(path):
    lines = read_lines(path)
    header, cells = [], []
    i, n = 0, len(lines)
    while i < n and not lines[i].startswith("`celldefine"):
        header.append(lines[i])
        i += 1
    while i < n:
        if lines[i].startswith("`celldefine"):
            block = []
            while i < n:
                block.append(lines[i])
                end = lines[i].startswith("`endcelldefine")
                i += 1
                if end:
                    break
            cells.append(block)
        else:
            i += 1
    if not cells:
        fail(f"celldefine ブロックが見つかりません: {path}")
    return header, cells


def split_md(path):
    lines = read_lines(path)
    idx = None
    for i, l in enumerate(lines):
        if l.startswith("# Cell Infomation"):
            idx = i
            break
    if idx is None:
        fail(f"'# Cell Infomation' 見出しが見つかりません: {path}")
    header = lines[: idx + 1]
    cells, cur = [], None
    for l in lines[idx + 1:]:
        if l.startswith("## "):
            if cur is not None:
                cells.append(cur)
            cur = [l]
        elif cur is not None:
            cur.append(l)
    if cur is not None:
        cells.append(cur)
    if not cells:
        fail(f"cell セクション(## )が見つかりません: {path}")
    return header, cells


# --- cell 名の同定（ISS-00171: 上書き判定のキー）---
def cell_name(block, kind):
    """cell ブロックの先頭からセル名を取り出す。 .lib=cell (<name>) / .v=module <name> / .md=## <name>"""
    if kind == "lib":
        m = re.match(r"\s*cell\s*\(\s*([^)\s]+)\s*\)", block[0])
    elif kind == "v":
        m = None
        for line in block:
            m = re.match(r"\s*module\s+([A-Za-z_][\w$]*)", line)
            if m:
                break
    else:  # md
        m = re.match(r"##\s+(\S+)", block[0])
    if not m:
        fail(f"cell 名を同定できません（{kind}）: {block[0].rstrip()}")
    return m.group(1)


# --- ヘッダ照合 / date 置換 ---
def check_headers(parsed, is_date, kind):
    ref_path, ref_h = parsed[0][0], parsed[0][1]
    ref_nd = [l for l in ref_h if not is_date(l)]
    for path, h, _ in parsed[1:]:
        nd = [l for l in h if not is_date(l)]
        if nd != ref_nd:
            ref_line, tgt_line = first_diff(ref_nd, nd)
            fail(
                f".{kind} ヘッダが date 以外で不一致: {path}\n"
                f"  基準 ({ref_path}): {ref_line!r}\n"
                f"  対象 ({path}): {tgt_line!r}"
            )


def first_diff(a, b):
    for x, y in zip(a, b):
        if x != y:
            return x, y
    if len(a) > len(b):
        return a[len(b)], "(行なし)"
    if len(b) > len(a):
        return "(行なし)", b[len(a)]
    return "", ""


def merged_header(parsed, is_date):
    ref_h = parsed[0][1]
    last_h = parsed[-1][1]
    last_date = next((l for l in last_h if is_date(l)), None)
    out = []
    for l in ref_h:
        if is_date(l) and last_date is not None:
            out.append(last_date)
        else:
            out.append(l)
    return out


def merge_group(paths, splitter, is_date, kind, footer):
    parsed = []
    for p in paths:
        h, cells = splitter(p)
        parsed.append((p, h, cells))
    check_headers(parsed, is_date, kind)
    out = list(merged_header(parsed, is_date))
    #-- ISS-00171: f1 をベースに f2, f3 ... を順次適用（同名 cell は上書き、 未登場の cell は追加）。
    #   部分再実行の結果を既存の統合ファイルへ差し戻す運用（1 セルだけ再 sim して統合 lib を更新）
    #   のため。 出力順は f1 の並びを保ち、 新規 cell は末尾へ追加する（dict の挿入順保持を利用）。
    merged = {}
    n_update = 0
    for _, _, cells in parsed:
        for blk in cells:
            name = cell_name(blk, kind)
            if name in merged:
                n_update += 1
            merged[name] = blk
    if n_update:
        print(f"util_merge: .{kind}: {n_update} cell(s) updated by later file(s)")
    blocks = list(merged.values())
    for bi, block in enumerate(blocks):
        out.extend(block)
        # .lib/.v は cell ブロック間に空行を 1 行入れる（.md は元のセクション区切りを保つ）
        if kind != "md" and bi != len(blocks) - 1:
            if out and not out[-1].endswith("\n"):
                out[-1] += "\n"
            out.append("\n")
    if footer:
        if out and not out[-1].endswith("\n"):
            out[-1] += "\n"
        out.append(footer)
    return "".join(out), len(blocks)


SPECS = {
    "lib": (split_lib, is_date_lib, "}\n"),
    "v": (split_v, is_date_v, "\n"),
    "md": (split_md, is_date_md, None),
}


def main():
    ap = argparse.ArgumentParser(
        description="rslt ディレクトリ群の .lib/.v/.md を同名ファイル同士で統合する。"
    )
    ap.add_argument(
        "--out_dir", required=True, metavar="DIR",
        help="出力ディレクトリ（無ければ作成）。 入力と同じファイル名で出力する",
    )
    ap.add_argument("in_dir_list", nargs="+", help="入力ディレクトリ（rslt 等）。 先頭がベース、以降が順次更新")
    args = ap.parse_args()

    for d in args.in_dir_list:
        if not os.path.isdir(d):
            fail(f"入力ディレクトリがありません: {d}")

    #-- ISS-00171: ファイル名（basename）ごとに束ねる。 PVT 条件でファイル名が変わっても
    #   同名ファイル同士だけがマージ対象になる。 順序は in_dir_list の並び（先頭がベース）。
    targets = {}   # basename -> [path, ...]
    for d in args.in_dir_list:
        for fn in sorted(os.listdir(d)):
            ext = fn.rsplit(".", 1)[-1].lower() if "." in fn else ""
            if ext not in SPECS:
                continue
            targets.setdefault(fn, []).append(os.path.join(d, fn))

    if not targets:
        fail(f"入力ディレクトリに .lib/.v/.md がありません: {' '.join(args.in_dir_list)}")

    os.makedirs(args.out_dir, exist_ok=True)

    for fn, paths in targets.items():
        ext = fn.rsplit(".", 1)[-1].lower()
        splitter, is_date, footer = SPECS[ext]
        text, ncell = merge_group(paths, splitter, is_date, ext, footer)
        outpath = os.path.join(args.out_dir, fn)
        with open(outpath, "w", encoding="utf-8") as fp:
            fp.write(text)
        print(f"util_merge: {outpath} <- {len(paths)} files, {ncell} cells")


if __name__ == "__main__":
    main()
