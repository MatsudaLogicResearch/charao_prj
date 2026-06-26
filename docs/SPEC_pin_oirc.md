# SPEC: pin_oirc 仕様（spice 制御 と Liberty 出力 の mapping）

ISS-00118 / ISS-00126 関連。 mylogic の `pin_oirc[0/1/2/3]` が charao 内でどう解釈され、 spice 制御（testbench 駆動）と Liberty 出力（.lib pin / related_pin / internal_power）にそれぞれどう mapping されるかを明文化する。

## 1. pin_oirc 各位置の意味

| 位置 | 名称 | spice 駆動の意味 | Liberty 出力での使われ方 |
|---|---|---|---|
| **pin_oirc[0]** | output | VOUT 観察 pin（driver なし、 cell 内部 driver にお任せ） | **delay / power_tout 系の `pin (X)` の X**（output 観察 pin）|
| **pin_oirc[1]** | input | VIN 駆動 pin（計測対象 input） | **power_tin / const / passive 系の `pin (X)` の X**（input 計測 pin）|
| **pin_oirc[2]** | related | VREL 駆動 pin（slew 計測対象 + related pin） | **timing / internal_power(output) の `related_pin (Y)` の Y** |
| **pin_oirc[3]** | clock | VCLK 駆動 pin（active edge / 補助 CLK） | **.lib に直接出力されない**（sim 内部の edge 駆動のみ）|

## 2. charao 内 field mapping（myConditionsAndResults.py）

```python
target_outport = pin_oirc[0]    # set_target_outport()
target_inport  = pin_oirc[1]    # set_target_inport()   ← .lib の pin(X) を決定（input 系）
target_relport = pin_oirc[2]    # set_target_relport()  ← related_pin (Y) を決定
target_clkport = pin_oirc[3]    # set_target_clkport()  ← .lib には出ない
```

## 3. 全 measure_type × spice 駆動 × Liberty 出力 網羅表

| # | measure_type | template_kind | spice 駆動の pin_oirc 意味 | spice 計測 | Liberty 出力 |
|---|---|---|---|---|---|
| 1 | `delay`（CLK 無し） | delay | [0]=VOUT 観察, [1]=VIN slew input, [2]=同 [1], [3]=- | input → output delay | `pin([0]) timing { related_pin=[2], timing_type="delay" }` |
| 2 | `rising_edge` / `falling_edge` | delay | [0]=VOUT 観察, [1]=stable D, [2]=related (CLK 等), [3]=CLK | CLK edge → output delay | `pin([0]) timing { related_pin=[2], timing_type="rising_edge"\|"falling_edge" }` |
| 3 | `clear` | delay | [0]=VOUT 観察, [1]=stable D, **[2]=RN (active edge 元)**, [3]=CLK | RN active → Q clear delay | `pin([0]) timing { related_pin=[2] (=RN), timing_type="clear" }` |
| 4 | `preset` | delay | [0]=VOUT 観察, [1]=stable D, **[2]=SETN (active edge 元)**, [3]=CLK | SETN active → Q preset delay | `pin([0]) timing { related_pin=[2] (=SETN), timing_type="preset" }` |
| 5 | `three_state_enable` / `three_state_disable` | delay | [0]=VOUT 観察, [1]=stable D, **[2]=EN pin**, [3]=- | EN switching → Z 遷移 delay | `pin([0]) timing { related_pin=[2] (=EN), timing_type="three_state_*" }` |
| 6 | `power_tout` | power_tout | （同 delay/rising_edge） | output 遷移時 energy | `pin([0]) internal_power { related_pin=[2], when }` |
| 7 | `power_c2c` / `i2c` / `c2i` / `i2i` | power_* | 同 | clk-to-clk 等の power | `pin([0]) internal_power { related_pin=[2] }` |
| 8 | **`power_tin` (input pin X)** | power_tin | [0]=VOUT 観察, **[1]=X 駆動 (計測対象 input)**, [2]=同 [1] (VREL=同 X), [3]=他 CLK 駆動 | X switching 時 energy | `pin([1] = X) internal_power { related_pin omitted (=same X), when }` |
| 9 | `power_tin` (biport HOLD 等) | power_tin | [0]=biport pin, [1]=- (or biport), [2]=同, [3]=- | biport switching | `pin([0] = biport) internal_power { related_pin omitted }` |
| 10 | `passive` (input stable state) | passive | [1]=input X stable, [2]=同 | static state での energy | `pin([1] = X) internal_power` |
| 11 | `setup_rising` / `setup_falling` | const | [0]=VOUT 観察, **[1]=D (計測 input)**, [2]=CLK (active edge), [3]=CLK | D vs CLK 距離 bisection | `pin([1] = D) timing { related_pin=[2] (=CLK), timing_type="setup_*" }` |
| 12 | `hold_rising` / `hold_falling` | const | 同 setup | 同 | `pin([1] = D) timing { related_pin=[2] (=CLK), timing_type="hold_*" }` |
| 13 | `recovery_rising` / `recovery_falling` | const | [0]=VOUT 観察, **[1]=async pin (RN/SETN)** (setup/hold コード流用都合), [2]=CLK, [3]=CLK | async vs CLK 距離 bisection | `pin([1] = RN/SETN) timing { related_pin=[2] (=CLK), timing_type="recovery_*" }` |
| 14 | `removal_rising` / `removal_falling` | const | 同 recovery | 同 | `pin([1] = RN/SETN) timing { related_pin=[2] (=CLK), timing_type="removal_*" }` |
| 15 | `min_pulse_width_high/low` | （専用 logic） | [0]=VOUT 観察, **[1]=計測対象 pin (CLK/E/RN/SETN)**, [2]=同, [3]=同 | pulse 幅 bisection | `pin([1]) timing { rise/fall_constraint scalar, timing_type="min_pulse_width" }` |
| 16 | `leakage` | leakage | static state（[1]/[2]/[3] で各 input 値） | static current | **cell-level** `leakage_power { when (各 input state), value }` |

