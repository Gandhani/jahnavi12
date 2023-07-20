from __future__ import annotations

import uuid
from abc import ABC
from typing import Any, Sequence

import pydantic
from pydantic import BaseModel, Field


class MetricRepositoryBaseModel(BaseModel, ABC):
    """Base class for all MetricRepository related models."""

    class Config:
        extra = pydantic.Extra.forbid


class Value(MetricRepositoryBaseModel):
    value: Any  # TODO: Better than Any


class Metric(MetricRepositoryBaseModel, ABC):
    id: uuid.UUID = Field(description="Metric id")
    run_id: uuid.UUID = Field(description="Run id")
    # TODO: reimplement batch param
    # batch: Batch = Field(description="Batch")
    metric_name: str = Field(description="Metric name")
    metric_domain_kwargs: dict = Field(description="Metric domain kwargs")
    metric_value_kwargs: dict = Field(description="Metric value kwargs")
    value: Value = Field(description="Metric value")
    details: dict = Field(description="Metric details")


class TableMetric(Metric):
    pass


class ColumnMetric(Metric):
    column: str = Field(description="Column name")


# TODO: Add ColumnPairMetric, MultiColumnMetric


class Metrics(MetricRepositoryBaseModel):
    """Collection of Metric objects."""

    id: uuid.UUID = Field(description="Run id")
    # created_at, created_by filled in by the backend.
    metrics: Sequence[Metric]
