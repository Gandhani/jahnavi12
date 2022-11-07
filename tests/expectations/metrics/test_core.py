import copy
import datetime
import logging
from typing import Union

import numpy as np
import pandas as pd
import pytest

import great_expectations.exceptions as ge_exceptions
from great_expectations.core.batch import Batch
from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
)
from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    SqlAlchemyBatchData,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.import_manager import pyspark_sql_Column
from great_expectations.expectations.registry import get_metric_provider
from great_expectations.self_check.util import (
    build_pandas_engine,
    build_sa_engine,
    build_spark_engine,
)
from great_expectations.util import isclose
from great_expectations.validator.metric_configuration import MetricConfiguration
from tests.expectations.test_util import get_table_columns_metric


def test_metric_loads_pd():
    assert get_metric_provider("column.max", PandasExecutionEngine()) is not None


def test_basic_metric_pd():
    df = pd.DataFrame({"a": [1, 2, 3, 3, None]})
    batch = Batch(data=df)
    engine = PandasExecutionEngine(batch_data_dict={batch.id: batch.data})

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: 3}


def test_mean_metric_pd():
    engine = build_pandas_engine(pd.DataFrame({"a": [1, 2, 3, None]}))

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.mean",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: 2}


def test_stdev_metric_pd():
    engine = build_pandas_engine(pd.DataFrame({"a": [1, 2, 3, None]}))

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.standard_deviation",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: 1}


def test_column_value_lengths_min_metric_pd():
    engine = build_pandas_engine(
        pd.DataFrame(
            {
                "names": [
                    "Ada Lovelace",
                    "Alan Kay",
                    "Donald Knuth",
                    "Edsger Dijkstra",
                    "Guido van Rossum",
                    "John McCarthy",
                    "Marvin Minsky",
                    "Ray Ozzie",
                ]
            }
        )
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column_values.length.min",
        metric_domain_kwargs={"column": "names"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: 8}


def test_column_value_lengths_min_metric_sa(sa):
    engine = build_sa_engine(
        pd.DataFrame(
            {
                "names": [
                    "Ada Lovelace",
                    "Alan Kay",
                    "Donald Knuth",
                    "Edsger Dijkstra",
                    "Guido van Rossum",
                    "John McCarthy",
                    "Marvin Minsky",
                    "Ray Ozzie",
                ]
            }
        ),
        sa,
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    aggregate_fn_metric = MetricConfiguration(
        metric_name="column_values.length.min.aggregate_fn",
        metric_domain_kwargs={
            "column": "names",
        },
        metric_value_kwargs=None,
    )
    aggregate_fn_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(metrics_to_resolve=(aggregate_fn_metric,))

    desired_metric = MetricConfiguration(
        metric_name="column_values.length.min",
        metric_domain_kwargs={},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "metric_partial_fn": aggregate_fn_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=results
    )

    assert results == {desired_metric.id: 8}


def test_column_value_lengths_min_metric_spark(spark_session):
    engine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            {
                "names": [
                    "Ada Lovelace",
                    "Alan Kay",
                    "Donald Knuth",
                    "Edsger Dijkstra",
                    "Guido van Rossum",
                    "John McCarthy",
                    "Marvin Minsky",
                    "Ray Ozzie",
                ]
            }
        ),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    aggregate_fn_metric = MetricConfiguration(
        metric_name="column_values.length.min.aggregate_fn",
        metric_domain_kwargs={
            "column": "names",
        },
        metric_value_kwargs=None,
    )
    aggregate_fn_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(metrics_to_resolve=(aggregate_fn_metric,))

    desired_metric = MetricConfiguration(
        metric_name="column_values.length.min",
        metric_domain_kwargs={},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "metric_partial_fn": aggregate_fn_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=results
    )

    assert results == {desired_metric.id: 8}


def test_column_value_lengths_max_metric_pd():
    engine = build_pandas_engine(
        pd.DataFrame(
            {
                "names": [
                    "Ada Lovelace",
                    "Alan Kay",
                    "Donald Knuth",
                    "Edsger Dijkstra",
                    "Guido van Rossum",
                    "John McCarthy",
                    "Marvin Minsky",
                    "Ray Ozzie",
                ]
            }
        )
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column_values.length.max",
        metric_domain_kwargs={"column": "names"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: 16}


def test_column_value_lengths_max_metric_sa(sa):
    engine = build_sa_engine(
        pd.DataFrame(
            {
                "names": [
                    "Ada Lovelace",
                    "Alan Kay",
                    "Donald Knuth",
                    "Edsger Dijkstra",
                    "Guido van Rossum",
                    "John McCarthy",
                    "Marvin Minsky",
                    "Ray Ozzie",
                ]
            }
        ),
        sa,
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    aggregate_fn_metric = MetricConfiguration(
        metric_name="column_values.length.max.aggregate_fn",
        metric_domain_kwargs={
            "column": "names",
        },
        metric_value_kwargs=None,
    )
    aggregate_fn_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(metrics_to_resolve=(aggregate_fn_metric,))

    desired_metric = MetricConfiguration(
        metric_name="column_values.length.max",
        metric_domain_kwargs={},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "metric_partial_fn": aggregate_fn_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=results
    )

    assert results == {desired_metric.id: 16}


def test_column_value_lengths_max_metric_spark(spark_session):
    engine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            {
                "names": [
                    "Ada Lovelace",
                    "Alan Kay",
                    "Donald Knuth",
                    "Edsger Dijkstra",
                    "Guido van Rossum",
                    "John McCarthy",
                    "Marvin Minsky",
                    "Ray Ozzie",
                ]
            }
        ),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    aggregate_fn_metric = MetricConfiguration(
        metric_name="column_values.length.max.aggregate_fn",
        metric_domain_kwargs={
            "column": "names",
        },
        metric_value_kwargs=None,
    )
    aggregate_fn_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(metrics_to_resolve=(aggregate_fn_metric,))

    desired_metric = MetricConfiguration(
        metric_name="column_values.length.max",
        metric_domain_kwargs={},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "metric_partial_fn": aggregate_fn_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=results
    )

    assert results == {desired_metric.id: 16}


def test_quantiles_metric_pd():
    engine = build_pandas_engine(pd.DataFrame({"a": [1, 2, 3, 4]}))

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.quantile_values",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "quantiles": [2.5e-1, 5.0e-1, 7.5e-1],
            "allow_relative_error": "linear",
        },
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: [1.75, 2.5, 3.25]}


def test_quantiles_metric_sa(sa):
    engine = build_sa_engine(pd.DataFrame({"a": [1, 2, 3, 4]}), sa)

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    partial_metric = MetricConfiguration(
        metric_name="table.row_count.aggregate_fn",
        metric_domain_kwargs={},
        metric_value_kwargs=None,
    )

    results = engine.resolve_metrics(
        metrics_to_resolve=(partial_metric,), metrics=metrics
    )
    metrics.update(results)

    table_row_count_metric = MetricConfiguration(
        metric_name="table.row_count",
        metric_domain_kwargs={},
        metric_value_kwargs=None,
    )
    table_row_count_metric._metric_dependencies = {
        "metric_partial_fn": partial_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(table_row_count_metric,), metrics=metrics
    )
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.quantile_values",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "quantiles": [2.5e-1, 5.0e-1, 7.5e-1],
        },
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
        "table.row_count": table_row_count_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: [1.0, 2.0, 3.0]}


def test_quantiles_metric_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame({"a": [1, 2, 3, 4]}),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.quantile_values",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "quantiles": [2.5e-1, 5.0e-1, 7.5e-1],
        },
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: [1.0, 2.0, 3.0]}


def test_column_histogram_metric_pd():
    engine = build_pandas_engine(
        pd.DataFrame(
            {
                "a": [
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                ]
            }
        )
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.histogram",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "bins": [0.0, 0.9, 1.8, 2.7, 3.6, 4.5, 5.4, 6.3, 7.2, 8.1, 9.0],
        },
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}


def test_column_histogram_metric_sa(sa):
    engine = build_sa_engine(
        pd.DataFrame(
            {
                "a": [
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                ],
                "b": [
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                ],
            }
        ),
        sa,
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.histogram",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "bins": [0.0, 0.9, 1.8, 2.7, 3.6, 4.5, 5.4, 6.3, 7.2, 8.1, 9.0],
        },
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}

    desired_metric = MetricConfiguration(
        metric_name="column.histogram",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs={
            "bins": [0.0],
        },
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: [10]}


def test_column_histogram_metric_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            {
                "a": [
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                ]
            }
        ),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.histogram",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "bins": [0.0, 0.9, 1.8, 2.7, 3.6, 4.5, 5.4, 6.3, 7.2, 8.1, 9.0],
        },
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}


def test_column_partition_metric_pd():
    """
    Test of "column.partition" metric for both, standard numeric column and "datetime.datetime" valued column.

    The "column.partition" metric depends on "column.max" metric and on "column.max" metric.

    For "PandasExecutionEngine", explicit values of these metrics are needed.

    For standard numerical data, test set contains 12 evenly spaced integers.
    For "datetime.datetime" data, test set contains 12 dates, starting with January 1, 2021, separated by 7 days.

    Expected partition boundaries are pre-computed algorithmically and asserted to be "close" to actual metric values.
    """
    week_idx: int
    engine = build_pandas_engine(
        pd.DataFrame(
            {
                "a": [
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                ],
                "b": [
                    datetime.datetime(2021, 1, 1, 0, 0, 0)
                    + datetime.timedelta(days=(week_idx * 7))
                    for week_idx in range(12)
                ],
            },
        ),
    )

    seconds_in_week: int = 604800

    n_bins: int = 10

    increment: Union[float, datetime.timedelta]
    idx: int
    element: Union[float, pd.Timestamp]

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    # Test using standard numeric column.

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    column_min_metric: MetricConfiguration = MetricConfiguration(
        metric_name="column.min",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": False,
        },
    )
    column_min_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    column_max_metric: MetricConfiguration = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": False,
        },
    )
    column_max_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(
            column_min_metric,
            column_max_metric,
        ),
        metrics=metrics,
    )
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.partition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "bins": "uniform",
            "n_bins": n_bins,
            "allow_relative_error": False,
        },
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
        "column.min": column_min_metric,
        "column.max": column_max_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)

    increment = float(n_bins + 1) / n_bins
    assert all(
        isclose(operand_a=element, operand_b=(increment * idx))
        for idx, element in enumerate(results[desired_metric.id])
    )

    # Test using "datetime.datetime" column.

    metrics = {}
    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    column_min_metric: MetricConfiguration = MetricConfiguration(
        metric_name="column.min",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": True,
        },
    )
    column_min_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    column_max_metric: MetricConfiguration = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": True,
        },
    )
    column_max_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(
            column_min_metric,
            column_max_metric,
        ),
        metrics=metrics,
    )
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.partition",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs={
            "bins": "uniform",
            "n_bins": n_bins,
            "allow_relative_error": False,
        },
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
        "column.min": column_min_metric,
        "column.max": column_max_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)

    increment = datetime.timedelta(
        seconds=(seconds_in_week * float(n_bins + 1) / n_bins)
    )
    assert all(
        isclose(
            operand_a=element.to_pydatetime(),
            operand_b=(datetime.datetime(2021, 1, 1, 0, 0, 0) + (increment * idx)),
        )
        for idx, element in enumerate(results[desired_metric.id])
    )


