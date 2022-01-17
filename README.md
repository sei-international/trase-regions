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

Clients can consume the data committed into this repo by following the link to the raw data, example:

## Prerequisites

You'll need Python and [Poetry](https://python-poetry.org/), a Python package manager.

## Installation

Prerequisites on Ubuntu (for the `psycopg2` package):

```bash
sudo apt install libpq-dev python3-dev
```

Then:

```bash
poetry install
```

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
