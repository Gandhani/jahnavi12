import pytest

import great_expectations as ge


def test_validate_non_dataset(file_data_asset, empty_expectations_config):
    with pytest.raises(ValueError, match=r"The validate util method only supports dataset validations"):
        ge.validate(file_data_asset, empty_expectations_config, data_asset_type=ge.data_asset.FileDataAsset)


def test_validate_dataset(dataset, basic_expectations_config):
    res = ge.validate(dataset, basic_expectations_config)
    assert res["success"] == True
    assert res["statistics"]["evaluated_expectations"] == 4
    if isinstance(dataset, ge.dataset.PandasDataset):
        res = ge.validate(dataset, basic_expectations_config,  data_asset_type=ge.dataset.PandasDataset)
        assert res["success"] == True
        assert res["statistics"]["evaluated_expectations"] == 4
        with pytest.raises(ValueError, match=r"The validate util method only supports validation for subtypes of the provided data_asset_type"):
            ge.validate(dataset, basic_expectations_config,  data_asset_type=ge.dataset.SqlAlchemyDataset)

    elif isinstance(dataset, ge.dataset.SqlAlchemyDataset):
        res = ge.validate(dataset, basic_expectations_config,  data_asset_type=ge.dataset.SqlAlchemyDataset)
        assert res["success"] == True
        assert res["statistics"]["evaluated_expectations"] == 4
        with pytest.raises(ValueError, match=r"The validate util method only supports validation for subtypes of the provided data_asset_type"):
            ge.validate(dataset, basic_expectations_config,  data_asset_type=ge.dataset.PandasDataset)

    elif isinstance(dataset, ge.dataset.SparkDFDataset):
        res = ge.validate(dataset, basic_expectations_config, data_asset_type=ge.dataset.SparkDFDataset)
        assert res["success"] == True
        assert res["statistics"]["evaluated_expectations"] == 4
        with pytest.raises(ValueError, match=r"The validate util method only supports validation for subtypes of the provided data_asset_type"):
            ge.validate(dataset, basic_expectations_config,  data_asset_type=ge.dataset.PandasDataset)

def test_validate_using_data_context(dataset, data_context):
    # Before running, the data context should not have compiled parameters
    assert data_context._compiled == False
    res = ge.validate(dataset, data_asset_name="parameterized_expectations_config_fixture", data_context=data_context)

    # After handling a validation result registration, it should be
    assert data_context._compiled == True

    # And, we should have validated the right number of expectations from the context-provided config
    assert res["success"] == False
    assert res["statistics"]["evaluated_expectations"] == 2

    
def test_validate_invalid_parameters(dataset, basic_expectations_config, data_context):
    with pytest.raises(ValueError, match="Either an expectations config or a DataContext is required for validation."):
        ge.validate(dataset)