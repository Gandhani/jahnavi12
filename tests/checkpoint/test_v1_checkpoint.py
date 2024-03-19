from __future__ import annotations

import json
import pathlib
import uuid
from unittest import mock

import pytest

import great_expectations as gx
from great_expectations.checkpoint.actions import (
    MicrosoftTeamsNotificationAction,
    SlackNotificationAction,
    ValidationAction,
)
from great_expectations.checkpoint.v1_checkpoint import Checkpoint
from great_expectations.compatibility.pydantic import ValidationError
from great_expectations.core.batch_config import BatchConfig
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core.validation_config import ValidationConfig
from great_expectations.data_context.data_context.ephemeral_data_context import (
    EphemeralDataContext,
)
from tests.test_utils import working_directory


@pytest.mark.unit
def test_checkpoint_no_validations_raises_error():
    with pytest.raises(ValueError) as e:
        Checkpoint(name="my_checkpoint", validations=[], actions=[])

    assert "Checkpoint must contain at least one validation" in str(e.value)


class TestCheckpointSerialization:
    @pytest.fixture
    def in_memory_context(self) -> EphemeralDataContext:
        return gx.get_context(mode="ephemeral")

    @pytest.fixture
    def validation_config_1(
        self, in_memory_context: EphemeralDataContext, mocker: pytest.MockFixture
    ):
        name = "my_first_validation"
        vc = ValidationConfig(
            name=name,
            data=mocker.Mock(spec=BatchConfig),
            suite=mocker.Mock(spec=ExpectationSuite),
        )
        with mock.patch.object(
            ValidationConfig,
            "json",
            return_value=json.dumps({"id": str(uuid.uuid4()), "name": name}),
        ):
            yield in_memory_context.validations.add(vc)

    @pytest.fixture
    def validation_config_2(
        self, in_memory_context: EphemeralDataContext, mocker: pytest.MockFixture
    ):
        name = "my_second_validation"
        vc = ValidationConfig(
            name=name,
            data=mocker.Mock(spec=BatchConfig),
            suite=mocker.Mock(spec=ExpectationSuite),
        )
        with mock.patch.object(
            ValidationConfig,
            "json",
            return_value=json.dumps({"id": str(uuid.uuid4()), "name": name}),
        ):
            yield in_memory_context.validations.add(vc)

    @pytest.fixture
    def validation_configs(
        self,
        validation_config_1: ValidationConfig,
        validation_config_2: ValidationConfig,
    ) -> list[ValidationConfig]:
        return [validation_config_1, validation_config_2]

    @pytest.fixture
    def slack_action(self):
        return SlackNotificationAction(
            slack_webhook="slack_webhook",
        )

    @pytest.fixture
    def teams_action(self):
        return MicrosoftTeamsNotificationAction(
            teams_webhook="teams_webhook",
        )

    @pytest.fixture
    def actions(
        self,
        slack_action: SlackNotificationAction,
        teams_action: MicrosoftTeamsNotificationAction,
    ) -> list[ValidationAction]:
        return [slack_action, teams_action]

    @pytest.mark.parametrize(
        "action_fixture_name, expected_actions",
        [
            pytest.param(None, [], id="no_actions"),
            pytest.param(
                "actions",
                [
                    {
                        "notify_on": "all",
                        "notify_with": None,
                        "renderer": {
                            "class_name": "SlackRenderer",
                            "module_name": "great_expectations.render.renderer.slack_renderer",
                        },
                        "show_failed_expectations": False,
                        "slack_channel": None,
                        "slack_token": None,
                        "slack_webhook": "slack_webhook",
                        "type": "slack",
                    },
                    {
                        "notify_on": "all",
                        "renderer": {
                            "class_name": "MicrosoftTeamsRenderer",
                            "module_name": "great_expectations.render.renderer.microsoft_teams_renderer",
                        },
                        "teams_webhook": "teams_webhook",
                        "type": "microsoft",
                    },
                ],
                id="actions",
            ),
        ],
    )
    @pytest.mark.unit
    def test_checkpoint_serialization(
        self,
        validation_configs: list[ValidationConfig],
        action_fixture_name: str | None,
        expected_actions: dict,
        request: pytest.FixtureRequest,
    ):
        actions = (
            request.getfixturevalue(action_fixture_name) if action_fixture_name else []
        )
        cp = Checkpoint(
            name="my_checkpoint",
            validations=validation_configs,
            actions=actions,
        )

        actual = json.loads(cp.json(models_as_dict=False))
        expected = {
            "name": cp.name,
            "validations": [
                {
                    "id": mock.ANY,
                    "name": "my_first_validation",
                },
                {
                    "id": mock.ANY,
                    "name": "my_second_validation",
                },
            ],
            "actions": expected_actions,
            "id": cp.id,
        }

        assert actual == expected
        self._assert_valid_uuid(actual["validations"][0]["id"])
        self._assert_valid_uuid(actual["validations"][1]["id"])

    @pytest.mark.unit
    def test_checkpoint_round_trip_adds_ids(
        self, tmp_path: pathlib.Path, actions: list[ValidationAction]
    ):
        with working_directory(tmp_path):
            context = gx.get_context(mode="file")

        ds_name = "my_datasource"
        asset_name = "my_asset"
        batch_config_name_1 = "my_batch1"
        suite_name_1 = "my_suite1"
        validation_config_name_1 = "my_validation1"
        batch_config_name_2 = "my_batch2"
        suite_name_2 = "my_suite2"
        validation_config_name_2 = "my_validation2"
        cp_name = "my_checkpoint"

        ds = context.sources.add_pandas(ds_name)
        asset = ds.add_csv_asset(asset_name, "my_file.csv")

        bc1 = asset.add_batch_config(batch_config_name_1)
        suite1 = ExpectationSuite(suite_name_1)
        vc1 = ValidationConfig(name=validation_config_name_1, data=bc1, suite=suite1)

        bc2 = asset.add_batch_config(batch_config_name_2)
        suite2 = ExpectationSuite(suite_name_2)
        vc2 = ValidationConfig(name=validation_config_name_2, data=bc2, suite=suite2)

        validations = [vc1, vc2]
        cp = Checkpoint(name=cp_name, validations=validations, actions=actions)

        serialized_checkpoint = cp.json(models_as_dict=False)
        serialized_checkpoint_dict = json.loads(serialized_checkpoint)

        assert serialized_checkpoint_dict == {
            "name": cp_name,
            "validations": [
                {
                    "id": mock.ANY,
                    "name": validation_config_name_1,
                },
                {
                    "id": mock.ANY,
                    "name": validation_config_name_2,
                },
            ],
            "actions": [
                {
                    "notify_on": "all",
                    "notify_with": None,
                    "renderer": {
                        "class_name": "SlackRenderer",
                        "module_name": "great_expectations.render.renderer.slack_renderer",
                    },
                    "show_failed_expectations": False,
                    "slack_channel": None,
                    "slack_token": None,
                    "slack_webhook": "slack_webhook",
                    "type": "slack",
                },
                {
                    "notify_on": "all",
                    "renderer": {
                        "class_name": "MicrosoftTeamsRenderer",
                        "module_name": "great_expectations.render.renderer.microsoft_teams_renderer",
                    },
                    "teams_webhook": "teams_webhook",
                    "type": "microsoft",
                },
            ],
            "id": None,
        }

        cp = Checkpoint.parse_raw(serialized_checkpoint)
        assert cp.validations[0].id is not None
        assert cp.validations[1].id is not None
        assert cp.validations[0].suite.id is not None
        assert cp.validations[1].suite.id is not None

    def _assert_valid_uuid(self, id: str | None) -> None:
        if not id:
            pytest.fail(
                "id is None when it should be a valid UUID generated from a Store."
            )

        try:
            uuid.UUID(id)
        except ValueError:
            pytest.fail(f"{id} is not a valid UUID.")

    @pytest.mark.parametrize(
        "serialized_checkpoint, expected_error",
        [
            pytest.param(
                {
                    "name": "my_checkpoint",
                    "validations": [],
                    "actions": [],
                    "id": "c758816-64c8-46cb-8f7e-03c12cea1d67",
                },
                "Checkpoint must contain at least one validation",
                id="missing_validations",
            ),
            pytest.param(
                {
                    "name": "my_checkpoint",
                    "validations": [
                        {
                            "name": "i_do_not_exist",
                            "id": "a758816-64c8-46cb-8f7e-03c12cea1d67",
                        }
                    ],
                    "actions": [],
                    "id": "c758816-64c8-46cb-8f7e-03c12cea1d67",
                },
                "Unable to retrieve validation config",
                id="nonexistent_validation",
            ),
            pytest.param(
                {
                    "name": "my_checkpoint",
                    "validations": [
                        {
                            "other_key": "i_do_not_exist",
                            "id": "a758816-64c8-46cb-8f7e-03c12cea1d67",
                        }
                    ],
                    "actions": [],
                    "id": "c758816-64c8-46cb-8f7e-03c12cea1d67",
                },
                "validations -> name\n  field required",
                id="invalid_validation",
            ),
        ],
    )
    @pytest.mark.unit
    def test_checkpoint_deserialization_failure(
        self, serialized_checkpoint: str, expected_error: str
    ):
        with pytest.raises(ValidationError) as e:
            Checkpoint.parse_obj(serialized_checkpoint)

        assert expected_error in str(e.value)
