WITH source AS (
    SELECT * FROM {{ ref('scd_hf_models_snapshot') }}
),

renamed_and_casted AS (
    SELECT
        CAST(id AS TEXT) AS model_id,
        CAST(author AS TEXT) AS author,
        CAST(pipeline_tag AS TEXT) AS pipeline_tag,
        CAST(library_name AS TEXT) AS library_name,
        COALESCE(CAST(downloads AS BIGINT), 0) AS downloads,
        COALESCE(CAST(likes AS BIGINT), 0) AS likes,
        COALESCE(CAST(private AS BOOLEAN), FALSE) AS is_private,
        CAST(gated AS TEXT) AS gated_status,
        CAST(license AS TEXT) AS license,
        CAST(base_model AS TEXT) AS base_model,
        CAST(language AS TEXT) AS language,
        CAST(datasets AS TEXT) AS datasets,
        CAST(tags AS TEXT) AS tags,
        CAST(created_at AS TIMESTAMP) AS created_at,
        CAST(last_modified AS TIMESTAMP) AS last_modified,
        dbt_scd_id,
        dbt_updated_at,
        dbt_valid_from,
        dbt_valid_to
    FROM source
)

SELECT * FROM renamed_and_casted