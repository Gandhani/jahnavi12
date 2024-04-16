import copy
import os
from typing import Dict, Final, Optional
from unittest import mock

import pytest

from great_expectations.data_context import get_context
from great_expectations.data_context.data_context.serializable_data_context import (
    SerializableDataContext,
)
from great_expectations.data_context.types.base import (
    BaseStoreBackendDefaults,
    DatabaseStoreBackendDefaults,
    DataContextConfig,
    DataContextConfigDefaults,
    DataContextConfigSchema,
    DatasourceConfig,
    FilesystemStoreBackendDefaults,
    GCSStoreBackendDefaults,
    InMemoryStoreBackendDefaults,
    S3StoreBackendDefaults,
)
from great_expectations.util import filter_properties_dict

"""
What does this test and why?

This file will hold various tests to ensure that the UI functions as expected when creating a DataContextConfig object. It will ensure that the appropriate defaults are used, including when the store_backend_defaults parameter is set.
"""  # noqa: E501

_DEFAULT_CONFIG_VERSION: Final[float] = float(
    DataContextConfigDefaults.DEFAULT_CONFIG_VERSION.value
)


@pytest.fixture(scope="function")
def construct_data_context_config():
    """
    Construct a DataContextConfig fixture given the modifications in the input parameters
    Returns:
        Dictionary representation of a DataContextConfig to compare in tests
    """

    def _construct_data_context_config(
        data_context_id: str,
        datasources: Dict,
        config_version: float = _DEFAULT_CONFIG_VERSION,
        expectations_store_name: str = DataContextConfigDefaults.DEFAULT_EXPECTATIONS_STORE_NAME.value,  # noqa: E501
        validation_results_store_name: str = DataContextConfigDefaults.DEFAULT_VALIDATIONS_STORE_NAME.value,  # noqa: E501
        suite_parameter_store_name: str = DataContextConfigDefaults.DEFAULT_SUITE_PARAMETER_STORE_NAME.value,  # noqa: E501
        checkpoint_store_name: str = DataContextConfigDefaults.DEFAULT_CHECKPOINT_STORE_NAME.value,
        profiler_store_name: str = DataContextConfigDefaults.DEFAULT_PROFILER_STORE_NAME.value,
        plugins_directory: Optional[str] = None,
        stores: Optional[Dict] = None,
        validation_operators: Optional[Dict] = None,
        data_docs_sites: Optional[Dict] = None,
    ):
        if stores is None:
            stores = copy.deepcopy(DataContextConfigDefaults.DEFAULT_STORES.value)
        if data_docs_sites is None:
            data_docs_sites = copy.deepcopy(DataContextConfigDefaults.DEFAULT_DATA_DOCS_SITES.value)

        return {
            "config_version": config_version,
            "datasources": datasources,
            "expectations_store_name": expectations_store_name,
            "validation_results_store_name": validation_results_store_name,
            "suite_parameter_store_name": suite_parameter_store_name,
            "checkpoint_store_name": checkpoint_store_name,
            "profiler_store_name": profiler_store_name,
            "plugins_directory": plugins_directory,
            "validation_operators": validation_operators,
            "stores": stores,
            "data_docs_sites": data_docs_sites,
            "config_variables_file_path": None,
            "anonymous_usage_statistics": {
                "data_context_id": data_context_id,
                "enabled": True,
            },
            "include_rendered_content": {
                "globally": False,
                "expectation_suite": False,
                "expectation_validation_result": False,
            },
        }

    return _construct_data_context_config


@pytest.fixture()
def default_pandas_datasource_config():
    return {
        "my_pandas_datasource": {
            "batch_kwargs_generators": {
                "subdir_reader": {
                    "base_directory": "../data/",
                    "class_name": "SubdirReaderBatchKwargsGenerator",
                }
            },
            "class_name": "PandasDatasource",
            "data_asset_type": {
                "class_name": "PandasDataset",
                "module_name": "great_expectations.dataset",
            },
            "module_name": "great_expectations.datasource",
        }
    }


@pytest.mark.unit
def test_DataContextConfig_with_BaseStoreBackendDefaults_and_simple_defaults(
    construct_data_context_config, default_pandas_datasource_config
):
    """
    What does this test and why?
    Ensure that a very simple DataContextConfig setup with many defaults is created accurately
    and produces a valid DataContextConfig
    """

    store_backend_defaults = BaseStoreBackendDefaults()
    data_context_config = DataContextConfig(
        datasources={
            "my_pandas_datasource": DatasourceConfig(
                class_name="PandasDatasource",
                batch_kwargs_generators={
                    "subdir_reader": {
                        "class_name": "SubdirReaderBatchKwargsGenerator",
                        "base_directory": "../data/",
                    }
                },
            )
        },
        store_backend_defaults=store_backend_defaults,
        checkpoint_store_name=store_backend_defaults.checkpoint_store_name,
        profiler_store_name=store_backend_defaults.profiler_store_name,
    )

    desired_config = construct_data_context_config(
        data_context_id=data_context_config.anonymous_usage_statistics.data_context_id,
        datasources=default_pandas_datasource_config,
    )

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )


@pytest.mark.unit
def test_DataContextConfig_with_S3StoreBackendDefaults(
    construct_data_context_config, default_pandas_datasource_config
):
    """
    What does this test and why?
    Make sure that using S3StoreBackendDefaults as the store_backend_defaults applies appropriate
    defaults, including default_bucket_name getting propagated to all stores.
    """

    store_backend_defaults = S3StoreBackendDefaults(default_bucket_name="my_default_bucket")
    data_context_config = DataContextConfig(
        datasources={
            "my_pandas_datasource": DatasourceConfig(
                class_name="PandasDatasource",
                batch_kwargs_generators={
                    "subdir_reader": {
                        "class_name": "SubdirReaderBatchKwargsGenerator",
                        "base_directory": "../data/",
                    }
                },
            )
        },
        store_backend_defaults=store_backend_defaults,
    )

    # Create desired config
    desired_stores_config = {
        "suite_parameter_store": {"class_name": "SuiteParameterStore"},
        "expectations_S3_store": {
            "class_name": "ExpectationsStore",
            "store_backend": {
                "bucket": "my_default_bucket",
                "class_name": "TupleS3StoreBackend",
                "prefix": "expectations",
            },
        },
        "validations_S3_store": {
            "class_name": "ValidationsStore",
            "store_backend": {
                "bucket": "my_default_bucket",
                "class_name": "TupleS3StoreBackend",
                "prefix": "validations",
            },
        },
        "validation_definition_store": {
            "class_name": "ValidationDefinitionStore",
            "store_backend": {
                "bucket": "my_default_bucket",
                "class_name": "TupleS3StoreBackend",
                "prefix": "validation_definitions",
            },
        },
        "checkpoint_S3_store": {
            "class_name": "CheckpointStore",
            "store_backend": {
                "bucket": "my_default_bucket",
                "class_name": "TupleS3StoreBackend",
                "prefix": "checkpoints",
            },
        },
        "profiler_S3_store": {
            "class_name": "ProfilerStore",
            "store_backend": {
                "bucket": "my_default_bucket",
                "class_name": "TupleS3StoreBackend",
                "prefix": "profilers",
            },
        },
    }
    desired_data_docs_sites_config = {
        "s3_site": {
            "class_name": "SiteBuilder",
            "show_how_to_buttons": True,
            "site_index_builder": {
                "class_name": "DefaultSiteIndexBuilder",
            },
            "store_backend": {
                "bucket": "my_default_bucket",
                "class_name": "TupleS3StoreBackend",
                "prefix": "data_docs",
            },
        }
    }

    desired_config = construct_data_context_config(
        data_context_id=data_context_config.anonymous_usage_statistics.data_context_id,
        datasources=default_pandas_datasource_config,
        expectations_store_name="expectations_S3_store",
        validation_results_store_name="validations_S3_store",
        suite_parameter_store_name=DataContextConfigDefaults.DEFAULT_SUITE_PARAMETER_STORE_NAME.value,
        checkpoint_store_name="checkpoint_S3_store",
        profiler_store_name="profiler_S3_store",
        stores=desired_stores_config,
        data_docs_sites=desired_data_docs_sites_config,
    )

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )


@pytest.mark.unit
def test_DataContextConfig_with_S3StoreBackendDefaults_using_all_parameters(
    construct_data_context_config, default_pandas_datasource_config
):
    """
    What does this test and why?
    Make sure that S3StoreBackendDefaults parameters are handled appropriately
    E.g. Make sure that default_bucket_name is ignored if individual bucket names are passed
    """

    store_backend_defaults = S3StoreBackendDefaults(
        default_bucket_name="custom_default_bucket_name",
        expectations_store_bucket_name="custom_expectations_store_bucket_name",
        validation_results_store_bucket_name="custom_validation_results_store_bucket_name",
        data_docs_bucket_name="custom_data_docs_store_bucket_name",
        checkpoint_store_bucket_name="custom_checkpoint_store_bucket_name",
        profiler_store_bucket_name="custom_profiler_store_bucket_name",
        expectations_store_prefix="custom_expectations_store_prefix",
        validation_results_store_prefix="custom_validation_results_store_prefix",
        data_docs_prefix="custom_data_docs_prefix",
        checkpoint_store_prefix="custom_checkpoint_store_prefix",
        profiler_store_prefix="custom_profiler_store_prefix",
        expectations_store_name="custom_expectations_S3_store_name",
        validation_results_store_name="custom_validations_S3_store_name",
        suite_parameter_store_name="custom_suite_parameter_store_name",
        checkpoint_store_name="custom_checkpoint_S3_store_name",
        profiler_store_name="custom_profiler_S3_store_name",
    )
    data_context_config = DataContextConfig(
        datasources={
            "my_pandas_datasource": DatasourceConfig(
                class_name="PandasDatasource",
                module_name="great_expectations.datasource",
                data_asset_type={
                    "module_name": "great_expectations.dataset",
                    "class_name": "PandasDataset",
                },
                batch_kwargs_generators={
                    "subdir_reader": {
                        "class_name": "SubdirReaderBatchKwargsGenerator",
                        "base_directory": "../data/",
                    }
                },
            )
        },
        store_backend_defaults=store_backend_defaults,
    )

    # Create desired config
    desired_stores_config = {
        "custom_suite_parameter_store_name": {"class_name": "SuiteParameterStore"},
        "custom_expectations_S3_store_name": {
            "class_name": "ExpectationsStore",
            "store_backend": {
                "bucket": "custom_expectations_store_bucket_name",
                "class_name": "TupleS3StoreBackend",
                "prefix": "custom_expectations_store_prefix",
            },
        },
        "custom_validations_S3_store_name": {
            "class_name": "ValidationsStore",
            "store_backend": {
                "bucket": "custom_validation_results_store_bucket_name",
                "class_name": "TupleS3StoreBackend",
                "prefix": "custom_validation_results_store_prefix",
            },
        },
        "validation_definition_store": {
            "class_name": "ValidationDefinitionStore",
            "store_backend": {
                "bucket": "custom_default_bucket_name",
                "class_name": "TupleS3StoreBackend",
                "prefix": "validation_definitions",
            },
        },
        "custom_checkpoint_S3_store_name": {
            "class_name": "CheckpointStore",
            "store_backend": {
                "bucket": "custom_checkpoint_store_bucket_name",
                "class_name": "TupleS3StoreBackend",
                "prefix": "custom_checkpoint_store_prefix",
            },
        },
        "custom_profiler_S3_store_name": {
            "class_name": "ProfilerStore",
            "store_backend": {
                "bucket": "custom_profiler_store_bucket_name",
                "class_name": "TupleS3StoreBackend",
                "prefix": "custom_profiler_store_prefix",
            },
        },
    }
    desired_data_docs_sites_config = {
        "s3_site": {
            "class_name": "SiteBuilder",
            "show_how_to_buttons": True,
            "site_index_builder": {
                "class_name": "DefaultSiteIndexBuilder",
            },
            "store_backend": {
                "bucket": "custom_data_docs_store_bucket_name",
                "class_name": "TupleS3StoreBackend",
                "prefix": "custom_data_docs_prefix",
            },
        }
    }

    desired_config = construct_data_context_config(
        data_context_id=data_context_config.anonymous_usage_statistics.data_context_id,
        datasources=default_pandas_datasource_config,
        expectations_store_name="custom_expectations_S3_store_name",
        validation_results_store_name="custom_validations_S3_store_name",
        suite_parameter_store_name="custom_suite_parameter_store_name",
        checkpoint_store_name="custom_checkpoint_S3_store_name",
        profiler_store_name="custom_profiler_S3_store_name",
        stores=desired_stores_config,
        data_docs_sites=desired_data_docs_sites_config,
    )

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )


@pytest.mark.unit
def test_DataContextConfig_with_FilesystemStoreBackendDefaults_and_simple_defaults(
    construct_data_context_config, default_pandas_datasource_config
):
    """
    What does this test and why?
    Ensure that a very simple DataContextConfig setup using FilesystemStoreBackendDefaults is created accurately
    This test sets the root_dir parameter
    """  # noqa: E501

    test_root_directory = "test_root_dir"

    store_backend_defaults = FilesystemStoreBackendDefaults(root_directory=test_root_directory)
    data_context_config = DataContextConfig(
        datasources={
            "my_pandas_datasource": DatasourceConfig(
                class_name="PandasDatasource",
                batch_kwargs_generators={
                    "subdir_reader": {
                        "class_name": "SubdirReaderBatchKwargsGenerator",
                        "base_directory": "../data/",
                    }
                },
            )
        },
        store_backend_defaults=store_backend_defaults,
    )

    # Create desired config
    data_context_id = data_context_config.anonymous_usage_statistics.data_context_id
    desired_config = construct_data_context_config(
        data_context_id=data_context_id, datasources=default_pandas_datasource_config
    )
    # Add root_directory to stores and data_docs
    desired_config["stores"][desired_config["expectations_store_name"]]["store_backend"][
        "root_directory"
    ] = test_root_directory
    desired_config["stores"][desired_config["validation_results_store_name"]]["store_backend"][
        "root_directory"
    ] = test_root_directory
    desired_config["stores"][desired_config["checkpoint_store_name"]]["store_backend"][
        "root_directory"
    ] = test_root_directory
    desired_config["stores"][desired_config["profiler_store_name"]]["store_backend"][
        "root_directory"
    ] = test_root_directory
    desired_config["data_docs_sites"]["local_site"]["store_backend"]["root_directory"] = (
        test_root_directory
    )

    desired_config["stores"]["validation_definition_store"]["store_backend"]["root_directory"] = (
        test_root_directory
    )

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )


@pytest.mark.unit
def test_DataContextConfig_with_FilesystemStoreBackendDefaults_and_simple_defaults_no_root_directory(  # noqa: E501
    construct_data_context_config, default_pandas_datasource_config
):
    """
    What does this test and why?
    Ensure that a very simple DataContextConfig setup using FilesystemStoreBackendDefaults is created accurately
    This test does not set the optional root_directory parameter
    """  # noqa: E501

    store_backend_defaults = FilesystemStoreBackendDefaults()
    data_context_config = DataContextConfig(
        datasources={
            "my_pandas_datasource": DatasourceConfig(
                class_name="PandasDatasource",
                batch_kwargs_generators={
                    "subdir_reader": {
                        "class_name": "SubdirReaderBatchKwargsGenerator",
                        "base_directory": "../data/",
                    }
                },
            )
        },
        store_backend_defaults=store_backend_defaults,
        checkpoint_store_name=store_backend_defaults.checkpoint_store_name,
        profiler_store_name=store_backend_defaults.profiler_store_name,
    )

    # Create desired config
    data_context_id = data_context_config.anonymous_usage_statistics.data_context_id
    desired_config = construct_data_context_config(
        data_context_id=data_context_id, datasources=default_pandas_datasource_config
    )

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )


@pytest.mark.unit
def test_DataContextConfig_with_GCSStoreBackendDefaults(
    construct_data_context_config, default_pandas_datasource_config
):
    """
    What does this test and why?
    Make sure that using GCSStoreBackendDefaults as the store_backend_defaults applies appropriate
    defaults, including default_bucket_name & default_project_name getting propagated
    to all stores.
    """

    store_backend_defaults = GCSStoreBackendDefaults(
        default_bucket_name="my_default_bucket",
        default_project_name="my_default_project",
    )
    data_context_config = DataContextConfig(
        datasources={
            "my_pandas_datasource": DatasourceConfig(
                class_name="PandasDatasource",
                module_name="great_expectations.datasource",
                data_asset_type={
                    "module_name": "great_expectations.dataset",
                    "class_name": "PandasDataset",
                },
                batch_kwargs_generators={
                    "subdir_reader": {
                        "class_name": "SubdirReaderBatchKwargsGenerator",
                        "base_directory": "../data/",
                    }
                },
            )
        },
        store_backend_defaults=store_backend_defaults,
    )

    # Create desired config
    data_context_id = data_context_config.anonymous_usage_statistics.data_context_id
    desired_stores_config = {
        "suite_parameter_store": {"class_name": "SuiteParameterStore"},
        "expectations_GCS_store": {
            "class_name": "ExpectationsStore",
            "store_backend": {
                "bucket": "my_default_bucket",
                "project": "my_default_project",
                "class_name": "TupleGCSStoreBackend",
                "prefix": "expectations",
            },
        },
        "validations_GCS_store": {
            "class_name": "ValidationsStore",
            "store_backend": {
                "bucket": "my_default_bucket",
                "project": "my_default_project",
                "class_name": "TupleGCSStoreBackend",
                "prefix": "validations",
            },
        },
        "validation_definition_store": {
            "class_name": "ValidationDefinitionStore",
            "store_backend": {
                "bucket": "my_default_bucket",
                "project": "my_default_project",
                "class_name": "TupleGCSStoreBackend",
                "prefix": "validation_definitions",
            },
        },
        "checkpoint_GCS_store": {
            "class_name": "CheckpointStore",
            "store_backend": {
                "bucket": "my_default_bucket",
                "project": "my_default_project",
                "class_name": "TupleGCSStoreBackend",
                "prefix": "checkpoints",
            },
        },
        "profiler_GCS_store": {
            "class_name": "ProfilerStore",
            "store_backend": {
                "bucket": "my_default_bucket",
                "project": "my_default_project",
                "class_name": "TupleGCSStoreBackend",
                "prefix": "profilers",
            },
        },
    }
    desired_data_docs_sites_config = {
        "gcs_site": {
            "class_name": "SiteBuilder",
            "show_how_to_buttons": True,
            "site_index_builder": {
                "class_name": "DefaultSiteIndexBuilder",
            },
            "store_backend": {
                "bucket": "my_default_bucket",
                "project": "my_default_project",
                "class_name": "TupleGCSStoreBackend",
                "prefix": "data_docs",
            },
        }
    }

    desired_config = construct_data_context_config(
        data_context_id=data_context_id,
        datasources=default_pandas_datasource_config,
        expectations_store_name="expectations_GCS_store",
        validation_results_store_name="validations_GCS_store",
        checkpoint_store_name="checkpoint_GCS_store",
        profiler_store_name="profiler_GCS_store",
        suite_parameter_store_name=DataContextConfigDefaults.DEFAULT_SUITE_PARAMETER_STORE_NAME.value,
        stores=desired_stores_config,
        data_docs_sites=desired_data_docs_sites_config,
    )

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )


