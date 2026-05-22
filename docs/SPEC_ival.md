# ival / arc_oirc 波形仕様

charao の `MyExpectCell` の `ival` / `arc_oirc` の値定義と、 testbench への
適応タイミングを定める（ISS-00101）。

---

## 1. 目的

sim の波形を `ival`（init 期間の各 pin 値）と `arc_oirc`（計測フェーズの遷移）の
2 フィールドで一元的に表現する。 従来の `mondrv_oirc` / `clk_role` / `clk_init` は
本仕様へ吸収し、 必要時 charao 内で導出する。

---

## 2. 期間定義

testbench の時間軸を 3 期間に分ける：

| 期間 | 時刻範囲 | 内容 |
|------|----------|------|
| init 前半 | 0ns 〜 `_t_init1` | 0ns に初期値。 `_t_init1` まで前半値 |
| init 後半 | `_t_init2` 〜 `_t_init3` | 後半値。 `_t_init1`〜`_t_init2` が遷移帯 |
| 計測フェーズ | `_t_in*` / `_t_rel*` / `_t_clk4` 以降 | `arc_oirc` が支配 |

`ival` は init 前半・後半の値を、 `arc_oirc` は計測フェーズの遷移を指定する。

時刻は `myTbParam.compute_timing()` が算出（`t_init0..3` → `t_in0/1` → `t_rel0..3` →
`t_clk0..7`）。

---

## 3. ポートタイプ（o / c / r / s / i）

`pin_oirc` の各要素のポート役割：

| 記号 | ポート | pin_oirc スロット | 説明 |
|------|--------|-------------------|------|
| `o` | output | [0] | 出力ピン |
| `i` | input | [1] | 入力ピン（clock/reset/set 以外）|
| `r` | reset | [2] | 非同期リセット（related の一種）|
| `s` | set | [2] | 非同期セット（related の一種）|
| `c` | clock | [3] | クロックピン |

`c` / `r` / `s` は**遷移型信号**で、 `pin_oirc[3]`（clock スロット）にも使える。

---

## 4. ival 値定義（確定）

| ival 値 | init 前半<br>（0〜_t_init1）| init 後半<br>（_t_init2〜_t_init3）| o | c,r,s | i | 用途 |
|---------|------|------|----|-------|----|------|
| `0` | L | L | ○ | ○ | ○ | L 固定 |
| `1` | H | H | ○ | ○ | ○ | H 固定 |
| `r` | L | H |  | ○ | ○ | init 内 rise（_t_init1〜2 で遷移）|
| `f` | H | L |  | ○ | ○ | init 内 fall |
| `p` | L→H | H→L |  | ○ |  | pos-edge clock の pulse（clk_init=pulse）|
| `n` | H→L | L→H |  | ○ |  | neg-edge clock の pulse |
| `u` | open | open + `.IC`=H | ○ |  | ○ | bidir/tri-state（H 初期）|
| `d` | open | open + `.IC`=L | ○ |  | ○ | bidir/tri-state（L 初期）|
| `z` | open | open（純 Hi-Z）| ○ |  | ○ | bidir/tri-state（Hi-Z）|

**ポートタイプ列の意味**：
- `o` = output（`pin_oirc[0]`）
- `c,r,s` = 遷移型信号 clock / reset / set（`pin_oirc[2]` related・`pin_oirc[3]` clock）
- `i` = input（clock/reset/set 以外、 `pin_oirc[1]`）

**補足**：
- `r`/`f`：前半・後半で値固定、 遷移は期間境界（`_t_init1`〜`_t_init2`）
- `p`/`n`：各期間内で遷移（`p` = 前半 rise ＋ 後半 fall）。 clock 専用
- `o`（output）に `r`/`f`/`p`/`n` は現状未使用
- `u`/`d`/`z` は driver を接続せず `.IC` で初期化（bidir/tri-state 用）

---

## 5. arc_oirc 値定義（確定）

| arc 値 | 意味 | 適応期間 |
|--------|------|----------|
| `r` | rise（L→H）| input→`_t_in`、 related→`_t_rel`、 clock→`_t_clk4` 以降 |
| `f` | fall（H→L）| 同上 |
| `s` | static（遷移なし）| — |

