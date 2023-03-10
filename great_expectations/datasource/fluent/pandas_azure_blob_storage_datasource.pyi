import re
import typing
from logging import Logger
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Hashable,
    Iterable,
    Optional,
    Sequence,
    Union,
)

from typing_extensions import Literal

from great_expectations.core._docs_decorators import public_api as public_api
from great_expectations.core.util import AzureUrl as AzureUrl
from great_expectations.datasource.fluent import _PandasFilePathDatasource
from great_expectations.datasource.fluent.data_asset.data_connector import (
    AzureBlobStorageDataConnector as AzureBlobStorageDataConnector,
)
from great_expectations.datasource.fluent.data_asset.data_connector import (
    FilesystemDataConnector as FilesystemDataConnector,
)
from great_expectations.datasource.fluent.interfaces import Sorter as Sorter
from great_expectations.datasource.fluent.interfaces import (
    SortersDefinition as SortersDefinition,
)
from great_expectations.datasource.fluent.interfaces import (
    TestConnectionError as TestConnectionError,
)
from great_expectations.datasource.fluent.pandas_datasource import (
    PandasDatasourceError as PandasDatasourceError,
)
from great_expectations.datasource.fluent.pandas_file_path_datasource import (
    CSVAsset as CSVAsset,
)
from great_expectations.datasource.fluent.pandas_file_path_datasource import (
    ExcelAsset as ExcelAsset,
)
from great_expectations.datasource.fluent.pandas_file_path_datasource import (
    JSONAsset as JSONAsset,
)
from great_expectations.datasource.fluent.pandas_file_path_datasource import (
    ParquetAsset as ParquetAsset,
)

if TYPE_CHECKING:
    from great_expectations.datasource.fluent import Sorter
    from great_expectations.datasource.fluent.dynamic_pandas import (
        CompressionOptions,
        CSVEngine,
        FilePath,
        IndexLabel,
        StorageOptions,
    )
    from great_expectations.datasource.fluent.pandas_file_path_datasource import (
        CSVAsset,
        ExcelAsset,
        FeatherAsset,
        HDFAsset,
        HTMLAsset,
        JSONAsset,
        ORCAsset,
        ParquetAsset,
        PickleAsset,
        SASAsset,
        SPSSAsset,
        STATAAsset,
        XMLAsset,
    )

logger: Logger
ABS_IMPORTED: bool

class PandasAzureBlobStorageDatasourceError(PandasDatasourceError): ...