def test_column_partition_metric_sa(sa):
    """
    Test of "column.partition" metric for both, standard numeric column and "datetime.datetime" valued column.

    The "column.partition" metric depends on "column.max" metric and on "column.max" metric.

    For "SqlAlchemyExecutionEngine", explicit values of these metrics are needed, each requiring a "metric_partial_fn",
    corresponding to "column.min.aggregate_fn" metric and "column.max.aggregate_fn" metric, respectively, resolved.

    For standard numerical data, test set contains 12 evenly spaced integers.
    For "datetime.datetime" data, test set contains 12 dates, starting with January 1, 2021, separated by 7 days.

    Expected partition boundaries are pre-computed algorithmically and asserted to be "close" to actual metric values.
    """
    week_idx: int
    engine = build_sa_engine(
        pd.DataFrame(
            {
                "a": [
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                ],
                "b": [
                    datetime.datetime(2021, 1, 1, 0, 0, 0)
                    + datetime.timedelta(days=(week_idx * 7))
                    for week_idx in range(12)
                ],
            },
        ),
        sa,
    )

    seconds_in_week: int = 604800

    n_bins: int = 10

    increment: Union[float, datetime.timedelta]
    idx: int
    element: Union[float, pd.Timestamp]

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    # Test using standard numeric column.

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    partial_column_min_metric = MetricConfiguration(
        metric_name="column.min.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    partial_column_min_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    partial_column_max_metric = MetricConfiguration(
        metric_name="column.max.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    partial_column_max_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(
            partial_column_min_metric,
            partial_column_max_metric,
        ),
        metrics=metrics,
    )
    metrics.update(results)

    column_min_metric: MetricConfiguration = MetricConfiguration(
        metric_name="column.min",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": False,
        },
    )
    column_min_metric._metric_dependencies = {
        "metric_partial_fn": partial_column_min_metric,
        "table.columns": table_columns_metric,
    }
    column_max_metric: MetricConfiguration = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": False,
        },
    )
    column_max_metric._metric_dependencies = {
        "metric_partial_fn": partial_column_max_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(
            column_min_metric,
            column_max_metric,
        ),
        metrics=metrics,
    )
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.partition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "bins": "uniform",
            "n_bins": n_bins,
            "allow_relative_error": False,
        },
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
        "column.min": column_min_metric,
        "column.max": column_max_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)

    increment = float(n_bins + 1) / n_bins
    assert all(
        isclose(operand_a=element, operand_b=(increment * idx))
        for idx, element in enumerate(results[desired_metric.id])
    )

    # Test using "datetime.datetime" column.

    metrics = {}
    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    partial_column_min_metric = MetricConfiguration(
        metric_name="column.min.aggregate_fn",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs=None,
    )
    partial_column_min_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    partial_column_max_metric = MetricConfiguration(
        metric_name="column.max.aggregate_fn",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs=None,
    )
    partial_column_max_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(
            partial_column_min_metric,
            partial_column_max_metric,
        ),
        metrics=metrics,
    )
    metrics.update(results)

    column_min_metric: MetricConfiguration = MetricConfiguration(
        metric_name="column.min",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": True,
        },
    )
    column_min_metric._metric_dependencies = {
        "metric_partial_fn": partial_column_min_metric,
        "table.columns": table_columns_metric,
    }
    column_max_metric: MetricConfiguration = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": True,
        },
    )
    column_max_metric._metric_dependencies = {
        "metric_partial_fn": partial_column_max_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(
            column_min_metric,
            column_max_metric,
        ),
        metrics=metrics,
    )
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.partition",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs={
            "bins": "uniform",
            "n_bins": n_bins,
            "allow_relative_error": False,
        },
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
        "column.min": column_min_metric,
        "column.max": column_max_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)

    increment = datetime.timedelta(
        seconds=(seconds_in_week * float(n_bins + 1) / n_bins)
    )
    assert all(
        isclose(
            operand_a=element,
            operand_b=(datetime.datetime(2021, 1, 1, 0, 0, 0) + (increment * idx)),
        )
        for idx, element in enumerate(results[desired_metric.id])
    )


def test_column_partition_metric_spark(spark_session):
    """
    Test of "column.partition" metric for both, standard numeric column and "datetime.datetime" valued column.

    The "column.partition" metric depends on "column.max" metric and on "column.max" metric.

    For "SparkDFExecutionEngine", explicit values of these metrics are needed, each requiring a "metric_partial_fn",
    corresponding to "column.min.aggregate_fn" metric and "column.max.aggregate_fn" metric, respectively, resolved.

    For standard numerical data, test set contains 12 evenly spaced integers.
    For "datetime.datetime" data, test set contains 12 dates, starting with January 1, 2021, separated by 7 days.

    Expected partition boundaries are pre-computed algorithmically and asserted to be "close" to actual metric values.
    """
    from great_expectations.expectations.metrics.import_manager import sparktypes

    week_idx: int
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            {
                "a": [
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                ],
                "b": [
                    datetime.datetime(2021, 1, 1, 0, 0, 0)
                    + datetime.timedelta(days=(week_idx * 7))
                    for week_idx in range(12)
                ],
            },
        ),
        schema=sparktypes.StructType(
            [
                sparktypes.StructField("a", sparktypes.IntegerType(), True),
                sparktypes.StructField("b", sparktypes.TimestampType(), True),
            ]
        ),
        batch_id="my_id",
    )

    seconds_in_week: int = 604800

    n_bins: int = 10

    increment: Union[float, datetime.timedelta]
    idx: int
    element: Union[float, pd.Timestamp]

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    # Test using standard numeric column.

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    partial_column_min_metric = MetricConfiguration(
        metric_name="column.min.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    partial_column_min_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    partial_column_max_metric = MetricConfiguration(
        metric_name="column.max.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    partial_column_max_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(
            partial_column_min_metric,
            partial_column_max_metric,
        ),
        metrics=metrics,
    )
    metrics.update(results)

    column_min_metric: MetricConfiguration = MetricConfiguration(
        metric_name="column.min",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": False,
        },
    )
    column_min_metric._metric_dependencies = {
        "metric_partial_fn": partial_column_min_metric,
        "table.columns": table_columns_metric,
    }
    column_max_metric: MetricConfiguration = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": False,
        },
    )
    column_max_metric._metric_dependencies = {
        "metric_partial_fn": partial_column_max_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(
            column_min_metric,
            column_max_metric,
        ),
        metrics=metrics,
    )
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.partition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "bins": "uniform",
            "n_bins": n_bins,
            "allow_relative_error": False,
        },
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
        "column.min": column_min_metric,
        "column.max": column_max_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)

    increment = float(n_bins + 1) / n_bins
    assert all(
        isclose(operand_a=element, operand_b=(increment * idx))
        for idx, element in enumerate(results[desired_metric.id])
    )

    # Test using "datetime.datetime" column.

    metrics = {}
    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    partial_column_min_metric = MetricConfiguration(
        metric_name="column.min.aggregate_fn",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs=None,
    )
    partial_column_min_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    partial_column_max_metric = MetricConfiguration(
        metric_name="column.max.aggregate_fn",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs=None,
    )
    partial_column_max_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(
            partial_column_min_metric,
            partial_column_max_metric,
        ),
        metrics=metrics,
    )
    metrics.update(results)

    column_min_metric: MetricConfiguration = MetricConfiguration(
        metric_name="column.min",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": True,
        },
    )
    column_min_metric._metric_dependencies = {
        "metric_partial_fn": partial_column_min_metric,
        "table.columns": table_columns_metric,
    }
    column_max_metric: MetricConfiguration = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": True,
        },
    )
    column_max_metric._metric_dependencies = {
        "metric_partial_fn": partial_column_max_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(
            column_min_metric,
            column_max_metric,
        ),
        metrics=metrics,
    )
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.partition",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs={
            "bins": "uniform",
            "n_bins": n_bins,
            "allow_relative_error": False,
        },
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
        "column.min": column_min_metric,
        "column.max": column_max_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)

    increment = datetime.timedelta(
        seconds=(seconds_in_week * float(n_bins + 1) / n_bins)
    )
    assert all(
        isclose(
            operand_a=element,
            operand_b=(datetime.datetime(2021, 1, 1, 0, 0, 0) + (increment * idx)),
        )
        for idx, element in enumerate(results[desired_metric.id])
    )


def test_max_metric_column_exists_pd():
    df = pd.DataFrame({"a": [1, 2, 3, 3, None]})
    batch = Batch(data=df)
    engine = PandasExecutionEngine(batch_data_dict={batch.id: batch.data})

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: 3}


def test_max_metric_column_does_not_exist_pd():
    df = pd.DataFrame({"a": [1, 2, 3, 3, None]})
    batch = Batch(data=df)
    engine = PandasExecutionEngine(batch_data_dict={batch.id: batch.data})

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "non_existent_column"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    with pytest.raises(ge_exceptions.MetricResolutionError) as eee:
        # noinspection PyUnusedLocal
        results = engine.resolve_metrics(
            metrics_to_resolve=(desired_metric,), metrics=metrics
        )
        metrics.update(results)
    assert (
        str(eee.value)
        == 'Error: The column "non_existent_column" in BatchData does not exist.'
    )


def test_max_metric_column_exists_sa(sa):
    engine = build_sa_engine(pd.DataFrame({"a": [1, 2, 1, None]}), sa)

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    partial_metric = MetricConfiguration(
        metric_name="column.max.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    partial_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(partial_metric,), metrics=metrics
    )
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "metric_partial_fn": partial_metric,
        "table.columns": table_columns_metric,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: 2}


def test_max_metric_column_does_not_exist_sa(sa):
    engine = build_sa_engine(pd.DataFrame({"a": [1, 2, 1, None]}), sa)

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    partial_metric = MetricConfiguration(
        metric_name="column.max.aggregate_fn",
        metric_domain_kwargs={"column": "non_existent_column"},
        metric_value_kwargs=None,
    )
    partial_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    with pytest.raises(ge_exceptions.MetricResolutionError) as eee:
        # noinspection PyUnusedLocal
        results = engine.resolve_metrics(
            metrics_to_resolve=(partial_metric,), metrics=metrics
        )
        metrics.update(results)
    assert (
        'Error: The column "non_existent_column" in BatchData does not exist.'
        in str(eee.value)
    )


def test_max_metric_column_exists_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame({"a": [1, 2, 1]}),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    partial_metric = MetricConfiguration(
        metric_name="column.max.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    partial_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(partial_metric,), metrics=metrics
    )
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "metric_partial_fn": partial_metric,
        "table.columns": table_columns_metric,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: 2}


def test_max_metric_column_does_not_exist_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame({"a": [1, 2, 1]}),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    partial_metric = MetricConfiguration(
        metric_name="column.max.aggregate_fn",
        metric_domain_kwargs={"column": "non_existent_column"},
        metric_value_kwargs=None,
    )
    partial_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    with pytest.raises(ge_exceptions.MetricResolutionError) as eee:
        # noinspection PyUnusedLocal
        results = engine.resolve_metrics(
            metrics_to_resolve=(partial_metric,), metrics=metrics
        )
        metrics.update(results)
    assert (
        str(eee.value)
        == 'Error: The column "non_existent_column" in BatchData does not exist.'
    )


