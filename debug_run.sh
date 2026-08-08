#!/bin/bash
# charao debug runner via lrPymRPC
#
# Usage:
#   bash debug_run.sh clean           # cleanup
#   bash debug_run.sh run_all         # run as single batch (one charao invocation)
#   bash debug_run.sh run_each        # run per-cell (loop over CELLS, archive each)
#   bash debug_run.sh merge           # rslt 群 -> 1 本の .lib/.v/.md
#   bash debug_run.sh lib2csv         # .lib 1 本 -> CSV
#   bash debug_run.sh compare         # charao CSV vs orig CSV -> compare_<RUN_NAME>.csv
#
# Env vars (all optional):
#
#   --- 実行の 2 軸（ISS-00196。旧 MODE / EXEC は廃止）---
#   EXEC_MACHINE=local|server   # どのマシンで python を回すか（既定 local）
#   EXEC_SCRIPT=local_repo|git+pip|git+clone
#                               # どの charao を使うか（既定 git+pip）
#   CHARAO_TAG=main             # git+pip / git+clone のリビジョン
#
#   --- merge / lib2csv / compare の入出力 ---
#   MERGE_DIRS="a/rslt b/rslt"  # merge の入力（未指定なら <RUN_NAME>/rslt_*）
#   MERGED_DIR="merged"         # merge の出力（既定 <RUN_NAME>/merged）
#   LIB / CSV_OUT               # lib2csv の入力 .lib / 出力 CSV dir
#   CSV_NEW                     # compare の charao 側 CSV dir（既定 tmp/charao_<RUN_NAME>）
#   SKIP_IF_EXISTS=0|1          # lib2csv: 既存 CSV があれば作り直さない（既定 1）
#   CONFIRM=yes                 # clean_all を実際に実行するために必要
#
#   CELLS="short1 short2..."  # unset -> no --cells_only (all cells)
#   MYLOGIC="comb_base seq_lat"# unset -> no --mylogic_only (all modules). mylogic_<name>.py の <name> を指定（ISS-00169）
#   INDEX1="0 9"              # unset -> no --template_index1_only (all idx1)
#   INDEX2="0 9"              # unset -> no --template_index2_only (all idx2)
#   COMPARE_INTERPOLATE=0|1   # default: 1 (--interpolate on)
#   (INDEX1/INDEX2 とも未設定で全 grid 実行時は --keep_zero_new 自動付与)
#   SRC_DIR="sample_src"      # default: sample_src (PDK SPICE / lib 等の src 群)
#   TARGET_DIR="sample_target"# default: sample_target。旧版 sim 比較時は old_target に切替
#   SPICE_PATH=<dir>          # cell netlist のルート。未指定なら std_*.jsonc の "spice_path"。
#                             #   **ファイル名は変えず**ルートだけ差し替える（ISS-00205）。
#                             #   例: プリレイアウト <-> PEX 版の切り替え
#
#   --- PDK 切替（未指定なら gf180）---
#   FAB / VENDOR / REV        # charao の -f / -v / -r（target dir の 3 階層）
#   GROUP / UV / CORNER / TEMP / VDD  # -g / -u / -p / -t / --vdd
#   VNW / VPW                 # --vnw / --vpw（未指定なら charao が --vdd/--vss を反映）
#   CELL_PREFIX               # CELLS の短縮名に前置するセル名 prefix（OSU035 は空）
#   MATCH                     # --SOURCE_MATCH の PDK 判別語（default: $FAB）
#   LIB_FILE / ORIG_LIB / ORIG_CSV_DIR  # 通常は自動導出。orig 無し PDK は compare 系を使わない
#
# Examples:
#   # 2x2 corners, all cells, local charao, then extract + compare
#   INDEX1="0 9" INDEX2="0 9" EXEC_MACHINE=server EXEC_SCRIPT=local_repo bash debug_run.sh clean run_all merge lib2csv compare
#
#   # orig CSV は一度作れば再利用（LIB / CSV_OUT で orig を指定）
#   LIB="$ORIG_LIB" CSV_OUT="$ORIG_CSV_DIR" bash debug_run.sh lib2csv
#
#   # 旧 vs 新 sim 比較 (corner x1):
#   #   新版: EXEC_SCRIPT=local_repo + sample_target (default)
#   INDEX1="9" INDEX2="9" CELLS="inv_1" EXEC_MACHINE=server EXEC_SCRIPT=local_repo RUN_NAME=run_new bash debug_run.sh clean run_each
#   #   旧版: EXEC_SCRIPT=git+pip + TARGET_DIR=old_target
#   INDEX1="9" INDEX2="9" CELLS="inv_1" EXEC_MACHINE=server EXEC_SCRIPT=git+pip TARGET_DIR=old_target RUN_NAME=run_old bash debug_run.sh run_each
#
#   # OSU035（他 PDK）2x2 corner を数セルで確認
#   FAB=OSU035 VENDOR=VENDOR REV=CB_REV2 UV=3P30 VDD=3.3 MATCH=OSU035 CELL_PREFIX= \
#   INDEX1="0 6" INDEX2="0 6" CELLS="INV_1X NAND2_1X DFFARAS_1X" \
#   EXEC_MACHINE=server EXEC_SCRIPT=local_repo RESULT_ITEMS="rslt" RUN_NAME=run_osu bash debug_run.sh run_all
#
#   # SKY130（MATCH は既定の PDK 名でよい。 モデルが libs.ref/sky130_fd_pr にあるため絞れない）
#   FAB=sky130 VENDOR=fd REV=sc_hd UV=1P80 VDD=1.8 MATCH=sky130 CELL_PREFIX=sky130_fd_sc_hd__ \
#   INDEX1="0 6" INDEX2="0 6" CELLS="inv_1" \
#   EXEC_MACHINE=server EXEC_SCRIPT=local_repo RESULT_ITEMS="rslt" RUN_NAME=run_sky bash debug_run.sh run_all

# Activate venv if available (no-op when already activated or absent)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "$VIRTUAL_ENV" ] && [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
  source "$SCRIPT_DIR/venv/bin/activate"
