#!/usr/bin/env bash
if [[ -z $1 ]]; then
    echo "usage: ./make_booklet.sh <inputfile.tex>"
    exit
fi



latexmk -lualatex $1
tex_basename=$(basename $1)
pdf_basename="${tex_basename/tex/pdf}"
latexmk -lualatex -usepretex="\def\filename{$pdf_basename}" bookletize.tex
latexmk -c

echo $tex_basename
echo $pdf_basename
echo "now you can run:"
echo
echo "    open bookletize.pdf"
echo
echo "to view the booklet"