def test_map_value_set_sa(sa):
    engine = build_sa_engine(pd.DataFrame({"a": [1, 2, 3, 3, None]}), sa)

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column_values.in_set.condition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"value_set": [1, 2, 3]},
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    metrics = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )

    # Note: metric_dependencies is optional here in the config when called from a validator.
    aggregate_partial = MetricConfiguration(
        metric_name="column_values.in_set.unexpected_count.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"value_set": [1, 2, 3]},
    )
    aggregate_partial._metric_dependencies = {
        "unexpected_condition": desired_metric,
    }

    metrics = engine.resolve_metrics(
        metrics_to_resolve=(aggregate_partial,), metrics=metrics
    )
    desired_metric = MetricConfiguration(
        metric_name="column_values.in_set.unexpected_count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"value_set": [1, 2, 3]},
    )
    desired_metric._metric_dependencies = {
        "metric_partial_fn": aggregate_partial,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    assert results == {desired_metric.id: 0}


def test_map_of_type_sa(sa):
    eng = sa.create_engine("sqlite://")
    df = pd.DataFrame({"a": [1, 2, 3, 3, None]})
    df.to_sql(name="test", con=eng, index=False)
    batch_data = SqlAlchemyBatchData(
        execution_engine=eng, table_name="test", source_table_name="test"
    )
    engine = SqlAlchemyExecutionEngine(
        engine=eng, batch_data_dict={"my_id": batch_data}
    )
    desired_metric = MetricConfiguration(
        metric_name="table.column_types",
        metric_domain_kwargs={},
        metric_value_kwargs=None,
    )

    results = engine.resolve_metrics(metrics_to_resolve=(desired_metric,))
    assert results[desired_metric.id][0]["name"] == "a"
    assert isinstance(results[desired_metric.id][0]["type"], sa.FLOAT)


def test_map_value_set_spark(spark_session, basic_spark_df_execution_engine):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            {"a": [1, 2, 3, 3, None]},
        ),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_values.in_set.condition",
        metric_domain_kwargs={
            "column": "a",
        },
        metric_value_kwargs={
            "value_set": [1, 2, 3],
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,), metrics=metrics
    )
    metrics.update(results)

    # Note: metric_dependencies is optional here in the config when called from a validator.
    aggregate_partial = MetricConfiguration(
        metric_name="column_values.in_set.unexpected_count.aggregate_fn",
        metric_domain_kwargs={
            "column": "a",
        },
        metric_value_kwargs={
            "value_set": [1, 2, 3],
        },
    )
    aggregate_partial._metric_dependencies = {
        "unexpected_condition": condition_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(aggregate_partial,), metrics=metrics
    )
    metrics.update(results)
    desired_metric = MetricConfiguration(
        metric_name="column_values.in_set.unexpected_count",
        metric_domain_kwargs={
            "column": "a",
        },
        metric_value_kwargs={
            "value_set": [1, 2, 3],
        },
    )
    desired_metric._metric_dependencies = {
        "metric_partial_fn": aggregate_partial,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: 0}

    # We run the same computation again, this time with None being replaced by nan instead of NULL
    # to demonstrate this behavior
    df = pd.DataFrame({"a": [1, 2, 3, 3, None]})
    df = spark_session.createDataFrame(df)
    engine = basic_spark_df_execution_engine
    engine.load_batch_data(batch_id="my_id", batch_data=df)

    condition_metric = MetricConfiguration(
        metric_name="column_values.in_set.condition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"value_set": [1, 2, 3]},
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,), metrics=metrics
    )
    metrics.update(results)

    # Note: metric_dependencies is optional here in the config when called from a validator.
    aggregate_partial = MetricConfiguration(
        metric_name="column_values.in_set.unexpected_count.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"value_set": [1, 2, 3]},
    )
    aggregate_partial._metric_dependencies = {
        "unexpected_condition": condition_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(aggregate_partial,), metrics=metrics
    )
    metrics.update(results)
    desired_metric = MetricConfiguration(
        metric_name="column_values.in_set.unexpected_count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"value_set": [1, 2, 3]},
    )
    desired_metric._metric_dependencies = {
        "metric_partial_fn": aggregate_partial,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: 1}


def test_map_column_value_lengths_between_pd():
    engine = build_pandas_engine(
        pd.DataFrame({"a": ["a", "aaa", "bcbc", "defgh", None]})
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column_values.value_length.map",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    ser_expected_lengths = pd.Series([1, 3, 4, 5])
    result_series, _, _ = results[desired_metric.id]
    assert ser_expected_lengths.equals(result_series)


@pytest.mark.filterwarnings(
    "ignore:pandas.Int64Index is deprecated*:FutureWarning:tests.expectations.metrics"
)
def test_map_column_values_increasing_pd():
    engine = build_pandas_engine(
        pd.DataFrame(
            {
                "a": [
                    "2021-01-01",
                    "2021-01-31",
                    "2021-02-28",
                    "2021-03-20",
                    "2021-02-21",
                    "2021-05-01",
                    "2021-06-18",
                ]
            }
        )
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_values.increasing.condition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "strictly": True,
            "parse_strings_as_datetimes": True,
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    with pytest.warns(DeprecationWarning) as record:
        results = engine.resolve_metrics(
            metrics_to_resolve=(condition_metric,),
            metrics=metrics,
        )
        metrics.update(results)
    assert len(record) == 1
    assert 'The parameter "parse_strings_as_datetimes" is deprecated' in str(
        record.list[0].message
    )

    unexpected_count_metric = MetricConfiguration(
        metric_name="column_values.increasing.unexpected_count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    assert list(metrics[condition_metric.id][0]) == [
        False,
        False,
        False,
        False,
        True,
        False,
        False,
    ]
    assert metrics[unexpected_count_metric.id] == 1

    unexpected_rows_metric = MetricConfiguration(
        metric_name="column_values.increasing.unexpected_rows",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 1}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id]["a"].index == pd.Int64Index(
        [4], dtype="int64"
    )
    assert metrics[unexpected_rows_metric.id]["a"].values == ["2021-02-21"]


def test_map_column_values_increasing_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            {
                "a": [1, 2, 3.0, 4.5, 6, None, 3],
            }
        ),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    table_column_types = MetricConfiguration(
        metric_name="table.column_types",
        metric_domain_kwargs={},
        metric_value_kwargs={
            "include_nested": True,
        },
    )
    results = engine.resolve_metrics(
        metrics_to_resolve=(table_column_types,),
        metrics=metrics,
    )
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_values.increasing.condition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "strictly": True,
            "parse_strings_as_datetimes": True,
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
        "table.column_types": table_column_types,
    }
    with pytest.warns(DeprecationWarning) as record:
        results = engine.resolve_metrics(
            metrics_to_resolve=(condition_metric,),
            metrics=metrics,
        )
        metrics.update(results)
    assert len(record) == 1
    assert 'The parameter "parse_strings_as_datetimes" is deprecated' in str(
        record.list[0].message
    )

    unexpected_count_metric = MetricConfiguration(
        metric_name="column_values.increasing.unexpected_count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_count_metric.id] == 1

    unexpected_rows_metric = MetricConfiguration(
        metric_name="column_values.increasing.unexpected_rows",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 1}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id] == [
        (3,),
    ]


@pytest.mark.filterwarnings(
    "ignore:pandas.Int64Index is deprecated*:FutureWarning:tests.expectations.metrics"
)
def test_map_column_values_decreasing_pd():
    engine = build_pandas_engine(
        pd.DataFrame(
            {
                "a": [
                    "2021-06-18",
                    "2021-05-01",
                    "2021-02-21",
                    "2021-03-20",
                    "2021-02-28",
                    "2021-01-31",
                    "2021-01-01",
                ]
            }
        )
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_values.decreasing.condition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "strictly": True,
            "parse_strings_as_datetimes": True,
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    with pytest.warns(DeprecationWarning) as record:
        results = engine.resolve_metrics(
            metrics_to_resolve=(condition_metric,),
            metrics=metrics,
        )
        metrics.update(results)
    assert len(record) == 1
    assert 'The parameter "parse_strings_as_datetimes" is deprecated' in str(
        record.list[0].message
    )

    unexpected_count_metric = MetricConfiguration(
        metric_name="column_values.decreasing.unexpected_count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    assert list(metrics[condition_metric.id][0]) == [
        False,
        False,
        False,
        True,
        False,
        False,
        False,
    ]
    assert metrics[unexpected_count_metric.id] == 1

    unexpected_rows_metric = MetricConfiguration(
        metric_name="column_values.decreasing.unexpected_rows",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 1}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id]["a"].index == pd.Int64Index(
        [3], dtype="int64"
    )
    assert metrics[unexpected_rows_metric.id]["a"].values == ["2021-03-20"]


def test_map_column_values_decreasing_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            {
                "a": [3, None, 6, 4.5, 3.0, 2, 1],
            }
        ),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    table_column_types = MetricConfiguration(
        metric_name="table.column_types",
        metric_domain_kwargs={},
        metric_value_kwargs={
            "include_nested": True,
        },
    )
    results = engine.resolve_metrics(
        metrics_to_resolve=(table_column_types,),
        metrics=metrics,
    )
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_values.decreasing.condition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "strictly": True,
            "parse_strings_as_datetimes": True,
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
        "table.column_types": table_column_types,
    }
    with pytest.warns(DeprecationWarning) as record:
        results = engine.resolve_metrics(
            metrics_to_resolve=(condition_metric,),
            metrics=metrics,
        )
        metrics.update(results)
    assert len(record) == 1
    assert 'The parameter "parse_strings_as_datetimes" is deprecated' in str(
        record.list[0].message
    )

    unexpected_count_metric = MetricConfiguration(
        metric_name="column_values.decreasing.unexpected_count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_count_metric.id] == 1

    unexpected_rows_metric = MetricConfiguration(
        metric_name="column_values.decreasing.unexpected_rows",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 1}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id] == [(6,)]


def test_map_unique_column_exists_pd():
    engine = build_pandas_engine(pd.DataFrame({"a": [1, 2, 3, 3, 4, None]}))

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_values.unique.condition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name="column_values.unique.unexpected_count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    assert list(metrics[condition_metric.id][0]) == [False, False, True, True, False]
    assert metrics[unexpected_count_metric.id] == 2

    unexpected_rows_metric = MetricConfiguration(
        metric_name="column_values.unique.unexpected_rows",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 1}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id]["a"].index == [2]
    assert metrics[unexpected_rows_metric.id]["a"].values == [3]


def test_map_unique_column_does_not_exist_pd():
    engine = build_pandas_engine(pd.DataFrame({"a": [1, 2, 3, 3, None]}))

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column_values.unique.condition",
        metric_domain_kwargs={"column": "non_existent_column"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    with pytest.raises(ge_exceptions.MetricResolutionError) as eee:
        # noinspection PyUnusedLocal
        results = engine.resolve_metrics(
            metrics_to_resolve=(desired_metric,), metrics=metrics
        )
    assert (
        str(eee.value)
        == 'Error: The column "non_existent_column" in BatchData does not exist.'
    )


def test_map_unique_column_exists_sa(sa):
    engine = build_sa_engine(
        pd.DataFrame(
            {"a": [1, 2, 3, 3, None], "b": ["foo", "bar", "baz", "qux", "fish"]}
        ),
        sa,
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_values.unique.condition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,), metrics=metrics
    )
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column_values.unique.unexpected_count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,),
        metrics=metrics,  # metrics=aggregate_fn_metrics
    )
    metrics.update(results)
    assert results[desired_metric.id] == 2

    desired_metric = MetricConfiguration(
        metric_name="column_values.unique.unexpected_values",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "result_format": {"result_format": "BASIC", "partial_unexpected_count": 20}
        },
    )
    desired_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results[desired_metric.id] == [3, 3]

    desired_metric = MetricConfiguration(
        metric_name="column_values.unique.unexpected_value_counts",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "result_format": {"result_format": "BASIC", "partial_unexpected_count": 20}
        },
    )
    desired_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    assert results[desired_metric.id] == [(3, 2)]

    desired_metric = MetricConfiguration(
        metric_name="column_values.unique.unexpected_rows",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "result_format": {"result_format": "BASIC", "partial_unexpected_count": 20}
        },
    )
    desired_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results[desired_metric.id] == [(3, "baz"), (3, "qux")]


