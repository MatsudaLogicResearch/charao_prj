# charao measure_type 仕様書

charao の各 measure_type（`meas_types` フィールドに指定する値）の計測内容、 sim 動作、 .lib 出力先、 Liberty 標準（orig vendor）との対応を定義する（ISS-00111）。

mylogic 修正の方向性決定と、 orig との乖離（ISS-00108 / ISS-00109 / ISS-00110）の解消に向けた基準書。

---

## 1. 目的

- charao の measure_type を整理し、 各々の **何を計測しているか** / **sim で何が動くか** / **.lib のどの field に出力されるか** を明確化
- orig vendor の Liberty 標準と対応付け、 **過剰実装**（charao 独自）と **欠落**（orig 必須）を識別
- ISS-00101（ival/arc 値モデル刷新） の mylogic 修正方針を後戻りなく決めるための上位仕様

---

## 2. 用語

| 用語 | 意味 |
|------|------|
| **VIN** | testbench で `pin_oirc[1]` に対応する pin の波形 |
| **VREL** | testbench で `pin_oirc[2]` に対応する pin の波形（計測対象） |
| **VCLK** | testbench で `pin_oirc[3]` に対応する pin の波形 |
| **VOUT** | testbench で `pin_oirc[0]` に対応する pin の波形（出力観測） |
| **slew 期間** | input pin が rise/fall する遷移時間（`_t_rel0` 〜 `_t_rel1` 等）|
| **active edge** | DFF: CLK rise (posedge) / LATCH: E fall (close)、 内部状態が確定する edge |
| **transparent** | LATCH の E=H 状態（D 透過、 Q = D 直結）|
| **closed** | LATCH の E=L 状態（D lock、 Q = 前値保持）|

---

## 3. measure_type 一覧

charao 内部で使用される measure_type 全体：

| # | measure_type | 計測種別 | 主な対象 family | Liberty 対応 |
|---|--------------|----------|-----------------|--------------|
| 1 | `delay` | prop delay + transition | comb / seq_lat (combinational) | `timing_type: combinational` |
| 2 | `rising_edge` | prop delay + transition | seq_ff / seq_scan / seq_lat | `timing_type: rising_edge` |
| 3 | `falling_edge` | prop delay + transition | seq_ff (NC 系) / seq_scan | `timing_type: falling_edge` |
| 4 | `setup_rising` | setup constraint | seq_ff (posedge) / seq_scan | `timing_type: setup_rising` |
| 5 | `setup_falling` | setup constraint | seq_ff (negedge) / seq_lat | `timing_type: setup_falling` |
| 6 | `hold_rising` | hold constraint | seq_ff (posedge) / seq_scan | `timing_type: hold_rising` |
| 7 | `hold_falling` | hold constraint | seq_ff (negedge) / seq_lat | `timing_type: hold_falling` |
| 8 | `recovery_rising` | async recovery | seq_ff (posedge) / seq_lat | `timing_type: recovery_rising` |
| 9 | `recovery_falling` | async recovery | seq_ff (negedge) / seq_lat (negedge LAT) | `timing_type: recovery_falling` |
| 10 | `removal_rising` | async removal | 同上 | `timing_type: removal_rising` |
| 11 | `removal_falling` | async removal | 同上 | `timing_type: removal_falling` |
| 12 | `clear` | RN fall → Q async prop | RN を持つ family | `timing_type: clear` |
| 13 | `preset` | SETN fall → Q async prop | SETN を持つ family | `timing_type: preset` |
| 14 | `min_pulse_width_high` | H pulse 最小幅 | CLK / E / RN / SETN | `timing_type: min_pulse_width`（`rise_constraint`）|
| 15 | `min_pulse_width_low` | L pulse 最小幅 | 同上 | `timing_type: min_pulse_width`（`fall_constraint`）|
| 16 | `power_tout` | output 遷移時の dynamic energy | 全 family | `internal_power { rise_power / fall_power }`（output pin 内）|
| 17 | `power_tin` | input pin slew 時の dynamic energy | 全 family | `internal_power { rise_power / fall_power }`（input pin 内）|
| 18 | `passive` | output 無いセルの input pin capacitance 算出 | ANTENNA / filler 等 | `pin (<input>) { capacitance }` |
| 19 | `leakage` | DC 動作点(`op`)での static leak 電力＝`min(p_supply, p_absorb)`＋`leakage_offset`（§4.12）| 全 family（物理セルは measure-less）| `leakage_power { when ; value }` |

### Liberty 標準で必要だが charao に欠落

| 欠落 measure / timing_type | 説明 | 影響 family |
|----------------------------|------|-------------|
| `minimum_period` | clock の最小周期（`min_pulse_high + min_pulse_low`）| 全 seq_ff / seq_scan |
| `non_seq_setup_rising` | RN/SETN 等 async pin 間の setup 制約 | RN/SETN 持つ DFF/LAT |
| `non_seq_hold_rising` | 同上の hold | RN/SETN 持つ DFF/LAT |
| `three_state_enable` | output enable 遷移の prop delay | comb_tristate (BUFZ/INVZ) |
| `three_state_disable` | output disable 遷移の prop delay | comb_tristate |

---

## 4. 各 measure_type の詳細

### 4.1 `delay`（combinational delay）

**計測内容**：
- 入力 pin → 出力 pin の **prop delay** と **output transition time**
- 組合せ回路、 または LATCH の D 透過時（E=H）の D→Q

**sim 動作**：
- VIN（入力 pin）を rise/fall させる
- VOUT（出力）の遷移を観測
- `chg_out` で VOUT が 50% を超える時刻を計測
- `prop_in_out` で VIN→VOUT delay 計測
- `trans_out` で VOUT の遷移時間計測（閾値は config 依存：gf180 は 30%→70% / 70%→30%
  ＝`logic_threshold_low/high`、default は 20%/80%）

**.lib 出力**：
- `pin (Q) { timing { related_pin: "<input>"; timing_type: "combinational"; cell_rise / cell_fall / rise_transition / fall_transition } }`
- **出力 transition の slew_derate（ISS-00157 / a31）**：`rise/fall_transition` は Liberty 規約に従い
  **格納値 = 実測（閾値間 30-70%）/ `slew_derate_from_library`**（gf180=0.5 → 格納値 = 実測 ×2）で格納する。
  `cell_rise/fall`（delay）や const 等の「時刻」値は slew_derate 非対象。config: `slew_derate_from_library`
  （`config_lib.jsonc`）、実装: `myConditionsAndResults.py` / `myExportLib.py`（`.lib`）・`myExportDoc.py`（`.md`）。

**`pin_oirc` 構成**：
- `[o0, i0, i0, c0]` (LATCH)：[1]=[2]=D で VIN=VREL=D 同時 slew、 [3]=E
- comb は `[o0, i0, ...]` で VIN=入力 pin

### 4.2 `rising_edge` / `falling_edge`（active edge → Q prop）

**計測内容**：
- active edge（DFF: CLK rise / negedge DFF: CLK fall / LATCH: E rise（open））→ Q の prop delay
- output transition time

**sim 動作**：
- init phase で DUT 内部状態確立（D 取り込み）
- 計測 phase で CLK or E の active edge で Q 遷移
- VOUT の 50% 通過時刻計測

**.lib 出力**：
- `pin (Q) { timing { related_pin: "CLK"/"E"; timing_type: "rising_edge"/"falling_edge"; cell_rise / cell_fall ... } }`

> **判定方式の現行仕様（2026-07-11）**：const 系（setup/hold/recovery/removal）の掃引は
> 実装上 **CLK 側（_t_clk4）を動かす**（D/async の遷移時刻は固定）。 pass/fail 判定は
> 遷移型（FF setup/hold、 recovery、 LAT setup）＝prop_clk_out の degradation、
> 保持型（LAT/ICG hold、 removal）＝電圧化け判定（judge_vlt）。 詳細は `SPEC_const.md` §1/§4 参照。

### 4.3 `setup_rising` / `setup_falling`

**計測内容**：
- D vs active edge の **setup time**（最小遅延）

**sim 動作**：
- secant 探索で D 遷移時刻を active edge に近づける
- Q が D 変化を取り込めなくなる境界 = 最小 setup time

**.lib 出力**：
- `pin (D) { timing { related_pin: "CLK"/"E"; timing_type: "setup_rising"/"setup_falling"; rise_constraint / fall_constraint } }`

### 4.4 `hold_rising` / `hold_falling`

**計測内容**：D vs active edge の **hold time**

**sim 動作**：D 遷移時刻を active edge より後ろにずらし、 Q が古い値を保持できる境界 = 最小 hold time

**.lib 出力**：
- `pin (D) { timing { related_pin: ...; timing_type: "hold_rising"/"hold_falling"; rise_constraint / fall_constraint } }`

### 4.5 `recovery_rising` / `recovery_falling`

**計測内容**：RN/SETN の rise（inactive 化）と active edge の **recovery time**

**sim 動作**：RN/SETN rise 時刻を active edge より前にして、 reset/set 動作が確実に解除される境界

**.lib 出力**：
- `pin (RN/SETN) { timing { related_pin: "CLK"/"E"; timing_type: "recovery_*"; rise_constraint } }`

### 4.6 `removal_rising` / `removal_falling`

**計測内容**：active edge と RN/SETN の rise の **removal time**

**.lib 出力**：
- `pin (RN/SETN) { timing { related_pin: ...; timing_type: "removal_*"; rise_constraint } }`

### 4.7 `clear` / `preset`

**計測内容**：RN fall / SETN fall → Q async prop delay

**sim 動作**：RN/SETN fall で Q がリセット / セットされる時刻を計測

**.lib 出力**：
- `pin (Q) { timing { related_pin: "RN"/"SETN"; timing_type: "clear"/"preset"; cell_fall / cell_rise / fall_transition / rise_transition } }`

### 4.8 `min_pulse_width_high` / `min_pulse_width_low`

**計測内容**：CLK / E / RN / SETN の H/L pulse 最小幅

**sim 動作**：pulse 幅を sweep し、 DUT が動作（D 取り込み or reset/set 完了）できなくなる境界。
**ISS-00160(a31) で slew-index テーブル化**：パルス対象ピンの slew（template `kind=mpw` の
`index_1`、gf180 は `[0.02, 0.8, 4.0]`、要素数は PDK 依存で任意）ごとに境界を探索し 1D テーブル化する。
旧 `simulation_slew_for_pulse`（固定 slew スカラー）は廃止（`myLibrarySetting.py`、`charao_run.py`）。

**.lib 出力**：
- `pin (CLK/E/RN/SETN) { timing { timing_type: "min_pulse_width"; rise_constraint (mpw_template_3x0) (high) / fall_constraint (low) } }`
  ＝ **Liberty timing() constraint テーブル**（`index_1 = constrained_pin_transition`、template は `config_lib.jsonc` の `kind=mpw`）
