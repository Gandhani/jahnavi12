from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional, Type

import pydantic
from pydantic import dataclasses as pydantic_dc
from typing_extensions import ClassVar

from great_expectations.experimental.datasources.interfaces import DataAsset

if TYPE_CHECKING:
    import sqlalchemy

from typing_extensions import Literal

from great_expectations.experimental.datasources.sql_datasource import (
    BatchSortersDefinition,
    ColumnSplitter,
    DatetimeRange,
    SQLDatasource,
    TableAsset,
    _query_for_year_and_month,
)


class SqliteTableAsset(TableAsset):
    # Subclass overrides
    type: Literal["sqlite_table"] = "sqlite_table"  # type: ignore[assignment]
    column_splitter: Optional[SqliteYearMonthSplitter] = None  # type: ignore[assignment]

    # This asset type will support a variety of splitters
    def add_year_and_month_splitter(
        self,
        column_name: str,
    ) -> TableAsset:
        """Associates a year month splitter with this sqlite table data asset

        Args:
            column_name: A column name of the date column where year and month will be parsed out.

        Returns:
            This SqliteTableAsset so we can use this method fluently.
        """
        self.column_splitter = SqliteYearMonthSplitter(
            column_name=column_name,
        )
        return self


@pydantic_dc.dataclass(frozen=True)
class SqliteYearMonthSplitter(ColumnSplitter):
    method_name: Literal["split_on_year_and_month"] = "split_on_year_and_month"
    param_names: List[Literal["year", "month"]] = pydantic.Field(
        default_factory=lambda: ["year", "month"]
    )

    def param_defaults(self, table_asset: TableAsset) -> Dict[str, List]:
        """Query sqlite database to get the years and months to split over.

        Args:
            table_asset: A TableAsset over which we want to split the data.
        """
        return _query_for_year_and_month(
            table_asset, self.column_name, _get_sqlite_datetime_range
        )


def _get_sqlite_datetime_range(
    conn: sqlalchemy.engine.base.Connection, table_name: str, col_name: str
) -> DatetimeRange:
    q = f"select STRFTIME('%Y%m%d', min({col_name})), STRFTIME('%Y%m%d', max({col_name})) from {table_name}"
    min_max_dt = [datetime.strptime(dt, "%Y%m%d") for dt in list(conn.execute(q))[0]]
    return DatetimeRange(min=min_max_dt[0], max=min_max_dt[1])


class SqliteDatasource(SQLDatasource):
    # class var definitions
    asset_types: ClassVar[List[Type[DataAsset]]] = [SqliteTableAsset]

    # Subclass instance var overrides
    # right side of the operator determines the type name
    # left side enforces the names on instance creation
    type: Literal["sqlite"] = "sqlite"  # type: ignore[assignment]
    connection_string: str
    assets: Dict[str, SqliteTableAsset] = {}  # type: ignore[assignment]

    def add_table_asset(
        self,
        name: str,
        table_name: str,
        order_by: Optional[BatchSortersDefinition] = None,
    ) -> TableAsset:
        """Adds a sqlite table asset to this sqlite datasource.

        Args:
            name: The name of this table asset.
            table_name: The table where the data resides.
            order_by: A list of BatchSorters or BatchSorter strings.

        Returns:
            The TableAsset that is added to the datasource.
        """
        asset = SqliteTableAsset(
            name=name,
            table_name=table_name,
            order_by=order_by or [],  # type: ignore[arg-type]  # coerce list[str]
            # see TableAsset._parse_order_by_sorter()
        )
        # TODO (kilo59): custom init for `DataAsset` to accept datasource in constructor?
        # Will most DataAssets require a `Datasource` attribute?
        asset._datasource = self
        self.assets[name] = asset
        return asset
