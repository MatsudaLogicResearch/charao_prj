# charao テスト計画

## テスト方針

| フェーズ | 条件 | 内容 |
|---------|------|------|
| **フェーズ1（完了）** | ngspice不要 | 計算・変換関数のユニットテスト |
| **フェーズ2（進行中）** | lrPymRPC経由でngspice実行可能 | OSU035（std既存セル）で回帰テスト構築 |
| **フェーズ2b** | 不足SPICE入手後 | OSU035（BUF/TIE/ANTENNA/DFFB）シナリオ追加 |
| **フェーズ3** | TRIP62導入後 | IOセル全meas_typeを網羅 |

---

## logic_type 一覧

| logic | logic_type | meas_type | OSU035セル | SPICE状況 |
|-------|-----------|-----------|-----------|---------|
| ANTENNA | comb | leakage, passive | なし | 要入手（フェーズ2b） |
| TIE1 | comb | leakage | なし | 要入手（フェーズ2b） |
| TIE0 | comb | leakage | なし | 要入手（フェーズ2b） |
| BUF | comb | leakage, delay | なし（BUFX1相当） | 要入手（フェーズ2b） |
| DEL | comb | leakage, delay | なし | 要入手（フェーズ2b） |
| INV | comb | leakage, delay | INV_1X ✓ | あり |
| AND2/3/4 | comb | leakage, delay, power | AND2/3/4_1X ✓ | あり |
| OR2/3/4 | comb | leakage, delay, power | OR2/3/4_1X ✓ | あり |
| NAND2/3/4 | comb | leakage, delay, power | NAND2/3/4_1X ✓ | あり |
| NOR2/3/4 | comb | leakage, delay, power | NOR2/3/4_1X ✓ | あり |
| XOR2 | comb | leakage, delay, power | XOR2_1X ✓ | あり |
| XNOR2 | comb | leakage, delay, power | XNOR2_1X ✓ | あり |
| MUX2 | comb | leakage, delay, power | SEL2_1X ✓（jsonc未登録） | jsonc追加で対応可 |
| DFF_PC_NR_NS | seq | leakage, rising_edge, clear, preset, setup_rising, hold_rising, recovery_rising, removal_rising, passive, min_pulse_width_high/low | DFFARAS_1X ✓ | あり |
| DFFB_PC_PR | seq | leakage, rising_edge, clear, preset, setup_rising, hold_rising, recovery_rising, removal_rising, passive, min_pulse_width_high | なし（Q+QB出力） | 要入手（フェーズ2b） |
| DFFB_PC_NS | seq | leakage, rising_edge, preset, setup_rising, hold_rising, recovery_rising, removal_rising, passive, min_pulse_width_high | なし（Q+QB出力） | 要入手（フェーズ2b） |
| P_VDD | io | なし | なし | TRIP62（フェーズ3） |
| P_VSS | io | なし | なし | TRIP62（フェーズ3） |
| P_ANA1 | io | leakage | なし | TRIP62（フェーズ3） |
| P_IP_SMTX_... | io | leakage, delay_i2c, delay_c2c | なし | TRIP62（フェーズ3） |
| P_IP_SMTA_... | io | leakage, delay_i2c, delay_c2c | なし | TRIP62（フェーズ3） |
| P_IX_SMTX_... | io | leakage, delay_c2i, three_state_enable/disable_c2i | なし | TRIP62（フェーズ3） |

---

## meas_type 網羅状況

| meas_type | ngspice解析 | フェーズ2 | フェーズ2b | フェーズ3 |
|-----------|-----------|---------|---------|---------|
| leakage | DC解析 | ✓ | ✓ | ✓ |
| delay | 過渡解析（伝搬遅延） | ✓ | ✓ | - |
| power | 過渡解析（スイッチング電力） | ✓ | - | - |
| passive | 過渡解析（静的電力） | ✓ | ✓ | - |
| rising_edge | 過渡解析（CLK→Q） | ✓ | ✓ | - |
| clear | 過渡解析（非同期Reset→Q） | ✓ | ✓ | - |
| preset | 過渡解析（非同期Set→Q） | ✓ | ✓ | - |
| setup_rising | 二分探索 | ✓ | ✓ | - |
| hold_rising | 二分探索 | ✓ | ✓ | - |
| recovery_rising | 二分探索 | ✓ | ✓ | - |
| removal_rising | 二分探索 | ✓ | ✓ | - |
| min_pulse_width_high | 二分探索 | ✓ | ✓ | - |
| min_pulse_width_low | 二分探索 | ✓ | ✓ | - |
| delay_c2c | 過渡解析（IOセル内部） | - | - | ✓ |
| delay_c2i | 過渡解析（CORE→PAD） | - | - | ✓ |
| delay_i2c | 過渡解析（PAD→CORE） | - | - | ✓ |
| three_state_enable_c2i | 過渡解析（トライステート有効） | - | - | ✓ |
| three_state_disable_c2i | 過渡解析（トライステート無効） | - | - | ✓ |

