from helpers.constants import (
    COUNTRY_CODE_COL,
    COUNTRY_NAME_COL,
    LEVEL_COL,
    SIMPLIFY_DEGREES,
)

cte_table_name = "base"
# The CASE statement assigns a level = 'biome' to biomes,
# since these don't have a level right now in the db.
regions_cte = f"""
WITH {cte_table_name} AS (
    SELECT
        name,
        trase_id,
        biome,
        region_type,
        country,
        CASE
            WHEN region_type = 'BIOME' THEN 'biome'
            ELSE level::VARCHAR
        END AS level,
        geometry
    FROM views.regions
)
"""

def regions_dictionary_query():
    """
    Get a list of regions that exist in the database and that
    have geometries.
    """
    return f"""
    {regions_cte}
    SELECT
        country AS {COUNTRY_NAME_COL},
        LEFT(trase_id, 2) as {COUNTRY_CODE_COL},
        level AS {LEVEL_COL},
        region_type,
        COUNT(1) as regions_count
    FROM {cte_table_name}
    WHERE geometry IS NOT NULL
      AND level IS NOT NULL
    GROUP BY 1,2,3,4
    ORDER BY 1,2,3,4
    """


def generate_geojson_query(country_name, level):
    # NOTE: the replacing of single quotes in country name is for Cote D'Ivoire
    return f"""
    {regions_cte}
    SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(t.json)
        ) AS "data" FROM (
    select
    jsonb_build_object(
        'type',       'Feature',
        'id',         trase_id,
        'properties', to_jsonb( r.* ) - 'geometry',
        'geometry',   ST_AsGeoJSON(ST_Simplify(geometry, {SIMPLIFY_DEGREES}), 4)::jsonb
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
        FROM {cte_table_name}
        WHERE geometry IS NOT NULL
            AND "level" = '{level}'
            AND country = '{country_name.replace("'", "''")}'
        ) r
    ) as t
    """
