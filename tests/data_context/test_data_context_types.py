import pytest

from great_expectations.data_context.types import DataAssetIdentifier
from great_expectations.data_context.types.metrics import MetricIdentifier
from great_expectations.datasource.types import BatchFingerprint


# noinspection PyPep8Naming
from great_expectations.exceptions import (
    InvalidTopLevelConfigKeyError,
    MissingTopLevelConfigKeyError,
)


def test_NamespaceAwareValidationMetric():
    metric_no_value = MetricIdentifier(
        data_asset_name=DataAssetIdentifier("my_dataset", "my_generator", "my_asset"),
        batch_fingerprint=BatchFingerprint(partition_id="20190101", fingerprint="74d1a208bcf41091d60c9d333a85b82f"),
        metric_name="column_value_count",
        metric_kwargs={
            "column": "Age"
        }
    )

    assert metric_no_value.to_tuple() == \
    ('ValidationMetric',
        DataAssetIdentifier(datasource='my_dataset', generator='my_generator', generator_asset='my_asset'),
        BatchFingerprint(partition_id="20190101", fingerprint="74d1a208bcf41091d60c9d333a85b82f"),
        'column_value_count', (('column', 'Age'),))

    metric_with_value = MetricIdentifier(
        data_asset_name=DataAssetIdentifier("my_dataset", "my_generator", "my_asset"),
        batch_fingerprint=BatchFingerprint(partition_id="20190101", fingerprint="74d1a208bcf41091d60c9d333a85b82f"),
        metric_name="column_value_count",
        metric_kwargs={
            "column": "Age"
        },
        metric_value=30
    )

    assert metric_with_value.to_tuple() == \
    ('ValidationMetric',
        DataAssetIdentifier(datasource='my_dataset', generator='my_generator', generator_asset='my_asset'),
        BatchFingerprint(partition_id="20190101", fingerprint="74d1a208bcf41091d60c9d333a85b82f"),
        'column_value_count', (('column', 'Age'),))

    with pytest.raises(InvalidTopLevelConfigKeyError):
        extra_key_metric = MetricIdentifier(
            data_asset_name=DataAssetIdentifier("my_dataset", "my_generator", "my_asset"),
            batch_fingerprint=BatchFingerprint(partition_id="20190101", fingerprint="74d1a208bcf41091d60c9d333a85b82f"),
            metric_name="column_value_count",
            metric_kwargs={
                "column": "Age"
            },
            metric_value=30,
            not_a_key="lemmein"
        )

    with pytest.raises(MissingTopLevelConfigKeyError):
        missing_key_metric = MetricIdentifier(
            data_asset_name=DataAssetIdentifier("my_dataset", "my_generator", "my_asset"),
            batch_fingerprint=BatchFingerprint(partition_id="20190101", fingerprint="74d1a208bcf41091d60c9d333a85b82f"),
            metric_kwargs={
                "column": "Age"
            },
            metric_value=30,
        )

