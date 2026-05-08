# CHANGELOG

このファイルは UTF-8 で記述されています。

---

## [0.9.14a03] 2026-05-08

Alpha pre-release toward `1.0.0`. Adds full tri-state / bus-keeper cell support: HOLD bus keeper (ISS-00069) and BUFZ / INVZ tri-state buffer/inverter all 14 cells (ISS-00066) with three_state_enable / three_state_disable timing arcs.

### Added
- `docs/SPEC_three_state.md`: developer-facing specification for tri-state / bus-keeper cell characterization. Covers Liberty output structure (biport vs output direction), `mylogic_*.py` logic_dict and cell-entry `oe_infos` rules, MyExpectCell patterns for active / enable / disable arcs, charao internal flow (dispatch / tb / pullres), and a step-by-step porting guide for new PDKs.
- `charao/script/mylogic_comb_tristate.py`: HOLD / BUFZ / INVZ logic definitions including three_state_enable / three_state_disable arc MyExpectCells.
- `delay_disable` template kind: 1D (10x0, slope only, load-independent) template for `three_state_disable` arc. Added across `myItem.py`, `myLogicCell.py`, `myLibrarySetting.py`, `myConditionsAndResults.py`, `charao_run.py`, `myExportDoc.py`, plus `delay_disable_10x0_d00` entry in `config_lib.jsonc`.
- `sample/target/gf180/fd/mcuC7t20240817/std_comb.jsonc`: 14 cell entries (`bufz_1/2/3/4/8/12/16`, `invz_1/2/3/4/8/12/16`) with `oe_infos` (NI_N / NI_P internal gate signals) and HOLD entry.
- `sim_pullres_std_enable` / `sim_pullres_std_disable` / `sim_pullres_io_enable` / `sim_pullres_io_disable` (`myLibrarySetting.py`): cell-type-aware pullres for three_state arcs (defaults: 100k / 0.1 / 100 / 1).

### Changed
- `charao/script/charao_run.py`:
  - `runSpicePowerTinSingle`: estart/eend now computed as absolute time (`_t_in1 + _tdelay_rel`) so the VREL transition window is covered for biport input pins (HOLD).
  - three_state dispatch generalized to `startswith("three_state_")` (no `_c2i` suffix required).
  - 1D template fallback: `delay_disable` accepts empty `index_2` and uses `[0.0]` as a single load corner.
- `charao/script/myConditionsAndResults.py`: dispatch generalized; `set_lut` accepts `delay_disable` kind.
- `charao/script/myExportLib.py`:
  - biport block emits `three_state` via `replace_by_portmap` so cell-side condition expressions (e.g. `(!i1)`) resolve to portmap'd port names (`(!EN)`).
  - output pin block now emits `driver_type` and `three_state` attributes from `logic_dict`.
- `charao/script/myExportDoc.py`: handles 1D template (empty `index_2`) when emitting three_state markdown tables.
- `charao/script/myTbParam.py`: `pullres` selection now branches on `h.mlc.isio` to pick std vs io variants.
- `charao/script/myLogicCell.py`, `myLibrarySetting.py`, `myItem.py`: `delay_disable` added to literal lists, dicts, and template-line scaffolding.
- `sample/target/TRIP62/LR/STDIO_24R03/config_lib.jsonc`: replaced legacy `sim_pullres_enable` / `sim_pullres_disable` with the new four-key form (std/io × enable/disable).

### Verified
- HOLD: full INDEX, all corners, 0 spice failures. Liberty `pin(Z)` matches orig structurally (direction:inout / function:Z / driver_type:bus_hold / three_state:"1" / internal_power power_tin 1D fall+rise).
- BUFZ_1 / INVZ_1 INDEX 0,9 + full INDEX:
  - 3 timing arcs all emitted with correct sense / type / template (combinational 2D, three_state_enable 2D, three_state_disable 1D).
  - timing matched 440 points; diff avg ≈ -0.09 ns (existing systematic offset, not specific to tri-state).
- BUFZ/INVZ all 14 cells: full INDEX run with 0 spice failures (compare run scheduled separately).

---

## [0.9.14a02] 2026-05-04