class PandasAzureBlobStorageDatasource(_PandasFilePathDatasource):
    type: Literal["pandas_abs"]
    azure_options: Dict[str, Any]

    _account_name: str
    _azure_client: Any
    def test_connection(self, test_assets: bool = ...) -> None: ...
    def add_csv_asset(
        self,
        name: str,
        batching_regex: Union[re.Pattern, str],
        container: str,
        name_starts_with: str = "",
        delimiter: str = "/",  # FIXME: this conflicts with the read_csv delimiter
        order_by: Optional[SortersDefinition] = ...,
        sep: typing.Union[str, None] = ...,
        header: Union[int, Sequence[int], None, Literal["infer"]] = "infer",
        names: Union[Sequence[Hashable], None] = ...,
        index_col: Union[IndexLabel, Literal[False], None] = ...,
        usecols: typing.Union[int, str, typing.Sequence[int], None] = ...,
        squeeze: typing.Union[bool, None] = ...,
        prefix: str = ...,
        mangle_dupe_cols: bool = ...,
        dtype: typing.Union[dict, None] = ...,
        engine: Union[CSVEngine, None] = ...,
        converters: typing.Any = ...,
        true_values: typing.Any = ...,
        false_values: typing.Any = ...,
        skipinitialspace: bool = ...,
        skiprows: typing.Union[typing.Sequence[int], int, None] = ...,
        skipfooter: int = 0,
        nrows: typing.Union[int, None] = ...,
        na_values: typing.Any = ...,
        keep_default_na: bool = ...,
        na_filter: bool = ...,
        verbose: bool = ...,
        skip_blank_lines: bool = ...,
        parse_dates: typing.Any = ...,
        infer_datetime_format: bool = ...,
        keep_date_col: bool = ...,
        date_parser: typing.Any = ...,
        dayfirst: bool = ...,
        cache_dates: bool = ...,
        iterator: bool = ...,
        chunksize: typing.Union[int, None] = ...,
        compression: CompressionOptions = "infer",
        thousands: typing.Union[str, None] = ...,
        decimal: str = ".",
        lineterminator: typing.Union[str, None] = ...,
        quotechar: str = '"',
        quoting: int = 0,
        doublequote: bool = ...,
        escapechar: typing.Union[str, None] = ...,
        comment: typing.Union[str, None] = ...,
        encoding: typing.Union[str, None] = ...,
        encoding_errors: typing.Union[str, None] = "strict",
        dialect: typing.Union[str, None] = ...,
        error_bad_lines: typing.Union[bool, None] = ...,
        warn_bad_lines: typing.Union[bool, None] = ...,
        on_bad_lines: typing.Any = ...,
        delim_whitespace: bool = ...,
        low_memory: typing.Any = ...,
        memory_map: bool = ...,
        storage_options: StorageOptions = ...,
    ) -> CSVAsset: ...
    def add_excel_asset(
        self,
        name: str,
        batching_regex: Union[re.Pattern, str],
        container: str,
        name_starts_with: str = "",
        delimiter: str = "/",
        order_by: Optional[SortersDefinition] = ...,
        sheet_name: typing.Union[str, int, None] = 0,
        header: Union[int, Sequence[int], None] = 0,
        names: typing.Union[typing.List[str], None] = ...,
        index_col: Union[int, Sequence[int], None] = ...,
        usecols: typing.Union[int, str, typing.Sequence[int], None] = ...,
        squeeze: typing.Union[bool, None] = ...,
        dtype: typing.Union[dict, None] = ...,
        true_values: Union[Iterable[Hashable], None] = ...,
        false_values: Union[Iterable[Hashable], None] = ...,
        skiprows: typing.Union[typing.Sequence[int], int, None] = ...,
        nrows: typing.Union[int, None] = ...,
        na_values: typing.Any = ...,
        keep_default_na: bool = ...,
        na_filter: bool = ...,
        verbose: bool = ...,
        parse_dates: typing.Union[typing.List, typing.Dict, bool] = ...,
        thousands: typing.Union[str, None] = ...,
        decimal: str = ".",
        comment: typing.Union[str, None] = ...,
        skipfooter: int = 0,
        convert_float: typing.Union[bool, None] = ...,
        mangle_dupe_cols: bool = ...,
        storage_options: StorageOptions = ...,
    ) -> ExcelAsset: ...
    def add_feather_asset(
        self,
        name: str,
        order_by: typing.List[Sorter] = ...,
        batching_regex: typing.Pattern = ...,
        columns: Union[Sequence[Hashable], None] = ...,
        use_threads: bool = ...,
        storage_options: StorageOptions = ...,
    ) -> FeatherAsset: ...
    def add_hdf_asset(
        self,
        name: str,
        order_by: typing.List[Sorter] = ...,
        batching_regex: typing.Pattern = ...,
        key: typing.Any = ...,
        mode: str = "r",
        errors: str = "strict",
        where: typing.Union[str, typing.List, None] = ...,
        start: typing.Union[int, None] = ...,
        stop: typing.Union[int, None] = ...,
        columns: typing.Union[typing.List[str], None] = ...,
        iterator: bool = ...,
        chunksize: typing.Union[int, None] = ...,
        kwargs: typing.Union[dict, None] = ...,
    ) -> HDFAsset: ...
    def add_html_asset(
        self,
        name: str,
        order_by: typing.List[Sorter] = ...,
        batching_regex: typing.Pattern = ...,
        match: Union[str, typing.Pattern] = ".+",
        flavor: typing.Union[str, None] = ...,
        header: Union[int, Sequence[int], None] = ...,
        index_col: Union[int, Sequence[int], None] = ...,
        skiprows: typing.Union[typing.Sequence[int], int, None] = ...,
        attrs: typing.Union[typing.Dict[str, str], None] = ...,
        parse_dates: bool = ...,
        thousands: typing.Union[str, None] = ",",
        encoding: typing.Union[str, None] = ...,
        decimal: str = ".",
        converters: typing.Union[typing.Dict, None] = ...,
        na_values: Union[Iterable[object], None] = ...,
        keep_default_na: bool = ...,
        displayed_only: bool = ...,
    ) -> HTMLAsset: ...
    def add_json_asset(
        self,
        name: str,
        batching_regex: Union[re.Pattern, str],
        container: str,
        name_starts_with: str = "",
        delimiter: str = "/",
        order_by: Optional[SortersDefinition] = ...,
        orient: typing.Union[str, None] = ...,
        dtype: typing.Union[dict, None] = ...,
        convert_axes: typing.Any = ...,
        convert_dates: typing.Union[bool, typing.List[str]] = ...,
        keep_default_dates: bool = ...,
        numpy: bool = ...,
        precise_float: bool = ...,
        date_unit: typing.Union[str, None] = ...,
        encoding: typing.Union[str, None] = ...,
        encoding_errors: typing.Union[str, None] = "strict",
        lines: bool = ...,
        chunksize: typing.Union[int, None] = ...,
        compression: CompressionOptions = "infer",
        nrows: typing.Union[int, None] = ...,
        storage_options: StorageOptions = ...,
    ) -> JSONAsset: ...
    def add_orc_asset(
        self,
        name: str,
        order_by: typing.List[Sorter] = ...,
        batching_regex: typing.Pattern = ...,
        columns: typing.Union[typing.List[str], None] = ...,
        kwargs: typing.Union[dict, None] = ...,
    ) -> ORCAsset: ...
    def add_parquet_asset(
        self,
        name: str,
        batching_regex: Union[re.Pattern, str],
        container: str,
        name_starts_with: str = "",
        delimiter: str = "/",
        order_by: Optional[SortersDefinition] = ...,
        engine: str = "auto",
        columns: typing.Union[typing.List[str], None] = ...,
        storage_options: StorageOptions = ...,
        use_nullable_dtypes: bool = ...,
        kwargs: typing.Union[dict, None] = ...,
    ) -> ParquetAsset: ...
    def add_pickle_asset(
        self,
        name: str,
        order_by: typing.List[Sorter] = ...,
        batching_regex: typing.Pattern = ...,
        compression: CompressionOptions = "infer",
        storage_options: StorageOptions = ...,
    ) -> PickleAsset: ...
    def add_sas_asset(
        self,
        name: str,
        order_by: typing.List[Sorter] = ...,
        batching_regex: typing.Pattern = ...,
        format: typing.Union[str, None] = ...,
        index: Union[Hashable, None] = ...,
        encoding: typing.Union[str, None] = ...,
        chunksize: typing.Union[int, None] = ...,
        iterator: bool = ...,
        compression: CompressionOptions = "infer",
    ) -> SASAsset: ...
    def add_spss_asset(
        self,
        name: str,
        order_by: typing.List[Sorter] = ...,
        batching_regex: typing.Pattern = ...,
        usecols: typing.Union[int, str, typing.Sequence[int], None] = ...,
        convert_categoricals: bool = ...,
    ) -> SPSSAsset: ...
    def add_stata_asset(
        self,
        name: str,
        order_by: typing.List[Sorter] = ...,
        batching_regex: typing.Pattern = ...,
        convert_dates: bool = ...,
        convert_categoricals: bool = ...,
        index_col: typing.Union[str, None] = ...,
        convert_missing: bool = ...,
        preserve_dtypes: bool = ...,
        columns: Union[Sequence[str], None] = ...,
        order_categoricals: bool = ...,
        chunksize: typing.Union[int, None] = ...,
        iterator: bool = ...,
        compression: CompressionOptions = "infer",
        storage_options: StorageOptions = ...,
    ) -> STATAAsset: ...
    def add_xml_asset(
        self,
        name: str,
        order_by: typing.List[Sorter] = ...,
        batching_regex: typing.Pattern = ...,
        xpath: str = "./*",
        namespaces: typing.Union[typing.Dict[str, str], None] = ...,
        elems_only: bool = ...,
        attrs_only: bool = ...,
        names: Union[Sequence[str], None] = ...,
        dtype: typing.Union[dict, None] = ...,
        encoding: typing.Union[str, None] = "utf-8",
        stylesheet: Union[FilePath, None] = ...,
        iterparse: typing.Union[typing.Dict[str, typing.List[str]], None] = ...,
        compression: CompressionOptions = "infer",
        storage_options: StorageOptions = ...,
    ) -> XMLAsset: ...