@pytest.mark.unit
def test_DataContextConfig_with_GCSStoreBackendDefaults_using_all_parameters(
    construct_data_context_config, default_pandas_datasource_config
):
    """
    What does this test and why?
    Make sure that GCSStoreBackendDefaults parameters are handled appropriately
    E.g. Make sure that default_bucket_name is ignored if individual bucket names are passed
    """

    store_backend_defaults = GCSStoreBackendDefaults(
        default_bucket_name="custom_default_bucket_name",
        default_project_name="custom_default_project_name",
        expectations_store_bucket_name="custom_expectations_store_bucket_name",
        validation_results_store_bucket_name="custom_validation_results_store_bucket_name",
        data_docs_bucket_name="custom_data_docs_store_bucket_name",
        checkpoint_store_bucket_name="custom_checkpoint_store_bucket_name",
        profiler_store_bucket_name="custom_profiler_store_bucket_name",
        expectations_store_project_name="custom_expectations_store_project_name",
        validation_results_store_project_name="custom_validation_results_store_project_name",
        data_docs_project_name="custom_data_docs_store_project_name",
        checkpoint_store_project_name="custom_checkpoint_store_project_name",
        profiler_store_project_name="custom_profiler_store_project_name",
        expectations_store_prefix="custom_expectations_store_prefix",
        validation_results_store_prefix="custom_validation_results_store_prefix",
        data_docs_prefix="custom_data_docs_prefix",
        checkpoint_store_prefix="custom_checkpoint_store_prefix",
        profiler_store_prefix="custom_profiler_store_prefix",
        expectations_store_name="custom_expectations_GCS_store_name",
        validation_results_store_name="custom_validations_GCS_store_name",
        suite_parameter_store_name="custom_suite_parameter_store_name",
        checkpoint_store_name="custom_checkpoint_GCS_store_name",
        profiler_store_name="custom_profiler_GCS_store_name",
    )
    data_context_config = DataContextConfig(
        datasources={
            "my_pandas_datasource": DatasourceConfig(
                class_name="PandasDatasource",
                module_name="great_expectations.datasource",
                data_asset_type={
                    "module_name": "great_expectations.dataset",
                    "class_name": "PandasDataset",
                },
                batch_kwargs_generators={
                    "subdir_reader": {
                        "class_name": "SubdirReaderBatchKwargsGenerator",
                        "base_directory": "../data/",
                    }
                },
            )
        },
        store_backend_defaults=store_backend_defaults,
    )

    # Create desired config
    desired_stores_config = {
        "custom_suite_parameter_store_name": {"class_name": "SuiteParameterStore"},
        "custom_expectations_GCS_store_name": {
            "class_name": "ExpectationsStore",
            "store_backend": {
                "bucket": "custom_expectations_store_bucket_name",
                "project": "custom_expectations_store_project_name",
                "class_name": "TupleGCSStoreBackend",
                "prefix": "custom_expectations_store_prefix",
            },
        },
        "custom_validations_GCS_store_name": {
            "class_name": "ValidationsStore",
            "store_backend": {
                "bucket": "custom_validation_results_store_bucket_name",
                "project": "custom_validation_results_store_project_name",
                "class_name": "TupleGCSStoreBackend",
                "prefix": "custom_validation_results_store_prefix",
            },
        },
        "validation_definition_store": {
            "class_name": "ValidationDefinitionStore",
            "store_backend": {
                "bucket": "custom_default_bucket_name",
                "class_name": "TupleGCSStoreBackend",
                "prefix": "validation_definitions",
                "project": "custom_default_project_name",
            },
        },
        "custom_checkpoint_GCS_store_name": {
            "class_name": "CheckpointStore",
            "store_backend": {
                "bucket": "custom_checkpoint_store_bucket_name",
                "project": "custom_checkpoint_store_project_name",
                "class_name": "TupleGCSStoreBackend",
                "prefix": "custom_checkpoint_store_prefix",
            },
        },
        "custom_profiler_GCS_store_name": {
            "class_name": "ProfilerStore",
            "store_backend": {
                "bucket": "custom_profiler_store_bucket_name",
                "project": "custom_profiler_store_project_name",
                "class_name": "TupleGCSStoreBackend",
                "prefix": "custom_profiler_store_prefix",
            },
        },
    }
    desired_data_docs_sites_config = {
        "gcs_site": {
            "class_name": "SiteBuilder",
            "show_how_to_buttons": True,
            "site_index_builder": {
                "class_name": "DefaultSiteIndexBuilder",
            },
            "store_backend": {
                "bucket": "custom_data_docs_store_bucket_name",
                "project": "custom_data_docs_store_project_name",
                "class_name": "TupleGCSStoreBackend",
                "prefix": "custom_data_docs_prefix",
            },
        }
    }
    desired_config = construct_data_context_config(
        data_context_id=data_context_config.anonymous_usage_statistics.data_context_id,
        datasources=default_pandas_datasource_config,
        expectations_store_name="custom_expectations_GCS_store_name",
        validation_results_store_name="custom_validations_GCS_store_name",
        suite_parameter_store_name="custom_suite_parameter_store_name",
        checkpoint_store_name="custom_checkpoint_GCS_store_name",
        profiler_store_name="custom_profiler_GCS_store_name",
        stores=desired_stores_config,
        data_docs_sites=desired_data_docs_sites_config,
    )

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )


