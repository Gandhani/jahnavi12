import math
from datetime import datetime, timedelta
from timeit import timeit

import dateutil
import pandas
import pandas as pd
import pytest

from great_expectations.core import ExpectationValidationResult
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.core.evaluation_parameters import (
    _deduplicate_evaluation_parameter_dependencies,
    find_evaluation_parameter_dependencies,
    parse_evaluation_parameter,
)
from great_expectations.exceptions import DataContextError, EvaluationParameterError


@pytest.mark.unit
def test_parse_evaluation_parameter():
    # Substitution alone is ok
    assert parse_evaluation_parameter("a", {"a": 1}) == 1
    assert (
        parse_evaluation_parameter(
            "urn:great_expectations:validations:blarg",
            {"urn:great_expectations:validations:blarg": 1},
        )
        == 1
    )

    # Very basic arithmetic is allowed as-is:
    assert parse_evaluation_parameter("1 + 1", {}) == 2

    # So is simple variable substitution:
    assert parse_evaluation_parameter("a + 1", {"a": 2}) == 3

    # URN syntax works
    assert (
        parse_evaluation_parameter(
            "urn:great_expectations:validations:source_patient_data.default"
            ":expect_table_row_count_to_equal.result.observed_value * 0.9",
            {
                "urn:great_expectations:validations:source_patient_data.default"
                ":expect_table_row_count_to_equal.result.observed_value": 10
            },
        )
        == 9
    )

    # bare decimal is accepted
    assert (
        parse_evaluation_parameter(
            "urn:great_expectations:validations:source_patient_data.default"
            ":expect_table_row_count_to_equal.result.observed_value * .9",
            {
                "urn:great_expectations:validations:source_patient_data.default"
                ":expect_table_row_count_to_equal.result.observed_value": 10
            },
        )
        == 9
    )

    # We have basic operations (trunc)
    assert (
        parse_evaluation_parameter(
            "urn:great_expectations:validations:source_patient_data.default"
            ":expect_table_row_count_to_equal.result.observed_value * 0.9",
            {
                "urn:great_expectations:validations:source_patient_data.default"
                ":expect_table_row_count_to_equal.result.observed_value": 11
            },
        )
        != 9
    )

    assert (
        parse_evaluation_parameter(
            "trunc(urn:great_expectations:validations:source_patient_data.default"
            ":expect_table_row_count_to_equal.result.observed_value * 0.9)",
            {
                "urn:great_expectations:validations:source_patient_data.default"
                ":expect_table_row_count_to_equal.result.observed_value": 11
            },
        )
        == 9
    )

    # Non GX URN syntax fails
    with pytest.raises(EvaluationParameterError) as err:
        parse_evaluation_parameter("urn:ieee:not_ge * 10", {"urn:ieee:not_ge": 1})
    assert "Parse Failure" in str(err.value)

    # Valid variables but invalid expression is no good
    with pytest.raises(EvaluationParameterError) as err:
        parse_evaluation_parameter("1 / a", {"a": 0})
    assert (
        "Error while evaluating evaluation parameter expression: division by zero"
        in str(err.value)
    )

    # It is okay to *substitute* strings in the expression...
    assert parse_evaluation_parameter("foo", {"foo": "bar"}) == "bar"

    # ...and to have whitespace in substituted values...
    assert parse_evaluation_parameter("foo", {"foo": "bar "}) == "bar "

    # ...but whitespace is *not* preserved from the parameter name if we evaluate it
    assert parse_evaluation_parameter("foo ", {"foo": "bar"}) == "bar"  # NOT "bar "

    # We can use multiple parameters...
    assert parse_evaluation_parameter("foo * bar", {"foo": 2, "bar": 3}) == 6

    # ...but we cannot leave *partially* evaluated expressions (phew!)
    with pytest.raises(EvaluationParameterError) as e:
        parse_evaluation_parameter("foo + bar", {"foo": 2})
    assert (
        "Error while evaluating evaluation parameter expression: could not convert string to float"
        in str(e.value)
    )


