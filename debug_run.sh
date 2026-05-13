#!/bin/bash
# charao debug runner via lrPymRPC
#
# Usage:
#   bash debug_run.sh clean           # cleanup
#   bash debug_run.sh run_all         # run as single batch (one charao invocation)
#   bash debug_run.sh run_each        # run per-cell (loop over CELLS, archive each)
#   bash debug_run.sh lib2csv_orig    # extract orig .lib -> CSV (overwrite existing)
#   bash debug_run.sh lib2csv_charao  # extract charao .lib -> CSV (wipes tmp/charao_* first)
#   bash debug_run.sh compare         # compare charao CSV vs orig CSV (wipes tmp/compare_* first)
#
# Env vars (all optional):
#   MODE=pip|local            # default: pip
#   CELLS="short1 short2..."  # unset -> no --cells_only (all cells)
#   INDEX1="0 9"              # unset -> no --template_index1_only (all idx1)
#   INDEX2="0 9"              # unset -> no --template_index2_only (all idx2)
#   COMPARE_INTERPOLATE=0|1   # default: 1 (--interpolate on)
#   (INDEX1/INDEX2 とも未設定で全 grid 実行時は --keep_zero_new 自動付与)
#
# Examples:
#   # 2x2 corners, all cells, local charao, then extract + compare
#   INDEX1="0 9" INDEX2="0 9" MODE=local bash debug_run.sh clean run_all lib2csv_charao compare
#
#   # Full flow including orig lib extract (first time)
#   bash debug_run.sh lib2csv_orig lib2csv_charao compare

# Activate venv if available (no-op when already activated or absent)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "$VIRTUAL_ENV" ] && [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
  source "$SCRIPT_DIR/venv/bin/activate"
fi

set -e

LIB_FILE="gf180CB5P00fdmcuC7t20240817_TTV5P00C25_b00.lib"
ORIG_LIB="sample/src/gf180mcuC/libs.ref/gf180mcu_fd_sc_mcu7t5v0/lib/gf180mcu_fd_sc_mcu7t5v0__tt_025C_5v00.lib"
ORIG_CSV_DIR="tmp/gf180_fd_mcuC7t20240817/tt_025C_5v00"

_setup_args() {
  MODE_="${MODE:-pip}"

  INDEX1_OPT=""
  [ -n "${INDEX1}" ] && INDEX1_OPT="--template_index1_only ${INDEX1}"
  INDEX2_OPT=""
  [ -n "${INDEX2}" ] && INDEX2_OPT="--template_index2_only ${INDEX2}"
  MEAS_ONLY_OPT=""
  [ -n "${MEAS_ONLY}" ] && MEAS_ONLY_OPT="--measures_only ${MEAS_ONLY}"

  # mylogic_user.py をプロジェクトルート直下から自動検出（v0.9.14 以降は通常不要）
  MYLOGIC_USER_OPT=""
  MYLOGIC_USER_SOURCE=""
  MYLOGIC_USER_MATCH=""
  if [ -f "mylogic_user.py" ]; then
    MYLOGIC_USER_OPT="--mylogic_user mylogic_user.py"
    MYLOGIC_USER_SOURCE="mylogic_user.py"
    MYLOGIC_USER_MATCH="mylogic_user"
  fi

  if [ "$MODE_" = "local" ]; then
    CHARAO_CMD="python3 -m charao.script.charao"
    REPO_ARG="--REPO_URL jsoncomment=jsoncomment,pydantic=pydantic,numpy=numpy,jinja2=jinja2"
    SOURCE_ARG="--SOURCE sample ${MYLOGIC_USER_SOURCE} charao"
    SOURCE_INCLUDE_ARG="--SOURCE_INCLUDE .spice .ngspice .sp .jsonc .py .jp2"
    SOURCE_MATCH_ARG="--SOURCE_MATCH gf180 ${MYLOGIC_USER_MATCH} charao"
  else
    CHARAO_CMD="python3 -m charao"
    REPO_ARG="--REPO_URL charao=git+https://github.com/MatsudaLogicResearch/charao_prj.git"
    SOURCE_ARG="--SOURCE sample ${MYLOGIC_USER_SOURCE}"
    SOURCE_INCLUDE_ARG="--SOURCE_INCLUDE .spice .ngspice .sp .jsonc .py"
    SOURCE_MATCH_ARG="--SOURCE_MATCH gf180 ${MYLOGIC_USER_MATCH}"
  fi
}

cmd_clean() {
  set -x
  rm -rf rslt rslt_* work work_* lrpymrpc*.log
  { set +x; } 2>/dev/null
}