fi

set -e

# RUN_NAME: default "run" (常に設定、 並列実行時は run1/run2/... 等を指定)
# 全 cmd_* で ${RUN_NAME} を直接参照（RUN_NAME 指定時 ./<name>/rslt、 指定なし ./run/rslt）
RUN_NAME="${RUN_NAME:-run}"

# SRC_DIR / TARGET_DIR: charao の src / target dir。 旧版 sim 比較は TARGET_DIR=old_target で切替
SRC_DIR="${SRC_DIR:-sample_src}"
TARGET_DIR="${TARGET_DIR:-sample_target}"

# ---------------------------------------------------------------------------
# PDK パラメータ（未指定なら gf180）。 他 PDK は env で切替える。
#   例) OSU035:
#     FAB=OSU035 VENDOR=VENDOR REV=CB_REV2 UV=3P30 VDD=3.3 \
#     MATCH=OSU035 CELL_PREFIX= bash debug_run.sh run_all
# ---------------------------------------------------------------------------
FAB="${FAB:-gf180}"          # -f : プロセス名（target dir の第 1 階層）
VENDOR="${VENDOR:-fd}"       # -v : ベンダ ID（第 2 階層）
REV="${REV:-mcuC7t20240817}" # -r : リビジョン（第 3 階層）
GROUP="${GROUP:-std}"        # -g : cell_group（std / io）
UV="${UV:-5P00}"             # -u : usage_voltage（.lib 名に入る文字列）
CORNER="${CORNER:-TT}"       # -p : process_corner
TEMP="${TEMP:-25.0}"         # -t : 温度
VDD="${VDD:-5.0}"            # --vdd
#--- ISS-00185: well 電圧は charao 側で --vdd/--vss に追従する（--vnw/--vpw の既定は None）。
#    ユーザは --vdd/--vss を指定するだけでよい。 トリプルウェル等で別電位が要る場合のみ
#    VNW/VPW を env で明示する。 ここでは明示時だけオプションを渡す（既定をダブらせない）。
#    ※ 従来は charao の --vnw 既定が 5.0V 固定で、 5V の gf180 では偶然正しかったが
#      1.8V の SKY130 では nwell に 5V ＝ pMOS バルクに 3.2V の逆バイアスが掛かり、
#      rise 側の遅延だけが伸びていた（OSU035 3.3V も同様に 1.7V の逆バイアス）。
VNW_OPT=""; [ -n "${VNW:-}" ] && VNW_OPT="--vnw ${VNW}"
VPW_OPT=""; [ -n "${VPW:-}" ] && VPW_OPT="--vpw ${VPW}"
# CELL_PREFIX: CELLS へ短縮名を渡すときに前置するセル名 prefix
CELL_PREFIX="${CELL_PREFIX-gf180mcu_fd_sc_mcu7t5v0__}"
# MATCH: lrPymRPC の --SOURCE_MATCH に渡す文字列（複数可、OR 判定）。
#   既定は PDK 名。 転送量を削りたくなるが、 モデルの include 連鎖を壊しやすいので注意。
#
#   【SKY130 での実測（2026-07-31）】
#     MATCH=sky130                                    1074 ファイル / 64.6MB
#     libs.tech + sc_hd/spice のみに絞る                390 ファイル /  9.7MB → ★sim 全滅
#     libs.tech + fd_pr/spice + sc_hd/spice           1065 ファイル / 58.2MB（正しい最小構成）
#
#   モデル本体は libs.tech ではなく **libs.ref/sky130_fd_pr/spice/** にあり、
#   libs.tech/ngspice/all.spice が ../../libs.ref/sky130_fd_pr/... を 62 箇所から
#   include している。 fd_pr を外すと ngspice が起動できず returncode=1 で全滅する。
#   結局この PDK では削れるのは他ライブラリ（sram_macros / fd_io / sc_hvl）だけで
#   約 10% にしかならないため、 **既定の MATCH=<FAB> のままでよい**。
#
#   絞り込む場合は「モデルの include 連鎖を実際に追ってから」行うこと。
MATCH="${MATCH:-${FAB}}"

# --- .lib ファイル名は charao の update_name() と同じ規則で組み立てる ---
#     basename = <process><ip_type><usage_voltage><vendor><revision>
#     lib_name = <basename>_<corner><Vx_xx><Cxx>   (ip_type: std->CB / io->P)
_IP_TYPE="CB"; [ "${GROUP}" = "io" ] && _IP_TYPE="P"
_VDD_STR="V$(printf '%.2f' "${VDD}" | tr '.' 'P')"
_TEMP_STR="C$(printf '%.0f' "${TEMP}")"
LIB_FILE="${LIB_FILE:-${FAB}${_IP_TYPE}${UV}${VENDOR}${REV}_${CORNER}${_VDD_STR}${_TEMP_STR}_b00.lib}"

# --- orig .lib（比較用）。 orig を持たない PDK では compare 系を使わない ---
ORIG_LIB="${ORIG_LIB:-${SRC_DIR}/gf180mcuC/libs.ref/gf180mcu_fd_sc_mcu7t5v0/lib/gf180mcu_fd_sc_mcu7t5v0__tt_025C_5v00.lib}"
ORIG_CSV_DIR="${ORIG_CSV_DIR:-tmp/gf180_fd_mcuC7t20240817/tt_025C_5v00}"

