from numbers import Number
from typing import List, Optional, Tuple, Union

from great_expectations.core import (
    ExpectationConfiguration,
    ExpectationValidationResult,
)
from great_expectations.expectations.expectation import (
    ColumnMapExpectation,
    InvalidExpectationConfigurationError,
)
from great_expectations.render import (
    LegacyDescriptiveRendererType,
    LegacyRendererType,
    RenderedBulletListContent,
    RenderedStringTemplateContent,
    ValueListContent,
)
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.renderer_configuration import (
    ParamSchemaType,
    RendererConfiguration,
    RendererParams,
)
from great_expectations.render.util import (
    num_to_str,
    parse_row_condition_string_pandas_engine,
    substitute_none_for_missing,
)
from great_expectations.rule_based_profiler.config import (
    ParameterBuilderConfig,
    RuleBasedProfilerConfig,
)
from great_expectations.rule_based_profiler.parameter_container import (
    DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME,
    FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY,
    FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER,
    FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY,
    PARAMETER_KEY,
    VARIABLES_KEY,
)

try:
    import sqlalchemy as sa  # noqa: F401
except ImportError:
    pass
from great_expectations.expectations.expectation import (
    render_evaluation_parameter_string,
)


class ExpectColumnValuesToBeInSet(ColumnMapExpectation):
    """Expect each column value to be in a given set.

    For example:
    ::

        # my_df.my_col = [1,2,2,3,3,3]
        >>> my_df.expect_column_values_to_be_in_set(
            "my_col",
            [2,3]
        )
        {
          "success": false
          "result": {
            "unexpected_count": 1
            "unexpected_percent": 16.66666666666666666,
            "unexpected_percent_nonmissing": 16.66666666666666666,
            "partial_unexpected_list": [
              1
            ],
          },
        }

    expect_column_values_to_be_in_set is a \
    :func:`column_map_expectation <great_expectations.execution_engine.execution_engine.MetaExecutionEngine
    .column_map_expectation>`.

    Args:
        column (str): \
            The column name.
        value_set (set-like): \
            A set of objects used for comparison.

    Keyword Args:
        mostly (None or a float between 0 and 1): \
            Return `"success": True` if at least mostly fraction of values match the expectation. \
            For more detail, see :ref:`mostly`.
        parse_strings_as_datetimes (boolean or None) : If True values provided in value_set will be parsed as \
            datetimes before making comparisons.

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
        :func:`expect_column_values_to_not_be_in_set \
        <great_expectations.execution_engine.execution_engine.ExecutionEngine
        .expect_column_values_to_not_be_in_set>`

    """

    # This dictionary contains metadata for display in the public gallery
    library_metadata = {
        "maturity": "production",
        "tags": ["core expectation", "column map expectation"],
        "contributors": ["@great_expectations"],
        "requirements": [],
        "has_full_test_suite": True,
        "manually_reviewed_code": True,
    }

    map_metric = "column_values.in_set"

    args_keys = (
        "column",
        "value_set",
    )

    success_keys = (
        "value_set",
        "mostly",
        "parse_strings_as_datetimes",
        "auto",
        "profiler_config",
    )

    value_set_estimator_parameter_builder_config: ParameterBuilderConfig = (
        ParameterBuilderConfig(
            module_name="great_expectations.rule_based_profiler.parameter_builder",
            class_name="ValueSetMultiBatchParameterBuilder",
            name="value_set_estimator",
            metric_domain_kwargs=DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME,
            metric_value_kwargs=None,
            evaluation_parameter_builder_configs=None,
        )
    )
    validation_parameter_builder_configs: List[ParameterBuilderConfig] = [
        value_set_estimator_parameter_builder_config,
    ]
    default_profiler_config = RuleBasedProfilerConfig(
        name="expect_column_values_to_be_in_set",  # Convention: use "expectation_type" as profiler name.
        config_version=1.0,
        variables={},
        rules={
            "default_expect_column_values_to_be_in_set_rule": {
                "variables": {
                    "mostly": 1.0,
                },
                "domain_builder": {
                    "class_name": "ColumnDomainBuilder",
                    "module_name": "great_expectations.rule_based_profiler.domain_builder",
                },
                "expectation_configuration_builders": [
                    {
                        "expectation_type": "expect_column_values_to_be_in_set",
                        "class_name": "DefaultExpectationConfigurationBuilder",
                        "module_name": "great_expectations.rule_based_profiler.expectation_configuration_builder",
                        "validation_parameter_builder_configs": validation_parameter_builder_configs,
                        "column": f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
                        "value_set": f"{PARAMETER_KEY}{value_set_estimator_parameter_builder_config.name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}",
                        "mostly": f"{VARIABLES_KEY}mostly",
                        "meta": {
                            "profiler_details": f"{PARAMETER_KEY}{value_set_estimator_parameter_builder_config.name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
                        },
                    },
                ],
            },
        },
    )

    default_kwarg_values = {
        "value_set": [],
        "parse_strings_as_datetimes": False,
        "auto": False,
        "profiler_config": default_profiler_config,
    }

    @classmethod
    def _prescriptive_template(
        cls,
        renderer_configuration: RendererConfiguration,
    ) -> RendererConfiguration:
        renderer_configuration.add_param(
            name="column",
            schema_type=ParamSchemaType.STRING,
        )
        renderer_configuration.add_param(
            name="value_set",
            schema_type=ParamSchemaType.ARRAY,
        )
        renderer_configuration.add_param(
            name="mostly",
            schema_type=ParamSchemaType.NUMBER,
        )
        renderer_configuration.add_param(
            name="mostly_pct",
            schema_type=ParamSchemaType.STRING,
        )
        renderer_configuration.add_param(
            name="parse_strings_as_datetimes",
            schema_type=ParamSchemaType.BOOLEAN,
        )
        renderer_configuration.add_param(
            name="row_condition",
            schema_type=ParamSchemaType.STRING,
        )
        renderer_configuration.add_param(
            name="condition_parser",
            schema_type=ParamSchemaType.STRING,
        )

        params: RendererParams
        params = renderer_configuration.params

        if not params.value_set or len(params.value_set.value) == 0:
            values_string = "[ ]"
        else:
            for i, v in enumerate(params.value_set.value):
                if isinstance(v, Number):
                    schema_type = ParamSchemaType.NUMBER
                else:
                    schema_type = ParamSchemaType.STRING
                renderer_configuration.add_param(
                    name=f"v__{str(i)}", schema_type=schema_type, value=v
                )

            params = renderer_configuration.params

            values_string = " ".join(
                [f"$v__{str(i)}" for i, v in enumerate(params.value_set.value)]
            )

        template_str = f"values must belong to this set: {values_string}"

        if params.mostly.value and params.mostly.value < 1.0:
            params.mostly_pct.value = num_to_str(
                params.mostly.value * 100, precision=15, no_scientific=True
            )
            template_str += ", at least $mostly_pct % of the time."
        else:
            template_str += "."

        if params.parse_strings_as_datetimes.value:
            template_str += " Values should be parsed as datetimes."

        if renderer_configuration.include_column_name:
            template_str = f"$column {template_str}"

        if params.row_condition.value:
            (
                conditional_template_str,
                conditional_params,
            ) = parse_row_condition_string_pandas_engine(params.row_condition.value)
            template_str = f"{conditional_template_str}, then {template_str}"
            for conditional_param, condition in conditional_params.items():
                renderer_configuration.add_param(
                    name=conditional_param,
                    schema_type=ParamSchemaType.STRING,
                    value=condition,
                )

        renderer_configuration.template_str = template_str

        return renderer_configuration

    @classmethod
    @renderer(renderer_type=LegacyRendererType.PRESCRIPTIVE)
    @render_evaluation_parameter_string
    def _prescriptive_renderer(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> List[RenderedStringTemplateContent]:
        renderer_configuration = RendererConfiguration(
            configuration=configuration,
            result=result,
            runtime_configuration=runtime_configuration,
        )
        params = substitute_none_for_missing(
            configuration.kwargs,
            [
                "column",
                "value_set",
                "mostly",
                "parse_strings_as_datetimes",
                "row_condition",
                "condition_parser",
            ],
        )

        if params["value_set"] is None or len(params["value_set"]) == 0:
            values_string = "[ ]"
        else:
            for i, v in enumerate(params["value_set"]):
                params[f"v__{str(i)}"] = v

            values_string = " ".join(
                [f"$v__{str(i)}" for i, v in enumerate(params["value_set"])]
            )

        template_str = f"values must belong to this set: {values_string}"

        if params["mostly"] is not None and params["mostly"] < 1.0:
            params["mostly_pct"] = num_to_str(
                params["mostly"] * 100, precision=15, no_scientific=True
            )
            # params["mostly_pct"] = "{:.14f}".format(params["mostly"]*100).rstrip("0").rstrip(".")
            template_str += ", at least $mostly_pct % of the time."
        else:
            template_str += "."

        if params.get("parse_strings_as_datetimes"):
            template_str += " Values should be parsed as datetimes."

        if renderer_configuration.include_column_name:
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
                        "styling": renderer_configuration.styling,
                    },
                }
            )
        ]

    @classmethod
    @renderer(renderer_type=LegacyDescriptiveRendererType.EXAMPLE_VALUES_BLOCK)
    def _descriptive_example_values_block_renderer(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> Optional[Union[RenderedBulletListContent, ValueListContent]]:
        assert result, "Must pass in result."
        if "partial_unexpected_counts" in result.result:
            partial_unexpected_counts = result.result["partial_unexpected_counts"]
            values = [str(v["value"]) for v in partial_unexpected_counts]
        elif "partial_unexpected_list" in result.result:
            values = [str(item) for item in result.result["partial_unexpected_list"]]
        else:
            return

        classes = ["col-3", "mt-1", "pl-1", "pr-1"]

        if any(len(value) > 80 for value in values):
            content_block_type = "bullet_list"
            content_block_class = RenderedBulletListContent
        else:
            content_block_type = "value_list"
            content_block_class = ValueListContent

        new_block = content_block_class(
            **{
                "content_block_type": content_block_type,
                "header": RenderedStringTemplateContent(
                    **{
                        "content_block_type": "string_template",
                        "string_template": {
                            "template": "Example Values",
                            "tooltip": {"content": "expect_column_values_to_be_in_set"},
                            "tag": "h6",
                        },
                    }
                ),
                content_block_type: [
                    {
                        "content_block_type": "string_template",
                        "string_template": {
                            "template": "$value",
                            "params": {"value": value},
                            "styling": {
                                "default": {
                                    "classes": ["badge", "badge-info"]
                                    if content_block_type == "value_list"
                                    else [],
                                    "styles": {"word-break": "break-all"},
                                },
                            },
                        },
                    }
                    for value in values
                ],
                "styling": {
                    "classes": classes,
                },
            }
        )

        return new_block

    def validate_configuration(
        self, configuration: Optional[ExpectationConfiguration]
    ) -> None:
        super().validate_configuration(configuration)
        # supports extensibility by allowing value_set to not be provided in config but captured via child-class default_kwarg_values, e.g. parameterized expectations
        value_set = configuration.kwargs.get(
            "value_set"
        ) or self.default_kwarg_values.get("value_set")
        try:
            assert (
                "value_set" in configuration.kwargs or value_set
            ), "value_set is required"
            assert isinstance(
                value_set, (list, set, dict)
            ), "value_set must be a list, set, or dict"
            if isinstance(value_set, dict):
                assert (
                    "$PARAMETER" in value_set
                ), 'Evaluation Parameter dict for value_set kwarg must have "$PARAMETER" key.'
        except AssertionError as e:
            raise InvalidExpectationConfigurationError(str(e))
