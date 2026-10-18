WITH fct_models AS (
    SELECT
        model_id,
        pipeline_tag,
        library_name,
        downloads,
        likes
    FROM {{ ref('fct_model_metrics', version=1) }}
    WHERE pipeline_tag IS NOT NULL AND is_current = TRUE
),

aggregated AS (
    SELECT
        pipeline_tag,
        COUNT(DISTINCT model_id) AS total_models,
        SUM(downloads) AS total_downloads,
        SUM(likes) AS total_likes,
        ROUND(AVG(downloads), 2) AS avg_downloads_per_model,
        ROUND(AVG(likes), 2) AS avg_likes_per_model,
        MODE() WITHIN GROUP (ORDER BY library_name) AS dominant_library
    FROM fct_models
    GROUP BY pipeline_tag
),

final AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['pipeline_tag']) }} AS pk_pipeline_overview_id,
        pipeline_tag,
        dominant_library,
        total_models,
        total_downloads,
        total_likes,
        avg_downloads_per_model,
        avg_likes_per_model,
        ROUND(
            (total_models * 100.0) / SUM(total_models) OVER (), 
            2
        ) AS market_share_percentage,
        ROW_NUMBER() OVER (ORDER BY total_downloads DESC) AS rank_by_downloads
    FROM aggregated
)

SELECT * FROM final