_setup_args() {
  _resolve_exec

  INDEX1_OPT=""
  [ -n "${INDEX1}" ] && INDEX1_OPT="--template_index1_only ${INDEX1}"
  INDEX2_OPT=""
  [ -n "${INDEX2}" ] && INDEX2_OPT="--template_index2_only ${INDEX2}"
  MEAS_ONLY_OPT=""
  [ -n "${MEAS_ONLY}" ] && MEAS_ONLY_OPT="--measures_only ${MEAS_ONLY}"
  MYLOGIC_OPT=""
  [ -n "${MYLOGIC}" ] && MYLOGIC_OPT="--mylogic_only ${MYLOGIC}"          # ISS-00169: module 単位でセルを絞る
  WAVE_RAW_OPT=""
  [ -n "${WAVE_RAW}" ] && WAVE_RAW_OPT="--wave_raw"
  # ISS-00205: cell netlist のルートを差し替える（ファイル名は同じまま）。
  #            未指定なら各 std_*.jsonc の "spice_path" を使う。
  SPICE_PATH_OPT=""
  [ -n "${SPICE_PATH}" ] && SPICE_PATH_OPT="--spice_path ${SPICE_PATH}"
  DEBUG_STOP_OPT=""
  [ -n "${DEBUG_STOP}" ] && DEBUG_STOP_OPT="--debug_stop ${DEBUG_STOP}"   # ISS-00118 debug: stop after N sp

  # mylogic_user.py をプロジェクトルート直下から自動検出（v0.9.14 以降は通常不要）
  MYLOGIC_USER_OPT=""
  MYLOGIC_USER_SOURCE=""
  MYLOGIC_USER_MATCH=""
  if [ -f "mylogic_user.py" ]; then
    MYLOGIC_USER_OPT="--mylogic_user mylogic_user.py"
    MYLOGIC_USER_SOURCE="mylogic_user.py"
    MYLOGIC_USER_MATCH="mylogic_user"
  fi

  #--- ISS-00196: EXEC_SCRIPT で「使う charao の出所」を決める（旧 MODE を廃止）。
  #      local_repo … 手元の作業ツリー（未 push の修正を試すとき）
  #      git+pip    … GitHub から pip install（既定。再現性のある実行）
  #      git+clone  … ローカルへ clone してからその dir を pip install
  #                   （非公開リポジトリ向け。lrPya_prj と同じ方式）
  #    実行マシンは EXEC_MACHINE（local / server）で別途決める。
  CHARAO_CMD="python3 -m charao.script.charao"
  case "${EXEC_SCRIPT_}" in
    local_repo)
      # 手元のソースを丸ごと送る。 charao 自体は pip install しない
      REPO_ARG="--REPO_URL jsoncomment=jsoncomment,pydantic=pydantic,numpy=numpy,jinja2=jinja2"
      SOURCE_ARG="--SOURCE ${SRC_DIR} ${TARGET_DIR} ${MYLOGIC_USER_SOURCE} charao"
      # ISS-00172: std_primitives.v はファイル名で指定（--SOURCE_INCLUDE は後方一致）。
      #            ".v" にすると PDK 同梱の *.v（約 2MB）まで巻き込むため。
      SOURCE_INCLUDE_ARG="--SOURCE_INCLUDE .spice .spi .ngspice .sp .jsonc .py .jp2 std_primitives.v"
      SOURCE_MATCH_ARG="--SOURCE_MATCH ${MATCH} ${MYLOGIC_USER_MATCH} charao"
      ;;
    git+pip)
      REPO_ARG="--REPO_URL charao=${CHARAO_GIT}@${CHARAO_TAG}"
      SOURCE_ARG="--SOURCE ${SRC_DIR} ${TARGET_DIR} ${MYLOGIC_USER_SOURCE}"
      SOURCE_INCLUDE_ARG="--SOURCE_INCLUDE .spice .spi .ngspice .sp .jsonc .py std_primitives.v"
      SOURCE_MATCH_ARG="--SOURCE_MATCH ${MATCH} ${MYLOGIC_USER_MATCH}"
      ;;
    git+clone)
      # clone 済みの dir を送り、 サーバ側でそれを pip install する（lrPya 方式）
      REPO_ARG="--REPO_URL charao=${PIP_CLONE_DIR}"
      SOURCE_ARG="--SOURCE ${SRC_DIR} ${TARGET_DIR} ${MYLOGIC_USER_SOURCE} ${PIP_CLONE_DIR}"
      SOURCE_INCLUDE_ARG="--SOURCE_INCLUDE .spice .spi .ngspice .sp .jsonc .py .jp2 .toml std_primitives.v"
      SOURCE_MATCH_ARG="--SOURCE_MATCH ${MATCH} ${MYLOGIC_USER_MATCH} ${PIP_CLONE_DIR#./}"
      ;;
  esac

  # env override: SOURCE_ITEMS で --SOURCE の対象一式を上書き（未指定時は EXEC_SCRIPT 別の既定）
  [ -n "${SOURCE_ITEMS}" ] && SOURCE_ARG="--SOURCE ${SOURCE_ITEMS}"
  #--- ISS-00204: SOURCE_INCLUDE_ITEMS で --SOURCE_INCLUDE を上書きし、 転送量を絞る。
  #    既定は拡張子だけで拾うため sky130A では 59.93MB / 1,215 ファイルを毎回運んでいた
  #    （SRAM マクロ 5.17MB・IO セル 0.79MB・montecarlo 1.22MB・未使用コーナー多数）。
  #    --SOURCE_INCLUDE は **後方一致**なので、 ファイル名をそのまま並べれば個別指定できる。
  [ -n "${SOURCE_INCLUDE_ITEMS}" ] && SOURCE_INCLUDE_ARG="--SOURCE_INCLUDE ${SOURCE_INCLUDE_ITEMS}"
  # env override: RESULT_ITEMS で --RESULT の回収対象を上書き（未指定時は rslt work。例: RESULT_ITEMS="rslt" で work 除外）
  RESULT_ARG="--RESULT ${RESULT_ITEMS:-rslt work}"
}

