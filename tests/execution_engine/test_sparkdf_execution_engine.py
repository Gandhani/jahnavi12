import pytest
import datetime
import random
import os
import numpy as np
import pandas as pd
from great_expectations.core.batch import Batch

import great_expectations.exceptions.exceptions as ge_exceptions
from great_expectations.data_context.util import file_relative_path
from great_expectations.execution_environment.types.batch_spec import RuntimeDataBatchSpec, PathBatchSpec
from great_expectations.execution_engine import (
    SparkDFExecutionEngine,
)

try:
    import pyspark.sql.functions as F
    from pyspark.sql.types import IntegerType, StringType
except ImportError:
    F = None
    SparkSession = None


def _build_spark_engine(spark_session, df):
    df = spark_session.createDataFrame(
        [
            tuple(
                None if isinstance(x, (float, int)) and np.isnan(x) else x
                for x in record.tolist()
            )
            for record in df.to_records(index=False)
        ],
        df.columns.tolist(),
    )
    batch = Batch(data=df)
    engine = SparkDFExecutionEngine(batch_data_dict={batch.id: batch.data})
    return engine


@pytest.fixture
def test_sparkdf(spark_session):
    def generate_ascending_list_of_datetimes(
        k,
        start_date=datetime.date(2020, 1, 1),
        end_date=datetime.date(2020, 12, 31)
    ):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day)
        days_between_dates = (end_date - start_date).total_seconds()
        datetime_list = [start_time + datetime.timedelta(seconds=random.randrange(days_between_dates)) for i in range(k)]
        datetime_list.sort()
        return datetime_list

    k = 120
    random.seed(1)
    timestamp_list = generate_ascending_list_of_datetimes(k, end_date=datetime.date(2020,1,31))
    date_list = [datetime.date(ts.year, ts.month, ts.day) for ts in timestamp_list]

    batch_ids = [random.randint(0, 10) for i in range(k)]
    batch_ids.sort()
    session_ids = [random.randint(2, 60) for i in range(k)]
    session_ids.sort()
    session_ids = [i-random.randint(0, 2) for i in session_ids]

    spark_df = spark_session.createDataFrame(data=pd.DataFrame({
       "id": range(k),
       "batch_id": batch_ids,
       "date": date_list,
       "y": [d.year for d in date_list],
       "m": [d.month for d in date_list],
       "d": [d.day for d in date_list],
       "timestamp": timestamp_list,
       "session_ids": session_ids,
       "event_type": [random.choice(["start", "stop", "continue"]) for i in range(k)],
       "favorite_color": ["#"+"".join([random.choice(list("0123456789ABCDEF")) for j in range(6)]) for i in range(k)]
    }))
    spark_df = spark_df.withColumn("timestamp", F.col("timestamp").cast(IntegerType()).cast(StringType()))
    return spark_df


def test_basic_setup(spark_session):
    pd_df = pd.DataFrame({"x": range(10)})
    df = spark_session.createDataFrame(
        [
            tuple(
                None if isinstance(x, (float, int)) and np.isnan(x) else x
                for x in record.tolist()
            )
            for record in pd_df.to_records(index=False)
        ],
        pd_df.columns.tolist(),
    )
    batch_data = SparkDFExecutionEngine().get_batch_data(
        batch_spec=RuntimeDataBatchSpec(
            batch_data=df,
            data_asset_name="DATA_ASSET",
        )
    )
    assert batch_data is not None


def test_get_batch_data(test_sparkdf):
    test_sparkdf = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
        batch_data=test_sparkdf,
        data_asset_name="DATA_ASSET"
    ))
    assert test_sparkdf.count() == 120
    assert len(test_sparkdf.columns) == 10


def test_get_batch_empty_splitter(test_folder_connection_path):
    # reader_method not configured because spark will configure own reader by default
    test_sparkdf = SparkDFExecutionEngine().get_batch_data(
        PathBatchSpec(
            path=os.path.join(test_folder_connection_path, "test.csv"),
            splitter_method=None
        )
    )
    assert test_sparkdf.count() == 6
    assert len(test_sparkdf.columns) == 3


def test_get_batch_with_split_on_whole_table_filesystem(test_folder_connection_path):
    # reader_method not configured because spark will configure own reader by default
    test_sparkdf = SparkDFExecutionEngine().get_batch_data(
        PathBatchSpec(
            path=os.path.join(test_folder_connection_path, "test.csv"),
            splitter_method="_split_on_whole_table"
        )
    )
    assert test_sparkdf.count() == 6
    assert len(test_sparkdf.columns) == 3


def test_get_batch_with_split_on_whole_table(test_sparkdf):
    db_file = file_relative_path(
        __file__, os.path.join("test_sets", "test_cases_for_sql_data_connector.db"),
    )

    test_sparkdf = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
        batch_data=test_sparkdf,
        splitter_method="_split_on_whole_table"
    ))
    assert test_sparkdf.count() == 120
    assert len(test_sparkdf.columns) == 10


def test_get_batch_with_split_on_column_value(test_sparkdf):
    split_df = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
        batch_data=test_sparkdf,
        splitter_method="_split_on_column_value",
        splitter_kwargs={
            "column_name": "batch_id",
            "partition_definition": {
                "batch_id": 2
            }
        }
    ))
    assert test_sparkdf.count() == 120
    assert len(test_sparkdf.columns) == 10
    collected = split_df.collect()
    for val in collected:
        assert val.batch_id == 2

    split_df = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
        batch_data=test_sparkdf,
        splitter_method="_split_on_column_value",
        splitter_kwargs={
            "column_name": "date",
            "partition_definition": {
                "date": datetime.date(2020, 1, 30)
            }
        }
    ))
    assert split_df.count() == 3
    assert len(split_df.columns) == 10