cmd_run_all() {
  _setup_args
  local CELLS_OPT=""
  if [ -n "${CELLS}" ]; then
    local CELLS_FULL=""
    for s in $CELLS; do
      CELLS_FULL="${CELLS_FULL} gf180mcu_fd_sc_mcu7t5v0__${s}"
    done
    CELLS_OPT="--cells_only${CELLS_FULL}"
  fi

  echo "===== run_all: MODE=${MODE_} CELLS='${CELLS:-<all>}' INDEX1='${INDEX1:-<all>}' INDEX2='${INDEX2:-<all>}' (batch) ====="
  rm -rf rslt work
  local LOG="lrpymrpc_debug_batch.log"
  local CMD="${CHARAO_CMD} -f gf180 -v fd -r mcuC7t20240817 -g std -u 5P00 -p TT -t 25.0 --vdd 5.0 --target sample/target ${CELLS_OPT} ${INDEX1_OPT} ${INDEX2_OPT} ${MEAS_ONLY_OPT} ${MYLOGIC_USER_OPT}"
  set -x
  python -u -m lrPymRPC \
    --SERVER_IP 192.168.168.103 \
    $REPO_ARG \
    $SOURCE_ARG \
    $SOURCE_INCLUDE_ARG \
    $SOURCE_MATCH_ARG \
    --RESULT rslt work \
    --CMD "$CMD" 2>&1 | tee "$LOG"
  { set +x; } 2>/dev/null
  echo ""
  echo "===== summary: failed-spice grep (batch log) ====="
  local n
  n=$(grep -c "Failed to launch spice" "$LOG" 2>/dev/null || true)
  [ -z "$n" ] && n=0
  printf "  %-20s : %s failures\n" "batch" "$n"
}

cmd_run_each() {
  _setup_args
  if [ -z "${CELLS}" ]; then
    echo "run_each requires CELLS to be set (per-cell loop)" >&2
    exit 2
  fi
  echo "===== run_each: MODE=${MODE_} CELLS='${CELLS}' INDEX1='${INDEX1:-<all>}' INDEX2='${INDEX2:-<all>}' (per-cell) ====="
  for short in $CELLS; do
    local full="gf180mcu_fd_sc_mcu7t5v0__${short}"
    echo "=========================================="
    echo "===== running cell: ${short}"
    echo "=========================================="
    rm -rf rslt work "work_${short}" "rslt_${short}"
    local LOG="lrpymrpc_debug_${short}.log"
    local CMD="${CHARAO_CMD} -f gf180 -v fd -r mcuC7t20240817 -g std -u 5P00 -p TT -t 25.0 --vdd 5.0 --target sample/target --cells_only ${full} ${INDEX1_OPT} ${INDEX2_OPT} ${MEAS_ONLY_OPT} ${MYLOGIC_USER_OPT}"
    set -x
    python -u -m lrPymRPC \
      --SERVER_IP 192.168.168.103 \
      $REPO_ARG \
      $SOURCE_ARG \
      $SOURCE_INCLUDE_ARG \
      $SOURCE_MATCH_ARG \
      --RESULT rslt work \
      --CMD "$CMD" 2>&1 | tee "$LOG"
    { set +x; } 2>/dev/null
    [ -d work ] && mv work "work_${short}"
    [ -d rslt ] && mv rslt "rslt_${short}"
  done
  echo ""
  echo "===== summary: failed-spice grep across logs ====="
  for short in $CELLS; do
    local n
    n=$(grep -c "Failed to launch spice" "lrpymrpc_debug_${short}.log" 2>/dev/null || true)
    [ -z "$n" ] && n=0
    printf "  %-20s : %s failures\n" "$short" "$n"
  done
}

cmd_lib2csv_orig() {
  echo "===== lib2csv_orig: extract orig .lib -> CSV (${ORIG_CSV_DIR}) ====="
  [ -f "$ORIG_LIB" ] || { echo "lib2csv_orig: orig lib not found: $ORIG_LIB" >&2; exit 2; }
  set -x
  python -u -m charao.script.util_extract_lib_csv \
    --lib "$ORIG_LIB" \
    --out "$ORIG_CSV_DIR"
  { set +x; } 2>/dev/null
}

