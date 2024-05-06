from helpers.constants import (
    COUNTRY_CODE_COL,
    COUNTRY_NAME_COL,
    LEVEL_COL,
    LEVEL_NAME_COL,
    GEOMETRY_COL,
    SIMPLIFY_DEGREES,
)

cte_table_name = "base"
regions_cte = f"""
WITH {cte_table_name} AS (
    SELECT
        name,
        trase_id,
        biome,
        {LEVEL_NAME_COL},
        country,
        TRUNC(level)::VARCHAR AS level,
        {LEVEL_COL},
        {GEOMETRY_COL} AS geometry
    FROM website.regions
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
        level,
        {LEVEL_COL} AS {LEVEL_COL},
        {LEVEL_NAME_COL},
        COUNT(1) as regions_count
    FROM {cte_table_name}
    WHERE geometry IS NOT NULL
      AND {LEVEL_COL} IS NOT NULL
    GROUP BY 1,2,3,4,5
    ORDER BY 1,2,3,4,5
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
        'geometry',   ST_AsGeoJSON(ST_Simplify(ST_GeomFromGeoJSON(geometry), {SIMPLIFY_DEGREES}), 4)::jsonb
        -- 'geometry', geometry
        ) AS json
    FROM (
        SELECT
            name,
            trase_id,
            biome,
            geometry,
            {LEVEL_NAME_COL},
            "{LEVEL_COL}",
            country
        FROM {cte_table_name}
        WHERE geometry IS NOT NULL
            AND "{LEVEL_COL}" = '{level}'
            AND country = '{country_name.replace("'", "''")}'
        ) r
    ) as t
    """
