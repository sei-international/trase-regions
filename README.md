# Trase Regions

This is a script that extracts spatial and attribute data from the Trase db and saves it to geojson and topojson, for easier consumption by front-end clients such as dashboards.

The data is saved into the `data` folder, in the following structure:

```
.
└── data
    ├── metadata.json  # contains metadata on all regions
    ├── [2-letter country code]
        ├── [region_level.geojson]
        └── [region_level.topo.json]
    └── all  # geometries of all countries,
             # combined into a single file for each level
        ├── [region_level.geojson]
        └── [region_level.topo.json]
```

For example:

```
.
└── data
    ├── metadata.json
    ├── br
        ├── 1.geojson
        ├── 1.topo.json
        ├── 2.geojson
        ├── 2.topo.json
        └── etc.
    └── etc.
```

Clients can consume the data committed into this repo by following the link to the raw data, example: https://raw.githubusercontent.com/sei-international/trase-regions/main/data/ar/1.geojson

After extracting data for all regions, this script also combines them into a single geojson and topojson file for each region level, placing them in the folder `data/all`, e.g. `data/all/1.geojson` (for all level 1 geometries across all countries), or `data/all/biome.geojson` (for all biomes).

## Prerequisites

You'll need Python and [Poetry](https://python-poetry.org/), a Python package manager.

## Installation

### Ubuntu

Prerequisites on Ubuntu (for the `psycopg2` package):

```bash
sudo apt install libpq-dev python3-dev
```

Then:

```bash
poetry install
```

For simplify-geometries script:

```
nvm install
nvm use
npm install
```

### Mac

Install postgresql:

```bash
brew install postgresql
```

Then (if you have pyenv):

```
pyenv install 3.11
poetry env use 3.11
poetry install
```

For simplify-geometries script:

```
nvm install
nvm use
npm install
```

---

Make a copy of `secrets.yml.sample` as `secrets.yml` and add your credentials for the database there. Remember to keep these credentials safe and **never commit them**.

## Usage

To run for all regions:

```bash
poetry run python extract_trase_regions
```

To run for specific regions, pass the 2-letter country codes as arguments (e.g. Cote D'Ivoire and Bolivia):

```bash
poetry run python extract_trase_regions --country_codes CI BO
```

To simplify geojsons which are too large, run (run this as many times as needed, until all files are under the maxiumum file size):

```bash
npm run simplify
```

## To-do

- [ ] Use Github Actions to run automatically
