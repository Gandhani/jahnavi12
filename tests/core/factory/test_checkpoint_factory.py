import pytest
from pytest_mock import MockerFixture

from great_expectations import set_context
from great_expectations.checkpoint.v1_checkpoint import Checkpoint
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core.factory.checkpoint_factory import CheckpointFactory
from great_expectations.core.validation_definition import ValidationDefinition
from great_expectations.data_context import AbstractDataContext
from great_expectations.data_context.store.checkpoint_store import (
    V1CheckpointStore as CheckpointStore,
)
from great_expectations.exceptions import DataContextError


@pytest.fixture
def checkpoint_dict():
    return {
        "name": "my_checkpoint",
        "validation_definitions": [
            {
                "name": "my_validation_def",
                "id": "a758816-64c8-46cb-8f7e-03c12cea1d67",
            }
        ],
        "actions": [],
        "id": "c758816-64c8-46cb-8f7e-03c12cea1d67",
    }


def _assert_checkpoint_equality(actual: Checkpoint, expected: Checkpoint):
    # Checkpoint equality is currently defined as equality of the config
    # TODO: We should change this to a more robust comparison (instead of memory addresses)
    actual_config = actual.config.to_json_dict()
    expected_config = expected.config.to_json_dict()
    assert actual_config == expected_config


@pytest.mark.unit
def test_checkpoint_factory_get_uses_store_get(checkpoint_dict: dict, mocker: MockerFixture):
    # Arrange
    name = "test-checkpoint"
    store = mocker.MagicMock(spec=CheckpointStore)
    store.has_key.return_value = True
    key = store.get_key.return_value
    store.get.return_value = checkpoint_dict
    context = mocker.MagicMock(spec=AbstractDataContext)
    factory = CheckpointFactory(store=store, context=context)
    set_context(context)

    # Act
    result = factory.get(name=name)

    # Assert
    store.get.assert_called_once_with(key=key)

    assert result == checkpoint_dict


@pytest.mark.unit
def test_checkpoint_factory_get_raises_error_on_missing_key(
    checkpoint_dict: dict, mocker: MockerFixture
):
    # Arrange
    name = "test-checkpoint"
    store = mocker.MagicMock(spec=CheckpointStore)
    store.has_key.return_value = False
    store.get.return_value = checkpoint_dict
    context = mocker.MagicMock(spec=AbstractDataContext)
    factory = CheckpointFactory(store=store, context=context)
    set_context(context)

    # Act
    with pytest.raises(DataContextError, match=f"Checkpoint with name {name} was not found."):
        factory.get(name=name)

    # Assert
    store.get.assert_not_called()


@pytest.mark.unit
def test_checkpoint_factory_add_uses_store_add(mocker: MockerFixture):
    # Arrange
    name = "test-checkpoint"
    store = mocker.MagicMock(spec=CheckpointStore)
    store.has_key.return_value = False
    key = store.get_key.return_value
    context = mocker.MagicMock(spec=AbstractDataContext)
    factory = CheckpointFactory(store=store, context=context)
    set_context(context)
    checkpoint = Checkpoint(
        name=name, validation_definitions=[mocker.Mock(spec=ValidationDefinition)], actions=[]
    )

    # Act
    factory.add(checkpoint=checkpoint)

    # Assert
    store.add.assert_called_once_with(key=key, value=checkpoint.dict())


@pytest.mark.unit
def test_checkpoint_factory_add_raises_for_duplicate_key(mocker: MockerFixture):
    # Arrange
    name = "test-checkpoint"
    store = mocker.MagicMock(spec=CheckpointStore)
    store.has_key.return_value = True
    context = mocker.MagicMock(spec=AbstractDataContext)
    factory = CheckpointFactory(store=store, context=context)
    set_context(context)
    checkpoint = Checkpoint(
        name=name, validation_definitions=[mocker.Mock(spec=ValidationDefinition)], actions=[]
    )

    # Act
    with pytest.raises(
        DataContextError,
        match=f"Cannot add Checkpoint with name {name} because it already exists.",
    ):
        factory.add(checkpoint=checkpoint)

    # Assert
    store.add.assert_not_called()


