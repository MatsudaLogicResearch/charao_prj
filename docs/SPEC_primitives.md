# SPEC : Verilog primitives (std_primitives.v)

charao が生成する Verilog モデルは、順序セルの記述に **UDP（User Defined Primitive）** を使う。
この UDP 定義は **PDK 固有の資産**であるため、charao 本体ではなく **target ディレクトリ**が供給する。

ISS-00172 で導入（1.0.0 以降）。それ以前は `mylogic_*.py` の `get_code_primitive()` が
Python ソース中に UDP を埋め込んでいたが、以下の理由で廃止した。

- **ライセンス分離**：GF180 由来の UDP は Apache-2.0。charao 本体（GPL-2.0-or-later）の
  ソースへ埋め込むと、ライセンスの異なるコードが混在する
- **PDK 移植性**：PDK ごとに UDP の table が異なりうる。target 側に置けば charao 本体を
  触らずに差し替えられる

---

## 1. 入力と出力

### 入力

```
<ARGS.target>/<ARGS.fab_process>/<ARGS.cell_vendor>/<ARGS.cell_revision>/std_primitives.v
```

`config_lib.jsonc` と同じディレクトリに置く。例：

```
sample_target/gf180/fd/mcuC7t20240817/std_primitives.v
```

**ファイル名が `std_` で始まる理由**：多くの PDK は同名の `primitives.v` を同梱している。
リモート実行（lrPymRPC）では `--SOURCE_INCLUDE` が**パスの後方一致**でファイルを選ぶため、
`primitives.v` のままだと PDK 同梱分（GF180 では約 2 MB の `*.v` 群）まで転送対象になる。
`std_primitives.v` にしておけば、`--SOURCE_INCLUDE ... std_primitives.v` で
**本ファイルだけ**を確実に転送できる。`std_comb.jsonc` / `std_seq.jsonc` と同じ命名規約でもある。

### 出力

```
<config_lib.result_path>/<lib_basename>_primitives.v
```

例：`rslt/gf180CB5P00fdmcuC7t20240817_primitives.v`

- **入力ファイルをそのままコピーする**（charao はヘッダを付けず、内容を一切加工しない）
- **build_stamp を付けない**。primitive は build に依存しないため
- `ARGS.cell_group=std` のときのみ出力する（io では出力しない）
- `std_primitives.v` が存在しない場合は **出力をスキップ**し、`[INF]` を表示して処理を続行する
  （UDP を必要としないセル群だけを対象にした実行を妨げないため）

### 本体 .v との関係

`<lib_basename>_<build_stamp>.v`（本体）には primitive を**含めない**。2 ファイルは独立しており、
シミュレータには両方を渡す。

```bash
iverilog gf180CB5P00fdmcuC7t20240817_primitives.v gf180CB5P00fdmcuC7t20240817_b00.v tb.v
```

論理合成では本体 .v のみを渡す（`*_primitives.v` は渡さない）。

---

## 2. charao が要求するインタフェース契約

`mylogic_*.py` の `vcode` が UDP を**名前とポート順で直接インスタンス化**する。

```verilog
udp_iq_ff_n inst (iq1, c_int, p_int, c0, d_int, notifier);
```

したがって **primitives.v は下表の 4 つを、この名前・このポート順・この意味論で定義する義務**を負う。
名前を変えたい場合は `mylogic_seq_ff.py` / `mylogic_seq_scan.py` / `mylogic_seq_lat.py` の
`vcode` も同時に変更すること。

| primitive | ポート順 | 用途 |
|---|---|---|
| `udp_iq_ff_n` | `(Q, C, P, CK, D, N)` | posedge FF。非同期端子 0〜1 本のセル用 |
| `udp_iq_ff_hn` | `(Q, C, P, CK, D, N)` | posedge FF。C/P 同時 assert 時は **P が優先** |
| `udp_iq_latch_n` | `(Q, C, P, CK, D, N)` | level latch（CK = enable, active-H） |
| `udp_iq_latch_hn` | `(Q, C, P, CK, D, N)` | level latch。C/P 同時 assert 時は **P が優先** |

### ポートの意味

| ポート | 向き | 意味 |
|---|---|---|
| `Q` | output (reg) | セル内部の保持ノード |
| `C` | input | clear、**active-High** |
| `P` | input | preset、**active-High** |
| `CK` | input | FF はクロック（posedge）、LATCH は enable（active-High） |
| `D` | input | データ |
| `N` | input | notifier（タイミングチェック違反で `Q=x` にする） |

- 非同期端子を持たないセルでも 6 ポートは省略できない。`vcode` 側が `1'b0` を渡す

  ```verilog
  udp_iq_ff_n inst (o0, 1'b0, 1'b0, c0, i0, notifier);
  ```

