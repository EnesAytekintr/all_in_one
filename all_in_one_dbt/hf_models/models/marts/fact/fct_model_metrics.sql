WITH models  AS (
    SELECT
	dbt_scd_id AS pk_model_version_id,
	SPLIT_PART(model_id, '/', 2) AS model_id,
	{{ dbt_utils.generate_surrogate_key(['author']) }} AS fk_author_id,
	downloads,
	likes,
	pipeline_tag,
	library_name,
	license,
	base_model,
	gated_status,
	is_private,
	created_at,
	last_modified,
	CASE 
		WHEN dbt_valid_to IS NULL THEN TRUE
		ELSE FALSE
	END AS is_current,
	dbt_updated_at,
	dbt_valid_from,
	dbt_valid_to
    FROM {{ ref('stg_models', version=1,) }}
	{% if is_incremental() %}
	WHERE dbt_updated_at > (SELECT MAX(dbt_updated_at) FROM {{ this }})
	{% endif %}
)
SELECT * FROM models