#--- ISS-00196(a): clean は **RUN_NAME 単位**で消す。
#    以前は `rm -rf run* *.log*` の全消しで、 2026-08-04 に 8/2 の 7h53m 回帰・
#    旧 template 回帰・ログ 13 本を巻き添えで失った（git 管理外で復旧不可）。
#    全消しが要るときは clean_all を CONFIRM=yes 付きで明示的に呼ぶ。
cmd_clean() {
  local targets=()
  [ -d "${RUN_NAME}" ] && targets+=("${RUN_NAME}")
  for f in "lrpymrpc_debug_batch_${RUN_NAME}.log" "lrpymrpc_debug_batch_${RUN_NAME}.log.gz"; do
    [ -f "$f" ] && targets+=("$f")
  done
  if [ ${#targets[@]} -eq 0 ]; then
    echo "clean: 削除対象なし（RUN_NAME=${RUN_NAME}）"
    return
  fi
  echo "===== clean: RUN_NAME=${RUN_NAME} の成果物のみ削除 ====="
  printf '  %s\n' "${targets[@]}"
  set -x
  rm -rf "${targets[@]}"
  { set +x; } 2>/dev/null
}

#--- 全消し。 事故防止のため CONFIRM=yes を要求する（ISS-00196(a)）
cmd_clean_all() {
  local targets=( run* *.log* )
  local n=0
  for t in "${targets[@]}"; do [ -e "$t" ] && n=$((n+1)); done
  if [ "$n" -eq 0 ]; then
    echo "clean_all: 削除対象なし"
    return
  fi
  echo "===== clean_all: 以下を **すべて** 削除します（${n} 件）====="
  for t in "${targets[@]}"; do [ -e "$t" ] && echo "  $t"; done
  if [ "${CONFIRM:-}" != "yes" ]; then
    echo ""
    echo "  中断しました。 実行するには CONFIRM=yes を付けてください:" >&2
    echo "    CONFIRM=yes bash $0 clean_all" >&2
    exit 2
  fi
  set -x
  rm -rf run* *.log*
  { set +x; } 2>/dev/null
}

#=====================================================================
# ISS-00196: 実行の 2 軸を分離する（旧 MODE / EXEC を廃止）
#   EXEC_MACHINE = local | server      … **どのマシンで python を回すか**
#   EXEC_SCRIPT  = local_repo | git+pip | git+clone
#                                      … **どの charao を使うか**
#   CHARAO_TAG   = tag / branch        … git+pip / git+clone のリビジョン
#
# 既定は local + git+pip（一般ユーザ想定＝手元で、再現性のある版を使う）。
# ダーマツ環境では EXEC_MACHINE=server を毎回明示する。
# 開発中（未 push の修正を試す）は EXEC_SCRIPT=local_repo を明示する。
#=====================================================================
CHARAO_GIT="${CHARAO_GIT:-git+https://github.com/MatsudaLogicResearch/charao_prj.git}"
# EXEC_SCRIPT=git+clone の clone 先（ISS-00198）。
#   既定は **RUN_NAME 別**（pip_pkg_<RUN_NAME>）。 RUN_NAME を分ければ clone 先も
#   自動的に分かれるので、 同時実行しても競合しない。 env で明示指定もできる
#   （CHARAO_TAG 別に持ちたいとき等。 例 PIP_CLONE_DIR=pip_pkg_2.0.0.a04）。
#   ※ 先頭の ./ は必須。 pip は「パスらしい引数」（./foo、/abs、foo/bar）だけを
#     ローカルパスとして扱い、 単純な名前（foo）は **パッケージ名として PyPI を探す**。
#     ./ が無いと `pip install pip_pkg_run` が "No matching distribution found" になる。
#   ※ 逆に --SOURCE_MATCH へ渡すときは ./ を外す（${PIP_CLONE_DIR#./}）。
#     tar 内のパスは "pip_pkg_run/..." で ./ を含まないため、 そのまま渡すと
#     フィルタが一致せず pyproject.toml まで除外されてしまう。
PIP_CLONE_DIR="${PIP_CLONE_DIR:-./pip_pkg_${RUN_NAME}}"

_resolve_exec() {
  EXEC_MACHINE_="${EXEC_MACHINE:-local}"
  EXEC_SCRIPT_="${EXEC_SCRIPT:-git+pip}"
  CHARAO_TAG="${CHARAO_TAG:-main}"
  case "$EXEC_MACHINE_" in
    local|server) ;;
    *) echo "EXEC_MACHINE は local / server のいずれか（指定: $EXEC_MACHINE_）" >&2; exit 2 ;;
  esac
  case "$EXEC_SCRIPT_" in
    local_repo|git+pip|git+clone) ;;
    *) echo "EXEC_SCRIPT は local_repo / git+pip / git+clone のいずれか（指定: $EXEC_SCRIPT_）" >&2; exit 2 ;;
  esac

  # local + git+* は **pip 版を使う**。 python -I でカレントを sys.path から外すことで
  # 手元の ./charao/ が勝つのを防ぐ（3.10 でも -I は script's dir / カレントを除外する）。
  PY_ISOLATE=""
  if [ "$EXEC_MACHINE_" = "local" ] && [ "$EXEC_SCRIPT_" != "local_repo" ]; then
    PY_ISOLATE="-I"
  fi
}

# clone / pip install を用意する（冪等）。 EXEC_SCRIPT ごとに必要な準備だけ行う。
_prepare_script() {
  case "$EXEC_SCRIPT_" in
    local_repo) ;;
    git+clone)
      #--- clone 先は RUN_NAME 別（pip_pkg_<RUN_NAME>）なので同時実行でも競合しない。
      #    既存 clone が別の TAG なら作り直す（.git の有無だけだと古いものを使い続ける）。
      _have=""
      if [ -d "${PIP_CLONE_DIR}/.git" ]; then
        _have=$(git -C "${PIP_CLONE_DIR}" describe --tags --exact-match 2>/dev/null \
                || git -C "${PIP_CLONE_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
      fi
      if [ "${_have}" != "${CHARAO_TAG}" ]; then
        echo "===== clone: ${CHARAO_GIT#git+} @ ${CHARAO_TAG} -> ${PIP_CLONE_DIR}${_have:+（既存 ${_have} を作り直し）} ====="
        rm -rf "${PIP_CLONE_DIR}"
        set -x
        git clone --depth 1 --branch "${CHARAO_TAG}" "${CHARAO_GIT#git+}" "${PIP_CLONE_DIR}"
        { set +x; } 2>/dev/null
      fi
      if [ "$EXEC_MACHINE_" = "local" ]; then _pip_install_local "${PIP_CLONE_DIR}"; fi
      ;;
    git+pip)
      if [ "$EXEC_MACHINE_" = "local" ]; then _pip_install_local "${CHARAO_GIT}@${CHARAO_TAG}"; fi
      ;;
  esac
}

