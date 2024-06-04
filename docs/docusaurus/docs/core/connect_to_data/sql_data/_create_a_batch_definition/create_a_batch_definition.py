"""
To run this test locally, run:
1. Activate docker.
2. From the repo root dir, activate the postgresql database docker container:

pytest  --postgresql --docs-tests -k "create_a_batch_definition_postgres" tests/integration/test_script_runner.py
"""

# This section is setup for the environment used in the example script.
import great_expectations as gx
from tests.integration.db.taxi_data_utils import load_data_into_test_database

# add test_data to database for testing
load_data_into_test_database(
    table_name="postgres_taxi_data",
    csv_path="./data/yellow_tripdata_sample_2020-01.csv",
    connection_string="postgresql+psycopg2://postgres:@localhost/test_ci",
)

# Set up the Data Source and a Data Asset
context = gx.get_context()

datasource_name = "my_datasource"
my_connection_string = "${POSTGRESQL_CONNECTION_STRING}"

data_source = context.data_sources.add_postgres(
    name=datasource_name, connection_string=my_connection_string
)

asset_name = "MY_TABLE_ASSET"
database_table_name = "postgres_taxi_data"
table_data_asset = data_source.add_table_asset(
    table_name=database_table_name, name=asset_name
)

# The example starts here
import great_expectations as gx

context = gx.get_context()

# Retrieve a Data Source
datasource_name = "my_datasource"
data_source = context.get_datasource(datasource_name)

# Get the Data Asset from the Data Source
asset_name = "MY_TABLE_ASSET"
data_asset = data_source.get_asset(asset_name)

# Example of a full table Batch Definition
bd_name = "FULL_TABLE"
full_table_batch_definition = data_asset.add_batch_definition_whole_table(name=bd_name)

# Verify that the Batch Definition is valid
full_table_batch = full_table_batch_definition.get_batch()
full_table_batch.head()


bd_name = "DAILY"
date_column = "pickup_datetime"
daily_table_batch_definition = data_asset.add_batch_definition_daily(
    name=bd_name, column=date_column
)

daily_table_batch = daily_table_batch_definition.get_batch()
daily_table_batch.head()