cmd_lib2csv_charao() {
  echo "===== lib2csv_charao: extract charao .lib -> CSV (wipes tmp/charao_* first) ====="
  set -x
  rm -rf tmp/charao_*
  { set +x; } 2>/dev/null
  local found=0
  # batch: rslt/
  if [ -f "rslt/${LIB_FILE}" ]; then
    found=1
    set -x
    python -u -m charao.script.util_extract_lib_csv \
      --lib "rslt/${LIB_FILE}" \
      --out tmp/charao_batch
    { set +x; } 2>/dev/null
  fi
  # per-cell: rslt_<name>/
  for d in rslt_*; do
    [ -d "$d" ] || continue
    [ -f "${d}/${LIB_FILE}" ] || continue
    found=1
    local name="${d#rslt_}"
    set -x
    python -u -m charao.script.util_extract_lib_csv \
      --lib "${d}/${LIB_FILE}" \
      --out "tmp/charao_${name}"
    { set +x; } 2>/dev/null
  done
  if [ $found -eq 0 ]; then
    echo "lib2csv_charao: no rslt/ or rslt_*/ with ${LIB_FILE} found" >&2
    exit 2
  fi
}

cmd_compare() {
  echo "===== compare: charao CSV vs orig CSV (wipes tmp/compare_* first) ====="
  set -x
  rm -f tmp/compare_*.csv tmp/compare_*.txt
  { set +x; } 2>/dev/null
  [ -d "$ORIG_CSV_DIR" ] || { echo "compare: orig CSV dir not found: $ORIG_CSV_DIR (run lib2csv_orig first)" >&2; exit 2; }
  local found=0
  for d in tmp/charao_*; do
    [ -d "$d" ] || continue
    found=1
    local name=$(basename "$d")
    name="${name#charao_}"
    local INTERP_OPT=""
    [ "${COMPARE_INTERPOLATE:-1}" = "1" ] && INTERP_OPT="--interpolate"
    # 全 index 実行（INDEX1/INDEX2 とも未設定）なら 0値も採用（drop_zero_new=False）
    local KEEP_ZERO_OPT=""
    [ -z "${INDEX1}" ] && [ -z "${INDEX2}" ] && KEEP_ZERO_OPT="--keep_zero_new"
    set -x
    python -u -m charao.script.util_compare_lib_csv \
      --orig "$ORIG_CSV_DIR" \
      --new "$d" \
      $INTERP_OPT \
      $KEEP_ZERO_OPT \
      --out_csv "tmp/compare_${name}.csv"
    { set +x; } 2>/dev/null
  done
  if [ $found -eq 0 ]; then
    echo "compare: no tmp/charao_*/ found (run lib2csv_charao first)" >&2
    exit 2
  fi
}

usage() {
  cat <<EOF
Usage: $0 <clean|run_all|run_each|lib2csv_orig|lib2csv_charao|compare> ...
  clean          : rm -rf rslt* work* lrpymrpc*.log
  run_all        : lrPymRPC charao run (batch: single invocation, single log)
  run_each       : lrPymRPC charao run (per-cell: loop over CELLS, per-cell log/work archive)
  lib2csv_orig   : extract orig .lib -> CSV (${ORIG_CSV_DIR})
  lib2csv_charao : extract charao .lib -> CSV (rslt/ -> tmp/charao_batch, rslt_<cell>/ -> tmp/charao_<cell>; wipes tmp/charao_* first)
  compare        : compare charao CSV vs orig CSV -> tmp/compare_<name>.csv (wipes tmp/compare_* first)

Env vars (all optional):
  MODE=pip|local            (default: pip)
  CELLS="short1 short2..."  (unset = all cells; no --cells_only)
  INDEX1="0 9"              (unset = all idx1;   no --template_index1_only)
  INDEX2="0 9"              (unset = all idx2;   no --template_index2_only)

Examples:
  # all cells, 2x2 corners, local, batch + extract + compare
  INDEX1="0 9" INDEX2="0 9" MODE=local bash $0 clean run_all lib2csv_charao compare

  # 6 cells per-cell, 2x2 corners, then extract + compare
  CELLS="and4_2 and4_4 mux2_1 nand4_2 nor3_2 nor4_1" INDEX1="0 9" INDEX2="0 9" MODE=local bash $0 clean run_each lib2csv_charao compare

  # first-time setup: generate orig CSV, then charao run + extract + compare
  bash $0 lib2csv_orig
  INDEX1="0 9" INDEX2="0 9" MODE=local bash $0 run_all lib2csv_charao compare
EOF
  exit 1
}

[ $# -eq 0 ] && usage

for arg in "$@"; do
  case "$arg" in
    clean)          cmd_clean ;;
    run_all)        cmd_run_all ;;
    run_each)       cmd_run_each ;;
    lib2csv_orig)   cmd_lib2csv_orig ;;
    lib2csv_charao) cmd_lib2csv_charao ;;
    compare)        cmd_compare ;;
    *) echo "unknown arg: $arg" >&2; usage ;;
  esac
done
