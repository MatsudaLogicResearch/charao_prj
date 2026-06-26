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
| `b` | biport | [0]/[1]/[2] | 双方向ピン（inout、 bus_hold 等）。 同一 pin を output/input/related スロット全部に置く |

`c` / `r` / `s` は**遷移型信号**で、 `pin_oirc[3]`（clock スロット）にも使える。
`b`（biport）は output/input/related を兼ねる単一 net。 ival キーは独自に `"b"`、 値は `0`/`1` のみ使用可能（例：`ival={"o":[],"i":[],"b":["0"]}`）。 HOLD 等の bus_hold セル用。

### 3.1 ival キーと pin index 対応（2026-06-11 明示化）

`ival` は dict 構造で、 各 key（`"o"`/`"i"`/`"c"`/`"r"`/`"s"`/`"b"`）の値は **list**（各 pin の値）。 list の index は同種 pin の番号に対応：

| ival key | list の各 index 対応 pin |
|---|---|
| `ival["o"]` | `[o0, o1, ...]`：output pin 群（通常 1 個）|
| `ival["i"]` | `[i0, i1, i2, ...]`：input pin 群（D, SI, SE 等）|
| `ival["c"]` | `[c0, c1, ...]`：clock pin 群 |
| `ival["r"]` | `[r0, r1, ...]`：reset pin 群 |
| `ival["s"]` | `[s0, s1, ...]`：set pin 群 |
| `ival["b"]` | `[b0, b1, ...]`：biport pin 群 |

**例**：`ival={"o":["0"],"i":["1","0","0"],"c":["p"],"r":["1"],"s":["1"]}` は
- `o0=0`、 `i0=1`/`i1=0`/`i2=0`（D=1, SI=0, SE=0）、 `c0=p`（CLK init pulse）、 `r0=1`（RN inactive）、 `s0=1`（SETN inactive）。

---

## 4. ival 値定義（確定）

| ival 値 | init 前半<br>（0〜_t_init1）| init 後半<br>（_t_init2〜_t_init3）| output[0] | input[1] | clock[3] | related[2]＝r/s | 用途 |
|---------|------|------|----|----|----|----|------|
| `0` | L | L | ○ | ○ | ○ | ○ | L 固定 |
| `1` | H | H | ○ | ○ | ○ | ○ | H 固定 |
| `r` | L | H |  |  | ○ |  | clock init 内 rise（_t_init1〜2 で遷移）|
| `f` | H | L |  |  | ○ |  | clock init 内 fall |
| `p` | L→H | H→L |  |  | ○ |  | pos-edge pulse（旧 `clk_init=pulse` 相当）|
| `n` | H→L | L→H |  |  | ○ |  | neg-edge pulse |
| `u` | H 強制 | H 強制 | ○ | ○ |  |  | Hi-Z を `.IC`＋pre-charge SW で H 初期化 |
| `d` | L 強制 | L 強制 | ○ | ○ |  |  | Hi-Z を `.IC`＋pre-charge SW で L 初期化 |
| `z` | open | open（純 Hi-Z）| ○ |  |  |  | 純 Hi-Z（`.IC`/SW なし）|

**ポートタイプ列の意味**：
- `output[0]` = `pin_oirc[0]`
- `input[1]` = `pin_oirc[1]`（clock/reset/set 以外）
- `clock[3]` = `pin_oirc[3]`
- `related[2]` = `pin_oirc[2]`（reset/set。 VREL は遷移できないので `ival` は `0`/`1` のみ）
- `biport[0]/[1]/[2]` = `pin_oirc[0]=[1]=[2]` 同一 pin。 ival キーは `"b"` を使用、 値は `0`/`1` のみ

**補足**：
- `r`/`f`：前半・後半で値固定、 遷移は期間境界（`_t_init1`〜`_t_init2`）。 **clock 専用**（VIN/VREL は遷移不可）
- `p`/`n`：各期間内で遷移（`p` = 前半 rise ＋ 後半 fall）。 **clock 専用**（旧 `clk_init=pulse` を吸収）
- `u`/`d`：output/input のみ。 related は `0`/`1` のみで `u`/`d` 不可
- `z`：output のみ。 input/related の `z` は未サポート（ISS-00102）
- `u`/`d`：driver は接続しないが、 output（`pin_oirc[0]`）が Hi-Z でも `.meas` を成立させるため、
  `.IC` と pre-charge SW（ISS-00076、 `u`=`"1"` 群／`d`=`"0"` 群）で WOUT を H/L に初期化する。
  input/related の `u`/`d` は VIN/VREL を `.IC` で H/L 初期化（pre-charge SW なし）。
