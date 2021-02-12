import json
from typing import Optional

from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
)
from great_expectations.expectations.expectation import (
    ColumnMapExpectation,
    ExpectationConfiguration,
)
from great_expectations.expectations.metrics.import_manager import F, sparktypes
from great_expectations.expectations.metrics.map_metric import (
    ColumnMapMetricProvider,
    column_condition_partial,
)

from great_expectations.expectations.util import render_evaluation_parameter_string

from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.types import RenderedStringTemplateContent
from great_expectations.render.util import (
    num_to_str,
    parse_row_condition_string_pandas_engine,
    substitute_none_for_missing,
)

try:
    import sqlalchemy as sa
except ImportError:
    pass


class ColumnValuesPassFilter(ColumnMapMetricProvider):
    condition_metric_name = "column_values.to_pass_filter"
    condition_value_keys = ("filter",)

    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column, filter, **kwargs):
        # filter must be a function
        assert(callable(filter))

        return column.map(filter)

    @column_condition_partial(engine=SparkDFExecutionEngine)
    def _spark(cls, column, filter, **kwargs):
        # filter must be a function
        assert(callable(filter))

        passes_function_udf = F.udf(filter, sparktypes.BooleanType())

        return passes_function_udf(column)

class ExpectColumnValuesToPassFilter(ColumnMapExpectation):
    """Expect column entries to pass a custom filter function.

    expect_column_values_to_pass_filter is a \
    :func:`column_map_expectation <great_expectations.execution_engine.execution_engine.MetaExecutionEngine
    .column_map_expectation>`.

    Args:
        column (str): \
            The column name.
        filter (function): \
            A filter function that takes the column value as input and returns true or false.

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
    """

    # These examples will be shown in the public gallery, and also executed as unit tests for your Expectation
    examples = [
        {
            "data": {
                "even_number": [2,4,6,8,10],
                "odd_number": [1,3,5,7,9],
            },
            "tests": [
                {
                    "title": "test_numbers_even",
                    "exact_match_out": True,
                    "include_in_gallery": True,
                    "in": {
                        "column": "even_number",
                        "filter": lambda x: x % 2 == 0,
                    },
                    "out": {
                        "success": True,
                        "unexpected_index_list": [],
                        "unexpected_list": [],
                    },
                },
                {
                    "title": "test_numbers_odd",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {
                        "column": "odd_number",
                        "filter": lambda x: x % 2 == 0,
                    },
                    "out": {
                        "success": False,
                        "unexpected_index_list": [],
                        "unexpected_list": [],
                    },
                },
            ]
        }
    ]

    # This dictionary contains metadata for display in the public gallery
    library_metadata = {
        "maturity": "experimental",  # "experimental", "beta", or "production"
        "tags": ["filter" , "glam"],
        "contributors": ["@mielvds"],
        "package": "experimental_expectations",
        "requirements": [],
    }

    map_metric = "column_values.to_pass_filter"
    success_keys = (
        "filter",
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

    @classmethod
    @renderer(renderer_type="renderer.prescriptive")
    @render_evaluation_parameter_string
    def _prescriptive_renderer(
        cls,
        configuration=None,
        result=None,
        language=None,
        runtime_configuration=None,
        **kwargs
    ):
        runtime_configuration = runtime_configuration or {}
        include_column_name = runtime_configuration.get("include_column_name", True)
        include_column_name = (
            include_column_name if include_column_name is not None else True
        )
        styling = runtime_configuration.get("styling")
        params = substitute_none_for_missing(
            configuration.kwargs,
            ["column", "filter", "mostly", "row_condition", "condition_parser"],
        )

        if not params.get("filter"):
            template_str = "values must match a filter function but none was specified."
        else:
            params["formatted_function"] = (
                "<pre>" + params.get("filter") + "</pre>"
            )
            if params["mostly"] is not None:
                params["mostly_pct"] = num_to_str(
                    params["mostly"] * 100, precision=15, no_scientific=True
                )
                template_str = "values must pass the filter function, at least $mostly_pct % of the time: $formatted_function"
            else:
                template_str = (
                    "values must pass the following function: $formatted_xml"
                )

        if include_column_name:
            template_str = "$column " + template_str

        if params["row_condition"] is not None:
            (
                conditional_template_str,
                conditional_params,
            ) = parse_row_condition_string_pandas_engine(params["row_condition"])
            template_str = conditional_template_str + ", then " + template_str
            params.update(conditional_params)

        return [
            RenderedStringTemplateContent(
                **{
                    "content_block_type": "string_template",
                    "string_template": {
                        "template": template_str,
                        "params": params,
                        "styling": {"params": {"filter": {"classes": []}}},
                    },
                }
            )
        ]

if __name__ == "__main__":
    diagnostics_report = ExpectColumnValuesToPassFilter().run_diagnostics()
    print(diagnostics_report)
    
    #print(json.dumps(diagnostics_report, indent=2))