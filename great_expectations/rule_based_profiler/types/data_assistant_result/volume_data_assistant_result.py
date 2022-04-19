from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, KeysView, List, Optional

import altair as alt
import pandas as pd

from great_expectations.core import ExpectationConfiguration, ExpectationSuite
from great_expectations.core.util import convert_to_json_serializable
from great_expectations.execution_engine.execution_engine import MetricDomainTypes
from great_expectations.rule_based_profiler.data_assistant.visualization.plot import (
    display,
    get_attributed_metrics_by_domain,
    get_expect_domain_values_to_be_between_chart,
    get_line_chart,
)
from great_expectations.rule_based_profiler.parameter_builder import MetricValues
from great_expectations.rule_based_profiler.types import Domain, ParameterNode
from great_expectations.rule_based_profiler.types.data_assistant_result import (
    DataAssistantResult,
)


@dataclass
class VolumeDataAssistantResult(DataAssistantResult):
    """
    DataAssistantResult is an immutable "dataclass" object, designed to hold results of executing "data_assistant.run()"
    method.  Available properties ("metrics", "expectation_configurations", "expectation_suite", and configuration
    object (of type "RuleBasedProfilerConfig") of effective Rule-Based Profiler, which embodies given "DataAssistant".
    """

    profiler_config: Optional["RuleBasedProfilerConfig"] = None  # noqa: F821
    metrics_by_domain: Optional[Dict[Domain, Dict[str, Any]]] = None
    # Obtain "expectation_configurations" using "expectation_configurations = expectation_suite.expectations".
    # Obtain "meta/details" using "meta = expectation_suite.meta".
    expectation_suite: Optional[ExpectationSuite] = None
    execution_time: Optional[float] = None  # Execution time (in seconds).

    def plot(
        self,
        result: DataAssistantResult,
        prescriptive: bool = False,
    ) -> None:
        """
        VolumeDataAssistant-specific plots are defined with Altair and passed to "display()" for presentation.
        """
        metrics_by_domain: Dict[
            Domain, Dict[str, ParameterNode]
        ] = result.metrics_by_domain

        # TODO: <Alex>ALEX Currently, only one Domain key (with domain_type of MetricDomainTypes.TABLE) is utilized; enhancements may require additional Domain key(s) with different domain_type value(s) to be incorporated.</Alex>
        # noinspection PyTypeChecker
        attributed_metrics_by_domain: Dict[Domain, Dict[str, ParameterNode]] = dict(
            filter(
                lambda element: element[0].domain_type == MetricDomainTypes.TABLE,
                get_attributed_metrics_by_domain(
                    metrics_by_domain=metrics_by_domain
                ).items(),
            )
        )

        # TODO: <Alex>ALEX Currently, only one Domain key (with domain_type of MetricDomainTypes.TABLE) is utilized; enhancements may require additional Domain key(s) with different domain_type value(s) to be incorporated.</Alex>
        attributed_values_by_metric_name: Dict[str, ParameterNode] = list(
            attributed_metrics_by_domain.values()
        )[0]

        # Altair does not accept periods.
        # TODO: <Alex>ALEX Currently, only one Domain key (with domain_type of MetricDomainTypes.TABLE) is utilized; enhancements may require additional Domain key(s) with different domain_type value(s) to be incorporated.</Alex>
        metric_name: str = list(attributed_values_by_metric_name.keys())[0].replace(
            ".", "_"
        )
        x_axis_name: str = "batch"

        # available data types: https://altair-viz.github.io/user_guide/encoding.html#encoding-data-types
        x_axis_type: str = "ordinal"
        metric_type: str = "quantitative"

        batch_ids: KeysView[str]
        metric_values: MetricValues
        batch_ids, metric_values = list(attributed_values_by_metric_name.values())[
            0
        ].keys(), sum(list(attributed_values_by_metric_name.values())[0].values(), [])

        idx: int
        batch_numbers: List[int] = [idx + 1 for idx in range(len(batch_ids))]

        df: pd.DataFrame = pd.DataFrame(batch_numbers, columns=[x_axis_name])
        df["batch_id"] = batch_ids
        df[metric_name] = metric_values

        plot_impl: Callable
        charts: List[alt.Chart] = []

        expectation_configurations: List[
            ExpectationConfiguration
        ] = result.expectation_suite.expectations
        expectation_configuration: ExpectationConfiguration
        if prescriptive:
            for expectation_configuration in expectation_configurations:
                if (
                    expectation_configuration.expectation_type
                    == "expect_table_row_count_to_be_between"
                ):
                    df["min_value"] = expectation_configuration.kwargs["min_value"]
                    df["max_value"] = expectation_configuration.kwargs["max_value"]

            plot_impl = self._plot_prescriptive
        else:
            plot_impl = self._plot_descriptive

        table_row_count_chart: alt.Chart = plot_impl(
            df=df,
            metric=metric_name,
            metric_type=metric_type,
            x_axis_name=x_axis_name,
            x_axis_type=x_axis_type,
        )

        charts.append(table_row_count_chart)

        display(charts=charts)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json_dict(self) -> dict:
        return convert_to_json_serializable(data=self.to_dict())

    @staticmethod
    def _plot_descriptive(
        df: pd.DataFrame,
        metric: str,
        metric_type: str,
        x_axis_name: str,
        x_axis_type: str,
    ) -> alt.Chart:
        descriptive_chart: alt.Chart = get_line_chart(
            df=df,
            metric=metric,
            metric_type=metric_type,
            x_axis_name=x_axis_name,
            x_axis_type=x_axis_type,
        )
        return descriptive_chart

    @staticmethod
    def _plot_prescriptive(
        df: pd.DataFrame,
        metric: str,
        metric_type: str,
        x_axis_name: str,
        x_axis_type: str,
    ) -> alt.Chart:
        prescriptive_chart: alt.Chart = get_expect_domain_values_to_be_between_chart(
            df=df,
            metric=metric,
            metric_type=metric_type,
            x_axis_name=x_axis_name,
            x_axis_type=x_axis_type,
        )
        return prescriptive_chart
