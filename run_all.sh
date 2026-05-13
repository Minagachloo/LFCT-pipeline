#!/bin/bash
set -e
cd "$(dirname "$0")"

python3 Code/01_xml_to_csv.py
python3 Code/02_sparsify.py
python3 Code/03_lineage.py
python3 Code/04_video.py

echo
echo "Done. Outputs are in Output/."
