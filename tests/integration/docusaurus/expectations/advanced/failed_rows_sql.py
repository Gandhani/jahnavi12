import great_expectations as gx

context = gx.get_context(context_root_dir="./great_expectations", cloud_mode=False)
datasource = context.sources.add_sqlite(
    name="visits_datasource",
    connection_string=f"sqlite:///data/visits.db",
)
asset = datasource.add_table_asset(
    name="visits",
    table_name="event_names",
)

# get checkpoint
my_checkpoint = context.get_checkpoint("my_checkpoint")


# Example 1
results = my_checkpoint.run()
evrs = results.list_validation_results()
assert (evrs[0]["results"][0]["result"]) == {
    "element_count": 6,
    "unexpected_count": 3,
    "unexpected_percent": 50.0,
    "partial_unexpected_list": ["user_signup", "purchase", "download"],
    "missing_count": 0,
    "missing_percent": 0.0,
    "unexpected_percent_total": 50.0,
    "unexpected_percent_nonmissing": 50.0,
    "partial_unexpected_counts": [
        {"value": "download", "count": 1},
        {"value": "purchase", "count": 1},
        {"value": "user_signup", "count": 1},
    ],
}


# Example 2
result_format: dict = {
    "result_format": "COMPLETE",
    "unexpected_index_column_names": ["event_id"],
}
results = my_checkpoint.run(result_format=result_format)
evrs = results.list_validation_results()
assert (evrs[0]["results"][0]["result"]) == {
    "element_count": 6,
    "unexpected_count": 3,
    "unexpected_percent": 50.0,
    "partial_unexpected_list": ["user_signup", "purchase", "download"],
    "unexpected_index_column_names": ["event_id"],
    "missing_count": 0,
    "missing_percent": 0.0,
    "unexpected_percent_total": 50.0,
    "unexpected_percent_nonmissing": 50.0,
    "partial_unexpected_index_list": [
        {"event_id": 3, "event_type": "user_signup"},
        {"event_id": 4, "event_type": "purchase"},
        {"event_id": 5, "event_type": "download"},
    ],
    "partial_unexpected_counts": [
        {"value": "download", "count": 1},
        {"value": "purchase", "count": 1},
        {"value": "user_signup", "count": 1},
    ],
    "unexpected_list": ["user_signup", "purchase", "download"],
    "unexpected_index_list": [
        {"event_id": 3, "event_type": "user_signup"},
        {"event_id": 4, "event_type": "purchase"},
        {"event_id": 5, "event_type": "download"},
    ],
    "unexpected_index_query": "SELECT event_id, event_type \nFROM event_names \nWHERE event_type IS NOT NULL AND (event_type NOT IN ('page_load', 'page_view'));",
}

# Example 3
result_format: dict = {
    "result_format": "COMPLETE",
    "unexpected_index_column_names": ["event_id", "visit_id"],
}
results = my_checkpoint.run(result_format=result_format)
evrs = results.list_validation_results()
assert (evrs[0]["results"][0]["result"]) == {
    "element_count": 6,
    "unexpected_count": 3,
    "unexpected_percent": 50.0,
    "partial_unexpected_list": ["user_signup", "purchase", "download"],
    "unexpected_index_column_names": ["event_id", "visit_id"],
    "missing_count": 0,
    "missing_percent": 0.0,
    "unexpected_percent_total": 50.0,
    "unexpected_percent_nonmissing": 50.0,
    "partial_unexpected_index_list": [
        {"event_id": 3, "visit_id": 1470387700, "event_type": "user_signup"},
        {"event_id": 4, "visit_id": 1470438716, "event_type": "purchase"},
        {"event_id": 5, "visit_id": 1470420524, "event_type": "download"},
    ],
    "partial_unexpected_counts": [
        {"value": "download", "count": 1},
        {"value": "purchase", "count": 1},
        {"value": "user_signup", "count": 1},
    ],
    "unexpected_list": ["user_signup", "purchase", "download"],
    "unexpected_index_list": [
        {"event_id": 3, "visit_id": 1470387700, "event_type": "user_signup"},
        {"event_id": 4, "visit_id": 1470438716, "event_type": "purchase"},
        {"event_id": 5, "visit_id": 1470420524, "event_type": "download"},
    ],
    "unexpected_index_query": "SELECT event_id, visit_id, event_type \nFROM event_names \nWHERE event_type IS NOT NULL AND (event_type NOT IN ('page_load', 'page_view'));",
}
