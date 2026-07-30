# Verilog specify 記述仕様

charao の `MyExpectCell.specify` フィールドの記述ルールを定める。
`specify` は生成される `.v`（Verilog タイミングモデル）の
`specify ... endspecify` ブロックに出力される。

---

## 1. 目的

`mylogic_*.py` の各 `MyExpectCell` が持つ `specify` 文字列の書式と、
`.v` 出力時の挙動（`if (when)` 分岐・`ifnone`）を明文化する。

---

## 2. specify ブロックとは

Verilog の `specify` ブロックは、 セルのパス遅延（path delay）と
タイミングチェック（`$setup` / `$hold` 等）を宣言する構文。
STA や論理シミュレーションでの SDF アノテーション対象となる。

charao は各セルの `.v` に `specify ... endspecify` を出力する。
遅延値そのものは常に `(0,0)` 等のプレースホルダで、 実値は `.lib` 側が持つ。
specify は **タイミング構造（どのピン間に arc があるか）の宣言**であり、
sim 計測値とは独立。

---

## 3. charao での生成

`myExportLib.py` が `logic_dict[<logic>]["expect"]` の各 `MyExpectCell` の
`specify` を走査し、 空でないものを集約して 1 つの `specify` ブロックを生成する。

ポート名は mylogic の logic port（`o0` / `i0` / `c0` / `r0` / `s0`）で記述する。
出力時に `replace_by_portmap()` で実ポート名（`Q` / `D` / `E` / `RN` / `SETN` 等）へ
変換される。

---

## 4. specify 文の種類

| 種類 | 書式例 | 用途 |
|------|--------|------|
| パス遅延（組合せ）| `(i0 => o0) = (0,0);` | 組合せパス |
| エッジ付きパス遅延 | `(posedge c0 => (o0 +: i0)) =(0,0);` | clock↑ → Q（同相 `+:`）|
| 〃（clear）| `(negedge r0 => (o0 +: 1'b0)) = (0,0);` | 非同期 reset |
| 〃（preset）| `(negedge s0 => (o0 -: 1'b1)) = (0,0);` | 非同期 set |
| `$setup` | `$setup(posedge i0, negedge c0, 0, notifier);` | セットアップ制約 |
| `$hold` | `$hold(negedge c0, negedge i0, 0, notifier);` | ホールド制約 |
| `$recovery` | `$recovery(posedge r0, negedge c0, 0, notifier);` | recovery 制約 |
| `$removal` | `$removal(posedge r0, negedge c0, 0, notifier);` | removal 制約 |
| `$width` | `$width(posedge c0, 0, 0, notifier);` | 最小パルス幅 |

- パス遅延の `+:` は同相（data 値をそのまま伝搬）、 `-:` は逆相。
- `1'b0` / `1'b1` は固定値伝搬（clear→0 / preset→1）。
- 制約系（`$setup` 等）の第 1 引数が constraint pin、 第 2 引数が基準 edge。

---

## 5. tmg_when との関係（条件付けの記法）

`MyExpectCell.tmg_when` が空でなければ条件を付与する。**付与の記法は
specify の種類で異なる**（ISS-00147, 2026-07-18）。

| specify の種類 | 条件付けの記法 | 例（tmg_when="r0"）|
|----------------|----------------|--------------------|
| **module path**（`(...) => (...)`）| `if (<when>) <path>` を前置 | `if (RN) (negedge RN => (Q +: 1'b0)) = (0,0);` |
| **timing check**（`$setup`/`$hold`/`$width`/`$recovery`/`$removal`）| **第 1 イベント引数に `&&& (<when>)`** を付与 | `$setup(posedge D &&& (RN), negedge CLKN, 0, notifier);` |

- **重要**：timing check に `if (<when>)` を前置するのは **Verilog 文法違反**
  （`syntax error in specify block`）。system timing check は `if` 前置不可で、
  条件は必ずイベント式内の `&&&` で表す。module path のみ `if` 前置が合法。
- `when` 空なら条件なしでそのまま出力する。
- 実装：`myExportLib.py` が `specify.lstrip().startswith("$")` で timing check を
  判別し分岐する。`when` は `replace_by_portmap()` で実ポート名へ変換される。

