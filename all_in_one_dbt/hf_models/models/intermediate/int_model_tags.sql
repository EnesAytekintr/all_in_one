WITH unnested AS (
    SELECT
        model_id,
        TRIM(BOTH '[]'' ' FROM UNNEST(STRING_TO_ARRAY(tags, ','))) AS tag
    FROM {{ ref('stg_models', version=1) }}
    WHERE tags IS NOT NULL AND tags != ''
),

final AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['model_id', 'tag']) }} AS pk_model_tag_id,
        model_id,
        tag
    FROM unnested
    WHERE tag != ''
)

SELECT * FROM final