def test_map_unique_column_does_not_exist_sa(sa):
    engine = build_sa_engine(
        pd.DataFrame(
            {"a": [1, 2, 3, 3, None], "b": ["foo", "bar", "baz", "qux", "fish"]}
        ),
        sa,
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_values.unique.condition",
        metric_domain_kwargs={"column": "non_existent_column"},
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    with pytest.raises(ge_exceptions.MetricResolutionError) as eee:
        # noinspection PyUnusedLocal
        metrics = engine.resolve_metrics(
            metrics_to_resolve=(condition_metric,), metrics=metrics
        )
    assert (
        'Error: The column "non_existent_column" in BatchData does not exist.'
        in str(eee.value)
    )


def test_map_unique_empty_query_sa(sa):
    """If the table contains zero rows then there must be zero unexpected values."""
    engine = build_sa_engine(
        pd.DataFrame({"a": [], "b": []}),
        sa,
    )

    table_columns_metric: MetricConfiguration
    metrics: dict
    table_columns_metric, metrics = get_table_columns_metric(engine=engine)

    condition_metric = MetricConfiguration(
        metric_name="column_values.unique.condition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,), metrics=metrics
    )
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column_values.unique.unexpected_count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,),
        metrics=metrics,
    )
    assert results[desired_metric.id] == 0


def test_map_unique_column_exists_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            {
                "a": [1, 2, 3, 3, 4, None],
                "b": [None, "foo", "bar", "baz", "qux", "fish"],
            }
        ),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_values.unique.condition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,), metrics=metrics
    )
    metrics.update(results)

    # unique is a *window* function so does not use the aggregate_fn version of unexpected count
    desired_metric = MetricConfiguration(
        metric_name="column_values.unique.unexpected_count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results[desired_metric.id] == 2

    desired_metric = MetricConfiguration(
        metric_name="column_values.unique.unexpected_values",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "result_format": {"result_format": "BASIC", "partial_unexpected_count": 20}
        },
    )
    desired_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results[desired_metric.id] == [3, 3]

    desired_metric = MetricConfiguration(
        metric_name="column_values.unique.unexpected_value_counts",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "result_format": {"result_format": "BASIC", "partial_unexpected_count": 20}
        },
    )
    desired_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results[desired_metric.id] == [(3, 2)]

    desired_metric = MetricConfiguration(
        metric_name="column_values.unique.unexpected_rows",
        metric_domain_kwargs={
            "column": "a",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "BASIC", "partial_unexpected_count": 20}
        },
    )
    desired_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results[desired_metric.id] == [(3, "bar"), (3, "baz")]


def test_map_unique_column_does_not_exist_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            {
                "a": [1, 2, 3, 3, 4, None],
                "b": [None, "foo", "bar", "baz", "qux", "fish"],
            }
        ),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_values.unique.condition",
        metric_domain_kwargs={"column": "non_existent_column"},
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    with pytest.raises(ge_exceptions.MetricResolutionError) as eee:
        # noinspection PyUnusedLocal
        metrics = engine.resolve_metrics(
            metrics_to_resolve=(condition_metric,), metrics=metrics
        )
    assert (
        str(eee.value)
        == 'Error: The column "non_existent_column" in BatchData does not exist.'
    )


def test_z_score_under_threshold_pd():
    df = pd.DataFrame({"a": [1, 2, 3, None]})
    engine = PandasExecutionEngine(batch_data_dict={"my_id": df})

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    mean = MetricConfiguration(
        metric_name="column.mean",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    mean._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    stdev = MetricConfiguration(
        metric_name="column.standard_deviation",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    stdev._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    desired_metrics = (mean, stdev)
    results = engine.resolve_metrics(
        metrics_to_resolve=desired_metrics, metrics=metrics
    )
    metrics.update(results)

    column_values_z_score_map_metric = MetricConfiguration(
        metric_name="column_values.z_score.map",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    column_values_z_score_map_metric._metric_dependencies = {
        "column.standard_deviation": stdev,
        "column.mean": mean,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(column_values_z_score_map_metric,), metrics=metrics
    )
    metrics.update(results)
    column_values_z_score_under_threshold_condition_metric = MetricConfiguration(
        metric_name="column_values.z_score.under_threshold.condition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"double_sided": True, "threshold": 2},
    )
    column_values_z_score_under_threshold_condition_metric._metric_dependencies = {
        "column_values.z_score.map": column_values_z_score_map_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(column_values_z_score_under_threshold_condition_metric,),
        metrics=metrics,
    )
    assert list(
        results[column_values_z_score_under_threshold_condition_metric.id][0]
    ) == [False, False, False]
    metrics.update(results)
    desired_metric = MetricConfiguration(
        metric_name="column_values.z_score.under_threshold.unexpected_count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"double_sided": True, "threshold": 2},
    )
    desired_metric._metric_dependencies = {
        "unexpected_condition": column_values_z_score_under_threshold_condition_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    assert results[desired_metric.id] == 0


def test_z_score_under_threshold_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            {"a": [1, 2, 3, 3, None]},
        ),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    column_mean_aggregate_fn_metric = MetricConfiguration(
        metric_name="column.mean.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    column_mean_aggregate_fn_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    column_standard_deviation_aggregate_fn_metric = MetricConfiguration(
        metric_name="column.standard_deviation.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    column_standard_deviation_aggregate_fn_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    desired_metrics = (
        column_mean_aggregate_fn_metric,
        column_standard_deviation_aggregate_fn_metric,
    )
    results = engine.resolve_metrics(
        metrics_to_resolve=desired_metrics, metrics=metrics
    )
    metrics.update(results)

    mean = MetricConfiguration(
        metric_name="column.mean",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    mean._metric_dependencies = {
        "metric_partial_fn": column_mean_aggregate_fn_metric,
    }
    stdev = MetricConfiguration(
        metric_name="column.standard_deviation",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    stdev._metric_dependencies = {
        "metric_partial_fn": column_standard_deviation_aggregate_fn_metric,
        "table.columns": table_columns_metric,
    }
    desired_metrics = (mean, stdev)
    results = engine.resolve_metrics(
        metrics_to_resolve=desired_metrics, metrics=metrics
    )
    metrics.update(results)

    column_values_z_score_map_metric = MetricConfiguration(
        metric_name="column_values.z_score.map",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    column_values_z_score_map_metric._metric_dependencies = {
        "column.standard_deviation": stdev,
        "column.mean": mean,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(column_values_z_score_map_metric,), metrics=metrics
    )
    metrics.update(results)
    condition_metric = MetricConfiguration(
        metric_name="column_values.z_score.under_threshold.condition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"double_sided": True, "threshold": 2},
    )
    condition_metric._metric_dependencies = {
        "column_values.z_score.map": column_values_z_score_map_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,), metrics=metrics
    )
    metrics.update(results)

    aggregate_fn_metric = MetricConfiguration(
        metric_name="column_values.z_score.under_threshold.unexpected_count.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"double_sided": True, "threshold": 2},
    )
    aggregate_fn_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(aggregate_fn_metric,), metrics=metrics
    )
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column_values.z_score.under_threshold.unexpected_count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"double_sided": True, "threshold": 2},
    )
    desired_metric._metric_dependencies = {
        "metric_partial_fn": aggregate_fn_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    assert results[desired_metric.id] == 0


def test_table_metric_pd(caplog):
    df = pd.DataFrame({"a": [1, 2, 3, 3, None], "b": [1, 2, 3, 3, None]})
    engine = PandasExecutionEngine(batch_data_dict={"my_id": df})
    desired_metric = MetricConfiguration(
        metric_name="table.row_count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    results = engine.resolve_metrics(metrics_to_resolve=(desired_metric,))
    assert results == {desired_metric.id: 5}
    assert (
        'Unexpected key(s) "column" found in domain_kwargs for domain type "table"'
        in caplog.text
    )


def test_map_column_pairs_equal_metric_pd():
    engine = build_pandas_engine(
        pd.DataFrame(
            data={
                "a": [0, 1, 9, 2],
                "b": [5, 4, 3, 6],
                "c": [5, 4, 3, 6],
                "d": [7, 8, 9, 0],
            }
        )
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    """
    Two tests:
    1. Pass -- no unexpected rows.
    2. Fail -- one or more unexpected rows.
    """

    # Save original metrics for testing unexpected results.
    metrics_save: dict = copy.deepcopy(metrics)

    metric_name: str = "column_pair_values.equal"
    condition_metric_name: str = f"{metric_name}.condition"
    unexpected_count_metric_name: str = f"{metric_name}.unexpected_count"
    unexpected_rows_metric_name: str = f"{metric_name}.unexpected_rows"
    unexpected_values_metric_name: str = f"{metric_name}.unexpected_values"

    # First, assert Pass (no unexpected results).

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_A": "b",
            "column_B": "c",
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_A": "b",
            "column_B": "c",
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert list(metrics[condition_metric.id][0]) == [False, False, False, False]
    assert metrics[unexpected_count_metric.id] == 0

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_A": "b",
            "column_B": "c",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id].empty
    assert len(metrics[unexpected_rows_metric.id].columns) == 4

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_A": "b",
            "column_B": "c",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 0
    assert metrics[unexpected_values_metric.id] == []

    # Restore from saved original metrics in order to start fresh on testing for unexpected results.
    metrics = copy.deepcopy(metrics_save)

    # Second, assert Fail (one or more unexpected results).

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "d",
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "d",
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert list(metrics[condition_metric.id][0]) == [True, True, False, True]
    assert metrics[unexpected_count_metric.id] == 3

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "d",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id].equals(
        pd.DataFrame(
            data={"a": [0, 1, 2], "b": [5, 4, 6], "c": [5, 4, 6], "d": [7, 8, 0]},
            index=pd.Index([0, 1, 3]),
        )
    )
    assert len(metrics[unexpected_rows_metric.id].columns) == 4
    pd.testing.assert_index_equal(
        metrics[unexpected_rows_metric.id].index, pd.Index([0, 1, 3])
    )

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "d",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 3
    assert metrics[unexpected_values_metric.id] == [(0, 7), (1, 8), (2, 0)]


def test_table_metric_sa(sa):
    engine = build_sa_engine(pd.DataFrame({"a": [1, 2, 1, 2, 3, 3]}), sa)

    aggregate_fn_metric = MetricConfiguration(
        metric_name="table.row_count.aggregate_fn",
        metric_domain_kwargs={},
        metric_value_kwargs=None,
    )
    results = engine.resolve_metrics(metrics_to_resolve=(aggregate_fn_metric,))

    desired_metric = MetricConfiguration(
        metric_name="table.row_count",
        metric_domain_kwargs={},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "metric_partial_fn": aggregate_fn_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=results
    )

    assert results == {desired_metric.id: 6}


def test_map_column_pairs_equal_metric_sa(sa):
    engine = build_sa_engine(
        pd.DataFrame(
            data={
                "a": [0, 1, 9, 2],
                "b": [5, 4, 3, 6],
                "c": [5, 4, 3, 6],
                "d": [7, 8, 9, 0],
            }
        ),
        sa,
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    """
    Two tests:
    1. Pass -- no unexpected rows.
    2. Fail -- one or more unexpected rows.
    """

    # Save original metrics for testing unexpected results.
    metrics_save: dict = copy.deepcopy(metrics)

    metric_name: str = "column_pair_values.equal"
    condition_metric_name: str = f"{metric_name}.condition"
    unexpected_count_metric_name: str = f"{metric_name}.unexpected_count"
    unexpected_rows_metric_name: str = f"{metric_name}.unexpected_rows"
    unexpected_values_metric_name: str = f"{metric_name}.unexpected_values"

    # First, assert Pass (no unexpected results).

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_A": "b",
            "column_B": "c",
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_A": "b",
            "column_B": "c",
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_count_metric.id] == 0

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_A": "b",
            "column_B": "c",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_rows_metric.id]) == 0

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_A": "b",
            "column_B": "c",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 0
    assert metrics[unexpected_values_metric.id] == []

    # Restore from saved original metrics in order to start fresh on testing for unexpected results.
    metrics = copy.deepcopy(metrics_save)

    # Second, assert Fail (one or more unexpected results).

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "d",
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "d",
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_count_metric.id] == 3

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "d",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id] == [
        (0, 5, 5, 7),
        (1, 4, 4, 8),
        (2, 6, 6, 0),
    ]

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "d",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 3
    assert metrics[unexpected_values_metric.id] == [(0, 7), (1, 8), (2, 0)]


