from typing import Dict, List, Optional

from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.execution_engine import ExecutionEngine
from great_expectations.expectations.expectation import ColumnExpectation
from great_expectations.expectations.util import render_evaluation_parameter_string
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.types import RenderedStringTemplateContent
from great_expectations.render.util import (
    handle_strict_min_max,
    num_to_str,
    parse_row_condition_string_pandas_engine,
    substitute_none_for_missing,
)
from great_expectations.rule_based_profiler.config.base import (
    ParameterBuilderConfig,
    RuleBasedProfilerConfig,
)
from great_expectations.rule_based_profiler.types.parameter_container import (
    DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME,
    FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY,
    FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER,
    FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY,
    PARAMETER_KEY,
    VARIABLES_KEY,
)


class ExpectColumnUniqueValueCountToBeBetween(ColumnExpectation):
    """Expect the number of unique values to be between a minimum value and a maximum value.

            expect_column_unique_value_count_to_be_between is a \
            :func:`column_aggregate_expectation
            <great_expectations.execution_engine.MetaExecutionEngine.column_aggregate_expectation>`.

            Args:
                column (str): \
                    The column name.
                min_value (int or None): \
                    The minimum number of unique values allowed.
                max_value (int or None): \
                    The maximum number of unique values allowed.

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

            Notes:
                These fields in the result object are customized for this expectation:
                ::

                    {
                        "observed_value": (int) The number of unique values in the column
                    }

                * min_value and max_value are both inclusive.
                * If min_value is None, then max_value is treated as an upper bound
                * If max_value is None, then min_value is treated as a lower bound

            See Also:
                :func:`expect_column_proportion_of_unique_values_to_be_between \
                <great_expectations.execution_engine.execution_engine.ExecutionEngine
                .expect_column_proportion_of_unique_values_to_be_between>`

            """

    # This dictionary contains metadata for display in the public gallery
    library_metadata = {
        "maturity": "production",
        "tags": ["core expectation", "column aggregate expectation"],
        "contributors": ["@great_expectations"],
        "requirements": [],
        "has_full_test_suite": True,
        "manually_reviewed_code": True,
    }

    # Setting necessary computation metric dependencies and defining kwargs, as well as assigning kwargs default values\
    metric_dependencies = ("column.distinct_values.count",)
    success_keys = (
        "min_value",
        "max_value",
        "auto",
        "profiler_config",
    )

    column_unique_values_range_estimator_parameter_builder_config: ParameterBuilderConfig = ParameterBuilderConfig(
        module_name="great_expectations.rule_based_profiler.parameter_builder",
        class_name="NumericMetricRangeMultiBatchParameterBuilder",
        name="column_unique_values_range_estimator",
        metric_name="column.distinct_values.count",
        metric_domain_kwargs=DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME,
        metric_value_kwargs=None,
        enforce_numeric_metric=True,
        replace_nan_with_zero=True,
        reduce_scalar_metric=True,
        false_positive_rate=f"{VARIABLES_KEY}false_positive_rate",
        quantile_statistic_interpolation_method=f"{VARIABLES_KEY}quantile_statistic_interpolation_method",
        estimator=f"{VARIABLES_KEY}estimator",
        n_resamples=f"{VARIABLES_KEY}n_resamples",
        random_seed=f"{VARIABLES_KEY}random_seed",
        include_bootstrap_samples_histogram_in_details=f"{VARIABLES_KEY}include_bootstrap_samples_histogram_in_details",
        truncate_values=f"{VARIABLES_KEY}truncate_values",
        round_decimals=f"{VARIABLES_KEY}round_decimals",
        evaluation_parameter_builder_configs=None,
        json_serialize=True,
    )
    validation_parameter_builder_configs: List[ParameterBuilderConfig] = [
        column_unique_values_range_estimator_parameter_builder_config,
    ]
    default_profiler_config: RuleBasedProfilerConfig = RuleBasedProfilerConfig(
        name="expect_column_unique_value_count_to_be_between",  # Convention: use "expectation_type" as profiler name.
        config_version=1.0,
        variables={},
        rules={
            "default_expect_column_unique_values_to_be_between_rule": {
                "variables": {
                    "mostly": 1.0,
                    "strict_min": False,
                    "strict_max": False,
                    "false_positive_rate": 0.05,
                    "quantile_statistic_interpolation_method": "auto",
                    "estimator": "bootstrap",
                    "n_resamples": 9999,
                    "random_seed": None,
                    "include_bootstrap_samples_histogram_in_details": False,
                    "truncate_values": {
                        "lower_bound": 0,
                        "upper_bound": None,
                    },
                    "round_decimals": 0,
                },
                "domain_builder": {
                    "class_name": "ColumnDomainBuilder",
                    "module_name": "great_expectations.rule_based_profiler.domain_builder",
                },
                "expectation_configuration_builders": [
                    {
                        "expectation_type": "expect_column_unique_value_count_to_be_between",
                        "class_name": "DefaultExpectationConfigurationBuilder",
                        "module_name": "great_expectations.rule_based_profiler.expectation_configuration_builder",
                        "validation_parameter_builder_configs": validation_parameter_builder_configs,
                        "column": f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
                        "min_value": f"{PARAMETER_KEY}{column_unique_values_range_estimator_parameter_builder_config.name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[0]",
                        "max_value": f"{PARAMETER_KEY}{column_unique_values_range_estimator_parameter_builder_config.name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[1]",
                        "strict_min": f"{VARIABLES_KEY}strict_min",
                        "strict_max": f"{VARIABLES_KEY}strict_max",
                        "meta": {
                            "profiler_details": f"{PARAMETER_KEY}{column_unique_values_range_estimator_parameter_builder_config.name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
                        },
                    },
                ],
            },
        },
    )

    # Default values
    default_kwarg_values = {
        "row_condition": None,
        "condition_parser": None,
        "min_value": None,
        "max_value": None,
        "result_format": "BASIC",
        "include_config": True,
        "catch_exceptions": False,
        "auto": False,
        "profiler_config": default_profiler_config,
    }
    args_keys = (
        "column",
        "min_value",
        "max_value",
    )

    """ A Column Aggregate Metric Decorator for the Unique Value Count"""

    def validate_configuration(
        self, configuration: Optional[ExpectationConfiguration]
    ) -> None:
        """
        Validates that a configuration has been set, and sets a configuration if it has yet to be set. Ensures that
        necessary configuration arguments have been provided for the validation of the expectation.

        Args:
            configuration (OPTIONAL[ExpectationConfiguration]): \
                An optional Expectation Configuration entry that will be used to configure the expectation
        Returns:
            None. Raises InvalidExpectationConfigurationError if the config is not validated successfully
        """
        super().validate_configuration(configuration)
        self.validate_metric_value_between_configuration(configuration=configuration)

    @classmethod
    def _atomic_prescriptive_template(
        cls,
        configuration=None,
        result=None,
        language=None,
        runtime_configuration=None,
        **kwargs,
    ):
        runtime_configuration = runtime_configuration or {}
        include_column_name = runtime_configuration.get("include_column_name", True)
        include_column_name = (
            include_column_name if include_column_name is not None else True
        )
        styling = runtime_configuration.get("styling")
        params = substitute_none_for_missing(
            configuration.kwargs,
            [
                "column",
                "min_value",
                "max_value",
                "mostly",
                "row_condition",
                "condition_parser",
                "strict_min",
                "strict_max",
            ],
        )
        params_with_json_schema = {
            "column": {"schema": {"type": "string"}, "value": params.get("column")},
            "min_value": {
                "schema": {"type": "number"},
                "value": params.get("min_value"),
            },
            "max_value": {
                "schema": {"type": "number"},
                "value": params.get("max_value"),
            },
            "mostly": {"schema": {"type": "number"}, "value": params.get("mostly")},
            "mostly_pct": {
                "schema": {"type": "string"},
                "value": params.get("mostly_pct"),
            },
            "row_condition": {
                "schema": {"type": "string"},
                "value": params.get("row_condition"),
            },
            "condition_parser": {
                "schema": {"type": "string"},
                "value": params.get("condition_parser"),
            },
            "strict_min": {
                "schema": {"type": "boolean"},
                "value": params.get("strict_min"),
            },
            "strict_max": {
                "schema": {"type": "boolean"},
                "value": params.get("strict_max"),
            },
        }

        at_least_str, at_most_str = handle_strict_min_max(params)

        if (params["min_value"] is None) and (params["max_value"] is None):
            template_str = "may have any number of unique values."
        else:
            if params["mostly"] is not None and params["mostly"] < 1.0:
                params_with_json_schema["mostly_pct"]["value"] = num_to_str(
                    params["mostly"] * 100, precision=15, no_scientific=True
                )
                # params["mostly_pct"] = "{:.14f}".format(params["mostly"]*100).rstrip("0").rstrip(".")
                if params["min_value"] is None:
                    template_str = f"must have {at_most_str} $max_value unique values, at least $mostly_pct % of the time."
                elif params["max_value"] is None:
                    template_str = f"must have {at_least_str} $min_value unique values, at least $mostly_pct % of the time."
                else:
                    template_str = f"must have {at_least_str} $min_value and {at_most_str} $max_value unique values, at least $mostly_pct % of the time."
            else:
                if params["min_value"] is None:
                    template_str = f"must have {at_most_str} $max_value unique values."
                elif params["max_value"] is None:
                    template_str = f"must have {at_least_str} $min_value unique values."
                else:
                    template_str = f"must have {at_least_str} $min_value and {at_most_str} $max_value unique values."

        if include_column_name:
            template_str = f"$column {template_str}"

        if params["row_condition"] is not None:
            (
                conditional_template_str,
                conditional_params,
            ) = parse_row_condition_string_pandas_engine(
                params["row_condition"], with_schema=True
            )
            template_str = f"{conditional_template_str}, then {template_str}"
            params_with_json_schema.update(conditional_params)

        return (template_str, params_with_json_schema, styling)

    @classmethod
    @renderer(renderer_type="renderer.prescriptive")
    @render_evaluation_parameter_string
    def _prescriptive_renderer(
        cls,
        configuration=None,
        result=None,
        language=None,
        runtime_configuration=None,
        **kwargs,
    ):
        runtime_configuration = runtime_configuration or {}
        include_column_name = runtime_configuration.get("include_column_name", True)
        include_column_name = (
            include_column_name if include_column_name is not None else True
        )
        styling = runtime_configuration.get("styling")
        params = substitute_none_for_missing(
            configuration.kwargs,
            [
                "column",
                "min_value",
                "max_value",
                "mostly",
                "row_condition",
                "condition_parser",
                "strict_min",
                "strict_max",
            ],
        )

        at_least_str, at_most_str = handle_strict_min_max(params)

        if (params["min_value"] is None) and (params["max_value"] is None):
            template_str = "may have any number of unique values."
        else:
            if params["mostly"] is not None and params["mostly"] < 1.0:
                params["mostly_pct"] = num_to_str(
                    params["mostly"] * 100, precision=15, no_scientific=True
                )
                # params["mostly_pct"] = "{:.14f}".format(params["mostly"]*100).rstrip("0").rstrip(".")
                if params["min_value"] is None:
                    template_str = f"must have {at_most_str} $max_value unique values, at least $mostly_pct % of the time."
                elif params["max_value"] is None:
                    template_str = f"must have {at_least_str} $min_value unique values, at least $mostly_pct % of the time."
                else:
                    template_str = f"must have {at_least_str} $min_value and {at_most_str} $max_value unique values, at least $mostly_pct % of the time."
            else:
                if params["min_value"] is None:
                    template_str = f"must have {at_most_str} $max_value unique values."
                elif params["max_value"] is None:
                    template_str = f"must have {at_least_str} $min_value unique values."
                else:
                    template_str = f"must have {at_least_str} $min_value and {at_most_str} $max_value unique values."

        if include_column_name:
            template_str = f"$column {template_str}"

        if params["row_condition"] is not None:
            (
                conditional_template_str,
                conditional_params,
            ) = parse_row_condition_string_pandas_engine(params["row_condition"])
            template_str = f"{conditional_template_str}, then {template_str}"
            params.update(conditional_params)

        return [
            RenderedStringTemplateContent(
                **{
                    "content_block_type": "string_template",
                    "string_template": {
                        "template": template_str,
                        "params": params,
                        "styling": styling,
                    },
                }
            )
        ]

    @classmethod
    @renderer(
        renderer_type="renderer.descriptive.column_properties_table.distinct_count_row"
    )
    def _descriptive_column_properties_table_distinct_count_row_renderer(
        cls,
        configuration=None,
        result=None,
        language=None,
        runtime_configuration=None,
        **kwargs,
    ):
        assert result, "Must pass in result."
        observed_value = result.result["observed_value"]
        template_string_object = RenderedStringTemplateContent(
            **{
                "content_block_type": "string_template",
                "string_template": {
                    "template": "Distinct (n)",
                    "tooltip": {
                        "content": "expect_column_unique_value_count_to_be_between"
                    },
                },
            }
        )
        if not observed_value:
            return [template_string_object, "--"]
        else:
            return [template_string_object, observed_value]

    def _validate(
        self,
        configuration: ExpectationConfiguration,
        metrics: Dict,
        runtime_configuration: dict = None,
        execution_engine: ExecutionEngine = None,
    ):
        return self._validate_metric_value_between(
            metric_name="column.distinct_values.count",
            configuration=configuration,
            metrics=metrics,
            runtime_configuration=runtime_configuration,
            execution_engine=execution_engine,
        )
