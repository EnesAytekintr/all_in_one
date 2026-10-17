WITH source AS (
    SELECT
        author
    FROM {{ ref('stg_models') }}
    WHERE author IS NOT NULL
),

final AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['author']) }} AS pk_author_id,
        author
    FROM source
    GROUP BY author
)

SELECT * FROM final