@pytest.mark.integration
def test_query_store_results_in_evaluation_parameters(data_context_with_query_store):
    TITANIC_ROW_COUNT = 1313  # taken from the titanic db conftest
    DISTINCT_TITANIC_ROW_COUNT = 4

    # parse_evaluation_parameters correctly resolves a stores URN
    res1 = parse_evaluation_parameter(
        parameter_expression="urn:great_expectations:stores:my_query_store:col_count",
        evaluation_parameters=None,
        data_context=data_context_with_query_store,
    )
    assert res1 == TITANIC_ROW_COUNT

    # and can handle an operator
    res2 = parse_evaluation_parameter(
        parameter_expression="urn:great_expectations:stores:my_query_store:col_count * 2",
        evaluation_parameters=None,
        data_context=data_context_with_query_store,
    )
    assert res2 == TITANIC_ROW_COUNT * 2

    # can even handle multiple operators
    res3 = parse_evaluation_parameter(
        parameter_expression="urn:great_expectations:stores:my_query_store:col_count * 0 + 100",
        evaluation_parameters=None,
        data_context=data_context_with_query_store,
    )
    assert res3 == 100

    # allows stores URNs with functions
    res4 = parse_evaluation_parameter(
        parameter_expression="cos(urn:great_expectations:stores:my_query_store:col_count)",
        evaluation_parameters=None,
        data_context=data_context_with_query_store,
    )
    assert math.isclose(math.cos(TITANIC_ROW_COUNT), res4)

    # multiple stores URNs can be used
    res5 = parse_evaluation_parameter(
        parameter_expression="urn:great_expectations:stores:my_query_store:col_count - urn:great_expectations:stores:my_query_store:dist_col_count",
        evaluation_parameters=None,
        data_context=data_context_with_query_store,
    )
    assert res5 == TITANIC_ROW_COUNT - DISTINCT_TITANIC_ROW_COUNT

    # complex expressions can combine operators, urns, and functions
    res6 = parse_evaluation_parameter(
        parameter_expression="abs(-urn:great_expectations:stores:my_query_store:col_count - urn:great_expectations:stores:my_query_store:dist_col_count)",
        evaluation_parameters=None,
        data_context=data_context_with_query_store,
    )
    assert res6 == TITANIC_ROW_COUNT + DISTINCT_TITANIC_ROW_COUNT


@pytest.mark.unit
def test_parser_timing():
    """We currently reuse the parser, clearing the stack between calls, which is about 10 times faster than not
    doing so. But these operations are really quick, so this may not be necessary."""
    assert (
        timeit(
            "parse_evaluation_parameter('x', {'x': 1})",
            setup="from great_expectations.core.evaluation_parameters import parse_evaluation_parameter",
            number=100,
        )
        < 1
    )


@pytest.mark.unit
def test_math_evaluation_paramaters():
    assert parse_evaluation_parameter("sin(2*PI)") == math.sin(math.pi * 2)
    assert parse_evaluation_parameter("cos(2*PI)") == math.cos(math.pi * 2)
    assert parse_evaluation_parameter("tan(2*PI)") == math.tan(math.pi * 2)


@pytest.mark.unit
def test_temporal_evaluation_parameters():
    # allow 1 second for "now" tolerance
    now = datetime.now()
    assert (
        (now - timedelta(weeks=1, seconds=3))
        < dateutil.parser.parse(
            parse_evaluation_parameter("now() - timedelta(weeks=1, seconds=2)")
        )
        < now - timedelta(weeks=1, seconds=1)
    )


@pytest.mark.unit
def test_temporal_evaluation_parameters_complex():
    # allow 1 second for "now" tolerance
    now = datetime.now()
    # Choosing "2*3" == 6 weeks shows we can parse an expression inside a kwarg.
    assert (
        (now - timedelta(weeks=2 * 3, seconds=3))
        < dateutil.parser.parse(
            parse_evaluation_parameter("now() - timedelta(weeks=2*3, seconds=2)")
        )
        < now - timedelta(weeks=2 * 3, seconds=1)
    )


