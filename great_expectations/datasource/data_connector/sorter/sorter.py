import json
import logging
from typing import Any, List

import great_expectations.exceptions as ge_exceptions
from great_expectations.core.batch import BatchDefinition

logger = logging.getLogger(__name__)


class Sorter:
    def __init__(self, name: str, orderby: str = "asc") -> None:
        self._name = name
        if orderby is None or orderby == "asc":
            reverse: bool = False
        elif orderby == "desc":
            reverse: bool = True
        else:
            raise ge_exceptions.SorterError(
                f'Illegal sort order "{orderby}" for attribute "{name}".'
            )
        self._reverse = reverse

    def get_sorted_batch_definitions(
        self, batch_definitions: List[BatchDefinition]
    ) -> List[BatchDefinition]:
        none_batches: List[int] = []
        value_batches: List[int] = []
        for idx, batch_definition in enumerate(batch_definitions):
            # if the batch_identifiers take the form of a nested dictionary, we need to extract the values of the
            # inner dict to check for special case sorting of None
            if isinstance(list(batch_definition.batch_identifiers.values())[0], dict):
                batch_identifier_values = dict(
                    batch_definition.batch_identifiers.values()
                ).values()
            else:
                batch_identifier_values = batch_definition.batch_identifiers.values()

            if None in batch_identifier_values or len(batch_identifier_values) == 0:
                none_batches.append(idx)
            else:
                value_batches.append(idx)

        none_batch_definitions: List[BatchDefinition] = [
            batch_definitions[idx] for idx in none_batches
        ]
        value_batch_definitions: List[BatchDefinition] = sorted(
            [batch_definitions[idx] for idx in value_batches],
            key=self.get_batch_key,
            reverse=self.reverse,
        )

        # the convention for ORDER BY in SQL is for NULL values to be first in the sort order for ascending
        # and last in the sort order for descending
        if self.reverse:
            return value_batch_definitions + none_batch_definitions
        return none_batch_definitions + value_batch_definitions

    def get_batch_key(self, batch_definition: BatchDefinition) -> Any:
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self._name

    @property
    def reverse(self) -> bool:
        return self._reverse

    def __repr__(self) -> str:
        doc_fields_dict: dict = {"name": self.name, "reverse": self.reverse}
        return json.dumps(doc_fields_dict, indent=2)