- **ISS-00160 で charao 独自 scalar field `min_pulse_width_high / min_pulse_width_low` は撤去**
  （Liberty 仕様上、timing() constraint が authoritative なため）

### 4.9 `power_tout`（output dynamic energy）

**計測内容**：output が rise/fall するときの dynamic energy

**sim 動作**：
- VOUT の遷移期間で I(VDD_DYN) を integrate
- input pin slope と output load の 2 次元 LUT

**.lib 出力**：
- `pin (Q) { internal_power { related_pin: "<active input>"; rise_power / fall_power } }`

### 4.10 `power_tin`（input dynamic energy）

**計測内容**：input pin が rise/fall するときの dynamic energy（input cap charge + 内部 logic switching）

**sim 動作**：
- VREL（pin_oirc[2] = 計測対象 input pin）を rise/fall
- slew 期間中の I(VDD_DYN) を integrate
- input pin slope の 1 次元 LUT

**.lib 出力**：
- `pin (<input>) { internal_power { related_pin: ""; rise_power / fall_power } }`

### 4.11 `passive`（**output 無いセル限定**）

**用途**：
- output pin を持たないセル（ANTENNA、 filler 等）の input pin の capacitance 算出
- `pin_oirc[0]=""` のとき input pin の slew だけで `q_in_dyn` を測り c_in を取得
- output ありセルは他 measure（delay / power_tout 等）の副産物として c_in を取得するため passive 不要（§9 参照）

**sim 動作**：
- VIN（`pin_oirc[1]` = 計測対象 input pin）を rise/fall
- slew 期間中の `q_in_dyn` を integrate → `c_in = abs(q_in_dyn) / vdd_voltage`

**.lib 出力**：
- `pin (<input>) { capacitance : <num> }`（passive 由来の独自 field なし）

### 4.12 `leakage`（DC leak）

**計測内容**：DUT 全 pin を DC stable に固定した状態の静的 leak 電力。state 組合せ（各 input の H/L、 seq/lat は保持値）ごとに 1 値。

> **重要（2026-07-25、ISS-00166/00167 で全面改訂）**：旧実装は tran の AVG（電源電流を時間平均）だったが、**seq/lat/icg は内部保持ノード（クロスカップル feedback＝高インピーダンス）の平衡時定数が μs 級**で、測定窓（init 後 10ns）では未静定 → 電流に変位電流（well 充電等、真 DC の 24〜46 倍）が混入し **orig の 5〜640 倍過大**になっていた（comb は電源に低抵抗直結で ps 静定のため無問題）。**現行は DC 動作点（`op`）で計測**する。制御は jp2 の `meas_energy==3` 分岐。

**sim 動作（B案＝tran で状態確立 → nodeset 書き戻し → op、`temp_testbench.sp.jp2`）**：
1. **tran で状態確立**：全 input source を arc の DC 値に設定して `run`。tran 長は `tslew_in = leakage_stable_time × time_mag`（内部保持ノードを静定させる。§SPEC_config_lib `leakage_stable_time`、gf180=1ns）
2. **内部ノード電圧を取得**：`meas tran v(<node>) find ... at=leak_meas_at`（`leak_meas_at = tsim_end − timestep_tmax`＝終端の僅か手前。厳密な終端は補間で "out of interval" になり得るため）。**内部ノード名は netlist から自動取得**（`myLogicCell.get_internal_nodes()`＝cell subckt を parse し全 Tr 端子から外部ポート（ports_dict キー）・モデル名・W=/L= を除いて列挙）
3. **nodeset に書き戻し**：取得値を `alterparam` で `.param n<i>_init` に代入 → `reset`
4. **DC 動作点**：input source を arc の DC hold 値に `alter` → `op`。`.nodeset v(xcell.xdut.<node>)={n<i>_init}` で **op の初期推定値**として与える（force ではなく Newton の初期値。双安定 hold 状態が正しい安定解へ収束するのを助ける）
5. **電源電流を出力**：`let`/`print` で 6 電流（i_vdd/i_vss/i_vnw/i_vpw/i_vddio/i_rel）を取得。旧 `.MEASURE i_*_leak` は無効化（jp2 で行頭 `*`）

**pleak の算出（ISS-00167、`charao_run.py:genFileLogic_LeakageTrial1x`）**：
```
p_supply = (i_vdd + i_vnw) × (Vdd − Vss)      # 供給側（電源から出る電流）
p_absorb = (i_vss + i_vpw) × (Vnw − Vpw)      # 吸収側（グランドへ入る電流）
pleak    = min(p_supply, p_absorb)            # ← min を採用（ISS-00167）
```
- 電荷保存より本来 `p_supply == p_absorb`（clean 状態は実測で比 1.00）
- **入力ピン経由の駆動電流は VDD 側か VSS 側の片方電源にしか出ない**（例：latch で set active & D=0 のとき `VDD→set駆動→内部→pass gate→D ピン(外部VSS)` の貫通で p_supply だけ大。逆向きなら p_absorb だけ大）。真の電源間リークは両側に均等に出るので、**`min` で片側だけ膨らんだ入力駆動成分を除去し真リークを保存**する（`max` は逆に貫通側を拾う＝旧バグ、`p_supply` 単独は VDD 側貫通を拾う。`min` が両方向の貫通を除ける唯一の式）

**leakage_offset の加算（ISS-00165、§SPEC_config_lib 3.1）**：
- 計測 pleak に **全セル一律の嵩上げ値**を加算：`h.pleak = rslt["pleak"] + leakage_offset × leakage_power_mag`
- orig−charao が駆動 1x〜20x の全域で一定（gf180 は 4.90〜5.00e-05）＝clamp でなく加算。gf180 config で `leakage_offset = 5e-05`

**物理セル（fill/fillcap/endcap/filltie、ISS-00165）**：
- 空 subckt（Tr 0）で sim 特性化不可 → **measure-less**。leakage は `leakage_offset` のみで付与（`mylogic_physical.py` の logic_type `"physical"`／`std_physical.jsonc` 専用ループ）

**.lib 出力**：
- `cell { leakage_power { when : "<state>" ; value : <uW> } }` を state 組合せ別に出力
- default 行も `leakage_power { value : ... }` として（orig）または `default_cell_leakage_power` field として（charao、 ISS-00108(8)）

**検証（全 229 セル回帰、2026-07-25）**：貫通ゼロ・comb 1.00x（不変）・seq(dff) 0.81x／lat 0.89x／icg 0.77x／physical 1.00x。seq/lat/icg の残る一律 0.72〜0.89x 系統オフセットは貫通と別種（ISS-00168、post-1.0.0 検討）

---

## 5. orig vs charao 構造比較（代表 cell）

| family | cell | pin | timing | int_pwr | **passive_pwr** | leak | timing_type 内訳 |
|--------|------|-----|--------|---------|-----------------|------|------------------|
| comb | inv_1 | 2 | 1 | 1 | **0** | 3 | combinational |
| comb | buf_1 | 2 | 1 | 1 | **0** | 3 | combinational |
| comb_complex | aoi21_1 | 4 | 6 | 12 | **0** | 9 | combinational |
| **comb_tristate** | bufz_1 | 3 | 3 | 5 | **0** | 5 | combinational + **three_state_enable** + **three_state_disable** |
| seq_ff | dffq_1 | 3 | 7 | 5 | **0** | 5 | rising_edge + setup/hold_rising + min_pulse_width + **minimum_period** |
| seq_ff | dffrsnq_1 | 5 | 49 | 41 | **0** | 17 | + clear + preset + recovery/removal_rising + **non_seq_setup/hold_rising** |
| seq_scan | sdffq_1 | 10 | 33 | 36 | **0** | 17 | rising_edge×5, setup×6, hold×6 等 |
| seq_scan | sdffrsnq_1 | 14 | 195 | 228 | **0** | 65 | 全 when 別大量展開 |
| seq_lat | latq_1 | 3 | 6 | 5 | **0** | 5 | **combinational** + rising_edge + setup/hold_falling + min_pulse_width |
| seq_lat | latrsnq_1 | 5 | 34 | 37 | **0** | 17 | + clear + preset + recovery/removal_falling + non_seq_setup/hold_rising |

### 重要発見

1. **orig の全 cell で `passive_power` field は 0 件**（Liberty 標準で使われていない）
2. **欠落 timing_type**：`minimum_period` / `non_seq_setup_rising` / `non_seq_hold_rising` / `three_state_enable` / `three_state_disable`
3. **internal_power の when 別詳細展開**：orig は RN/SETN/SI/SE の状態組合せで大量展開、 charao は集約

---

## 6. 整合化方針（ISS-00111 第3段階での実施）

### 6.1 削除・統合対象

| measure_type | 対応 |
|--------------|------|
| `passive`（seq 系 / output ありセル全般）| 削除（c_in は他 measure 副産物に統一、 §9 参照）。 output 無いセル（ANTENNA 等）では維持 |

### 6.2 追加対象

| 追加項目 | 対象 family | 実装 |
|----------|-------------|------|
| `minimum_period` 出力 | seq_ff / seq_scan | **保留（ISS-00082）**：`myExportLib.py` に `minimum_period` timing block 未実装。min_pulse 自体は ISS-00160(a31) で timing() constraint テーブル化済 |
| `non_seq_setup_rising` / `non_seq_hold_rising` | RN/SETN 持つ DFF/LAT | mylogic に新 entry 追加、 setup/hold 構造を流用 |
| `three_state_enable` / `three_state_disable` | comb_tristate (BUFZ/INVZ) | mylogic_comb_tristate に新 measure_type 追加 |

### 6.3 詳細展開対象

| 項目 | 対応 |
|------|------|
| internal_power の when 別展開 | 各 family で D/RN/SETN/SI/SE 状態組合せの entry 追加 |
| SI/SE 関連 timing arc | SDFF 4 family に setup/hold/power_tin 追加（ISS-00109）|

### 6.4 出力 field 整理

| 項目 | charao 現状 | orig 標準 | 対応 |
|------|-------------|-----------|------|
| `min_pulse_width` | **timing() constraint テーブル（`rise/fall_constraint(mpw_template_3x0)`）＝orig 標準に整合済** | timing block (`rise/fall_constraint` table) | **ISS-00160(a31) で timing() constraint テーブル化・実装済**（旧 scalar field `min_pulse_width_high/low` は撤去）|
| `min_period` | **未出力（scalar 撤去・保留）** | `minimum_period` timing block | scalar `min_period` は ISS-00160 で撤去。`minimum_period` timing block 出力は**保留**（`myExportLib.py` に未実装、ISS-00082 で検討）|
| `default_cell_leakage_power` | field（cell 属性）| `leakage_power { value }`（block 内）| myExportLib.py で block 内 default 行追加（ISS-00108(8)）|

