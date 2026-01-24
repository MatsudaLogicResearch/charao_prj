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


## USAGE

### option
```
usage: charao.py [-h] [-f FAB_PROCESS] [-v CELL_VENDOR] [-r CELL_REVISION] [-g {std,io}] [-u USAGE_VOLTAGE] [-p PROCESS_CORNER] [-t TEMP] [--vdd VDD]
                 [--vss VSS] [--vnw VNW] [--vpw VPW] [--target TARGET] [--cells_only [CELLS_ONLY ...]] [--measures_only [MEASURES_ONLY ...]]
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