@pytest.mark.unit
def test_checkpoint_factory_delete_uses_store_remove_key(mocker: MockerFixture):
    # Arrange
    name = "test-checkpoint"
    store = mocker.MagicMock(spec=CheckpointStore)
    store.has_key.return_value = True
    key = store.get_key.return_value
    context = mocker.MagicMock(spec=AbstractDataContext)
    factory = CheckpointFactory(store=store, context=context)
    set_context(context)
    checkpoint = Checkpoint(
        name=name, validation_definitions=[mocker.Mock(spec=ValidationDefinition)], actions=[]
    )

    # Act
    factory.delete(checkpoint=checkpoint)

    # Assert
    store.remove_key.assert_called_once_with(
        key=key,
    )


@pytest.mark.unit
def test_checkpoint_factory_delete_raises_for_missing_checkpoint(mocker: MockerFixture):
    # Arrange
    name = "test-checkpoint"
    store = mocker.MagicMock(spec=CheckpointStore)
    store.has_key.return_value = False
    context = mocker.MagicMock(spec=AbstractDataContext)
    factory = CheckpointFactory(store=store, context=context)
    set_context(context)
    checkpoint = Checkpoint(
        name=name, validation_definitions=[mocker.Mock(spec=ValidationDefinition)], actions=[]
    )

    # Act
    with pytest.raises(
        DataContextError,
        match=f"Cannot delete Checkpoint with name {name} because it cannot be found.",
    ):
        factory.delete(checkpoint=checkpoint)

    # Assert
    store.remove_key.assert_not_called()


@pytest.mark.filesystem
def test_checkpoint_factory_is_initialized_with_context_filesystem(empty_data_context):
    assert isinstance(empty_data_context.checkpoints, CheckpointFactory)


@pytest.mark.cloud
def test_checkpoint_factory_is_initialized_with_context_cloud(empty_cloud_data_context):
    assert isinstance(empty_cloud_data_context.checkpoints, CheckpointFactory)


@pytest.mark.filesystem
def test_checkpoint_factory_add_success_filesystem(empty_data_context, mocker: MockerFixture):
    _test_checkpoint_factory_add_success(empty_data_context, mocker)


@pytest.mark.cloud
def test_checkpoint_factory_add_success_cloud(empty_cloud_context_fluent, mocker: MockerFixture):
    _test_checkpoint_factory_add_success(empty_cloud_context_fluent, mocker)


def _test_checkpoint_factory_add_success(context, mocker):
    # Arrange
    name = "test-checkpoint"
    ds = context.sources.add_pandas("my_datasource")
    asset = ds.add_csv_asset("my_asset", "data.csv")
    batch_def = asset.add_batch_definition("my_batch_definition")
    suite = ExpectationSuite(name="my_suite")

    checkpoint = Checkpoint(
        name=name,
        validation_definitions=[
            ValidationDefinition(name="validation_def", data=batch_def, suite=suite)
        ],
        actions=[],
    )
    with pytest.raises(DataContextError, match=f"Checkpoint with name {name} was not found."):
        context.checkpoints.get(name)

    # Act
    created_checkpoint = context.checkpoints.add(checkpoint=checkpoint)

    # Assert
    assert created_checkpoint == context.checkpoints.get(name=name)


@pytest.mark.filesystem
def test_checkpoint_factory_delete_success_filesystem(empty_data_context):
    _test_checkpoint_factory_delete_success(empty_data_context)


@pytest.mark.cloud
def test_checkpoint_factory_delete_success_cloud(empty_cloud_context_fluent):
    _test_checkpoint_factory_delete_success(empty_cloud_context_fluent)


def _test_checkpoint_factory_delete_success(context):
    # Arrange
    name = "test-checkpoint"
    ds = context.sources.add_pandas("my_datasource")
    asset = ds.add_csv_asset("my_asset", "data.csv")
    batch_def = asset.add_batch_definition("my_batch_definition")
    suite = ExpectationSuite(name="my_suite")

    checkpoint = context.checkpoints.add(
        checkpoint=Checkpoint(
            name=name,
            validation_definitions=[
                ValidationDefinition(name="validation_def", data=batch_def, suite=suite)
            ],
            actions=[],
        )
    )

    # Act
    context.checkpoints.delete(checkpoint)

    # Assert
    with pytest.raises(
        DataContextError,
        match=f"Checkpoint with name {name} was not found.",
    ):
        context.checkpoints.get(name)


class TestCheckpointFactoryAnalytics:
    # TODO: Write tests once analytics are in place
    pass