# local 実行用に charao を venv へ入れる（既に同じものが入っていれば何もしない）
_pip_install_local() {
  local src="$1"
  #--- ISS-00198: 同時実行では複数ジョブが同じ venv へ pip install して競合する。
  #    flock で直列化し、 ロック取得後に改めて import 可否を確認する。
  mkdir -p tmp
  (
    flock 9
    if ! python -I -c "import charao" 2>/dev/null; then
      echo "===== pip install ${src}（local 実行用）====="
      set -x
      python -m pip install "$src"
      { set +x; } 2>/dev/null
    fi
  ) 9>tmp/.pip.lock
}

# ── python 実行はここ 1 箇所 ────────────────────────────────────────────
# 呼び出し前に以下をセットする（server 実行時のみ使う）:
#   PY_SRC / PY_RSLT / PY_INC / PY_MATCH / PY_LOG / PY_RUN_NAME_OPT
# _py_run <module> <args...>
_py_run() {
  _prepare_script
  if [ "$EXEC_MACHINE_" = "local" ]; then
    set -x
    # ISS-00135: ローカル実行は最低優先度で（前面の対話・他作業へ CPU を譲る）
    # PY_ISOLATE=-I のとき、 カレントの ./charao/ ではなく pip 版が使われる
    if [ -n "${PY_LOG:-}" ]; then
      nice -n 19 python -u ${PY_ISOLATE} -m "$@" 2>&1 | tee "$PY_LOG"
    else
      nice -n 19 python -u ${PY_ISOLATE} -m "$@"
    fi
    { set +x; } 2>/dev/null
    return
  fi
  # server 実行（lrPymRPC 経由）。 sim も util もここを通る
  local log="${PY_LOG:-lrpymrpc_run.log}"
  set -x
  python -u -m lrPymRPC \
    --SERVER_IP 192.168.168.103 \
    $REPO_ARG \
    --SOURCE $PY_SRC \
    --SOURCE_INCLUDE $PY_INC \
    --SOURCE_MATCH $PY_MATCH \
    ${PY_RUN_NAME_OPT} \
    --RESULT $PY_RSLT \
    --CMD "python3 -m $*" 2>&1 | tee "$log"
  { set +x; } 2>/dev/null
}

# _charao_run <ログ名> <cells_only の中身（空可）>
#   sim 中は非圧縮 .log に逐次書き込み（tail -f で進捗確認可）、 取得完了後に gzip 圧縮。
_charao_run() {
  PY_LOG="$1"
  local cells_opt="$2"
  PY_SRC="${SOURCE_ARG#--SOURCE }"
  PY_INC="${SOURCE_INCLUDE_ARG#--SOURCE_INCLUDE }"
  PY_MATCH="${SOURCE_MATCH_ARG#--SOURCE_MATCH }"
  PY_RSLT="${RESULT_ARG#--RESULT }"
  PY_RUN_NAME_OPT=""
  [ -n "${RUN_NAME}" ] && PY_RUN_NAME_OPT="--RUN_NAME ${RUN_NAME}"
  #--- ISS-00198: local 実行は lrPymRPC の作業 dir 分離が効かないため、 charao の
  #    出力先を直接 <RUN_NAME>/ 配下へ向ける（これで local でも並列実行できる）。
  #    server 実行では リモートの /tmp/lrpymrpc/<uuid>/ が分離しており、 回収は
  #    --RUN_NAME が行うので指定しない（従来どおり ./rslt / work を使う）。
  #    ※ work_dir は **work と同じ階層でなければならない**（ISS-00198 で判明）。
  #      charao は work_dir へ chdir してから ngspice を起動するが、 モデルファイル内の
  #      相対 include（../../../../sample_src/...）が「work_dir は 1 階層」を前提に
  #      書かれており、 <RUN_NAME>/work にすると 1 階層ずれて model が見つからず全滅する。
  #      そのため sim 中は work_<RUN_NAME>（同じ階層）を使い、 完了後に <RUN_NAME>/work へ移す。
  #      result_path は chdir の対象ではないので <RUN_NAME>/rslt を直接指定できる。
  local OUT_OPT="" WORK_TMP=""
  if [ "$EXEC_MACHINE_" = "local" ] && [ -n "${RUN_NAME}" ]; then
    WORK_TMP="work_${RUN_NAME}"
    OUT_OPT="--result_path ${RUN_NAME}/rslt --work_dir ${WORK_TMP}"
  fi
  _py_run charao.script.charao \
    -f "${FAB}" -v "${VENDOR}" -r "${REV}" -g "${GROUP}" -u "${UV}" -p "${CORNER}" \
    -t "${TEMP}" --vdd "${VDD}" ${VNW_OPT} ${VPW_OPT} --target "${TARGET_DIR}" \
    ${cells_opt} ${MYLOGIC_OPT} ${INDEX1_OPT} ${INDEX2_OPT} ${MEAS_ONLY_OPT} \
    ${WAVE_RAW_OPT} ${DEBUG_STOP_OPT} ${MYLOGIC_USER_OPT} ${SPICE_PATH_OPT} ${OUT_OPT}

  #--- sim 中は同じ階層に置いた work を、 完了後に <RUN_NAME>/work へ移す
  #    （server 実行時の配置と揃える。 移動なので並列実行でも衝突しない）
  if [ -n "${WORK_TMP}" ] && [ -d "${WORK_TMP}" ]; then
    mkdir -p "${RUN_NAME}"
    rm -rf "${RUN_NAME}/work"
    mv "${WORK_TMP}" "${RUN_NAME}/work"
  fi
}

