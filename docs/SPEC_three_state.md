# Three-state cell support specification

このドキュメントは charao における三相態（tri-state）/バスキーパーセルのキャラクタライズ規約と、
新規 PDK／プロセスへ移植する際の手順をまとめたものです。GF180 PDK の `hold` / `bufz_*` / `invz_*`
を実装した経緯（v0.9.14a03）に基づきます。

---

## 1. 対象セルの種類

| 種別 | 例（GF180） | Liberty 上の特徴 |
|---|---|---|
| バスキーパー（biport） | `hold` | `pin(Z) direction:inout`, `three_state:"1"`, `driver_type:bus_hold` |
| Tri-state buffer/inverter | `bufz_*`, `invz_*` | `pin(Z) direction:output`, `three_state:"(!EN)"` + 3 種の timing arc |

両者とも internal driver が disable 状態で出力を Hi-Z にする点は共通だが、Liberty の `pin` direction が
異なるため、 charao の MyExpectCell の `pin_oir` の扱い（biport: `b0` / output: `o0`）と Liberty 出力経路
（`myExportLib` の biport ループ / outport ループ）が分かれる。

---

## 2. Liberty 出力構造

### 2.1 biport 系（HOLD）

```
pin (Z) {
  direction          : "inout";
  function           : "Z";
  driver_type        : bus_hold;
  three_state        : "1";
  internal_power () {
    fall_power(power_tin_energy_template_10x0) { values("...") }
    rise_power(power_tin_energy_template_10x0) { values("...") }
  }
}
leakage_power () { when:"!Z"; value: ... }
leakage_power () { when:"Z";  value: ... }
```

### 2.2 output 系（BUFZ / INVZ）

```
pin (Z) {            // INVZ は ZN
  direction          : "output";
  function           : "I";   // INVZ は "!I"
  three_state        : "(!EN)";
  timing () {        // active arc
    related_pin      : "I";
    when             : "EN";
    timing_sense     : "positive_unate";   // INVZ は "negative_unate"
    timing_type      : "combinational";
    cell_fall/cell_rise/fall_transition/rise_transition (delay_template_10x10)
  }
  timing () {        // disable arc (output load 非依存 → 1D template)
    related_pin      : "EN";
    timing_sense     : "negative_unate";
    timing_type      : "three_state_disable";
    cell_fall/cell_rise/... (delay_disable_template_10x0)
  }
  timing () {        // enable arc (output load 依存 → 2D template)
    related_pin      : "EN";
    timing_sense     : "positive_unate";
    timing_type      : "three_state_enable";
    cell_fall/cell_rise/... (delay_template_10x10)
  }
}
leakage_power() x4 (when: !EN&!I, !EN&I, EN&!I, EN&I)
```

---

## 3. mylogic_*.py logic_dict の規約

### 3.1 共通フィールド

| キー | 用途 |
|---|---|
| `logic_type` | `"comb"`（HOLD/BUFZ/INVZ）or `"io"` |
| `functions` | `{"o0":"i0"}` 等。 Liberty の function 出力に使われる |
| `vcode` | `.v` 出力用 Verilog primitive（`bufif1` / `notif1` / `buf (weak0,weak1)` 等） |
| `three_state` | Liberty の `three_state` 属性値（条件式リテラル、 portmap 後の port 名） |
| `driver_type` | バスキーパー用に `"bus_hold"` 等（任意） |
| `expect` | `MyExpectCell` のリスト |

### 3.2 cell 個別の SPICE 内部信号 → cell info（jsonc）側

`oe_infos` は **cell ごとに subckt の内部 net 名が変わる**ため、 mylogic ではなく
`std_comb.jsonc` などの cell entry（`info` dict）に書く：

```jsonc
{"cell":"gf180mcu_fd_sc_mcu7t5v0__bufz_1", "logic":"BUFZ", ...,
 "oe_infos":{"o0":{"drv0":{"type":"nmos","gate":"NI_N"},
                   "drv1":{"type":"pmos","gate":"NI_P"}}}}
```

- `drv0`：output Z を low 側に駆動する **NMOS pulldown** の **gate 信号**
- `drv1`：output Z を high 側に駆動する **PMOS pullup** の **gate 信号**

OE 切断時、これらの gate がそれぞれ vss/vdd レベルに固定されることで、 charao tb 内の
SW 素子（`SW_NMOS`/`SW_PMOS`）が pullres を切り離す挙動を再現する。

