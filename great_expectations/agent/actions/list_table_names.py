from typing import TYPE_CHECKING, List

from great_expectations.agent.actions.agent_action import (
    ActionResult,
    AgentAction,
)
from great_expectations.agent.models import (
    CreatedResource,
    ListTableNamesEvent,
)
from great_expectations.compatibility.sqlalchemy import inspect
from great_expectations.core.http import create_session
from great_expectations.data_context.types.base import GXCloudConfig
from great_expectations.datasource.fluent import Datasource as FluentDatasource
from great_expectations.datasource.fluent import SQLDatasource
from great_expectations.exceptions import GXCloudError

if TYPE_CHECKING:
    from great_expectations.compatibility.sqlalchemy.engine import Inspector


class ListTableNamesAction(AgentAction[ListTableNamesEvent]):
    def run(self, event: ListTableNamesEvent, id: str) -> ActionResult:
        datasource_name: str = event.datasource_name
        datasource: FluentDatasource = self._context.get_datasource(
            datasource_name=datasource_name
        )
        if not isinstance(datasource, SQLDatasource):
            raise TypeError(
                f"This operation requires a SQL Datasource but got {type(datasource).__name__}."
            )

        inspector: Inspector = inspect(datasource.get_engine())
        table_names: List[str] = inspector.get_table_names()

        self._add_or_update_table_names_list(
            datasource_id=str(datasource.id), table_names=table_names
        )

        return ActionResult(
            id=id,
            type=event.type,
            created_resources=[],
        )

    def _add_or_update_table_names_list(
        self, datasource_id: str, table_names: list[str]
    ) -> str:
        cloud_config: GXCloudConfig = self._context._cloud_config

        session = create_session(access_token=cloud_config.access_token)
        response = session.patch(
            url=f"{cloud_config.gx_cloud_base_url}/organizations/"
            f"{cloud_config.gx_cloud_organization_id}/datasources/{datasource_id}",
            json={"table_names": table_names},
        )
        if response.status_code != 204:
            raise GXCloudError(
                message=f"Unable to update table_names for Datasource with id={datasource_id}.",
                response=response,
            )