@pytest.mark.unit
def test_find_evaluation_parameter_dependencies():
    parameter_expression = "(-3 * urn:great_expectations:validations:profile:expect_column_stdev_to_be_between.result.observed_value:column=norm) + urn:great_expectations:validations:profile:expect_column_mean_to_be_between.result.observed_value:column=norm"
    dependencies = find_evaluation_parameter_dependencies(parameter_expression)
    assert dependencies == {
        "urns": {
            "urn:great_expectations:validations:profile:expect_column_stdev_to_be_between.result.observed_value:column=norm",
            "urn:great_expectations:validations:profile:expect_column_mean_to_be_between.result.observed_value:column=norm",
        },
        "other": set(),
    }

    parameter_expression = "upstream_value * urn:great_expectations:validations:profile:expect_column_stdev_to_be_between.result.observed_value:column=norm"
    dependencies = find_evaluation_parameter_dependencies(parameter_expression)
    assert dependencies == {
        "urns": {
            "urn:great_expectations:validations:profile:expect_column_stdev_to_be_between.result.observed_value:column=norm",
        },
        "other": {"upstream_value"},
    }

    parameter_expression = "upstream_value"
    dependencies = find_evaluation_parameter_dependencies(parameter_expression)
    assert dependencies == {"urns": set(), "other": {"upstream_value"}}

    parameter_expression = "3 * upstream_value"
    dependencies = find_evaluation_parameter_dependencies(parameter_expression)
    assert dependencies == {"urns": set(), "other": {"upstream_value"}}

    parameter_expression = "3"
    dependencies = find_evaluation_parameter_dependencies(parameter_expression)
    assert dependencies == {"urns": set(), "other": set()}


@pytest.mark.unit
def test_deduplicate_evaluation_parameter_dependencies():
    dependencies = {
        "profile": [
            {
                "metric_kwargs_id": {
                    "column=norm": [
                        "expect_column_mean_to_be_between.result.observed_value"
                    ]
                }
            },
            {
                "metric_kwargs_id": {
                    "column=norm": [
                        "expect_column_stdev_to_be_between.result.observed_value"
                    ]
                }
            },
        ]
    }

    deduplicated = _deduplicate_evaluation_parameter_dependencies(dependencies)

    # For test, use set to ignore order
    deduplicated["profile"][0]["metric_kwargs_id"]["column=norm"] = set(
        deduplicated["profile"][0]["metric_kwargs_id"]["column=norm"]
    )

    assert {
        "profile": [
            {
                "metric_kwargs_id": {
                    "column=norm": {
                        "expect_column_mean_to_be_between.result.observed_value",
                        "expect_column_stdev_to_be_between.result.observed_value",
                    }
                }
            }
        ]
    } == deduplicated


@pytest.mark.integration
@pytest.mark.parametrize(
    "dataframe,evaluation_parameters,expectation_type,expectation_kwargs,expected_expectation_validation_result",
    [
        (
            pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
            (
                ("my_min", 1),
                ("my_max", 5),
            ),
            "expect_table_row_count_to_be_between",
            {
                "min_value": {
                    "$PARAMETER": "my_min",
                    "$PARAMETER.upstream_row_count": 10,
                },
                "max_value": {
                    "$PARAMETER": "my_max",
                    "$PARAMETER.upstream_row_count": 50,
                },
            },
            ExpectationValidationResult(
                expectation_config={
                    "meta": {
                        "substituted_parameters": {"min_value": 1, "max_value": 5}
                    },
                    "kwargs": {
                        "min_value": 1,
                        "max_value": 5,
                        "batch_id": "15fe04adb6ff20b9fc6eda486b7a36b7",
                    },
                    "expectation_type": "expect_table_row_count_to_be_between",
                    "ge_cloud_id": None,
                },
                meta={},
                exception_info={
                    "raised_exception": False,
                    "exception_traceback": None,
                    "exception_message": None,
                },
                success=True,
                result={"observed_value": 3},
            ),
        ),
    ],
)
def test_evaluation_parameters_for_between_expectations_parse_correctly(
    titanic_pandas_data_context_with_v013_datasource_with_checkpoints_v1_with_empty_store_stats_enabled,
    dataframe,
    evaluation_parameters,
    expectation_type,
    expectation_kwargs,
    expected_expectation_validation_result,
):
    context = titanic_pandas_data_context_with_v013_datasource_with_checkpoints_v1_with_empty_store_stats_enabled

    expectation_suite_name = "test_suite"
    context.create_expectation_suite(expectation_suite_name=expectation_suite_name)

    validator = context.get_validator(
        batch_request=RuntimeBatchRequest(
            datasource_name="my_datasource",
            data_connector_name="my_runtime_data_connector",
            data_asset_name="foo",
            runtime_parameters={"batch_data": dataframe},
            batch_identifiers={
                "pipeline_stage_name": "kickoff",
                "airflow_run_id": "1234",
            },
        ),
        expectation_suite_name=expectation_suite_name,
    )

    for evaluation_parameter in evaluation_parameters:
        validator.set_evaluation_parameter(*evaluation_parameter)

    actual_expectation_validation_result = getattr(validator, expectation_type)(
        **expectation_kwargs
    )

    assert (
        actual_expectation_validation_result == expected_expectation_validation_result
    )


