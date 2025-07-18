#===========================================================
# cell/<PROCESS_NAME>/<CELL_NAME>/gen_cmd.py is command-generator for libretto.py
#
#   script: cell/<PROCESS_NAME>/<CELL_NAME>/gen_cmd.py  <-- set process & spice model .
#   output: cmd/libretto.cmd
#
# libretto.py is spice simulator with ngspice/hspice.
#
#   script: script/libretto.py
#   input:  cmd/libretto.cmd
#           cell/<PROCESS_NAME>/<CELL_NAME>/CELL/*.spi 
#   output: tming/<PROCESS_NAME>.v
#           tming/<PROCESS_NAME>_<CELL_NAME>_<VDD>_<TEMP>.lib .pdf
# 
#===========================================================
# 01: prepare std-cell
#     --> create & edit MOS model replace.sh in cell/<PROCESS_NAME>/<CELL_NAME>
#     --> generate spice file by  replace.sh in cell/<PROCESS_NAME>/<CELL_NAME> from CELL_BASE to CALL.
#
# 02: select std-cell, spice model,,,,
#     --> create & edit gen_cmd.py in cell/<PROCESS_NAME>/<CELL_NAME>
#     --> prapare MOS model(include file) as cell/model_<PROCESS_NAME>_<SPEED>.sp
#     --> generate cmd/libretto.cmd from cell/<PROCESS_NAME>/<CELL_NAME>/gen_cmd.py
#
# 03: characterization
#     --> make PROCESS_NAME=<PROCESS_NAME> CELL_NAME=<CELL_NAME> CONDITION=<CONDITION> VDD=<VDD> SPEED=<SPEED> TEMP=<TEMP>
#     --> output timing/<PROCESS_NAME>_<CELL_NAME>_<VDD>_<TEMP>.v .lib .md .pdf
#===========================================================

.SUFFIXES:
.SUFFIXES: .md .sp

FAB_PROCESS := OSU035
CELL_VENDOR := SAMPLE

CONDITION    := TT
PROCESS      := 1.0
TEMP 				 := 25
VDD  				 := 5.0
VSS  				 := 0.0
VNW  				 := 5.0
VPW  				 := 0.0

#===========================================================
#for rpc_make
SOURCEDIR     := "target script"
#RESULTDIR     := "timing work"
RESULTDIR     := "timing"
REMOTE 				:= 0
#===========================================================

LIBRETTO	= script/libretto.py
#------------------------------------------------
#========================================================================
.PHONY: all prep lib pdf clean finish

ifeq ($(REMOTE),1)
all:
	python3 /home/ldapusers/matsuda/project/DESIGN_ASSETS/8.tools/rpc/rpc_make/rpc_make_client.py \
	--SERVER_IP "192.168.168.103" \
	--SERVER_PORT "8765" \
	--TOOL libretto \
	--TARGET all PROCESS_NAME=$(PROCESS_NAME) CELL_NAME=$(CELL_NAME) PROCESS=$(PROCESS) CONDITION=$(CONDITION) VDD=$(VDD) SPEED=$(SPEED) TEMP=$(TEMP) \
	--SOURCE "$(SOURCEDIR)" \
	--RESULT "$(RESULTDIR)";

else
all:finish

endif

finish:pdf
	mv *.lib *.v *.pdf *.md timing/

pdf:lib
	@for f in $(wildcard *.md); do \
	  [ -e "$$f" ] && /bin/pandoc "$$f" -o  "$${f%.md}.pdf" -V documentclass=ltjarticle --pdf-engine=lualatex -V geometry:margin=1in -N --toc -V secnumdepth=4; \
	done

lib:prep
	time python3 $(LIBRETTO) -f $(FAB_PROCESS) -v $(CELL_VENDOR) --condition $(CONDITION) --process $(PROCESS) --temp $(TEMP) --vdd $(VDD) --vss $(VSS) --vnw $(VNW) --vpw $(VPW)

prep:
	\rm -rf work *.v *.md *.lib;\
	\mkdir -p work timing;\

lc:
	lc_shell -f tcl/run_lc.tcl 

clean:
	\rm -rf work log.txt  cat_run.sh script/__pycache__  *.db *.lib *.v *.log *.md *.pdf __tmp__

clean_all:clean
	\rm -rf timing

test:
	echo "OK"

