# charao Internal Power Specification

This document describes how charao characterizes and emits Liberty `internal_power`
in line with the Liberty specification's separation by pin direction.

Introduced in `0.9.14a01` (Phase A2, toward `1.0.0`).

---

## 1. Liberty `internal_power` by pin direction

In a Liberty file, an `internal_power () { ... }` block can appear inside both
input pin and output pin blocks. The semantics differ:

| pin direction | template (Liberty) | dimension | content |
|---------------|--------------------|-----------|---------|
| **output pin** | `power_tout_energy_template_10x10` | 2D (input slope x output load) | active arc (output toggles when an input toggles); `related_pin` specifies the trigger input |
| **input pin** | `power_tin_energy_template_10x0` | 1D (input slope only, **no output load**) | state-dependent power (input toggles, output stays at a fixed value); `related_pin` is omitted (Liberty default = the same input pin) |

> **power_tout の帰属（ISS-00154）**：charao の `power_tout` は遷移エネルギーを**計測 arc（出力ピン）に総量計上**する。一方 orig(vendor) は同エネルギーを寄与ピン（pin(CLK)＋pin(Q) 等）へ**分解**して計上する流儀差がある。**ライブラリ総和は等価**（orig の per-pin 値を合算すると charao 総量とオーダー一致）だが、per-pin 突合やクロックツリー電力の分離抽出では値の置き場所が構造的に異なる。1.0.0 は総量計上のまま（post-1.0.0 検討事案）。

### Example: AOI21 (`o = !((A1 & A2) | B)`)

Inside `cell(aoi21_X)`:

```liberty
pin (A1) {
  direction : input ;
  internal_power () {              # input pin power: A1 toggles, output stays
    when : "!A2 !B" ;              # state where output stays at 1
    fall_power(power_tin_energy_template_10x0) { ... } # value for A1 fall
    rise_power(power_tin_energy_template_10x0) { ... } # value for A1 rise
  }
  internal_power () { when : "!A2 B" ; ... }
  internal_power () { when : "A2 B" ;  ... }
}
pin (A2) { /* 3 input-pin internal_power entries (similar to A1) */ }
pin (B)  { /* 1 input-pin internal_power entry  (when : "A1 A2") */ }
pin (Z)  {
  direction : output ;
  internal_power () {              # output pin power: A1 toggles, Z toggles
    related_pin : "A1" ;
    when : "A2 !B" ;
    fall_power(power_tout_energy_template_10x10) { ... }
    rise_power(power_tout_energy_template_10x10) { ... }
  }
  /* 4 more output-pin internal_power entries for A1/A2/B active arcs */
}
```

`fall_power`/`rise_power` semantics:
- **output pin entries**: reflect the **output's** transition direction (LRM-standard).
- **input pin entries**: reflect the **input's** transition direction (vendor convention; output is stable so output direction is undefined).

---

## 2. charao schema (`meas_types` / template `kind`)

### `meas_types` (mandatory list field of `MyExpectCell`)

| `meas_types` value | location in Liberty output | sim function | template `kind` |
|--------------------|---------------------------|--------------|-----------------|
| `["delay", ...]` | output pin `timing()` | `runSpiceDelayMultiThread` | `delay` (2D) |
| `["power_tout", ...]` | output pin `internal_power()` | `runSpicePowerToutMultiThread` | `power_tout` (2D) |
| `["power_tin"]` | input pin `internal_power()` | `runSpicePowerTinMultiThread` | `power_tin` (1D) |
| `["leakage"]` | cell-level `leakage_power()` | `runSpiceLeakageMultiThread` | `leakage` (0D) |

A single `MyExpectCell` may declare multiple meas_types in one entry, e.g.
`meas_types=["delay", "power_tout"]` so that one stimulus is reused for both
delay and output-pin power simulation.

`meas_type` (singular) is internal-only (`init=False`); `runExpectation` iterates
over `meas_types`, deep-copies the entry, and assigns one `meas_type` per
iteration via `set_meas_type()`.

### Liberty template registration (`config_lib.jsonc`)

