import pydantic

from great_expectations.compatibility.not_imported import (
    is_version_greater_or_equal,
)

if is_version_greater_or_equal(version=pydantic.VERSION, compare_version="2.0.0"):
    # from pydantic.v1 import BaseModel, Field, StrictStr
    from pydantic.v1 import *  # noqa: F403
    from pydantic.v1 import (
        AnyUrl,
        UrlError,
        error_wrappers,
        errors,
        generics,
        json,
        schema,
    )
    from pydantic.v1.generics import GenericModel
    from pydantic.v1.main import ModelMetaclass

    # from pydantic.v1 import Extra
else:
    # from pydantic import BaseModel, Field, StrictStr
    from pydantic import *  # noqa: F403

    # from pydantic import Extra


# from pydantic import StrictStr
# from pydantic.schema import default_ref_template

__all__ = [
    "ModelMetaclass",
    "errors",
    "generics",
    "error_wrappers",
    "GenericModel",
    "json",
    "schema",
    "AnyUrl",
    "UrlError",
]
