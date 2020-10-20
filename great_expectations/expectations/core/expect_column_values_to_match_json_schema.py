import json
from typing import Dict, List, Optional, Union

import jsonschema
import numpy as np
import pandas as pd

from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.execution_engine import (
    ExecutionEngine,
    PandasExecutionEngine,
    SparkDFExecutionEngine,
)

from ...core.batch import Batch
from ...data_asset.util import parse_result_format
from ...execution_engine.sqlalchemy_execution_engine import SqlAlchemyExecutionEngine
from ..expectation import (
    ColumnMapDatasetExpectation,
    Expectation,
    InvalidExpectationConfigurationError,
    _format_map_output,
)
from ..registry import extract_metrics, get_metric_kwargs

try:
    import sqlalchemy as sa
except ImportError:
    pass


class ExpectColumnValuesToMatchJsonSchema(ColumnMapDatasetExpectation):
    """Expect column entries to be JSON objects matching a given JSON schema.

    expect_column_values_to_match_json_schema is a \
    :func:`column_map_expectation <great_expectations.execution_engine.execution_engine.MetaExecutionEngine
    .column_map_expectation>`.

    Args:
        column (str): \
            The column name.

    Keyword Args:
        mostly (None or a float between 0 and 1): \
            Return `"success": True` if at least mostly fraction of values match the expectation. \
            For more detail, see :ref:`mostly`.

    Other Parameters:
        result_format (str or None): \
            Which output mode to use: `BOOLEAN_ONLY`, `BASIC`, `COMPLETE`, or `SUMMARY`.
            For more detail, see :ref:`result_format <result_format>`.
        include_config (boolean): \
            If True, then include the expectation config as part of the result object. \
            For more detail, see :ref:`include_config`.
        catch_exceptions (boolean or None): \
            If True, then catch exceptions and include them as part of the result object. \
            For more detail, see :ref:`catch_exceptions`.
        meta (dict or None): \
            A JSON-serializable dictionary (nesting allowed) that will be included in the output without \
            modification. For more detail, see :ref:`meta`.

    Returns:
        An ExpectationSuiteValidationResult

        Exact fields vary depending on the values passed to :ref:`result_format <result_format>` and
        :ref:`include_config`, :ref:`catch_exceptions`, and :ref:`meta`.

    See Also:
        :func:`expect_column_values_to_be_json_parseable \
        <great_expectations.execution_engine.execution_engine.ExecutionEngine
        .expect_column_values_to_be_json_parseable>`


        The `JSON-schema docs <http://json-schema.org/>`_.
    """

    map_metric = "column_values.match_json_schema"
    success_keys = (
        "json_schema",
        "mostly",
    )

    default_kwarg_values = {
        "row_condition": None,
        "condition_parser": None,  # we expect this to be explicitly set whenever a row_condition is passed
        "mostly": 1,
        "result_format": "BASIC",
        "include_config": True,
        "catch_exceptions": True,
    }

    def validate_configuration(self, configuration: Optional[ExpectationConfiguration]):
        super().validate_configuration(configuration)

        return True

    # @PandasExecutionEngine.column_map_metric(
    #     metric_name="column_values.match_json_schema",
    #     metric_domain_keys=ColumnMapDatasetExpectation.domain_keys,
    #     metric_value_keys=("json_schema",),
    #     metric_dependencies=tuple(),
    #     filter_column_isnull=True,
    # )
    def _pandas_column_values_match_json_schema(
        self,
        series: pd.Series,
        metrics: dict,
        metric_domain_kwargs: dict,
        metric_value_kwargs: dict,
        runtime_configuration: dict = None,
        filter_column_isnull: bool = True,
    ):
        json_schema = metric_value_kwargs["json_schema"]

        def matches_json_schema(val):
            try:
                val_json = json.loads(val)
                jsonschema.validate(val_json, json_schema)
                # jsonschema.validate raises an error if validation fails.
                # So if we make it this far, we know that the validation succeeded.
                return True
            except jsonschema.ValidationError:
                return False
            except jsonschema.SchemaError:
                raise
            except:
                raise

        return pd.DataFrame(
            {"column_values.match_json_schema": series.map(matches_json_schema)}
        )

    # @SqlAlchemyExecutionEngine.column_map_metric(
    #     metric_name="column_values.match_json_schema",
    #     metric_domain_keys=ColumnMapDatasetExpectation.domain_keys,
    #     metric_value_keys=("json",),
    #     metric_dependencies=tuple(),
    # )
    # def _sqlalchemy_match_json_schema(
    #     self,
    #     column: sa.column,
    #     json: str,
    #     runtime_configuration: dict = None,
    #     filter_column_isnull: bool = True,
    # ):
    #     json_expression = execution_engine._get_dialect_json_expression(column, json)
    #     if json_expression is None:
    #         logger.warning(
    #             "json is not supported for dialect %s" % str(self.sql_engine_dialect)
    #         )
    #         raise NotImplementedError
    #
    #     return json_expression
    #     if json is None:
    #         # vacuously true
    #         return True
    #
    #     return column.in_(tuple(json))
    #
    # @SparkDFExecutionEngine.column_map_metric(
    #     metric_name="column_values.match_json_schema",
    #     metric_domain_keys=ColumnMapDatasetExpectation.domain_keys,
    #     metric_value_keys=("json",),
    #     metric_dependencies=tuple(),
    # )
    # def _spark_match_json_schema(
    #     self,
    #     data: "pyspark.sql.DataFrame",
    #     column: str,
    #     json: str,
    #     runtime_configuration: dict = None,
    #     filter_column_isnull: bool = True,
    # ):
    #     import pyspark.sql.functions as F
    #
    #     if json is None:
    #         # vacuously true
    #         return data.withColumn(column + "__success", F.lit(True))
    #
    #     return data.withColumn(column + "__success", F.col(column).isin(json))
