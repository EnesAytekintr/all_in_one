WITH unnested AS (
    SELECT
        model_id,
        TRIM(BOTH '[]'' ' FROM UNNEST(STRING_TO_ARRAY(datasets, ','))) AS dataset
    FROM {{ ref('stg_models') }}
    WHERE datasets IS NOT NULL AND datasets != ''
),

final AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['model_id', 'dataset']) }} AS pk_model_datasets_id,
        model_id,
        dataset
    FROM unnested
    WHERE dataset != ''
)

SELECT * FROM final