import os

from ruamel import yaml

import great_expectations as ge
from great_expectations.core.expectation_validation_result import (
    ExpectationSuiteValidationResult,
)
from great_expectations.core.run_identifier import RunIdentifier
from great_expectations.data_context.types.base import CheckpointConfig
from great_expectations.data_context.types.resource_identifiers import (
    ValidationResultIdentifier,
)

context = ge.get_context()

# Add datasource for all tests
datasource_yaml = """
name: taxi_datasource
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
  default_inferred_data_connector_name:
    class_name: InferredAssetFilesystemDataConnector
    base_directory: ../data/
    default_regex:
      group_names:
        - data_asset_name
      pattern: (.*)\.csv
  default_runtime_data_connector_name:
    class_name: RuntimeDataConnector
    batch_identifiers:
      - default_identifier_name
"""
context.test_yaml_config(datasource_yaml)
context.add_datasource(**yaml.load(datasource_yaml))
assert [ds["name"] for ds in context.list_datasources()] == ["taxi_datasource"]
context.create_expectation_suite("my_expectation_suite")
context.create_expectation_suite("my_other_expectation_suite")

# Add a Checkpoint
checkpoint_yaml = """
name: test_checkpoint
config_version: 1
class_name: Checkpoint
run_name_template: "%Y-%M-foo-bar-template"
validations:
  - batch_request:
      datasource_name: taxi_datasource
      data_connector_name: default_inferred_data_connector_name
      data_asset_name: yellow_tripdata_sample_2019-01
      data_connector_query:
        index: -1
    expectation_suite_name: my_expectation_suite
    action_list:
      - name: <ACTION NAME FOR STORING VALIDATION RESULTS>
        action:
          class_name: StoreValidationResultAction
      - name: <ACTION NAME FOR STORING EVALUATION PARAMETERS>
        action:
          class_name: StoreEvaluationParametersAction
      - name: <ACTION NAME FOR UPDATING DATA DOCS>
        action:
          class_name: UpdateDataDocsAction
"""
context.add_checkpoint(**yaml.load(checkpoint_yaml))
assert context.list_checkpoints() == ["test_checkpoint"]

results = context.run_checkpoint(checkpoint_name="test_checkpoint")
assert results.success == True
run_id_type = type(results.run_id)
assert run_id_type == RunIdentifier
validation_result_id_type_set = set(type(k) for k in results.run_results.keys())
assert len(validation_result_id_type_set) == 1
validation_result_id_type = next(iter(validation_result_id_type_set))
assert validation_result_id_type == ValidationResultIdentifier
validation_result_id = results.run_results[[k for k in results.run_results.keys()][0]]
assert (
    type(validation_result_id["validation_result"]) == ExpectationSuiteValidationResult
)
assert type(results.checkpoint_config) == CheckpointConfig

typed_results = {
    "run_id": run_id_type,
    "run_results": {
        validation_result_id_type: {
            "validation_result": type(validation_result_id["validation_result"]),
            "actions_results": {
                "<ACTION NAME FOR STORING VALIDATION RESULTS>": {
                    "class": "StoreValidationResultAction"
                }
            },
        }
    },
    "checkpoint_config": CheckpointConfig,
    "success": True,
}

documentation_results = {
    "run_id": RunIdentifier,
    "run_results": {
        ValidationResultIdentifier: {
            "validation_result": ExpectationSuiteValidationResult,
            "actions_results": {
                "<ACTION NAME FOR STORING VALIDATION RESULTS>": {
                    "class": "StoreValidationResultAction"
                }
            },
        }
    },
    "checkpoint_config": CheckpointConfig,
    "success": True,
}

assert typed_results == documentation_results

# A few different Checkpoint examples
os.environ["VAR"] = "ge"
os.environ["MY_PARAM"] = "1000"
os.environ["OLD_PARAM"] = "500"

no_nesting = """
name: my_checkpoint
config_version: 1
class_name: Checkpoint
run_name_template: "%Y-%M-foo-bar-template-$VAR"
validations:
  - batch_request:
      datasource_name: taxi_datasource
      data_connector_name: default_inferred_data_connector_name
      data_asset_name: yellow_tripdata_sample_2019-01
      data_connector_query:
        index: -1
    expectation_suite_name: my_expectation_suite
    action_list:
      - name: store_validation_result
        action:
          class_name: StoreValidationResultAction
      - name: store_evaluation_params
        action:
          class_name: StoreEvaluationParametersAction
      - name: update_data_docs
        action:
          class_name: UpdateDataDocsAction
    evaluation_parameters:
      param1: $MY_PARAM
      param2: 1 + $OLD_PARAM
    runtime_configuration:
      result_format:
        result_format: BASIC
        partial_unexpected_count: 20
"""
context.add_checkpoint(**yaml.load(no_nesting))
results = context.run_checkpoint(checkpoint_name="my_checkpoint")
assert results.success == True

