import pathlib

import pytest
from pytest import TempPathFactory

# apply markers to entire test module
pytestmark = [pytest.mark.integration]

from great_expectations import get_context
from great_expectations.experimental.datasources.config import GxConfig


@pytest.fixture
def zep_config_dict() -> dict:
    return {
        "datasources": {
            "my_sql_ds": {
                "connection_string": "sqlite:///:memory:",
                "name": "my_sql_ds",
                "type": "sql",
                "assets": {
                    "my_table_asset": {
                        "name": "my_table_asset",
                        "table_name": "my_table",
                        "type": "table",
                        "column_splitter": {
                            "column_name": "my_column",
                            "method_name": "split_on_year_and_month",
                            "name": "y_m_splitter",
                            "param_names": ["year", "month"],
                        },
                        "order_by": [
                            {"metadata_key": "year"},
                            {"metadata_key": "month", "reverse": True},
                        ],
                    },
                },
            }
        }
    }


@pytest.fixture
def zep_only_config(zep_config_dict: dict) -> GxConfig:
    zep_config = GxConfig.parse_obj(zep_config_dict)
    assert zep_config.datasources
    return zep_config


@pytest.fixture
def zep_yaml_config_file(
    tmp_path: pathlib.Path, zep_only_config: GxConfig
) -> pathlib.Path:
    """
    Dump the provided GxConfig to a temporary path. File is removed during test teardown.
    """
    config_file_path = tmp_path / "great_expectations" / "zep_config.yaml"
    config_file_path.parent.mkdir()

    assert config_file_path.exists() is False

    zep_only_config.yaml(config_file_path)
    assert config_file_path.exists() is True
    return config_file_path


def test_load_an_existing_config(
    zep_yaml_config_file: pathlib.Path, zep_only_config: GxConfig
):
    context = get_context(
        context_root_dir=zep_yaml_config_file.parent, cloud_mode=False
    )

    assert context.zep_config == zep_only_config


if __name__ == "__main__":
    pytest.main([__file__, "-vv"])
