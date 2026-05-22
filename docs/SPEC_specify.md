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

## 5. tmg_when との関係

`MyExpectCell.tmg_when` が空でなければ `if (<when>) <specify>`、
空なら `<specify>` をそのまま出力する。

```
tmg_when="!i0&c0"  →  .v:  if (!D&E) <specify>
tmg_when=""        →  .v:  <specify>
```

`when` 文字列も `replace_by_portmap()` で実ポート名へ変換される。

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

- `charao/script/myExportLib.py`：specify ブロック生成（`if`/`ifnone`）、
  `.lib` timing の `when` / default block 生成
- `docs/SPEC_seq_lat.md`：LATCH の measure 仕様（clear/preset の when 整備）