Alpha pre-release toward `1.0.0`. Adds the developer-facing internal_power specification document and a direction-split power compare utility.

### Added
- `docs/SPEC_internal_power.md`: developer-facing specification of charao `internal_power` handling: Liberty conventions, `meas_types` schema, mylogic entry rules for `power_tin`, sim path (`meas_energy=5`), CSV extraction (1D-aware), and verification guidelines. Linked from `README.md`.

### Changed
- `util_compare_lib_csv.py`: split `power.csv` compare by pin direction:
  - `=== power (output pin, active arc) ===`: rows with `related_pin != ""` (charao `power_tout` and IO `power_c2c` etc.).
  - `=== power (input pin, stable state) ===`: rows with `related_pin == ""` (charao `power_tin`).
  - Each section reports its own `matched groups` / `missing groups` / `matched points`.

### Verified
- AOI21_1 with `--keep_zero_new --cell gf180mcu_fd_sc_mcu7t5v0__aoi21_1` (INDEX 0/9):
  - timing: 12 matched / 8 missing (charao emits default block in addition to active arcs; orig has active arcs only).
  - power (output pin, active arc): **10 / 0 missing**.
  - power (input pin, stable state): **14 / 0 missing** (matches orig vendor exactly: A1x3 + A2x3 + Bx1 stable states x 2 directions).
- INV_1: power (input pin, stable state): 0 / 0 (no `power_tin` needed and orig has none).

---

## [0.9.14a01] 2026-05-04

This is an alpha pre-release toward `1.0.0`. Intermediate alphas (`0.9.14a01`, `0.9.14a02`, ...) are pushed on `feature/1.0.0` branch for diff visibility. Final release will be tagged `1.0.0` and merged to `main`.

### Added
- **Phase A2: `internal_power` separation by pin direction (power_tout / power_tin)**:
  - `meas_types` field becomes mandatory in MyExpectCell (`list[str]`, external input). `meas_type` is now internal-only (`init=False`, set per loop iteration in `runExpectation` via `set_meas_type()` setter).
  - Rename template `kind=power` to `kind=power_tout` (output pin, 2D: slope x load).
  - Add new template `kind=power_tin` (input pin, 1D: slope only, no output load).
  - Split `runSpicePowerMultiThread` into `runSpicePowerToutMultiThread` / `runSpicePowerTinMultiThread`.
  - Split `runSpicePowerSingle` and `genFileLogic_PowerTrial1x` into Tout / Tin variants.
  - `runSpicePowerTinSingle` uses `meas_energy=5` (new): autostop disabled, `energy_start`/`energy_end` `.MEASURE TRAN` skipped, `tsim_end` fixed to input transition window, `estart`/`eend` assigned directly from arguments (no SPICE measurement).
  - tb_template: add `meas_energy=5` branches.
  - `util_extract_lib_csv` extended for 1D tables (input pin internal_power CSV extraction).
  - `myExportLib.py`: emit `internal_power () { when:"..."; fall_power(...) rise_power(...) }` inside input pin blocks (related_pin omitted = Liberty default of input pin).
- **mylogic power_tin entries (2,030 total) auto-generated**:
  - comb_base: AND/OR/NAND/NOR 2/3/4-input + MUX2 (11 logics, 324 entries).
  - comb_complex: AOI21/22/211/221/222, OAI21/22/31/32/33/211/221/222, MUX4 (14 logics, 1,706 entries).
  - Generators: `tmp/insert_power_tin.py`, `tmp/insert_complex.py` (git-untracked, temporary).
- **ADDH/ADDF (ISS-00068, multi-output adders)**: 6 cells (addh_1/2/4 + addf_1/2/4) ported into `mylogic_comb_complex.py`, registered in `std_comb.jsonc`.
- **ANTENNA cell**: registered in `std_comb.jsonc`, `.model_gf180_TT.sp` includes `diode_typical` model.
- `debug_run.sh`: auto-activate venv at top (for claude-code invocation).

