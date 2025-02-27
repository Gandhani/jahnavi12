---
title: Manage credentials
toc_min_heading_level: 2
toc_max_heading_level: 2
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

import InProgress from '../_core_components/_in_progress.md'

To access a deployment environment or a data storage system you must provide your access credentials. These access credentials must be stored securely outside of version control. With GX 1.0 you can store you access credentials as environment variables, in a YAML file that exists outside of version control, or in a third-party secrets manager. GX 1.0 supports the AWS Secrets Manager, Google Cloud Secret Manager, and Azure Key Vault secrets managers. 

## Environment variables

1. To store your database password and connection string as environment variables, run ``export ENV_VAR_NAME=env_var_value`` in a terminal or add the commands to your ``~/.bashrc`` file. For example:

    ```bash title="Terminal" name="docs/docusaurus/docs/oss/guides/setup/configuring_data_contexts/how_to_configure_credentials.py export_env_vars"
    ```

2. Run the following code to use the `connection_string` parameter values when you add a `datasource` to a Data Context:

    ```python title="Python" name="docs/docusaurus/docs/oss/guides/setup/configuring_data_contexts/how_to_configure_credentials.py add_credentials_as_connection_string"
    ```

## YAML file

YAML files make variables more visible, are easier to edit, and allow for modularization. For example, you can create a YAML file for development and testing and another for production.

The default ``config_variables.yml`` file located at ``great_expectations/uncommitted/config_variables.yml`` applies to deployments using ``FileSystemDataContexts``.

1. Save your access credentials or the database connection string to ``great_expectations/uncommitted/config_variables.yml``. For example:

    ```yaml title="YAML" name="docs/docusaurus/docs/oss/guides/setup/configuring_data_contexts/how_to_configure_credentials.py config_variables_yaml"
    ```
    To store values that include the dollar sign character ``$``, escape them using a backslash ``\`` to avoid substitution issues. For example, in the previous example for Postgres credentials you'd set ``password: pa\$sword`` if your password is ``pa$sword``. You can also have multiple substitutions for the same item. For example ``database_string: ${USER}:${PASSWORD}@${HOST}:${PORT}/${DATABASE}``.


2. Run the following code to use the `connection_string` parameter values when you add a `datasource` to a Data Context:

    ```python title="Python" name="docs/docusaurus/docs/oss/guides/setup/configuring_data_contexts/how_to_configure_credentials.py add_credential_from_yml"
    ```

## Secrets manager

GX 1.0 supports the AWS Secrets Manager, Google Cloud Secret Manager, and Azure Key Vault secrets managers.

<Tabs
  queryString="secrets_manager"
  groupId="manage-credentials"
  defaultValue='aws'
  values={[
  {label: 'AWS Secrets Manager', value:'aws'},
  {label: 'Google Cloud Secret Manager', value:'gcp'},
  {label: 'Azure Key Vault', value:'azure'},
  ]}>
<TabItem value="aws">

Configure your Great Expectations project to substitute variables from the AWS Secrets Manager. Secrets store substitution uses the configurations from your ``config_variables.yml`` file after all other types of substitution are applied with environment variables.

Secrets store substitution uses keywords and retrieves secrets from the secrets store for values starting with ``secret|arn:aws:secretsmanager``. If the values you provide don't match the keywords, the values aren't substituted.

1. Optional. Run the following code to install the ``great_expectations`` package with the ``aws_secrets`` requirement:

    ```bash
    pip install 'great_expectations[aws_secrets]'
    ```

2. Provide an arn of the secret to substitute your value by a secret in AWS Secrets Manager. For example:

    ``secret|arn:aws:secretsmanager:123456789012:secret:my_secret-1zAyu6``

    The last seven characters of the arn are automatically generated by AWS and are not mandatory to retrieve the secret. For example, ``secret|arn:aws:secretsmanager:region-name-1:123456789012:secret:my_secret`` retrieves the same secret. The latest version of the secret is returned by default.

3. Optional. To get a specific version of the secret you want to retrieve, specify its version UUID. For example,``secret|arn:aws:secretsmanager:region-name-1:123456789012:secret:my_secret:00000000-0000-0000-0000-000000000000``.

4. Optional. To retrieve a specific secret value for a JSON string, use ``secret|arn:aws:secretsmanager:region-name-1:123456789012:secret:my_secret|key`` or 
``secret|arn:aws:secretsmanager:region-name-1:123456789012:secret:my_secret:00000000-0000-0000-0000-000000000000|key``.

5. Save your access credentials or the database connection string to ``great_expectations/uncommitted/config_variables.yml``. For example:

    ```yaml
    # We can configure a single connection string
    my_aws_creds:  secret|arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:dev_db_credentials|connection_string

    # Or each component of the connection string separately
    drivername: secret|arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:dev_db_credentials|drivername
    host: secret|arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:dev_db_credentials|host
    port: secret|arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:dev_db_credentials|port
    username: secret|arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:dev_db_credentials|username
    password: secret|arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:dev_db_credentials|password
    database: secret|arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:dev_db_credentials|database
    ```

6. Run the following code to use the `connection_string` parameter values when you add a `datasource` to a Data Context:

    ```python 
    # We can use a single connection string
    pg_datasource = context.data_sources.add_or_update_sql(
        name="my_postgres_db", connection_string="${my_aws_creds}"
    )

    # Or each component of the connection string separately
    pg_datasource = context.data_sources.add_or_update_sql(
        name="my_postgres_db", connection_string="${drivername}://${username}:${password}@${host}:${port}/${database}"
    )
    ```

</TabItem>
<TabItem value="gcp">

