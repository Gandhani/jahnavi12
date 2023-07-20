from great_expectations.agent.actions import ActionResult, AgentAction
from great_expectations.agent.models import (
    CreatedResource,
    RunBatchInspectorEvent,
)
from great_expectations.experimental.metric_repository.batch_inspector import (
    BatchInspector,
)
from great_expectations.experimental.metric_repository.cloud_data_store import (
    CloudDataStore,
)
from great_expectations.experimental.metric_repository.metric_repository import (
    MetricRepository,
)


class RunBatchInspectorAction(AgentAction[RunBatchInspectorEvent]):
    def run(self, event: RunBatchInspectorEvent, id: str) -> ActionResult:
        datasource = self._context.get_datasource(event.datasource_name)
        data_asset = datasource.get_asset(event.data_asset_name)
        batch_request = data_asset.build_batch_request()

        batch_inspector = BatchInspector(self._context)
        metrics = batch_inspector.get_column_descriptive_metrics(batch_request)

        cloud_data_store = CloudDataStore(self._context)
        column_descriptive_metrics_repository = MetricRepository(
            data_store=cloud_data_store
        )
        column_descriptive_metrics_repository.create(metrics)

        # TODO: Reconcile this with storing multiple metrics (eg metrics.id):
        return ActionResult(
            id=id,
            type=event.type,
            created_resources=[
                CreatedResource(
                    resource_id="TODO_SOME_ID_probably_run_id", type="Metrics"
                ),
            ],
        )
