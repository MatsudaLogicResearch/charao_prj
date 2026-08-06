# Sequential FF / SDFF cell support specification

このドキュメントは charao における順序回路（D-Flip-Flop と Scan-D-Flip-Flop）の
キャラクタライズ規約と、新規 PDK / プロセスへ移植する際の手順をまとめたものです。
GF180 PDK の `dffq` / `dffnq` / `dffrnq` / `dffnrnq` / `dffsnq` / `dffnsnq` /
`dffrsnq` / `dffnrsnq` を実装した経緯（v0.9.14a05 以降）に基づきます。

LATCH / Clock-gate は別 SPEC（追加予定）を参照。

## 1. 目的

- D-Flip-Flop family（edge-triggered seq cell）を charao で characterize する規約を定める
- 既存の OSU035 流 logic（`DFF_PC_NR_NS`/`DFFB_PC_*`）と GF180 流の差異を明確化
- 新規 PDK 移植時のチェックリストを提供

## 2. GF180 命名規則と charao logic 名のマッピング（メモ程度）

GF180 std cell の `dff[n][r][s]nq` 命名規則：

| 要素 | 意味 |
|---|---|
| `dff` | D-Flip-Flop |
| `[n]` (1 つ目) | **negedge clock**（CLKN 入力、 active edge は CLKN's negedge） |
| `[r]` | active-low reset `RN` 入力 |
| `[s]` | active-low set `SETN` 入力 |
| `nq` | 末尾の `n` は表記上の慣例、 **出力は Q-direct**（NQ ではない） |

charao logic 名（`DFF<B>_<P\|N>C[_<P\|N>R][_<P\|N>S]`）：

| GF180 cell | charao logic | clock | reset | set |
|---|---|---|---|---|
| dffq | DFF_PC | posedge | – | – |
| dffnq | DFF_NC | negedge | – | – |
| dffrnq | DFF_PC_NR | posedge | active-low | – |
| dffnrnq | DFF_NC_NR | negedge | active-low | – |
| dffsnq | DFF_PC_NS | posedge | – | active-low |
| dffnsnq | DFF_NC_NS | negedge | – | active-low |
| dffrsnq | DFF_PC_NR_NS | posedge | active-low | active-low |
| dffnrsnq | DFF_NC_NR_NS | negedge | active-low | active-low |

**全 GF180 std cell は Q-direct 出力**。 Q-bar 出力 cell（OSU035 / TRIP62 系の `DFFB_*`）は別系統で、
本仕様の対象外。

## 3. logic_dict の field 構造（全体仕様）

詳細は別 SPEC（charao_core 仕様、 後日整備予定）を参照。

本 SPEC では FF 固有の field のみ触れる：
- `logic_type`: `"seq"`
- `functions`: `{"o0":"Io0"}`（出力 Q = internal Io0）
- `ff`: `{"out", "next_state", "clocked_on", "clear"?, "preset"?}`
- `vcode`: GF180 wrap 流の Verilog コード（§6 参照）
- `expect`: MyExpectCell リスト

## 4. MyExpectCell の 4 要素 spec（全体仕様）

詳細は `docs/SPEC_pin_oirc.md` を参照。 `pin_oirc` / `arc_oirc` は **4 要素必須**：

| index | 対応 pin |
|---|---|
| [0] | output port |
| [1] | input port |
| [2] | related port |
| [3] | **clock port**（seq）または `""`（comb / tristate） |

comb / tristate cell では [3] = `""`、 seq では [3] = `"c0"`。

**注（現行仕様）**：
- `mondrv_oirc` は ISS-00101 で**廃止**（省略。spice 駆動値は arc_oirc/ival から決定）。
- **Liberty 出力の target / related pin は別 field `pin_tr`（ISS-00127、全 entry 必須）で決まる**
  （`pin_oirc` からの自動推定は不採用）。詳細は `docs/SPEC_pin_oirc.md` §5。

## 5. meas_types の使い分け（全体仕様）

詳細は別 SPEC を参照。 FF / SDFF で使用する meas_types：

| meas_type | 用途 |
|---|---|
| `rising_edge` / `falling_edge` | clock edge → Q transition delay |
| `setup_rising` / `setup_falling` | D setup time to CLK edge |
| `hold_rising` / `hold_falling` | D hold time from CLK edge |
| `clear` | async reset arc (RN fall → Q fall) |
| `preset` | async set arc (SETN fall → Q rise) |
| `recovery_rising` / `recovery_falling` | RN/SETN release to CLK edge |
| `removal_rising` / `removal_falling` | CLK edge after RN/SETN release |
| `power_tout` | 出力遷移時の internal power（各 timing arc entry の `meas_types` に併載）|
| `power_tin` | 入力遷移時の internal power（出力遷移を伴わない入力遷移）|
| `passive` | input pin の容量計測（capacitance） |
| `min_pulse_width_high` | CLK の最小 H pulse 幅（posedge cell） |
| `min_pulse_width_low` | CLKN / RN / SETN の最小 L pulse 幅 |
| `leakage` | 静止状態の各 conditions（2^N 通り） |

