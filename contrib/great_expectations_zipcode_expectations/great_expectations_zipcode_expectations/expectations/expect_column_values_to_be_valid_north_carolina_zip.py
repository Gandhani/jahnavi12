from __future__ import annotations

import zipcodes

from great_expectations.execution_engine import PandasExecutionEngine
from great_expectations.expectations.expectation import ColumnMapExpectation
from great_expectations.expectations.metrics import (
    ColumnMapMetricProvider,
    column_condition_partial,
)


def is_valid_north_carolina_zip(zip: str):
    list_of_dicts_of_north_carolina_zips = zipcodes.filter_by(state="NC")
    list_of_north_carolina_zips = [
        d["zip_code"] for d in list_of_dicts_of_north_carolina_zips
    ]
    if len(zip) > 10:
        return False
    elif type(zip) != str:  # noqa: E721
        return False
    elif zip in list_of_north_carolina_zips:
        return True
    else:
        return False


# This class defines a Metric to support your Expectation.
# For most ColumnMapExpectations, the main business logic for calculation will live in this class.
class ColumnValuesToBeValidNorthCarolinaZip(ColumnMapMetricProvider):
    # This is the id string that will be used to reference your metric.
    condition_metric_name = "column_values.valid_north_carolina_zip"

    # This method implements the core logic for the PandasExecutionEngine
    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column, **kwargs):
        return column.apply(lambda x: is_valid_north_carolina_zip(x))

    # This method defines the business logic for evaluating your metric when using a SqlAlchemyExecutionEngine
    # @column_condition_partial(engine=SqlAlchemyExecutionEngine)
    # def _sqlalchemy(cls, column, _dialect, **kwargs):
    #     raise NotImplementedError

    # This method defines the business logic for evaluating your metric when using a SparkDFExecutionEngine
    # @column_condition_partial(engine=SparkDFExecutionEngine)
    # def _spark(cls, column, **kwargs):
    #     raise NotImplementedError


# This class defines the Expectation itself
class ExpectColumnValuesToBeValidNorthCarolinaZip(ColumnMapExpectation):
    """Expect values in this column to be valid North Carolina zipcodes.

    See https://pypi.org/project/zipcodes/ for more information.
    """

    # These examples will be shown in the public gallery.
    # They will also be executed as unit tests for your Expectation.
    examples = [
        {
            "data": {
                "valid_north_carolina_zip": ["27248", "27612", "28077", "28901"],
                "invalid_north_carolina_zip": ["-10000", "1234", "99999", "25487"],
            },
            "tests": [
                {
                    "title": "basic_positive_test",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {"column": "valid_north_carolina_zip"},
                    "out": {"success": True},
                },
                {
                    "title": "basic_negative_test",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {"column": "invalid_north_carolina_zip"},
                    "out": {"success": False},
                },
            ],
        }
    ]

    # This is the id string of the Metric used by this Expectation.
    # For most Expectations, it will be the same as the `condition_metric_name` defined in your Metric class above.
    map_metric = "column_values.valid_north_carolina_zip"

    # This is a list of parameter names that can affect whether the Expectation evaluates to True or False
    success_keys = ("mostly",)

    # This dictionary contains default values for any parameters that should have default values
    default_kwarg_values = {}

    # This object contains metadata for display in the public Gallery
    library_metadata = {
        "maturity": "experimental",  # "experimental", "beta", or "production"
        "tags": [
            "hackathon",
            "typed-entities",
        ],  # Tags for this Expectation in the Gallery
        "contributors": [  # Github handles for all contributors to this Expectation.
            "@luismdiaz01",
            "@derekma73",  # Don't forget to add your github handle here!
        ],
        "requirements": ["zipcodes"],
    }


if __name__ == "__main__":
    ExpectColumnValuesToBeValidNorthCarolinaZip().print_diagnostic_checklist()
