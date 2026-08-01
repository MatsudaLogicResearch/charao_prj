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
udp_iq_ff_n inst (iq1, c_int, p_int, c0, d_int, notifier, vdd, vss);
```

したがって **primitives.v は下表の 4 つを、この名前・このポート順・この意味論で定義する義務**を負う。
名前を変えたい場合は `mylogic_seq_ff.py` / `mylogic_seq_scan.py` / `mylogic_seq_lat.py` の
`vcode` も同時に変更すること。

| primitive | ポート順 | 用途 |
|---|---|---|
| `udp_iq_ff_n` | `(Q, C, P, CK, D, N, VPWR, VGND)` | posedge FF。非同期端子 0〜1 本のセル用 |
| `udp_iq_ff_hn` | `(Q, C, P, CK, D, N, VPWR, VGND)` | posedge FF。C/P 同時 assert 時は **P が優先** |
| `udp_iq_latch_n` | `(Q, C, P, CK, D, N, VPWR, VGND)` | level latch（CK = enable, active-H） |
| `udp_iq_latch_hn` | `(Q, C, P, CK, D, N, VPWR, VGND)` | level latch。C/P 同時 assert 時は **P が優先** |

### ポートの意味

| ポート | 向き | 意味 |
|---|---|---|
| `Q` | output (reg) | セル内部の保持ノード |
| `C` | input | clear、**active-High** |
| `P` | input | preset、**active-High** |
| `CK` | input | FF はクロック（posedge）、LATCH は enable（active-High） |
| `D` | input | データ |
| `N` | input | notifier（タイミングチェック違反で `Q=x` にする） |
| **`VPWR`** | input | **電源**。UDP 内のローカル名。`vcode` はセルの電源ピンを配線する |
| **`VGND`** | input | **接地**。同上 |

- 非同期端子を持たないセルでも 8 ポートは省略できない。`vcode` 側が `1'b0` を渡す

  ```verilog
  udp_iq_ff_n inst (o0, 1'b0, 1'b0, c0, i0, notifier, vdd, vss);
  ```

- active-Low の外部端子（RN / SETN）は `vcode` 側で `not` を挟んで active-High に変換する

  ```verilog
  not (p_int, r0); udp_iq_ff_n inst (iq1, 1'b0, p_int, c0, d_int, notifier, vdd, vss);
  ```

- **negedge クロックのセル（dffnq 等）も `vcode` 側で `not` を挟む。UDP は posedge 版のみ。**
  このとき **`specify` のタイミングチェックはセル端子側に付ける**（内部反転信号ではない）。
  charao は既にこの分離ができており、追加対応は不要。

  ```verilog
  not (clkn_int, c0);                                   // UDP へは内部反転信号
  udp_iq_ff_n inst (iq1, 1'b0, 1'b0, clkn_int, d_int, notifier, vdd, vss);
  ...
  $setup(posedge i0, negedge c0, 0, notifier);           // specify はセル端子 c0 の negedge
  $hold (negedge c0, posedge i0, 0, notifier);
  ```

### 電源ポート（`VPWR` / `VGND`）について

**2026-07-30 に 6 ポート → 8 ポートへ拡張**（ダーマツ判断）。パワーカット時にセルの入出力信号が
影響を受けるため、電源状態を UDP の表に取り込む。

`vcode` は **`vdd` / `vss`**（logic 側のポート名）を渡し、セルの実ピン名へ
自動的に置換される。したがって **同一の vcode が PDK ごとの電源ピン名へ展開される**。

> **置換の根拠（2026-08-01 実装＝ISS-00187）**：`vdd` / `vss` / `vnw` / `vpw` は `ports_dict` の
> 値ではないため、`ports_dict` の逆置換では変換されない。`replace_by_portmap()` が
> **`config_lib.jsonc` の `vdd_name` / `vss_name` / `nwell_name` / `pwell_name`** を使って
> 語境界一致で置換する。**これらは vcode 内で予約語扱い**になる。
> 2026-07-31 まで実装が無く、gf180 は `ports_dict` の値が `"vdd"` のため偶然置換されていたが、
> SKY130 は未置換のまま残り、生成 `.v` で**未宣言の暗黙 wire**（UDP の電源入力が `x`）になっていた。