def test_map_column_pairs_equal_metric_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            data={
                "a": [0, 1, 9, 2],
                "b": [5, 4, 3, 6],
                "c": [5, 4, 3, 6],
                "d": [7, 8, 9, 0],
            }
        ),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    """
    Two tests:
    1. Pass -- no unexpected rows.
    2. Fail -- one or more unexpected rows.
    """

    # Save original metrics for testing unexpected results.
    metrics_save: dict = copy.deepcopy(metrics)

    metric_name: str = "column_pair_values.equal"
    condition_metric_name: str = f"{metric_name}.condition"
    unexpected_count_metric_name: str = f"{metric_name}.unexpected_count"
    unexpected_rows_metric_name: str = f"{metric_name}.unexpected_rows"
    unexpected_values_metric_name: str = f"{metric_name}.unexpected_values"

    # First, assert Pass (no unexpected results).

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_A": "b",
            "column_B": "c",
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_A": "b",
            "column_B": "c",
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert metrics[unexpected_count_metric.id] == 0

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_A": "b",
            "column_B": "c",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_rows_metric.id]) == 0

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_A": "b",
            "column_B": "c",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 0
    assert metrics[unexpected_values_metric.id] == []

    # Restore from saved original metrics in order to start fresh on testing for unexpected results.
    metrics = copy.deepcopy(metrics_save)

    # Second, assert Fail (one or more unexpected results).

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "d",
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "d",
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert metrics[unexpected_count_metric.id] == 3

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "d",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id] == [
        (0, 5, 5, 7),
        (1, 4, 4, 8),
        (2, 6, 6, 0),
    ]

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "d",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 3
    assert metrics[unexpected_values_metric.id] == [(0, 7), (1, 8), (2, 0)]


