from typing import Optional

from sqlalchemy.engine import reflection

from great_expectations.core import ExpectationConfiguration
from great_expectations.core.metric import Metric
from great_expectations.execution_engine import ExecutionEngine, PandasExecutionEngine
from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.column_aggregate_metric import (
    ColumnAggregateMetric,
    column_aggregate_metric,
)
from great_expectations.expectations.metrics.column_aggregate_metric import sa as sa
from great_expectations.expectations.metrics.table_metric import (
    TableMetric,
    table_metric,
)
from great_expectations.expectations.metrics.utils import column_reflection_fallback
from great_expectations.validator.validation_graph import MetricConfiguration


class TableColumnCount(TableMetric):
    metric_name = "table.column_count"

    @table_metric(engine=PandasExecutionEngine)
    def _pandas(cls, table, **kwargs):
        return table.shape[1]

    @table_metric(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(cls, table, _dialect, _sqlalchemy_engine, _metrics, **kwargs):
        columns = _metrics.get("columns")
        return len(columns)

    @classmethod
    def get_evaluation_dependencies(
        cls,
        metric: MetricConfiguration,
        configuration: Optional[ExpectationConfiguration] = None,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[dict] = None,
    ):
        """This should return a dictionary:

        {
          "dependency_name": MetricConfiguration,
          ...
        }
        """
        return {
            "table.columns": MetricConfiguration(
                "table.columns", metric.metric_domain_kwargs
            ),
        }