# _run_summary <表示名> <ログ> <.lib パス>
#   ISS-00196(c): ngspice の失敗だけでなく **生成物の実在**まで見る。
#   2026-08-05 の真打ちで seq_lat が lrPymRPC の通信断（gRPC Connection reset by peer）で
#   1h06m 走った末に成果物ゼロだったが、 集計は「0 failures」と表示された。
_run_summary() {
  local name="$1" log="$2" lib="$3"
  local n t cells
  n=$(grep -c "Failed to launch spice" "$log" 2>/dev/null || true)
  t=$(grep -c "Traceback (most recent call last)" "$log" 2>/dev/null || true)
  [ -z "$n" ] && n=0
  [ -z "$t" ] && t=0
  if [ -f "$lib" ]; then
    cells=$(grep -c "^  cell (" "$lib" 2>/dev/null || echo 0)
  else
    cells="-"
  fi
  printf "  %-20s : %s failures / %s traceback / .lib %s cells\n" "$name" "$n" "$t" "$cells"
  if [ ! -f "$lib" ]; then
    echo "  [WARN] .lib が生成されていない: $lib" >&2
    echo "         （通信断・charao の異常終了の可能性。 log の Traceback を確認すること）" >&2
  fi
}

cmd_run_all() {
  _setup_args
  local CELLS_OPT=""
  if [ -n "${CELLS}" ]; then
    local CELLS_FULL=""
    for s in $CELLS; do
      CELLS_FULL="${CELLS_FULL} ${CELL_PREFIX}${s}"
    done
    CELLS_OPT="--cells_only${CELLS_FULL}"
  fi
  echo "===== run_all: EXEC=${EXEC_MACHINE_}/${EXEC_SCRIPT_} CELLS='${CELLS:-<all>}' MYLOGIC='${MYLOGIC:-<all>}' INDEX1='${INDEX1:-<all>}' INDEX2='${INDEX2:-<all>}' RUN_NAME='${RUN_NAME:-}' (batch) ====="
  local RSLT_PATH="${RUN_NAME:+$RUN_NAME/}rslt"
  local WORK_PATH="${RUN_NAME:+$RUN_NAME/}work"
  rm -rf "$RSLT_PATH" "$WORK_PATH"
  local LOG="lrpymrpc_debug_batch${RUN_NAME:+_$RUN_NAME}.log"
  _charao_run "$LOG" "$CELLS_OPT"
  echo ""
  echo "===== summary: run result ====="
  _run_summary "batch${RUN_NAME:+_$RUN_NAME}" "$LOG" "${RSLT_PATH}/${LIB_FILE}"
  if [ -f "$LOG" ]; then gzip -f "$LOG"; fi
}

cmd_run_each() {
  _setup_args
  if [ -z "${CELLS}" ]; then
    echo "run_each requires CELLS to be set (per-cell loop)" >&2
    exit 2
  fi
  echo "===== run_each: EXEC=${EXEC_MACHINE_}/${EXEC_SCRIPT_} CELLS='${CELLS}' INDEX1='${INDEX1:-<all>}' INDEX2='${INDEX2:-<all>}' RUN_NAME='${RUN_NAME:-}' (per-cell) ====="
  for short in $CELLS; do
    local full="${CELL_PREFIX}${short}"
    echo "=========================================="
    echo "===== running cell: ${short}"
    echo "=========================================="
    local RSLT_PATH="${RUN_NAME:+$RUN_NAME/}rslt"
    local WORK_PATH="${RUN_NAME:+$RUN_NAME/}work"
    local RSLT_DEST="${RUN_NAME:+$RUN_NAME/}rslt_${short}"
    local WORK_DEST="${RUN_NAME:+$RUN_NAME/}work_${short}"
    rm -rf "$RSLT_PATH" "$WORK_PATH" "$RSLT_DEST" "$WORK_DEST"
    local LOG="lrpymrpc_debug${RUN_NAME:+_$RUN_NAME}_${short}.log"
    _charao_run "$LOG" "--cells_only ${full}"
    [ -d "$WORK_PATH" ] && mv "$WORK_PATH" "$WORK_DEST"
    [ -d "$RSLT_PATH" ] && mv "$RSLT_PATH" "$RSLT_DEST"
  done
  echo ""
  echo "===== summary: run result ====="
  for short in $CELLS; do
    local LOG="lrpymrpc_debug${RUN_NAME:+_$RUN_NAME}_${short}.log"
    _run_summary "$short" "$LOG" "${RUN_NAME:+$RUN_NAME/}rslt_${short}/${LIB_FILE}"
    if [ -f "$LOG" ]; then gzip -f "$LOG"; fi
  done
}

