from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

import pandas as pd
import pytest
from pydantic import ValidationError

from great_expectations.checkpoint import SimpleCheckpoint
from great_expectations.checkpoint.types.checkpoint_result import CheckpointResult
from great_expectations.core.metric_function_types import MetricPartialFunctionTypes
from great_expectations.data_context import AbstractDataContext
from great_expectations.execution_engine import (
    ExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.import_manager import pyspark_sql_Row
from great_expectations.experimental.datasources.interfaces import (
    BatchRequest,
    DataAsset,
    Datasource,
)
from great_expectations.render import (
    AtomicDiagnosticRendererType,
    AtomicPrescriptiveRendererType,
)
from great_expectations.rule_based_profiler.data_assistant_result import (
    DataAssistantResult,
)
from great_expectations.validator.metric_configuration import MetricConfiguration

if TYPE_CHECKING:
    from great_expectations.experimental.datasources.interfaces import Batch
    from great_expectations.validator.computed_metric import MetricValue


def sql_data(
    context: AbstractDataContext,
) -> tuple[AbstractDataContext, Datasource, DataAsset, BatchRequest]:
    db_file = (
        pathlib.Path(__file__)
        / "../../../test_sets/taxi_yellow_tripdata_samples/sqlite/yellow_tripdata.db"
    ).resolve()
    datasource = context.sources.add_sqlite(
        name="test_datasource",
        connection_string=f"sqlite:///{db_file}",
    )
    asset = (
        datasource.add_table_asset(
            name="my_asset",
            table_name="yellow_tripdata_sample_2019_01",
        )
        .add_year_and_month_splitter(column_name="pickup_datetime")
        .add_sorters(["year", "month"])
    )
    batch_request = asset.get_batch_request({"year": 2019, "month": 1})
    return context, datasource, asset, batch_request


def pandas_data(
    context: AbstractDataContext,
) -> tuple[AbstractDataContext, Datasource, DataAsset, BatchRequest]:
    csv_path = (
        pathlib.Path(__file__) / "../../../test_sets/taxi_yellow_tripdata_samples"
    ).resolve()
    panda_ds = context.sources.add_pandas(name="my_pandas")
    asset = panda_ds.add_csv_asset(
        name="csv_asset",
        data_path=csv_path,
        regex=r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv",
        order_by=["year", "month"],
    )
    batch_request = asset.get_batch_request({"year": "2019", "month": "01"})
    return context, panda_ds, asset, batch_request


@pytest.fixture(params=[sql_data, pandas_data])
def datasource_test_data(
    empty_data_context, request
) -> tuple[AbstractDataContext, Datasource, DataAsset, BatchRequest]:
    return request.param(empty_data_context)


@pytest.mark.integration
@pytest.mark.parametrize("include_rendered_content", [False, True])
def test_run_checkpoint_and_data_doc(datasource_test_data, include_rendered_content):
    # context, datasource, asset, batch_request
    context, _, _, batch_request = datasource_test_data
    if include_rendered_content:
        context.variables.include_rendered_content.globally = True

    # Define an expectation suite
    suite_name = "my_suite"
    context.create_expectation_suite(expectation_suite_name=suite_name)
    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=suite_name,
    )
    validator.expect_table_row_count_to_be_between(0, 10000)
    validator.expect_column_max_to_be_between(
        column="passenger_count", min_value=1, max_value=7
    )
    validator.expect_column_median_to_be_between(
        column="passenger_count", min_value=1, max_value=4
    )
    validator.save_expectation_suite(discard_failed_expectations=False)

    # Configure and run a checkpoint
    checkpoint_config = {
        "class_name": "SimpleCheckpoint",
        "validations": [
            {"batch_request": batch_request, "expectation_suite_name": suite_name}
        ],
    }
    metadata = validator.active_batch.metadata
    checkpoint = SimpleCheckpoint(
        f"batch_with_year_{metadata['year']}_month_{metadata['month']}_{suite_name}",
        context,
        **checkpoint_config,
    )
    checkpoint_result = checkpoint.run()

    # Verify checkpoint runs successfully
    assert checkpoint_result._success, "Running expectation suite failed"
    number_of_runs = len(checkpoint_result.run_results)
    assert (
        number_of_runs == 1
    ), f"{number_of_runs} runs were done when we only expected 1"

    # Grab the validation result and verify it is correct
    result = checkpoint_result["run_results"][
        list(checkpoint_result["run_results"].keys())[0]
    ]
    validation_result = result["validation_result"]
    assert validation_result.success

    expected_metric_values = {
        "expect_table_row_count_to_be_between": {
            "value": 10000,
            "rendered_template": "Must have greater than or equal to $min_value and less than or equal to $max_value rows.",
        },
        "expect_column_max_to_be_between": {
            "value": 6,
            "rendered_template": "$column maximum value must be greater than or equal to $min_value and less than or equal to $max_value.",
        },
        "expect_column_median_to_be_between": {
            "value": 1,
            "rendered_template": "$column median must be greater than or equal to $min_value and less than or equal to $max_value.",
        },
    }
    assert len(validation_result.results) == 3

    for r in validation_result.results:
        assert r.success
        assert (
            r.result["observed_value"]
            == expected_metric_values[r.expectation_config.expectation_type]["value"]
        )

        if include_rendered_content:
            # There is a prescriptive atomic renderer on r.expectation_config
            num_prescriptive_renderer = len(r.expectation_config.rendered_content)
            assert (
                num_prescriptive_renderer == 1
            ), f"Expected exactly 1 rendered content, found {num_prescriptive_renderer}"
            rendered_content = r.expectation_config.rendered_content[0]
            assert rendered_content.name == AtomicPrescriptiveRendererType.SUMMARY
            assert (
                rendered_content.value.template
                == expected_metric_values[r.expectation_config.expectation_type][
                    "rendered_template"
                ]
            )

            # There is a diagnostic atomic renderer on r, a validation result result.
            num_diagnostic_render = len(r.rendered_content)
            assert (
                num_diagnostic_render == 1
            ), f"Expected 1 diagnostic renderer, found {num_diagnostic_render}"
            diagnostic_renderer = r.rendered_content[0]
            assert (
                diagnostic_renderer.name == AtomicDiagnosticRendererType.OBSERVED_VALUE
            )
            assert (
                diagnostic_renderer.value.schema["type"]
                == "com.superconductive.rendered.string"
            )
        else:
            assert r.rendered_content is None
            assert r.expectation_config.rendered_content is None

    # Rudimentary test for data doc generation
    docs_dict = context.build_data_docs()
    assert "local_site" in docs_dict, "build_data_docs returned dictionary has changed"
    assert docs_dict["local_site"].startswith(
        "file://"
    ), "build_data_docs returns file path in unexpected form"
    path = docs_dict["local_site"][7:]
    with open(path) as f:
        data_doc_index = f.read()

    # Checking for ge-success-icon tests the result table was generated and it was populated with a successful run.
    assert "ge-success-icon" in data_doc_index
    assert "ge-failed-icon" not in data_doc_index


