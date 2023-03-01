from __future__ import annotations

import copy
import dataclasses
import logging
from pprint import pformat as pf
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Dict,
    Generic,
    List,
    MutableMapping,
    Optional,
    Set,
    Type,
)

import pydantic
from typing_extensions import Literal

import great_expectations.exceptions as gx_exceptions
from great_expectations.core.batch_spec import PandasBatchSpec
from great_expectations.experimental.datasources.dynamic_pandas import (
    _generate_pandas_data_asset_models,
)
from great_expectations.experimental.datasources.interfaces import (
    Batch,
    BatchRequest,
    DataAsset,
    Datasource,
    _DataAssetT,
)
from great_expectations.experimental.datasources.sources import (
    DEFAULT_PANDAS_DATA_ASSET_NAME,
)

if TYPE_CHECKING:
    from great_expectations.execution_engine import PandasExecutionEngine
    from great_expectations.experimental.datasources.interfaces import (
        BatchRequestOptions,
    )
    from great_expectations.validator.validator import Validator

logger = logging.getLogger(__name__)


class PandasDatasourceError(Exception):
    pass


class _PandasDataAsset(DataAsset):
    _EXCLUDE_FROM_READER_OPTIONS: ClassVar[Set[str]] = {
        "name",
        "order_by",
        "type",
    }

    class Config:
        """
        Need to allow extra fields for the base type because pydantic will first create
        an instance of `_PandasDataAsset` before we select and create the more specific
        asset subtype.
        Each specific subtype should `forbid` extra fields.
        """

        extra = pydantic.Extra.allow

    def _get_reader_method(self) -> str:
        raise NotImplementedError(
            """One needs to explicitly provide "reader_method" for Pandas DataAsset extensions as temporary \
work-around, until "type" naming convention and method for obtaining 'reader_method' from it are established."""
        )

    def test_connection(self) -> None:
        pass

    def batch_request_options_template(
        self,
    ) -> BatchRequestOptions:
        return {}

    def get_batch_list_from_batch_request(
        self, batch_request: BatchRequest
    ) -> list[Batch]:
        self._validate_batch_request(batch_request)
        batch_list: List[Batch] = []

        batch_spec = PandasBatchSpec(
            reader_method=self._get_reader_method(),
            reader_options=self.dict(
                exclude=self._EXCLUDE_FROM_READER_OPTIONS,
                exclude_unset=True,
                by_alias=True,
            ),
        )
        execution_engine: PandasExecutionEngine = self.datasource.get_execution_engine()
        data, markers = execution_engine.get_batch_data_and_markers(
            batch_spec=batch_spec
        )

        # batch_definition (along with batch_spec and markers) is only here to satisfy a
        # legacy constraint when computing usage statistics in a validator. We hope to remove
        # it in the future.
        # imports are done inline to prevent a circular dependency with core/batch.py
        from great_expectations.core import IDDict
        from great_expectations.core.batch import BatchDefinition

        batch_definition = BatchDefinition(
            datasource_name=self.datasource.name,
            data_connector_name="experimental",
            data_asset_name=self.name,
            batch_identifiers=IDDict(batch_request.options),
            batch_spec_passthrough=None,
        )

        batch_metadata = copy.deepcopy(batch_request.options)

        # Some pydantic annotations are postponed due to circular imports.
        # Batch.update_forward_refs() will set the annotations before we
        # instantiate the Batch class since we can import them in this scope.
        Batch.update_forward_refs()
        batch_list.append(
            Batch(
                datasource=self.datasource,
                data_asset=self,
                batch_request=batch_request,
                data=data,
                metadata=batch_metadata,
                legacy_batch_markers=markers,
                legacy_batch_spec=batch_spec,
                legacy_batch_definition=batch_definition,
            )
        )
        return batch_list

    def build_batch_request(
        self, options: Optional[BatchRequestOptions] = None
    ) -> BatchRequest:
        if options:
            actual_keys = set(options.keys())
            raise gx_exceptions.InvalidBatchRequestError(
                "Data Assets associated with PandasDatasource can only contain a single batch,\n"
                "therefore BatchRequest options cannot be supplied. BatchRequest options with keys:\n"
                f"{actual_keys}\nwere passed.\n"
            )

        return BatchRequest(
            datasource_name=self.datasource.name,
            data_asset_name=self.name,
            options={},
        )

    def _validate_batch_request(self, batch_request: BatchRequest) -> None:
        """Validates the batch_request has the correct form.

        Args:
            batch_request: A batch request object to be validated.
        """
        if not (
            batch_request.datasource_name == self.datasource.name
            and batch_request.data_asset_name == self.name
            and not batch_request.options
        ):
            expect_batch_request_form = BatchRequest(
                datasource_name=self.datasource.name,
                data_asset_name=self.name,
                options={},
            )
            raise gx_exceptions.InvalidBatchRequestError(
                "BatchRequest should have form:\n"
                f"{pf(dataclasses.asdict(expect_batch_request_form))}\n"
                f"but actually has form:\n{pf(dataclasses.asdict(batch_request))}\n"
            )


_PANDAS_READER_METHOD_UNSUPPORTED_LIST = (
    # "read_csv",
    # "read_json",
    # "read_excel",
    # "read_parquet",
    # "read_clipboard",
    # "read_feather",
    "read_fwf",  # unhandled type
    # "read_gbq",
    # "read_hdf",
    # "read_html",
    # "read_orc",
    # "read_pickle",
    # "read_sas",
    # "read_spss",
    # "read_sql",
    # "read_sql_query",
    # "read_sql_table",
    # "read_stata",
    # "read_table",
    # "read_xml",
)