```jsonc
"templates": [
  {"kind":"delay",      "grid":"10x10", "name":"d000", "index_1":[...], "index_2":[...]},
  {"kind":"power_tout", "grid":"10x10", "name":"d000", "index_1":[...], "index_2":[...]},
  {"kind":"power_tin",  "grid":"10x0",  "name":"d000", "index_1":[...], "index_2":[]},
  ...
]
```

charao が `.lib` に出力する lu_table_template 名（`gen_lut_templates` / `myExportLib.py`、`<kind>_energy_template_<grid>` 形式）:
- `kind=delay`      -> `delay_template_10x10`
- `kind=power_tout` -> `power_tout_energy_template_10x10`
- `kind=power_tin`  -> `power_tin_energy_template_10x0`

### Cell template_kgn (`std_*.jsonc`)

```jsonc
{"template_kgn": [
   ["leakage",    "0x0",   "d00"],
   ["delay",      "10x10", "d018"],
   ["power_tout", "10x10", "d018"],
   ["power_tin",  "10x0",  "d000"]   // only when the cell needs input pin internal_power
 ],
 "spice": "...", "cell": "...", "logic": "AOI21", "area": ...,
 "ports_dict": {...}}
```

`["power_tin", ...]` is added only to cells whose original Liberty has input
pin `internal_power` (see section 4 for the rule).

### 出力 port 別 template（第 4 要素、ISS-00150）

orig（vendor lib）は同一セルでも**出力ピンごとに異なる load 軸**を使う場合がある
（GF180 では adder のみ：addh_2 は S/CO で最終値が 25.7% 異なる。addf_2=7.0%、addf_4=11.7%。
他の複数出力セル addh_1/addh_4/addf_1 はピン間差 <1% でセル単位割当のまま）。

このため `template_kgn` の各エントリは**省略可能な第 4 要素＝logic 出力 port 名**を取れる：

```jsonc
{"template_kgn": [
   ["leakage",    "0x0",   "d00"],
   ["delay",      "10x10", "d028"],          // セル単位（第 4 要素なし）＝未指定 port の既定
   ["delay",      "10x10", "d023", "o0"],    // pin S(o0) だけ d023 を使う
   ["power_tout", "10x10", "d028"],
   ["power_tout", "10x10", "d023", "o0"]
 ], ...}
```

- **解決順**：`Mlc.get_template(kind, oport)` が `template_pin["<kind>@<oport>"]` →
  `template[kind]`（セル単位）の順で解決する。第 4 要素なしの既存記述は完全に従来動作
- **格納**：`myLogicCell.py` の `add_template()` が第 4 要素付きエントリを
  `Mlc.template_pin`（key=`"delay@o0"` 形式）へ、なしを従来の `Mlc.template[kind]` へ格納
- **参照側**：`charao_run.py` の delay / power_tout の template 選択が
  `mlc.get_template(kind, mec.pin_oirc[0])`（entry の出力 port で per-pin 解決）
- **対象 kind**：load 軸（index_2）を持つ delay / power_tout を想定
  （power_tin / passive は slew 1 軸、const は slew×slew のため通常は不要）
- **注意**：jsonc は行末コメント不可（jsoncomment は行頭 `//` のみ対応）。
  コメントは独立行に書くこと

---

## 3. mylogic entry rules for power_tin

### Required fields

