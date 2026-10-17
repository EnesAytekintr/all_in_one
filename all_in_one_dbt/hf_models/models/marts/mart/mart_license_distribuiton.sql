WITH fct_models AS (
    SELECT
        model_id,
        license,
        gated_status,
        downloads,
        likes
    FROM {{ ref('fct_model_metrics') }}
    WHERE license IS NOT NULL AND is_current = TRUE
),

aggregated AS (
    SELECT
        license,
        COUNT(DISTINCT model_id) AS total_models,
        SUM(downloads) AS total_downloads,
        SUM(likes) AS total_likes,
        ROUND(AVG(downloads), 2) AS avg_downloads_per_model,
        COUNT(DISTINCT CASE WHEN gated_status != 'false' AND gated_status IS NOT NULL THEN model_id END) AS gated_models_count
    FROM fct_models
    GROUP BY license
),

final AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['license']) }} AS pk_license_distribution_id,
        license,
        total_models,
        total_downloads,
        total_likes,
        avg_downloads_per_model,
        gated_models_count,
        ROUND(
            (gated_models_count * 100.0) / NULLIF(total_models, 0),
            2
        ) AS gated_percentage,
        ROUND(
            (total_models * 100.0) / SUM(total_models) OVER (),
            2
        ) AS market_share_percentage,
        ROW_NUMBER() OVER (ORDER BY total_downloads DESC) AS rank_by_downloads
    FROM aggregated
)

SELECT * FROM final