### Changed
- `myExportLib.py` / `myExportDoc.py`: replace `startswith("power")` with explicit enumeration (`power_tout`, `power_c`, `power_i`, `power_tin`) to avoid mixing input/output pin power.
- `std_comb.jsonc`: add `["power_tin","10x0","d000"]` template_kgn only to cells that need input pin internal_power (AND/OR/NAND/NOR, MUX, AOI/OAI families - 81 cells). Cells without input pin internal_power in orig vendor (INV/BUF/clkinv/clkbuf/DLY/TIE/ANTENNA/XOR/XNOR/ADDH/ADDF - 62 cells) are excluded.

### Fixed
- Bug: `mylogic_comb_complex.py` had 716 entries with `meas_types=["delay"]` only; corrected to `["delay","power_tout"]` (active arc was missing power_tout sim trigger except in AOI21).
- ADDH `ports_dict` key order must match SPICE subckt port order (`A B CO S`, not `A B S CO`); fixed to avoid `Pin Name missmatch` error.

### Removed
- ISS-00071 (filler/endcap/fillcap cells): closed as out-of-scope (not handled by STA/synthesis, charao does not target these).

### Verified
- INV / AND2_1 / AOI21_1: input pin internal_power `when` expressions match orig vendor exactly (AOI21_1 has 7 stable states: A1x3 + A2x3 + Bx1).
- comb_base 25 + comb_complex 14 cells (INDEX 0/9): SPICE failures 0, baseline regression OK.

### Known Issues
- Verilog output: `\`timescale` is inconsistent across modules (IEEE 1800-2017 violation; only addf_1 has it). Will be addressed in a later alpha.
- Full-grid compare against orig vendor (INDEX full grid) is not yet executed; planned before `1.0.0` final release.

---

## [0.9.14] 2026-04-26

### Added
- **複合セル mylogic 拡張（K4 既知 14 種別 + XOR3/XNOR3 計 16 セル、ISS-00064）**：1118 entries 実装。
  - AOI21/22/211/221/222、OAI21/22/211/221/222/31/32/33、MUX4、XOR3、XNOR3
  - 試走 0 failures、`tmg_when` same-group 省略（v2 形式）で 4 入力以上の AOI/OAI で timing matched 0→856 に大幅改善。
- `tmp/gen_logic_entries.py`：5 入力以上の複合ゲート entries 自動生成スクリプト（git 管理外、テンポラリ運用）。
  - truth table から active sensitization を抽出、`groups` フィールドで same-group 入力を `tmg_when` から省略。
- `sample/target/gf180/fd/mcuC7t20240817/std_comb.jsonc` に 14 セル直接登録（複合ゲートを `ports_dict` で orig SPICE subckt に mapping）。

### Changed
- **`mylogic_base.py` を 4 ファイルに分割**：
  - `mylogic_comb_base.py`（INV/BUF/AND/OR/NAND/NOR/XOR2/XNOR2/MUX2/XOR3/XNOR3 + lr_mux primitive）
  - `mylogic_comb_complex.py`（AOI/OAI/MUX4 系 14 種別）
  - `mylogic_seq.py`（DFF + lr_dff primitive）
  - `mylogic_io.py`（IO セル：P_VDD/P_VSS/P_ANA1/P_IP_*/P_IX_*）
- `charao.py`：4 module を merge する仕組みを追加（重複 logic 名は ERR、primitive は連結）。

### Removed
- `std_comb_debug.jsonc` 運用を廃止（プロトタイプ検証も本流 `std_comb.jsonc` に直接登録、`--cells_only` で対象を絞って試走）。
- `mylogic_base.py`（4 分割により役割完了）。

### Known Issues
- 複合ゲートの power matched は orig の全 state 展開慣習との差で完全 matched 不可 → ISS-00065（timing/internal_power 分離）で長期解決。
- 残対応：tristate（ISS-00066）/ clkbuf（ISS-00067）/ adders（ISS-00068）/ delay（ISS-00069）/ 順序（ISS-00070）/ filler（ISS-00071）。

## [0.9.13] 2026-04-17