@pytest.mark.integration
@pytest.mark.slow  # sql: 7s  # pandas: 4s
def test_run_data_assistant_and_checkpoint(datasource_test_data):
    context, _, _, batch_request = datasource_test_data
    data_assistant_result, checkpoint_result = _configure_and_run_data_assistant(
        context, batch_request
    )
    batch_num = len(
        data_assistant_result._batch_id_to_batch_identifier_display_name_map
    )
    assert batch_num == 1, f"Only expected 1 batch but found {batch_num}"

    # We assert the data assistant successfully generated expectations.
    # We don't care about the exact number since that may change as data assistants evolve.
    expectation_num = len(data_assistant_result.expectation_configurations)
    assert expectation_num > 100
    assert checkpoint_result.success, "Running expectation suite failed"
    # Verify that the number of checkpoint validations is the number of expectations generated by the data assistant
    assert (
        len(
            checkpoint_result["run_results"][
                list(checkpoint_result["run_results"].keys())[0]
            ]["validation_result"].results
        )
        == expectation_num
    )


def multibatch_sql_data(
    context: AbstractDataContext,
) -> tuple[AbstractDataContext, Datasource, DataAsset, BatchRequest]:
    db_file = (
        pathlib.Path(__file__)
        / "../../../test_sets/taxi_yellow_tripdata_samples/sqlite/yellow_tripdata_sample_2020_all_months_combined.db"
    ).resolve()
    datasource = context.sources.add_sqlite(
        name="test_datasource",
        connection_string=f"sqlite:///{db_file}",
    )
    asset = (
        datasource.add_table_asset(
            name="my_asset",
            table_name="yellow_tripdata_sample_2020",
        )
        .add_year_and_month_splitter(column_name="pickup_datetime")
        .add_sorters(["year", "month"])
    )
    batch_request = asset.get_batch_request({"year": 2020})
    return context, datasource, asset, batch_request


