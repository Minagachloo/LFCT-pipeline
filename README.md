Overview

This repository contains the code used to prepare the Low-Frame-Rate Cell Tracking (LFCT) benchmark dataset. The pipeline takes a TrackMate annotation XML file and the raw phase-contrast and nuclear fluorescence frames as input. It extracts spot and lineage information, sparsifies the annotations at GAP factors 2, 4, and 8, generates lineage trees, and merges the two channels into a video for each sparsification level.

Annotation extraction
The TrackMate annotations are stored in a complex XML file with separate sections for spots, edges, and tracks. To make this information easier to use in the next steps, we convert the XML into a single CSV file where each row corresponds to one cell at one frame. The CSV includes the position, frame, track ID, and the parent spot ID. The parent links are taken from the edges section. This is implemented in 01_xml_to_csv.py.
