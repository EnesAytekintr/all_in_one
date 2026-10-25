WITH fct_models AS (
    SELECT
        model_id,
        fk_author_id,
        downloads,
        likes,
        created_at
    FROM {{ ref('fct_model_metrics', version=1) }} 
    WHERE is_current = TRUE
),
dim_author AS (
    SELECT
        pk_author_id,
        author
    FROM {{ ref('dim_author', version=1) }}
    WHERE author IS NOT NULL
),
aggregated AS (
    SELECT
        COALESCE(dim_author.author, 'unknown') AS author,
        COUNT(DISTINCT fct_models.model_id) AS total_models,
        SUM(fct_models.downloads) AS total_downloads,
        SUM(fct_models.likes) AS total_likes,
        ROUND(AVG(fct_models.downloads), 2) AS avg_downloads_per_model,
        ROUND(AVG(fct_models.likes), 2) AS avg_likes_per_model,
        MIN(fct_models.created_at) AS first_model_created_at,
        MAX(fct_models.created_at) AS last_model_created_at
    FROM fct_models
    LEFT JOIN dim_author
        ON fct_models.fk_author_id = dim_author.pk_author_id
    GROUP BY dim_author.author
),

final AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['author']) }} AS pk_author_leaderboard_id,
        author,
        total_models,
        total_downloads,
        total_likes,
        avg_downloads_per_model,
        avg_likes_per_model,
        first_model_created_at,
        last_model_created_at,
        ROW_NUMBER() OVER (ORDER BY total_downloads DESC) AS rank_by_downloads,
        ROW_NUMBER() OVER (ORDER BY total_likes DESC) AS rank_by_likes
    FROM aggregated
)

SELECT * FROM final