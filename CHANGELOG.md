# CHANGELOG

このファイルは UTF-8 で記述されています。

---

## [0.9.7] 2026-04-12
### Fixed
- Fix internal energy calculation for fall transition: remove conditional guard on e_load;
  use signed Cload energy (e_all - max(e_load, 0)) to correctly handle fall/rise asymmetry
- Remove `rm -rf` after tar in compressFiles: rm is blocked on remote server

### Added
- Add charao/script/extract_lib_csv.py: extract leakage/power/timing tables from Liberty .lib
  to CSV for reference comparison (supports single file and multi-corner directory modes)

## [0.9.6] 2026-04-11
### Added
- Add `--only_template_index1` / `--only_template_index2` options: limit simulation to specified index positions (0-based) for debug/fast-check use

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