def test_map_column_pairs_greater_metric_pd():
    df = pd.DataFrame({"a": [2, 3, 4, None, 3, None], "b": [1, 2, 3, None, 3, 5]})
    engine = PandasExecutionEngine(batch_data_dict={"my_id": df})

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_pair_values.a_greater_than_b.condition",
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "b",
            "ignore_row_if": "either_value_is_missing",
        },
        metric_value_kwargs={
            "or_equal": True,
            "result_format": {
                "result_format": "SUMMARY",
                "partial_unexpected_count": 6,
            },
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    assert (
        results[condition_metric.id][0]
        .reset_index(drop=True)
        .equals(pd.Series([False, False, False, False]))
    )

    unexpected_values_metric = MetricConfiguration(
        metric_name="column_pair_values.a_greater_than_b.unexpected_values",
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "b",
            "ignore_row_if": "either_value_is_missing",
        },
        metric_value_kwargs={
            "or_equal": True,
            "result_format": {
                "result_format": "SUMMARY",
                "partial_unexpected_count": 6,
            },
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 0
    assert metrics[unexpected_values_metric.id] == []


def test_map_column_pairs_greater_metric_sa(sa):
    engine = build_sa_engine(
        pd.DataFrame(
            data={
                "a": [2, 3, 4, None, 3, None],
                "b": [1, 2, 3, None, 3, 5],
            }
        ),
        sa,
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_pair_values.a_greater_than_b.condition",
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "b",
            "ignore_row_if": "either_value_is_missing",
        },
        metric_value_kwargs={
            "or_equal": True,
            "result_format": {
                "result_format": "SUMMARY",
                "partial_unexpected_count": 6,
            },
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_values_metric = MetricConfiguration(
        metric_name="column_pair_values.a_greater_than_b.unexpected_values",
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "b",
            "ignore_row_if": "either_value_is_missing",
        },
        metric_value_kwargs={
            "or_equal": True,
            "result_format": {
                "result_format": "SUMMARY",
                "partial_unexpected_count": 6,
            },
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 0
    assert metrics[unexpected_values_metric.id] == []


def test_map_column_pairs_greater_metric_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            data={
                "a": [2, 3, 4, None, 3, None],
                "b": [1, 2, 3, None, 3, 5],
            }
        ),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_pair_values.a_greater_than_b.condition",
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "b",
            "ignore_row_if": "either_value_is_missing",
        },
        metric_value_kwargs={
            "or_equal": True,
            "result_format": {
                "result_format": "SUMMARY",
                "partial_unexpected_count": 6,
            },
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_values_metric = MetricConfiguration(
        metric_name="column_pair_values.a_greater_than_b.unexpected_values",
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "b",
            "ignore_row_if": "either_value_is_missing",
        },
        metric_value_kwargs={
            "or_equal": True,
            "result_format": {
                "result_format": "SUMMARY",
                "partial_unexpected_count": 6,
            },
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 0
    assert metrics[unexpected_values_metric.id] == []


def test_map_column_pairs_in_set_metric_pd():
    df = pd.DataFrame({"a": [10, 3, 4, None, 3, None], "b": [1, 2, 3, None, 3, 5]})
    engine = PandasExecutionEngine(batch_data_dict={"my_id": df})

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_pair_values.in_set.condition",
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "b",
            "ignore_row_if": "either_value_is_missing",
        },
        metric_value_kwargs={
            "value_pairs_set": [(2, 1), (3, 2), (4, 3), (3, 3)],
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    assert (
        results[condition_metric.id][0]
        .reset_index(drop=True)
        .equals(pd.Series([True, False, False, False]))
    )


def test_map_column_pairs_in_set_metric_sa(sa):
    engine = build_sa_engine(
        pd.DataFrame(
            {"a": [10, 9, 3, 4, None, 3, None], "b": [1, 4, 2, 3, None, 3, 5]}
        ),
        sa,
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_pair_values.in_set.condition",
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "b",
            "ignore_row_if": "either_value_is_missing",
        },
        metric_value_kwargs={
            "value_pairs_set": [(2, 1), (3, 2), (4, 3), (3, 3)],
            "result_format": {
                "result_format": "SUMMARY",
                "partial_unexpected_count": 6,
            },
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_values_metric = MetricConfiguration(
        metric_name="column_pair_values.in_set.unexpected_values",
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "b",
            "ignore_row_if": "either_value_is_missing",
        },
        metric_value_kwargs={
            "value_pairs_set": [(2, 1), (3, 2), (4, 3), (3, 3)],
            "result_format": {
                "result_format": "SUMMARY",
                "partial_unexpected_count": 6,
            },
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    assert results[unexpected_values_metric.id] == [(10, 1), (9, 4)]

    condition_metric = MetricConfiguration(
        metric_name="column_pair_values.in_set.condition",
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "b",
            "ignore_row_if": "both_values_are_missing",
        },
        metric_value_kwargs={
            "value_pairs_set": [(2, 1), (3, 2), (4, 3), (3, 3)],
            "result_format": {
                "result_format": "SUMMARY",
                "partial_unexpected_count": 6,
            },
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_values_metric = MetricConfiguration(
        metric_name="column_pair_values.in_set.unexpected_values",
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "b",
            "ignore_row_if": "either_value_is_missing",
        },
        metric_value_kwargs={
            "value_pairs_set": [(2, 1), (3, 2), (4, 3), (3, 3)],
            "result_format": {
                "result_format": "SUMMARY",
                "partial_unexpected_count": 6,
            },
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    assert results[unexpected_values_metric.id] == [
        (10.0, 1.0),
        (9.0, 4.0),
        (None, 5.0),
    ]


def test_map_column_pairs_in_set_metric_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            {"a": [10, 9, 3, 4, None, 3, None], "b": [1, 4, 2, 3, None, 3, 5]}
        ),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name="column_pair_values.in_set.condition",
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "b",
            "ignore_row_if": "either_value_is_missing",
        },
        metric_value_kwargs={
            "value_pairs_set": [(2, 1), (3, 2), (4, 3), (3, 3)],
            "result_format": {
                "result_format": "SUMMARY",
                "partial_unexpected_count": 6,
            },
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_values_metric = MetricConfiguration(
        metric_name="column_pair_values.in_set.unexpected_values",
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "b",
            "ignore_row_if": "either_value_is_missing",
        },
        metric_value_kwargs={
            "value_pairs_set": [(2, 1), (3, 2), (4, 3), (3, 3)],
            "result_format": {
                "result_format": "SUMMARY",
                "partial_unexpected_count": 6,
            },
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    assert results[unexpected_values_metric.id] == [(10, 1), (9, 4)]

    condition_metric = MetricConfiguration(
        metric_name="column_pair_values.in_set.condition",
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "b",
            "ignore_row_if": "both_values_are_missing",
        },
        metric_value_kwargs={
            "value_pairs_set": [(2, 1), (3, 2), (4, 3), (3, 3)],
            "result_format": {
                "result_format": "SUMMARY",
                "partial_unexpected_count": 6,
            },
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_values_metric = MetricConfiguration(
        metric_name="column_pair_values.in_set.unexpected_values",
        metric_domain_kwargs={
            "column_A": "a",
            "column_B": "b",
            "ignore_row_if": "either_value_is_missing",
        },
        metric_value_kwargs={
            "value_pairs_set": [(2, 1), (3, 2), (4, 3), (3, 3)],
            "result_format": {
                "result_format": "SUMMARY",
                "partial_unexpected_count": 6,
            },
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    assert results[unexpected_values_metric.id] == [
        (10.0, 1.0),
        (9.0, 4.0),
        (None, 5.0),
    ]


def test_table_metric_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            {"a": [1, 2, 1]},
        ),
        batch_id="my_id",
    )

    aggregate_fn_metric = MetricConfiguration(
        metric_name="table.row_count.aggregate_fn",
        metric_domain_kwargs={},
        metric_value_kwargs=None,
    )
    results = engine.resolve_metrics(metrics_to_resolve=(aggregate_fn_metric,))

    desired_metric = MetricConfiguration(
        metric_name="table.row_count",
        metric_domain_kwargs={},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "metric_partial_fn": aggregate_fn_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=results
    )

    assert results == {desired_metric.id: 3}


def test_column_median_metric_pd():
    engine = build_pandas_engine(
        pd.DataFrame(
            {"a": [1, 2, 3]},
        )
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.median",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: 2}


@pytest.mark.parametrize(
    "dataframe,median,",
    [
        pytest.param(
            pd.DataFrame({"a": [1, 2, 3]}),
            2,
        ),
        pytest.param(
            pd.DataFrame({"a": [1]}),
            1,
        ),
    ],
)
def test_column_median_metric_sa(sa, dataframe: pd.DataFrame, median: int):
    engine = build_sa_engine(
        dataframe,
        sa,
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    partial_metric = MetricConfiguration(
        metric_name="table.row_count.aggregate_fn",
        metric_domain_kwargs={},
        metric_value_kwargs=None,
    )

    results = engine.resolve_metrics(
        metrics_to_resolve=(partial_metric,), metrics=metrics
    )
    metrics.update(results)

    table_row_count_metric = MetricConfiguration(
        metric_name="table.row_count",
        metric_domain_kwargs={},
        metric_value_kwargs=None,
    )
    table_row_count_metric._metric_dependencies = {
        "metric_partial_fn": partial_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(table_row_count_metric,), metrics=metrics
    )
    metrics.update(results)

    column_values_null_condition_metric = MetricConfiguration(
        metric_name="column_values.null.condition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    column_values_null_condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(column_values_null_condition_metric,), metrics=metrics
    )
    metrics.update(results)

    column_values_nonnull_count_metric = MetricConfiguration(
        metric_name="column_values.null.unexpected_count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    column_values_nonnull_count_metric._metric_dependencies = {
        "unexpected_condition": column_values_null_condition_metric,
        "metric_partial_fn": partial_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(column_values_nonnull_count_metric,), metrics=metrics
    )
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.median",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
        "table.row_count": table_row_count_metric,
        "column_values.nonnull.count": column_values_nonnull_count_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert results == {desired_metric.id: median}


def test_column_median_metric_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            {"a": [1, 2, 3]},
        ),
        batch_id="my_id",
    )

    aggregate_fn_metric = MetricConfiguration(
        metric_name="table.row_count.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    metrics = engine.resolve_metrics(metrics_to_resolve=(aggregate_fn_metric,))

    row_count = MetricConfiguration(
        metric_name="table.row_count",
        metric_domain_kwargs={},
        metric_value_kwargs=None,
    )
    row_count._metric_dependencies = {
        "metric_partial_fn": aggregate_fn_metric,
    }
    metrics = engine.resolve_metrics(metrics_to_resolve=(row_count,), metrics=metrics)

    desired_metric = MetricConfiguration(
        metric_name="column.median",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric._metric_dependencies = {
        "table.row_count": row_count,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    assert results == {desired_metric.id: 2}


@pytest.mark.integration
def test_value_counts_metric_pd():
    engine = build_pandas_engine(pd.DataFrame({"a": [1, 2, 1, 2, 3, 3]}))

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric = MetricConfiguration(
        metric_name="column.value_counts",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"sort": "value", "collate": None},
    )
    desired_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric,), metrics=metrics
    )
    metrics.update(results)
    assert pd.Series(index=[1, 2, 3], data=[2, 2, 2]).equals(metrics[desired_metric.id])


@pytest.mark.integration
def test_value_counts_metric_sa(sa):
    engine = build_sa_engine(
        pd.DataFrame({"a": [1, 2, 1, 2, 3, 3], "b": [4, 4, 4, 4, 4, 4]}), sa
    )

    desired_metric = MetricConfiguration(
        metric_name="column.value_counts",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"sort": "value", "collate": None},
    )
    desired_metric_b = MetricConfiguration(
        metric_name="column.value_counts",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs={"sort": "value", "collate": None},
    )

    metrics = engine.resolve_metrics(
        metrics_to_resolve=(desired_metric, desired_metric_b)
    )
    assert pd.Series(
        index=pd.Index(data=[1, 2, 3], name="value"),
        data=[2, 2, 2],
        dtype=np.object,
    ).equals(metrics[desired_metric.id])
    assert pd.Series(
        index=pd.Index(data=[4], name="value"),
        data=[6],
        dtype=np.object,
    ).equals(metrics[desired_metric_b.id])


@pytest.mark.integration
def test_value_counts_metric_spark(spark_session):
    from great_expectations.expectations.metrics.import_manager import sparktypes

    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            {
                "a": [1, 2, 1, 2, 3, 3, None],
                "b": [None, None, None, None, None, None, None],
            },
        ),
        schema=sparktypes.StructType(
            [
                sparktypes.StructField("a", sparktypes.FloatType(), True),
                sparktypes.StructField("b", sparktypes.NullType(), True),
            ]
        ),
        batch_id="my_id",
    )

    desired_metric = MetricConfiguration(
        metric_name="column.value_counts",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"sort": "value", "collate": None},
    )

    metrics = engine.resolve_metrics(metrics_to_resolve=(desired_metric,))
    assert pd.Series(index=[1.0, 2.0, 3.0, np.nan], data=[2, 2, 2, 1]).equals(
        metrics[desired_metric.id]
    )

    desired_metric = MetricConfiguration(
        metric_name="column.value_counts",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs={"sort": "value", "collate": None},
    )

    metrics = engine.resolve_metrics(metrics_to_resolve=(desired_metric,))
    assert pd.Series(index=[], data=[]).equals(metrics[desired_metric.id])


@pytest.mark.integration
@pytest.mark.parametrize(
    "dataframe",
    [
        pd.DataFrame({"a": [1, 2, 1, 2, 3, 3, None]}),
        pd.DataFrame({"a": [1, 2, 1, 2, 3, 3, None], "b": [1, 3, 5, 3, 4, 2, None]}),
    ],
)
def test_distinct_metric_spark(
    spark_session,
    dataframe,
):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=dataframe,
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    column_distinct_values_metric = MetricConfiguration(
        metric_name="column.distinct_values",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    column_distinct_values_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(column_distinct_values_metric,),
        metrics=metrics,
    )
    metrics.update(results)
    assert metrics[column_distinct_values_metric.id] == {1, 2, 3}

    column_distinct_values_count_metric_partial_fn = MetricConfiguration(
        metric_name="column.distinct_values.count.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    column_distinct_values_count_metric_partial_fn._metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(column_distinct_values_count_metric_partial_fn,),
        metrics=metrics,
    )
    metrics.update(results)
    assert isinstance(
        metrics[column_distinct_values_count_metric_partial_fn.id][0],
        pyspark_sql_Column,
    )

    column_distinct_values_count_metric = MetricConfiguration(
        metric_name="column.distinct_values.count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    column_distinct_values_count_metric._metric_dependencies = {
        "metric_partial_fn": column_distinct_values_count_metric_partial_fn
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(column_distinct_values_count_metric,), metrics=metrics
    )
    metrics.update(results)
    assert metrics[column_distinct_values_count_metric.id] == 3

    column_distinct_values_count_threshold_metric = MetricConfiguration(
        metric_name="column.distinct_values.count.under_threshold",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"threshold": 5},
    )
    column_distinct_values_count_threshold_metric._metric_dependencies = {
        "column.distinct_values.count": column_distinct_values_count_metric,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(column_distinct_values_count_threshold_metric,),
        metrics=metrics,
    )
    metrics.update(results)
    assert metrics[column_distinct_values_count_threshold_metric.id] is True


@pytest.mark.integration
def test_distinct_metric_sa(
    sa,
):
    engine: SqlAlchemyExecutionEngine = build_sa_engine(
        pd.DataFrame(
            {
                "a": [1, 2, 1, 2, 3, 3, None],
            }
        ),
        sa,
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    column_distinct_values_metric = MetricConfiguration(
        metric_name="column.distinct_values",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    column_distinct_values_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(column_distinct_values_metric,),
        metrics=metrics,
    )
    metrics.update(results)
    assert metrics[column_distinct_values_metric.id] == {1, 2, 3}

    column_distinct_values_count_metric_partial_fn = MetricConfiguration(
        metric_name="column.distinct_values.count.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    column_distinct_values_count_metric_partial_fn._metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(column_distinct_values_count_metric_partial_fn,),
        metrics=metrics,
    )
    metrics.update(results)
    assert isinstance(
        metrics[column_distinct_values_count_metric_partial_fn.id][0],
        sa.sql.functions.count,
    )

    column_distinct_values_count_metric = MetricConfiguration(
        metric_name="column.distinct_values.count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    column_distinct_values_count_metric._metric_dependencies = {
        "metric_partial_fn": column_distinct_values_count_metric_partial_fn
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(column_distinct_values_count_metric,), metrics=metrics
    )
    metrics.update(results)
    assert metrics[column_distinct_values_count_metric.id] == 3

    column_distinct_values_count_threshold_metric = MetricConfiguration(
        metric_name="column.distinct_values.count.under_threshold",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"threshold": 5},
    )
    column_distinct_values_count_threshold_metric._metric_dependencies = {
        "column.distinct_values.count": column_distinct_values_count_metric,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(column_distinct_values_count_threshold_metric,),
        metrics=metrics,
    )
    metrics.update(results)
    assert metrics[column_distinct_values_count_threshold_metric.id] is True


@pytest.mark.integration
def test_distinct_metric_pd():
    engine = build_pandas_engine(pd.DataFrame({"a": [1, 2, 1, 2, 3, 3]}))

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    column_distinct_values_metric = MetricConfiguration(
        metric_name="column.distinct_values",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    column_distinct_values_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(column_distinct_values_metric,), metrics=metrics
    )
    metrics.update(results)
    assert metrics[column_distinct_values_metric.id] == {1, 2, 3}

    column_distinct_values_count_metric = MetricConfiguration(
        metric_name="column.distinct_values.count",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    column_distinct_values_count_metric._metric_dependencies = {
        "column.distinct_values": column_distinct_values_metric,
        "table.columns": table_columns_metric,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(column_distinct_values_count_metric,), metrics=metrics
    )
    metrics.update(results)
    assert metrics[column_distinct_values_count_metric.id] == 3

    column_distinct_values_count_threshold_metric = MetricConfiguration(
        metric_name="column.distinct_values.count.under_threshold",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"threshold": 5},
    )
    column_distinct_values_count_threshold_metric._metric_dependencies = {
        "column.distinct_values.count": column_distinct_values_count_metric,
        "table.columns": table_columns_metric,
    }

    results = engine.resolve_metrics(
        metrics_to_resolve=(column_distinct_values_count_threshold_metric,),
        metrics=metrics,
    )
    metrics.update(results)
    assert metrics[column_distinct_values_count_threshold_metric.id] is True


def test_batch_aggregate_metrics_pd():
    import datetime

    engine = build_pandas_engine(
        pd.DataFrame(
            {
                "a": [
                    "2021-01-01",
                    "2021-01-31",
                    "2021-02-28",
                    "2021-03-20",
                    "2021-02-21",
                    "2021-05-01",
                    "2021-06-18",
                ],
                "b": [
                    "2021-06-18",
                    "2021-05-01",
                    "2021-02-21",
                    "2021-03-20",
                    "2021-02-28",
                    "2021-01-31",
                    "2021-01-01",
                ],
            }
        )
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_metric_1 = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": True,
        },
    )
    desired_metric_1._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    desired_metric_2 = MetricConfiguration(
        metric_name="column.min",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": True,
        },
    )
    desired_metric_2._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    desired_metric_3 = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": True,
        },
    )
    desired_metric_3._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    desired_metric_4 = MetricConfiguration(
        metric_name="column.min",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs={
            "parse_strings_as_datetimes": True,
        },
    )
    desired_metric_4._metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    start = datetime.datetime.now()
    with pytest.warns(DeprecationWarning) as records:
        results = engine.resolve_metrics(
            metrics_to_resolve=(
                desired_metric_1,
                desired_metric_2,
                desired_metric_3,
                desired_metric_4,
            ),
            metrics=metrics,
        )
        metrics.update(results)
    assert len(records) == 4
    for record in records:
        assert 'The parameter "parse_strings_as_datetimes" is deprecated' in str(
            record.message
        )
    end = datetime.datetime.now()
    print(end - start)
    assert results[desired_metric_1.id] == pd.Timestamp(year=2021, month=6, day=18)
    assert results[desired_metric_2.id] == pd.Timestamp(year=2021, month=1, day=1)
    assert results[desired_metric_3.id] == pd.Timestamp(year=2021, month=6, day=18)
    assert results[desired_metric_4.id] == pd.Timestamp(year=2021, month=1, day=1)


