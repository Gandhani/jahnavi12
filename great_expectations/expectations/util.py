import logging

from great_expectations.exceptions import GreatExpectationsError
from great_expectations.render.types import RenderedStringTemplateContent

logger = logging.getLogger(__name__)


legacy_method_parameters = {
    "expect_column_bootstrapped_ks_test_p_value_to_be_greater_than": (
        "column",
        "partition_object",
        "p",
        "bootstrap_samples",
        "bootstrap_sample_size",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_chisquare_test_p_value_to_be_greater_than": (
        "column",
        "partition_object",
        "p",
        "tail_weight_holdout",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_distinct_values_to_be_in_set": (
        "column",
        "value_set",
        "parse_strings_as_datetimes",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_distinct_values_to_contain_set": (
        "column",
        "value_set",
        "parse_strings_as_datetimes",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_distinct_values_to_equal_set": (
        "column",
        "value_set",
        "parse_strings_as_datetimes",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_kl_divergence_to_be_less_than": (
        "column",
        "partition_object",
        "threshold",
        "tail_weight_holdout",
        "internal_weight_holdout",
        "bucketize_data",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_max_to_be_between": (
        "column",
        "min_value",
        "max_value",
        "strict_min",
        "strict_max",
        "parse_strings_as_datetimes",
        "output_strftime_format",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_mean_to_be_between": (
        "column",
        "min_value",
        "max_value",
        "strict_min",
        "strict_max",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_median_to_be_between": (
        "column",
        "min_value",
        "max_value",
        "strict_min",
        "strict_max",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_min_to_be_between": (
        "column",
        "min_value",
        "max_value",
        "strict_min",
        "strict_max",
        "parse_strings_as_datetimes",
        "output_strftime_format",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_most_common_value_to_be_in_set": (
        "column",
        "value_set",
        "ties_okay",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_pair_cramers_phi_value_to_be_less_than": (
        "column_A",
        "column_B",
        "bins_A",
        "bins_B",
        "n_bins_A",
        "n_bins_B",
        "threshold",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_pair_values_A_to_be_greater_than_B": (
        "column_A",
        "column_B",
        "or_equal",
        "parse_strings_as_datetimes",
        "allow_cross_type_comparisons",
        "ignore_row_if",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_pair_values_to_be_equal": (
        "column_A",
        "column_B",
        "ignore_row_if",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_pair_values_to_be_in_set": (
        "column_A",
        "column_B",
        "value_pairs_set",
        "ignore_row_if",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_parameterized_distribution_ks_test_p_value_to_be_greater_than": (
        "column",
        "distribution",
        "p_value",
        "params",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_proportion_of_unique_values_to_be_between": (
        "column",
        "min_value",
        "max_value",
        "strict_min",
        "strict_max",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_quantile_values_to_be_between": (
        "column",
        "quantile_ranges",
        "allow_relative_error",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_stdev_to_be_between": (
        "column",
        "min_value",
        "max_value",
        "strict_min",
        "strict_max",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_sum_to_be_between": (
        "column",
        "min_value",
        "max_value",
        "strict_min",
        "strict_max",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_to_exist": (
        "column",
        "column_index",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_unique_value_count_to_be_between": (
        "column",
        "min_value",
        "max_value",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_value_lengths_to_be_between": (
        "column",
        "min_value",
        "max_value",
        "mostly",
        "row_condition",
        "condition_parser",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_value_lengths_to_equal": (
        "column",
        "value",
        "mostly",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_be_between": (
        "column",
        "min_value",
        "max_value",
        "strict_min",
        "strict_max",
        "allow_cross_type_comparisons",
        "parse_strings_as_datetimes",
        "output_strftime_format",
        "mostly",
        "row_condition",
        "condition_parser",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_be_dateutil_parseable": (
        "column",
        "mostly",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_be_decreasing": (
        "column",
        "strictly",
        "parse_strings_as_datetimes",
        "mostly",
        "row_condition",
        "condition_parser",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_be_in_set": (
        "column",
        "value_set",
        "mostly",
        "parse_strings_as_datetimes",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_be_in_type_list": (
        "column",
        "type_list",
        "mostly",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_be_increasing": (
        "column",
        "strictly",
        "parse_strings_as_datetimes",
        "mostly",
        "row_condition",
        "condition_parser",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_be_json_parseable": (
        "column",
        "mostly",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_be_null": (
        "column",
        "mostly",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_be_of_type": (
        "column",
        "type_",
        "mostly",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_be_unique": (
        "column",
        "mostly",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_match_json_schema": (
        "column",
        "json_schema",
        "mostly",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_match_regex": (
        "column",
        "regex",
        "mostly",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_match_regex_list": (
        "column",
        "regex_list",
        "match_on",
        "mostly",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_match_strftime_format": (
        "column",
        "strftime_format",
        "mostly",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_not_be_in_set": (
        "column",
        "value_set",
        "mostly",
        "parse_strings_as_datetimes",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_not_be_null": (
        "column",
        "mostly",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_not_match_regex": (
        "column",
        "regex",
        "mostly",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_column_values_to_not_match_regex_list": (
        "column",
        "regex_list",
        "mostly",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_compound_columns_to_be_unique": (
        "column_list",
        "ignore_row_if",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_multicolumn_sum_to_equal": (
        "column_list",
        "sum_total",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_multicolumn_values_to_be_unique": (
        "column_list",
        "ignore_row_if",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_select_column_values_to_be_unique_within_record": (
        "column_list",
        "ignore_row_if",
        "result_format",
        "row_condition",
        "condition_parser",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_table_column_count_to_be_between": (
        "min_value",
        "max_value",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_table_column_count_to_equal": (
        "value",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_table_columns_to_match_ordered_list": (
        "column_list",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_table_columns_to_match_set": (
        "column_set",
        "exact_match",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_table_row_count_to_be_between": (
        "min_value",
        "max_value",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
    "expect_table_row_count_to_equal": (
        "value",
        "result_format",
        "include_config",
        "catch_exceptions",
        "meta",
    ),
}


def render_evaluation_parameter_string(render_func):
    def inner_func(*args, **kwargs):
        rendered_string_template = render_func(*args, **kwargs)
        current_expectation_params = list()
        app_template_str = (
            "\n - $eval_param = $eval_param_value (at time of validation)."
        )
        configuration = kwargs.get("configuration", None)
        kwargs_dict = configuration.kwargs
        for key, value in kwargs_dict.items():
            if isinstance(value, dict) and "$PARAMETER" in value.keys():
                current_expectation_params.append(value["$PARAMETER"])

        # if expectation configuration has no eval params, then don't look for the values in runtime_configuration
        if len(current_expectation_params) > 0:
            runtime_configuration = kwargs.get("runtime_configuration", None)
            if runtime_configuration:
                eval_params = runtime_configuration.get("evaluation_parameters", {})
                styling = runtime_configuration.get("styling")
                for key, val in eval_params.items():
                    # this needs to be more complicated?
                    # the possibility that it is a substring?
                    for param in current_expectation_params:
                        # "key in param" condition allows for eval param values to be rendered if arithmetic is present
                        if key == param or key in param:
                            app_params = dict()
                            app_params["eval_param"] = key
                            app_params["eval_param_value"] = val
                            to_append = RenderedStringTemplateContent(
                                **{
                                    "content_block_type": "string_template",
                                    "string_template": {
                                        "template": app_template_str,
                                        "params": app_params,
                                        "styling": styling,
                                    },
                                }
                            )
                            rendered_string_template.append(to_append)
            else:
                raise GreatExpectationsError(
                    f"""GE was not able to render the value of evaluation parameters.
                        Expectation {render_func} had evaluation parameters set, but they were not passed in."""
                )
        return rendered_string_template

    return inner_func
