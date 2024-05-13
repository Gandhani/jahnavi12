from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

from great_expectations.render.renderer.renderer import Renderer

if TYPE_CHECKING:
    from great_expectations.core.expectation_validation_result import (
        ExpectationSuiteValidationResult,
    )


class SlackRenderer(Renderer):
    def render(  # noqa: PLR0913
        self,
        validation_result: ExpectationSuiteValidationResult,
        checkpoint_name: str,
        data_docs_pages: list[dict] | None = None,
        notify_with: list[str] | None = None,
        show_failed_expectations: bool = False,
        validation_result_urls: list[str] | None = None,
    ) -> list[dict]:
        data_docs_pages = data_docs_pages or []
        notify_with = notify_with or []
        validation_result_urls = validation_result_urls or []
        run_id = validation_result.meta.get("run_id", "__no_run_id__")
        run_time = datetime.fromisoformat(str(run_id.run_time))
        formatted_run_time = run_time.strftime("%Y/%m/%d %I:%M %p")

        blocks: list[dict] = []
        run_time_block = self._build_run_time_block(time=formatted_run_time)
        blocks.append(run_time_block)
        description_block = self._build_description_block(
            validation_result=validation_result,
            validation_result_urls=validation_result_urls,
            checkpoint_name=checkpoint_name
        )
        blocks.append(description_block)

        report_element_block = self._build_report_element_block(
            data_docs_pages=data_docs_pages, notify_with=notify_with
        )
        if report_element_block:
            blocks.append(report_element_block)

        return blocks

    def _build_description_block(
            self,
            validation_result: ExpectationSuiteValidationResult,
            validation_result_urls: list[str],
            checkpoint_name: str
    ) -> dict:
        status = "Failed :x:"
        if validation_result.success:
            status = "Success :tada:"

        validation_link = None
        summary_text = ""
        if validation_result_urls:
            if len(validation_result_urls) == 1:
                validation_link = validation_result_urls[0]
            else:
                title_hlink = "*Validation Result*"
                batch_validation_status_hlinks = "".join(
                    f"*Batch Validation Status*: *<{validation_result_url} | {status}>*"
                    for validation_result_url in validation_result_urls
                )
                summary_text += f"""{title_hlink}
    {batch_validation_status_hlinks}
                """

        expectation_suite_name = validation_result.suite_name
        data_asset_name = validation_result.asset_name or "__no_data_asset_name__"
        summary_text += \
            f"*Checkpoint*: {checkpoint_name}\n*Expectation Suite*: {expectation_suite_name}"

        if validation_link is not None:
            summary_text += f"\n*Asset*: {data_asset_name}  <{validation_link} | View Results>"

        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": summary_text,
            },
        }

    def concatenate_text_blocks(self, action_name: str, text_blocks: list[dict], success: bool) -> dict:
        all_blocks = [self._build_header(name=action_name, success=success)]
        for block in text_blocks:
            all_blocks.append(block)
        all_blocks.append(self._build_divider())


        return {"blocks": all_blocks}

    def _build_description(self, checkpoint_name: str, expectation_suite_name: str, data_asset_name: str) \
            -> dict:
        summary_text = ""
        summary_text += f"""
        *Checkpoint*: {checkpoint_name}
        *Expectation Suite*: {expectation_suite_name}
        *Asset*: {data_asset_name}
        """
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": summary_text,
            },
        }

    def _build_header(self, name: str, success: bool) -> dict:
        status = "Success :white_check_mark:" if success else "Failure :no_entry:"
        return {"type": "header", "text": {"type": "plain_text", "text": f"{name} - {status}"}}

    def _build_run_time_block(self, time: str) -> dict:
        return {"type": "section", "text": {"type": "plain_text", "text": f"Runtime: {time}"}}

    def _build_divider(self) -> dict:
        return {"type": "divider"}

    def _build_footer(self) -> dict:
        documentation_url = "https://docs.greatexpectations.io/docs/terms/data_docs"
        return {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Learn how to review validation results in Data Docs: {documentation_url}",  # noqa: E501
                }
            ],
        }

    def _get_report_element(self, docs_link):
        report_element = None
        if docs_link:
            try:
                if "file://" in docs_link:
                    # handle special case since Slack does not render these links
                    report_element = {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*DataDocs* can be found here: `{docs_link}` \n (Please copy and paste link into "  # noqa: E501
                            f"a browser to view)\n",
                        },
                    }
                else:
                    report_element = {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*DataDocs* can be found here: <{docs_link}|{docs_link}>",
                        },
                    }
            except Exception as e:
                logger.warning(
                    f"""SlackRenderer had a problem with generating the docs link.
                    link used to generate the docs link is: {docs_link} and is of type: {type(docs_link)}.
                    Error: {e}"""  # noqa: E501
                )
                return
        else:
            logger.warning("No docs link found. Skipping data docs link in Slack message.")
        return report_element

    def _build_report_element_block(
        self, data_docs_pages: list[dict], notify_with: list[str]
    ) -> dict | None:
        if not data_docs_pages:
            return None

        if notify_with:
            for docs_link_key in notify_with:
                if docs_link_key in data_docs_pages:
                    docs_link = data_docs_pages[docs_link_key]
                    report_element = self._get_report_element(docs_link)
                else:
                    logger.critical(
                        f"*ERROR*: Slack is trying to provide a link to the following DataDocs: `"
                        f"{docs_link_key!s}`, but it is not configured under `data_docs_sites` in the "  # noqa: E501
                        f"`great_expectations.yml`\n"
                    )
                    report_element = {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*ERROR*: Slack is trying to provide a link to the following DataDocs: "  # noqa: E501
                            f"`{docs_link_key!s}`, but it is not configured under "
                            f"`data_docs_sites` in the `great_expectations.yml`\n",
                        },
                    }
                if report_element:
                    return report_element
        else:
            for docs_link_key in data_docs_pages:
                if docs_link_key == "class":
                    continue
                docs_link = data_docs_pages[docs_link_key]
                report_element = self._get_report_element(docs_link)
                return report_element

        return None