| PDK | 展開結果 |
|---|---|
| gf180 | `udp_iq_ff_hn inst (iq1, c_int, p_int, CLK, d_int, notifier, **VDD**, **VSS**)` |
| OSU035 | `udp_iq_ff_hn inst (iq1, c_int, p_int, CLK, d_int, notifier, **VDD**, **VSS**)` |
| SKY130 | `udp_iq_ff_n inst (iq1, 1'b0, p_int, CLK, d_int, notifier, **VPWR**, **VGND**)` |

表の作りは SKY130 の `*_pp$PG$N` 版に倣う。

- **通常の全行で `VPWR=1` / `VGND=0` を要求**（電源正常時のみ動作する）
- **末尾に「電源が変化したら `Q=x`」の 2 行**を置く

  ```
  //--- 電源が変化したら Q は不定（パワーカット時の x 伝播）
     ?  ?  ?  ?  ?  *  ?  :  ?  :  x;
     ?  ?  ?  ?  ?  ?  *  :  ?  :  x;
  ```

これにより論理シミュレーションでパワーカット時の `x` 伝播が正しく現れる。

### `USE_POWER_PINS` — 電源端子の on/off（2026-08-01、ダーマツ判断＝ISS-00187）

生成 `.v` の**セル側の電源端子**は `` `ifdef USE_POWER_PINS `` で切り替える。
**SKY130 純正 `.v` と同じ流儀**（`sky130_fd_sc_hd__blackbox.v` が同型）。

```verilog
module sky130_fd_sc_hd__dfxtp_1 (CLK,D,Q
`ifdef USE_POWER_PINS
  ,VGND,VNB,VPB,VPWR
`endif
);
output Q;  input CLK;  input D;
`ifdef USE_POWER_PINS
inout VGND;  inout VNB;  inout VPB;  inout VPWR;
`else
supply0 VGND;  supply0 VNB;  supply1 VPB;  supply1 VPWR;
`endif
`ifndef SYNTHESIS
reg notifier; udp_iq_ff_n inst (Q, 1'b0, 1'b0, CLK, D, notifier, VPWR, VGND);
```

| モード | 電源端子 | 用途 |
|--------|----------|------|
| `USE_POWER_PINS` 有効 | port list と `inout` 宣言に出る | パワーアウェア検証（パワーカットの `x` 伝播を見る） |
| 無効（既定） | port から外れ、`supply1`/`supply0` でモジュール内宣言 | 通常の論理シミュレーション |

- `supply1` / `supply0` の割当は `config_lib.jsonc` の
  `vdd_name` / `nwell_name` → **`supply1`**、`vss_name` / `pwell_name` → **`supply0`**
- **ネット名が両モードで同じ**なので、**UDP の接続行は 1 本で済む**
  （`1'b1` / `1'b0` を直結する案より素直。UDP 側も 8 端子の 1 種で足りる）
- 検証：全 181 セル（SKY130）で `iverilog -g2012 -tnull -Wall` が**両モードとも error 0**

---

> **なお `.lib` 側の多電源対応（`KAPWR` のような第 2 電源、`is_isolation_cell`、`level_shifter`）は
> 別課題**（ISS-00182）。本節は Verilog モデルの品質向上のみを扱う。

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

## 5. 配線規約 — 優先度と極性は「表」ではなく「配線」で作る

UDP の表は **`P` 側が優先**という 1 種類（`hn`）と、**優先度を定義しない**もの（`n`）しか無い。
実セルが「リセット優先」でも「セット優先」でも、**新しい UDP を作る必要は無い**。
**どちらを優先させるかは、UDP へ何を配線するかで決まる。**

### 規約 1 — 極性が違うときは反転して渡す

UDP の `C` / `P` は **active-High**。実セルの `RN` / `SETN` が active-Low なら、
vcode 側で `not` を挟んで反転してから渡す。

```verilog
not (p_int, r0);      // P <= !RN
not (c_int, s0);      // C <= !SETN
```

### 規約 2 — 優先させたい信号を `P` へ渡し、出力を反転して取り出す

`hn` は `P` が勝つ表なので、**リセット優先なら `RN` 由来の信号を `P` へ**配線する。
このとき UDP の出力は「内部ノード `IQ1`」として受け、**その反転をセル出力 `Q`** とする。

```verilog
udp_iq_ff_hn inst (iq1, c_int, p_int, c0, d_int, notifier);
not (o0, iq1);        // Q <= !IQ1
```

### 実例：gf180 と charao は同型

gf180 純正の `dffrsnq_func` は次のとおりで、charao の `DFF_PC_NR_NS` vcode と完全に同じ形をしている。

```verilog
not MGM_BG_0( MGM_P0, RN );      // P <= !RN      ← リセットを優先ポートへ
not MGM_BG_1( MGM_C0, SETN );    // C <= !SETN
not MGM_BG_2( MGM_D0, D );       // D <= !D
gf180mcu_fd_sc_mcu7t5v0__udp_hn_iq_ff( IQ1, MGM_C0, MGM_P0, CLK, MGM_D0, notifier );
not MGM_BG_3( Q, IQ1 );          // Q <= !IQ1
```

**gf180 は preset 優先の UDP しか用意していないが、この配線によってリセット優先の実回路を
正しく表現している。** 実測でも gf180 `dffrsnq_1` / OSU035 `DFFARAS_1X` はともに
**セルの端子で見ればリセット優先**であり、この 1 種類の UDP で両方とも表現できる。

> **注意**：UDP 座標（`C` / `P` / `Q`）とセル端子（`SETN` / `RN` / `Q`）を取り違えると、
> 「リセット優先だから新しい UDP が必要」という誤った結論になる。**必ず vcode の配線を見て、
> どちらが `P` に入っているか、出力が反転されているかを確認すること。**

---

## 6. `tools/gen_udp.py` — 実回路から UDP を検証・生成する

UDP は「実回路の挙動を Verilog の真理値表として再現する」ものなので、**実回路を測って表を決める**
のが正しい。契約端子が `(Q, C, P, CK, D, N, VPWR, VGND)` に固定されているため検証すべき状態空間も固定でき、
テストベンチは 1 本で済む。セル依存部は「インスタンス行」と「端子の極性」だけになる。

### 機能

対象セルの SPICE netlist と端子対応を受け取り、ngspice で実回路を動かして挙動を判定し、
対応する UDP を標準出力へ書き出す。

| 測る | 測らない |
|---|---|
| 取り込みエッジ（posedge / negedge） | UDP 表中の `x` や `(?0)` 等のエッジ記法 |
| clear 単独 / preset 単独での `Q` | （解析シミュレーションでは観測できないため） |
| **clear と preset の同時アサート時にどちらが勝つか** | → 測定結果に対応する**正準表を選んで**出力する |
| 保持（クロックエッジ無し）で `Q` が保たれるか | |

### 使い方

```bash
# OSU035（素の .include だけで済む PDK）
python3 tools/gen_udp.py \
    --model   sample_src/OSU035/TT/nmos.sp \
    --model   sample_src/OSU035/TT/pmos.sp \
    --netlist sample_src/OSU035/std/NORMAL/V02.00/spice/DFFARAS_1X.spi \
    --subckt  DFFARAS_1X \
    --ports   "CLK DATA NRST NSET Q VDD VSS VNW VPW" \
    --map     "CK=CLK,D=DATA:L,C=NSET:L,P=NRST:L,Q=Q:L" \
    --power   "VDD=VDD,VSS=VSS,VNW=VNW,VPW=VPW" \
    --vdd 3.3 --kind ff --name udp_iq_ff_hn
