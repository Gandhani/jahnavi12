import yaml

from great_expectations.data_context import BaseDataContext
from great_expectations.data_context.types.base import (
    ConcurrencyConfig,
    DataContextConfig,
    InMemoryStoreBackendDefaults,
)


def test_concurrency_disabled_by_default():
    data_context_config = DataContextConfig()
    assert not data_context_config.concurrency.enabled


def test_concurrency_enabled_with_dict():
    data_context_config = DataContextConfig(concurrency={"enabled": True})
    assert data_context_config.concurrency.enabled


def test_concurrency_enabled_with_yaml():
    yaml_config = """
    concurrency:
      enabled: true
    """
    data_context_config = DataContextConfig(**yaml.load(yaml_config))
    assert data_context_config.concurrency.enabled
    assert (
        yaml.load(data_context_config.to_yaml_str())["concurrency"]["enabled"] is True
    )


def test_concurrency_enabled_with_config():
    data_context_config = DataContextConfig(concurrency=ConcurrencyConfig(enabled=True))
    assert data_context_config.concurrency.enabled


def test_data_context_concurrency_property():
    data_context = BaseDataContext(
        project_config=DataContextConfig(
            concurrency=ConcurrencyConfig(enabled=True),
            store_backend_defaults=InMemoryStoreBackendDefaults(),
        )
    )
    assert data_context.concurrency.enabled