@pytest.mark.unit
def test_DataContextConfig_with_DatabaseStoreBackendDefaults(
    construct_data_context_config, default_pandas_datasource_config
):
    """
    What does this test and why?
    Make sure that using DatabaseStoreBackendDefaults as the store_backend_defaults applies appropriate
    defaults, including default_credentials getting propagated to stores and not data_docs
    """  # noqa: E501

    store_backend_defaults = DatabaseStoreBackendDefaults(
        default_credentials={
            "drivername": "postgresql",
            "host": os.getenv("GE_TEST_LOCAL_DB_HOSTNAME", "localhost"),
            "port": "65432",
            "username": "ge_tutorials",
            "password": "ge_tutorials",
            "database": "ge_tutorials",
        },
    )
    data_context_config = DataContextConfig(
        datasources={
            "my_pandas_datasource": DatasourceConfig(
                class_name="PandasDatasource",
                module_name="great_expectations.datasource",
                data_asset_type={
                    "module_name": "great_expectations.dataset",
                    "class_name": "PandasDataset",
                },
                batch_kwargs_generators={
                    "subdir_reader": {
                        "class_name": "SubdirReaderBatchKwargsGenerator",
                        "base_directory": "../data/",
                    }
                },
            )
        },
        store_backend_defaults=store_backend_defaults,
    )

    # Create desired config
    desired_stores_config = {
        "suite_parameter_store": {"class_name": "SuiteParameterStore"},
        "expectations_database_store": {
            "class_name": "ExpectationsStore",
            "store_backend": {
                "class_name": "DatabaseStoreBackend",
                "credentials": {
                    "drivername": "postgresql",
                    "host": os.getenv("GE_TEST_LOCAL_DB_HOSTNAME", "localhost"),
                    "port": "65432",
                    "username": "ge_tutorials",
                    "password": "ge_tutorials",
                    "database": "ge_tutorials",
                },
            },
        },
        "validations_database_store": {
            "class_name": "ValidationsStore",
            "store_backend": {
                "class_name": "DatabaseStoreBackend",
                "credentials": {
                    "drivername": "postgresql",
                    "host": os.getenv("GE_TEST_LOCAL_DB_HOSTNAME", "localhost"),
                    "port": "65432",
                    "username": "ge_tutorials",
                    "password": "ge_tutorials",
                    "database": "ge_tutorials",
                },
            },
        },
        "validation_definition_store": {
            "class_name": "ValidationDefinitionStore",
            "store_backend": {
                "class_name": "DatabaseStoreBackend",
                "credentials": {
                    "database": "ge_tutorials",
                    "drivername": "postgresql",
                    "host": "localhost",
                    "password": "ge_tutorials",
                    "port": "65432",
                    "username": "ge_tutorials",
                },
            },
        },
        "checkpoint_database_store": {
            "class_name": "CheckpointStore",
            "store_backend": {
                "class_name": "DatabaseStoreBackend",
                "credentials": {
                    "drivername": "postgresql",
                    "host": os.getenv("GE_TEST_LOCAL_DB_HOSTNAME", "localhost"),
                    "port": "65432",
                    "username": "ge_tutorials",
                    "password": "ge_tutorials",
                    "database": "ge_tutorials",
                },
            },
        },
        "profiler_database_store": {
            "class_name": "ProfilerStore",
            "store_backend": {
                "class_name": "DatabaseStoreBackend",
                "credentials": {
                    "drivername": "postgresql",
                    "host": os.getenv("GE_TEST_LOCAL_DB_HOSTNAME", "localhost"),
                    "port": "65432",
                    "username": "ge_tutorials",
                    "password": "ge_tutorials",
                    "database": "ge_tutorials",
                },
            },
        },
    }
    desired_data_docs_sites_config = {
        "local_site": {
            "class_name": "SiteBuilder",
            "show_how_to_buttons": True,
            "site_index_builder": {
                "class_name": "DefaultSiteIndexBuilder",
            },
            "store_backend": {
                "base_directory": "uncommitted/data_docs/local_site/",
                "class_name": "TupleFilesystemStoreBackend",
            },
        }
    }

    desired_config = construct_data_context_config(
        data_context_id=data_context_config.anonymous_usage_statistics.data_context_id,
        datasources=default_pandas_datasource_config,
        expectations_store_name="expectations_database_store",
        validation_results_store_name="validations_database_store",
        checkpoint_store_name="checkpoint_database_store",
        profiler_store_name="profiler_database_store",
        suite_parameter_store_name=DataContextConfigDefaults.DEFAULT_SUITE_PARAMETER_STORE_NAME.value,
        stores=desired_stores_config,
        data_docs_sites=desired_data_docs_sites_config,
    )

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )


@pytest.mark.unit
def test_DataContextConfig_with_DatabaseStoreBackendDefaults_using_all_parameters(
    construct_data_context_config, default_pandas_datasource_config
):
    """
    What does this test and why?
    Make sure that DatabaseStoreBackendDefaults parameters are handled appropriately
    E.g. Make sure that default_credentials is ignored if individual store credentials are passed
    """

    store_backend_defaults = DatabaseStoreBackendDefaults(
        default_credentials={
            "drivername": "postgresql",
            "host": os.getenv("GE_TEST_LOCAL_DB_HOSTNAME", "localhost"),
            "port": "65432",
            "username": "ge_tutorials",
            "password": "ge_tutorials",
            "database": "ge_tutorials",
        },
        expectations_store_credentials={
            "drivername": "custom_expectations_store_drivername",
            "host": "custom_expectations_store_host",
            "port": "custom_expectations_store_port",
            "username": "custom_expectations_store_username",
            "password": "custom_expectations_store_password",
            "database": "custom_expectations_store_database",
        },
        validation_results_store_credentials={
            "drivername": "custom_validation_results_store_drivername",
            "host": "custom_validation_results_store_host",
            "port": "custom_validation_results_store_port",
            "username": "custom_validation_results_store_username",
            "password": "custom_validation_results_store_password",
            "database": "custom_validation_results_store_database",
        },
        checkpoint_store_credentials={
            "drivername": "custom_checkpoint_store_drivername",
            "host": "custom_checkpoint_store_host",
            "port": "custom_checkpoint_store_port",
            "username": "custom_checkpoint_store_username",
            "password": "custom_checkpoint_store_password",
            "database": "custom_checkpoint_store_database",
        },
        profiler_store_credentials={
            "drivername": "custom_profiler_store_drivername",
            "host": "custom_profiler_store_host",
            "port": "custom_profiler_store_port",
            "username": "custom_profiler_store_username",
            "password": "custom_profiler_store_password",
            "database": "custom_profiler_store_database",
        },
        expectations_store_name="custom_expectations_database_store_name",
        validation_results_store_name="custom_validations_database_store_name",
        suite_parameter_store_name="custom_suite_parameter_store_name",
        checkpoint_store_name="custom_checkpoint_database_store_name",
        profiler_store_name="custom_profiler_database_store_name",
    )
    data_context_config = DataContextConfig(
        datasources={
            "my_pandas_datasource": DatasourceConfig(
                class_name="PandasDatasource",
                module_name="great_expectations.datasource",
                data_asset_type={
                    "module_name": "great_expectations.dataset",
                    "class_name": "PandasDataset",
                },
                batch_kwargs_generators={
                    "subdir_reader": {
                        "class_name": "SubdirReaderBatchKwargsGenerator",
                        "base_directory": "../data/",
                    }
                },
            )
        },
        store_backend_defaults=store_backend_defaults,
    )

    # Create desired config
    desired_stores_config = {
        "custom_suite_parameter_store_name": {"class_name": "SuiteParameterStore"},
        "custom_expectations_database_store_name": {
            "class_name": "ExpectationsStore",
            "store_backend": {
                "class_name": "DatabaseStoreBackend",
                "credentials": {
                    "database": "custom_expectations_store_database",
                    "drivername": "custom_expectations_store_drivername",
                    "host": "custom_expectations_store_host",
                    "password": "custom_expectations_store_password",
                    "port": "custom_expectations_store_port",
                    "username": "custom_expectations_store_username",
                },
            },
        },
        "custom_validations_database_store_name": {
            "class_name": "ValidationsStore",
            "store_backend": {
                "class_name": "DatabaseStoreBackend",
                "credentials": {
                    "database": "custom_validation_results_store_database",
                    "drivername": "custom_validation_results_store_drivername",
                    "host": "custom_validation_results_store_host",
                    "password": "custom_validation_results_store_password",
                    "port": "custom_validation_results_store_port",
                    "username": "custom_validation_results_store_username",
                },
            },
        },
        "validation_definition_store": {
            "class_name": "ValidationDefinitionStore",
            "store_backend": {
                "class_name": "DatabaseStoreBackend",
                "credentials": {
                    "database": "ge_tutorials",
                    "drivername": "postgresql",
                    "host": "localhost",
                    "password": "ge_tutorials",
                    "port": "65432",
                    "username": "ge_tutorials",
                },
            },
        },
        "custom_checkpoint_database_store_name": {
            "class_name": "CheckpointStore",
            "store_backend": {
                "class_name": "DatabaseStoreBackend",
                "credentials": {
                    "database": "custom_checkpoint_store_database",
                    "drivername": "custom_checkpoint_store_drivername",
                    "host": "custom_checkpoint_store_host",
                    "password": "custom_checkpoint_store_password",
                    "port": "custom_checkpoint_store_port",
                    "username": "custom_checkpoint_store_username",
                },
            },
        },
        "custom_profiler_database_store_name": {
            "class_name": "ProfilerStore",
            "store_backend": {
                "class_name": "DatabaseStoreBackend",
                "credentials": {
                    "database": "custom_profiler_store_database",
                    "drivername": "custom_profiler_store_drivername",
                    "host": "custom_profiler_store_host",
                    "password": "custom_profiler_store_password",
                    "port": "custom_profiler_store_port",
                    "username": "custom_profiler_store_username",
                },
            },
        },
    }
    desired_data_docs_sites_config = {
        "local_site": {
            "class_name": "SiteBuilder",
            "show_how_to_buttons": True,
            "site_index_builder": {
                "class_name": "DefaultSiteIndexBuilder",
            },
            "store_backend": {
                "base_directory": "uncommitted/data_docs/local_site/",
                "class_name": "TupleFilesystemStoreBackend",
            },
        }
    }

    desired_config = construct_data_context_config(
        data_context_id=data_context_config.anonymous_usage_statistics.data_context_id,
        datasources=default_pandas_datasource_config,
        expectations_store_name="custom_expectations_database_store_name",
        validation_results_store_name="custom_validations_database_store_name",
        suite_parameter_store_name="custom_suite_parameter_store_name",
        checkpoint_store_name="custom_checkpoint_database_store_name",
        profiler_store_name="custom_profiler_database_store_name",
        stores=desired_stores_config,
        data_docs_sites=desired_data_docs_sites_config,
    )

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )


@pytest.mark.unit
def test_override_general_defaults(
    construct_data_context_config,
    default_pandas_datasource_config,
):
    """
    What does this test and why?
    A DataContextConfig should be able to be created by passing items into the constructor that override any defaults.
    It should also be able to handle multiple datasources, even if they are configured with a dictionary or a DatasourceConfig.
    """  # noqa: E501

    data_context_config = DataContextConfig(
        config_version=999,
        plugins_directory="custom_plugins_directory",
        config_variables_file_path="custom_config_variables_file_path",
        datasources={
            "my_pandas_datasource": DatasourceConfig(
                class_name="PandasDatasource",
                batch_kwargs_generators={
                    "subdir_reader": {
                        "class_name": "SubdirReaderBatchKwargsGenerator",
                        "base_directory": "../data/",
                    }
                },
            ),
        },
        stores={
            "expectations_S3_store": {
                "class_name": "ExpectationsStore",
                "store_backend": {
                    "class_name": "TupleS3StoreBackend",
                    "bucket": "REPLACE_ME",
                    "prefix": "REPLACE_ME",
                },
            },
            "expectations_S3_store2": {
                "class_name": "ExpectationsStore",
                "store_backend": {
                    "class_name": "TupleS3StoreBackend",
                    "bucket": "REPLACE_ME",
                    "prefix": "REPLACE_ME",
                },
            },
            "validations_S3_store": {
                "class_name": "ValidationsStore",
                "store_backend": {
                    "class_name": "TupleS3StoreBackend",
                    "bucket": "REPLACE_ME",
                    "prefix": "REPLACE_ME",
                },
            },
            "validations_S3_store2": {
                "class_name": "ValidationsStore",
                "store_backend": {
                    "class_name": "TupleS3StoreBackend",
                    "bucket": "REPLACE_ME",
                    "prefix": "REPLACE_ME",
                },
            },
            "custom_suite_parameter_store": {"class_name": "SuiteParameterStore"},
            "checkpoint_S3_store": {
                "class_name": "CheckpointStore",
                "store_backend": {
                    "class_name": "TupleS3StoreBackend",
                    "bucket": "REPLACE_ME",
                    "prefix": "REPLACE_ME",
                },
            },
            "profiler_S3_store": {
                "class_name": "ProfilerStore",
                "store_backend": {
                    "class_name": "TupleS3StoreBackend",
                    "bucket": "REPLACE_ME",
                    "prefix": "REPLACE_ME",
                },
            },
        },
        expectations_store_name="custom_expectations_store_name",
        validation_results_store_name="custom_validation_results_store_name",
        suite_parameter_store_name="custom_suite_parameter_store_name",
        checkpoint_store_name="checkpoint_S3_store",
        profiler_store_name="profiler_S3_store",
        data_docs_sites={
            "s3_site": {
                "class_name": "SiteBuilder",
                "store_backend": {
                    "class_name": "TupleS3StoreBackend",
                    "bucket": "REPLACE_ME",
                },
                "site_index_builder": {
                    "class_name": "DefaultSiteIndexBuilder",
                },
            },
            "local_site": {
                "class_name": "SiteBuilder",
                "show_how_to_buttons": True,
                "site_index_builder": {
                    "class_name": "DefaultSiteIndexBuilder",
                },
                "store_backend": {
                    "base_directory": "uncommitted/data_docs/local_site/",
                    "class_name": "TupleFilesystemStoreBackend",
                },
            },
        },
        validation_operators={
            "custom_action_list_operator": {
                "class_name": "ActionListValidationOperator",
                "action_list": [
                    {
                        "name": "custom_store_validation_result",
                        "action": {"class_name": "CustomStoreValidationResultAction"},
                    },
                    {
                        "name": "update_data_docs",
                        "action": {"class_name": "UpdateDataDocsAction"},
                    },
                ],
            }
        },
        anonymous_usage_statistics={"enabled": True},
    )

    desired_stores = {
        "custom_suite_parameter_store": {"class_name": "SuiteParameterStore"},
        "expectations_S3_store": {
            "class_name": "ExpectationsStore",
            "store_backend": {
                "bucket": "REPLACE_ME",
                "class_name": "TupleS3StoreBackend",
                "prefix": "REPLACE_ME",
            },
        },
        "expectations_S3_store2": {
            "class_name": "ExpectationsStore",
            "store_backend": {
                "bucket": "REPLACE_ME",
                "class_name": "TupleS3StoreBackend",
                "prefix": "REPLACE_ME",
            },
        },
        "validations_S3_store": {
            "class_name": "ValidationsStore",
            "store_backend": {
                "bucket": "REPLACE_ME",
                "class_name": "TupleS3StoreBackend",
                "prefix": "REPLACE_ME",
            },
        },
        "validations_S3_store2": {
            "class_name": "ValidationsStore",
            "store_backend": {
                "bucket": "REPLACE_ME",
                "class_name": "TupleS3StoreBackend",
                "prefix": "REPLACE_ME",
            },
        },
        "validation_definition_store": {
            "class_name": "ValidationDefinitionStore",
        },
        "checkpoint_S3_store": {
            "class_name": "CheckpointStore",
            "store_backend": {
                "bucket": "REPLACE_ME",
                "class_name": "TupleS3StoreBackend",
                "prefix": "REPLACE_ME",
            },
        },
        "profiler_S3_store": {
            "class_name": "ProfilerStore",
            "store_backend": {
                "bucket": "REPLACE_ME",
                "class_name": "TupleS3StoreBackend",
                "prefix": "REPLACE_ME",
            },
        },
    }

    desired_data_docs_sites_config = {
        "local_site": {
            "class_name": "SiteBuilder",
            "show_how_to_buttons": True,
            "site_index_builder": {
                "class_name": "DefaultSiteIndexBuilder",
            },
            "store_backend": {
                "base_directory": "uncommitted/data_docs/local_site/",
                "class_name": "TupleFilesystemStoreBackend",
            },
        },
        "s3_site": {
            "class_name": "SiteBuilder",
            "site_index_builder": {
                "class_name": "DefaultSiteIndexBuilder",
            },
            "store_backend": {
                "bucket": "REPLACE_ME",
                "class_name": "TupleS3StoreBackend",
            },
        },
    }
    desired_validation_operators = {
        "custom_action_list_operator": {
            "class_name": "ActionListValidationOperator",
            "action_list": [
                {
                    "name": "custom_store_validation_result",
                    "action": {"class_name": "CustomStoreValidationResultAction"},
                },
                {
                    "name": "update_data_docs",
                    "action": {"class_name": "UpdateDataDocsAction"},
                },
            ],
        }
    }

    desired_config = construct_data_context_config(
        data_context_id=data_context_config.anonymous_usage_statistics.data_context_id,
        datasources={
            **default_pandas_datasource_config,
        },
        config_version=999.0,
        expectations_store_name="custom_expectations_store_name",
        validation_results_store_name="custom_validation_results_store_name",
        suite_parameter_store_name="custom_suite_parameter_store_name",
        checkpoint_store_name="checkpoint_S3_store",
        profiler_store_name="profiler_S3_store",
        stores=desired_stores,
        validation_operators=desired_validation_operators,
        data_docs_sites=desired_data_docs_sites_config,
        plugins_directory="custom_plugins_directory",
    )
    desired_config["config_variables_file_path"] = "custom_config_variables_file_path"

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )


@pytest.mark.big
@pytest.mark.slow  # 1.81s
def test_DataContextConfig_with_S3StoreBackendDefaults_and_simple_defaults_with_variable_sub(
    monkeypatch, construct_data_context_config, default_pandas_datasource_config
):
    """
    What does this test and why?
    Ensure that a very simple DataContextConfig setup with many defaults is created accurately
    and produces a valid DataContextConfig
    """

    monkeypatch.setenv("SUBSTITUTED_BASE_DIRECTORY", "../data/")

    store_backend_defaults = S3StoreBackendDefaults(default_bucket_name="my_default_bucket")
    data_context_config = DataContextConfig(
        datasources={
            "my_pandas_datasource": DatasourceConfig(
                class_name="PandasDatasource",
                batch_kwargs_generators={
                    "subdir_reader": {
                        "class_name": "SubdirReaderBatchKwargsGenerator",
                        "base_directory": "${SUBSTITUTED_BASE_DIRECTORY}",
                    }
                },
            )
        },
        store_backend_defaults=store_backend_defaults,
    )

    # Create desired config
    desired_stores_config = {
        "suite_parameter_store": {"class_name": "SuiteParameterStore"},
        "expectations_S3_store": {
            "class_name": "ExpectationsStore",
            "store_backend": {
                "bucket": "my_default_bucket",
                "class_name": "TupleS3StoreBackend",
                "prefix": "expectations",
            },
        },
        "validations_S3_store": {
            "class_name": "ValidationsStore",
            "store_backend": {
                "bucket": "my_default_bucket",
                "class_name": "TupleS3StoreBackend",
                "prefix": "validations",
            },
        },
        "validation_definition_store": {
            "class_name": "ValidationDefinitionStore",
            "store_backend": {
                "bucket": "my_default_bucket",
                "class_name": "TupleS3StoreBackend",
                "prefix": "validation_definitions",
            },
        },
        "checkpoint_S3_store": {
            "class_name": "CheckpointStore",
            "store_backend": {
                "bucket": "my_default_bucket",
                "class_name": "TupleS3StoreBackend",
                "prefix": "checkpoints",
            },
        },
        "profiler_S3_store": {
            "class_name": "ProfilerStore",
            "store_backend": {
                "bucket": "my_default_bucket",
                "class_name": "TupleS3StoreBackend",
                "prefix": "profilers",
            },
        },
    }
    desired_data_docs_sites_config = {
        "s3_site": {
            "class_name": "SiteBuilder",
            "show_how_to_buttons": True,
            "site_index_builder": {
                "class_name": "DefaultSiteIndexBuilder",
            },
            "store_backend": {
                "bucket": "my_default_bucket",
                "class_name": "TupleS3StoreBackend",
                "prefix": "data_docs",
            },
        }
    }

    desired_config = construct_data_context_config(
        data_context_id=data_context_config.anonymous_usage_statistics.data_context_id,
        datasources=default_pandas_datasource_config,
        expectations_store_name="expectations_S3_store",
        validation_results_store_name="validations_S3_store",
        checkpoint_store_name="checkpoint_S3_store",
        profiler_store_name="profiler_S3_store",
        suite_parameter_store_name=DataContextConfigDefaults.DEFAULT_SUITE_PARAMETER_STORE_NAME.value,
        stores=desired_stores_config,
        data_docs_sites=desired_data_docs_sites_config,
    )

    desired_config["datasources"]["my_pandas_datasource"]["batch_kwargs_generators"][
        "subdir_reader"
    ]["base_directory"] = "${SUBSTITUTED_BASE_DIRECTORY}"

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )

    data_context = get_context(project_config=data_context_config)
    assert (
        data_context.datasources["my_pandas_datasource"]
        .get_batch_kwargs_generator("subdir_reader")
        ._base_directory
        == "../data/"
    )


@pytest.mark.unit
def test_DataContextConfig_with_InMemoryStoreBackendDefaults(
    construct_data_context_config,
):
    store_backend_defaults = InMemoryStoreBackendDefaults()
    data_context_config = DataContextConfig(
        store_backend_defaults=store_backend_defaults,
    )

    desired_config = {
        "anonymous_usage_statistics": {
            "data_context_id": data_context_config.anonymous_usage_statistics.data_context_id,
            "enabled": True,
        },
        "checkpoint_store_name": "checkpoint_store",
        "profiler_store_name": "profiler_store",
        "config_version": 3.0,
        "suite_parameter_store_name": "suite_parameter_store",
        "expectations_store_name": "expectations_store",
        "include_rendered_content": {
            "expectation_suite": False,
            "expectation_validation_result": False,
            "globally": False,
        },
        "stores": {
            "checkpoint_store": {
                "class_name": "CheckpointStore",
                "store_backend": {"class_name": "InMemoryStoreBackend"},
            },
            "profiler_store": {
                "class_name": "ProfilerStore",
                "store_backend": {"class_name": "InMemoryStoreBackend"},
            },
            "suite_parameter_store": {"class_name": "SuiteParameterStore"},
            "expectations_store": {
                "class_name": "ExpectationsStore",
                "store_backend": {"class_name": "InMemoryStoreBackend"},
            },
            "validation_results_store": {
                "class_name": "ValidationsStore",
                "store_backend": {"class_name": "InMemoryStoreBackend"},
            },
            "validation_definition_store": {
                "class_name": "ValidationDefinitionStore",
                "store_backend": {"class_name": "InMemoryStoreBackend"},
            },
        },
        "validation_results_store_name": "validation_results_store",
    }

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )


@pytest.mark.unit
def test_data_context_config_defaults():
    config = DataContextConfig()
    assert config.to_json_dict() == {
        "anonymous_usage_statistics": {
            "data_context_id": mock.ANY,
            "enabled": True,
            "explicit_id": False,
            "explicit_url": False,
            "usage_statistics_url": "https://stats.greatexpectations.io/great_expectations/v1/usage_statistics",
        },
        "checkpoint_store_name": None,
        "config_variables_file_path": None,
        "config_version": 3,
        "data_docs_sites": None,
        "datasources": {},
        "suite_parameter_store_name": None,
        "expectations_store_name": None,
        "fluent_datasources": {},
        "include_rendered_content": {
            "expectation_suite": False,
            "expectation_validation_result": False,
            "globally": False,
        },
        "plugins_directory": None,
        "profiler_store_name": None,
        "progress_bars": None,
        "stores": DataContextConfigDefaults.DEFAULT_STORES.value,
        "validation_operators": None,
        "validation_results_store_name": None,
    }
