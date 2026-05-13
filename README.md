Overview

This repository contains the code used to prepare the Low-Frame-Rate Cell Tracking (LFCT) benchmark dataset. The pipeline takes a TrackMate annotation XML file and the raw phase-contrast and nuclear fluorescence frames as input. It extracts spot and lineage information, sparsifies the annotations at GAP factors 2, 4, and 8, generates lineage trees, and merges the two channels into a video for each sparsification level.

Annotation Extraction
The TrackMate XML annotations are converted into a CSV table to simplify downstream processing. Each row in the CSV represents one cell detection at one frame.

Input: TrackMate XML file (FLD_3.xml)
Output: CSV file with one row per spot
Columns: spot ID, frame, track ID, parent spot ID, position (x, y), and all other spot attributes from TrackMate

Script: 01_xml_to_csv.py



