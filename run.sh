#!/usr/bin/bash
OPTION=""
#OPTION="--cells_only INV_X1 --measures_only passive"

## generate liberty
time python3 script/charao.py -f OSU035     -v SAMPLE -g std -u 5.0 -p TT -t 25 --vdd 5.0 ${OPTION}
#time python3 script/charao.py -f TOKAI_IP62 -v LR     -g std -u 5.0 -p TT -t 25 --vdd 5.0 ${OPTION}
#time python3 script/charao.py -f TOKAI_IP62 -v LR     -g io  -u 5.0 -p TT -t 25 --vdd 5.0 ${OPTION}
				

# create pdf
for md in ./*.md; do
  echo "  convert ${md} -> ${md%.md}.pdf"
  /bin/pandoc ${md} -o  ${md%.md}.pdf -V documentclass=ltjarticle --pdf-engine=lualatex  -V tables-alignment=left -V geometry:margin=1in -N --toc -V secnumdepth=4; 
done

# move files
mkdir -p timing
for f in *.lib *.v *.md *.pdf ; do
  echo "  mv ${f} -> ./timing/"
	mv ${f} timing/
done
# EOF

