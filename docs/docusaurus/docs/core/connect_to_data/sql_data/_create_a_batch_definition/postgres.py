"""
To run this test locally, run:
1. Activate docker.
2. From the repo root dir, activate the postgresql database docker container:

pytest  --postgresql --docs-tests -k "create_a_datasource_postgres" tests/integration/test_script_runner.py
"""

from tests.integration.db.taxi_data_utils import load_data_into_test_database

# add test_data to database for testing
load_data_into_test_database(
    table_name="postgres_taxi_data",
    csv_path="./data/yellow_tripdata_sample_2019-01.csv",
    connection_string="postgresql+psycopg2://postgres:@localhost/test_ci",
)

import great_expectations as gx

context = gx.get_context()

datasource_name = "my_new_datasource"
# You only need to define one of these:
my_connection_string = (
    "postgresql+psycopg2://${USERNAME}:${PASSWORD}@<host>:<port>/<database>"
)
my_connection_string = "${POSTGRESQL_CONNECTION_STRING}"

data_source = context.data_sources.add_postgres(
    name=datasource_name, connection_string=my_connection_string
)
print(context.list_datasources())

data_asset = data_source.add_table_asset(
    table_name="postgres_taxi_data", name="taxi_asset"
)
print(data_source.assets)

batch_definition = data_asset.add_batch_definition_whole_table(
    name="taxi_data_full_table"
)
batch_definition.get_batch().head()
