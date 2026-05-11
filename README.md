# SVMF Event Poster Generator

Python generator for consistent speaker posters and related event social assets. The repo is data-driven: edit the CSV, add photos, rerun the script, and get matching PNG outputs.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python generate_posts.py
```

Generated files are saved in `output/`.

For higher resolution:

```bash
python generate_posts.py --size 2400 --output output_2400
```

## Data

The public sample dataset is [data/speakers.csv](data/speakers.csv). It includes one mock/example row for Jef Caers:

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

Optional fixed-event columns can override the built-in defaults:

- `event_name`
- `date`
- `location_line_1`
- `location_line_2`

## Folders

```text
assets/      Fixed design assets and fonts
data/        CSV content source
photos/      Speaker photos referenced by the CSV
output/      Generated PNG files, ignored by git
```

Private speaker lists, extra photos, spreadsheets, and generated outputs are intentionally ignored by `.gitignore`.