```

### 主なオプション

| オプション | 意味 |
|---|---|
| `--map` | `<UDP端子>=<セルピン>[:L]`。**`:L` で反転**。`§5` の配線規約をそのまま写す |
| `--ports` | subckt のピン順 |
| `--power` | `VDD=` / `VSS=` / `VNW=` / `VPW=` |
| `--kind` | `ff` / `latch` |
| `--name` | 出力する primitive 名 |
| `--raw` | TB 冒頭へ挿入する行。**コーナーをセクションで選ぶ PDK は `.lib` をここで渡す** |
| `--raw-path` | `--model` / `--netlist` を絶対パス化しない（リモート実行用） |
| `--tb-only` | TB を書き出すだけで sim しない |
| `--lis` | 既存の ngspice 出力から測定値を読む（リモート実行の結果を持ち込む） |

### `--map` は配線規約どおりに写すこと

**最重要**。`§5` のとおり、優先させたい信号は `P` に入り、出力は反転される。
gf180 / OSU035 のようなリセット優先セルは次のように書く。

```
--map "CK=CLK,D=DATA:L,C=NSET:L,P=NRST:L,Q=Q:L"
             ^^^^^^^^^ ^^^^^^^^^ ^^^^^^^^^ ^^^^
             D 反転     C←SETN    P←RN      Q 反転
