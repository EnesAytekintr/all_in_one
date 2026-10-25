WITH unnested AS (
    SELECT
        model_id,
        TRIM(BOTH '[]'' ' FROM UNNEST(STRING_TO_ARRAY(language, ':'))) AS language
    FROM {{ ref('stg_models', version=1) }}
    WHERE language IS NOT NULL AND language != ''
),

final AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['model_id', 'language']) }} AS pk_model_language_id,
        model_id,
        language
    FROM unnested
    WHERE language != ''
)

SELECT * FROM final