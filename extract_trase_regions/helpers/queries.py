from helpers.constants import (
    COUNTRY_CODE_COL,
    COUNTRY_NAME_COL,
    LEVEL_COL,
    LEVEL_NAME_COL,
    GEOMETRY_COL,
)

max_year = 10000
cte_table_name = "base"
regions_cte = f"""
WITH 
create_ranges AS (
    WITH cleaned AS (
        select
            country,
            node_type_slug,
            trase_id as id,
            coalesce(year_start, 1)::INTEGER as year_start,
            coalesce(year_end, {max_year})::INTEGER as year_end
        from
            views.regions
    ),
    -- boundaries per group
    boundaries AS (
        SELECT
            country,
            node_type_slug,
            year_start AS boundary
        FROM
            cleaned
        UNION
        SELECT
            country,
            node_type_slug,
            year_end AS boundary
        FROM
            cleaned
    ),
    sorted_boundaries AS (
        SELECT DISTINCT country, node_type_slug, boundary
        FROM boundaries
        ORDER BY 1,2,3  
    ),
    -- order boundaries and get next boundary per group
    ranges AS (
        SELECT
            country,
            node_type_slug,
            boundary AS slice_start,
            LEAD(boundary) OVER (
                PARTITION BY country,
                node_type_slug
                ORDER BY
                    boundary
            ) - 1 AS slice_end
        FROM
            boundaries
    ),
    -- only slices with a real next boundary
    intervals AS (
        SELECT
            country,
            node_type_slug,
            slice_start,
            slice_end
        FROM
            ranges
        WHERE
            slice_end IS NOT NULL
    ),
    -- determine which ids are active in each interval
    slice_contents AS (
        SELECT
            i.country,
            i.node_type_slug,
            i.slice_start,
            i.slice_end,
            c.id AS trase_id
        FROM
            intervals i
            JOIN cleaned c ON c.country = i.country
            AND c.node_type_slug = i.node_type_slug
            AND c.year_start <= i.slice_start
            AND c.year_end >= i.slice_end
    )
    SELECT * FROM slice_contents
)
, {cte_table_name} AS (
    SELECT
        r.name,
        cr.trase_id,
        r.biome,
        r.{LEVEL_NAME_COL},
        cr.slice_start AS year_start,
        cr.slice_end AS year_end,
        r.country,
        TRUNC(r.level)::VARCHAR AS level,
        r.{LEVEL_COL},
        p.name AS parent_name,
        p.{LEVEL_NAME_COL} AS parent_{LEVEL_NAME_COL},
        r.{GEOMETRY_COL} AS geometry
    FROM create_ranges AS cr
    JOIN views.regions AS r
        ON r.trase_id = cr.trase_id
        AND r.country = cr.country
        AND r.node_type_slug = cr.node_type_slug
        AND COALESCE(r.year_start, 1)::INTEGER <= cr.slice_start
        AND COALESCE(r.year_end, {max_year - 1})::INTEGER >= cr.slice_end
    LEFT JOIN views.regions AS p
        ON p.trase_id =
        CASE
            -- HACK: force Brazil to use states as parent region
            WHEN r.country = 'BRAZIL' AND r.{LEVEL_COL} = 'municipality' THEN LEFT(r.trase_id, 5)
            ELSE r.parent_trase_id
        END
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
        year_start,
        year_end,
        COUNT(1) as regions_count
    FROM {cte_table_name}
    WHERE TRUE
      AND geometry IS NOT NULL
      AND {LEVEL_COL} IS NOT NULL
      AND LEFT(trase_id, 2) IS NOT NULL
    GROUP BY 1,2,3,4,5,6,7
    ORDER BY 1,2,3,4,5,6,7
    """


def generate_geojson_query(country_name, level, year_start, year_end):
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
        'geometry',   ST_AsGeoJSON(ST_GeomFromGeoJSON(geometry))::jsonb
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
            year_start,
            year_end,
            parent_name,
            parent_{LEVEL_NAME_COL},
            country
        FROM {cte_table_name}
        WHERE TRUE
            AND "{LEVEL_COL}" = '{level}'
            AND country = '{country_name.replace("'", "''")}'
            AND year_start <= {year_start}
            AND year_end >= {year_end}
        ) r
    ) as t
    """