---

## 7. orig 集計の代表セル選定（2026-05-31 確定）

ISS-00111 第2段階（orig との詳細対応表）作成に向け、 gf180 の cell を機能区分に分け、 各区分から **最大公約数となる代表セル** を選定。 代表セルの timing_type 群は同区分の全 family の timing_type を **包含**する（orig lib で検証済）。

### 7.1 区分と代表セル

| 区分 | 区分名 | 代表セル | timing_type 種類数 | 同区分メンバー |
|------|--------|---------|-------------------|----------------|
| **A1** | comb 単純 (single-input) | `inv_1` | 1 (combinational) | inv, buf, clkbuf, clkinv, dlya, dlyb, dlyc, dlyd |
| **A1** | comb 単純 (multi-input) | `nand3_1` | 1 (combinational) | and{2,3,4}, or{2,3,4}, nand{2,3,4}, nor{2,3,4}, xor{2,3}, xnor{2,3} |
| **A2** | comb 複合 (AOI/OAI) | `aoi222_1` | 1 (combinational) | aoi{21,211,22,221,222}, oai{21,211,22,221,222,31,32,33} |
| **A2** | comb mux | `mux4_1` | 1 (combinational) | mux{2,4} |
| **A2** | comb arith | `addf_1` | 1 (combinational) | addh, addf |
| **A2** | comb gating posedge | `icgtp_1` | 5 (combinational, combinational_fall, setup_rising, hold_rising, min_pulse_width) | icgtp |
| **A2** | comb gating negedge | `icgtn_1` | 5 (combinational, combinational_rise, setup_falling, hold_falling, min_pulse_width) | icgtn |
| **A3** | 特殊（tie/antenna） | `tieh` | 0 (timing なし、 leakage のみ) | tieh, tiel, antenna, filltie |
| **A4** | comb_tristate | `bufz_1` | 3 (combinational, three_state_enable, three_state_disable) | bufz, invz |
| **B1** | DFF posedge | `dffrsnq_1` | 11 (rising_edge, setup/hold_rising, clear, preset, recovery/removal_rising, non_seq_setup/hold_rising, min_pulse_width, minimum_period) | dffq, dffrnq, dffsnq, dffrsnq |
| **B2** | DFF negedge | `dffnrsnq_1` | 11 (B1 の falling 版 + non_seq_*) | dffnq, dffnrnq, dffnsnq, dffnrsnq |
| **C1** | LAT pos-enable | `latrsnq_1` | 11 (combinational + rising_edge + setup/hold_falling + clear + preset + recovery/removal_falling + non_seq_setup/hold_rising + min_pulse_width) | latq, latrnq, latsnq, latrsnq |
| **C2** | LAT neg-enable | (gf180 になし) | - | - |
| **D1** | SDFF posedge | `sdffrsnq_1` | 11 (B1 と同じ + scan 関連は entry 増 / timing_type 種類同じ) | sdffq, sdffrnq, sdffsnq, sdffrsnq |
| **D2** | SDFF negedge | (gf180 になし) | - | - |
| **E** | I/O | (gf180 標準セル lib になし、 ISS-00104 で保留) | - | - |

### 7.2 補足

- **dly （遅延セル）は buf と論理的に同じ**ため A1 (single-input) に統合
- **A2 gating は posedge / negedge で timing_type が完全分離**するため 2 区分に分けた
- **B1 と D1 は timing_type 種類が完全一致**（SDFF は SI/SE で entry 増だが timing_type 種類同じ）
- **A3 (tie/antenna) は timing なし** → leakage のみ計測
- **fill / fillcap は timing も leakage も無い**（filler セル）→ 集計対象外

### 7.3 包含検証結果（2026-05-31）

全 13 区分（A1×2 + A2×5 + A3 + A4 + B1 + B2 + C1 + D1）で代表セルが同区分の **全 member の timing_type を包含**することを orig lib で確認済。

> **【2026-08-16 追記・ISS-00113 クローズに伴う確認】A2 gating（`icgtp_1` / `icgtn_1`）は本表のとおり有効。**
> ISS-00113（2026-06-03 起票）は「`icgtp_1` / `icgtn_1` は gf180MCU 5v00 lib に存在しない」として
> **代表セルを 13 → 11 に再調整**したが、**これは誤り**だった。原因は grep の書式差で、当時
> `grep "cell (gf180mcu_..._icgt"`（`cell` と `(` の間に空白）を使ったが gf180 orig の書式は
> **`cell(`（空白なし）**。実際には **`icgtp_1/_2/_4` と `icgtn_1/_2/_4` の 6 セルが存在する**
> （`__icgtn_1` L104388 / `__icgtp_1` L107313）。charao 側も `mylogic_seq_lat.py` に
> **`ICG_PC` / `ICG_NC` を実装済み**（ISS-00151/00152/00153、真打ち 1,600 点・外れ 0）。
> **本 §7 / §8 の 13 区分がそのまま現行仕様**であり、11 への再調整は無効とする。

---

## 8. orig 代表セルの timing_type / internal_power / leakage 詳細集計（2026-05-31）

ISS-00111 第2段階：orig の代表セルから抽出した timing arc / internal_power / leakage の構造。 charao の implement 整合化と欠落補完の基準。

### 8.1 A 系（comb）

| 区分 | cell | input pin | output pin | timing arc 内訳（output pin） | internal_power 内訳 | leakage |
|------|------|-----------|------------|------------------------------|---------------------|---------|
| **A1 single** | `inv_1` | I | ZN | combinational neg_unate × 1 | ZN: rel=I × 1 | 3 (2 state + default) |
| **A1 multi** | `nand3_1` | A1, A2, A3 | ZN | combinational neg_unate × 3 | A1/A2/A3 各 3、 ZN: rel=Aj × 1 each = 3 | 9 (8 state + default) |
| **A2 AOI/OAI** | `aoi222_1` | A1, A2, B1, B2, C1, C2 | ZN | combinational neg_unate × **60**（各入力 × 10 when）| 各 input pin 23、 ZN 54 | 65 (64 + default) |
| **A2 mux** | `mux4_1` | I0, I1, I2, I3, S0, S1 | Z | combinational × 72 (I 系 pos_unate × 9 × 4 + S 系 both_unate × 9 × 2 × 2) | Ij 各 24、 Sj 各 16、 Z 64 | 65 |
| **A2 arith** | `addf_1` | A, B, CI | CO, S | CO: × 9 (各 pos_unate × 3) / S: × 18 (各 both_unate × 3 × 2) | CO: 6、 S: 12 | 9 |
| **A2 gating pos** | `icgtp_1` | CLK, E, TE | Q, IQ2, IQN2 | Q: **combinational × 4 + combinational_fall × 1** | CLK/E/TE 各 4、 Q: 4 | 9 |
| | | CLK: min_pulse_width × 4 / E, TE: setup_rising × 1, hold_rising × 1 | | | | |
| **A2 gating neg** | `icgtn_1` | CLKN, E, TE | Q, IQ3, IQN3 | Q: **combinational × 4 + combinational_rise × 1** | 同上（CLKN 系）| 9 |
| | | CLKN: min_pulse_width × 4 / E, TE: setup_falling × 1, hold_falling × 1 | | | | |
| **A3 tie** | `tieh` | (なし) | Z | (timing なし) | (なし) | 1 (default のみ) |
| **A4 tristate** | `bufz_1` | EN, I | Z | Z: **three_state_enable** + **three_state_disable** + combinational(I→Z) | EN 2、 I 1、 Z 2 | 5 |

### 8.2 B 系 / C 系 / D 系（seq）

#### B1 DFF posedge — `dffrsnq_1`（pin: CLK, D, RN, SETN, Q）

| pin | timing arc | internal_power |
|-----|-----------|----------------|
| CLK | min_pulse_width × 2 + **minimum_period × 2** = 4 | 8 (related=なし) |
| D | setup_rising × 1, hold_rising × 1 = 2 | 8 |
| Q | rising_edge × 1 + **clear × 9** + **preset × 5** = 15 | rel=CLK 1, rel=RN 8, rel=SETN 4 = 13 |
| RN | recovery_rising × 1 + removal_rising × 1 + min_pulse_width × 4 + **non_seq_setup_rising × 4** + **non_seq_hold_rising × 4** = 14 | 4 |
| SETN | 同上 = 14 | 8 |
| 合計 | timing 49、 internal_power 41 | leakage 17 (16 + default) |

#### B2 DFF negedge — `dffnrsnq_1`（CLKN, D, RN, SETN, Q）

B1 と同構造、 negedge：
- Q: **falling_edge** × 1 + clear × 9 + preset × 5 = 15
- D: setup_**falling** × 1, hold_**falling** × 1
- RN/SETN: recovery_**falling** + removal_**falling** + non_seq_setup/hold_rising（**non_seq は rising のまま**）

#### C1 LAT pos-enable — `latrsnq_1`（D, E, RN, SETN, Q）

| pin | timing arc | internal_power |
|-----|-----------|----------------|
| D | setup_**falling** × 1, hold_**falling** × 1 = 2 | 7 |
| E | min_pulse_width × 2 = 2 | 8 |
| Q | **combinational [D→Q] × 1** + **rising_edge [E→Q] × 1** + clear × 4 + preset × 8 = 14 | rel=D 1, rel=E 1, rel=RN 3, rel=SETN 7 = 12 |
| RN | recovery_**falling** × 1 + removal_**falling** × 1 + min_pulse_width × 2 + non_seq_setup/hold_rising × 4 = 8 | 7 |
| SETN | 同 8 | 3 |
| 合計 | timing 34、 internal_power 37 | leakage 17 |

#### D1 SDFF posedge — `sdffrsnq_1`（CLK, D, RN, SE, SETN, SI, Q）

| pin | timing arc | internal_power |
|-----|-----------|----------------|
| CLK | min_pulse_width × 8 + **minimum_period × 8** = 16 | 32 |
| D | setup_rising × 2 + hold_rising × 2 = 4 | 32 |
| SE | setup_rising × 2 + hold_rising × 2 = 4 | 32 |
| SI | setup_rising × 2 + hold_rising × 2 = 4 | 32 |
| Q | rising_edge × 5 + **clear × 33** + **preset × 17** = 55 | rel=CLK 4, rel=RN 32, rel=SETN 16 = 52 |
| RN | recovery_rising × 4 + removal_rising × 4 + min_pulse_width × 16 + non_seq_setup/hold_rising × 32 = 56 | 16 |
| SETN | 同 56 | 32 |
| 合計 | timing **195**、 internal_power **228** | leakage 65 (64 + default) |

### 8.3 timing_type の出現マトリクス

各 timing_type が代表セルにどれだけ含まれるか：

