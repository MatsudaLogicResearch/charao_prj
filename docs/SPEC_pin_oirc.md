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

## 3. 全 measure_type × spice 駆動 × Liberty 出力 網羅表（2026-07-11 改訂＝ISS-00135 reorg 後の現行）

> **現行の大原則（ISS-00135 reorg、 2026-06 確定）**：
> - **同一 DUT pin を複数 slot に重複指定することは不可**（旧「[2]=同[1]」記法は廃止）。 各 pin は「それを駆動する 1 slot」 にのみ書く
> - Liberty の target/related pin は **`pin_tr` で明示**（pin_oirc は spice 駆動専用）
> - ある pin がどの slot で駆動されているかの逆引きは **c > r > i の優先順**（`myTbParam.set_common_value` 参照）
> - power_tin の積分窓・slope・cin は **target スロット方式**（ISS-00142）：`pin_tr[0]` の逆引きで `energy_tgt_slot/node` を決め、 その slot の遷移時刻（t_in0/1、 t_clk4/5、 t_rel0/1）を窓に使う。 energy_start のトリガは `pin_tr[1]` の逆引き（`energy_trig_slot`）

| # | measure_type | template_kind | spice 駆動の pin_oirc（現行例） | spice 計測 | Liberty 出力 |
|---|---|---|---|---|---|
| 1 | `delay`（comb） | delay | `[o0, "", i0, ""]`＝[0]=VOUT 観察, **[2]=VREL が入力駆動**, [1]/[3]=空 | input → output delay | `pin(pin_tr[0]=o0) timing { related_pin=pin_tr[1]=i0 }` |
| 2 | `rising_edge` / `falling_edge` | delay | `[o0, i0, "", c0]`＝[1]=VIN=D（初期値）, [3]=VCLK=CLK | CLK edge → output delay | `pin_tr=[o0, c0]` |
| 3 | `clear` | delay | `[o0, i0, r0, c0]`＝**[2]=VREL=RN（active edge 元）** | RN active → Q clear delay | `pin_tr=[o0, r0]` |
| 4 | `preset` | delay | `[o0, i0, s0, c0]`＝**[2]=VREL=SETN** | SETN active → Q preset delay | `pin_tr=[o0, s0]` |
| 5 | `three_state_enable` / `three_state_disable` | delay | [2]=VREL=EN pin | EN switching → Z 遷移 delay | `pin_tr=[o0, EN]` |
| 6 | `power_tout` | power_tout | （同 delay/rising_edge。 併記 meas_types） | output 遷移時 energy | `pin(pin_tr[0]) internal_power { related_pin=pin_tr[1], when }` |
| 7 | `power_c2c` / `i2c` / `c2i` / `i2i` | power_* | 同 | clk-to-clk 等の power | 同 |
| 8 | **`power_tin`（input pin X）** | power_tin | X の駆動 slot は種別で異なる：pin(D)=`[o0, i0, "", c0]`（slot1）、 pin(CLK)=`[o0, i0, "", c0]` で **X=CLK は slot3 駆動**、 pin(RN)=slot2。 **窓/slope/cin は `pin_tr[0]` の逆引き（energy_tgt_slot、 ISS-00142）** | X switching 時 energy | `pin(pin_tr[0]=X) internal_power { related 省略 }`（`pin_tr=[X, ""]`） |
| 9 | `power_tin`（biport HOLD 等） | power_tin | [0]=biport pin | biport switching | `pin_tr=[biport, ""]` |
| 10 | `passive`（input stable state） | passive | `["", "", i0, ""]`＝[2]=VREL が入力駆動 | static state での energy | `pin_tr=[i0, ""]` |
| 11 | `setup_rising` / `setup_falling` | const | `[o0, i0, "", c0]`＝[1]=VIN=D（constrained）, [3]=VCLK=CLK/E, **[2]=空** | D vs CLK 距離 secant | `pin_tr=[i0, c0]` |
| 12 | `hold_rising` / `hold_falling` | const | 同 setup | 同（判定は SPEC_const.md §1 参照） | `pin_tr=[i0, c0]` |
| 13 | `recovery_rising` / `recovery_falling` | const | `[o0, i0, r0/s0, c0]`＝**[2]=VREL=async（RN/SETN）駆動**（async-on-VREL、 a26〜） | async vs CLK 距離 secant | `pin_tr=[r0/s0, c0]` |
| 14 | `removal_rising` / `removal_falling` | const | 同 recovery | 同 | `pin_tr=[r0/s0, c0]` |
| 15 | `min_pulse_width_high/low` | （専用 logic） | `[o0, i0, "", c0]`＝**計測対象 CLK は slot3 駆動**（`ival c=["p"/"n"]` でパルス生成）。 RN/SETN 対象は slot2 | pulse 幅 secant | `pin_tr=[c0, ""]` 等（`pin(pin_tr[0])` に scalar constraint） |
| 16 | `leakage` | leakage | static state（[1]/[2]/[3] で各 input 値。 `pin_tr=["",""]` 必須） | static current | **cell-level** `leakage_power { when, value }` |

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

### 5.2 measure 別の具体例（2026-07-11 改訂＝現行 mylogic の実パターン。 重複指定なし）

