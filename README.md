# Bulk Event Poster Generator

<p>
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="Status" src="https://img.shields.io/badge/status-demo%20ready-lightgrey">
</p>

**Authors:** Sofia Mantilla ([@sofia-mantilla](https://github.com/sofia-mantilla))

Created with OpenAI Codex.

## Overview

This repository generates consistent event speaker posters from a CSV and a folder of photos. It was built for Silicon Valley Minerals Forum-style social posts, but the structure can be adapted for event flyers, speaker cards, and other recurring event materials.

## Module Core Functionality

- Load speaker metadata from CSV.
- Load speaker photos from a local folder.
- Render a fixed poster design with logos, typography, circular masks, and gradient backgrounds.
- Export one PNG per speaker at configurable resolution.

## Real Problem

Event teams often need many visually consistent speaker graphics; this tool turns a content spreadsheet and photos into repeatable, on-brand outputs.

## Keywords

event posters, speaker cards, batch image generation, Pillow, CSV workflow, social media assets, Mineral-X

## Getting Started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python generate_posts.py
```

Generated files are saved in `output/`.

For higher-resolution output:

```bash
python generate_posts.py --size 2400 --output output_2400
```

## Installation Guide

Requirements:

- Python 3.10+
- `pip`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Input Data

The public sample dataset is [data/speakers.csv](data/speakers.csv). It contains one demo row:

```csv
speaker_name,title,organization,photo_filename,output_filename
Jef Caers,Professor & Director,Stanford Mineral-X,jef_caers.jpg,jef_caers.png
```

Required columns:

- `speaker_name`
- `title`
- `organization`
- `photo_filename`
- `output_filename`

Optional columns can override the fixed event defaults:

- `event_name`
- `date`
- `location_line_1`
- `location_line_2`

Photos referenced by `photo_filename` should be placed in `photos/`.

## Output Data

The script writes PNG files to the selected output folder. Each output file uses the `output_filename` value from the CSV row.

Example:

```text
output/jef_caers.png
```

## Demo Case

The repository includes one small demo row and one sample speaker photo. Run:

```bash
python generate_posts.py
```

to create the sample poster.

## Repo Tree

```text
.
├── assets/              # Fixed design assets and fonts
├── data/                # Public sample CSV
├── photos/              # Public sample photo
├── generate_posts.py    # Batch rendering script
├── requirements.txt     # Python dependencies
├── README.md
└── LICENSE
```

Private speaker lists, extra photos, spreadsheets, and generated outputs are intentionally ignored by `.gitignore`.

## License

This project is released under the [MIT License](LICENSE).
