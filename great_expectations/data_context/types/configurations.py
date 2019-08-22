from six import string_types

from great_expectations.types import Config


class DataContextConfig(Config):
    _allowed_keys = set([
        "plugins_directory",
        "expectations_directory",
        "evaluation_parameter_store_name",
        "datasources",
        "stores",
        "data_docs",  # TODO: Rename this to sites, to remove a layer of extraneous nesting
    ])

    _required_keys = set([
        "plugins_directory",
        "expectations_directory",
        "evaluation_parameter_store_name",
        "datasources",
        "stores",
        "data_docs",
    ])

    _key_types = {
        "plugins_directory": string_types,
        "expectations_directory": string_types,
        "evaluation_parameter_store_name": string_types,
        "datasources": dict,
        "stores": dict,
        "data_docs": dict,
    }
