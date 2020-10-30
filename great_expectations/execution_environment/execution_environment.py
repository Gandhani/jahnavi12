# -*- coding: utf-8 -*-

import copy
import logging
from typing import Union, List, Dict, Callable, Any, Optional

from great_expectations.data_context.types.base import (
    DataConnectorConfig,
    dataConnectorConfigSchema
)
from great_expectations.data_context.util import instantiate_class_from_config
from ruamel.yaml.comments import CommentedMap
from great_expectations.execution_environment.data_connector.data_connector import DataConnector
from great_expectations.execution_environment.data_connector.pipeline_data_connector import PipelineDataConnector
from great_expectations.execution_environment.data_connector.partitioner.partition import Partition
from great_expectations.core.id_dict import (
    PartitionRequest,
    PartitionDefinition,
    BatchSpec
)
from great_expectations.core.batch import (
    Batch,
    BatchRequest,
    BatchDefinition
)

import great_expectations.exceptions as ge_exceptions

logger = logging.getLogger(__name__)


class ExecutionEnvironment(object):
    """
    An ExecutionEnvironment is the glue between an ExecutionEngine and a DataConnector.
    """
    recognized_batch_parameters: set = {"limit"}

    def __init__(
        self,
        name: str,
        execution_engine=None,
        data_connectors=None,
        data_context_root_directory: str = None,
    ):
        """
        Build a new ExecutionEnvironment.

        Args:
            name: the name for the datasource
            execution_engine (ClassConfig): the type of compute engine to produce
            data_connectors: DataConnectors to add to the datasource
        """
        self._name = name
        self._execution_engine = instantiate_class_from_config(
            config=execution_engine,
            runtime_environment={},
            config_defaults={
                "module_name": "great_expectations.execution_engine"
            }
        )
        self._execution_environment_config = {
            "execution_engine": execution_engine
        }

        if data_connectors is None:
            data_connectors = {}
        self._execution_environment_config["data_connectors"] = data_connectors

        self._data_connectors_cache = {}

        self._data_context_root_directory = data_context_root_directory

        # if data_connectors is None:
        #     data_connectors = {}
        self._data_connectors_cache = {}
        self._build_data_connectors()

    def get_batch_from_batch_definition(
        self,
        batch_definition: BatchDefinition,
        in_memory_dataset: Any = None,
    ) -> Batch:
        """
        Note: this method should *not* be used when getting a Batch from a BatchRequest, since it does not capture BatchRequest metadata.
        """
        if not isinstance(in_memory_dataset, type(None)):
            # TODO: <Alex>Abe: Are the comments below still pertinent?  Or can they be deleted?</Alex>
            # NOTE Abe 20201014: Maybe do more careful type checking here?
            # Seems like we should verify that in_memory_dataset is compatible with the execution_engine...?
            batch_data = in_memory_dataset
            batch_spec, batch_markers = None, None
        else:
            data_connector: DataConnector = self.get_data_connector(
                name=batch_definition.data_connector_name
            )
            batch_data, batch_spec, batch_markers = data_connector.get_batch_data_and_metadata_from_batch_definition(
                batch_definition=batch_definition
            )
        new_batch: Batch = Batch(
            data=batch_data,
            batch_request=None,
            batch_definition=batch_definition,
            batch_spec=batch_spec,
            batch_markers=batch_markers,
        )
        return new_batch

    def get_batch_list_from_batch_request(
        self,
        batch_request: BatchRequest
    ) -> List[Batch]:
        data_connector: DataConnector

        if batch_request.in_memory_dataset is not None:
            partition_request: dict = batch_request.partition_request
            partition_definition: Optional[PartitionDefinition]
            if partition_request is None:
                partition_definition = None
            else:
                partition_definition = PartitionDefinition(partition_request)
            data_connector_name: str = batch_request.data_connector_name
            data_connector = PipelineDataConnector(
                name=data_connector_name,
                execution_environment_name=batch_request.execution_environment_name,
                execution_engine=self.execution_engine,
                data_asset_name=batch_request.data_asset_name,
                batch_data=batch_request.in_memory_dataset,
                partition_definition=partition_definition
            )
            self._data_connectors_cache[data_connector_name] = data_connector
        else:
            data_connector: DataConnector = self.get_data_connector(
                name=batch_request.data_connector_name
            )

        batch_definition_list: List[BatchDefinition] = data_connector.get_batch_definition_list_from_batch_request(
            batch_request=batch_request
        )

        batches: List[Batch] = []
        for batch_definition in batch_definition_list:
            batch_data, batch_spec, batch_markers = data_connector.get_batch_data_and_metadata_from_batch_definition(
                batch_definition=batch_definition
            )

            new_batch: Batch = Batch(
                data=batch_data,
                batch_request=batch_request,
                batch_definition=batch_definition,
                batch_spec=batch_spec,
                batch_markers=batch_markers,
            )
            batches.append(new_batch)

        return batches

    @property
    def name(self):
        """
        Property for datasource name
        """
        return self._name

    @property
    def execution_engine(self):
        return self._execution_engine

    @property
    def config(self):
        return copy.deepcopy(self._execution_environment_config)

    def _build_data_connectors(self):
        """
        Build DataConnector objects from the ExecutionEnvironment configuration.

        Returns:
            None
        """
        if "data_connectors" in self._execution_environment_config:
            for data_connector in self._execution_environment_config["data_connectors"].keys():
                self.get_data_connector(name=data_connector)

    # TODO Abe 10/6/2020: Should this be an internal method?
    def get_data_connector(self, name: str) -> DataConnector:
        """Get the (named) DataConnector from an ExecutionEnvironment)

        Args:
            name (str): name of DataConnector
            runtime_environment (dict):

        Returns:
            DataConnector (DataConnector)
        """
        data_connector: DataConnector
        if name in self._data_connectors_cache:
            return self._data_connectors_cache[name]
        elif (
            "data_connectors" in self._execution_environment_config
            and name in self._execution_environment_config["data_connectors"]
        ):
            data_connector_config: dict = copy.deepcopy(
                self._execution_environment_config["data_connectors"][name]
            )
        else:
            raise ge_exceptions.DataConnectorError(
                f'Unable to load data connector "{name}" -- no configuration found or invalid configuration.'
            )
        data_connector: DataConnector = self._build_data_connector_from_config(
            name=name, config=data_connector_config
        )
        self._data_connectors_cache[name] = data_connector
        return data_connector

    def _build_data_connector_from_config(
        self,
        name: str,
        config: dict,
    ) -> DataConnector:
        """Build a DataConnector using the provided configuration and return the newly-built DataConnector."""
        data_connector: DataConnector = instantiate_class_from_config(
            config=config,
            runtime_environment={
                "name": name,
                "execution_environment_name": self.name,
                "data_context_root_directory": self._data_context_root_directory,
                "execution_engine": self.execution_engine,
            },
            config_defaults={
                "module_name": "great_expectations.execution_environment.data_connector"
            },
        )

        return data_connector

    # TODO Abe 10/6/2020: Should this be an internal method?<Alex>Pros/cons for either choice exist; happy to discuss.</Alex>
    def list_data_connectors(self) -> List[dict]:
        """List currently-configured DataConnector for this ExecutionEnvironment.

        Returns:
            List(dict): each dictionary includes "name" and "type" keys
        """
        data_connectors: List[dict] = []

        if "data_connectors" in self._execution_environment_config:
            for key, value in self._execution_environment_config["data_connectors"].items():
                data_connectors.append({"name": key, "class_name": value["class_name"]})

        return data_connectors

    def get_available_data_asset_names(self, data_connector_names: Optional[Union[list, str]] = None) -> dict:
        """
        Returns a dictionary of data_asset_names that the specified data
        connector can provide. Note that some data_connectors may not be
        capable of describing specific named data assets, and some (such as
        files_data_connectors) require the user to configure
        data asset names.

        Args:
            data_connector_names: the DataConnector for which to get available data asset names.

        Returns:
            dictionary consisting of sets of data assets available for the specified data connectors:
            ::

                {
                  data_connector_name: {
                    names: [ (data_asset_1, data_asset_1_type), (data_asset_2, data_asset_2_type) ... ]
                  }
                  ...
                }
        """
        available_data_asset_names: dict = {}
        if data_connector_names is None:
            data_connector_names = self._data_connectors_cache.keys()
        elif isinstance(data_connector_names, str):
            data_connector_names = [data_connector_names]

        for data_connector_name in data_connector_names:
            data_connector: DataConnector = self.get_data_connector(name=data_connector_name)
            available_data_asset_names[data_connector_name] = data_connector.get_available_data_asset_names()

        return available_data_asset_names

    def get_available_batch_definitions(
        self,
        batch_request: BatchRequest
        # data_connector_name: str,
        # data_asset_name: str = None,
        # partition_request: Union[Dict[str, Union[int, list, tuple, slice, str, Dict, Callable, None]], None] = None,
        # in_memory_dataset: Any = None,
        # runtime_parameters: Union[dict, None] = None,
        # repartition: bool = False
    ) -> List[BatchDefinition]:
        if batch_request.execution_environment_name != self.name:
            raise ValueError(
                f"""execution_environment_name {batch_request.execution_environment_name} does not match name
{self.name}.
                """
            )

        data_connector: DataConnector = self.get_data_connector(
            name=batch_request.data_connector_name
        )
        batch_definition_list = data_connector.get_batch_definition_list_from_batch_request(
            batch_request=batch_request
        )
        return batch_definition_list

    def self_check(self, pretty_print=True, max_examples=3):
        return_object = {
            "execution_engine": {
                "class_name" : self.execution_engine.__class__.__name__,
            }
        }

        if pretty_print:
            print(f"Execution engine: {self.execution_engine.__class__.__name__}")

        if pretty_print:
            print(f"Data connectors:")

        data_connector_list = self.list_data_connectors()
        data_connector_list.sort()
        return_object["data_connectors"] = {
            "count": len(data_connector_list)
        }

        for data_connector in data_connector_list:
            data_connector_obj: DataConnector = self.get_data_connector(name=data_connector["name"])
            data_connector_return_obj = data_connector_obj.self_check(
                pretty_print=pretty_print,
                max_examples=max_examples
            )
            return_object["data_connectors"][data_connector["name"]] = data_connector_return_obj

        return return_object