```

**`C` と `P` を取り違えると誤った UDP を出力する。** vcode の配線を必ず確認すること。

### リモート実行（gf180 等）

ローカル ngspice が PDK モデルに対応していない場合（gf180 の `mulu0` は ngspice-36 で未対応）は、
`--tb-only` で TB だけ生成し、lrPymRPC でリモート実行してから `--lis` で結果を読み込む。

```bash
# ① TB 生成
python3 tools/gen_udp.py --tb-only --tb-out . --raw-path \
    --raw ".inc sample_src/gf180mcuC/libs.tech/ngspice/design.ngspice" \
    --raw ".lib sample_src/gf180mcuC/libs.tech/ngspice/sm141064.ngspice typical" \
    ... （以下同じ）

# ② リモート実行
python -m lrPymRPC --SERVER_IP <ip> --SOURCE .spiceinit udp_tb.sp sample_src \
    --SOURCE_INCLUDE .spice .ngspice .sp .spiceinit udp_tb.sp \
    --SOURCE_MATCH gf180 udp_tb spiceinit \
    --RESULT udp_tb.lis --CMD "ngspice -b -o udp_tb.lis udp_tb.sp"

# ③ 結果から UDP を生成
python3 tools/gen_udp.py --lis udp_tb.lis ... （同じ引数）
```

### 実装上の注意（TB 生成側で対処済み）

| 症状 | 原因 | 対処 |
|---|---|---|
| DC が `nan` | `.tran` だけでも ngspice は先に DC 動作点を解く。FF のクロスカップル・ラッチは**双安定**で解が一意に決まらない | `.tran ... uic` |
| 初期タイムステップ破綻 | `uic` では t=0 に全ノード 0V なのに電源だけ印加済みという不整合が生じる | **電源を 0 から立ち上げる**（入力も同時にランプ） |
| DC が壊れる | 極性反転を B ソース（挙動ソース）で行うと不連続関数になる | **波形生成側で反転**し、挙動ソースを使わない |

### 順序セルを触るときの注意

ラッチは「**書き込み経路 > フィードバック（キーパー）**」の強さ関係で成立している。
`W` を n/p で非対称にスケールするとこの関係が壊れ、**ラッチが書けなくなって sim が発振・非収束**する。
順序セルのサイズを変えるときは、全トランジスタを同率でスケールするか、`L` のみ変更すること。

---

## 7. 関連

- `docs/SPEC_seq_ff.md` — FF セルの vcode 記述規約
- `docs/SPEC_seq_lat.md` — LATCH セルの vcode 記述規約
- `tools/gen_udp.py` — 実回路から UDP を検証・生成する
- ISS-00172 — primitive を target 側へ移設
- ISS-00173 — dead primitive（`lr_mux` / `lr_dff`）の削除
- ISS-00176 — `gen_udp.py` の整備
