from abc import ABC
from typing import List, Optional

import great_expectations.exceptions as ge_exceptions
from great_expectations import DataContext
from great_expectations.core.batch import BatchRequest
from great_expectations.profiler.domain_builder.domain import Domain
from great_expectations.profiler.domain_builder.util import get_batch_ids
from great_expectations.profiler.parameter_builder.parameter_builder import (
    ParameterBuilder,
)
from great_expectations.validator.validator import Validator


# TODO: <Alex>ALEX -- If ParameterBuilder already extends ABC, why does this class need to do the same?</Alex>
class MultiBatchParameterBuilder(ParameterBuilder, ABC):
    """
    Defines the abstract MultiBatchParameterBuilder class

    MultiBatchParameterBuilder checks that there are multiple batch ids passed to build_parameters,
    and uses a configured batch_request parameter to obtain them if they are not.
    """

    def __init__(
        self,
        name: str,
        validator: Validator,
        domain: Domain,
        batch_request: BatchRequest,
        rule_variables: Optional[ParameterContainer] = None,
        rule_domain_parameters: Optional[Dict[str, ParameterContainer]] = None,
        data_context: Optional[DataContext] = None,
    ):
        if data_context is None:
            raise ge_exceptions.ProfilerExecutionError(
                message=f"MultiBatchParameterBuilder requires a data_context, but none was provided."
            )

        super().__init__(
            name=name,
            validator=validator,
            domain=domain,
            rule_variables=rule_variables,
            rule_domain_parameters=rule_domain_parameters,
            data_context=data_context,
        )

        self._batch_request = batch_request
        self._batch_ids = get_batch_ids(
            data_context=self.data_context, batch_request=self._batch_request
        )

    @property
    def batch_ids(self) -> List[str]:
        return self._batch_ids
