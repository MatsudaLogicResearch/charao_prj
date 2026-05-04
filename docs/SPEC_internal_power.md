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
| **output pin** | `pwr_tin_oload_10x10` | 2D (input slope x output load) | active arc (output toggles when an input toggles); `related_pin` specifies the trigger input |
| **input pin** | `pwr_tin_10` | 1D (input slope only, **no output load**) | state-dependent power (input toggles, output stays at a fixed value); `related_pin` is omitted (Liberty default = the same input pin) |

### Example: AOI21 (`o = !((A1 & A2) | B)`)

Inside `cell(aoi21_X)`:

```liberty
pin (A1) {
  direction : input ;
  internal_power () {              # input pin power: A1 toggles, output stays
    when : "!A2 !B" ;              # state where output stays at 1
    fall_power(pwr_tin_10) { ... } # value for A1 fall
    rise_power(pwr_tin_10) { ... } # value for A1 rise
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
    fall_power(pwr_tin_oload_10x10) { ... }
    rise_power(pwr_tin_oload_10x10) { ... }
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

Map to Liberty:
- `kind=delay`      -> `tmg_ntin_oload_10x10`
- `kind=power_tout` -> `pwr_tin_oload_10x10`
- `kind=power_tin`  -> `pwr_tin_10`

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

---

## 3. mylogic entry rules for power_tin

### Required fields

```python
MyExpectCell(
    pin_oir   = ["o0", "iN", "iN"],          # output pin, input pin, related pin (= same input pin)
    ival      = {"o":["<output_value>"],
                 "i":["<input0>","<input1>",...]},  # full state (per cell input width)
    mondrv_oir= ["<output_unchanged>",
                 "1" or "0",                  # input transitions to 1 (rise) or 0 (fall)
                 "1" or "0"],                 # related = input value
    meas_types= ["power_tin"],
    tmg_sense = "non",                        # not an active arc
    arc_oir   = ["s",                         # output stable
                 "r" or "f",                  # input rise or fall
                 "r" or "f"],                 # related = input direction
    tmg_when  = "<other_inputs_state>",       # e.g. "!i1&!i2", in i-notation; replaced by ports at output time
    specify   = "",
)
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
- charao sets `tsim_end = eend + 1ns` where `eend = tdelay_rel + tslew_rel` (input transition window).
- charao sets `time_energy = [estart, eend]` directly (no SPICE measurement of energy_start/end).
- `eintl` is then computed by the same min-rail formula as power_tout.

`runSpicePowerTinSingle` takes no `index2_load` argument (1D template, output
load fixed at 0 pF). The result is stored in `dict_list2["eintl"][slope][0.0]`.

---

## 5. Liberty output (`myExportLib.py`)

- Output pin block: existing logic emits `internal_power()` blocks for harnesses
  whose `template_kind` is in `("power_tout", "power_c2c", "power_c2i", "power_i2c", "power_i2i")`,
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
