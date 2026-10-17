WITH models  AS (
    SELECT
	{{ dbt_utils.generate_surrogate_key(['model_id']) }} AS pk_model_id,
	model_id,
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
	last_modified
    FROM {{ ref('stg_models') }}
)
SELECT * FROM models