`ival` の `r`/`f`（init 内遷移）と `arc_oirc` の `r`/`f`（計測フェーズ遷移）は
同じ記号だが**期間が別**（二層構造）。

---

## 6. 全条件網羅表

### 6.1 ival × arc_oirc → 各期間の値

`ival` が init 前半・後半、 `arc_oirc` が計測フェーズの遷移を決める。
計測後の値（rval、 旧 `mondrv_oirc` 相当）は **ival 後半値に arc を適用**して導出する。

| ival | init 前半 | init 後半 | arc=`s` | arc=`r` | arc=`f` | rval（計測後）|
|------|-----------|-----------|---------|---------|---------|---------------|
| `0` | L | L | L 静止 | L→H | （不可：後半 L）| s→L / r→H |
| `1` | H | H | H 静止 | （不可：後半 H）| H→L | s→H / f→L |
| `r` | L | H | H 静止 | （不可）| H→L | s→H / f→L |
| `f` | H | L | L 静止 | L→H | （不可）| s→L / r→H |
| `p` | L→H→L（pulse）| — | clock 計測は `_t_clk4` 以降（arc[3]）| | | — |
| `n` | H→L→H（pulse）| — | 同上 | | | — |
| `u` | open | open + `.IC`=H | Hi-Z 保持 | — | — | bidir 結果値 |
| `d` | open | open + `.IC`=L | Hi-Z 保持 | — | — | bidir 結果値 |
| `z` | open | open（Hi-Z）| Hi-Z 保持 | — | — | bidir 結果値 |

- **arc と ival 後半値の整合制約**：後半 L（`0`/`f`）→ arc は `s` または `r` のみ、
  後半 H（`1`/`r`）→ arc は `s` または `f` のみ。 不整合は ERROR とする。
- **rval 導出**：arc=`s`→ival 後半値そのまま、 arc=`r`→H、 arc=`f`→L。
  これにより `mondrv_oirc` は明示フィールドから廃止し charao 内で導出可能。

### 6.2 ポートタイプ別の testbench 実装

| ポート | testbench 信号 | init 期間（`ival`）| 計測フェーズ（`arc_oirc`）|
|--------|----------------|--------------------|---------------------------|
| `o`（output）| WOUT | `0`/`1`→WOUT pre-charge SW（ISS-00076）で L/H 強制、 `u`/`d`/`z`→`.IC` | arc[0]=`r`/`f` で出力遷移を計測、 `s` は計測なし |
| `i`（input）| VIN | `ival` 前半/後半値で PWL knot（`_t_init0/1/2/3`）、 `u`/`d`/`z`→`.IC` | arc[1]=`r`/`f` で `_t_in0`〜`_t_in1` に遷移 PWL |
| `r`/`s`（related）| VREL | 同上（`_t_init*` の PWL knot）| arc[2]=`r`/`f` で `_t_rel0`〜`_t_rel1` に遷移 PWL（pulse は `_t_rel2/3`）|
| `c`（clock）| VCLK | `0`/`1`→stable、 `p`/`n`→pulse PWL（`_t_clk0..3`）| arc[3]=`r`/`f` で `_t_clk4..7` に clock サイクル |

### 6.3 廃止対象パラメータの導出

| 廃止対象 | 導出方法 |
|----------|----------|
| `mondrv_oirc` | ival 後半値 + arc_oirc（6.1）から rval を charao 内で生成 |
| `clk_role` | clock pin（`pin_oirc[3]`）の arc_oirc が `r`/`f`/`s` のいずれか、 および related/input の役割は pin_oirc スロットから判定 |
| `clk_init` | clock pin の ival 値が `p`/`n`（=pulse）か `0`/`1`（=stable）かで決定 |

---

## 7. 参照

- 関連 issue：ISS-00101（本仕様）、 ISS-00082（min_pulse_width when）、
  ISS-00090（LAT when 整備）、 ISS-00097（u/d 妥当性）、 ISS-00098（mondrv_oirc 整合）
- 実装ファイル：`charao/script/temp_testbench.sp.jp2`、 `charao/script/myExpectCell.py`、
  `charao/script/charao_run.py`、 `charao/script/myTbParam.py`