### Fixed
- `.option rshunt=1e9` をコメントアウト。5V/1GΩ=5nA の人工電流が leakage を 330 倍過大にしていた。
- `.option gmin=1e-10` をコメントアウト。5V×0.1nS=0.5nA の人工電流が leakage に混入していた。
- `.option abstol=1e-11` をコメントアウト（ngspice デフォルト使用）。
- `.option autostop` を energy2/3/4 で無効化。leakage テストベンチで `.meas` が `out of interval` で失敗していた問題を解消。
- leakage テストベンチの `timestep_tmax` を `tsim_end*0.1` で上限キャップ。
- `charao_run.py:474` energy2 の `tsim_end` を `eend + 1ns` → `max(eend, estart + tslew_rel) + 1ns` に変更（2026-04-23）。組合せセル + 遅 slope で VREL midpoint が VOUT 完了 (`energy_end`) より後に来るケース（xor3_1 / inv_1 等で再現）の `prop_in_out` / `setup_in_rel` / `hold_rel_in` measure 失敗を解消。VREL 完了時刻 (`_t_rel1 ≈ estart + tslew_rel`) を sim 区間に包含。

### Changed
- pleak 計算式を全端子（VDD/VSS/VNW/VPW）対応に変更。
  `pleak = max(p_supply, p_absorb)`、`p_supply = i_vdd*(VDD-VSS) + i_vnw*(VNW-VPW)`。
  符号付き（abs 不使用）でエネルギー回生を表現可能。
- `i_vnw_leak`, `i_vpw_leak` の `.meas` を energy2/4 と leakage テストベンチに追加。

### Added
- `util_compare_lib_csv.py`: `--interpolate` 時の部分ラン検出ガード追加。
- `debug_run.sh`: `COMPARE_INTERPOLATE` 環境変数追加（0: off、1: on）。
- `debug_run.sh`: `grep -c` の `|| true` 修正（set -e 対策）。
- `myExpectCell.py`: `timing_default: bool = False` field 追加（2026-04-23）。Liberty default block 生成の on/off を verilog `ifnone` マーカー（`;;`）から独立制御。
- `myExportLib.py`: timing/power block 出力時、group 内に `timing_default=True` のエントリがあれば **when なし default block を自動生成**。STA/synthesis ツール互換性向上。
- `mylogic_base.py`: AND2/3/4, OR2/3/4, NAND2/3/4, NOR2/3/4 の delay entries 72 件に `tmg_when`（active sensitization）と `timing_default=True` を追加。orig との power arc match 向上（single-when missing 21,600 → 14,760、-32%）。

### Changed
- `mylogic_base.py` / `mylogic_user.py`: `specify=";;"` マーカーの再配置（Verilog LRM 準拠）。
  - **削除**（全 state 網羅セル、`ifnone` は redundant）：XOR2/XNOR2/MUX2/XOR3 の `;;` 15 件 → `;` へ戻す。
  - **追加**（補集合ありセル、`ifnone` で state cover）：AND/OR/NAND/NOR の fall entries 36 件に `;;` 付与。
  - 併せて全対象セルの最後のエントリに `timing_default=True` を付与（Liberty default block 生成）。

## [0.9.12] 2026-04-16

### Fixed
- internal_power 計算を min-rail 方式に変更（`min(|Q_vdd|, |Q_vss|) × Vdd`、libretto 互換）。
  従来の `|Q_vdd| × Vdd - Q_out × Vdd` は PMOS I²R 損失を含み STA switching と二重計上になっていた。
- `e_load` 計算を Liberty 仕様に修正（`× energy_meas_high_threshold_voltage` → `× vdd_voltage`）。
- テストベンチの load cap (`C0`) 接続先を `VSS_DYN` → 理想 GND (`0`) に変更。
  `I(VSS_DYN)` に cap 充放電電流が混入し `Q_vss` 測定が不正確だった問題を解消。
- `.option` から `reltol=1e-2` を削除（ngspice デフォルト `1e-3` を使用）。

### Added
- `util_compare_lib_csv.py` に `--interpolate` オプション追加。
  orig と charao で load グリッドが異なる場合に 2D bilinear 補間（線形外挿）で全点比較可能。
- `util_make_templates_from_new.py` 新規追加。
  Cin-fanout 方式で index_1/index_2 を生成し、orig .lib 不要で templates セクションを作成。

### Changed
- `util_make_templates.py` を `util_make_templates_from_origin.py` にリネーム。
- `debug_run.sh`: compare に `--interpolate` 追加。
  `MODE=local` で `python3 -m charao.script.charao` を使用（pip 版と分離）。