- active-Low の外部端子（RN / SETN）は `vcode` 側で `not` を挟んで active-High に変換する

  ```verilog
  not (p_int, r0); udp_iq_ff_n inst (iq1, 1'b0, p_int, c0, d_int, notifier);
  ```

- negedge クロックのセル（dffnq 等）も `vcode` 側で `not` を挟む。UDP は posedge 版のみ

---

## 3. `n` と `hn` の違い

**table の差は 1 行だけ**である（FF・LATCH とも同じ）。

```
hn:   ?  1  ?  ?  ?  :  ?  :  1;     ← C は don't care
n :   0  1  ?  ?  ?  :  ?  :  1;     ← C=0 を要求
       C  P  CK D  N     Qold  Qnew
```

つまり **P（preset）を assert したときに C（clear）をどう扱うか**の違いである。

| 入力 | `udp_iq_*_n` | `udp_iq_*_hn` |
|---|---|---|
| C=1, P=0 | Q=0 | Q=0 |
| C=0, P=1 | Q=1 | Q=1 |
| **C=1, P=1** | **どの行にもマッチせず Q=x** | **Q=1（P が優先）** |

- `n` は C と P の同時 assert を **禁止状態**として扱う（優先度を定義しない）
- `hn` は preset に**優先度を与えた**版。`h` は "high priority (preset)" の意

> **注意**：1.0.0 以前の `mylogic_seq_ff.py` のコメントには
> 「`n` = C (clear) dominates over P (preset)」とあったが、これは**誤り**である。
> 正しくは上表のとおり「`n` は C/P 同時 assert を未定義（x）とする」。

### 使い分け

**非同期端子を 2 本持つセルだけが `hn` を必要とする。**

| セル | 非同期端子 | 使用 primitive |
|---|---|---|
| dffq / dffnq | なし | `udp_iq_ff_n`（C=P=`1'b0` 固定） |
| dffrnq / dffnrnq | RN のみ | `udp_iq_ff_n` |
| dffsnq / dffnsnq | SETN のみ | `udp_iq_ff_n` |
| **dffrsnq / dffnrsnq** | RN ＋ SETN | **`udp_iq_ff_hn`** |
| sdffq / sdffrnq / sdffsnq | 0〜1 本 | `udp_iq_ff_n` |
| **sdffrsnq** | RN ＋ SETN | **`udp_iq_ff_hn`** |
| latq / latrnq / latsnq | 0〜1 本 | `udp_iq_latch_n` |
| **latrsnq** | RN ＋ SETN | **`udp_iq_latch_hn`** |

RN と SETN を両方持つセルは、ユーザが同時に assert しうる。`x` を出さないために
優先度を定義した `hn` を使う、という理屈である。

---

## 4. 他 PDK への移植手順

1. **対象 PDK の Verilog モデルから UDP を探す**
   - 多くの PDK は標準セル Verilog に UDP を同梱している
   - 例（GF180）：`libs.ref/gf180mcu_fd_sc_mcu7t5v0/verilog/primitives.v`

2. **§2 の 4 つに対応づける**
   - PDK 側の UDP を、charao が要求する名前・ポート順に合わせて改名する
   - ポート順が異なる場合は並べ替える（table の列順も一致させること）
   - `hn` に相当する UDP が無い PDK では、`n` の table の
     `0 1 ? ? ? : ? : 1;` を `? 1 ? ? ? : ? : 1;` に変えたものを `hn` として用意する

3. **UDP が存在しない PDK の場合**
   - §2 の意味論を満たす UDP を新規に記述する
   - GF180 版（`sample_target/gf180/fd/mcuC7t20240817/primitives.v`）を雛形にできるが、
     **Apache-2.0 の条件（改変告知・条文添付）を満たすこと**

4. **ライセンス表記を整える**
   - PDK 由来のコードを持ち込む場合、元のライセンスヘッダを保持する
   - 改名・改変した場合は **改変告知**を明記する（Apache-2.0 なら §4(b) の義務）
   - 必要なライセンス条文を `sample_target/<pdk>/LICENSE-*.txt` として同梱する

5. **動作確認**
   - `<target>` に置いて charao を実行し、`rslt/*_primitives.v` が生成されることを確認
   - 生成された本体 .v が参照する UDP 名が、primitives.v の定義名と一致することを確認

     ```bash
     grep -o "udp_iq_[a-z_]*" rslt/*_b00.v | sort -u
     grep "^primitive" rslt/*_primitives.v
     ```

   - シミュレータで両ファイルをコンパイルし、未定義 primitive が無いことを確認

---

## 5. 関連

- `docs/SPEC_seq_ff.md` — FF セルの vcode 記述規約
- `docs/SPEC_seq_lat.md` — LATCH セルの vcode 記述規約
- ISS-00172 — primitive を target 側へ移設
- ISS-00173 — dead primitive（`lr_mux` / `lr_dff`）の削除