```
tmg_when=""        →  .v:  <specify>
tmg_when="i0&!c0"  (path)  →  .v:  if (D&!E) <path>
tmg_when="r0"      (check) →  .v:  $setup(<evt1> &&& (RN), <evt2>, ...);
```

### when 条件の各 pin 値の作り方

`tmg_when` に含まれる pin は、 sim 時にその論理状態を実際に作る必要がある。
pin の役割により作り方が異なる：

- **input pin（`pin_oirc[1]`）**：t_init→t_in で遷移しうる。 when の値（= 計測時の値）は
  **`mondrv_oirc[1]`（t_in の値、 `0`/`1`）**で指定する。 `ival["i"]`（t_init の値）は
  measure 前の内部状態初期化に使い、 `ival["i"]` と `mondrv_oirc[1]` が異なれば
  `arc_oirc[1]` を遷移（`r`/`f`）、 同じなら `s` にする
- **related / clock pin で計測中 static なもの**：`ival` の該当キー（`c`/`r`/`s`）で
  固定値（`0`/`1`）を指定する

例：latch clear の when `!D&!E`（D=0, E=0）— D（`pin_oirc[1]`）は `ival["i"]=1`
（t_init で内部状態 IQ2=1→Q=1 を作る）、 `mondrv_oirc[1]=0`（t_in = when の `!D`）、
`arc_oirc[1]="f"`。 E は `ival["c"]=0`（static）。

注：output（`pin_oirc[0]`）の初期化に `u`/`d`（`.IC`）を使う方法は tri-state（Hi-Z
ノード）専用で、 latch/FF の内部状態は作れない。 内部状態を要する when は上記の
input pin 取り込み方式で作る。

---

## 6. ifnone（`;;` サフィックス）

`specify` 文字列が **`;;`（セミコロン 2 個）で終わる**と ifnone フラグが立ち、
`if (<when>) <specify>` に加えて `ifnone <specify>` も出力される。

- **用途**：when 付きの timing arc 群に対し、「上記 when のいずれにも
  該当しない条件」 のデフォルト arc を `.v` specify に宣言する。
- `;;` は出力時に `;` 1 個へ正規化される。
- 例：

  ```
  specify="(i0 => o0) = (0,0);;"  かつ  tmg_when="active"
    →  .v:  if (active) (i0 => o0) = (0,0);
            ifnone     (i0 => o0) = (0,0);
  ```

### 6.1 ifnone × edge-sensitive path の切替（`` `ifdef D_USE_IFNONE_SIMPLE ``）