def test_batch_aggregate_metrics_sa(caplog, sa):
    import datetime

    engine = build_sa_engine(
        pd.DataFrame({"a": [1, 2, 1, 2, 3, 3], "b": [4, 4, 4, 4, 4, 4]}), sa
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_aggregate_fn_metric_1 = MetricConfiguration(
        metric_name="column.max.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_aggregate_fn_metric_1._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    desired_aggregate_fn_metric_2 = MetricConfiguration(
        metric_name="column.min.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_aggregate_fn_metric_2._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    desired_aggregate_fn_metric_3 = MetricConfiguration(
        metric_name="column.max.aggregate_fn",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs=None,
    )
    desired_aggregate_fn_metric_3._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    desired_aggregate_fn_metric_4 = MetricConfiguration(
        metric_name="column.min.aggregate_fn",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs=None,
    )
    desired_aggregate_fn_metric_4._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(
            desired_aggregate_fn_metric_1,
            desired_aggregate_fn_metric_2,
            desired_aggregate_fn_metric_3,
            desired_aggregate_fn_metric_4,
        ),
        metrics=metrics,
    )
    metrics.update(results)

    desired_metric_1 = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric_1._metric_dependencies = {
        "metric_partial_fn": desired_aggregate_fn_metric_1,
        "table.columns": table_columns_metric,
    }
    desired_metric_2 = MetricConfiguration(
        metric_name="column.min",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric_2._metric_dependencies = {
        "metric_partial_fn": desired_aggregate_fn_metric_2,
        "table.columns": table_columns_metric,
    }
    desired_metric_3 = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs=None,
    )
    desired_metric_3._metric_dependencies = {
        "metric_partial_fn": desired_aggregate_fn_metric_3,
        "table.columns": table_columns_metric,
    }
    desired_metric_4 = MetricConfiguration(
        metric_name="column.min",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs=None,
    )
    desired_metric_4._metric_dependencies = {
        "metric_partial_fn": desired_aggregate_fn_metric_4,
        "table.columns": table_columns_metric,
    }
    caplog.clear()
    caplog.set_level(logging.DEBUG, logger="great_expectations")
    start = datetime.datetime.now()
    results = engine.resolve_metrics(
        metrics_to_resolve=(
            desired_metric_1,
            desired_metric_2,
            desired_metric_3,
            desired_metric_4,
        ),
        metrics=metrics,
    )
    metrics.update(results)
    end = datetime.datetime.now()
    print("t1")
    print(end - start)
    assert results[desired_metric_1.id] == 3
    assert results[desired_metric_2.id] == 1
    assert results[desired_metric_3.id] == 4
    assert results[desired_metric_4.id] == 4

    # Check that all four of these metrics were computed on a single domain
    found_message = False
    for record in caplog.records:
        if (
            record.message
            == "SqlAlchemyExecutionEngine computed 4 metrics on domain_id ()"
        ):
            found_message = True
    assert found_message


def test_batch_aggregate_metrics_spark(caplog, spark_session):
    import datetime

    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            {"a": [1, 2, 1, 2, 3, 3], "b": [4, 4, 4, 4, 4, 4]},
        ),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    desired_aggregate_fn_metric_1 = MetricConfiguration(
        metric_name="column.max.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_aggregate_fn_metric_1._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    desired_aggregate_fn_metric_2 = MetricConfiguration(
        metric_name="column.min.aggregate_fn",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_aggregate_fn_metric_2._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    desired_aggregate_fn_metric_3 = MetricConfiguration(
        metric_name="column.max.aggregate_fn",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs=None,
    )
    desired_aggregate_fn_metric_3._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    desired_aggregate_fn_metric_4 = MetricConfiguration(
        metric_name="column.min.aggregate_fn",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs=None,
    )
    desired_aggregate_fn_metric_4._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(
            desired_aggregate_fn_metric_1,
            desired_aggregate_fn_metric_2,
            desired_aggregate_fn_metric_3,
            desired_aggregate_fn_metric_4,
        ),
        metrics=metrics,
    )
    metrics.update(results)

    desired_metric_1 = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric_1._metric_dependencies = {
        "metric_partial_fn": desired_aggregate_fn_metric_1,
    }
    desired_metric_2 = MetricConfiguration(
        metric_name="column.min",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric_2._metric_dependencies = {
        "metric_partial_fn": desired_aggregate_fn_metric_2,
    }
    desired_metric_3 = MetricConfiguration(
        metric_name="column.max",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs=None,
    )
    desired_metric_3._metric_dependencies = {
        "metric_partial_fn": desired_aggregate_fn_metric_3,
    }
    desired_metric_4 = MetricConfiguration(
        metric_name="column.min",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs=None,
    )
    desired_metric_4._metric_dependencies = {
        "metric_partial_fn": desired_aggregate_fn_metric_4,
    }
    start = datetime.datetime.now()
    caplog.clear()
    caplog.set_level(logging.DEBUG, logger="great_expectations")
    results = engine.resolve_metrics(
        metrics_to_resolve=(
            desired_metric_1,
            desired_metric_2,
            desired_metric_3,
            desired_metric_4,
        ),
        metrics=metrics,
    )
    metrics.update(results)
    end = datetime.datetime.now()
    print(end - start)
    assert results[desired_metric_1.id] == 3
    assert results[desired_metric_2.id] == 1
    assert results[desired_metric_3.id] == 4
    assert results[desired_metric_4.id] == 4

    # Check that all four of these metrics were computed on a single domain
    found_message = False
    for record in caplog.records:
        if (
            record.message
            == "SparkDFExecutionEngine computed 4 metrics on domain_id ()"
        ):
            found_message = True
    assert found_message


def test_map_multicolumn_sum_equal_pd():
    engine = build_pandas_engine(
        pd.DataFrame(
            data={"a": [0, 1, 2], "b": [5, 4, 3], "c": [0, 0, 1], "d": [7, 8, 9]}
        )
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    """
    Two tests:
    1. Pass -- no unexpected rows.
    2. Fail -- one or more unexpected rows.
    """

    # Save original metrics for testing unexpected results.
    metrics_save: dict = copy.deepcopy(metrics)

    metric_name: str = "multicolumn_sum.equal"
    condition_metric_name: str = f"{metric_name}.condition"
    unexpected_count_metric_name: str = f"{metric_name}.unexpected_count"
    unexpected_rows_metric_name: str = f"{metric_name}.unexpected_rows"
    unexpected_values_metric_name: str = f"{metric_name}.unexpected_values"

    # First, assert Pass (no unexpected results).

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs={
            "sum_total": 5,
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert list(metrics[condition_metric.id][0]) == [False, False, False]
    assert metrics[unexpected_count_metric.id] == 0

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id].empty
    assert len(metrics[unexpected_rows_metric.id].columns) == 4

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 0
    assert metrics[unexpected_values_metric.id] == []

    # Restore from saved original metrics in order to start fresh on testing for unexpected results.
    metrics = copy.deepcopy(metrics_save)

    # Second, assert Fail (one or more unexpected results).

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
        },
        metric_value_kwargs={
            "sum_total": 5,
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert list(metrics[condition_metric.id][0]) == [False, False, True]
    assert metrics[unexpected_count_metric.id] == 1

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id].equals(
        pd.DataFrame(data={"a": [2], "b": [3], "c": [1], "d": [9]}, index=[2])
    )
    assert len(metrics[unexpected_rows_metric.id].columns) == 4
    pd.testing.assert_index_equal(
        metrics[unexpected_rows_metric.id].index, pd.Index([2])
    )

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 1
    assert metrics[unexpected_values_metric.id] == [{"a": 2, "b": 3, "c": 1}]


def test_map_multicolumn_sum_equal_sa(sa):
    engine = build_sa_engine(
        pd.DataFrame(
            data={"a": [0, 1, 2], "b": [5, 4, 3], "c": [0, 0, 1], "d": [7, 8, 9]}
        ),
        sa,
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    """
    Two tests:
    1. Pass -- no unexpected rows.
    2. Fail -- one or more unexpected rows.
    """

    # Save original metrics for testing unexpected results.
    metrics_save: dict = copy.deepcopy(metrics)

    metric_name: str = "multicolumn_sum.equal"
    condition_metric_name: str = f"{metric_name}.condition"
    unexpected_count_metric_name: str = f"{metric_name}.unexpected_count"
    unexpected_rows_metric_name: str = f"{metric_name}.unexpected_rows"
    unexpected_values_metric_name: str = f"{metric_name}.unexpected_values"

    # First, assert Pass (no unexpected results).
    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs={
            "sum_total": 5,
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_count_metric.id] == 0

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_rows_metric.id]) == 0

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 0
    assert metrics[unexpected_values_metric.id] == []

    # Restore from saved original metrics in order to start fresh on testing for unexpected results.
    metrics = copy.deepcopy(metrics_save)

    # Second, assert Fail (one or more unexpected results).

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
        },
        metric_value_kwargs={
            "sum_total": 5,
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_count_metric.id] == 1

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id] == [(2, 3, 1, 9)]
    assert len(metrics[unexpected_rows_metric.id][0]) == 4

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 1
    assert metrics[unexpected_values_metric.id] == [{"a": 2, "b": 3, "c": 1}]


def test_map_multicolumn_sum_equal_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            data={"a": [0, 1, 2], "b": [5, 4, 3], "c": [0, 0, 1], "d": [7, 8, 9]}
        ),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    """
    Two tests:
    1. Pass -- no unexpected rows.
    2. Fail -- one or more unexpected rows.
    """

    # Save original metrics for testing unexpected results.
    metrics_save: dict = copy.deepcopy(metrics)

    metric_name: str = "multicolumn_sum.equal"
    condition_metric_name: str = f"{metric_name}.condition"
    unexpected_count_metric_name: str = f"{metric_name}.unexpected_count"
    unexpected_rows_metric_name: str = f"{metric_name}.unexpected_rows"
    unexpected_values_metric_name: str = f"{metric_name}.unexpected_values"

    # First, assert Pass (no unexpected results).
    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs={
            "sum_total": 5,
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert metrics[unexpected_count_metric.id] == 0

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_rows_metric.id]) == 0

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 0
    assert metrics[unexpected_values_metric.id] == []

    # Restore from saved original metrics in order to start fresh on testing for unexpected results.
    metrics = copy.deepcopy(metrics_save)

    # Second, assert Fail (one or more unexpected results).

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
        },
        metric_value_kwargs={
            "sum_total": 5,
        },
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert metrics[unexpected_count_metric.id] == 1

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id] == [(2, 3, 1, 9)]
    assert len(metrics[unexpected_rows_metric.id][0]) == 4

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 1
    assert metrics[unexpected_values_metric.id] == [{"a": 2, "b": 3, "c": 1}]


def test_map_compound_columns_unique_pd():
    engine = build_pandas_engine(
        pd.DataFrame(data={"a": [0, 1, 1], "b": [1, 2, 3], "c": [0, 2, 2]})
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    """
    Two tests:
    1. Pass -- no duplicated compound column keys.
    2. Fail -- one or more duplicated compound column keys.
    """

    # Save original metrics for testing unexpected results.
    metrics_save: dict = copy.deepcopy(metrics)

    metric_name: str = "compound_columns.unique"
    condition_metric_name: str = f"{metric_name}.condition"
    unexpected_count_metric_name: str = f"{metric_name}.unexpected_count"
    unexpected_rows_metric_name: str = f"{metric_name}.unexpected_rows"
    unexpected_values_metric_name: str = f"{metric_name}.unexpected_values"

    # First, assert Pass (no unexpected results).

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert list(metrics[condition_metric.id][0]) == [False, False, False]
    assert metrics[unexpected_count_metric.id] == 0

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id].empty
    assert len(metrics[unexpected_rows_metric.id].columns) == 3

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 0
    assert metrics[unexpected_values_metric.id] == []

    # Restore from saved original metrics in order to start fresh on testing for unexpected results.
    metrics = copy.deepcopy(metrics_save)

    # Second, assert Fail (one or more unexpected results).

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "c"],
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "c"],
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert list(metrics[condition_metric.id][0]) == [False, True, True]
    assert metrics[unexpected_count_metric.id] == 2

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "c"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id].equals(
        pd.DataFrame(data={"a": [1, 1], "b": [2, 3], "c": [2, 2]}, index=[1, 2])
    )
    assert len(metrics[unexpected_rows_metric.id].columns) == 3
    pd.testing.assert_index_equal(
        metrics[unexpected_rows_metric.id].index, pd.Index([1, 2])
    )

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "c"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 2
    assert metrics[unexpected_values_metric.id] == [{"a": 1, "c": 2}, {"a": 1, "c": 2}]


