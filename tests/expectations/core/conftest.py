import os

import pandas as pd
import pytest

from great_expectations_v1.data_context.util import file_relative_path


@pytest.fixture(scope="module")
def titanic_df() -> pd.DataFrame:
    path = file_relative_path(
        __file__,
        os.path.join(  # noqa: PTH118
            "..",
            "..",
            "test_sets",
            "Titanic.csv",
        ),
    )
    df = pd.read_csv(path)
    return df
