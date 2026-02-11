
pandoc: https://github.com/jgm/pandoc.git

## installation

`sudo apt install pandoc`

## usage

convert markdown to docx: `pandoc --from/-f markdown --to/-t docx --reference-doc </path/to/custom-reference.docx> </path/to/src/file.md> --output/-o </path/to/output.docx>`