---

## テスト実行環境

### フェーズ1（ユニットテスト）
| 項目 | 内容 |
|------|------|
| **OS** | Windows 11 |
| **Python** | 3.10以上 |
| **テストFW** | pytest |
| **仮想環境** | `$HOME/.venv_charao` |
| **インストール** | `pip install -e ".[dev]"` |
| **実行コマンド** | `pytest -v` |

### フェーズ2・2b・3（E2Eテスト）
| 項目 | 内容 |
|------|------|
| **実行方式** | lrPymRPC（gRPC）経由でリモートLinuxサーバー上でcharaoを実行 |
| **ngspice** | リモートLinuxサーバー上で実行（Windowsへの導入不要） |
| **基準ファイル** | `tests/fixtures/<シナリオ名>/expected.yaml` に保存 |
| **検証内容** | `.lib` 内の数値を期待値と tolerance 照合 |
| **lrPymRPC インストール** | `pip install git+https://github.com/MatsudaLogicResearch/lrPymRPC_prj.git` |
| **実行コマンド** | `python -m pytest tests/test_e2e.py -v`（プロジェクトルートから） |
| **pytest.ini** | `--tb=short --capture=tee-sys`、`lrpymrpc_verbose = false` |
| **ログ出力** | `test_log/test_e2e.log`（テスト結果）、`test_log/<シナリオ名>/lrpymrpc.log`（lrPymRPC実行ログ） |

---

## テスト項目一覧

### フェーズ1：ユニットテスト（完了）

#### ① myFunc.py
**テストファイル：** `tests/test_myFunc.py` ✓

| # | テスト項目 | 状況 |
|---|-----------|------|
| 1 | `f2s_ceil()` 正の小数・有効桁数 | 完了 |
| 2 | `f2s_ceil()` 負の小数 | 完了 |
| 3 | `f2s_ceil()` ゼロ | 完了 |
| 4 | `f2s_ceil()` 大きい数（指数表記なし） | 完了 |
| 5 | `f2s_ceil()` 有効桁数1/2/3桁 | 完了 |

#### ② myLibrarySetting.py
**テストファイル：** `tests/test_myLibrarySetting.py` ✓

| # | テスト項目 | 状況 |
|---|-----------|------|
| 1 | `update_mag()` 各単位のスケール係数 | 完了 |
| 2 | `update_mag()` 大文字小文字を区別しない | 完了 |
| 3 | `update_threshold_voltage()` HIGH/LOW閾値電圧 | 完了 |
| 4 | `update_threshold_voltage()` LOW→HIGH閾値電圧 | 完了 |

---

### フェーズ2：E2Eテスト（OSU035 既存セル）

**テストファイル：** `tests/test_e2e.py` ✓（実装済み）
**設定ファイル：** `pytest.ini`（プロジェクトルート）
**期待値：** `tests/fixtures/<シナリオ名>/expected.yaml`

**E2E実行コマンド共通フォーマット（PowerShell）：**
```powershell
python -m lrPymRPC `
    --SERVER_IP 192.168.168.103 `
    --REPO_URL charao=git+https://github.com/MatsudaLogicResearch/charao_prj.git@<TAG> `
    --SOURCE sample `
    --RESULT rslt `
    --CMD "python3 -m charao -f OSU035 -v VENDOR -g std -u 5P00 -p TT -t 25.0 --vdd 5.0 --target sample/target <--cells_only ...> <--measures_only ...>"
