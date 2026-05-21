#!/usr/bin/env python3
"""util_merge.py - run_each の cell 別 .lib/.v/.md を 1 ファイルに統合する。

charao の `debug_run.sh run_each` は cell ごとに rslt_<cell>/ へ
.lib/.v/.md を出力する。 本スクリプトはそれらを 1 つの .lib/.v/.md に統合する。

使い方:
    util_merge.py <file>... --out <prefix>

  <file>...  .lib/.v/.md ファイル（混在可。 シェルのワイルドカードで展開）
  --out      出力 prefix。 <prefix>.lib / <prefix>.v / <prefix>.md を生成

ヘッダは date 行を除いて全ファイルの一致を検証し（不一致は ERROR で停止）、
date は引数リスト末尾のファイルのものを採用する。

ある拡張子のファイルが 1 つ（= 1 cell）のみの場合、 その拡張子はマージを
スキップする（元ファイルをそのまま使えばよく、 統合ファイルを作る意味が無い）。
"""
import argparse
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
    blocks = [blk for _, _, cells in parsed for blk in cells]
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
        description="cell 別 .lib/.v/.md を 1 ファイルに統合する。"
    )
    ap.add_argument("files", nargs="+", help=".lib/.v/.md ファイル（混在可）")
    ap.add_argument(
        "--out", required=True, metavar="PREFIX",
        help="出力 prefix（<PREFIX>.lib / .v / .md を生成）",
    )
    args = ap.parse_args()

    groups = {"lib": [], "v": [], "md": []}
    for f in args.files:
        ext = f.rsplit(".", 1)[-1].lower() if "." in f else ""
        if ext not in groups:
            fail(f"未対応の拡張子: {f}")
        groups[ext].append(f)

    if not any(groups.values()):
        fail("入力ファイルがありません。")

    for ext, paths in groups.items():
        if not paths:
            continue
        if len(paths) == 1:
            print(f"util_merge: .{ext} は 1 file のためマージをスキップ: {paths[0]}")
            continue
        splitter, is_date, footer = SPECS[ext]
        text, ncell = merge_group(paths, splitter, is_date, ext, footer)
        outpath = f"{args.out}.{ext}"
        with open(outpath, "w", encoding="utf-8") as fp:
            fp.write(text)
        print(f"util_merge: {outpath} <- {len(paths)} files, {ncell} cells")


if __name__ == "__main__":
    main()
