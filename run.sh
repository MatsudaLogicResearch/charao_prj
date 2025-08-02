#!/usr/bin/bash
FAB_PROCESS="TOKAI_IP62"
VENDOR="ALEX"
USAGE_VOLTAGE="5.0"
CELL_GROUP="std"

PROCESS_CORNER="TT"
TEMP="25.0"
VDD="5.0"
VNW="5.0"

OPTION=""
#OPTION="--cells_only INV_X1"

## generate liberty
time python3 script/libretto.py -g ${CELL_GROUP} -f ${FAB_PROCESS} -v ${VENDOR} -u ${USAGE_VOLTAGE} \
				-p ${PROCESS_CORNER} -t ${TEMP} --vdd ${VDD} --vnw ${VNW} \
				${OPTION}


# create pdf
for md in ./*.md; do
  echo "  convert ${md} -> ${md%.md}.pdf"
  /bin/pandoc ${md} -o  ${md%.md}.pdf -V documentclass=ltjarticle --pdf-engine=lualatex -V geometry:margin=1in -N --toc -V secnumdepth=4; 
done

# move files
for f in ./${FAB_PROCESS}_${VENDOR}*; do
  echo "  mv ${f} -> ./timing/"
	mv ${f} timing/
done
# EOF

