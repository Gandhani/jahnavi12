from typing import Any, Dict, List, Optional, Union

from great_expectations.core.batch import BatchRequestBase
from great_expectations.data_context import BaseDataContext
from great_expectations.execution_engine.execution_engine import MetricDomainTypes
from great_expectations.rule_based_profiler.data_assistant import DataAssistant
from great_expectations.rule_based_profiler.parameter_builder import (
    MetricMultiBatchParameterBuilder,
    ParameterBuilder,
)
from great_expectations.rule_based_profiler.rule import Rule
from great_expectations.rule_based_profiler.types import (
    DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME,
)
from great_expectations.rule_based_profiler.types.data_assistant_result import (
    VolumeDataAssistantResult,
)


# TODO: <Alex>ALEX Rename this "VolumeDataAssistant" to be more precise.</Alex>
class VolumeDataAssistant(DataAssistant):
    """
    VolumeDataAssistant provides exploration and validation of "Data Volume" aspects of specified data Batch objects.

    Self-Initializing Expectations relevant for assessing "Data Volume" include:
        - "expect_table_row_count_to_be_between";
        # TODO: <Alex>ALEX Implement Self-Initializing Capability for "expect_column_unique_value_count_to_be_between".</Alex>
        - "expect_column_unique_value_count_to_be_between";
        - Others in the future.
    """

    def __init__(
        self,
        name: str,
        batch_request: Union[BatchRequestBase, dict],
        data_context: BaseDataContext = None,
    ):
        self._result_class = VolumeDataAssistantResult

        super().__init__(
            name=name,
            batch_request=batch_request,
            data_context=data_context,
        )

    @property
    def expectation_kwargs_by_expectation_type(self) -> Dict[str, Dict[str, Any]]:
        return {
            "expect_table_row_count_to_be_between": {
                "auto": True,
                "profiler_config": None,
            },
        }

    @property
    def metrics_parameter_builders_by_domain_type(
        self,
    ) -> Dict[MetricDomainTypes, List[ParameterBuilder]]:
        table_row_count_metric_multi_batch_parameter_builder: MetricMultiBatchParameterBuilder = MetricMultiBatchParameterBuilder(
            name="table_row_count",
            metric_name="table.row_count",
            metric_domain_kwargs=DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME,
            metric_value_kwargs=None,
            enforce_numeric_metric=True,
            replace_nan_with_zero=True,
            reduce_scalar_metric=True,
            evaluation_parameter_builder_configs=None,
            json_serialize=True,
            batch_list=None,
            batch_request=None,
            data_context=None,
        )
        return {
            MetricDomainTypes.TABLE: [
                table_row_count_metric_multi_batch_parameter_builder,
            ],
        }

    @property
    def variables(self) -> Optional[Dict[str, Any]]:
        return None

    @property
    def rules(self) -> Optional[List[Rule]]:
        return None