- `z`：`.IC` も pre-charge SW も接続しない純 Hi-Z（外部からの初期化なし）。
- **biport (`b`)**：HOLD 等 bus_hold セル用。 ival キー `"b"` に `0`/`1` のみ指定可（`r`/`f`/`p`/`n`/`u`/`d`/`z` 使用不可）。 単一 net を VIN/VREL/WOUT 全てに割り当て、 弱駆動素子（bus_hold）の動作を観測する。
- pull 抵抗（`pullres_role`、 §6.4）は `ival` とは独立した別機構で、 `u`/`d`/`z` とは無関係。

---

## 5. arc_oirc 値定義（確定）

`arc_oirc` は計測フェーズ（input→`_t_in`、 related→`_t_rel`、 clock→`_t_clk4` 以降）の
各 pin の挙動を表す。 旧 `s`（static）は計測フェーズ値が init 終値依存だったため廃止し、
`0`/`1` で計測フェーズの静的値を**明示**する。

| arc 値 | 意味 | output[0] | input[1] | related[2] | clock[3] |
|--------|------|-----------|----------|------------|----------|
| `r` | rise（L→H、 以後 H 維持）| ○ | ○ | ○ | ○ |
| `f` | fall（H→L、 以後 L 維持）| ○ | ○ | ○ | ○ |
| `0` | static L | ○ | ○ | ○ | ○ |
| `1` | static H | ○ | ○ | ○ | ○ |
| `p` | pos-edge pulse（L→H→L、 1 パルス）|  |  | ○ | ○ |
| `n` | neg-edge pulse（H→L→H、 1 パルス）|  |  | ○ | ○ |
| `z` | Hi-Z | ○（予定）|  |  |  |

- **`s`（旧 static）は廃止**。 移行期はコード側で後方互換受理するが、 mylogic 変換完了後に最終削除。
- `p`/`n` は min_pulse_width 計測用。 **clock[3] と related[2] で使用可**：`pin_oirc[2]==pin_oirc[3]`（VREL と VCLK が同一 pin を駆動）のケースで arc[2]==arc[3]=p/n の整合性が必要なため、 related[2] も p/n 対応（jp2 で実装、 2026-06-11 確定）。
- `z`：output[0] の three_state arc 用（使用予定）。 input/related の `z` は未サポート（ISS-00102）、 clock の `z` も未サポート。
- `ival` の `r`/`f`（init 内遷移）と `arc_oirc` の `r`/`f`（計測フェーズ遷移）は同記号だが**期間が別**（二層構造）。

---

## 6. 全条件網羅表

### 6.1 ival × arc_oirc → 各期間の値

`ival` が init 期間の値、 `arc_oirc` が計測フェーズの値（遷移 or 静的）を決める。
計測後の値（rval、 旧 `mondrv_oirc` 相当）は **`arc_oirc` から直接導出**する。

**整合制約**：ival 後半値（init 終値）と `arc_oirc[i]` は整合する必要：
- 後半 L（ival=`0`/`f`/`d`）→ arc は `0`（static L）／`r`（rise）／`p`（pos pulse）
- 後半 H（ival=`1`/`r`/`u`）→ arc は `1`（static H）／`f`（fall）／`n`（neg pulse）
- 不整合（例：後半 L＋arc=`f`）は ERROR

**rval 導出**：

| arc 値 | rval（計測フェーズ最終値）|
|---|---|
| `0` | L |
| `1` | H |
| `r` | H（L→H、 以後 H 維持）|
| `f` | L（H→L、 以後 L 維持）|
| `p` | L（1 パルス後、 init 終値 L に戻る）|
| `n` | H（1 パルス後、 init 終値 H に戻る）|
| `z` | Hi-Z |
| `s`（旧）| ival 後半値（移行期、 後方互換）|

→ `arc=s` は廃止予定で、 ival 後半値依存（「前の値を覚える」必要）だったが、 新仕様の `0`/`1` で
計測フェーズの値を明示化することで解消。 `mondrv_oirc` は明示フィールドから廃止し charao 内で導出可能。

### 6.2 ポートタイプ別の testbench 実装