Configure your Great Expectations project to substitute variables from the Google Cloud Secret Manager. Secrets store substitution uses the configurations from your ``config_variables.yml`` file after all other types of substitution are applied with environment variables.

Secrets store substitution uses keywords and retrieves secrets from the secrets store for values matching the following regex ``^secret\|projects\/[a-z0-9\_\-]{6,30}\/secrets``. If the values you provide don't match the keywords, the values aren't substituted.

1. Optional. Run the following code to install the ``great_expectations`` package with the ``gcp`` requirement:

    ```bash
    pip install 'great_expectations[gcp]'
    ```

2. Provide the name of the secret you want to substitute in GCP Secret Manager. For example, ``secret|projects/project_id/secrets/my_secret``. 

    The latest version of the secret is returned by default.

3. Optional. To get a specific version of the secret, specify its version id. For example, ``secret|projects/project_id/secrets/my_secret/versions/1``.

4. Optional. To retrieve a specific secret value for a JSON string, use ``secret|projects/project_id/secrets/my_secret|key`` or ``secret|projects/project_id/secrets/my_secret/versions/1|key``.

5. Save your access credentials or the database connection string to ``great_expectations/uncommitted/config_variables.yml``. For example:

    ```yaml
    # We can configure a single connection string
    my_gcp_creds: secret|projects/${PROJECT_ID}/secrets/dev_db_credentials|connection_string

    # Or each component of the connection string separately
    drivername: secret|projects/${PROJECT_ID}/secrets/PROD_DB_CREDENTIALS_DRIVERNAME
    host: secret|projects/${PROJECT_ID}/secrets/PROD_DB_CREDENTIALS_HOST
    port: secret|projects/${PROJECT_ID}/secrets/PROD_DB_CREDENTIALS_PORT
    username: secret|projects/${PROJECT_ID}/secrets/PROD_DB_CREDENTIALS_USERNAME
    password: secret|projects/${PROJECT_ID}/secrets/PROD_DB_CREDENTIALS_PASSWORD
    database: secret|projects/${PROJECT_ID}/secrets/PROD_DB_CREDENTIALS_DATABASE
    ```

6. Run the following code to use the `connection_string` parameter values when you add a `datasource` to a Data Context:

    ```python 
    # We can use a single connection string 
    pg_datasource = context.data_sources.add_or_update_sql(
        name="my_postgres_db", connection_string="${my_gcp_creds}"
    )

    # Or each component of the connection string separately
    pg_datasource = context.data_sources.add_or_update_sql(
        name="my_postgres_db", connection_string="${drivername}://${username}:${password}@${host}:${port}/${database}"
    )
    ```

</TabItem>
<TabItem value="azure">

Configure your Great Expectations project to substitute variables from the Azure Key Vault. Secrets store substitution uses the configurations from your ``config_variables.yml`` file after all other types of substitution are applied with environment variables.

Secrets store substitution uses keywords and retrieves secrets from the secrets store for values matching the following regex ``^secret\|https:\/\/[a-zA-Z0-9\-]{3,24}\.vault\.azure\.net``. If the values you provide don't match the keywords, the values aren't substituted.

1. Optional. Run the following code to install the ``great_expectations`` package with the ``azure_secrets`` requirement:

    ```bash
    pip install 'great_expectations[azure_secrets]'
    ```

2. Provide the name of the secret you want to substitute in Azure Key Vault. For example, ``secret|https://my-vault-name.vault.azure.net/secrets/my-secret``. 

    The latest version of the secret is returned by default.

3. Optional. To get a specific version of the secret, specify its version id (32 lowercase alphanumeric characters). For example, ``secret|https://my-vault-name.vault.azure.net/secrets/my-secret/a0b00aba001aaab10b111001100a11ab``.

4. Optional. To retrieve a specific secret value for a JSON string, use ``secret|https://my-vault-name.vault.azure.net/secrets/my-secret|key`` or ``secret|https://my-vault-name.vault.azure.net/secrets/my-secret/a0b00aba001aaab10b111001100a11ab|key``.

5. Save your access credentials or the database connection string to ``great_expectations/uncommitted/config_variables.yml``. For example:

    ```yaml
    # We can configure a single connection string
    my_abs_creds: secret|https://${VAULT_NAME}.vault.azure.net/secrets/dev_db_credentials|connection_string

    # Or each component of the connection string separately
    drivername: secret|https://${VAULT_NAME}.vault.azure.net/secrets/dev_db_credentials|host
    host: secret|https://${VAULT_NAME}.vault.azure.net/secrets/dev_db_credentials|host
    port: secret|https://${VAULT_NAME}.vault.azure.net/secrets/dev_db_credentials|port
    username: secret|https://${VAULT_NAME}.vault.azure.net/secrets/dev_db_credentials|username
    password: secret|https://${VAULT_NAME}.vault.azure.net/secrets/dev_db_credentials|password
    database: secret|https://${VAULT_NAME}.vault.azure.net/secrets/dev_db_credentials|database
    ```

6. Run the following code to use the `connection_string` parameter values when you add a `datasource` to a Data Context:

    ```python 
    # We can use a single connection string
    pg_datasource = context.data_sources.add_or_update_sql(
        name="my_postgres_db", connection_string="${my_azure_creds}"
    )

    # Or each component of the connection string separately
    pg_datasource = context.data_sources.add_or_update_sql(
        name="my_postgres_db", connection_string="${drivername}://${username}:${password}@${host}:${port}/${database}"
    )
    ```

</TabItem>
</Tabs>

## Next steps

- [Connect to data](/core/manage_and_access_data/manage_and_access_data.md)