---

## [0.9.11] 2026-04-15

### Fixed
- energy2 を含む全セルで ngspice の `Timestep too small` 収束失敗を解消。
  `temp_testbench.sp.jp2` の `.option` に `gmin=1e-10 abstol=1e-11 rshunt=1e9 reltol=1e-2`
  を追加し、ill-conditioned matrix を広く救済。`rshunt=1e9` が決定打。
  2026-04-15 の gf180 91 セル × 2×2 コーナー検証で `Failed to launch spice` が 0 件。

### Changed
- `charao_run.py` の `.tran` タイムステップ算出ロジックを全面刷新：
  - `timestep_tstep = min(slope * 0.0099, simulation_timestep)`（従来の floor から ceiling へ）
  - `timestep_tmax = 20 * timestep_tstep`（delay / energy1 / setup / hold / passive）
  - `timestep_tmax = 4 * timestep_tstep`（energy2 のみ、`.tran` 終端着地対策）
  - 旧式の `slope/5` / `100×simulation_timestep` の min 制約は撤廃
  - 全 7 箇所（delay / power / setup_trial / setup / hold_trial / hold / passive）に適用
- `sample/target/gf180/fd/mcuC7t20240817/config_lib.jsonc`:
  - `simulation_timestep` を 1.0（ns、上限キャップとして機能）
  - `sim_segment_timestep_min` を 0.001（ns、setup/hold bisection 用、独立パラメータ）

---

## [0.9.10] 2026-04-15

### Fixed
- energy2 測定で最小 slew (slope=0.02 ns) 時に ngspice が `Timestep too small`
  （`vrel#branch` / `vhigh#branch` / `vlow#branch`）で abort する問題を修正。
  `charao/script/temp_testbench.sp.jp2` の `.option` 行に `gmin=1e-10 abstol=1e-11 rshunt=1e9`
  を追加することで、`.tran` 終端着地時の ill-conditioned matrix による数値発散を回避。
  `rshunt=1e9` が決定打。2026-04-14 の gf180 91セルフルランで発覚した spice エラー
  （energy2 系の `Failed to launch spice`）を解消。

### Changed
- `sample/target/gf180/fd/mcuC7t20240817/config_lib.jsonc`:
  `simulation_timestep` を 0.0001 → 0.0005、`sim_segment_timestep_min` を 0.001 → 0.0005
  に変更（最小 slew の約 1/40 目安）。実測で 0.0005 は全セル通過、それ未満への細分化は
  不要と判明。

---

## [0.9.9] 2026-04-14

### Fixed
- 入力 PWL ランプ時間の算出を orig `.lib` の `slew_derate_from_library` 規約に合わせて修正。
  `charao_run.py` でテンプレート `index_1` を「物理 threshold 区間（slew_lower→slew_upper）の時間」
  と解釈し、`index_1 / (logic_threshold_high - logic_threshold_low)` で全幅（0–100%）ランプ時間
  に換算するようにした。新ヘルパー `_tslew_from_template()` を 8 箇所に適用
  （組合せ delay/power、順序 setup/hold、three-state 系）。出力 transition は補正なしで
  そのまま書き出す（ルール：物理 threshold 区間の時間、derate 補正は書き出し時に入れない）。

### Added
- `slew_derate_from_library` フィールドを `MyLibrarySetting` に追加（デフォルト 1.0）。
  GF180 用 `config_lib.jsonc` には値 `0.5` を設定。`myExportLib.py` の `.lib` ヘッダ出力を
  ハードコード `1` から config 参照に変更。

### Changed
- `util_compare_lib_csv.py` の集計表示を ratio ベースから diff ベースに刷新
  （`diff avg / sigma / min / max`）。理由：ratio は orig 小値除算で暴れて本質を隠し、
  系統的オフセット（定数バイアス）を見落としやすい。per-point CSV から `ratio` 列を削除、
  `orig==0` のスキップも撤廃。
- サマリファイル出力を追加：`--out_csv <path.csv>` 指定時、同じ内容を `<path.summary.txt>`
  にも書き出す。対話での結果共有を容易にするため。

