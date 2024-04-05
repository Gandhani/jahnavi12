from __future__ import annotations

import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

from great_expectations.core.id_dict import BatchKwargs
from great_expectations.render.renderer.renderer import Renderer

if TYPE_CHECKING:
    from great_expectations.checkpoint.v1_checkpoint import CheckpointResult
    from great_expectations.core.expectation_validation_result import (
        ExpectationSuiteValidationResult,
    )
    from great_expectations.data_context.types.resource_identifiers import (
        ValidationResultIdentifier,
    )


class OpsgenieRenderer(Renderer):
    def v1_render(self, checkpoint_result: CheckpointResult):
        text_blocks: list[str] = []
        for run_id, run_result in checkpoint_result.run_results.items():
            text_block = self._v1_render(run_id=run_id, run_result=run_result)
            text_blocks.append(text_block)

        return self._concatenate_text_blocks(
            checkpoint_result=checkpoint_result, text_blocks=text_blocks
        )

    def _v1_render(
        self, run_id: ValidationResultIdentifier, run_result: ExpectationSuiteValidationResult
    ) -> str:
        suite_name = run_result.suite_name

        data_asset_name: str = "__no_data_asset_name__"
        if run_result.meta and "active_batch_definition" in run_result.meta:
            data_asset_name = run_result.meta["active_batch_definition"].data_asset_name

        n_checks_succeeded = run_result.statistics["successful_expectations"]
        n_checks = run_result.statistics["evaluated_expectations"]
        run_id = run_result.meta.get("run_id", "__no_run_id__")
        batch_id = BatchKwargs(run_result.meta.get("batch_kwargs", {})).to_id()
        check_details_text = f"{n_checks_succeeded} of {n_checks} expectations were met"

        if run_result.success:
            status = "Success 🎉"
        else:
            status = "Failed ❌"

        return f"""Batch Validation Status: {status}
Expectation Suite Name: {suite_name}
Data Asset Name: {data_asset_name}
Run ID: {run_id}
Batch ID: {batch_id}
Summary: {check_details_text}"""

    def _concatenate_text_blocks(
        self, checkpoint_result: CheckpointResult, text_blocks: list[str]
    ) -> str:
        checkpoint_name = checkpoint_result.checkpoint_config.name
        success = checkpoint_result.success
        run_id = checkpoint_result.run_id.run_time

        title = f"Checkpoint: {checkpoint_name} - Run ID: {run_id}"
        status = "Status: Failed ❌" if not success else "Status: Success 🎉"
        return f"{title}\n{status}\n\n" + "\n\n".join(text_blocks)

    def render(
        self,
        validation_result=None,
        data_docs_pages=None,
        notify_with=None,
    ):
        summary_text = "No validation occurred. Please ensure you passed a validation_result."
        status = "Failed ❌"

        if validation_result:
            expectation_suite_name = validation_result.meta.get(
                "expectation_suite_name", "__no_expectation_suite_name__"
            )

            if "batch_kwargs" in validation_result.meta:
                data_asset_name = validation_result.meta["batch_kwargs"].get(
                    "data_asset_name", "__no_data_asset_name__"
                )
            elif "active_batch_definition" in validation_result.meta:
                data_asset_name = (
                    validation_result.meta["active_batch_definition"].data_asset_name
                    if validation_result.meta["active_batch_definition"].data_asset_name
                    else "__no_data_asset_name__"
                )
            else:
                data_asset_name = "__no_data_asset_name__"

            n_checks_succeeded = validation_result.statistics["successful_expectations"]
            n_checks = validation_result.statistics["evaluated_expectations"]
            run_id = validation_result.meta.get("run_id", "__no_run_id__")
            batch_id = BatchKwargs(validation_result.meta.get("batch_kwargs", {})).to_id()
            check_details_text = f"{n_checks_succeeded} of {n_checks} expectations were met"

            if validation_result.success:
                status = "Success 🎉"

            summary_text = f"""Batch Validation Status: {status}
Expectation suite name: {expectation_suite_name}
Data asset name: {data_asset_name}
Run ID: {run_id}
Batch ID: {batch_id}
Summary: {check_details_text}"""

        return summary_text

    def _custom_blocks(self, evr):
        return None

    def _get_report_element(self, docs_link):
        return None
