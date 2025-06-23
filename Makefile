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
.SUFFIXES: .cmd .md .sp

PROCESS_NAME := OSU350
#PROCESS_NAME := VIS500MM
#PROCESS_NAME := NISD_BiM16_F

CELL_NAME := SAMPLE

PROCESS      := 1.0
CONDITION    := TCCOM
VDD  				 := 5.0
SPEED				 := TT
TEMP 				 := 25

#===========================================================
#for rpc_make
SOURCEDIR     := "cell script model"
#RESULTDIR     := "timing work"
RESULTDIR     := "timing"
REMOTE 				:= 0
#===========================================================

LIBRETTO	= script/libretto.py
GEN_CMD		= cell/$(PROCESS_NAME)/$(CELL_NAME)/gen_cmd.py

CMD_FILE	= cmd/libretto.cmd
#------------------------------------------------

#---- change value of VDD/TEMP 
VDD_STR      := $(subst .,P,$(VDD))V
TEMP_STR     := $(subst -,M,$(TEMP))C


LIB_NAME    := $(PROCESS_NAME)_$(CELL_NAME)_$(VDD_STR)_$(TEMP_STR)
PATH_MODEL  := model/$(PROCESS_NAME)/model_$(PROCESS_NAME)_$(SPEED).sp
PATH_CELL   := cell/$(PROCESS_NAME)/$(CELL_NAME)/CELL
MD          := timing/$(LIB_NAME).md
PDF         := timing/$(LIB_NAME).pdf
LIB         := timing/$(LIB_NAME).lib 
VERILOG     := timing/$(PROCESS_NAME).v

#========================================================================
.PHONY: all prep

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
all:$(LIB) $(VERILOG) $(PDF) 

endif



$(PDF):$(MD) 
	/bin/pandoc $(MD) -o $@ -V documentclass=ltjarticle --pdf-engine=lualatex -V geometry:margin=1in -N --toc -V secnumdepth=4;

$(LIB):prep
	python3 $(GEN_CMD) --vdd $(VDD) --temp  $(TEMP) --process $(PROCESS) --condition $(CONDITION) \
		--p_name $(PROCESS_NAME) --lib_name $(LIB_NAME)  \
		--path_model $(PATH_MODEL) --path_cell $(PATH_CELL);

	time python3 $(LIBRETTO) -b $(CMD_FILE);

	\mv -f $(LIB_NAME).* $(PROCESS_NAME).v timing/;

%.pdf:%.md

prep:
	\rm -rf work cmd ;\
	\mkdir -p work cmd timing;\

lc:
	lc_shell -f tcl/run_lc.tcl 

clean:
	\rm -rf work log.txt  cat_run.sh cmd/* script/__pycache__  *.db *.lib *.v *.log *.md *.pdf __tmp__

clean_all:clean
	\rm -rf timing

test:
	echo "OK"