def multibatch_pandas_data(
    context: AbstractDataContext,
) -> tuple[AbstractDataContext, Datasource, DataAsset, BatchRequest]:
    csv_path = (
        pathlib.Path(__file__) / "../../../test_sets/taxi_yellow_tripdata_samples"
    ).resolve()
    panda_ds = context.sources.add_pandas(name="my_pandas")
    asset = panda_ds.add_csv_asset(
        name="csv_asset",
        data_path=csv_path,
        regex=r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv",
        order_by=["year", "month"],
    )
    batch_request = asset.get_batch_request({"year": "2020"})
    return context, panda_ds, asset, batch_request


@pytest.fixture(params=[multibatch_sql_data, multibatch_pandas_data])
def multibatch_datasource_test_data(
    empty_data_context, request
) -> tuple[AbstractDataContext, Datasource, DataAsset, BatchRequest]:
    return request.param(empty_data_context)


@pytest.mark.integration
@pytest.mark.slow  # sql: 33s  # pandas: 9s
def test_run_multibatch_data_assistant_and_checkpoint(multibatch_datasource_test_data):
    """Test using data assistants to create expectation suite using multiple batches and to run checkpoint"""
    context, _, _, batch_request = multibatch_datasource_test_data
    data_assistant_result, checkpoint_result = _configure_and_run_data_assistant(
        context, batch_request
    )
    # Assert multiple batches were processed
    batch_num = len(
        data_assistant_result._batch_id_to_batch_identifier_display_name_map
    )
    assert batch_num == 12, f"Expected exactly 12 batches but found {batch_num}"

    expectation_num = len(data_assistant_result.expectation_configurations)
    assert expectation_num > 100
    assert checkpoint_result.success, "Running expectation suite failed"
    # Verify that the number of checkpoint validations is the number of expectations generated by the data assistant
    assert (
        len(
            checkpoint_result["run_results"][
                list(checkpoint_result["run_results"].keys())[0]
            ]["validation_result"].results
        )
        == expectation_num
    )


def _configure_and_run_data_assistant(
    context: AbstractDataContext,
    batch_request: BatchRequest,
) -> tuple[DataAssistantResult, CheckpointResult]:
    expectation_suite_name = "my_onboarding_assistant_suite"
    context.create_expectation_suite(
        expectation_suite_name=expectation_suite_name, overwrite_existing=True
    )
    data_assistant_result = context.assistants.onboarding.run(
        batch_request=batch_request,
        numeric_columns_rule={
            "estimator": "exact",
            "random_seed": 2022080401,
        },
        # We exclude congestion_surcharge due to this bug:
        # https://greatexpectations.atlassian.net/browse/GREAT-1465
        exclude_column_names=["congestion_surcharge"],
    )
    expectation_suite = data_assistant_result.get_expectation_suite(
        expectation_suite_name=expectation_suite_name
    )
    context.save_expectation_suite(
        expectation_suite=expectation_suite, discard_failed_expectations=False
    )

    # Run a checkpoint
    checkpoint_config = {
        "class_name": "SimpleCheckpoint",
        "validations": [
            {
                "batch_request": batch_request,
                "expectation_suite_name": expectation_suite_name,
            }
        ],
    }
    checkpoint = SimpleCheckpoint(
        f"yellow_tripdata_sample_{expectation_suite_name}",
        context,
        **checkpoint_config,
    )
    checkpoint_result = checkpoint.run()

    return data_assistant_result, checkpoint_result


