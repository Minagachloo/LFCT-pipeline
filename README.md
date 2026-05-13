# LFCT-Pipeline: A Pipeline for the Low-Frame-Rate Cell Tracking Benchmark Dataset

## Overview

LFCT (Low-Frame-Rate Cell Tracking) is a benchmark dataset for cell tracking under low-frame-rate imaging. The dataset covers four cell lines:

- MCF10A
- MDA-MB-231
- HEK293T
- U87

Each cell line is imaged at two magnifications (10× and 20×) using two channels:

- Phase contrast
- Nuclear fluorescence

All sequences are annotated in TrackMate (Fiji) and provided at four GAP factors (1, 2, 4, and 8) to simulate progressively lower temporal resolutions.

This repository contains the pipeline that prepares the dataset from the raw TrackMate XML annotations and the microscopy frames.

## Directory Structure

```
LFCT-pipeline/
├── Code/
│   ├── 01_xml_to_csv.py
│   ├── 02_sparsify.py
│   ├── 03_lineage.py
│   └── 04_video.py
├── Input/
│   ├── FLD_3.xml
│   ├── FLD_3_pc/
│   └── FLD_3_rfp/
├── Output/
├── run_all.sh
├── requirements.txt
└── README.md
```

- `Code/`: Python scripts for each step of the pipeline.
- `Input/`: Example data — TrackMate XML and microscopy frames for FLD_3 (MDA-MB-231, 20×).
- `Output/`: Generated CSV files and lineage tree PNGs. Videos are produced locally when the pipeline is run.
- `run_all.sh`: Runs all four scripts in order.
- `requirements.txt`: Python dependencies.

## Pipeline

### Annotation Extraction

The TrackMate XML annotations are converted into a CSV table. Each row represents one cell detection at one frame.

- Input: TrackMate XML file (`FLD_3.xml`)
- Output: CSV file with one row per spot
- Columns: spot ID, frame, track ID, parent spot ID, position (x, y), and all remaining spot attributes from TrackMate

Script: `01_xml_to_csv.py`

### Sparsification

The annotations are sparsified by retaining one out of every N frames to simulate low-frame-rate conditions. When a parent cell falls in a dropped frame, the child is reconnected to its nearest retained ancestor.

- Input: CSV from the previous step
- Output: One CSV file per GAP factor (GAP = 2, 4, 8)
- Each row includes the nearest retained ancestor, the ancestor's frame, and the displacement to it in pixels

Script: `02_sparsify.py`

### Lineage Tree Visualization

The lineage relationships are drawn as tree diagrams for each GAP factor. The horizontal axis shows frames, and each tree represents one cell lineage. Division events and daughter cells are highlighted with different colors.

- Input: CSV files from the previous steps
- Output: One PNG file per GAP factor (GAP = 1, 2, 4, 8)
- Color coding: blue for normal cells, brown for division parents, gold for daughter cells

Script: `03_lineage.py`

### Channel-Merged Video

The phase contrast and nuclear fluorescence frames are merged into a single video for each GAP factor so cell morphology and nuclear signal can be viewed together.

- Input: Phase contrast and nuclear fluorescence TIFF frames
- Output: One MP4 video per GAP factor (GAP = 1, 2, 4, 8)
- Frame rate: 5 fps

Script: `04_video.py`
