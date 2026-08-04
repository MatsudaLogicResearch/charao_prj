# PROJECT

charao is a open cell library characterizer.

## Introduction

This repository is a fork of [libretto](https://github.com/snishizawa/libretto).  
All credits and copyrights belong to the original authors.  
This fork includes additional modifications and customizations.

Current version support timing characterization and power characterization of combinational cells and sequential cells.
Multithread supported. All of the indexes are simulated in parallel.

## INSTALL
```bash
pip install git+https://github.com/MatsudaLogicResearch/charao_prj.git
```

### Development / E2E Test Environment (venv)

To run E2E tests locally, set up a venv with the following packages:

```powershell
# Create venv (first time only)
python -m venv .venv_charao

# Activate
.venv_charao\Scripts\activate   # Windows
# source .venv_charao/bin/activate  # Linux/Mac

# Install charao and test dependencies
pip install -e .
pip install pyyaml pytest
pip install git+https://github.com/MatsudaLogicResearch/lrPymRPC_prj.git
```

## Required Tools
- Simulator. We assume ngspice
- Pandoc, if you want to convert datasheet in Markdown to PDF

## Required Files
- Overview
    - SPICE models
     - Standard (STD) and IO cell SPICE files
     - Configuration files (JSONC format)

- SPICE Models
    - The paths to SPICE models are specified in the configuration file config_lib.jsonc under the key model_path.
    - The scripts refer to files in the format:
    ```
    <ARGS.target>/<ARGS.fab_process>/.model_<ARGS.fab_process>_<ARGS.process_corner>.sp
    ```
    - Each of these files contains include statements pointing to the actual SPICE model files.

- STD/IO Cell SPICE Files
    - The paths to standard and IO cell SPICE files are specified in config_lib.jsonc under the keys cell_spice_path and io_spice_path.
    - The scripts reference these files using paths like:
    ```
    config_lib.cell_spice_path/AND.sp
    config_lib.io_spice_path/GPIO.sp
    ```

- Configuration Files
    - Place the following four files in the directory:
    ```
    <ARGS.target>/<ARGS.fab_process>/<ARGS.cell_vendor>/
  	  config_lib.jsonc    : must
  		cell_comb.jsonc     : optional for ARGS.cell_group std
  		cell_seq.jsonc      : optional for ARGS.cell_group std
  		cell_io.jsonc       : optional for ARGS.cell_group io
    ```
    - These configuration files provide the necessary information for SPICE model paths, cell definitions, and IO configurations.

- Verilog Primitives (std_primitives.v)
    - Place `std_primitives.v` in the same directory as `config_lib.jsonc`:
    ```
    <ARGS.target>/<ARGS.fab_process>/<ARGS.cell_vendor>/<ARGS.cell_revision>/std_primitives.v
    ```
    - It must define the four UDPs that the generated Verilog instantiates
      (`udp_iq_ff_n` / `udp_iq_ff_hn` / `udp_iq_latch_n` / `udp_iq_latch_hn`).
    - charao copies this file to `<result_path>/<lib_basename>_primitives.v` as-is
      (for `ARGS.cell_group=std` only). If the file is absent, the primitive output is skipped.
    - See `docs/SPEC_primitives.md` for the required interface and porting steps.


## USAGE

### option
```
usage: charao.py [-h] [-f FAB_PROCESS] [-v CELL_VENDOR] [-r CELL_REVISION] [-g {std,io}] [-u USAGE_VOLTAGE] [-p PROCESS_CORNER] [-t TEMP] [--vdd VDD]
                 [--vss VSS] [--vnw VNW] [--vpw VPW] [--target TARGET] [--cells_only [CELLS_ONLY ...]] [--mylogic_only [MYLOGIC_ONLY ...]]
                 [--measures_only [MEASURES_ONLY ...]]
                 [-s SIGNIFICANT_DIGITS] [-b BUILD_STAMP] [-w WORK_DIR] [--mylogic_user MYLOGIC_USER]


argument

options:
  -h, --help                                      : show this help message and exit
  -f FAB_PROCESS, --fab_process FAB_PROCESS       : FAB process name(use for only search PATH)
  -v CELL_VENDOR, --cell_vendor CELL_VENDOR       : CELL type or vendor ID(use for only search PATH)
  -r CELL_REVISION, --cell_revision CELL_REVISION : CELL revision(use for only search PATH)
  -g {std,io}, --cell_group {std,io}              : select cell_type(use for only to select macro)
  -u USAGE_VOLTAGE, --usage_voltage USAGE_VOLTAGE : usage voltage(use for only to create file name)
  -p PROCESS_CORNER, --process_corner PROCESS_CORNER :process condition
  -t TEMP, --temp TEMP  : temperature.
  --vdd VDD             : VDD voltage.
  --vss VSS             : VSS voltage.
  --vnw VNW             : NWELL voltage
  --vpw VPW             : PWELL voltage
  --target TARGET       : PATH to <target> directory
  --cells_only [CELLS_ONLY ...]                                  : list of target cell names. blank meas all cells.
  --mylogic_only [MYLOGIC_ONLY ...]                              : list of target mylogic module names (ex "comb_base" for mylogic_comb_base.py). blank meas all modules. combined with --cells_only by AND.
  --measures_only [MEASURES_ONLY ...]                            : list of measure_type names. blank meas all measure_type.
  -s SIGNIFICANT_DIGITS, --significant_digits SIGNIFICANT_DIGITS : significant digits.
  -b BUILD_STAMP, --build_stamp BUILD_STAMP                      : build-stamp for output files.
  -w WORK_DIR, --work_dir WORK_DIR                               : work directory.
  --mylogic_user MYLOGIC_USER                                    : PATH to User-define Logic entries file(ex myloic_user.py).

```

### generate liberty/verilog/markdown
- command 
```bash
>python -m charao -g std -f OSU035 -v NORMAL -u 5.0 -p TT -t 25.0
```
- result
```
  OSU035CBV5P00NORMALV00.00.v
  OSU035CBV5P00NORMALV00.00_TTV5P00C25.lib
  OSU035CBV5P00NORMALV00.00_TTV5P00C25.md
```

### convert from markdown to PDF.
- command 
```bash
/bin/pandoc OSU035CBV5P00NORMALV00.00_TTV5P00C25.md -o OSU035CBV5P00NORMALV00.00_TTV5P00C25.pdf -V documentclass=ltjarticle --pdf-engine=lualatex  -V tables-alignment=left -V geometry:margin=1in -N -V secnumdepth=4; 
```
- result
```
  OSU035CBV5P00NORMALV00.00_TTV5P00C25.pdf
```
## E2E Tests

E2E tests run charao on a remote Linux server via [lrPymRPC](https://github.com/MatsudaLogicResearch/lrPymRPC_prj) and verify the generated `.lib` output against expected values.

### Prerequisites

- venv with `pyyaml`, `pytest`, and `lrPymRPC` installed (see [Development Environment](#development--e2e-test-environment-venv))
- Remote server accessible at `192.168.168.103` with ngspice installed

### Test Scenarios

| Scenario | Class | Library | Cell | Measures | Status |
|----------|-------|---------|------|----------|--------|
| std_comb_leakage_inv | `TestStdCombLeakageInv` | OSU035 / VENDOR / TT / 25°C / 5.0V | INV_1X | leakage | PASS (v0.9.4) |

### Running Tests

```powershell
cd D:\git\charao_prj
.venv_charao\Scripts\activate

# Run all E2E tests
pytest tests/test_e2e.py -v

# Run a specific scenario
pytest tests/test_e2e.py::TestStdCombLeakageInv -v
```

### Options

| Option | Effect |
|--------|--------|
| `-v` | Verbose test names |
| `--tb=long` | Full traceback on failure (default: short) |
| `--tb=no` | Suppress traceback |

To show full lrPymRPC output (pip install logs etc.) on success, set `lrpymrpc_verbose = true` in `pytest.ini`.

### Log Output

| Log | Path |
|-----|------|
| Test results | `test_log/test_e2e.log` |
| lrPymRPC execution log | `test_log/<scenario_name>/lrpymrpc.log` |

> Note: `test_log/` is recreated at the start of each test session.

## Documentation

- [Internal Power Specification](docs/SPEC_internal_power.md): output pin / input pin separation (`power_tout` / `power_tin`), mylogic entry rules, and verification guidelines (introduced in `0.9.14a01`).
- [Three-state cell support specification](docs/SPEC_three_state.md): bus keeper (HOLD) and tri-state buffer/inverter (BUFZ/INVZ) characterization rules, three_state_enable / three_state_disable arcs, `delay_disable` 1D template, and porting guide for new PDKs (introduced in `0.9.14a03`).
- [Sequential FF / SDFF cell support specification](docs/SPEC_seq_ff.md): D-Flip-Flop characterization rules (8 GF180 families: dffq / dffnq / dffrnq / dffnrnq / dffsnq / dffnsnq / dffrsnq / dffnrsnq), naming convention (`<S>DFF[B]_<P\|N>C[_<P\|N>R][_<P\|N>S]`), GF180 wrap-style vcode (`not gate + udp_iq_ff_n/hn + not gate`), and porting guide for new PDKs (introduced in `0.9.14a06`).
- [Verilog primitive specification](docs/SPEC_primitives.md): the four UDPs required by the generated Verilog (`udp_iq_ff_n` / `udp_iq_ff_hn` / `udp_iq_latch_n` / `udp_iq_latch_hn`), their port order and semantics, the `<target>/std_primitives.v` input, the `<lib_basename>_primitives.v` output, and porting steps for new PDKs.
- [Cell definition jsonc specification](docs/SPEC_cell_jsonc.md): how to write `std_comb.jsonc` /
  `std_seq.jsonc` — `ports_dict` (pin order must match the subckt; power pins take the real pin
  name as the value), `template_kgn` and the valid template kinds, and the porting steps for a
  new PDK.
- [Template generation specification](docs/SPEC_make_templates.md): how `util_make_templates.py`
  determines `templates` from measurement — the 5 stages (`1.probe` / `2.report` / `3.scan` /
  `4.analyze` / `5.build`), how `index_1[min/max]` and `index_2[min]` are decided, the per-cell
  `max_capacitance` convergence loop, and the `--measures_only` caveat for flip-flops
  (their delay measure is `rising_edge`/`falling_edge`, not `delay`).

## License

- **charao itself** : GNU General Public License v2.0 or later (see `LICENSE`).
- **`sample_target/gf180/fd/*/std_primitives.v`** : Apache License 2.0,
  Copyright 2022 GlobalFoundries PDK Authors.
  Derived from open_pdks gf180mcu; the primitives were renamed for charao
  (see the notice of modification in the file itself).
  A copy of the license is provided at `sample_target/gf180/LICENSE-Apache-2.0.txt`.

## Known issues (future works)
4. Multiple voltage for IOs and level shifters
5. Logic parser to find mismatch between logic definition and netlist.

## Done
1. Support more logics
 - Combinationals: multi-output cells
 - Sequentials: latches, scans
2. Verilog generation for timing simulation
3. Tristates
6. Use defined logic.