@pytest.mark.integration
@pytest.mark.parametrize(
    ["n_rows", "success"],
    [
        (
            None,
            True,
        ),
        (
            3,
            True,
        ),
        (
            7,
            True,
        ),
        (
            -100,
            True,
        ),
        (
            "invalid_value",
            False,
        ),
        (
            1.5,
            False,
        ),
        (
            0,
            True,
        ),
        (
            200000,
            True,
        ),
        (
            1,
            True,
        ),
        (
            -50000,
            True,
        ),
    ],
)
def test_batch_head(
    datasource_test_data: tuple[
        AbstractDataContext, Datasource, DataAsset, BatchRequest
    ],
    n_rows: int | float | str | None,
    success: bool,
) -> None:
    _, datasource, _, batch_request = datasource_test_data
    batch_list: list[Batch] = datasource.get_batch_list_from_batch_request(
        batch_request=batch_request
    )
    assert len(batch_list) > 0

    # arbitrarily select the first batch for testing
    batch: Batch = batch_list[0]
    if success:
        execution_engine: ExecutionEngine = batch.data.execution_engine
        execution_engine.batch_manager.load_batch_list(batch_list=[batch])
        resolved_metrics: dict[tuple[str, str, str], MetricValue] = {}

        # get the expected column names
        table_column_types_metric = MetricConfiguration(
            metric_name="table.column_types",
            metric_domain_kwargs={"batch_id": batch.id},
            metric_value_kwargs={
                "include_nested": True,
            },
        )
        resolved_metrics.update(
            execution_engine.resolve_metrics(
                metrics_to_resolve=(table_column_types_metric,)
            )
        )
        table_columns_metric = MetricConfiguration(
            metric_name="table.columns",
            metric_domain_kwargs={"batch_id": batch.id},
            metric_value_kwargs=None,
        )
        table_columns_metric.metric_dependencies = {
            "table.column_types": table_column_types_metric,
        }
        resolved_metrics.update(
            execution_engine.resolve_metrics(
                metrics_to_resolve=(table_columns_metric,), metrics=resolved_metrics
            )
        )
        expected_columns: set[str] = set(resolved_metrics[table_columns_metric.id])

        head_df: pd.DataFrame
        if n_rows is not None:
            # if n_rows is not None we pass it to Batch.head()
            head_df = batch.head(n_rows=n_rows)
            # the set of types returned by pd.DataFrame.head() and pyspark.sql.DataFrame.head()
            if pyspark_sql_Row and isinstance(head_df, list):
                assert all(isinstance(row, pyspark_sql_Row) for row in head_df)
                assert all(set(row.asDict()) == expected_columns for row in head_df)
            elif pyspark_sql_Row and isinstance(head_df, pyspark_sql_Row):
                assert set(head_df.asDict()) == expected_columns
            else:
                assert isinstance(head_df, pd.DataFrame)
                assert set(head_df.columns) == expected_columns

            # compute the total number of rows
            row_count_metric = MetricConfiguration(
                metric_name="table.row_count",
                metric_domain_kwargs={"batch_id": batch.id},
                metric_value_kwargs=None,
            )
            if isinstance(execution_engine, SqlAlchemyExecutionEngine):
                row_count_partial_fn_metric = MetricConfiguration(
                    metric_name=f"table.row_count.{MetricPartialFunctionTypes.AGGREGATE_FN.metric_suffix}",
                    metric_domain_kwargs={"batch_id": batch.id},
                    metric_value_kwargs=None,
                )
                resolved_metrics.update(
                    execution_engine.resolve_metrics(
                        metrics_to_resolve=(row_count_partial_fn_metric,)
                    )
                )
                row_count_metric.metric_dependencies = {
                    "metric_partial_fn": row_count_partial_fn_metric
                }

            resolved_metrics = execution_engine.resolve_metrics(
                metrics_to_resolve=(row_count_metric,), metrics=resolved_metrics
            )
            total_row_count: int = resolved_metrics[row_count_metric.id]

            # count the number of rows in head_df depending on return type
            head_df_row_count: int
            if pyspark_sql_Row and isinstance(head_df, pyspark_sql_Row):
                head_df_row_count = 1
            elif isinstance(head_df, pd.DataFrame):
                head_df_row_count = len(head_df.index)
            else:
                head_df_row_count = len(head_df)

            # if n_rows is between 0 and the total_row_count, that's how many rows we expect
            if 0 <= n_rows <= total_row_count:
                assert head_df_row_count == n_rows
            # if n_rows is greater than the total_row_count, we only expect total_row_count rows
            elif n_rows > total_row_count:
                assert head_df_row_count == total_row_count
            # if n_rows is negative and abs(n_rows) is larger than total_row_count we expect zero rows
            elif n_rows < 0 and abs(n_rows) > total_row_count:
                assert head_df_row_count == 0
            # if n_rows is negative, we expect all but the final abs(n_rows)
            else:
                assert head_df_row_count == n_rows + total_row_count
        else:
            # default to 5 rows
            head_df = batch.head()
            assert isinstance(head_df, pd.DataFrame)
            assert len(head_df.index) == 5
            assert set(head_df.columns) == expected_columns
    else:
        with pytest.raises(ValidationError) as e:
            batch.head(n_rows=n_rows)
        assert str(e.value) == (
            "1 validation error for Head\n"
            "n_rows\n"
            "  value is not a valid integer (type=type_error.integer)"
        )