```python
MyExpectCell(
    pin_tr    = ["iN", ""],                   # ISS-00127: Liberty 出力の [target, related]（全 entry 必須）。
                                              #   power_tin は target=入力ピン iN、related なし
    pin_oirc  = ["o0", "", "iN", ""],         # 4 要素: [0]=output, [1]=空, [2]=入力(related slot), [3]=空(comb)
    ival      = {"o":["<output_held>"],       # 出力の保持値（"0"/"1"）
                 "i":["<input0>","<input1>",...]},  # 全入力の状態（cell 入力幅ぶん）
    meas_types= ["power_tin"],
    tmg_sense = "non",                        # active arc ではない
    arc_oirc  = ["0" or "1",                  # [0]=保持される出力値（旧 "s" は廃止）
                 "",                           # [1]=空
                 "r" or "f",                  # [2]=入力の遷移方向
                 ""],                          # [3]=空(comb)
    tmg_when  = "<other_inputs_state>",       # 例 "!i1"（i-notation、出力時に実ポート名へ変換）
    specify   = "",
)
# 注（現行仕様）:
#   - mondrv_oirc は ISS-00101 で廃止（省略。spice 駆動値は ival/arc_oirc から決定）
#   - arc_oirc[0] の "s"（stable）は廃止 → 保持される出力値 "0"/"1" を書く
#   - Liberty の target/related は pin_tr で決まる（pin_oirc からの自動推定は不採用）
```

### tmg_when

`tmg_when` describes the state of the **other** inputs (those not toggling) such
that the output stays constant. For example, in AOI21 with i0 toggling:

| state of (i1, i2) | output stays? | tmg_when |
|-------------------|---------------|----------|
| (0, 0)            | yes (=1)      | `!i1&!i2` |
| (0, 1)            | yes (=0)      | `!i1&i2`  |
| (1, 0)            | **no** (active arc, handled by power_tout) | (skip) |
| (1, 1)            | yes (=0)      | `i1&i2`   |

Three power_tin entries x 2 directions (rise/fall) = 6 entries for i0.
Same logic for i1 (3 stable states) and i2 (1 stable state).

### Per-logic mapping (which logics need power_tin?)

A logic needs power_tin entries only when at least one input toggle leaves the
output unchanged.

| logic family | needs power_tin? | reason |
|--------------|------------------|--------|
| INV / BUF / DLY / TIE / ANTENNA | **No** | one-input or input-less; every toggle changes the output (or there is no input toggle path) |
| AND / OR / NAND / NOR (2/3/4-input) | **Yes** | toggling one input may leave the output unchanged when an "other input" forces the result |
| MUX2 / MUX4 | Yes | data input toggle is masked by select |
| AOI21 / AOI22 / AOI211 / AOI221 / AOI222 | Yes | input toggle in a non-controlling group leaves output stable |
| OAI21 / OAI22 / OAI31 / OAI32 / OAI33 / OAI211 / OAI221 / OAI222 | Yes | symmetric to AOI |
| XOR2 / XOR3 / XNOR2 / XNOR3 | **No** | XOR family always toggles the output for any input toggle |
| ADDH / ADDF | **No** | their SUM output is XOR-based; every input toggle changes SUM |

### Auto-generation

For combinational single-output cells, mylogic power_tin entries are generated
mechanically by enumerating all input states and selecting the ones where the
output is invariant under each input toggle. See:

- `tmp/insert_power_tin.py` (comb_base)
- `tmp/insert_complex.py` (comb_complex)

These scripts are git-ignored (temporary tooling); regenerate as needed.

---

## 4. Simulation: `runSpicePowerTinSingle` (`meas_energy=5`)

Output is stable, so the standard `.MEASURE TRAN ... WHEN V(VOUT)=...` for
`energy_end` cannot trigger. charao introduces `meas_energy=5`:

- `tb_template` skips `.option autostop` and the `energy_start` / `energy_end` `.MEASURE TRAN` blocks.
- `q_*` / `i_*` integrations (`q_in_dyn`, `q_rel_dyn`, `i_vdd_leak`, ...) run as in `meas_energy=2`.
- **ISS-00142（2026-07-06 改訂、 target スロット方式）**：積分窓は旧仕様の `estart = t_rel0` 固定ではなく、
  **`pin_tr[0]`（target pin X）を c > r > i で逆引きした駆動スロット（`energy_tgt_slot/node`）** の
  遷移時刻に取る：slot1(VIN)→`[t_in0, t_in1+1ns]`、 slot3(VCLK)→`[t_clk4, t_clk5+1ns]`、
  slot2(VREL)→`[t_rel0, t_rel1+1ns]`。 slope（index_1 軸の tslew 反映先）と cin も同スロット基準。
  （旧仕様＝t_rel0 固定・slope=tslew_clk 固定は、 CLK target で窓外→pin(CLK) 全 0、
  index_1 軸が物理反映されない、 cin≈0 の同根 3 バグの原因だった）