| timing_type | A1-s | A1-m | AOI | mux | arith | ICGp | ICGn | tie | tri | B1 | B2 | C1 | D1 |
|-------------|------|------|-----|-----|-------|------|------|-----|-----|----|----|----|----|
| combinational | 1 | 3 | 60 | 72 | 27 | 4 | 4 | - | 1 | - | - | 1 | - |
| combinational_fall | - | - | - | - | - | 1 | - | - | - | - | - | - | - |
| combinational_rise | - | - | - | - | - | - | 1 | - | - | - | - | - | - |
| three_state_enable | - | - | - | - | - | - | - | - | 1 | - | - | - | - |
| three_state_disable | - | - | - | - | - | - | - | - | 1 | - | - | - | - |
| rising_edge | - | - | - | - | - | - | - | - | - | 1 | - | 1 | 5 |
| falling_edge | - | - | - | - | - | - | - | - | - | - | 1 | - | - |
| setup_rising | - | - | - | - | - | 2 | - | - | - | 1 | - | - | 6 |
| hold_rising | - | - | - | - | - | 2 | - | - | - | 1 | - | - | 6 |
| setup_falling | - | - | - | - | - | - | 2 | - | - | - | 1 | 1 | - |
| hold_falling | - | - | - | - | - | - | 2 | - | - | - | 1 | 1 | - |
| clear | - | - | - | - | - | - | - | - | - | 9 | 9 | 4 | 33 |
| preset | - | - | - | - | - | - | - | - | - | 5 | 5 | 8 | 17 |
| recovery_rising | - | - | - | - | - | - | - | - | - | 2 | - | - | 8 |
| removal_rising | - | - | - | - | - | - | - | - | - | 2 | - | - | 8 |
| recovery_falling | - | - | - | - | - | - | - | - | - | - | 2 | 2 | - |
| removal_falling | - | - | - | - | - | - | - | - | - | - | 2 | 2 | - |
| min_pulse_width | - | - | - | - | - | 4 | 4 | - | - | 10 | 10 | 6 | 40 |
| minimum_period | - | - | - | - | - | - | - | - | - | 2 | 2 | - | 8 |
| non_seq_setup_rising | - | - | - | - | - | - | - | - | - | 8 | 8 | 4 | 32 |
| non_seq_hold_rising | - | - | - | - | - | - | - | - | - | 8 | 8 | 4 | 32 |

### 8.4 when 別展開の規模

orig の internal_power / leakage は **入力 state 組合せ別に展開**：

| 区分 | 状態変数 | 状態組合せ数 | leakage entry 数 |
|------|----------|--------------|------------------|
| A1 single (inv) | I (1bit) | 2 | 3 (2 + default) |
| A1 multi (nand3) | A1/A2/A3 (3bit) | 8 | 9 |
| A2 AOI (aoi222) | A1/A2/B1/B2/C1/C2 (6bit) | 64 | 65 |
| A2 mux (mux4) | I0..I3/S0/S1 (6bit) | 64 | 65 |
| A2 arith (addf) | A/B/CI (3bit) | 8 | 9 |
| A2 ICG | CLK/E/TE (3bit) | 8 | 9 |
| A4 tristate (bufz) | EN/I (2bit) | 4 | 5 |
| B1/B2/C1 | D/CLK or E/RN/SETN (4bit) | 16 | 17 |
| D1 SDFF | CLK/D/RN/SE/SETN/SI (6bit) | 64 | 65 |

### 8.5 internal_power の構造（重要発見、 2026-05-31）

**orig の `internal_power` は 2 種類に分かれる**：

| 種類 | 配置 pin | `related_pin` | 意味 | charao 対応 |
|------|----------|---------------|------|-------------|
| **input internal_power** | input pin 内 | **なし** | input pin の rise/fall switching 時の power | **`power_tin`** |
| **output internal_power** | output pin 内 | **あり**（input pin 名）| input pin の遷移に伴う output の switching power（dynamic）| **`power_tout`** |

#### A1 single (`inv_1`) — 基本形

```
pin (ZN) {
  internal_power () { related_pin: "I"; rise_power / fall_power }   # output 1 個
}
※ input pin (I) には internal_power なし（1 入力では state 違いなし）
```

#### A1 multi (`nand3_1`) — input pin 別 power

```
pin (A1) {
  internal_power () { when : "!A2&!A3"; rise_power / fall_power }   # A1 switching, A2=A3=L
  internal_power () { when : "!A2&A3";  rise_power / fall_power }   # A1 switching, A2=L,A3=H
  internal_power () { when : "A2&!A3";  rise_power / fall_power }   # A1 switching, A2=H,A3=L
  # ※ A2&A3=1 のときは A1 switching でも ZN=L から動かないので除外
}
pin (ZN) {
  internal_power () { related_pin: "A1"; when : "A2&A3"; ... }   # A1→ZN の output dynamic, A2&A3=1 のときのみ output 変化
  ... (A2, A3 も同様)
}
```

#### A2 AOI/OAI (`aoi222_1`) — 大規模 state 展開

- 各 input pin に **23 個** の internal_power（他 5 input の 2^5=32 state のうち、 該当 input switching で output 変化しない state 23 通り）
- pin (ZN) に **54 個** の internal_power（各 input 別 × output 変化する state 9 通り = 6 × 9 = 54）

#### A4 tristate (`bufz_1`)

```
pin (EN) {
  internal_power () { when : "!I"; ... }   # I=L のときの EN switching power
  internal_power () { when : "I";  ... }   # I=H のときの EN switching power
}
pin (I) {
  internal_power () { when : "EN"; ... }   # EN=H (enabled) のときの I switching
  # ※ EN=L (disabled) は I switching でも Z=Hi-Z で出力変化なし → 除外
}
pin (Z) {
  internal_power () { related_pin: "EN"; rise_power / fall_power }   # EN→Z output dynamic
  internal_power () { related_pin: "I";  rise_power / fall_power }   # I→Z output dynamic
}
```

#### B1 DFF posedge (`dffrsnq_1`)

```
pin (CLK) {
  internal_power () { when : "!D&!RN&!SETN"; rise_power / fall_power }   # 8 通り (D × RN × SETN)
  ... 計 8 個
}
pin (D) {
  internal_power () { when : "..."; ... }   # 8 通り
  ... 計 8 個
}
pin (RN) {
  internal_power () { when : "..."; ... }   # 4 通り
}
pin (SETN) {
  internal_power () { when : "..."; ... }   # 8 通り
}
pin (Q) {
  internal_power () { related_pin: "CLK"; when : "..."; ... }   # 1 個（CLK→Q rising_edge 用）
  internal_power () { related_pin: "RN"; ... }   # 8 個（RN→Q clear 用、 D × SETN × CLK 状態別）
  internal_power () { related_pin: "SETN"; ... }   # 4 個（SETN→Q preset 用）
}
# 合計 internal_power = 8+8+4+8+13 = 41 個
```

#### C1 LAT (`latrsnq_1`)

```
pin (D) {
  internal_power () { when : "..."; ... }   # 7 通り（E × RN × SETN 状態別、 D switching が Q に伝わる場合）
}
pin (E) {
  internal_power () { when : "..."; ... }   # 8 通り
}
pin (RN), pin (SETN): 各 internal_power
pin (Q) {
  internal_power () { related_pin: "D"; ... }   # 1 個（D→Q combinational）
  internal_power () { related_pin: "E"; ... }   # 1 個（E→Q rising_edge）
  internal_power () { related_pin: "RN"; ... }   # 3 個
  internal_power () { related_pin: "SETN"; ... }   # 7 個
}
```

### 8.6 leakage の構造

orig の leakage_power は **DUT 全 input pin の DC 状態組合せ別**に出力：

| 区分 | state 変数 | bit 数 | state 組合せ | leakage entry |
|------|------------|--------|--------------|---------------|
| A1 single (inv) | I | 1 | 2 | 2 + default = 3 |
| A1 multi (nand3) | A1, A2, A3 | 3 | 8 | 8 + default = 9 |
| A2 AOI (aoi222) | A1, A2, B1, B2, C1, C2 | 6 | 64 | 64 + default = 65 |
| A2 mux (mux4) | I0-I3, S0, S1 | 6 | 64 | 64 + default = 65 |
| A2 arith (addf) | A, B, CI | 3 | 8 | 8 + default = 9 |
| A2 ICG | CLK, E, TE | 3 | 8 | 8 + default = 9 |
| A3 tie | (なし) | 0 | - | 1 (default のみ) |
| A4 tri (bufz) | EN, I | 2 | 4 | 4 + default = 5 |
| B1/B2 DFF | D, CLK(N), RN, SETN | 4 | 16 | 16 + default = 17 |
| C1 LAT | D, E, RN, SETN | 4 | 16 | 16 + default = 17 |
| D1 SDFF | CLK, D, RN, SE, SETN, SI | 6 | 64 | 64 + default = 65 |

**leakage の when 表記**：すべての input pin の 0/1 状態を `&` で連結（例：`"!CLK&!D&!RN&!SETN"`）

**default 行**：state 組合せに該当しないとき用の代表値（orig は最大 leakage を default にする慣習が多い）

## 9. capacitance 算出統一（passive は output 無いセル限定で残す、 2026-05-31 確定）

ISS-00111 第3段階の方針確定。 §4.11 で疑問だった `passive` の役割は **output 無いセル（ANTENNA 等）の input cap 算出専用** と明確化。 output ありセルは他 measure 副産物に統一し、 passive entry を削除する。

### 9.1 passive の真の役割（コード解析で判明）

charao_run.py L2008 / L1835-1884 の `genFileLogic_PassiveTrial1x`：
- `c_in = abs(q_in_dyn) / vdd_voltage` で **input cap 算出**
- 全 slope (index1) × load (index2) の **100 sim** から `max` を採用（myLogicCell.py L399 `set_cin_max`）
- → `pin (X) { capacitance: <max> }` field に出力

つまり charao の `passive` は **input pin の capacitance 算出専用 sim**：
- output ありセル：他の measure（power_tin / power_tout / delay 等）でも sim 中に VIN slew があり、 同じ式で c_in 算出可能（既に L766 / L861 で実装済）→ **passive 不要**、 副産物に統一
- **output 無いセル（ANTENNA、 filler 等）**：他 measure が無い（delay/power_tout は output 必須）→ **passive を残す必要あり**
- 補足：output load (index2) は input cap に無関係（input cap は load 非依存）

### 9.2 capacitance 算出の統一案

#### pin_oirc 解釈による pin 別 cap 取得

各 measure の sim では `q_in_dyn` / `q_rel_dyn` / `q_clk_dyn` が取れる：

```python
c_in  = abs(q_in_dyn)  / vdd_voltage   # VIN slew 期間
c_rel = abs(q_rel_dyn) / vdd_voltage   # VREL slew 期間
c_clk = abs(q_clk_dyn) / vdd_voltage   # VCLK slew 期間
```

