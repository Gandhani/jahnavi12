import datetime
import json
import os
from typing import Optional

from ruamel.yaml.comments import CommentedMap

from great_expectations import DataContext
from great_expectations.cli.upgrade_helpers.base_upgrade_helper import BaseUpgradeHelper
from great_expectations.data_context.types.base import (
    DataContextConfig,
    DataContextConfigDefaults,
)
from great_expectations.data_context.util import default_checkpoints_exist


class UpgradeHelperV13(BaseUpgradeHelper):
    def __init__(
        self,
        data_context: Optional[DataContext] = None,
        context_root_dir: Optional[str] = None,
        update_version: Optional[bool] = False,
    ):
        assert (
            data_context or context_root_dir
        ), "Please provide a data_context object or a context_root_dir."

        self.data_context = data_context or DataContext(
            context_root_dir=context_root_dir
        )

        # noinspection SpellCheckingInspection
        self.upgrade_log = {
            "update_version": update_version,
            "skipped_checkpoints_upgrade": False,
            "added_checkpoint_store": {},
            "skipped_datasources_upgrade": False,
            "skipped_validation_operators_upgrade": False,
        }

        # noinspection SpellCheckingInspection
        self.upgrade_checklist = {
            "automatic": {
                "stores": {},
                "store_names": {},
            },
            "manual": {
                "datasources": {},
                "validation_operators": {},
            },
        }

        self._generate_upgrade_checklist()

    def _generate_upgrade_checklist(self):
        self._process_checkpoint_store_for_checklist()
        self._process_datasources_for_checklist()
        self._process_validation_operators_for_checklist()

    def _process_checkpoint_store_for_checklist(self):
        if default_checkpoints_exist(directory_path=self.data_context.root_directory):
            config_commented_map: CommentedMap = (
                self.data_context.get_config().commented_map
            )
            checkpoint_store_name: Optional[str] = config_commented_map.get(
                "checkpoint_store_name"
            )
            stores: dict = config_commented_map["stores"]
            if checkpoint_store_name:
                if stores.get(checkpoint_store_name):
                    self.upgrade_log["skipped_checkpoints_upgrade"] = True
                else:
                    self.upgrade_checklist["automatic"]["stores"] = {
                        checkpoint_store_name: DataContextConfigDefaults.DEFAULT_STORES.value[
                            DataContextConfigDefaults.DEFAULT_CHECKPOINT_STORE_NAME.value
                        ]
                    }
            else:
                checkpoint_store_name = (
                    DataContextConfigDefaults.DEFAULT_CHECKPOINT_STORE_NAME.value
                )
                self.upgrade_checklist["automatic"]["store_names"][
                    "checkpoint_store_name"
                ] = checkpoint_store_name
                if not stores.get(checkpoint_store_name):
                    self.upgrade_checklist["automatic"]["stores"] = {
                        checkpoint_store_name: DataContextConfigDefaults.DEFAULT_STORES.value[
                            checkpoint_store_name
                        ]
                    }
        else:
            self.upgrade_log["skipped_checkpoints_upgrade"] = True

    # noinspection SpellCheckingInspection
    def _process_datasources_for_checklist(self):
        config_commented_map: CommentedMap = (
            self.data_context.get_config().commented_map
        )
        datasources: dict = config_commented_map.get("datasources") or {}
        datasource_name: str
        datasource_config: dict
        self.upgrade_checklist["manual"]["datasources"] = {
            datasource_name: datasource_config
            for datasource_name, datasource_config in datasources.items()
            if (
                set(datasource_config.keys())
                & {"execution_engine", "data_connectors", "introspection", "tables"}
            )
            == set()
        }

        if len(self.upgrade_checklist["manual"]["datasources"]) == 0:
            self.upgrade_log["skipped_datasources_upgrade"] = True

    def _process_validation_operators_for_checklist(self):
        config_commented_map: CommentedMap = (
            self.data_context.get_config().commented_map
        )
        validation_operators: dict = (
            config_commented_map.get("validation_operators") or {}
        )
        validation_operator_name: str
        validation_operator_config: dict
        self.upgrade_checklist["manual"]["validation_operators"] = {
            validation_operator_name: validation_operator_config
            for validation_operator_name, validation_operator_config in validation_operators.items()
            if validation_operator_config
        }

        if len(self.upgrade_checklist["manual"]["validation_operators"]) == 0:
            self.upgrade_log["skipped_validation_operators_upgrade"] = True

    def manual_steps_required(self):
        return any(
            [
                len(manual_upgrade_item.keys()) > 0
                for manual_upgrade_item in self.upgrade_checklist["manual"].values()
            ]
        )

    def get_upgrade_overview(self):
        confirmation_required = not self.upgrade_log["skipped_checkpoints_upgrade"]

        manual_steps_required = self.manual_steps_required()

        increment_version = self.upgrade_log["update_version"]

        upgrade_overview = f"""\
<cyan>\
++====================================++
|| UpgradeHelperV13: Upgrade Overview ||
++====================================++\
</cyan>

"""
        stores_upgrade_checklist = list(
            self.upgrade_checklist["automatic"]["stores"].keys()
        )
        store_names_upgrade_checklist = list(
            self.upgrade_checklist["automatic"]["store_names"].keys()
        )

        # noinspection SpellCheckingInspection
        datasources_upgrade_checklist = self.upgrade_checklist["manual"]["datasources"]

        if increment_version:
            upgrade_overview += f"""\
UpgradeHelperV13 will upgrade your project to be compatible with Great Expectations 0.13.x.
"""
            # noinspection SpellCheckingInspection
            if (
                self.upgrade_log["skipped_checkpoints_upgrade"]
                and self.upgrade_log["skipped_datasources_upgrade"]
                and self.upgrade_log["skipped_validation_operators_upgrade"]
            ):
                upgrade_overview += """
<green>\
Good news! No special upgrade steps are required to bring your project up to date.
The Upgrade Helper will simply increment the config_version of your great_expectations.yml for you.
</green>
"""
            else:
                upgrade_overview += """
<red>**WARNING**: Before proceeding, please make sure you have appropriate backups of your project.</red>
"""
                if not self.upgrade_log["skipped_checkpoints_upgrade"]:
                    if stores_upgrade_checklist or store_names_upgrade_checklist:
                        upgrade_overview += """
<cyan>\
Automated Steps
================
</cyan>
The following Stores and/or Store Names will be upgraded:

"""
                        upgrade_overview += (
                            f"""\
    - Stores: {", ".join(stores_upgrade_checklist)}
"""
                            if stores_upgrade_checklist
                            else ""
                        )
                        upgrade_overview += (
                            f"""\
    - Store Names: {", ".join(store_names_upgrade_checklist)}
"""
                            if store_names_upgrade_checklist
                            else ""
                        )

                # noinspection SpellCheckingInspection
                if manual_steps_required:
                    upgrade_overview += """
<cyan>\
Manual Steps
=============
</cyan>
"""
                    # noinspection SpellCheckingInspection
                    if not self.upgrade_log["skipped_datasources_upgrade"]:
                        upgrade_overview += """\
The following Data Sources must be upgraded manually, due to using the old Datasource format, which is being deprecated:

"""
                        upgrade_overview += (
                            f"""\
    - Data Sources: {", ".join(datasources_upgrade_checklist)}
"""
                            if datasources_upgrade_checklist
                            else ""
                        )

                    if not self.upgrade_log["skipped_validation_operators_upgrade"]:
                        upgrade_overview += """
Your configuration uses validation_operators, which are being deprecated.  Please, manually convert \
validation_operators to use the new Checkpoint validation unit, since validation_operators will be deleted.

"""
                else:
                    upgrade_overview += """
<cyan>\
Manual Steps
=============
</cyan>
No manual upgrade steps are required.
"""

                upgrade_overview += """
<cyan>\
Upgrade Confirmation
=====================
</cyan>
Please consult the 0.13.x migration guide for instructions on how to complete any required manual steps or to learn \
more about the automated upgrade process:

    <cyan>https://docs.greatexpectations.io/docs/guides/miscellaneous/migration_guide</cyan>

Would you like to proceed with the project upgrade?\
"""
        else:
            upgrade_overview += f"""\
Your project needs to be upgraded in order to be compatible with Great Expectations 0.13.x.
"""
            # noinspection SpellCheckingInspection
            if (
                self.upgrade_log["skipped_checkpoints_upgrade"]
                and self.upgrade_log["skipped_datasources_upgrade"]
                and self.upgrade_log["skipped_validation_operators_upgrade"]
            ):
                upgrade_overview += """
<green>\
Good news! No special upgrade steps are required to bring your project up to date.
The Upgrade Helper will simply increment the config_version of your great_expectations.yml for you.
</green>

"""
            else:
                if not self.upgrade_log["skipped_checkpoints_upgrade"]:
                    if stores_upgrade_checklist or store_names_upgrade_checklist:
                        upgrade_overview += """
<cyan>\
Automated Steps
================
</cyan>
The following Stores and/or Store Names need to be upgraded:

"""
                        upgrade_overview += (
                            f"""\
    - Stores: {", ".join(stores_upgrade_checklist)}
"""
                            if stores_upgrade_checklist
                            else ""
                        )
                        upgrade_overview += (
                            f"""\
    - Store Names: {", ".join(store_names_upgrade_checklist)}
"""
                            if store_names_upgrade_checklist
                            else ""
                        )

                # noinspection SpellCheckingInspection
                if manual_steps_required:
                    upgrade_overview += """
<cyan>\
Manual Steps
=============
</cyan>
"""
                    # noinspection SpellCheckingInspection
                    if not self.upgrade_log["skipped_datasources_upgrade"]:
                        upgrade_overview += """\
The following Data Sources must be upgraded manually, due to using the old Datasource format, which is being deprecated:

"""
                        upgrade_overview += (
                            f"""\
    - Data Sources: {", ".join(datasources_upgrade_checklist)}
"""
                            if datasources_upgrade_checklist
                            else ""
                        )

                    if not self.upgrade_log["skipped_validation_operators_upgrade"]:
                        upgrade_overview += """
Your configuration uses validation_operators, which are being deprecated.  Please, manually convert \
validation_operators to use the new Checkpoint validation unit, since validation_operators will be deleted.
"""
                else:
                    upgrade_overview += """
<cyan>\
Manual Steps
=============
</cyan>
No manual upgrade steps are required.
"""

        return upgrade_overview, confirmation_required

    def upgrade_project(self):
        # noinspection PyBroadException
        try:
            self._upgrade_configuration_automatically()
        except Exception:
            pass

        # return a report of what happened, boolean indicating whether or not version should be incremented,
        # the report should include instructions for steps to be performed manually
        (
            upgrade_report,
            increment_version,
            exception_occurred,
        ) = self._generate_upgrade_report()
        return upgrade_report, increment_version, exception_occurred

    def _upgrade_configuration_automatically(self):
        if not self.upgrade_log["skipped_checkpoints_upgrade"]:
            config_commented_map: CommentedMap = (
                self.data_context.get_config().commented_map
            )
            for key, config in self.upgrade_checklist["automatic"]["stores"].items():
                config_commented_map["stores"][key] = config

            for key, value in self.upgrade_checklist["automatic"][
                "store_names"
            ].items():
                config_commented_map[key] = value

            data_context_config: DataContextConfig = (
                DataContextConfig.from_commented_map(commented_map=config_commented_map)
            )
            self.data_context.set_config(project_config=data_context_config)
            self.data_context._save_project_config()

            checkpoint_log_entry = {
                "stores": {
                    DataContextConfigDefaults.DEFAULT_CHECKPOINT_STORE_NAME.value: data_context_config.stores[
                        DataContextConfigDefaults.DEFAULT_CHECKPOINT_STORE_NAME.value
                    ],
                },
                "checkpoint_store_name": data_context_config.checkpoint_store_name,
            }
            self.upgrade_log["added_checkpoint_store"].update(checkpoint_log_entry)

    def _generate_upgrade_report(self):
        upgrade_log_path = self._save_upgrade_log()
        increment_version = self.upgrade_log["update_version"]
        upgrade_report = f"""\
<cyan>\
++================++
|| Upgrade Report ||
++================++\
</cyan>
"""
        manual_steps_required = self.manual_steps_required()

        if increment_version:
            if manual_steps_required:
                upgrade_report += f"""
<yellow>\
The Upgrade Helper has performed the automated upgrade steps as part of upgrading your project to be compatible with \
Great Expectations 0.13.x, and the config_version of your great_expectations.yml has been automatically incremented to \
3.0.  However, manual steps are required in order for the upgrade process to be completed successfully.

A log detailing the upgrade can be found here:

    - {upgrade_log_path}\
</yellow>\
"""
            else:
                upgrade_report += f"""
<green>\
Your project was successfully upgraded to be compatible with Great Expectations 0.13.x.  The config_version of your \
great_expectations.yml has been automatically incremented to 3.0.

A log detailing the upgrade can be found here:

    - {upgrade_log_path}\
</green>\
"""
        else:
            if manual_steps_required:
                upgrade_report += f"""
<yellow>\
The Upgrade Helper does not have any automated upgrade steps to perform as part of upgrading your project to be \
compatible with Great Expectations 0.13.x, and the config_version of your great_expectations.yml is already set to \
3.0.  However, manual steps are required in order for the upgrade process to be completed successfully.

A log detailing the upgrade can be found here:

    - {upgrade_log_path}\
</yellow>\
"""
            else:
                upgrade_report += f"""
<yellow>\
The Upgrade Helper finds your project to be compatible with Great Expectations 0.13.x, and the config_version of your \
great_expectations.yml is already set to 3.0.  There are no additional automatic or manual steps required, since the \
upgrade process has been completed successfully.

A log detailing the upgrade can be found here:

    - {upgrade_log_path}\
</yellow>\
"""
        exception_occurred = False
        return upgrade_report, increment_version, exception_occurred

    def _save_upgrade_log(self):
        current_time = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y%m%dT%H%M%S.%fZ"
        )
        dest_path = os.path.join(
            self.data_context.root_directory,
            "uncommitted",
            "logs",
            "project_upgrades",
            f"UpgradeHelperV13_{current_time}.json",
        )
        dest_dir, dest_filename = os.path.split(dest_path)
        os.makedirs(dest_dir, exist_ok=True)

        with open(dest_path, "w") as outfile:
            json.dump(self.upgrade_log, outfile, indent=2)

        return dest_path
