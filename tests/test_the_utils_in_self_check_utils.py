from __future__ import annotations
import pytest

from great_expectations.self_check.util import (
    generate_test_table_name_with_expectation_name,
)


@pytest.mark.parametrize(
    "dataset,expectation_name,index,sub_index,expected_output",
    [
        (
            {"dataset_name": "i_am_a_dataset"},
            "expect_things",
            1,
            None,
            "i_am_a_dataset",
        ),
        ({}, "expect_things", 1, None, "expect_things_dataset_1"),
        ({}, "expect_things", 1, 2, "expect_things_dataset_1_2"),
    ],
)
def test_generate_table_name_with_expectation(
    dataset: dict,
    expectation_name: str,
    expected_output: str,
    index: int,
    sub_index: int | None,
):
    assert (
        generate_test_table_name_with_expectation_name(
            dataset=dataset,
            expectation_type=expectation_name,
            index=index,
            sub_index=sub_index,
        )
        == expected_output
    )