- charao sets `time_energy = [estart, eend]` directly (no SPICE measurement of energy_start/end).
- `eintl` is then computed by the same min-rail formula as power_tout.

> **power_tout 側の窓（ISS-00151、 2026-07-08）**：energy2 の INTEG 窓は
> `[min(t_in0, t_rel0), max(t_in1, t_rel1, eend) + 0.3ns]`。 margin 0.3ns は eend（VOUT 閾値交差）
> 以降の指数尻尾（fall で 7.2% 実測）の取りこぼし対策（SW_TAIL は time_energy[1] 参照で自動追従）。
> energy_start/end の WHEN が大 slew で out of interval の場合は energy1 確定値
> （`ener_estart/eend`）へフォールバック。

`runSpicePowerTinSingle` takes no `index2_load` argument (1D template, output
load fixed at 0 pF). The result is stored in `dict_list2["eintl"][slope][0.0]`.

---

## 5. Liberty output (`myExportLib.py`)

- Output pin block: existing logic emits `internal_power()` blocks for harnesses
  whose `template_kind` matches `startswith(("power_tout", "power_c", "power_i"))`
  (prefix match, covering `power_tout` / `power_c*` / `power_i*`),
  with `related_pin` set to the trigger input.
- Input pin block: a new section emits `internal_power()` blocks for harnesses
  whose `template_kind == "power_tin"` and `target_inport == port`. `related_pin`
  is **omitted** (Liberty default = the input pin), `when` is the input pin's
  stable-state condition, and `fall_power` / `rise_power` table names use
  `passive_power` (input direction) since `direction_power` is `"stable"` here.

---

## 6. CSV extraction (`util_extract_lib_csv.py`)

`_emit_table` recognizes 1D tables (`index_2` empty): for power_tin, it emits
one row per `index_1` value with `index_2 = 0.0` placeholder. The resulting
`power.csv` row has `pin = <input pin>`, `related_pin = ""`, `when = "..."`.

---

## 7. CSV comparison (`util_compare_lib_csv.py`)

`power.csv` is compared twice, separated by pin direction:

- `=== power (output pin, active arc) ===`: rows with `related_pin != ""`
- `=== power (input pin, stable state) ===`: rows with `related_pin == ""`

Each section uses the standard `(cell, pin, related_pin, when, kind)` group key.

---

## 8. Verification

| cell | output pin power_tout | input pin power_tin | result |
|------|----------------------|---------------------|--------|
| `inv_1`   | 2 matched | 0 / 0 (not needed) | OK |
| `and2_1`  | 4 matched | 4 entries, charao output verified | OK |
| `aoi21_1` | 10 matched | **14 matched, 0 missing** vs orig | exact match |

`when` strings on AOI21_1 input pin `internal_power` blocks coincide with the
orig vendor library exactly:
- A1: `!A2 !B`, `!A2 B`, `A2 B`
- A2: `!A1 !B`, `!A1 B`, `A1 B`
- B: `A1 A2`

---

## 9. References

- Liberty Format Reference (vendor proprietary; vendor-specific conventions for
  `fall_power` / `rise_power` direction inside input pins).
- `charao/script/myExpectCell.py` (`MyExpectCell.meas_types`, `set_meas_type`)
- `charao/script/charao_run.py` (`runSpicePowerToutMultiThread`,
  `runSpicePowerTinMultiThread`, `runSpicePowerTinSingle`,
  `genFileLogic_PowerTinTrial1x`, `runExpectation`)
- `charao/script/temp_testbench.sp.jp2` (`meas_energy=5` branches)
- `charao/script/myExportLib.py` (input pin internal_power emission)
- `charao/script/util_extract_lib_csv.py` (1D table support)
- `charao/script/util_compare_lib_csv.py` (direction-split power compare)