---

## [0.9.8] 2026-04-13

### Fixed
- Fix `.MEASURE TRAN` `TD={_t_rel0/_t_clk3}` by adding `-2*_timestep` offset: prevents
  `out of interval` failure of `energy_start` WHEN clause at slope=0.02ns, which previously
  blocked ngspice autostop and extended SIM runtime up to 3838s per run. Max SIM time now
  44s (about 87x faster) with zero MEASURE errors across full inv_1 run (600 .lis)
- Remove ngspice `.lis` unit ambiguity on compare: `util_extract_lib_csv.py` now parses
  `time/voltage/current/leakage/energy` units from .lib header and normalizes CSV output
  to canonical units (ns / pF / V / mA / uW / pJ). `energy_unit` is derived from
  `V × A × s` when not declared (standard Liberty behavior)

### Changed
- Rename CLI options `--only_template_index1` / `--only_template_index2` to
  `--template_index1_only` / `--template_index2_only` for consistency with `--cells_only`
  / `--measures_only`. Internal `MyLibrarySetting` field names also renamed
- `sample/target/gf180/fd/mcuC7t20240817/config_lib.jsonc`: switch `leakage_power_unit`
  from `pW` to `uW` and `energy_unit` from `fJ` to `pJ` to match original GF180 .lib
  convention (makes CSV values directly comparable without unit scaling)
- `util_extract_lib_csv.py`: CSV column names now carry parenthesized units
  (`index1 (ns)`, `index2 (pF)`, `value (ns)`, `value (pJ)`, `leakage_power (uW)`);
  single source of truth via `UNITS_IN_CSV` dict

### Added
- `charao/script/util_compare_lib_csv.py`: compare two CSV directories produced by
  `util_extract_lib_csv.py`. Uses numpy.interp for 2D bilinear interpolation to evaluate
  the new side on the original grid, and reports ratio/abs_diff statistics grouped
  by `table_type` (timing) and `rise_fall` (power). Optional `--out_csv` writes
  per-point comparison rows
- `charao/script/util_extract_sim_time.py`: scan `work/*.sp.lis` and extract SIM time,
  data rows, autostop status, and error count to `rslt/sim_time.csv`. Useful for
  SIM speed regression and bottleneck analysis

## [0.9.7] 2026-04-12
### Fixed
- Fix internal energy calculation for fall transition: remove conditional guard on e_load;
  use signed Cload energy (e_all - max(e_load, 0)) to correctly handle fall/rise asymmetry
- Remove `rm -rf` after tar in compressFiles: rm is blocked on remote server

### Added
- Add charao/script/util_extract_lib_csv.py: extract leakage/power/timing tables from Liberty .lib
  to CSV for reference comparison (supports single file and multi-corner directory modes)

## [0.9.6] 2026-04-11
### Added
- Add `--template_index1_only` / `--template_index2_only` options: limit simulation to specified index positions (0-based) for debug/fast-check use (renamed from `--only_template_index1/2` for consistency with `--cells_only` / `--measures_only`)

## [0.9.5] 2026-04-11
### Added
- Add GF180 support: sample/target/gf180/ with config_lib.jsonc and std_comb.jsonc (inv_1)
- Add `spiceinit` field to MyLibrarySetting: generates .spiceinit from config_lib.jsonc (e.g. `set ngbehavior=hsp`)
- Add `energy_unit` declaration to .lib header output (prevents EDA tools from misinterpreting fJ values as nJ)
- Add `i_vnw_leak` measurement to leakage SPICE template (temp_testbench.sp.jp2)

### Fixed
- Fix leakage power for I=1 state: include I(VNW_DYN)*VNW in pleak calculation (PMOS body-drain junction current was ignored, causing ~0 pW for I=1)
- Fix SyntaxWarning in myExportDoc.py: invalid escape sequence `\c` → `\\c` in `\clearpage`
- Fix GF180 model loading: use `.lib typical` instead of individual sections to include fets_mm subckt wrappers

