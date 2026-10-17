{% snapshot scd_hf_models_snapshot %}

SELECT
    id,
    author,
    pipeline_tag,
    library_name,
    downloads,
    likes,
    "private",
    gated,
    license,
    base_model,
    "language",
    datasets,
    tags,
    created_at::TIMESTAMP AS created_at,
    last_modified::TIMESTAMP AS last_modified
FROM {{ source('hf_models', 'hf_models_raw') }}

{% endsnapshot %}