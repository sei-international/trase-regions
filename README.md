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

Clients consume this data from our AWS Cloudfront distribution that serves files from AWS S3. For how to deploy when files are changed, see "Copy to S3" section below.

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

Make a copy of `extract_trase_regions/secrets.yml.sample` as `extract_trase_regions/secrets.yml` and add your credentials for the database there. Remember to keep these credentials safe and **never commit them**.

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

Once you have generated the data, copy it to S3 so that it can be read, and issue a cache invalidation to ensure that the changes are immediately visible to website visitors:

```bash
aws s3 sync ./data/ s3://resources.trase.earth/data/trase-regions/ --exclude ".DS_Store"
aws cloudfront create-invalidation --distribution-id ES06N5GMZ1GUS --paths "/data/trase-regions/*"
```

> [!NOTE]
> All websites, be it production, staging or review all read from http://resources.trase.earth

## To-do

- [ ] Use Github Actions to run automatically
- [ ] Alter staging and review websites to read from other S3 buckets