| ポート | testbench 信号 | init 期間（`ival`）| 計測フェーズ（`arc_oirc`）|
|--------|----------------|--------------------|---------------------------|
| `o`（output）| WOUT | `0`/`1`/`u`/`d`→WOUT pre-charge SW（ISS-00076）＋`.IC` で L/H 強制（`u`=H／`d`=L）、 `z`→初期化なし | arc[0]=`r`/`f`→出力遷移を計測、 `0`/`1`→static（計測なし）、 `z`→Hi-Z（予定）|
| `i`（input）| VIN | val_oirc[1]=`0`/`1`→init 部 PWL の初期値 `_vss_vin`/`_vdd_vin` 決定（2026-06-11 jp2 拡張）、 **`u`/`d`/`r`/`f`/`p`/`n` 不可**（input は遷移不可）| arc[1]=`0`/`1`→static PWL、 `r`/`f`→`_t_in0`〜`_t_in1` 遷移 PWL、 `p`/`n` 不可（input は pulse 不要） |
| `r`/`s`（related）| VREL | val_oirc[2]=`0`/`1`→init 部 PWL の初期値 `_vss_vrel`/`_vdd_vrel` 決定（2026-06-11 jp2 拡張）、 **`u`/`d`/`r`/`f`/`p`/`n` 不可**（related は遷移不可）| arc[2]=`0`/`1`→`_t_rel0` static、 `r`/`f`→`_t_rel1` まで edge、 `p`/`n`→`_t_rel3` まで round trip pulse |
| `c`（clock）| VCLK | `0`/`1`→stable、 `p`/`n`→init 内 1 パルス PWL（`_t_clk0..3`）、 `r`/`f`→init 内 rise/fall（戻さない）| arc[3]=`r`/`f`/`0`/`1`/`p`/`n`→`_t_clk4` 以降。 **`clk_role` 不使用**（arc[3] のみで決定）|
| `b`（biport）| VIN/VREL/WOUT 共有（同 net 接続）| `b:0`/`b:1` で `.IC`+pre-charge SW により H/L 初期化（output 兼用）| arc[0]/[1]/[2] が揃って `r`/`f` で biport slew→`q_in_dyn` で power_tin / leakage を計測（HOLD 等 bus_hold セル）|

### 6.3 廃止対象パラメータの導出

| 廃止対象 | 導出方法 |
|----------|----------|
| `mondrv_oirc` | `arc_oirc` から直接（§6.1）。 `r`→H、 `f`→L、 `0`→L、 `1`→H、 `p`/`n`→pulse 後の値（init 終値）、 `z`→Hi-Z |
| `clk_role` | **完全廃止**。 VCLK 計測部は `arc_oirc[3]` だけで決定（related と input+rise の計測部波形が同一だったため、 区別不要）|
| `clk_init` | clock pin の `ival[3]` で吸収（`0`/`1`→stable、 `p`/`n`→pulse、 `r`/`f`→init 内遷移）|

### 6.4 pullres_role（three_state arc 用 external pull、 ival とは独立）

three_state_enable/disable arc の計測では output が Hi-Z の区間に external pull で
WOUT を駆動し遷移を作る。 `pullres_role` で制御され、 `ival` 値とは独立した別機構
（`charao_run.py` が `arc_oirc` と cell の `oe_infos` から自動設定）。

| pullres_role | 機構 | 適用 measure |
|--------------|------|--------------|
| `nouse` | pull なし | delay/power/leakage（three_state 以外すべて）|
| `up`/`down` | 固定抵抗 `R0` で WOUT を VDD/VSS に pull | three_state_enable |
| `up_ngate`/`up_pgate`/`down_ngate`/`down_pgate` | SW（cell の oe-driver gate 連動）| three_state_disable |

- enable：`arc_oirc[0]=r`→`down` / `f`→`up`（output と逆極性に初期 pull）
- disable：`arc_oirc[0]`＋cell type（nmos/pmos）から `*_ngate`/`*_pgate`、 gate ノードは `oe_infos[outport]["drv0"/"drv1"]["gate"]`
- 抵抗値 `pullres`：enable 時 ~100kΩ（弱 pull）、 disable 時 ~0.1Ω（強制 drive）。 std/io で別値（`myLibrarySetting`）

---

## 7. 参照

- 関連 issue：ISS-00101（本仕様）、 ISS-00082（min_pulse_width when）、
  ISS-00090（LAT when 整備）、 ISS-00097（u/d 妥当性）、 ISS-00098（mondrv_oirc 整合）
- 実装ファイル：`charao/script/temp_testbench.sp.jp2`、 `charao/script/myExpectCell.py`、
  `charao/script/charao_run.py`、 `charao/script/myTbParam.py`
