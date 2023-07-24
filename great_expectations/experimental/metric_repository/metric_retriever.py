from __future__ import annotations

import abc
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from great_expectations import DataContext
    from great_expectations.datasource.fluent import BatchRequest
    from great_expectations.experimental.metric_repository.metrics import Metric


class MetricRetriever(abc.ABC):
    # TODO: Docstrings
    def __init__(self, context: DataContext):
        self._context = context

    @abc.abstractmethod
    def get_metrics(self, batch_request: BatchRequest) -> list[Metric]:
        raise NotImplementedError

    def _generate_metric_id(self) -> uuid.UUID:
        return uuid.uuid4()