nesting_with_defaults = """
name: my_checkpoint
config_version: 1
class_name: Checkpoint
run_name_template: "%Y-%M-foo-bar-template-$VAR"
validations:
  - batch_request:
      datasource_name: taxi_datasource
      data_connector_name: default_inferred_data_connector_name
      data_asset_name: yellow_tripdata_sample_2019-01
      data_connector_query:
        index: -1
  - batch_request:
      datasource_name: taxi_datasource
      data_connector_name: default_inferred_data_connector_name
      data_asset_name: yellow_tripdata_sample_2019-02
      data_connector_query:
        index: -1
expectation_suite_name: my_expectation_suite
action_list:
  - name: store_validation_result
    action:
      class_name: StoreValidationResultAction
  - name: store_evaluation_params
    action:
      class_name: StoreEvaluationParametersAction
  - name: update_data_docs
    action:
      class_name: UpdateDataDocsAction
evaluation_parameters:
  param1: $MY_PARAM
  param2: 1 + $OLD_PARAM
runtime_configuration:
  result_format:
    result_format: BASIC
    partial_unexpected_count: 20
"""
context.add_checkpoint(**yaml.load(nesting_with_defaults))
results = context.run_checkpoint(checkpoint_name="my_checkpoint")
assert results.success == True

keys_passed_at_runtime = """
name: my_base_checkpoint
config_version: 1
class_name: Checkpoint
run_name_template: "%Y-%M-foo-bar-template-$VAR"
action_list:
  - name: store_validation_result
    action:
      class_name: StoreValidationResultAction
  - name: store_evaluation_params
    action:
      class_name: StoreEvaluationParametersAction
  - name: update_data_docs
    action:
      class_name: UpdateDataDocsAction
evaluation_parameters:
  param1: $MY_PARAM
  param2: 1 + $OLD_PARAM
runtime_configuration:
  result_format:
    result_format: BASIC
    partial_unexpected_count: 20
"""
context.add_checkpoint(**yaml.load(keys_passed_at_runtime))
results = context.run_checkpoint(
    checkpoint_name="my_base_checkpoint",
    validations=[
        {
            "batch_request": {
                "datasource_name": "taxi_datasource",
                "data_connector_name": "default_inferred_data_connector_name",
                "data_asset_name": "yellow_tripdata_sample_2019-01",
                "data_connector_query": {"index": -1},
            },
            "expectation_suite_name": "my_expectation_suite",
        },
        {
            "batch_request": {
                "datasource_name": "taxi_datasource",
                "data_connector_name": "default_inferred_data_connector_name",
                "data_asset_name": "yellow_tripdata_sample_2019-02",
                "data_connector_query": {"index": -1},
            },
            "expectation_suite_name": "my_other_expectation_suite",
        },
    ],
)
assert results.checkpoint_config.validations[0]["expectation_suite_name"] == "my_expectation_suite"
assert results.checkpoint_config.validations[1]["expectation_suite_name"] == "my_other_expectation_suite"

using_template = """
name: my_checkpoint
config_version: 1
class_name: Checkpoint
template_name: my_base_checkpoint
validations:
  - batch_request:
      datasource_name: taxi_datasource
      data_connector_name: default_inferred_data_connector_name
      data_asset_name: yellow_tripdata_sample_2019-01
      data_connector_query:
        index: -1
    expectation_suite_name: my_expectation_suite
  - batch_request:
      datasource_name: taxi_datasource
      data_connector_name: default_inferred_data_connector_name
      data_asset_name: yellow_tripdata_sample_2019-02
      data_connector_query:
        index: -1
    expectation_suite_name: my_other_expectation_suite
"""
context.add_checkpoint(**yaml.load(using_template))
results = context.run_checkpoint(checkpoint_name="my_checkpoint")
assert results.success == True

using_simple_checkpoint = """
name: my_checkpoint
config_version: 1
class_name: SimpleCheckpoint
validations:
  - batch_request:
      datasource_name: taxi_datasource
      data_connector_name: default_inferred_data_connector_name
      data_asset_name: yellow_tripdata_sample_2019-01
      data_connector_query:
        index: -1
    expectation_suite_name: my_expectation_suite
site_names: all
slack_webhook: <YOUR SLACK WEBHOOK URL>
notify_on: failure
notify_with: all
"""
using_simple_checkpoint = using_simple_checkpoint.replace(
    "<YOUR SLACK WEBHOOK URL>", "https://hooks.slack.com/foo/bar"
)
context.add_checkpoint(**yaml.load(using_simple_checkpoint))
results = context.run_checkpoint(checkpoint_name="my_checkpoint")
assert results.success == True

equivalent_using_checkpoint = """
name: my_checkpoint
config_version: 1
class_name: Checkpoint
validations:
  - batch_request:
      datasource_name: taxi_datasource
      data_connector_name: default_inferred_data_connector_name
      data_asset_name: yellow_tripdata_sample_2019-01
      data_connector_query:
        index: -1
    expectation_suite_name: my_expectation_suite
action_list:
  - name: store_validation_result
    action:
      class_name: StoreValidationResultAction
  - name: store_evaluation_params
    action:
      class_name: StoreEvaluationParametersAction
  - name: update_data_docs
    action:
      class_name: UpdateDataDocsAction
  - name: send_slack_notification
    action:
      class_name: SlackNotificationAction
      slack_webhook: <YOUR SLACK WEBHOOK URL>
      notify_on: failure
      notify_with: all
      renderer:
        module_name: great_expectations.render.renderer.slack_renderer
        class_name: SlackRenderer
"""
equivalent_using_checkpoint = equivalent_using_checkpoint.replace(
    "<YOUR SLACK WEBHOOK URL>", "https://hooks.slack.com/foo/bar"
)
context.add_checkpoint(**yaml.load(equivalent_using_checkpoint))
results = context.run_checkpoint(checkpoint_name="my_checkpoint")
assert results.success == True
