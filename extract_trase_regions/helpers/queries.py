from helpers.constants import (
    COUNTRY_CODE_COL,
    COUNTRY_NAME_COL,
    LEVEL_COL,
)

def regions_dictionary_query():
    return f"""
    SELECT
        country AS {COUNTRY_NAME_COL},
        LEFT(trase_id, 2) as {COUNTRY_CODE_COL},
        level AS {LEVEL_COL},
        region_type,
        COUNT(1) as regions_count
    FROM views.regions
    WHERE geometry IS NOT NULL
      AND level IS NOT NULL
    GROUP BY 1,2,3,4
    ORDER BY 1,2,3,4
    """


def generate_geojson_query(country_name, level):
    # NOTE: the replacing of single quotes in country name is for Cote D'Ivoire
    return f"""
    SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(t.json)
        ) AS "data" FROM (
    select
    jsonb_build_object(
        'type',       'Feature',
        'id',         trase_id,
        'properties', to_jsonb( r.* ) - 'geometry',
        'geometry',   ST_AsGeoJSON(ST_Simplify(geometry, 0.001), 4)::jsonb
        ) AS json
    FROM (
      SELECT
        name,
        trase_id,
        biome,
        geometry,
        region_type,
        "level",
        country
    FROM views.regions
    ) r
    WHERE "level" = '{level}' AND country = '{country_name.replace("'", "''")}'
    ) as t
    """
