from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.data_context import DataContext
from great_expectations.execution_engine.execution_engine import MetricDomainTypes
from great_expectations.rule_based_profiler.expectation_configuration_builder import (
    ConditionalExpectationConfigurationBuilder,
)
from great_expectations.rule_based_profiler.parameter_builder import (
    MetricMultiBatchParameterBuilder,
)
from great_expectations.rule_based_profiler.types import (
    Domain,
    ParameterContainer,
    get_parameter_value_by_fully_qualified_parameter_name,
)


def test_conditional_expectation_configuration_builder_alice(
    alice_columnar_table_single_batch_context,
):
    data_context: DataContext = alice_columnar_table_single_batch_context

    batch_request: dict = {
        "datasource_name": "alice_columnar_table_single_batch_datasource",
        "data_connector_name": "alice_columnar_table_single_batch_data_connector",
        "data_asset_name": "alice_columnar_table_single_batch_data_asset",
    }

    metric_domain_kwargs = {"column": "user_id"}

    min_user_id_parameter: MetricMultiBatchParameterBuilder = (
        MetricMultiBatchParameterBuilder(
            name="my_min_user_id",
            metric_name="column.min",
            metric_domain_kwargs=metric_domain_kwargs,
            data_context=data_context,
            batch_request=batch_request,
        )
    )

    parameter_container: ParameterContainer = ParameterContainer(parameter_nodes=None)
    domain: Domain = Domain(
        domain_type=MetricDomainTypes.COLUMN, domain_kwargs=metric_domain_kwargs
    )

    min_user_id_parameter._build_parameters(
        parameter_container=parameter_container, domain=domain
    )

    fully_qualified_parameter_name_for_value: str = "$parameter.my_min_user_id"
    value = get_parameter_value_by_fully_qualified_parameter_name(
        fully_qualified_parameter_name=fully_qualified_parameter_name_for_value,
        domain=domain,
        parameters={domain.id: parameter_container},
    )

    condition = None
    max_user_id = 999999999999

    conditional_expectation_configuration_builder = (
        ConditionalExpectationConfigurationBuilder(
            expectation_type="expect_column_values_to_be_between",
            condition=condition,
            min_value=value.value[0],
            max_value=max_user_id,
        )
    )

    expectation_configuration: ExpectationConfiguration = (
        conditional_expectation_configuration_builder._build_expectation_configuration(
            domain=domain, parameters={domain.id: parameter_container}
        )
    )

    assert expectation_configuration.kwargs["min_value"] == 397433