def test_map_compound_columns_unique_sa(sa):
    engine = build_sa_engine(
        pd.DataFrame(data={"a": [0, 1, 1], "b": [1, 2, 3], "c": [0, 2, 2]}),
        sa,
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    """
    Two tests:
    1. Pass -- no duplicated compound column keys.
    2. Fail -- one or more duplicated compound column keys.
    """

    # Save original metrics for testing unexpected results.
    metrics_save: dict = copy.deepcopy(metrics)

    prerequisite_function_metric_name: str = "compound_columns.count.map"

    prerequisite_function_metric = MetricConfiguration(
        metric_name=prerequisite_function_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs=None,
    )
    prerequisite_function_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(prerequisite_function_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    metric_name: str = "compound_columns.unique"
    condition_metric_name: str = f"{metric_name}.condition"
    unexpected_count_metric_name: str = f"{metric_name}.unexpected_count"
    unexpected_rows_metric_name: str = f"{metric_name}.unexpected_rows"
    unexpected_values_metric_name: str = f"{metric_name}.unexpected_values"

    # First, assert Pass (no unexpected results).

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "compound_columns.count.map": prerequisite_function_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return SQLAlchemy ColumnElement object.
    assert metrics[unexpected_count_metric.id] == 0

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_rows_metric.id]) == 0

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 0

    # Restore from saved original metrics in order to start fresh on testing for unexpected results.
    metrics = copy.deepcopy(metrics_save)

    # Second, assert Fail (one or more unexpected results).

    prerequisite_function_metric = MetricConfiguration(
        metric_name=prerequisite_function_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "c"],
        },
        metric_value_kwargs=None,
    )
    prerequisite_function_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(prerequisite_function_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "c"],
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "compound_columns.count.map": prerequisite_function_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "c"],
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return SQLAlchemy ColumnElement object.
    assert metrics[unexpected_count_metric.id] == 2

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "c"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id] == [(1, 2, 2), (1, 3, 2)]

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "c"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 2
    assert metrics[unexpected_values_metric.id] == [{"a": 1, "c": 2}, {"a": 1, "c": 2}]


def test_map_compound_columns_unique_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(data={"a": [0, 1, 1], "b": [1, 2, 3], "c": [0, 2, 2]}),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    """
    Two tests:
    1. Pass -- no duplicated compound column keys.
    2. Fail -- one or more duplicated compound column keys.
    """

    # Save original metrics for testing unexpected results.
    metrics_save: dict = copy.deepcopy(metrics)

    metric_name: str = "compound_columns.unique"
    condition_metric_name: str = f"{metric_name}.condition"
    unexpected_count_metric_name: str = f"{metric_name}.unexpected_count"
    unexpected_rows_metric_name: str = f"{metric_name}.unexpected_rows"
    unexpected_values_metric_name: str = f"{metric_name}.unexpected_values"

    # First, assert Pass (no unexpected results).

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert metrics[unexpected_count_metric.id] == 0

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id] == []

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 0
    assert metrics[unexpected_values_metric.id] == []

    # Restore from saved original metrics in order to start fresh on testing for unexpected results.
    metrics = copy.deepcopy(metrics_save)

    # Second, assert Fail (one or more unexpected results).

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "c"],
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "c"],
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert metrics[unexpected_count_metric.id] == 2

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "c"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id] == [(1, 2, 2), (1, 3, 2)]

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "c"],
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 2
    assert metrics[unexpected_values_metric.id] == [{"a": 1, "c": 2}, {"a": 1, "c": 2}]


def test_map_select_column_values_unique_within_record_pd():
    engine = build_pandas_engine(
        pd.DataFrame(
            data={
                "a": [1, 1, 8, 1, 4, None, None, 7],
                "b": [1, 2, 2, 2, 4, None, None, 1],
                "c": [2, 3, 7, 3, 4, None, 9, 0],
            }
        )
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    # Save original metrics for testing unexpected results.
    metrics_save: dict = copy.deepcopy(metrics)

    metric_name: str = "select_column_values.unique.within_record"
    condition_metric_name: str = f"{metric_name}.condition"
    unexpected_count_metric_name: str = f"{metric_name}.unexpected_count"
    unexpected_rows_metric_name: str = f"{metric_name}.unexpected_rows"
    unexpected_values_metric_name: str = f"{metric_name}.unexpected_values"

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "all_values_are_missing",
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "all_values_are_missing",
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert list(metrics[condition_metric.id][0]) == [
        True,
        False,
        False,
        False,
        True,
        True,
        False,
    ]
    assert metrics[unexpected_count_metric.id] == 3

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "all_values_are_missing",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 8}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id].equals(
        pd.DataFrame(
            data={"a": [1.0, 4.0, None], "b": [1.0, 4.0, None], "c": [2.0, 4.0, 9.0]},
            index=[0, 4, 6],
        )
    )
    assert len(metrics[unexpected_rows_metric.id].columns) == 3
    pd.testing.assert_index_equal(
        metrics[unexpected_rows_metric.id].index, pd.Index([0, 4, 6])
    )

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "all_values_are_missing",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 3

    unexpected_values = []
    for unexpected_value_dict in metrics[unexpected_values_metric.id]:
        updated_unexpected_value_dict = {
            key: "NULL" if np.isnan(value) else value
            for key, value in unexpected_value_dict.items()
        }
        unexpected_values.append(updated_unexpected_value_dict)

    assert unexpected_values == [
        {"a": 1.0, "b": 1.0, "c": 2.0},
        {"a": 4.0, "b": 4.0, "c": 4.0},
        {"a": "NULL", "b": "NULL", "c": 9.0},
    ]

    # Restore from saved original metrics in order to start fresh on testing for unexpected results.
    metrics = copy.deepcopy(metrics_save)

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "any_value_is_missing",
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "any_value_is_missing",
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert list(metrics[condition_metric.id][0]) == [
        True,
        False,
        False,
        False,
        True,
        False,
    ]
    assert metrics[unexpected_count_metric.id] == 2

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "any_value_is_missing",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id].equals(
        pd.DataFrame(
            data={"a": [1.0, 4.0], "b": [1.0, 4.0], "c": [2.0, 4.0]}, index=[0, 4]
        )
    )
    assert len(metrics[unexpected_rows_metric.id].columns) == 3
    pd.testing.assert_index_equal(
        metrics[unexpected_rows_metric.id].index, pd.Index([0, 4])
    )

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "any_value_is_missing",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 2
    assert metrics[unexpected_values_metric.id] == [
        {"a": 1.0, "b": 1.0, "c": 2.0},
        {"a": 4.0, "b": 4.0, "c": 4.0},
    ]


def test_map_select_column_values_unique_within_record_sa(sa):
    engine = build_sa_engine(
        pd.DataFrame(
            data={
                "a": [1, 1, 8, 1, 4, None, None, 7],
                "b": [1, 2, 2, 2, 4, None, None, 1],
                "c": [2, 3, 7, 3, 4, None, 9, 0],
            }
        ),
        sa,
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    # Save original metrics for testing unexpected results.
    metrics_save: dict = copy.deepcopy(metrics)

    metric_name: str = "select_column_values.unique.within_record"
    condition_metric_name: str = f"{metric_name}.condition"
    unexpected_count_metric_name: str = f"{metric_name}.unexpected_count"
    unexpected_rows_metric_name: str = f"{metric_name}.unexpected_rows"
    unexpected_values_metric_name: str = f"{metric_name}.unexpected_values"

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "all_values_are_missing",
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "all_values_are_missing",
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert metrics[unexpected_count_metric.id] == 3

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "all_values_are_missing",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 8}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id] == [
        (1.0, 1.0, 2.0),
        (4.0, 4.0, 4.0),
        (None, None, 9.0),
    ]

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "all_values_are_missing",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 3

    assert metrics[unexpected_values_metric.id] == [
        {"a": 1.0, "b": 1.0, "c": 2.0},
        {"a": 4.0, "b": 4.0, "c": 4.0},
        {"a": None, "b": None, "c": 9.0},
    ]

    # Restore from saved original metrics in order to start fresh on testing for unexpected results.
    metrics = copy.deepcopy(metrics_save)

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "any_value_is_missing",
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "any_value_is_missing",
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert metrics[unexpected_count_metric.id] == 2

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "any_value_is_missing",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id] == [(1.0, 1.0, 2.0), (4.0, 4.0, 4.0)]

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "any_value_is_missing",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 2
    assert metrics[unexpected_values_metric.id] == [
        {"a": 1.0, "b": 1.0, "c": 2.0},
        {"a": 4.0, "b": 4.0, "c": 4.0},
    ]


def test_map_select_column_values_unique_within_record_spark(spark_session):
    engine: SparkDFExecutionEngine = build_spark_engine(
        spark=spark_session,
        df=pd.DataFrame(
            data={
                "a": [1, 1, 8, 1, 4, None, None, 7],
                "b": [1, 2, 2, 2, 4, None, None, 1],
                "c": [2, 3, 7, 3, 4, None, 9, 0],
            }
        ),
        batch_id="my_id",
    )

    metrics: dict = {}

    table_columns_metric: MetricConfiguration
    results: dict

    table_columns_metric, results = get_table_columns_metric(engine=engine)
    metrics.update(results)

    # Save original metrics for testing unexpected results.
    metrics_save: dict = copy.deepcopy(metrics)

    metric_name: str = "select_column_values.unique.within_record"
    condition_metric_name: str = f"{metric_name}.condition"
    unexpected_count_metric_name: str = f"{metric_name}.unexpected_count"
    unexpected_rows_metric_name: str = f"{metric_name}.unexpected_rows"
    unexpected_values_metric_name: str = f"{metric_name}.unexpected_values"

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "all_values_are_missing",
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "all_values_are_missing",
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert metrics[unexpected_count_metric.id] == 3

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "all_values_are_missing",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 8}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id] == [
        (1.0, 1.0, 2.0),
        (4.0, 4.0, 4.0),
        (None, None, 9.0),
    ]

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "all_values_are_missing",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 3

    unexpected_values = []
    for unexpected_value_dict in metrics[unexpected_values_metric.id]:
        updated_unexpected_value_dict = {
            key: "NULL" if np.isnan(value) else value
            for key, value in unexpected_value_dict.items()
        }
        unexpected_values.append(updated_unexpected_value_dict)

    assert unexpected_values == [
        {"a": 1.0, "b": 1.0, "c": 2.0},
        {"a": 4.0, "b": 4.0, "c": 4.0},
        {"a": "NULL", "b": "NULL", "c": 9.0},
    ]

    # Restore from saved original metrics in order to start fresh on testing for unexpected results.
    metrics = copy.deepcopy(metrics_save)

    condition_metric = MetricConfiguration(
        metric_name=condition_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "any_value_is_missing",
        },
        metric_value_kwargs=None,
    )
    condition_metric._metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(condition_metric,),
        metrics=metrics,
    )
    metrics.update(results)

    unexpected_count_metric = MetricConfiguration(
        metric_name=unexpected_count_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "any_value_is_missing",
        },
        metric_value_kwargs=None,
    )
    unexpected_count_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_count_metric,), metrics=metrics
    )
    metrics.update(results)

    # Condition metrics return "negative logic" series.
    assert metrics[unexpected_count_metric.id] == 2

    unexpected_rows_metric = MetricConfiguration(
        metric_name=unexpected_rows_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "any_value_is_missing",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_rows_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_rows_metric,), metrics=metrics
    )
    metrics.update(results)

    assert metrics[unexpected_rows_metric.id] == [(1.0, 1.0, 2.0), (4.0, 4.0, 4.0)]

    unexpected_values_metric = MetricConfiguration(
        metric_name=unexpected_values_metric_name,
        metric_domain_kwargs={
            "column_list": ["a", "b", "c"],
            "ignore_row_if": "any_value_is_missing",
        },
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 3}
        },
    )
    unexpected_values_metric._metric_dependencies = {
        "unexpected_condition": condition_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(unexpected_values_metric,), metrics=metrics
    )
    metrics.update(results)

    assert len(metrics[unexpected_values_metric.id]) == 2
    assert metrics[unexpected_values_metric.id] == [
        {"a": 1.0, "b": 1.0, "c": 2.0},
        {"a": 4.0, "b": 4.0, "c": 4.0},
    ]
