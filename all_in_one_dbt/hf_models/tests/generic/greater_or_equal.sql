{% test value_greater_than_or_equal_to(model,column_name, value) %}
    SELECT *
    FROM {{ model }}
    WHERE {{ column_name }} < {{ value }}
{% endtest %}