@pytest.mark.integration
def test_evaluation_parameters_for_between_expectations_parse_datetime_correctly(
    titanic_pandas_data_context_with_v013_datasource_with_checkpoints_v1_with_empty_store_stats_enabled,
):
    context = titanic_pandas_data_context_with_v013_datasource_with_checkpoints_v1_with_empty_store_stats_enabled

    # Note that if you modify this batch request, you may save the new version as a .json file
    #  to pass in later via the --batch-request option
    df = pandas.DataFrame(
        {
            "my_date": [
                datetime(year=2017, month=1, day=1),
                datetime(year=2018, month=1, day=1),
                datetime(year=2019, month=1, day=1),
                datetime(year=2020, month=1, day=1),
            ]
        }
    )
    batch_request = {
        "datasource_name": "my_datasource",
        "data_connector_name": "my_runtime_data_connector",
        "data_asset_name": "foo",
        "runtime_parameters": {"batch_data": df},
        "batch_identifiers": {
            "pipeline_stage_name": "kickoff",
            "airflow_run_id": "1234",
        },
    }

    # Feel free to change the name of your suite here. Renaming this will not remove the other one.
    expectation_suite_name = "abcde"
    try:
        suite = context.get_expectation_suite(
            expectation_suite_name=expectation_suite_name
        )
        print(
            f'Loaded ExpectationSuite "{suite.expectation_suite_name}" containing {len(suite.expectations)} '
            f"expectations."
        )
    except DataContextError:
        suite = context.create_expectation_suite(
            expectation_suite_name=expectation_suite_name
        )
        print(f'Created ExpectationSuite "{suite.expectation_suite_name}".')

    validator = context.get_validator(
        batch_request=RuntimeBatchRequest(**batch_request),
        expectation_suite_name=expectation_suite_name,
    )
    column_names = [
        f'"{column_name}"' for column_name in validator.metrics_calculator.columns()
    ]
    print(f"Columns: {', '.join(column_names)}.")

    validator.set_evaluation_parameter("my_min_date", datetime(2016, 12, 10))
    validator.set_evaluation_parameter(
        "my_max_date", datetime(2022, 12, 13) - pd.Timedelta(weeks=1)
    )

    actual_result = validator.expect_column_values_to_be_between(
        column="my_date",
        min_value={"$PARAMETER": "my_min_date"},
        max_value={"$PARAMETER": "my_max_date"},
    )

    expected_result = ExpectationValidationResult(
        **{
            "expectation_config": {
                "meta": {
                    "substituted_parameters": {
                        "min_value": "2016-12-10T00:00:00",
                        "max_value": "2022-12-06T00:00:00",
                    }
                },
                "kwargs": {
                    "column": "my_date",
                    "min_value": "2016-12-10T00:00:00",
                    "max_value": "2022-12-06T00:00:00",
                    "batch_id": "15fe04adb6ff20b9fc6eda486b7a36b7",
                },
                "expectation_type": "expect_column_values_to_be_between",
                "ge_cloud_id": None,
            },
            "meta": {},
            "exception_info": {
                "raised_exception": False,
                "exception_traceback": None,
                "exception_message": None,
            },
            "success": True,
            "result": {
                "element_count": 4,
                "unexpected_count": 0,
                "unexpected_percent": 0.0,
                "partial_unexpected_list": [],
                "missing_count": 0,
                "missing_percent": 0.0,
                "unexpected_percent_total": 0.0,
                "unexpected_percent_nonmissing": 0.0,
            },
        }
    )

    assert actual_result == expected_result


@pytest.mark.unit
def test_now_evaluation_parameter():
    """
    now() is unique in the fact that it is the only evaluation param built-in that has zero arity (takes no arguments).
    The following tests ensure that it is properly parsed and evaluated in a variety of contexts.
    """
    # By itself
    res = parse_evaluation_parameter("now()")
    assert dateutil.parser.parse(
        res
    ), "Provided evaluation parameter is not dateutil-parseable"

    # In conjunction with timedelta
    res = parse_evaluation_parameter("now() - timedelta(weeks=1)")
    assert dateutil.parser.parse(
        res
    ), "Provided evaluation parameter is not dateutil-parseable"

    # Require parens to actually invoke
    with pytest.raises(EvaluationParameterError):
        parse_evaluation_parameter("now")