`info` dict は `Mlc(mls=targetLib, **info)` で Pydantic field に自動マッピングされるため、
コード変更は不要。

---

## 4. MyExpectCell 設計パターン

### 4.1 biport 系（HOLD）

```python
# power_tin: biport 駆動 (Z = b0)
MyExpectCell(pin_oir=["b0","b0","b0"], ival={"o":[],"i":[],"b":["0"]}, mondrv_oir=["1","1","1"]
            ,meas_types=["power_tin"], tmg_sense="non", arc_oir=["r","r","r"], tmg_when="", specify=""),
MyExpectCell(pin_oir=["b0","b0","b0"], ival={"o":[],"i":[],"b":["1"]}, mondrv_oir=["0","0","0"]
            ,meas_types=["power_tin"], tmg_sense="non", arc_oir=["f","f","f"], tmg_when="", specify=""),
# leakage: when:"!b0" / "b0"
```

### 4.2 output 系の active arc（delay + power_tout）

通常の組合せセルと同じ。 `tmg_when` で control pin の active 値を指定（BUFZ: `"i1"`、 INVZ: `"i1"`）。

### 4.3 three_state_enable arc（output 系）

| 観点 | 設定 |
|---|---|
| pin_oir | `["o0","i0","i1"]`（output / data / control） |
| arc_oir | `[output_dir, "s", "r"]`（control rise） |
| tmg_sense | `"pos"`（positive_unate） |
| tmg_when | `""`（fall/rise pair で 1 group） |
| ival.o | initial 値 = 反対極性（ext drive を 0 or 1 と仮定） |
| mondrv_oir | 終状態 = active 値 |

**fall/rise pair は same when 内で 2 entries 必要**（when 別に分けると group が分裂し
`len(group)!=2` エラーが出る）。

### 4.4 three_state_disable arc（output 系）

| 観点 | 設定 |
|---|---|
| pin_oir | `["o0","i0","i1"]` |
| arc_oir | `[output_dir, "s", "f"]`（control fall） |
| tmg_sense | `"neg"`（negative_unate） |
| tmg_when | `""` |
| 必須条件 | cell entry に `oe_infos` が無いと `[ERROR] no oe_infos exist for o0` |

### 4.5 leakage（4 conditions for output 系）

```python
# !EN&!I / EN&!I / !EN&I / EN&I (BUFZ では Z は EN&I で 1, !EN系 は Hi-Z=d, etc.)
```

---

## 5. charao 内部実装フロー

### 5.1 dispatch

| ファイル | 機能 |
|---|---|
| `charao_run.py:110` | `mt.startswith("three_state_")` で `runSpiceDelayMultiThread` 呼び出し |
| `charao_run.py:160` | `replace("three_state_disable","delay_disable")`（1D template kind） |
| `myConditionsAndResults.py:202,218-221` | `startswith("three_state_")` で measure_type / timing_type 振り分け |

### 5.2 tb 生成

| ファイル | 機能 |
|---|---|
| `charao_run.py:401-422` | `pullres_role` / `pullres_gate` を timing_type で切替 |
| `myTbParam.py:115-118` | `sim_pullres_*` から cell 種別（std/io）で選択 |
| `temp_testbench.sp.jp2:323-347` | `pullres_role` に応じて R / SW 素子を生成 |

### 5.3 sim_pullres の値（PDK 依存パラメータ）

| キー | デフォルト | 用途 |
|---|---|---|
| `sim_pullres_std_enable`  | 100000 (100kΩ) | std セル（数kΩ driver）が override できる弱 pull |
| `sim_pullres_std_disable` | 0.1 | std cell disable で強制駆動 |
| `sim_pullres_io_enable`   | 100 (100Ω) | IO セル（強 driver）用 |
| `sim_pullres_io_disable`  | 1 | IO cell disable で強制駆動 |

PDK の driver サイズに応じて `config_lib.jsonc` で override する。

---

## 6. delay_disable 1D template

three_state_disable arc は output load 非依存のため、**1D（slope のみ）テーブル**で出力する。
charao では `delay_disable` という独立した template kind として実装：

