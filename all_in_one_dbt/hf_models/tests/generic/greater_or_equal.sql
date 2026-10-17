{% test value_greater_than_or_equal_to(model,column_name,min_value) %}
    SELECT *
    FROM {{ model }}
    WHERE {{ column_name }} < {{ min_value }}
{% endtest %}