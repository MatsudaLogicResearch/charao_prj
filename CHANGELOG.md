# CHANGELOG

このファイルは UTF-8 で記述されています。

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
