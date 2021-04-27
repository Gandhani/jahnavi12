from abc import ABC, abstractmethod
from typing import List, Optional

from great_expectations.core.domain_types import MetricDomainTypes
from great_expectations.profiler.domain_builder.domain import Domain
from great_expectations.validator.validator import Validator


class DomainBuilder(ABC):
    """A DomainBuilder provides methods to get domains based on one or more batches of data.

    There is no default constructor for this class, and it may accept configuration as needed for the particular domain.
    """

    def get_domains(
        self,
        *,
        validator: Optional[Validator] = None,
        batch_ids: Optional[List[str]] = None,
        domain_type: Optional[MetricDomainTypes] = None,
        **kwargs
    ) -> List[Domain]:
        """
        Note: Please do not overwrite the public "get_domains()" method.  If a child class needs to check parameters,
        then please do so in its implementation of the (private) "_get_domains()" method, or in a utility method.
        """
        return self._get_domains(
            validator=validator, batch_ids=batch_ids, domain_type=domain_type, **kwargs
        )

    @abstractmethod
    def _get_domains(
        self,
        *,
        validator: Optional[Validator] = None,
        batch_ids: Optional[List[str]] = None,
        domain_type: Optional[MetricDomainTypes] = None,
        **kwargs
    ) -> List[Domain]:
        """_get_domains is the primary workhorse for the DomainBuilder"""
        pass