# _util_run <タグ> <SOURCE 群> -- <RESULT 群> -- <module> <args...>
#   util（merge / lib2csv / compare）用のラッパ。 sim と同じ _py_run を通す。
#   ※ lrPymRPC の --RESULT は **トップレベル名しか回収できない**（サブパスだと空 tar が
#     返り、 エラーも警告も出ずに何も落ちてこない）。 呼び出し側でトップレベル名を渡すこと。
_util_run() {
  _resolve_exec
  local tag="$1"; shift
  local src="" rslt="" phase=0 args=()
  for a in "$@"; do
    if [ "$a" = "--" ]; then phase=$((phase+1)); continue; fi
    case $phase in
      0) src="$src $a" ;;
      1) rslt="$rslt $a" ;;
      2) args+=("$a") ;;
    esac
  done
  #--- ISS-00198: EXEC_SCRIPT に応じて charao の入手方法（REPO_ARG）と --SOURCE を決める。
  #    以前は REPO_ARG を設定しておらず、 util の git+pip / git+clone は --REPO_URL が
  #    空のまま走っていた（＝サーバ側で charao が入らず、 検証になっていなかった）。
  case "${EXEC_SCRIPT_}" in
    local_repo)
      REPO_ARG="--REPO_URL jsoncomment=jsoncomment,pydantic=pydantic,numpy=numpy,jinja2=jinja2"
      src="$src charao" ;;
    git+pip)
      REPO_ARG="--REPO_URL charao=${CHARAO_GIT}@${CHARAO_TAG}" ;;
    git+clone)
      REPO_ARG="--REPO_URL charao=${PIP_CLONE_DIR}"
      src="$src ${PIP_CLONE_DIR}" ;;
  esac
  PY_SRC="$src"
  PY_RSLT="$rslt"
  PY_INC=".lib .v .md .py .csv .toml"
  PY_MATCH="${MATCH} charao rslt merged csv tmp ${PIP_CLONE_DIR#./}"
  #--- ISS-00198: server 実行では --RUN_NAME を渡す。 渡さないと lrPymRPC の
  #    _source.tar.gz / _result.tar.gz が **カレント固定**になり、 同時実行で奪い合って
  #    `tarfile.ReadError: empty file` になる（ダーマツ指摘）。
  #    ただし --RUN_NAME を渡すと結果も <RUN_NAME>/ 配下へ展開されるので、 回収後に戻す。
  PY_RUN_NAME_OPT=""
  if [ "$EXEC_MACHINE_" = "server" ] && [ -n "${RUN_NAME}" ]; then
    PY_RUN_NAME_OPT="--RUN_NAME ${RUN_NAME}"
  fi
  # ログ名も RUN_NAME で分ける（固定名だと同時実行で奪い合い、
  # 先に gzip した側で消えて他が "No such file" で落ちる）
  PY_LOG="lrpymrpc_${tag}${RUN_NAME:+_$RUN_NAME}.log"
  _py_run "${args[@]}"
  if [ "$EXEC_MACHINE_" = "server" ]; then
    #--- --RUN_NAME 指定で <RUN_NAME>/<出力> に落ちたものを、 本来の場所へ戻す
    if [ -n "${PY_RUN_NAME_OPT}" ]; then
      for r in $rslt; do
        if [ -e "${RUN_NAME}/${r}" ]; then
          mkdir -p "$(dirname "$r")"
          rm -rf "$r"
          mv "${RUN_NAME}/${r}" "$r"
        fi
      done
    fi
    echo ""
    printf "  %-24s : %s traceback\n" "$tag" \
           "$(grep -c 'Traceback (most recent call last)' "$PY_LOG" 2>/dev/null || echo 0)"
    gzip -f "$PY_LOG"
  fi
}

cmd_lib2csv() {
  local lib="${LIB:-${MERGED_DIR:-merged}/${LIB_FILE}}"
  local out="${CSV_OUT:-tmp/charao_${RUN_NAME}}"
  echo "===== lib2csv[${EXEC_MACHINE:-local}/${EXEC_SCRIPT:-git+pip}]: ${lib} -> ${out} ====="
  [ -f "$lib" ] || { echo "lib2csv: .lib が無い: $lib（先に merge か、LIB= で指定）" >&2; exit 2; }
  # orig .lib は不変なので、 既に CSV があれば作り直さない（作り直すなら rm -rf してから）
  if [ "${SKIP_IF_EXISTS:-1}" = "1" ] && [ -f "${out}/timing.csv" ]; then
    echo "  既存の CSV を再利用（作り直すには rm -rf ${out}）"
    return
  fi
  rm -rf "$out"
  # lrPymRPC の --RESULT は **トップレベルのディレクトリ名**しか回収できない
  #（"tmp/charao_x" のようなサブパスを渡すと空の tar が返り、 静かに何も落ちてこない）。
  # そのため出力の先頭要素を --RESULT に渡す。
  _util_run "lib2csv" \
    "${lib%%/*}" charao -- "${out%%/*}" -- \
    charao.script.util_extract_lib2csv --lib "$lib" --out "$out"
}

cmd_compare() {
  local new="${CSV_NEW:-tmp/charao_${RUN_NAME}}"
  local orig="${ORIG_CSV_DIR}"
  local name="${RUN_NAME}"
  echo "===== compare[${EXEC_MACHINE:-local}/${EXEC_SCRIPT:-git+pip}]: ${new} vs ${orig} ====="
  [ -d "$orig" ] || { echo "compare: orig CSV が無い: $orig（先に lib2csv）" >&2; exit 2; }
  [ -d "$new" ]  || { echo "compare: charao CSV が無い: $new（先に lib2csv）" >&2; exit 2; }
  local INTERP_OPT=""
  [ "${COMPARE_INTERPOLATE:-1}" = "1" ] && INTERP_OPT="--interpolate"
  # 全 index 実行（INDEX1/INDEX2 とも未設定）なら 0 値も採用（drop_zero_new=False）
  local KEEP_ZERO_OPT=""
  [ -z "${INDEX1}" ] && [ -z "${INDEX2}" ] && KEEP_ZERO_OPT="--keep_zero_new"
  # 出力はリポジトリ直下に置く（.gitignore の compare_* で除外済み）。
  # lrPymRPC の --RESULT はトップレベル名しか回収できないため（サブパスだと空 tar）。
  rm -f "compare_${name}.csv" "compare_${name}.summary.txt"
  _util_run "compare" \
    tmp charao -- "compare_${name}.csv" "compare_${name}.summary.txt" -- \
    charao.script.util_compare_csv --orig "$orig" --new "$new" \
      $INTERP_OPT $KEEP_ZERO_OPT --out_csv "compare_${name}.csv"
}

cmd_merge() {
  # 入力は MERGE_DIRS で明示指定できる（mylogic 別バッチの rslt/ を統合する用途）。
  # 未指定なら従来どおり run_each の <RUN_NAME>/rslt_* を拾う。
  local dirs="${MERGE_DIRS:-}"
  local out="${MERGED_DIR:-${RUN_NAME:+$RUN_NAME/}merged}"
  if [ -z "$dirs" ]; then
    local glob="${RUN_NAME:+$RUN_NAME/}rslt_*"
    local d=( $glob )
    if [ ! -d "${d[0]}" ]; then
      echo "merge: no ${glob}/ found（run_each の出力が無い。MERGE_DIRS で明示指定も可）" >&2
      exit 2
    fi
    dirs="$glob"
  fi
  echo "===== merge[${EXEC_MACHINE:-local}/${EXEC_SCRIPT:-git+pip}]: ${dirs} -> ${out} ====="
  rm -rf "$out"
  # SOURCE には入力 dir の親を渡す（rslt 単体だと階層が壊れる）
  local srcs=""
  for d in $dirs; do srcs="$srcs ${d%%/*}"; done
  # ISS-00171: util_merge は --out_dir + 入力ディレクトリ群（先頭がベース、以降が順次上書き更新）
  _util_run "merge" \
    $srcs charao -- "$out" -- \
    charao.script.util_merge --out_dir "$out" $dirs
}

