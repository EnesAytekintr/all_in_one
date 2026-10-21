WITH fct_models AS (
    SELECT
        model_id,
        downloads,
        likes
    FROM {{ ref('fct_model_metrics', v=1) }}
    WHERE pipeline_tag IS NOT NULL AND is_current = TRUE
),

int_model_tags AS (
    SELECT
        model_id,
        tag
    FROM {{ ref('int_model_tags', version=1) }}
    WHERE tag IS NOT NULL AND tag != ''
),

aggregated AS (
    SELECT
        int_model_tags.tag AS tag,
        COUNT(*) AS total_models_using_tag,
        SUM(fct_models.downloads) AS total_downloads,
        SUM(fct_models.likes) AS total_tag_likes,
        ROUND(AVG(fct_models.downloads), 2) AS avg_downloads_per_model
    FROM int_model_tags
    INNER JOIN fct_models
        ON int_model_tags.model_id = fct_models.model_id
    GROUP BY int_model_tags.tag
),

final AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['tag']) }} AS pk_tag_popularity_id,
        tag,
        total_models_using_tag,
        total_downloads,
        total_tag_likes,
        avg_downloads_per_model,
        ROUND(
            (total_models_using_tag * 100.0) / NULLIF(SUM(total_models_using_tag) OVER (), 0),
            2
        ) AS market_share_percentage,
        ROW_NUMBER() OVER (ORDER BY total_downloads DESC) AS rank_by_downloads
    FROM aggregated
)

SELECT * FROM final