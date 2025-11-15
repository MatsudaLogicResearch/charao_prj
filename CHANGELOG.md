# CHANGELOG

このファイルは UTF-8 で記述されています。

---

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