これらを **pin_oirc の位置別**に対応する pin の cap 候補として保存：

| pin_oirc index | testbench source | 取得 cap | 保存先 pin |
|----------------|------------------|---------|------------|
| `pin_oirc[1]` | VIN | `c_in` | `pin_oirc[1]` の pin |
| `pin_oirc[2]` | VREL | `c_rel` | `pin_oirc[2]` の pin |
| `pin_oirc[3]` | VCLK | `c_clk` | `pin_oirc[3]` の pin |

#### 重複 pin の自然除外

pin_oirc 内で同じ pin 名が複数 index に出る場合（例：`[o0, c0, c0, c0]` で pin_oirc[1]=pin_oirc[2]=pin_oirc[3]=c0）：

- ngspice の DUT 接続で重複 pin の片方は **OPEN 扱い**になる
- OPEN 端子では `q ≈ 0` → c ≈ 0pF
- **全 sim から `max` を取れば 0pF は自然に除外される**
- → 重複処理の特別条件分けは **不要**

```python
# pin 別 cap 候補リストを集積
pin_cap_candidates[pin_oirc[1]].append(c_in)
pin_cap_candidates[pin_oirc[2]].append(c_rel)
pin_cap_candidates[pin_oirc[3]].append(c_clk)

# 最終 cap = max（0pF は除外される）
for pin, cands in pin_cap_candidates.items():
    final_cap[pin] = max(cands)
```

### 9.3 代表セル別 input pin の cap 取得可能性検証（2026-05-31）

| 区分 | 代表 | input pin | 既存 measure で取得 | 備考 |
|------|------|-----------|---------------------|------|
| A1 single | inv_1 | I | ✓ (rising_edge, falling_edge, power_tout) | |
| A1 multi | nand3_1 | A1/A2/A3 | ✓ (rising_edge 各 input 別) | |
| A2 AOI/OAI | aoi222_1 | A1/A2/B1/B2/C1/C2 | ✓ (rising_edge 各 input 別) | |
| A2 mux | mux4_1 | I0-I3/S0/S1 | ✓ | |
| A2 arith | addf_1 | A/B/CI | ✓ | |
| A2 gating pos | icgtp_1 | CLK/E/TE | ✓ (rising_edge / setup / hold / power_tin / power_tout) | |
| A2 gating neg | icgtn_1 | CLKN/E/TE | ✓ (同上 negedge 版) | mylogic に icgt entry あれば |
| A3 tie/antenna | tieh | (input なし) | - | leakage のみ |
| A4 tristate | bufz_1 | EN/I | ✓ (rising_edge / three_state_enable/disable / power_tin) | |
| B1 DFF pos | dffrsnq_1 | CLK/D/RN/SETN | ✓ (CLK は 16 measure、 最も多い) | |
| B2 DFF neg | dffnrsnq_1 | CLKN/D/RN/SETN | ✓ (同上 negedge 版) | |
| C1 LAT | latrsnq_1 | D/E/RN/SETN | ✓ (D/E は多 measure、 RN/SETN は recovery/removal/clear/preset/min_pulse_width) | |
| D1 SDFF pos | sdffrsnq_1 | CLK/D/RN/SE/SETN/SI | CLK/D/RN/SETN は ✓、 **SI/SE は ISS-00109 で entry 追加必要** | ISS-00109 |

→ **SI/SE 以外は全 input pin が既存 measure で cap 取得可能**。 ISS-00109 で SDFF の SI/SE entry を追加すれば全 pin 対応完了。

### 9.4 passive 廃止と統一実装の計画

#### 削除対象（output ありセル）

| ファイル | 削除内容 |
|----------|---------|
| `mylogic_seq_ff.py` | passive entry 52 個 |
| `mylogic_seq_scan.py` | passive entry 24 個 |
| `mylogic_seq_lat.py` | passive entry 24 個 |

#### 残す（output 無いセル用）

| ファイル | 内容 |
|----------|------|
| `mylogic_comb_base.py` | passive entry 2 個（ANTENNA 用）|
| `charao_run.py` | `runSpicePassiveSingle` / `genFileLogic_PassiveTrial1x`（output 無いセル経路）|
| `myExportLib.py` | passive 由来の `pin (X) { capacitance }` 出力ロジック |

#### 追加・修正対象

| ファイル | 修正内容 |
|----------|---------|
| `charao_run.py` 全 measure 関数 | `c_in` / `c_rel` / `c_clk` 算出 + harness 保存（多くは既に実装済、 統一化）|
| `myLogicCell.set_cin_max()` | pin_oirc 解釈で pin 別 cap 候補集積 → 最大値選定 |
| `myExportLib.py` | 全 input pin の `capacitance` field 出力（既存ロジック流用）|

#### 削減効果

| 項目 | 現状 | 改善後 |
|------|------|--------|
| passive 専用 sim | あり (100 sim/cell) | **0 sim**（廃止）|
| input cap 算出 sim 数 | passive 100 sim/cell | **0**（他 measure 副産物）|
| sim 時間（全 family）| - | 大幅削減 |
| mylogic 行数 | 52+24+24+2 = 102 entry | **削減** |
| 仕様明確性 | passive の役割不明確 | **input cap 算出ロジックが統一**|

### 9.5 残課題（leakage）

passive / power_tin / power_tout / capacitance の整理が完了。 残るは `leakage` の整理 — §10 で扱う。

---

## 10. leakage の整理（2026-05-31）

`leakage` は他 measure と比較して **orig との整合性が高い**。 主な差分は既知の 2 ISS（00108(8) / 00109）で全て解決可能。

### 10.1 orig vs charao の leakage 構造比較

| 区分 | cell | orig (state + default) | charao (mylogic entry) | 状態 |
|------|------|------------------------|------------------------|------|
| A1 single | inv_1 | 2 + 1 = 3 | 2 | ✓ default 別出力 |
| A1 multi | nand3_1 | 8 + 1 = 9 | 8 | ✓ |
| A2 AOI | aoi222_1 | 64 + 1 = 65 | 64 | ✓ |
| A2 mux | mux4_1 | 64 + 1 = 65 | (要確認) | - |
| A2 arith | addf_1 | 8 + 1 = 9 | (要確認) | - |
| A4 tri | bufz_1 | 4 + 1 = 5 | 4 | ✓ |
| B1 DFF pos | dffrsnq_1 | 16 + 1 = 17 | 16 | ✓ |
| B2 DFF neg | dffnrsnq_1 | 16 + 1 = 17 | 16 | ✓ |
| C1 LAT | latrsnq_1 | 16 + 1 = 17 | 16 | ✓ |
| **D1 SDFF pos** | sdffrsnq_1 | **64 + 1 = 65** | **16** | **✗ SI/SE 不足 48 entry**（ISS-00109）|

### 10.2 整合性の高い項目

#### (a) state 組合せ（基本構造）

- A1〜A4 / B1 / B2 / C1：charao も orig と同 state 数（input pin の 2^N state）
- D1 SDFF：charao は SI/SE 不足で 2^4=16、 orig は 2^6=64 → ISS-00109 で対応

#### (b) state 別 when の機能等価性

orig と charao mylogic の when 表記：

| | when 表記例 |
|---|-------------|
| orig (Liberty 出力) | `"!CLK&!D&!RN&!SETN"`（pin 名）|
| charao mylogic | `"!r0&!s0&!i0&!c0"`（charao 内部 pin 役割名）|
| charao .lib 出力 | `"!CLK&!D&!RN&!SETN"`（pin 名に mapping 済）|

→ charao mylogic は内部表記、 .lib 出力時に pin 名にマッピングされ機能等価。

#### (c) when の順序

- orig：CLK→D→RN→SETN（アルファベット順か特定順）
- charao：family により異なる（`r,s,i,c` / `i,c,r,s` / `r,s,i0,c0` 等）

→ STA tool は when 条件を **論理式として解釈**するため、 表記順序は機能に無関係。 実害なし。

#### (d) leakage 値の算出方法

`charao_run.py` L2014-2021 (Pleak 算出)：

```python
i_vdd = -res["i_vdd_leak"]
i_vss =  res["i_vss_leak"]
i_vnw = -res["i_vnw_leak"]
i_vpw =  res["i_vpw_leak"]
p_supply = i_vdd * (vdd - vss) + i_vnw * (nwell - pwell)
p_absorb = i_vss * (vdd - vss) + i_vpw * (nwell - pwell)
pleak = max(p_supply, p_absorb)   # ← supply / absorb の最大値（保守的）
```

`i_vdd_leak` 等は `.MEASURE TRAN i_vdd_leak AVG I(VDD_DYN) FROM={_t_in0 - 11*_tslew_min} TO={_t_in0 - 1*_tslew_min}` で、 input slew 前の **stable 期間**で AVG 計測。 これは DC steady state に近い。

**⚠ 係数は 2026-08-21 に `101*` → `11*` へ変更**（ISS-00234）。 同時に `simulation_slew_min` を
1 ps → 10 ps へ上げているため、 **窓の幅は 100 ps のまま**。 窓に 0 点しか入らないと ngspice が
無警告で 0 A を返す（ISS-00236）ので、 `simulation_slew_min` を下げるときは幅も併せて確認する。

→ Liberty の leakage_power（DC current）と整合。

### 10.3 残課題（leakage 固有）

| 課題 | 対応 ISS |
|------|----------|
| **default 行の出力先**：orig は `leakage_power() { value }` block 内、 charao は `default_cell_leakage_power` field で別出力 | **ISS-00108(8)**：myExportLib で leakage_power block 内に default 行を追加 |
| **SDFF の SI/SE 不足**：state 16 → 64 に拡張 | **ISS-00109**：mylogic に SI/SE entry 追加（state combination も自動拡張）|
| pleak 値の精度（ISS-00075 系統誤差、 ISS-00105 TIE 14 桁ズレ）| ISS-00075 / ISS-00105 で個別対応中 |

### 10.4 leakage は新規 ISS 不要

leakage の整理結果：
- **基本構造は orig と整合**（B1/B2/C1 同等、 D1 のみ SI/SE 課題）
- **計算ロジックは保守的**（pleak = max(supply, absorb)）
- **既知の ISS（00108(8) / 00109）で全て解決可能**

→ leakage 固有の新規 ISS 起票は **不要**。

### 10.5 ISS-00111 完結

§3〜§9 + §10 の整理で、 charao の全 measure_type の：
- 計測内容 / sim 動作 / .lib 出力先（§4）
- orig との対応関係（§5, §8）
- 過剰 / 欠落の特定（§8.7）
- 整合化方針（§9 capacitance 統一 / passive は output 無いセル限定で維持、 §10 leakage 整合性確認）

が完了。 ISS-00111 第1段階 + 第2段階 + 第3段階方針確定。 実装フェーズは別途タスクとして起票。

---