`ifnone` を **edge-sensitive path**（`(negedge r0 => (o0 +: 1'b0))` 等）に
付けると、**iverilog は非対応**（`Sorry: ifnone with an edge-sensitive path is
not supported`）。一方 VCS/Xcelium 等の商用ツールは対応する。iverilog も
使えるよう、edge-sensitive な ifnone は `` `ifdef `` で **simple path と
切替可能**に出力する（ISS-00147, 2026-07-18）。

- **既定（define なし）**：edge-sensitive のまま（フル忠実度）
- **`+define+D_USE_IFNONE_SIMPLE`**：ifnone を simple path 化
  （`(negedge r0 => (o0 +: 1'b0))` → `(r0 => o0)`）
- **iverilog 利用時**：`iverilog +define+D_USE_IFNONE_SIMPLE ...` として使う

出力例（latch clear アーク）：

```verilog
if (!D&!E) (negedge RN => (Q +: 1'b0)) = (0,0);   // SDPD は edge のまま
if (D&!E)  (negedge RN => (Q +: 1'b0)) = (0,0);
`ifdef D_USE_IFNONE_SIMPLE
  ifnone (RN => Q) = (0,0);                         // simple（iverilog 対応）
`else
  ifnone (negedge RN => (Q +: 1'b0)) = (0,0);       // edge（既定・商用ツール）
`endif
if (D&E)   (negedge RN => (Q +: 1'b0)) = (0,0);
```

- 対象は edge-sensitive path の ifnone のみ（simple path の ifnone は
  そのまま出力し `` `ifdef `` で囲まない）。
- iverilog 対応の可否（実測）：素の edge / SDPD(`if`) edge / edge SDPD + simple
  ifnone / 全 simple は **可**、`ifnone` × edge のみ **不可**。
- gf180mcuC7t での該当：latch の clear/preset アーク（`;;` 付き）計 12 箇所。

---

## 6.2 notifier の宣言と接続（`reg notifier` / primitive N ポート）

timing check（`$setup` 等）の第 4 引数 `notifier` は **`reg` 型**で、制約違反時に
値がトグルし、それを受けた sequential primitive（UDP）の出力を X 化する
（違反を出力に伝播させる標準機構）。iverilog は未宣言でも implicit wire として
通すが、厳密ツールは `reg` を要求し、wire では notifier が機能しない。

charao の seq セルは `mylogic_*.py` の **vcode** で primitive をインスタンス化する。
そのため notifier の宣言・接続は **vcode 内で自己完結**させる（ISS-00147,
2026-07-18）。

- **宣言**：vcode 先頭に `reg notifier;` を置く。
- **接続**：primitive 末尾の **N ポート**へ notifier を接続する。
  charao の 4 primitive は末尾が N（notifier）：
  `udp_iq_ff_n (Q, C, P, CK, D, N, VPWR, VGND)` / `udp_iq_ff_hn(...)` /
  `udp_iq_latch_n(...)` / `udp_iq_latch_hn(...)`。

```
"vcode":"reg notifier; ... udp_iq_ff_n inst (iq1, 1'b0, p_int, clkn_int, d_int, notifier); not (Q, iq1);"
```

- **注意**：vcode を持つセルは `myExportLib.py` の `if targetCell.vcode:` 経路で
  出力され、`isflop` 分岐（`reg notifier;` を出す旧経路）は**スキップ**される。
  gf180mcuC7t の seq 54 セルは全て vcode 経由のため、宣言は vcode 側で行う。
- comb / io / tri-state セルは timing check を持たないため notifier 不要
  （vcode があっても宣言・接続しない）。
- 対象 vcode：`mylogic_seq_ff.py`(8) / `mylogic_seq_scan.py`(4) /
  `mylogic_seq_lat.py`(6) の計 18 本。

---

## 7. `.lib` timing block との対応

`specify` は `.v` 専用。 `.lib` の `when` / default block は別フィールドで制御する。
同じ `MyExpectCell` から生成されるが、 出力経路は独立している。

| | `.v` specify | `.lib` timing block |
|---|-------------|--------------------|
| 条件分岐 | `if (<when>)` ← `tmg_when` | `when : "..."` ← `tmg_when` |
| デフォルト | `ifnone` ← specify の `;;` | when-less default block ← `timing_default=True` |

orig vendor lib の `ifnone { timing_type:clear; ... }` 相当を charao で出すには、
`.v` 側は specify を `;;` で終え、 `.lib` 側は当該 `MyExpectCell` に
`timing_default=True` を設定する（両者はそれぞれ独立に指定が必要）。

---

## 8. 参照

- `charao/script/myExportLib.py`：specify ブロック生成（timing check の `&&&`
  条件化 / module path の `if` / `ifnone` の `` `ifdef `` 切替）、`reg notifier`
  宣言経路（vcode 経路 / isflop 経路）、`.lib` timing の `when` / default block 生成
- `charao/script/mylogic_seq_ff.py` / `mylogic_seq_scan.py` /
  `mylogic_seq_lat.py`：seq セルの vcode（primitive インスタンス＋`reg notifier`＋
  N ポート接続）、UDP primitive 定義（`udp_iq_ff_n` / `_hn` / `udp_iq_latch_n` / `_hn`）
- `docs/SPEC_seq_lat.md`：LATCH の measure 仕様（clear/preset の when 整備）
- Verilog マクロ `D_USE_IFNONE_SIMPLE`：iverilog 利用時に `+define+` で指定し、
  ifnone×edge-sensitive を simple path 化する（§6.1）