usage() {
  cat <<EOF
Usage: $0 <clean|clean_all|run_all|run_each|merge|lib2csv|compare> ...
  clean          : **RUN_NAME 単位**で削除（<RUN_NAME>/ と そのログ）
  clean_all      : run* / *.log* を全削除。 事故防止のため CONFIRM=yes が必要
  run_all        : lrPymRPC charao run (batch: single invocation, single log)
  run_each       : lrPymRPC charao run (per-cell: loop over CELLS, per-cell log/work archive)
  merge          : rslt 群の .lib/.v/.md を 1 本へ統合（MERGE_DIRS で入力指定、既定 <RUN_NAME>/rslt_*）
  lib2csv        : .lib 1 本 -> CSV（LIB / CSV_OUT で指定。既定 <MERGED_DIR>/<LIB_FILE> -> tmp/charao_<RUN_NAME>）
  compare        : charao CSV vs orig CSV -> compare_<RUN_NAME>.csv（リポジトリ直下）

  EXEC=local|remote  : merge / lib2csv / compare の実行先（既定 local）。
                       remote は lrPymRPC 経由でサーバ上の python を使い、ローカル CPU を空ける。

  典型フロー:
    MERGE_DIRS="run_a/rslt run_b/rslt" MERGED_DIR=merged EXEC=remote bash $0 merge
    LIB="\$ORIG_LIB" CSV_OUT="\$ORIG_CSV_DIR" EXEC=remote bash $0 lib2csv   # orig（初回のみ）
    EXEC=remote bash $0 lib2csv compare                                      # charao 側 + 比較

Env vars (all optional):
  --- 実行の 2 軸（ISS-00196。旧 MODE / EXEC は廃止）---
  EXEC_MACHINE=local|server            **どのマシンで python を回すか**（既定 local）
                                       local  = 手元（nice -n 19）
                                       server = lrPymRPC 経由（192.168.168.103）
  EXEC_SCRIPT=local_repo|git+pip|git+clone
                                       **どの charao を使うか**（既定 git+pip）
                                       local_repo = 手元の作業ツリー（未 push の修正を試す）
                                       git+pip    = GitHub から pip install（再現性のある実行）
                                       git+clone  = clone してその dir を pip install（非公開 repo 向け）
  CHARAO_TAG=main                      git+pip / git+clone のリビジョン（tag / branch）

  ※ EXEC_MACHINE=local かつ EXEC_SCRIPT=git+* のときは python -I で起動し、
    カレントの ./charao/ ではなく pip 版を使う（-I はカレントを sys.path から外す）。
  ※ sim（run_all/run_each）も util（merge/lib2csv/compare）も同じ経路（_py_run）を通る。

  --- sim の絞り込み ---
  CELLS="short1 short2..."  (unset = all cells; no --cells_only)
  MYLOGIC="comb_base ..."   (unset = all modules; no --mylogic_only)
  INDEX1="0 9"              (unset = all idx1;   no --template_index1_only)
  INDEX2="0 9"              (unset = all idx2;   no --template_index2_only)
  MEAS_ONLY="delay ..."     (unset = all measures)
  WAVE_RAW=1                波形（.raw）を残す
  RESULT_ITEMS="rslt work"  回収対象（既定 rslt work。"rslt" で work を除外＝転送削減）

  --- merge / lib2csv / compare の入出力 ---
  MERGE_DIRS="a/rslt b/rslt"  merge の入力（未指定なら <RUN_NAME>/rslt_*）
  MERGED_DIR="merged"         merge の出力（既定 <RUN_NAME>/merged）
  LIB / CSV_OUT               lib2csv の入力 .lib / 出力 CSV dir
  CSV_NEW                     compare の charao 側 CSV dir（既定 tmp/charao_<RUN_NAME>）
  SKIP_IF_EXISTS=0|1          lib2csv: 既存 CSV があれば作り直さない（既定 1）
  CONFIRM=yes                 clean_all を実際に実行するために必要

Examples:
  # all cells, 2x2 corners, local, batch + extract + compare
  INDEX1="0 9" INDEX2="0 9" EXEC_MACHINE=server EXEC_SCRIPT=local_repo bash $0 clean run_all merge lib2csv compare

  # 6 cells per-cell, 2x2 corners, then extract + compare
  CELLS="and4_2 and4_4 mux2_1 nand4_2 nor3_2 nor4_1" INDEX1="0 9" INDEX2="0 9" EXEC_MACHINE=server EXEC_SCRIPT=local_repo bash $0 clean run_each merge lib2csv compare

  # first-time setup: generate orig CSV, then charao run + extract + compare
  LIB="\$ORIG_LIB" CSV_OUT="\$ORIG_CSV_DIR" bash $0 lib2csv
  INDEX1="0 9" INDEX2="0 9" EXEC_MACHINE=server EXEC_SCRIPT=local_repo bash $0 run_all merge lib2csv compare
EOF
  exit 1
}

[ $# -eq 0 ] && usage

#--- EXEC_MACHINE / EXEC_SCRIPT の妥当性を先に検証する（不正値で走り出さない）
_resolve_exec

for arg in "$@"; do
  case "$arg" in
    clean)          cmd_clean ;;
    clean_all)      cmd_clean_all ;;
    run_all)        cmd_run_all ;;
    run_each)       cmd_run_each ;;
    lib2csv)        cmd_lib2csv ;;
    compare)        cmd_compare ;;
    merge)          cmd_merge ;;
    *) echo "unknown arg: $arg" >&2; usage ;;
  esac
done