| ファイル | 変更箇所 |
|---|---|
| `myItem.py` | `Literal["...", "delay_disable", ...]` |
| `myLogicCell.py` | `template` dict に `"delay_disable": None` |
| `myLibrarySetting.py` | `template_lines` / `var_1_dict` / `var_2_dict` に `delay_disable` 追加、 `lu_table_template` 判定にも |
| `myConditionsAndResults.py` | `set_lut` の許可リストに `delay_disable` |
| `charao_run.py` | `replace("three_state_disable","delay_disable")`、 `index2_loads=[0.0]` fallback |
| `myExportDoc.py` | 1D 表示で `index_2` 空のフォールバック |
| `config_lib.jsonc` | `{"kind":"delay_disable","grid":"10x0","name":"d00","index_1":[...]}` |
| `std_comb.jsonc` | `template_kgn` に `["delay_disable","10x0","d00"]` |

---

## 7. 別プロセス（PDK）への応用手順

### Step 1: orig Liberty 構造の確認

対象セルが「biport 系」「tri-state output 系」のどちらか。

- biport: `pin(...) direction:inout` + `driver_type` あれば bus keeper
- tri-state output: `pin(...) direction:output` + `three_state:"(...)"` + `timing_type:three_state_*`

3 種の timing arc / leakage 条件 / internal_power の `related_pin` と `when` を一覧化する。

### Step 2: SPICE subckt の出力 driver 解析

```bash
awk '/.SUBCKT <cell_name> /,/.ENDS/' <pdk>.spice
```

出力 pin Z（または ZN）に直接接続される NMOS/PMOS を探し、 その gate signal 名を取得：

- NMOS pulldown の gate → `oe_infos["o0"]["drv0"]["gate"]`
- PMOS pullup の gate → `oe_infos["o0"]["drv1"]["gate"]`

GF180 では BUFZ/INVZ 全サイズで `NI_N` / `NI_P` 共通だったが、 **PDK によってネット名が異なる**ため、
セル毎に確認する。

### Step 3: mylogic_comb_tristate.py に logic 追加

`HOLD` / `BUFZ` / `INVZ` を参考に、 active arc / enable arc / disable arc / leakage の MyExpectCell を定義。
section 4 の規約を踏襲。

### Step 4: cell entry（jsonc）の作成

`std_comb.jsonc`（または対応する jsonc）に各サイズの cell entry を追加：

- `template_kgn`: 既存 driver サイズの d0XX を流用、 disable arc 用に `["delay_disable","10x0","d00"]` 追加
- `ports_dict`: SPICE port 順序と一致
- `oe_infos`: Step 2 で取得した gate 名

### Step 5: sim_pullres の値調整（必要に応じて）

PDK の std セル driver の on-resistance を見て、 `sim_pullres_std_enable` を override：

- driver Ron が ~kΩ なら enable=100kΩ で十分
- driver Ron がより大きい場合は 1MΩ 等へ調整

### Step 6: 動作確認

```bash
CELLS="<cell_name>" INDEX1="0 9" INDEX2="0 9" MODE=local bash debug_run.sh clean run_all
```

- `failed-spice grep: 0 failures` を確認
- `.lis` で `.meas` errors（`out of interval` 等）が出ていないことを確認
- `.lib` の output 構造が orig と一致しているか目視確認

### Step 7: フル INDEX + orig 比較

```bash
CELLS="<cell_name>" MODE=local bash debug_run.sh clean run_all lib2csv_charao compare
```

`tmp/compare_*.summary.txt` で `matched points` / `diff avg` を確認。

---

## 8. 既知の制限事項

- BUFZ/INVZ の **input pin internal_power**（`pin(EN) when:"!I"/"I"`、 `pin(I) when:"!EN"`）は v0.9.14a03 時点で未実装
- BUFZ/INVZ の **output pin internal_power related:EN（no when）** も未実装
  → enable/disable arc に紐づく active power、 別 issue で対応予定
- 1D template (`delay_disable`) の simulation は load 1 corner で十分だが、 現状は load=0.0 で 1 回だけ sim する fallback で済ませている（最適化済み）

---

## 9. 参照

- 関連 issue: ISS-00066（BUFZ/INVZ tri-state）、 ISS-00069（HOLD bus keeper）
- 関連 spec: `docs/SPEC_internal_power.md`
- 実装ファイル: `charao/script/mylogic_comb_tristate.py` / `sample/target/gf180/fd/mcuC7t20240817/std_comb.jsonc`
