from typing import Any, Dict, List, Optional, Union

import great_expectations.exceptions as ge_exceptions
from great_expectations.core import IDDict
from great_expectations.execution_engine.execution_engine import MetricDomainTypes
from great_expectations.profiler.parameter_builder.parameter_tree_container_node import (
    ParameterTreeContainerNode,
)

DOMAIN_KWARGS_PARAMETER_NAME: str = "domain_kwargs"
DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME: str = (
    f"$domain.{DOMAIN_KWARGS_PARAMETER_NAME}"
)
VARIABLES_KEY: str = "$variables."


class RuleState:
    """Manages state for ProfilerRule objects. Keeps track of rule domain, rule parameters,
    and any other necessary variables for validating the rule."""

    # TODO: <Alex>ALEX -- Add type hints; what are the types?</Alex>
    def __init__(
        self,
        active_domain: Optional[
            Dict[str, Union[str, MetricDomainTypes, Dict[str, Any]]]
        ] = None,
        domains: Optional[
            List[Dict[str, Union[str, MetricDomainTypes, Dict[str, Any]]]]
        ] = None,
        # TODO: <Alex>ALEX -- what is the structure of this "parameters" argument?</Alex>
        parameters: Optional[Dict[str, ParameterTreeContainerNode]] = None,
        variables: Optional[ParameterTreeContainerNode] = None,
    ):
        self._active_domain = active_domain
        if domains is None:
            domains = {}
        self._domains = domains
        if parameters is None:
            parameters = {}
        self._parameters = parameters
        if variables is None:
            variables = ParameterTreeContainerNode(parameters={}, details=None)
        self._variables = variables

    @property
    def parameters(self) -> Dict[str, ParameterTreeContainerNode]:
        return self._parameters

    @property
    def domains(self) -> List[Dict[str, Union[str, MetricDomainTypes, Dict[str, Any]]]]:
        return self._domains

    @domains.setter
    def domains(
        self, domains: List[Dict[str, Union[str, MetricDomainTypes, Dict[str, Any]]]]
    ):
        self._domains = domains

    @property
    def active_domain(self) -> Dict[str, Union[str, MetricDomainTypes, Dict[str, Any]]]:
        return self._active_domain

    @active_domain.setter
    def active_domain(
        self, active_domain: Dict[str, Union[str, MetricDomainTypes, Dict[str, Any]]]
    ):
        self._active_domain = active_domain

    @property
    def active_domain_id(self) -> str:
        """
        Getter for the id of the rule domain
        :return: the id of the rule domain
        """
        return IDDict(self.active_domain).to_id()

    # TODO: <Alex>ALEX -- what is the return type?</Alex>
    @property
    def variables(self) -> ParameterTreeContainerNode:
        """
        Getter for rule_state variables
        :return: variables necessary for validating rule
        """
        return self._variables

    def get_parameter_value(self, fully_qualified_parameter_name: str) -> Any:
        """
        Get the parameter value from the current rule state using the fully-qualified parameter name.
        A fully-qualified parameter name must be dot-delimited, and may start either with the key "domain" or the name
        of a parameter.
        Args
            :param fully_qualified_parameter_name: str -- A string key starting with $ and corresponding to internal
            state arguments (e.g.: domain kwargs)
        :return: requested value
        """
        if not fully_qualified_parameter_name.startswith("$"):
            raise ge_exceptions.ProfilerExecutionError(
                message=f'Unable to get value for parameter name "{fully_qualified_parameter_name}" -- values must start with $.'
            )

        if (
            fully_qualified_parameter_name
            == DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME
        ):
            return self.active_domain[DOMAIN_KWARGS_PARAMETER_NAME]

        fully_qualified_parameter_name_references_variable: bool = False
        if fully_qualified_parameter_name.startswith(VARIABLES_KEY):
            fully_qualified_parameter_name = fully_qualified_parameter_name[
                len(VARIABLES_KEY) :
            ]
            fully_qualified_parameter_name_references_variable = True
        else:
            fully_qualified_parameter_name = fully_qualified_parameter_name[1:]

        parameter_name_hierarchy_list: List[str] = fully_qualified_parameter_name.split(
            "."
        )

        node: ParameterTreeContainerNode
        if fully_qualified_parameter_name_references_variable:
            node = self.variables
        else:
            node = self.parameters.get(
                self.active_domain_id,
                ParameterTreeContainerNode(parameters={}, details=None),
            )

        parameter_name_at_level_in_hierarchy: Optional[str] = None
        parameter_value: Optional[Any] = None
        try:
            for parameter_name_at_level_in_hierarchy in parameter_name_hierarchy_list:
                if node.descendants is None:
                    parameter_value = node.parameters[
                        parameter_name_at_level_in_hierarchy
                    ]
                else:
                    node = node.descendants[parameter_name_at_level_in_hierarchy]
        except KeyError:
            raise ge_exceptions.ProfilerExecutionError(
                message=f'Unable to find value for parameter name "{fully_qualified_parameter_name}": key "{parameter_name_at_level_in_hierarchy}" was missing.'
            )

        return parameter_value
