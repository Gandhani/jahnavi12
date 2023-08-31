from uuid import UUID

from great_expectations.data_context import CloudDataContext
from great_expectations.experimental.metric_repository.cloud_data_store import (
    CloudDataStore,
)
from great_expectations.experimental.metric_repository.metrics import (
    ColumnQuantileValuesMetric,
    MetricRun,
)

# Import and use fixtures defined in tests/datasource/fluent/conftest.py
from tests.datasource.fluent.conftest import (
    cloud_api_fake,  # noqa: F401  # used as a fixture
    cloud_details,  # noqa: F401  # used as a fixture
    empty_cloud_context_fluent,  # noqa: F401  # used as a fixture
)


class TestCloudDataStoreMetricRun:
    def test_cloud_data_store_build_payload_metric_run(
        self,
        empty_cloud_context_fluent: CloudDataContext,  # noqa: F811  # used as a fixture
    ):
        cloud_data_store = CloudDataStore(context=empty_cloud_context_fluent)

        static_id = UUID("b606af51-df84-49b5-b6a6-aef774b785ac")
        data_asset_id = UUID("4469ed3b-61d4-421f-9635-8339d2558b0f")
        metric_run = MetricRun(
            id=static_id,
            data_asset_id=data_asset_id,
            metrics=[
                ColumnQuantileValuesMetric(
                    id=static_id,
                    batch_id="batch_id",
                    metric_name="metric_name",
                    value=[0.25, 0.5, 0.75],
                    exception=None,
                    column="column",
                    quantiles=[0.25, 0.5, 0.75],
                    allow_relative_error=0.001,
                )
            ],
        )
        payload = cloud_data_store.build_payload(value=metric_run)

        assert payload == {
            "data": {
                "type": "metric-run",
                "attributes": {
                    "data_asset_id": UUID("4469ed3b-61d4-421f-9635-8339d2558b0f"),
                    "id": UUID("b606af51-df84-49b5-b6a6-aef774b785ac"),
                    "metrics": [
                        {
                            "allow_relative_error": 0.001,
                            "batch_id": "batch_id",
                            "column": "column",
                            "exception": None,
                            "id": UUID("b606af51-df84-49b5-b6a6-aef774b785ac"),
                            "metric_name": "metric_name",
                            "quantiles": [0.25, 0.5, 0.75],
                            "value": [0.25, 0.5, 0.75],
                        }
                    ],
                },
            }
        }

    def test_build_url_metric_run(
        self,
        empty_cloud_context_fluent: CloudDataContext,  # noqa: F811  # used as a fixture
    ):
        cloud_data_store = CloudDataStore(context=empty_cloud_context_fluent)
        static_id = UUID("b606af51-df84-49b5-b6a6-aef774b785ac")
        data_asset_id = UUID("4469ed3b-61d4-421f-9635-8339d2558b0f")
        metric_run = MetricRun(
            id=static_id,
            data_asset_id=data_asset_id,
            metrics=[
                ColumnQuantileValuesMetric(
                    id=static_id,
                    batch_id="batch_id",
                    metric_name="metric_name",
                    value=[0.25, 0.5, 0.75],
                    exception=None,
                    column="column",
                    quantiles=[0.25, 0.5, 0.75],
                    allow_relative_error=0.001,
                )
            ],
        )

        url = cloud_data_store.build_url(metric_run)
        expected_url = "https://app.greatexpectations.fake.io/organizations/12345678-1234-5678-1234-567812345678/metric-runs"
        assert url == expected_url