## 6. vcode 構造（GF180 wrap 流）

GF180 std cell は `dff*_func` wrap module で primitive を呼ぶ：
1. 必要に応じて **clock を not gate で反転**（negedge cell の場合）
2. 反転 latch design の family では **D を not gate で反転**（基本 posedge DFF〔DFF_PC〕は D 直結・反転なし）
3. RN / SETN を not gate で反転（active high の C / P に変換）
4. **`reg notifier;` を宣言**（ISS-00147）
5. **primitive 呼び出し**（`udp_iq_ff_n` or `udp_iq_ff_hn`）、末尾 N ポートに `notifier` を接続
6. primitive 出力 IQ1 を not gate で反転 → Q

charao の vcode 例（DFF_PC_NR_NS、 dffrsnq 用。ISS-00147 で notifier 宣言＋N 接続を追加）：

```verilog
reg notifier;       // ISS-00147: timing check の notifier（未宣言だと厳密ツールでエラー）
wire p_int; wire c_int; wire d_int; wire iq1;
not (p_int, r0);    // RN → !RN (active high P)
not (c_int, s0);    // SETN → !SETN (active high C)
not (d_int, i0);    // D → !D
udp_iq_ff_hn inst (iq1, c_int, p_int, c0, d_int, notifier);  // hn = P dominates over C、末尾 N = notifier
not (o0, iq1);      // IQ1 → !IQ1 = Q
```

primitive の選択：
- reset / set 両方 → `udp_iq_ff_hn`（P が C より優先）
- それ以外 → `udp_iq_ff_n`

negedge clock の場合は冒頭に `wire clkn_int; not (clkn_int, c0);` を追加し、 primitive の CK 引数を `clkn_int` に。

## 7. std_seq.jsonc cell entry 構造

```jsonc
{"template_kgn":[["leakage","0x0","d00"],
                 ["const","10x10","d00"],
                 ["delay","10x10","d016"],
                 ["power_tout","10x10","d016"],
                 ["passive","10x0","d00"]],
 "spice":"gf180mcu_fd_sc_mcu7t5v0.spice",
 "cell":"gf180mcu_fd_sc_mcu7t5v0__dffrsnq_1",
 "logic":"DFF_PC_NR_NS",
 "area":85.6128,
 "primitive":"udp_iq_ff_hn",
 "ports_dict":{"D":"i0","RN":"r0","SETN":"s0","CLK":"c0","Q":"o0",
               "VDD":"vdd","VNW":"vnw","VPW":"vpw","VSS":"vss"}}
```

注意：
- `ports_dict` の順序は **SPICE subckt の port 順序と一致**させる
- `primitive` field は将来の自動 vcode 生成用（現状 charao は使用していない）

## 8. 8 family の DFF 実装例（GF180）

| logic | primitive | vcode（CK 引数） | C 引数 | P 引数 | leakage 条件数 |
|---|---|---|---|---|---|
| DFF_PC | udp_iq_ff_n | c0 | 1'b0 | 1'b0 | 4 (i0 × c0) |
| DFF_NC | udp_iq_ff_n | clkn_int | 1'b0 | 1'b0 | 4 |
| DFF_PC_NR | udp_iq_ff_n | c0 | 1'b0 | p_int | 8 (+ r0) |
| DFF_NC_NR | udp_iq_ff_n | clkn_int | 1'b0 | p_int | 8 |
| DFF_PC_NS | udp_iq_ff_n | c0 | c_int | 1'b0 | 8 (+ s0) |
| DFF_NC_NS | udp_iq_ff_n | clkn_int | c_int | 1'b0 | 8 |
| DFF_PC_NR_NS | udp_iq_ff_hn | c0 | c_int | p_int | 16 (+ r0,s0) |
| DFF_NC_NR_NS | udp_iq_ff_hn | clkn_int | c_int | p_int | 16 |

各 logic の MyExpectCell 構成パターン：
- `rising_edge` / `falling_edge`: 2 entries (D=0/1)
- `setup` / `hold`: 各 2 entries
- `clear`: 1 entry (reset 系のみ)
- `preset`: 1 entry (set 系のみ)
- `recovery` / `removal`: reset/set 各 1 entry
- `passive`: data × 2 + clk × 2 + (reset × 2) + (set × 2)
- `min_pulse_width_high`: CLK の H pulse（posedge 系のみ）
- `min_pulse_width_low`: CLKN / RN / SETN の L pulse
- `leakage`: 2^N 条件（N = input/clk/reset/set の数）

## 9. 新規 PDK への移植手順

### Step 1: orig Liberty 構造の確認

対象 DFF cell の Liberty で：
- `ff(IQ_name, IQB_name)` block の `clocked_on` / `next_state` / `clear` / `preset`
- pin(Q) の `function`（出力極性、 通常 Q-direct なら IQ_name）
- timing arc 種類（rising_edge / setup / hold / clear / preset / recovery / removal）
- leakage_power の when 条件数（2^N）

