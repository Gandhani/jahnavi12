"""
This is a template for creating custom ColumnMapExpectations.
For detailed instructions on how to use it, please see:
    https://docs.greatexpectations.io/docs/guides/expectations/creating_custom_expectations/how_to_create_custom_column_map_expectations
"""

import dataprofiler as dp
import json
import numpy as np
# remove extra tf loggin
import tensorflow as tf
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.expectation import ColumnMapExpectation
from great_expectations.expectations.metrics import (
    ColumnMapMetricProvider,
    column_condition_partial,
)


class ColumnValuesProbabilisticallyMatchDataLabel(ColumnMapMetricProvider):
    """MetricProvider Class for Data Label Probability greater than \
    or equal to the user-specified data_type"""
    
    # This is the id string that will be used to reference your metric.
    condition_metric_name = "column_values.are_probibalistically_greater_or_equal_to_data_type"

    condition_value_keys = ("data_type",)

    # This method implements the core logic for the PandasExecutionEngine
    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column, data_type, **kwargs):
        """
        Implement the yes/no question for the expectation
        """
        labeler = dp.DataLabeler(labeler_type='structured')
        try:
            preds = labeler.predict(column, predict_options={"show_confidences": True})
        except:
            preds = None
        return preds["conf"] == data_type


class ExpectColumnValuesToProbabilisticallyMatchDataLabel(ColumnMapExpectation):
    """
    This function builds upon the custom column map expectations of Great Expectations. This function asks the question a yes/no question of each row in the user-specified column; namely, does the confidence data_type provided by the DataProfiler model exceed the user-specified data_type.

    :param: column,  
    :param: data_label,
    :param: data_type

    df.expect_column_values_to_probabilistically_match_data_label(
        column,
        data_label=<>,
        data_type=float(0<=1)
    )
    """

    examples = [
        {
            "data": {
                "OPEID6": ['1002', '1052', '25034'],
                "INSTNM": ['Alabama A & M University',
                    'University of Alabama at Birmingham', 'Amridge University'],
                "ZIP": ['35762', '35294-0110', '36117-3553'],
                "ACCREDAGENCY": ['Southern Association of Colleges and Schools Commission on Colleges',
                    'Southern Association of Colleges and Schools Commission on Colleges',
                    'Southern Association of Colleges and Schools Commission on Colleges'],
                "INSTURL": ['www.aamu.edu/', 'https://www.uab.edu',
                    'www.amridgeuniversity.edu'],
                "NPCURL": ['www.aamu.edu/admissions-aid/tuition-fees/net-price-calculator.html',
                    'https://uab.studentaidcalculator.com/survey.aspx',
                    'www2.amridgeuniversity.edu:9091/'],
                "LATITUDE": ['34.783368', '33.505697', '32.362609'],
                "LONGITUDE": ['-86.568502', '-86.799345', '-86.17401'],
                "RELAFFIL": ['NULL', 'NULL', '74'],
                "DEATH_YR2_RT": ['PrivacySuppressed', 'PrivacySuppressed', 'PrivacySuppressed'],
                "SEARCH_STRING": ['Alabama A & M University AAMU',
                    'University of Alabama at Birmingham ',
                    'Amridge University Southern Christian University  Regions University']
            },
            "tests": [
                {
                    "title": "positive_test_with_column_one",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {"column": "OPEID6",  "data_type": .65},
                    "out": {
                        "success": True,
                        "unexpected_index_list": [3],
                        "unexpected_list": [4, 5],
                    },
                },
            ],
        }
    ]

    # This is the id string of the Metric used by this Expectation.
    # For most Expectations, it will be the same as the `condition_metric_name` defined in your Metric class above.
    map_metric = "column_values.are_probibalistically_greater_or_equal_to_data_type"

    # This is a list of parameter names that can affect whether the Expectation evaluates to True or False
    success_keys = ("data_type", "mostly",)

    # This dictionary contains default values for any parameters that should have default values
    default_kwarg_values = {}

    # This object contains metadata for display in the public Gallery
    library_metadata = {
        "maturity": "experimental",  # "concept_only", "experimental", "beta", or "production"
        "tags": ["dataprofiler"],  # Tags for this Expectation in the Gallery
        "contributors": [  # Github handles for all contributors to this Expectation.
            "@taylorfturner",  # Don't forget to add your github handle here!
        ],
    }

if __name__ == "__main__":
    diagnostics_report = ExpectColumnValuesToProbabilisticallyMatchDataLabel().run_diagnostics()
    print(json.dumps(diagnostics_report, indent=2))