_PANDAS_ASSET_MODELS = _generate_pandas_data_asset_models(
    _PandasDataAsset,
    blacklist=_PANDAS_READER_METHOD_UNSUPPORTED_LIST,
    use_docstring_from_method=True,
    skip_first_param=False,
)


try:
    ClipboardAsset = _PANDAS_ASSET_MODELS["clipboard"]
    CSVAsset = _PANDAS_ASSET_MODELS["csv"]
    ExcelAsset = _PANDAS_ASSET_MODELS["excel"]
    FeatherAsset = _PANDAS_ASSET_MODELS["feather"]
    GBQAsset = _PANDAS_ASSET_MODELS["gbq"]
    HDFAsset = _PANDAS_ASSET_MODELS["hdf"]
    HTMLAsset = _PANDAS_ASSET_MODELS["html"]
    JSONAsset = _PANDAS_ASSET_MODELS["json"]
    ORCAsset = _PANDAS_ASSET_MODELS["orc"]
    ParquetAsset = _PANDAS_ASSET_MODELS["parquet"]
    PickleAsset = _PANDAS_ASSET_MODELS["pickle"]
    SQLAsset = _PANDAS_ASSET_MODELS["sql"]
    SQLQueryAsset = _PANDAS_ASSET_MODELS["sql_query"]
    SQLTableAsset = _PANDAS_ASSET_MODELS["sql_table"]
    SASAsset = _PANDAS_ASSET_MODELS["sas"]
    SPSSAsset = _PANDAS_ASSET_MODELS["spss"]
    StataAsset = _PANDAS_ASSET_MODELS["stata"]
    TableAsset = _PANDAS_ASSET_MODELS["table"]
    XMLAsset = _PANDAS_ASSET_MODELS["xml"]
except KeyError as key_err:
    logger.info(f"zep - {key_err} asset model could not be generated")
    ClipboardAsset = _PandasDataAsset
    CSVAsset = _PandasDataAsset
    ExcelAsset = _PandasDataAsset
    FeatherAsset = _PandasDataAsset
    GBQAsset = _PandasDataAsset
    HDFAsset = _PandasDataAsset
    HTMLAsset = _PandasDataAsset
    JSONAsset = _PandasDataAsset
    ORCAsset = _PandasDataAsset
    ParquetAsset = _PandasDataAsset
    PickleAsset = _PandasDataAsset
    SQLAsset = _PandasDataAsset
    SQLQueryAsset = _PandasDataAsset
    SQLTableAsset = _PandasDataAsset
    SASAsset = _PandasDataAsset
    SPSSAsset = _PandasDataAsset
    StataAsset = _PandasDataAsset
    TableAsset = _PandasDataAsset
    XMLAsset = _PandasDataAsset


class _PandasDatasource(Datasource, Generic[_DataAssetT]):
    # class attributes
    asset_types: ClassVar[List[Type[DataAsset]]] = []

    # instance attributes
    assets: MutableMapping[
        str,
        _DataAssetT,
    ] = {}

    # Abstract Methods
    @property
    def execution_engine_type(self) -> Type[PandasExecutionEngine]:
        """Return the PandasExecutionEngine unless the override is set"""
        from great_expectations.execution_engine.pandas_execution_engine import (
            PandasExecutionEngine,
        )

        return PandasExecutionEngine

    def test_connection(self, test_assets: bool = True) -> None:
        """Test the connection for the _PandasDatasource.

        Args:
            test_assets: If assets have been passed to the _PandasDatasource,
                         an attempt can be made to test them as well.

        Raises:
            TestConnectionError: If the connection test fails.
        """
        raise NotImplementedError(
            """One needs to implement "test_connection" on a _PandasDatasource subclass."""
        )

    # End Abstract Methods


class PandasDatasource(_PandasDatasource):
    # class attributes
    asset_types: ClassVar[List[Type[DataAsset]]] = list(_PANDAS_ASSET_MODELS.values())

    # private attributes
    _data_context = pydantic.PrivateAttr()

    # instance attributes
    type: Literal["pandas"] = "pandas"
    assets: Dict[
        str,
        _PandasDataAsset,
    ] = {}

    def test_connection(self, test_assets: bool = True) -> None:
        ...

    def _get_validator(self, asset: _PandasDataAsset) -> Validator:
        batch_request = asset.build_batch_request()
        return self._data_context.get_validator(batch_request=batch_request)

    def add_csv_asset(
        self, filepath_or_buffer: pydantic.FilePath, name: str, **kwargs
    ) -> CSVAsset:
        kwargs["filepath_or_buffer"] = filepath_or_buffer
        asset = CSVAsset(
            name=name,
            **kwargs,
        )
        return self.add_asset(asset=asset)

    def read_csv(
        self,
        filepath_or_buffer: pydantic.FilePath,
        name: Optional[str] = None,
        **kwargs,
    ) -> Validator:
        if not name:
            name = DEFAULT_PANDAS_DATA_ASSET_NAME
        asset: CSVAsset = self.add_csv_asset(
            filepath_or_buffer=filepath_or_buffer,
            name=name,
            **kwargs,
        )
        return self._get_validator(asset=asset)