### Step 2: SPICE subckt の解析

```bash
awk '/.SUBCKT <cell_name> /,/.ENDS/' <pdk>.spice
```

確認項目：
- 端子順序（ports_dict 用）
- 内部 net 名（`MGM_*` 等）：vcode 構造の参考

orig .v の `<cell>_func` module を確認：
```bash
grep -A 30 "module <cell>_func" <pdk>.v
```
not gate + primitive 呼び出しの構造を把握。

### Step 3: charao primitive の選択 / 追加

GF180 の 4 primitive（`udp_iq_ff_n` / `udp_iq_ff_hn` / `udp_iq_latch_n` / `udp_iq_latch_hn`）が
**charao の `get_code_primitive()` に登録済**。

別 PDK の primitive が互換でない場合、 `mylogic_seq_ff.py` の `get_code_primitive()` に
追加 primitive を含める（Apache 2.0 等のライセンスコメントを保持）。

### Step 4: mylogic_seq_ff.py に logic 追加

既存 8 logic（DFF_PC / DFF_NC / DFF_PC_NR / DFF_NC_NR / DFF_PC_NS / DFF_NC_NS /
DFF_PC_NR_NS / DFF_NC_NR_NS）が **GF180 wrap 流のテンプレート**。

新 PDK でも同じ命名規則・wrap 構造が使えるなら、 logic 追加は **ports_dict のマッピング**のみで可。

orig Liberty / SPICE が異なる場合（例：D 反転なし、 Q-bar 出力、 別 primitive など）、
新規 logic 名で定義する。

### Step 5: std_seq.jsonc に cell entry 追加

§7 のテンプレートに従って `template_kgn` / `cell` / `logic` / `area` / `primitive` /
`ports_dict` を記載。 サイズ展開（_1 / _2 / _4 等）は `area` を変えるのみ。

### Step 6: 動作確認

```bash
CELLS="<cell_name>" INDEX1="0 9" INDEX2="0 9" EXEC_MACHINE=server EXEC_SCRIPT=local_repo bash debug_run.sh clean run_all
```

確認：
- `failed-spice grep: 0 failures`
- `.lib` の `ff(...)` / `pin(Q)` / `timing()` / `leakage_power()` 構造が orig と一致
- `.v` の `udp_iq_ff_n/hn inst (...)` の引数順序が正しい

### Step 7: meas_types 個別確認（必要に応じて）

```bash
CELLS="<cell_name>" INDEX1="0 9" INDEX2="0 9" MEAS_ONLY="rising_edge" EXEC_MACHINE=server EXEC_SCRIPT=local_repo bash debug_run.sh clean run_all
```

`MEAS_ONLY` で 1 meas_type ずつ動作確認、 デバッグ時に有用。

### Step 8: フル INDEX + orig 比較

```bash
CELLS="<cell_name>" EXEC_MACHINE=server EXEC_SCRIPT=local_repo bash debug_run.sh clean run_all merge lib2csv compare
```

`tmp/compare_*.summary.txt` で matched groups / diff avg を確認。

## 10. 既知の制限事項

- 既存 OSU035 用 `DFF_PC_NR_NS` を GF180 流で上書きしている（v0.9.14a05 で確定）。
  OSU035 std_seq.jsonc は別途修正が必要（DFFARAS_1X の logic 名 rename or 別 logic 定義）
- 既存 TRIP62 用 `DFFB_PC_PR` / `DFFB_PC_NS`（Q+QB 2 出力系）は GF180 では未使用、 mylogic_seq_ff.py に保持（実行回帰は ISS-00141）
- SDFF（scan FF）は `mylogic_seq_scan.py`（SDFF_PC/_NR/_NS/_NR_NS）に実装済、LAT / ICG は `docs/SPEC_seq_lat.md` に整備済（本項の「別 SPEC で整備予定」は解消）
- **ドライブ変種**（ISS-00158/a31）：dff/sdff/lat/icg 各 family に `_2`/`_4` を追加し target 215 セル化（cell 名・area のみ差、logic/ports は `_1` と同一）
- **`.v` specify**（ISS-00147/a32）：各 entry の specify（`$setup`/`$hold`/`$width`＋`reg notifier`、ifnone 切替）は `docs/SPEC_specify.md` を参照

## 11. 参照

- 関連 issue: ISS-00070（DFF/LAT/SDFF/ICGT 順序系、解決済）、ISS-00147（.v specify）、ISS-00158（_2/_4 変種）、ISS-00141（OSU035/TRIP62 回帰）
- 関連 spec: `docs/SPEC_specify.md`、`docs/SPEC_pin_oirc.md`、`docs/SPEC_seq_lat.md`、`docs/SPEC_internal_power.md`、`docs/SPEC_three_state.md`
- 実装ファイル: `charao/script/mylogic_seq_ff.py`、 `sample_target/gf180/fd/mcuC7t20240817/std_seq.jsonc`
- primitive 定義: `mylogic_seq_ff.py` の `get_code_primitive()`（GF180 PDK Authors / Apache 2.0）
