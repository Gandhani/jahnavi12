from time_series_expectations.expectations.expect_batch_volume_to_match_prophet_date_model import (
    ExpectBatchVolumeToMatchProphetDateModel,
)
from time_series_expectations.expectations.expect_column_max_to_match_prophet_date_model import (
    ExpectColumnMaxToMatchProphetDateModel,
)
from time_series_expectations.expectations.expect_column_pair_values_to_match_prophet_date_model import (
    ExpectColumnPairValuesToMatchProphetDateModel,
)


def test_ExpectColumnPairValuesToMatchProphetDateModel():
    ExpectColumnPairValuesToMatchProphetDateModel().run_diagnostics()


def test_ExpectBatchVolumeToMatchProphetDateModel():
    ExpectBatchVolumeToMatchProphetDateModel().run_diagnostics()


def test_ExpectColumnMaxToMatchProphetDateModel():
    ExpectColumnMaxToMatchProphetDateModel().run_diagnostics()