## [0.9.4] 2026-03-27
### Added
- Add tests/test_e2e.py: E2E test for OSU035/INV_1X/leakage via lrPymRPC
- Add tests/conftest.py: E2E fixtures, lrPymRPC runner, .lib parser
- Add pytest.ini: --tb=short, --capture=tee-sys, lrpymrpc_verbose option
- Add tests/fixtures/std_comb_leakage_inv/expected.yaml: expected values for P2-0 scenario
- Add test_log/ output: test_e2e.log and per-scenario lrpymrpc.log
- Update tests/TEST_PLAN.md: reflect E2E infrastructure completion and SKY130 migration plan

## [0.9.3] 2026-03-26
### Added
- Add pytest to dev dependencies in pyproject.toml
- Add tests/test_myFunc.py: unit tests for f2s_ceil()
- Add tests/test_myLibrarySetting.py: unit tests for update_mag() / update_threshold_voltage()
- Add tests/TEST_PLAN.md: test plan including E2E strategy via lrPymRPC

## [0.9.2] 2026-03-26
### Fixed
- Fix bare `except:` to `except subprocess.CalledProcessError` with `my_exit()` in myLibrarySetting.py
- Fix typo `lunch` → `launch` in myLibrarySetting.py
- Add `my_exit()` to `except` clause in charao.py for proper error termination

## [0.9.1] 2026-03-26
### Fixed
- Fix typo in myLibrarySetting.py: `supress_debug_msglower()` → `supress_debug_msg.lower()` (ISS-00001)
- Remove undefined variable `nval` from error messages in myConditionsAndResults.py (ISS-00002)
- Change `[DEBUG]` to `[INFO]` in charao_run.py for stable operation monitoring (ISS-00003)
- Fix duplicate condition `self.cell == None` → `self.logic == None` in myLogicCell.py (ISS-00004)
- Replace `split('/')` with `pathlib.Path(...).name` in myFunc.py for Windows compatibility (ISS-00005)
- Remove dead comment code `#debug` / `#print(targetLib.templates)` in charao.py (ISS-00006)

## [0.9.0] 2026-01-24
### Changed
- Support --mylogic_user option for user-defined logic_dict().

## [0.8.5] 2026-01-10
### Changed
- Change default result directory to ./rslt.

## [0.8.4] 2025-12-18
### Changed
- Debug .lib output for TIE0/TIE1 cell.

## [0.8.3] 2025-12-11
### Changed
- Support TIE0/TIE1 cell(leakage).

## [0.8.2] 2025-12-04
### Changed
- Support ANTENNA cell(passive/leakage).

## [0.8.1] 2025-11-15
### Changed
- Support -w option to change work directory.

## [0.8.0] 2025-11-15
### Changed
- Change PATH to jsonc(target/[fab_process]/[cell_vendor]/[cell_revision]).
- Support Multi JSONC file for same [cell_group].
- Change JSONC format (Set spice_path in each [cell_group].jsonc).

## [0.7.6] 2025-11-13
### Changed
- Add build-stamp by -b option to output files(.lib, .md, .v).

## [0.7.5] 2025-11-13
### Changed
- Add revision in Verilog output.

## [0.7.4] 2025-11-11
### Changed
- Fix specify/libery CONDITION for MUX2.

## [0.7.3] 2025-11-06
### Changed
- Fix specify (recovery) and timescale in Verilog output.

## [0.7.2] 2025-10-24
### Changed
- DFFのverilog出力内容の訂正。

## [0.7.1] 2025-10-24
### Changed
- charao/target/OSU035/.model_OSU035_xx.spにて、spiceモデルのincludeパスを 実行場所(work)からの相対パスへ変更。

### Changed
- プロジェクト名を`charao_prj`へ変更
- モジュール化対応

## [0.6] 2025-09-01
### Changed
- ツール名を`charao`へ変更

## [0.5] 2025-xx-xx
### Added
- 複数のtemplateに対応
- パラメータ設定ファイルとして、`jsonc`を採用
- テストベンチの雛形生成に、`jinja2`を採用

## [0.2] 2025-xx-xx
### Added
- 複数の slope / load に対応

## [0.1] 2025-06-23
### Added
- `OriginalProject` (https://github.com/snishizawa/libretto) からフォーク
- SPICEモデルのパスを絶対パスに対応