```

| # | シナリオ | `--cells_only` | `--measures_only` | 網羅logic/meas_type | 推定時間 | 状況 |
|---|---------|---------------|------------------|-------------------|---------|------|
| P2-0 | `std_comb_leakage_inv` | INV_1X | leakage | leakage(INV) | ~14秒 | **完了（2026-03-27）** |
| P2-1 | `std_comb_leakage` | 全15 combセル | leakage | leakage(comb全logic) | ~5分 | 未着手 |
| P2-2 | `std_comb_delay` | NAND2_1X | delay | delay(combo) | ~5分 | 未着手 |
| P2-3 | `std_comb_power` | NAND2_1X | power | power(combo) | ~3分 | 未着手 |
| P2-4 | `std_seq_delay` | DFFARAS_1X | delay | rising_edge | ~5分 | 未着手 |
| P2-5 | `std_seq_const` | DFFARAS_1X | const | setup/hold/recovery/removal/clear/preset/min_pulse | ~10分 | 未着手 |
| P2-6 | `std_seq_passive` | DFFARAS_1X | passive | passive(seq) | ~3分 | 未着手 |
| P2-7 | `std_seq_leakage` | DFFARAS_1X | leakage | leakage(seq) | ~1分 | 未着手 |

**合計 ≈ 32分**

**ファイル出力確認（各シナリオ共通）：**

| ファイル | 検証内容 |
|---------|---------|
| `.lib` | Liberty構文正常、数値が expected.yaml と tolerance 内で一致 |
| `.v` | Verilogファイルが生成されている |
| `.md` | Markdownファイルが生成されている |

**期待値 YAML フォーマット：**
```yaml
# tests/fixtures/std_comb_leakage/expected.yaml
scenario:
  cells: [INV_1X, AND2_1X, AND3_1X, AND4_1X, OR2_1X, OR3_1X, OR4_1X,
          NAND2_1X, NAND3_1X, NAND4_1X, NOR2_1X, NOR3_1X, NOR4_1X,
          XOR2_1X, XNOR2_1X]
  group: std
  measures: leakage

expected:
  INV_1X:
    leakage_power: null   # 初回実行後に記入
    tolerance: 0.01       # ±1%
  NAND2_1X:
    leakage_power: null
    tolerance: 0.01
  # ... 全セル分
```

---

### フェーズ2b：E2Eテスト（OSU035 不足セル追加後）

**前提：** 下記SPICEファイルを `sample/src/OSU035/std/NORMAL/V00.00/spice/` に追加し、jsonc登録済み

| # | シナリオ | 対象logic | 必要SPICE | 入手先候補 |
|---|---------|---------|---------|---------|
| P2b-1 | `std_comb_buf` | BUF, DEL | BUFX1.spi | OSU035フルライブラリ or SKY130合成 |
| P2b-2 | `std_comb_tie` | TIE0, TIE1 | TIE0.spi, TIE1.spi | OSU035フルライブラリ or 合成SPICE |
| P2b-3 | `std_comb_antenna` | ANTENNA | ANTENNA.spi | OSU035フルライブラリ or 合成SPICE |
| P2b-4 | `std_comb_mux` | MUX2 | SEL2_1X.spi（既存） | jsonc登録のみで対応可 |
| P2b-5 | `std_seq_dffb_pr` | DFFB_PC_PR | DFFB_PR_1X.spi | OSU035フルライブラリ or 合成SPICE |
| P2b-6 | `std_seq_dffb_ns` | DFFB_PC_NS | DFFB_NS_1X.spi | OSU035フルライブラリ or 合成SPICE |

---

### フェーズ3：E2Eテスト（TRIP62 IOセル）

**前提：** TRIP62ライブラリ導入済み・io_*.jsonc設定済み

| # | シナリオ | 対象logic | 網羅meas_type | 状況 |
|---|---------|---------|-------------|------|
| P3-1 | `io_leakage` | P_ANA1, P_IP_*, P_IX_* | leakage(io) | 未着手 |
| P3-2 | `io_delay_i2c` | P_IP_SMTX_... | delay_i2c | 未着手 |
| P3-3 | `io_delay_c2c` | P_IP_SMTX_... | delay_c2c | 未着手 |
| P3-4 | `io_delay_c2i` | P_IX_SMTX_... | delay_c2i | 未着手 |
| P3-5 | `io_tristate` | P_IX_SMTX_... | three_state_enable/disable_c2i | 未着手 |

---

## 今後の優先順位

1. **【フェーズ2】** ~~`test_e2e.py` / `conftest.py` 実装~~ 完了（P2-0: std_comb_leakage_inv）
2. **【フェーズ2】** P2-1〜P2-7 シナリオ追加（NAND2/DFFARAS等）→ expected.yaml 保存
3. **【サンプルライブラリ検討】** OSU035の不足セル（BUF/TIE/ANTENNA/DFFB）対応として、サンプルライブラリをSKY130に切り替えることを検討する。SKY130はすべてのlogic_typeのSPICEが揃っており、フェーズ2b全シナリオを網羅できる可能性がある（`sample/target/SKY130/` を別途作成する方針）
4. **【フェーズ2b】** 不足SPICEの入手・合成 → jsonc登録 → シナリオ追加（OSU035継続の場合）
5. **【フェーズ3】** TRIP62 IOセル対応

---

## 注意事項

- `--cells_only INV_1X` で特定セルのみ実行（高速・軽量）
- `--measures_only leakage` で特定測定のみ実行
- `rm not found` はサーバーの意図的なセキュリティ制限で正常動作
- サーバー許可コマンド：`python, python3, sh, nice, cat, mkdir, ngspice, mv, tar, gzip`