## 4. spice 制御 と Liberty 出力 が ずれるパターン

### 4.1 同じ pin_oirc[1] が 2 つの意味を兼ねる
- spice 側：VIN 駆動 pin（電圧源 VIN を接続する pin）
- Liberty 側：input pin 識別子（`pin (X){}` の X を決定）

→ 両者は **同じ pin であるべき**。 別 pin にすると整合崩れる。

### 4.2 実例：2026-06-08 LATCH power_tin pin(E) の誤修正

**意図**: rising_edge entry が `pin_oirc=["o0","i0","c0","c0"]` だったので、 power_tin pin(E) も同構造に統一しようとした。

**結果**:
- `pin_oirc[1]=i0` に変更 → spice では VIN=D 駆動 + Liberty では target_inport=i0=D
- pin(E) entry が pin(D) の internal_power として group 化
- **pin(E) の internal_power が空**になり .lib 破綻

**正解**: `pin_oirc[1]=c0`（VIN=E、 spice / Liberty 両側で「pin=E」 として整合）

### 4.3 recovery/removal の pin_oirc[1] 非対称

- spice 側：[1]=async pin (RN/SETN)（setup/hold コード流用都合、 VIN slew が async pin に印加される必要）
- Liberty 側：pin (RN/SETN) timing の constraint として出力

→ async pin の setup/hold/recovery/removal constraint を出すには pin_oirc[1]=async pin で **両側整合**。

## 5. mylogic field 分離（2026-06-08 ダーマツ確定、 ISS-00127 で実装）

### 5.1 確定設計

mylogic に 2 つの field を持つ：

| field | 用途 | 構造 | 各位置の意味 |
|---|---|---|---|
| **`pin_oirc[0/1/2/3]`** | spice 制御（testbench 駆動）| 4 要素 | [0]=**o** (VOUT), [1]=**i** (VIN), [2]=**r** (VREL), [3]=**c** (VCLK) |
| **`pin_tr[0/1]`** | Liberty 出力 | 2 要素 | [0]=**t** (target pin、 `pin (X)` の X)、 [1]=**r** (related pin、 `related_pin (Y)` の Y) |

- `arc_oirc` も `pin_oirc` と同じ構造（4 要素、 各位置 o/i/r/c）
- 端子機能の優先順：**c > r > i**（同じ DUT pin が複数位置に出る場合、 VCLK が最優先で active edge 制御として扱う）

### 5.2 measure 別の具体例