| measure | `pin_oirc`（spice 駆動）| `pin_tr`（Liberty 出力）| 解説 |
|---|---|---|---|
| `delay`（comb）/ `power_tout` | [o0, "", **i0**, ""] | [**o0**, i0] | 入力は VREL（slot2）駆動。 target=output、 related=入力 |
| `rising_edge` / `power_tout`（seq） | [o0, i0, "", **c0**] | [**o0**, c0] | CLK は VCLK（slot3）駆動、 D は VIN（初期値） |
| `power_tin` pin(D) | [o0, **i0**, "", c0] | [**i0**, ""] | target=D（slot1 駆動、 energy_tgt_slot=1） |
| `power_tin` pin(CLK) | [o0, i0, "", **c0**] | [**c0**, ""] | target=CLK（slot3 駆動、 energy_tgt_slot=3。 ISS-00142） |
| `passive` | ["", "", **i0**, ""] | [**i0**, ""] | 入力は VREL 駆動、 target=input static |
| `setup_*` / `hold_*` | [o0, **i0**, "", c0] | [**i0**, c0] | slot2 は空（旧 [2]=c0 重複は廃止）。 target=D、 related=CLK/E |
| `recovery_*` / `removal_*` | [o0, i0, **r0/s0**, c0] | [**r0/s0**, c0] | async は VREL（slot2）駆動（async-on-VREL、 a26〜）。 target=async、 related=CLK/E |
| `clear` | [o0, i0, **r0**, c0] | [**o0**, r0] | target=output Q、 related=RN |
| `preset` | [o0, i0, **s0**, c0] | [**o0**, s0] | target=output Q、 related=SETN |
| `three_state_enable/disable` | [o0, i0, **i1**, c0] | [**o0**, i1] | target=Z output、 related=EN |
| `min_pulse_width_high/low`（CLK） | [o0, i0, "", **c0**] | [**c0**, ""] | 計測対象 CLK は slot3 駆動（ival c=["p"/"n"]）、 related なし |
| `leakage` | static state | [**""**, ""]（空ペア必須） | cell-level 出力 |

### 5.3 pin_tr は全 entry 必須（自動推定は不採用）

**`pin_tr` は全 mylogic entry に必須記載**。空だと error 終了する
（`myConditionsAndResults.py` `set_lib_target_related`：`[Error] ISS-00127: pin_tr is mandatory`）。
ISS-00127 の当初計画（§5.4）では「未指定なら pin_oirc から自動推定」する後方互換を想定したが、
**曖昧さ排除のため自動推定は実装せず、明示必須に確定**した。

以下は各 measure での `pin_tr` の**書き方の指針**（旧・自動推定案の対応表を、明示記述の目安として残す）：

| template_kind | `pin_tr` = [target, related] の目安 |
|---|---|
| `delay` / `power_tout` / `power_c*` / `power_i*` | `[pin_oirc[0], pin_oirc[2]]` |
| `power_tin` / `passive` | `[pin_oirc[1], ""]`（別 pin 指定時は明示、例 power_tin pin(E) は `[c0,""]`）|
| `const`（setup/hold/recovery/removal）| `[pin_oirc[1], pin_oirc[2]]` |
| `min_pulse_width_*` | `[pin_oirc[1], ""]` |
| `leakage` | `["", ""]`（cell-level、target/related なし）|

spice 駆動と Liberty 出力で pin が異なるケース（例 power_tin pin(E) で spice 上 `[o0,c0,c0,c0]` だが
Liberty は pin(E) を出す）は、目安に依らず `pin_tr=[c0,""]` を明示指定する。

### 5.4 実装計画（ISS-00127）

1. `myExpectCell.py` に `pin_tr: list[str]` field 追加（default=[]、ただし**空は error＝実質必須**。自動推定は不採用）
2. `myConditionsAndResults.py` の `set_lib_target_related` で `pin_tr[0]=target / pin_tr[1]=related` を設定（空なら `[Error] ISS-00127`）
3. `myExportLib.py` の `target_inport == port` / `target_outport == port` 等の filter を `pin_tr[0]` ベースに変更
4. 全 mylogic（comb / seq〔ff/scan/lat〕/ io）で **全 entry に `pin_tr` を明示**（自動推定なし）＝対応済

### 5.5 メリット

- spice 制御と Liberty 出力が **構文的に分離**、 意味が明確
- pin 別 designation（power_tin pin(E) 等）を `pin_tr` 明示で確実に指定（自動推定の曖昧さを排除）
- 2026-06-08 LATCH 誤修正のような「pin_oirc[1]=i0 に変更で pin(E) が消える」 bug を構文的に防止

## 6. 補足：ISS-00118 との関係

ISS-00118 は「pin_oirc[1]/[2] の measure 別意味の整理」 を扱う。 本 SPEC（pin_oirc 全体の意味、 ISS-00126）は ISS-00118 の上位整理として位置づけ、 ISS-00118 で残った課題（pin_oirc[1]/[2] の具体的 mapping）も本 SPEC に統合する。

## 改訂履歴

| 日付 | 内容 | 関連 ISS |
|---|---|---|
| 2026-06-08 | 初版作成（ISS-00126） | ISS-00126、 ISS-00118 |
| 2026-07-11 | §3/§5.2 を現行実装に改訂（ISS-00144 対応）：同一 pin の重複指定不可を明記、 「[2]=同[1]」記法を廃止、 const の slot2 空／async-on-VREL、 power_tin の target スロット方式（energy_tgt_slot/energy_trig_slot）を追記 | ISS-00144、 ISS-00135、 ISS-00142 |