## 11. Liberty 標準との対比（2026-05-31）

charao の lib 構成が **Liberty 標準（一般的な vendor lib 構成）** と整合しているか整理。 charao の実装は基本骨格として Liberty 標準に合致しており、 差分は全て既知 ISS で把握済 → 解決可能。

### 11.1 Liberty 標準の典型構成

```
library (name) {
  delay_model : table_lookup ;
  # 単位定義、 template 定義、 operating_conditions 等

  cell (cell_name) {
    area : <num> ;
    cell_leakage_power : <num> ;            # cell 全体 (max)
    pg_pin (VDD) { pg_type : primary_power ; ... }   # 電源 pin
    pg_pin (VSS) { pg_type : primary_ground ; ... }

    leakage_power () { when : "..." ; value : <num> ; }
    leakage_power () { value : <num> ; }    # default 行（when なし）

    ff (Io0, IQB) { clocked_on : "CLK" ; ... }       # FF group
    # OR  latch (Io0, IQB) { enable : "E" ; ... }    # LATCH

    pin (Q) {
      direction : output ;
      function : "IQ1" ;
      max_capacitance, max_transition, min_capacitance ;
      related_ground_pin, related_power_pin ;

      timing () {
        related_pin : "CLK" ;
        timing_type : rising_edge ;
        cell_rise / cell_fall / rise_transition / fall_transition
      }
      internal_power () { related_pin : "CLK" ; rise_power / fall_power }
    }

    pin (CLK) {
      direction : input ;
      capacitance : <num> ;
      clock : true ;

      timing () {
        timing_type : min_pulse_width ;
        rise_constraint / fall_constraint   # H/L pulse 制約
      }
      timing () { timing_type : minimum_period ; ... }   # 周期最小
      internal_power () { when : "..." ; rise_power / fall_power }
    }

    pin (D) {
      direction : input ;
      capacitance : <num> ;
      timing () { timing_type : setup_rising ; ... }
      timing () { timing_type : hold_rising ; ... }
      internal_power () { when : "..." ; ... }
    }
  }
}
```

### 11.2 charao 実装との対比

| Liberty 標準 | charao 現状 | 状態 | 関連 ISS |
|--------------|-------------|------|----------|
| `pg_pin (VDD/VSS/VNW/VPW)` | `inout VDD/...` 表記 | ✗ syntax 違い | ISS-00108(2) |
| `cell_leakage_power : <num>`（cell 直下）| `default_cell_leakage_power` field | ✗ 名称違い | - |
| `leakage_power () { value }`（default 行、 block 形式）| `default_cell_leakage_power` field で別出力 | ✗ 配置違い | ISS-00108(8) |
| `ff (Io0, IQB) { clocked_on : "CLK" ; clear : "(!RN)" ; preset : "(!SETN)" ; }` | ✓ 同等 | ✓ | - |
| `latch (Io0, IQB) { enable : "E" ; data_in : "(!D)" ; }` | ✓ 同等 | ✓ | - |
| `pin (Q) { function : "IQ1" }`（PDK 命名）| `function : "IQ"`（charao 内部 register 名）| ✗ 名称違い | ISS-00108(1) |
| `pin (Q) { max_capacitance / max_transition / min_capacitance / related_ground_pin / related_power_pin }` | **欠落** | ✗ 欠落 | ISS-00108(4) |
| `timing { timing_type : min_pulse_width; rise_constraint / fall_constraint }`（timing block 内） | **timing() constraint テーブル（`rise/fall_constraint(mpw_template_3x0)`、ISS-00160 で実装済）** | ✓ 整合 | ISS-00108(3) → ISS-00160 で解消 |
| `timing { timing_type : minimum_period }`（timing block 内）| **未出力（scalar `min_period` は撤去・timing block は保留）** | ✗ 欠落 | ISS-00082（保留）|
| `pin (Q) { internal_power { related_pin : "CLK" } }` | ✓ 同等 | ✓ | - |
| `pin (D) { capacitance : <num> }` | ✓（現状 passive sim から、 ISS-00111 で全 sim 副産物に統一）| ✓ | ISS-00111 |
| `pin (D) { internal_power { when : "..." } }` | `power_tin` で対応、 ただし when 別詳細展開不足 | △ | ISS-00108(7) |
| `pin (D) { timing { setup_rising / hold_rising } }` | ✓ 同等 | ✓ | - |
| `pin (RN/SETN) { timing { non_seq_setup_rising / non_seq_hold_rising } }`（async pin 間制約）| **欠落** | ✗ | ISS-00108(6) |
| `pin (Z) { timing { three_state_enable / three_state_disable } }`（tristate）| **欠落** | ✗ | ISS-00108(6) |
| `pin (CLK) { internal_power { combinational_fall / combinational_rise } }`（ICG）| **欠落** | ✗ | ISS-00108(6) |
| `pin (Q) { internal_power { related_pin : "<input>" ; when : "..." } }` の when 別大量展開 | charao は集約出力 | △ | ISS-00108(7) |

### 11.3 整合性評価

#### 一致している項目（基本骨格）

- ✓ **library → cell → pin → timing/internal_power/leakage_power の階層構造**
- ✓ **timing arc の配置**（output pin 内に prop delay、 input pin 内に constraint）
- ✓ **internal_power の使い分け**（output pin 内 ＝ active arc dynamic、 input pin 内 ＝ input switching dynamic）
- ✓ **leakage_power の配置**（cell 直下に when 別展開）
- ✓ **ff / latch group 定義**（clocked_on / next_state / clear / preset / enable / data_in）

#### 差異があるが機能等価（syntax）

- ✓ `min_pulse_width` は ISS-00160(a31) で timing() constraint テーブル化し解消（scalar field 撤去）。`minimum_period` は scalar 撤去済・timing block 出力は保留（ISS-00082）
- △ `pg_pin` vs `inout` → 一部 STA tool は pg_pin 要求、 `myExportLib` 修正で解消（ISS-00108(2)）
- △ `cell_leakage_power` / default 行の出力形式 → 同上（ISS-00108(8)）

#### 機能差分（欠落、 追加実装が必要）

- ✗ **欠落 timing_type**：`minimum_period` / `non_seq_setup/hold_rising` / `three_state_enable/disable` / `combinational_fall/rise`（ISS-00108(5)(6)）
- ✗ **欠落 electrical 属性**：`max_capacitance` / `max_transition` / `related_ground/power_pin`（ISS-00108(4)）
- ✗ **欠落 SI/SE 関連**：SDFF の SI/SE entry（ISS-00109）
- ✗ **欠落 internal_power の when 別展開**：seq 系で when を集約せず詳細展開（ISS-00108(7)）

### 11.4 評価結論

| 評価軸 | 結論 |
|--------|------|
| **基本構造の互換性** | ✓ **Liberty 標準と整合**。 階層構造、 timing/power 配置、 leakage 構成すべて正しい |
| **syntax 互換性** | △ 一部 field / block 形式が違うが、 myExportLib 修正で解消可能 |
| **機能カバレッジ** | △ 一部 timing_type / electrical 属性 / SDFF SI/SE が欠落、 ISS-00108/00109 で追加可能 |
| **値の精度** | △ leakage 系統誤差（ISS-00075/00105）等、 個別課題で対応中 |
| **STA tool 互換性** | △ 現状 charao 出力でも基本動作可、 ISS-00108/00109 解決で完全互換 |

**実装フェーズで ISS-00108 / ISS-00109 を順次対応すれば、 orig vendor lib と完全互換**になる。 charao の独自実装の根幹（capacitance 統一、 passive は output 無いセル限定で維持）も Liberty 標準に近づく方向。

---

### 8.7 charao 実装との主要差分（再整理）

| 課題 | 詳細 |
|------|------|
| 欠落 timing_type | `minimum_period` (全 seq)、 `non_seq_setup_rising` / `non_seq_hold_rising` (RN/SETN 持つ family)、 `three_state_enable` / `three_state_disable` (A4)、 `combinational_fall` / `combinational_rise` (A2 ICG) |
| 欠落 measure | SDFF の SI/SE 関連 setup/hold/power_tin（ISS-00109） |
| 過剰 measure | output ありセルの `passive` entry は不要（c_in は他 measure 副産物に統一、 §9 参照）。 output 無いセル（ANTENNA 等）の `passive` は維持 |
| internal_power 詳細展開不足 | charao は集約、 orig は state 別大量展開（特に dffrsnq 41 entry vs charao 9 entry）|
| leakage default 表記 | orig は leakage_power block 内に default 行、 charao は `default_cell_leakage_power` field |

---

## 12. `.tran` の刻み（`maxstep`）と probe（ISS-00219 / ISS-00223）

### 12.1 `maxstep` の決まり方

```
v       = slope / simulation_points_per_transition          _calc_maxstep()（clamp しない生値）

maxstep = _fix_maxstep(v)                                   ISS-00234（2026-08-17、 ダーマツ指示）
          ① ps 単位へ切り上げ    sim_segment_timestep_min ＝ PWL 折れ点と同じ 1 ps 格子
          ② 有効桁へ丸め        significant_digits（既定 3）
          ③ clamp               [tmax_low, tmax_high]

.tran {maxstep} {tsim_end} 0 {maxstep}
```

**この順序を守ること。** ②は①を壊さない（整数 ps は 0.001 ns の倍数で、 有効 3 桁は
0.001 ns 以上の分解能を必ず残す）。③の境界 `tmax_low` / `tmax_high` も **ps 格子上の値**に
しておく（sky130 は 0.01 / 0.3 ns）。①が切り上げなのは**刻みを粗い側＝安全側に倒す**ため。

**⚠️ ①が要る理由**：ISS-00234 で PWL 折れ点（`t_rel0` / `t_clk4`）は 1 ps 格子へ切り上げたのに、
**`maxstep` は有効桁丸めだけで格子に乗っていなかった**（ISS-00230 の狙いは格子合わせだったが
実装は桁丸め）。`26.6 ps` / `11.5 ps` という端数が出ており、`.tran` の刻みが整数 ps の折れ点を
またぐたびに端数の残りステップが生じる構図だった。

**`slope` は template の index 値**（閾値間の遷移時間）。**transition なので index のままでよく**、
実 PWL 幅への換算は不要（ISS-00234、ダーマツ判断）。measure ごとにどの index を使うかは §12.1.1。

**`simulation_points_per_transition` は probe（§12.3）と同じ設定**を使い、「遷移に何点乗せるか」の
意味を**入力側にも揃える**。

**⚠️ 2026-08-15 以前は `max(tmax_low, min(slope × 0.198, tmax_high))`** だった。`0.198` は根拠不明の
係数で、さらに **measure ごとに下限を破る追加処理**があった（ISS-00234 で全廃）。

### 12.1.1 measure 別の `slope`（どの index を使うか）