| measure | `pin_oirc`（spice 駆動）| `pin_tr`（Liberty 出力）| 解説 |
|---|---|---|---|
| `delay` / `rising_edge` | [o0, i0, c0, c0] | [**o0**, c0] | target=output Q、 related=CLK |
| `power_tout` | [o0, i0, c0, c0] | [**o0**, c0] | 同上、 internal_power(output) |
| `power_tin` pin(E) | [o0, **c0**, c0, c0] | [**c0**, ""] | target=E、 related 省略（=same input）|
| `power_tin` pin(D) | [o0, **i0**, i0, c0] | [**i0**, ""] | target=D、 related 省略 |
| `passive` | [o0, i0, i0, ""] | [**i0**, ""] | target=D static、 related 省略 |
| `setup_rising` / `hold_rising` | [o0, i0, c0, c0] | [**i0**, c0] | target=D（input）、 related=CLK |
| `recovery_rising` / `removal_rising` | [o0, **r0**, c0, c0] | [**r0**, c0] | target=async (RN/SETN)、 related=CLK |
| `clear` | [o0, i0, **r0**, c0] | [**o0**, r0] | target=output Q、 related=RN |
| `preset` | [o0, i0, **s0**, c0] | [**o0**, s0] | target=output Q、 related=SETN |
| `three_state_enable/disable` | [o0, i0, **i1**, c0] | [**o0**, i1] | target=Z output、 related=EN |
| `min_pulse_width_high/low` | [o0, **c0**, c0, c0] | [**c0**, ""] | target=計測対象 pin、 related なし |
| `leakage` | static state | （cell-level、 `pin_tr` 不要）| - |

### 5.3 互換性（後方互換ロジック）

`pin_tr` 未指定 entry は `pin_oirc` から自動推定：

| template_kind | `pin_tr` 推定 |
|---|---|
| `delay` / `power_tout` / `power_c*` / `power_i*` | `[pin_oirc[0], pin_oirc[2]]` |
| `power_tin` / `passive` | `[pin_oirc[1], ""]` |
| `const`（setup/hold/recovery/removal）| `[pin_oirc[1], pin_oirc[2]]` |
| `min_pulse_width_*` | `[pin_oirc[1], ""]` |
| `leakage` | （cell-level、 `pin_tr` 不要）|

明示が必要な entry（spice 駆動と Liberty 出力で pin が異なるケース、 例 power_tin pin(E) で spice 上 `[o0,c0,c0,c0]` で Liberty pin(E) を出す等）は `pin_tr=[c0,""]` を明示指定。

### 5.4 実装計画（ISS-00127）

1. `myExpectCell.py` に `pin_tr: list[str]` field 追加（default=[]、 空なら 5.3 の自動推定）
2. `myConditionsAndResults.py` の `set_target_outport/inport/relport` を `pin_tr[0]/pin_tr[1]` ベースに変更
3. `myExportLib.py` の `target_inport == port` / `target_outport == port` 等の filter を `pin_tr[0]` ベースに変更
4. 全 mylogic（comb 6 + seq 4 + io）は **順次対応**：自動推定で済むものは追加不要、 明示が必要な entry のみ `pin_tr` 追加

### 5.5 メリット

- spice 制御と Liberty 出力が **構文的に分離**、 意味が明確
- 同 pin 兼用の場合は自動推定で `pin_tr` 省略可（記述簡略）
- pin 別 designation が必要な場合（power_tin pin(E) 等）は `pin_tr` 明示で対応
- 2026-06-08 LATCH 誤修正のような「pin_oirc[1]=i0 に変更で pin(E) が消える」 bug を構文的に防止

## 6. 補足：ISS-00118 との関係

ISS-00118 は「pin_oirc[1]/[2] の measure 別意味の整理」 を扱う。 本 SPEC（pin_oirc 全体の意味、 ISS-00126）は ISS-00118 の上位整理として位置づけ、 ISS-00118 で残った課題（pin_oirc[1]/[2] の具体的 mapping）も本 SPEC に統合する。

## 改訂履歴

| 日付 | 内容 | 関連 ISS |
|---|---|---|
| 2026-06-08 | 初版作成（ISS-00126） | ISS-00126、 ISS-00118 |