def test_get_batch_with_split_on_converted_datetime(test_sparkdf):
    split_df = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
        batch_data=test_sparkdf,
        splitter_method="_split_on_converted_datetime",
        splitter_kwargs={
            "column_name": "timestamp",
            "partition_definition": {
                "timestamp": "2020-01-03"
            }
        }
    ))
    assert split_df.count() == 2
    assert len(split_df.columns) == 10


def test_get_batch_with_split_on_divided_integer(test_sparkdf):
    split_df = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
        batch_data=test_sparkdf,
        splitter_method="_split_on_divided_integer",
        splitter_kwargs={
            "column_name": "id",
            "divisor": 10,
            "partition_definition": {
                "id": 5
            }
        }
    ))
    assert split_df.count() == 10
    assert len(split_df.columns) == 10
    max_result = split_df.select([F.max("id")])
    assert max_result.collect()[0]['max(id)'] == 59
    min_result = split_df.select([F.min("id")])
    assert min_result.collect()[0]['min(id)'] == 50


def test_get_batch_with_split_on_mod_integer(test_sparkdf):
    split_df = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
        batch_data=test_sparkdf,
        splitter_method="_split_on_mod_integer",
        splitter_kwargs={
            "column_name": "id",
            "mod": 10,
            "partition_definition": {
                "id": 5
            }
        }
    ))

    assert split_df.count() == 12
    assert len(split_df.columns) == 10
    max_result = split_df.select([F.max("id")])
    assert max_result.collect()[0]['max(id)'] == 115
    min_result = split_df.select([F.min("id")])
    assert min_result.collect()[0]['min(id)'] == 5


def test_get_batch_with_split_on_multi_column_values(test_sparkdf):
    split_df = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
        batch_data=test_sparkdf,
        splitter_method="_split_on_multi_column_values",
        splitter_kwargs={
            "column_names": ["y", "m", "d"],
            "partition_definition": {
                "y": 2020,
                "m": 1,
                "d": 5,
            }
        },
    ))
    assert split_df.count() == 4
    assert len(split_df.columns) == 10
    collected = split_df.collect()
    for val in collected:
        assert val.date == datetime.date(2020, 1, 5)

    with pytest.raises(ValueError):
        split_df = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
            batch_data=test_sparkdf,
            splitter_method="_split_on_multi_column_values",
            splitter_kwargs={
                "column_names": ["I", "dont", "exist"],
                "partition_definition": {
                    "y": 2020,
                    "m": 1,
                    "d": 5,
                }
            },
        ))


def test_get_batch_with_split_on_hashed_column_incorrect_hash_function_name(test_sparkdf):
    with pytest.raises(ge_exceptions.ExecutionEngineError):
        split_df = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
            batch_data=test_sparkdf,
            splitter_method="_split_on_hashed_column",
            splitter_kwargs={
                "column_name": "favorite_color",
                "hash_digits": 1,
                "hash_function_name": "I_wont_work",
                "partition_definition": {
                    "hash_value": "a",
                }
            }
        ))


def test_get_batch_with_split_on_hashed_column(test_sparkdf):
    split_df = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
        batch_data=test_sparkdf,
        splitter_method="_split_on_hashed_column",
        splitter_kwargs={
            "column_name": "favorite_color",
            "hash_digits": 1,
            "hash_function_name": "sha256",
            "partition_definition": {
                "hash_value": "a",
            }
        }
    ))
    assert split_df.count() == 8
    assert len(split_df.columns) == 10


# ### Sampling methods ###
def test_get_batch_empty_sampler(test_sparkdf):
    sampled_df = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
        batch_data=test_sparkdf,
        sampling_method=None
    ))
    assert sampled_df.count() == 120
    assert len(sampled_df.columns) == 10


def test_sample_using_random(test_sparkdf):
    sampled_df = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
        batch_data=test_sparkdf,
        sampling_method="_sample_using_random"
    ))
    assert sampled_df.count() == 14
    assert len(sampled_df.columns) == 10


def test_sample_using_mod(test_sparkdf):
    sampled_df = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
        batch_data=test_sparkdf,
        sampling_method="_sample_using_mod",
        sampling_kwargs={
            "column_name": "id",
            "mod": 5,
            "value": 4,
        }
    ))
    assert sampled_df.count() == 24
    assert len(sampled_df.columns) == 10


def test_sample_using_a_list(test_sparkdf):
    sampled_df = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
        batch_data=test_sparkdf,
        sampling_method="_sample_using_a_list",
        sampling_kwargs={
            "column_name": "id",
            "value_list": [3, 5, 7, 11],
        }
    ))
    assert sampled_df.count() == 4
    assert len(sampled_df.columns) == 10


def test_sample_using_md5_wrong_hash_function_name(test_sparkdf):
    with pytest.raises(ge_exceptions.ExecutionEngineError):
        sampled_df = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
        batch_data=test_sparkdf,
        sampling_method="_sample_using_hash",
        sampling_kwargs={
            "column_name": "date",
            "hash_function_name": "I_wont_work",
            }
        ))

def test_sample_using_md5(test_sparkdf):
    sampled_df = SparkDFExecutionEngine().get_batch_data(RuntimeDataBatchSpec(
        batch_data=test_sparkdf,
        sampling_method="_sample_using_hash",
        sampling_kwargs={
            "column_name": "date",
            "hash_function_name": "md5",
        }
    ))
    assert sampled_df.count() == 10
    assert len(sampled_df.columns) == 10

    collected = sampled_df.collect()
    for val in collected:
        assert val.date in [datetime.date(2020, 1, 15), datetime.date(2020, 1, 29)]