| measure | `slope` |
|---|---|
| `delay` / `power_tout` / `power_tin` / `passive` | **入力 slew**（`index1_slope` / `index1_slope_in`） |
| `setup` / `hold` / `recovery` / `removal` / LAT `hold` | **CLK slew**（`index2_slope_rel`） |
| `min_pulse_width` | **なし** → `tmax_low`（ISS-00234、ダーマツ指示） |
| `leakage` | **なし** → `tmax_low`（入力が動かない measure） |

### 12.1.2 ⚠️ `maxstep` は全 measure で `[tmax_low, tmax_high]` を守る（ISS-00234）

**2026-08-15 以前は 5 経路が下限を破っていた。**

```
measure      旧・下限を破っていた処理                          落ちた先
delay        probe: min(_lim, maxstep)                       tmax_low 未満
const        probe: min(_lim, maxstep)                       tmax_low 未満
min_pulse    probe: min(_lim, maxstep)  ＋ 初期値 5×tmax_high  上限の 5 倍から出発
power_tin    max(maxstep/20, min(maxstep/5, tslew_min×20))   tmax_low の 1/5
passive      max(maxstep/20, min(maxstep, tslew_min×20))     tmax_low の 1/20
```

**`power_tin` は自己矛盾していた**。ISS-00188 が「共通値を下げると `power_tin` の最速 slew が
`Timestep too small` で落ちる」と実測して**専用フロア `tmax_low_power_tin`（sky130 で 20 ps）**を
設けたのに、**同じ関数の中で `/5` して 4 ps まで落としていた**＝ISS-00188 が禁じた領域に自ら入っていた。
`tslew_min × 20`（20 ps）と `tmax_low_power_tin`（20 ps）は同値なので、`/5` が無ければ 20 ps で確定していた。

**`min_pulse` の `5 × tmax_high`** は `.tran` の `tmax`（刻みの上限）であって**パルス幅ではない**。
`tmax_high = 20 ns` に対し `maxstep = 100 ns` と**上限の 5 倍**を指定していた。

**現在は `_fix_maxstep()`（`charao_run.py`）の 1 箇所に集約**し、初期式・probe とも必ず
`[tmax_low, tmax_high]` に収める。**`tmax_low_power_tin` は廃止**。

**⚠️ `_clamp_maxstep()` は削除済み**（ISS-00234、 2026-08-17）。`_calc_maxstep()` からも clamp を
除き、 **clamp は `_fix_maxstep()` だけが行う**。`_fmt_maxstep()`（有効桁丸め）は `_fix_maxstep()` の
内部でのみ使う。呼び出しは **16 箇所**（delay / power_tout / power_tin / const / removal /
lat_hold / passive / min_pulse_width / leakage の各経路と probe 4 経路）。

**`maxstep` の有効桁は `significant_digits` で決まる**（`_fmt_maxstep()`、既定 3）。従来は `"{:.5g}"` の
ハードコードだった。**`significant_digits` は本来 `.lib` / doc の出力桁**（`--significant_digits` / `-s`、
`config_lib.jsonc`）なので、**この値を変えると sim の刻みも変わり結果が動く**点に注意。
`-s` は未指定なら `config_lib.jsonc` → モデル既定 3 の順に解決される（ISS-00230 で `default=None` 化）。

**`.tran tstep tstop <tstart <tmax>>` の `tstep` は printing increment で解析に一切関与しない**
（`tmax` 明示時。ngspice マニュアルで確認、ISS-00219）。効くのは **`tmax` だけ**。そのため charao は
`tstep` を廃し **`maxstep` に一本化**している。`tstart` は**出力保存の開始時刻**にすぎず、`0〜tstart` も
計算されるので**時間短縮には使えない**。

#### ⚠️ `tmax` は「刻み」ではなく「刻みの上限」（2026-08-14 是正）

**`tmax` は実際の積分ステップではない。** ngspice は **LTE（局所打切り誤差）制御で刻みを自律的に決め、
必要なら `tmax` よりはるかに細かく刻む**。`tmax_low` から実際の刻みまでは **2 段階間接**である。

```
tmax_low  ──決める──▶  tmax = _fix_maxstep(slope / points_per_transition)
                        （= .tran の第 4 引数。 ①ps 格子 → ②有効桁 → ③clamp）
                              │
                              ├─ 上限 : 刻みはこれを超えない
                              └─ 下限 : delmin = 1e-11 × tmax（ngspice が内部算出）

実際の刻み = LTE 制御が delmin 〜 tmax の範囲で決める
```

**`tmax_low` を動かすと、上限の天井と `delmin` の床が同時に動く。** これが「下限は粗すぎても細かすぎても
失敗する」の正体である。

| 動かす向き | 効く側 | 破綻の仕方 |
|---|---|---|
| **粗くしすぎ** | 上限（天井） | 遷移をまたいでしまい、波形の形が取れない |
| **細かくしすぎ** | 下限（`delmin` の床） | LTE 制御が刻みを潰し切れる範囲が広がり、`timestep` が `delmin` 付近まで潰れて `Timestep too small` |

**細かくしすぎの実例（ISS-00229、sky130 `sdlclkp_1`）**：`tmax = 2 ps` → `delmin = 2e-23` に対し
`timestep = 2.5e-24` まで潰れて `Timestep too small: trouble with node "vclk#branch"` で abort。
落ちる直前の波形は **`vclk=0 / vrel=0 / vin=1.8 / vout=0` で完全に静止**しており、**回路が動いていない区間で
純粋に数値的に破綻**していた。`tmax_low` を 4 ps にすると `delmin = 4e-23` となり同じ時刻を素通りする。

#### `pts` は実点数ではなく「点数の下限見積り」

本仕様書および `[INFO] maxstep_fix` が出す

```
pts = vout_trans / maxstep
```

は **「遷移に最低でもこれだけの点が乗る」という下限**であって、実際の点数ではない。LTE 制御が細分化
すれば実点数はこれより多くなる。**`tmax_low` の妥当性は `pts` では判定できず、orig との transition 誤差
で判定する**（§12.2）。

### 12.2 `tmax_low` の決め方（PDK ごと）

**判定は orig との transition 誤差で行う。**`pts`（＝`vout_trans / maxstep`）は下限見積りにすぎず
判定基準にはならない（§12.1）。`pts` は**候補を絞る目安**として使い、**最終判断は必ず実測の誤差で下す**。

```
             出力遷移     tmax_low   判定
sky130       17〜25 ps     0.02       ✗ 粗すぎる（transition 誤差 18%）
                           0.002      ✗ LTE 破綻（ISS-00229、Timestep too small）
                           0.004      △ ISS-00229 は解消するが const/removal で破綻が残る
                           0.005      △ 5 → 4 failures
                           **0.010**  ⭕ **確定値**（ISS-00234、2026-08-15 ダーマツ判断）
gf180        70〜96 ps     0.02       ⭕ 採用（0.002 は orig から +58% 遠ざかる＝細かい≠高精度）
```

**sky130 の変遷**：`0.002 → 0.004`（ISS-00229）`→ 0.005 → 0.010`（ISS-00234）。
**`tmax_low` を上げるだけでは 3 failures で頭打ち**になり、そこから
「`maxstep` が下限を守っていない経路がある」という発見（§12.1.2）につながった。
**統一式と下限遵守を入れて初めて 0 failures**（`dfstp_1` 5→0、`dfrtn_1` 8→0）。

**細かくすれば精度が上がるとは限らない**のが要点である。gf180 で `0.002` にすると誤差が **+58% 悪化**した。
遷移幅は**露払いを 1 回回せば `.lib` から読める**ので、新規 PDK でもまず `pts` で当たりを付け、
**露払い（LTE 破綻の有無）→ full grid（orig との誤差）** の順に確定させる。

sky130 は `tmax_low_power_tin` で `power_tin` だけ分離している（`power_tin` は最速 slew で
`Timestep too small ... vclk#branch` を起こすため）。**`tmax_low` は measure 横断で効く**ので、
変更時は `power` 以外の全 measure が影響を受ける。

### 12.2.1 `tsim_end` は 1 ps 単位へ切り上げる（ISS-00230）

**const の `tsim_end` は `_quantize_tsim_end()` で 1 ps 単位へ切り上げる**（`_TSIM_END_QUANTUM = 1e-12`、
`charao_run.py` の 3 箇所＝probe ループ / nodeset 準備 / 掃引ループ）。

```
tsim_end = ceil( max(t_clk5, t_in1, t_rel1) + 3 ns  /  1 ps ) × 1 ps
```

**【なぜ必要か】** 端数のある `tstop` に**ちょうど着地した後**、ngspice が余分な 1 ステップを刻もうとして
`timestep` が `delmin` を割り、`Timestep too small` で abort する。

```
sky130 LAT/ICG hold  maxstep = 4 ps      _tsim_end = 14.040367 ns
  → time = 1.40404e-08, timestep = 5e-24: trouble with node "vclk#branch"
  → .raw は 3566 点で tstop まで完走して書けている（Δt = 4.00000 ps 一定、波形は静止）
  → しかし abort により .meas が実行されず、値が取れないまま捨てられる
```

**⚠️ 計算は完走しているのに結果を失う**のがこの症状の質の悪いところで、`.lib` には `0.0000` が残る。
`tsim_end` を 14.041 ns（**+0.633 ps**）にするだけで **12 failures → 0**、しかも**他の値は 1 点も動かない**
（sky130 5 セル × 全 measure × 2x2 の 3126 点で検証）。**切り上げ**に限るのは、縮めると測定対象
（Q の応答）を切り落とすため。

### 12.2.2 `simulation_slew_min` と `sw_ramp_time`（ISS-00234、2026-08-21〜22）

**`simulation_slew_min` は PWL の遷移幅の下限**［ns］で、 **3 PDK とも `0.01`（10 ps）**。
1 ps のエッジは ngspice の LTE が刻みを詰める要因になりうるため引き上げた。

**⚠ この 1 つの値が 6 箇所に効く**（括弧内は `simulation_slew_min = 0.01` のときの実効値）。

| 効く先 | 式 | 実効値 |
|---|---|--:|
| init パルスのエッジ | `INIT_EDGE_MULT(2) * slew_min`（`myTbParam.py`） | 20 ps |
| `t_rel3` / `t_clk7` の終端エッジ | `slew_min` | 10 ps |
| `tslew_in` / `tslew_clk` / `tslew_rel` の既定 | `slew_min` | 10 ps |
| 未使用 phase の折れ点間隔（ISS-00134） | `slew_min` | 10 ps |
| leak の AVG 窓（§9） | `{_t_in0-11*slew_min .. _t_in0-1*slew_min}` | 幅 100 ps |
| `.MEASURE` の TD マージン | `1*slew_min` | 10 ps |

