WITH source AS (
    SELECT * FROM {{ source('hf_models', 'hf_models_raw') }}
),

deduped AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY id 
            ORDER BY downloads DESC NULLS LAST
        ) AS row_num
    FROM source
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
        CAST(NULLIF(created_at, 'None') AS TIMESTAMP) AS created_at,
        CAST(NULLIF(last_modified, 'None') AS TIMESTAMP) AS last_modified
    FROM deduped
    WHERE row_num = 1
)

SELECT * FROM renamed_and_casted