**⚠ PDK ごとに変えない。** 上の係数は PDK 非依存のコードなので、 片方の PDK だけ下げると
**leak の AVG 窓や `tslew_clk` が一緒に潰れる**（ISS-00236 と同じ穴が開く）。

#### `sw_ramp_time` — pre-charge SW のゲートランプ幅（`simulation_slew_min` とは独立）

**`VPC_CTRL`（ISS-00076 の pre-charge SW のゲート制御）のランプ幅**［ns］。既定 **0.001（1 ps）**。

```
SW_PRECHARGE : Ron=0.1Ω → Roff=1GΩ（10 桁）をヒステリシス Vh=0.3 付きで通過
VPC_CTRL PWL( ... {_t_init0 - _tsw_ramp} vss  {_t_init0} vdd
                  {_t_init3 - _tsw_ramp} vdd  {_t_init3} vss )
```

**⚠ `simulation_slew_min` に紐づけてはならない。** `VPC_CTRL` は **DUT の入力波形ではなく
アナログ SW のゲート制御**で、 信号 slew とは別の量。2026-08-21 に `simulation_slew_min` を
1 ps → 10 ps へ上げた際、 この 1 箇所も道連れで鈍り、 **sky130 `dfrtp_1` に 16 件の
`Timestep too small`** が出た（`run_tm03_sky`）。

```
失敗 16 件すべて同一条件 : t = 3.00667 ns / maxstep = 10 ps（tmax_low フロア）
                          node vclk#branch / index_1 = 0.00338 pF（最小負荷）/ _t_ofs = 0
  変更前（1 ps）  : 3.009 → 3.010 ns
  変更後（10 ps） : 3.000 → 3.010 ns   失敗時刻 3.00667 ns ＝ ランプの途中
```

**遷移領域の滞在時間が 10 倍**になり、 `maxstep` が下限に張り付いた状態で LTE が破綻した。
専用設定へ切り出して 1 ps に戻すことで解消している。

### 12.3 probe（`simulation_points_per_transition`）

**出力遷移 `trans_out` に何点のサンプルを乗せるか**を指定し、**掃引位置を固定したまま** `maxstep` を
反復収束させる。

```
_lim = trans_out / simulation_points_per_transition
maxstep = min(_lim, maxstep)        絞る方向にしか動かない
収束     改善 20% 未満（_lim >= maxstep × 0.8）、上限 4 回
0.0      無効＝従来動作
```

掃引位置と同時に動かすと**変化がどちらに由来するか分離できない**（実測で 99 → 29 ps と往復し収束
判定できなかった）ため、位置を固定して `maxstep` だけを収束させる。実測では 297 → 49.5 → 8.3 → 5.1
→ 3.89 ps と単調に収束した（真値 7.5 ps に対し当初 99 ps ＝ 13 倍の過大評価）。

### 12.4 measure 別のカバレッジ

**probe は `trans_out` を測る measure にだけ存在する。**`_lim = trans_out / points` で刻みを決めるため、
`trans_out` を測らない measure では**原理的に成立しない**。

| measure | probe | 実装関数 |
|---|---|---|
| `delay` / `rising_edge` / `falling_edge` | **あり** | `runSpiceDelaySingle` |
| `setup_rising` / `setup_falling` | **あり** | `runSpiceConstSingle` |
| `recovery_rising` / `recovery_falling` | **あり** | 〃 |
| `hold_rising` / `hold_falling`（**FF**） | **あり** | 〃 |
| `hold_rising` / `hold_falling`（**LAT / ICG**） | **なし** | 〃（`is_hold and is_lat` で除外）。**電圧判定**（`judge_vlt_max/min`）で `trans_out` を測らない |
| `removal_rising` / `removal_falling` | **なし** | `runSpiceRemovalSingle`。**Q が遷移しないことが正常**なので遷移時間が定義できず、電圧判定を採る（ISS-00138 の設計） |
| `min_pulse_width_low` / `_high` | **あり** | `runSpiceMinPulseSingle` |
| `power_tout` / `power_tin` | なし | — |
| `passive` | なし | — |
| `leakage` | なし | — |

**⚠️ 既知の課題**：`removal` は **Q の一過性の落ち込みを見るため `maxstep` 感度は低くないのに適応機構が
無い**。sky130 で `dfrtn_1` の `removal` が唯一 `|diff| > 0.2` だったことと符合する（ISS-00223 の観察）。

### 12.5 ログ

`maxstep` 確定時に `[INFO] maxstep_fix` を出す。`maxstep` と `trans_out` は **`.lib` に出ない量**なので、
これが無いと `work`（`.sp` / `.lis`）を回収しないと解析できない。

```
[INFO] maxstep_fix <cell>/vt_<vdd>_<temp>_<n>_<meas>/oir=<oirc>_arc=<arc>_c<index1>_r<index2> \
       maxstep=7.2553e-12 vout_trans=1.39407e-11 pts=1.92
```

識別子は **`.sp` の命名から `_sXX`（掃引点）を除いた形**。マルチスレッド実行で行が混ざっても対象を
特定できる。`pts` は設定値ちょうどにはならない（収束を「改善 20% 未満」で打ち切るため。実測 1.61〜1.92）。

**`pts` の読み方**：`maxstep` が `tmax_low` に張り付いた点では `pts` が設定値を大きく上回る
（sky130 `sdlclkp_1` で 18.77〜25.51）。これは**精度が高いという意味ではなく、probe が「これ以上絞る
必要なし」と判断して即 break した＝上限が `tmax_low` に律速されている**サインで、**LTE 破綻の予兆**として
読む（ISS-00229）。**`pts` が過大な点を探せば、`tmax_low` のフロアに当たっている点を特定できる。**

### 12.6 効果（実測）

```
dfxtp_1 setup fall (1.5, 1.5)        5.0064 → 0.0474 ns（1/106）
buf_16 rise_transition (5, 0.0005)   +0.1787 → +0.0013（1/137）
buf_16 fall_transition               +0.0774 → −0.0020（1/39）
十分細かい点は 1 ビットも変わらない（buf_16 は 294 点中 176 点が無変化）
コスト                                const 1.13 倍 / delay 1.05 倍
```

---

## 13. `index_1` / `index_2` の意味と軸の正規化（2026-08-15、ダーマツ指示）

### 13.1 Liberty では軸の意味は `lu_table_template` が決める

`index_1` / `index_2` が何を表すかは **`lu_table_template` / `power_lut_template` の
`variable_1` / `variable_2` で宣言する**。したがって **どちらの順序でも正しい**。順序そのものに
標準はなく、**宣言と中身が一致していれば整合**する。

### 13.2 charao の並び（基準）

| measure | template | `index_1`（`variable_1`） | `index_2`（`variable_2`） |
|---|---|---|---|
| `delay` / `transition` | `delay_template_7x7` | `input_net_transition` | `total_output_net_capacitance` |
| `setup`/`hold`/`recovery`/`removal` | `const_template_7x7` | **`constrained_pin_transition`** | **`related_pin_transition`** |
| `min_pulse_width` | `mpw_template_3x0` | `constrained_pin_transition` | — |
| `power_tout` | `power_tout_energy_template_7x7` | `input_transition_time` | `total_output_net_capacitance` |
| `power_tin` | `power_tin_energy_template_7x0` | `input_transition_time` | — |
| `passive` | `passive_energy_template_7x0` | `input_transition_time` | — |

**実装との対応**（`charao_run.py`）：`runSpiceConstSingle(..., index1_slope_const, index2_slope_rel)` で
`index1` → 制約信号（D / SET / RESET）の slew、`index2` → CLK の slew。**宣言と一致している**。

### 13.3 PDK ごとの違い — **sky130 の const 系だけ順序が逆**

```
                     const 系の variable_1 / variable_2
charao        constrained_pin_transition / related_pin_transition
gf180 orig    constrained_pin_transition / related_pin_transition   ← 同じ
sky130 orig   related_pin_transition / constrained_pin_transition   ← 逆
```

`delay` 系（`input_net_transition` / `total_output_net_capacitance`）と `power` 系
（`input_transition_time` / `total_output_net_capacitance`）は **3 者とも同じ**。**const 系だけ**が食い違う。

### 13.4 正規化の方針（`util_liberty.py`）

**`make_template` / `extract` では、常に charao の並び（§13.2）へ正規化してから
生成・比較する**（ダーマツ指示）。実装は `util_liberty.py` の `LibertyParser`：

```
_scan_templates()   .lib 全体を先読みし、template 名 -> (variable_1, variable_2) を収集
_need_transpose()   その table の軸順が charao 基準と逆なら True
_emit_table(..., transpose=True)
                    index1/index2 を入れ替え、values を row-major で詰め替える
                      new[c*n1+r] = old[r*n2+c]
```

**1D table（`variable_2` なし）は転置対象外。** 軸名が未知の template も従来動作のまま。

**⚠️ これを入れないと、sky130 の const 系は値が転置したまま orig と突合される。**
2026-08-15 以前の sky130 const の orig 比較（ISS-00218 / ISS-00227 の数字）は
**この状態で得たものなので再評価が要る**。gf180 は元から同じ並びなので影響しない。

**【検証】** 変更前後で 3 つの `.lib` をパースして全行比較：

```
                timing 値が変わった   power 値が変わった   行数・キー
sky130(orig)         3720                   0            保存
gf180(orig)             0                   0            保存
sky130(charao)          0                   0            保存
```

sky130 orig の const 系（`vio_3_3_1` を使う setup/hold/recovery/removal）**だけ**が転置され、
対角成分は不変、非対角が入れ替わることを `dfrtn_1` / `setup_falling` の 3×3 で確認した。

### 13.5 併せて修正 — `index_2` の単位スケール

`_emit_table` は `index_1` に `time_scale`、**`index_2` に一律 `cap_scale`** を掛けていた。
**const 系は `index_2` も時間（slew）**なので誤り。`variable_1/2` に
`total_output_net_capacitance` が含まれるときだけ `cap_scale`、それ以外は `time_scale` を掛ける。

**実害は出ていなかった**（sky130 / gf180 とも `time_unit = 1ns` / `capacitive_load_unit(1, pf)` で
両スケールが 1.0）。単位系の違う `.lib` を読むと値が壊れるため、先に直した。

---

## 14. 参照

- ISS-00101：ival/arc 値モデル刷新（本仕様書と並行進行）
- ISS-00108：charao .lib と orig .lib の構成・属性差分
- ISS-00109：SDFF/scan family で SI/SE 関連 timing arc が未対応
- ISS-00110：pin_oirc 仕様整理（i_in_leak 廃止部分実装済）
- ISS-00111：本課題（measure_type 全体整理、 上位課題）
- 関連 SPEC：`SPEC_ival.md` / `SPEC_specify.md` / `SPEC_internal_power.md` / `SPEC_three_state.md` / `SPEC_seq_ff.md` / `SPEC_seq_lat.md`
