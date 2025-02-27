import datetime
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional

import pandas as pd

from great_expectations.compatibility.typing_extensions import override
from great_expectations.execution_engine.partition_and_sample.data_partitioner import (
    DatePart,
)
from tests.test_utils import convert_string_columns_to_datetime


class TaxiTestData:
    def __init__(
        self,
        test_df: pd.DataFrame,
        test_column_name: Optional[str] = None,
        test_column_names: Optional[List[str]] = None,
        column_names_to_convert: Optional[List[str]] = None,
    ):
        if (
            sum(
                bool(x)
                for x in [
                    test_column_name is not None,
                    test_column_names is not None,
                ]
            )
            > 1
        ):
            raise ValueError(
                "No more than one of test_column_name or test_column_names can be specified."
            )

        self._test_column_name = test_column_name
        self._test_column_names = test_column_names

        # Convert specified columns (e.g., "pickup_datetime" and "dropoff_datetime") to datetime column type.  # noqa: E501
        convert_string_columns_to_datetime(
            df=test_df, column_names_to_convert=column_names_to_convert
        )

        self._test_df = test_df

    @property
    def test_df(self) -> pd.DataFrame:
        return self._test_df

    @property
    def test_column_name(self) -> Optional[str]:
        return self._test_column_name

    @property
    def test_column_names(self) -> Optional[List[str]]:
        return self._test_column_names

    @staticmethod
    def years_in_taxi_data() -> List[datetime.datetime]:
        return (
            pd.date_range(start="2018-01-01", end="2020-12-31", freq="AS").to_pydatetime().tolist()
        )

    def year_batch_identifier_data(self) -> List[dict]:
        return [{DatePart.YEAR.value: dt.year} for dt in self.years_in_taxi_data()]

    @staticmethod
    def months_in_taxi_data() -> List[datetime.datetime]:
        return (
            pd.date_range(start="2018-01-01", end="2020-12-31", freq="MS").to_pydatetime().tolist()
        )

    def get_unique_sorted_months_in_taxi_data(self) -> List[str]:
        months: List[datetime.datetime] = sorted(set(self.months_in_taxi_data()))

        month: datetime.datetime
        return [month.strftime("%Y-%m-%d") for month in months]

    def year_month_batch_identifier_data(self) -> List[dict]:
        return [
            {DatePart.YEAR.value: dt.year, DatePart.MONTH.value: dt.month}
            for dt in self.months_in_taxi_data()
        ]

    def month_batch_identifier_data(self) -> List[dict]:
        return [{DatePart.MONTH.value: dt.month} for dt in self.months_in_taxi_data()]

    def year_month_day_batch_identifier_data(self) -> List[dict]:
        # Since taxi data does not contain all days,
        # we need to introspect the data to build the fixture:
        year_month_day_batch_identifier_list_unsorted: List[dict] = list(
            {val[0]: val[1], val[2]: val[3], val[4]: val[5]}
            for val in {
                (
                    DatePart.YEAR.value,
                    dt.year,
                    DatePart.MONTH.value,
                    dt.month,
                    DatePart.DAY.value,
                    dt.day,
                )
                for dt in self.test_df[self.test_column_name]
            }
        )

        return sorted(
            year_month_day_batch_identifier_list_unsorted,
            key=lambda x: (
                x[DatePart.YEAR.value],
                x[DatePart.MONTH.value],
                x[DatePart.DAY.value],
            ),
        )

    def get_test_column_values(self) -> List[Optional[Any]]:
        column_values: List[Optional[Any]] = self.test_df[self.test_column_name].tolist()
        return column_values

    def get_test_multi_column_values(self) -> List[dict]:
        multi_column_values: List[dict] = self.test_df[self.test_column_names].to_dict("records")
        return multi_column_values

    def get_unique_sorted_test_column_values(
        self,
        reverse: Optional[bool] = False,
        move_null_to_front: Optional[bool] = False,
        limit: Optional[int] = None,
    ) -> List[Optional[Any]]:
        column_values: List[Optional[Any]] = self.get_test_column_values()
        column_values = list(set(column_values))
        column_values = sorted(
            column_values,
            key=lambda element: (element is None, element),
            reverse=reverse,
        )

        column_value: Any
        if (
            move_null_to_front
            and any(column_value is None for column_value in column_values)
            and column_values[0] is not None
            and column_values[-1] is None
        ):
            num_null_values: int = column_values.count(None)
            column_values = list(filter(None, column_values))
            column_values = num_null_values * [None] + column_values

        if limit is None:
            return column_values

        return column_values[:limit]

    def get_unique_sorted_test_multi_column_values(
        self,
        reverse: Optional[bool] = False,
        limit: Optional[int] = None,
    ) -> List[dict]:
        multi_column_values: List[dict] = self.get_test_multi_column_values()
        multi_column_values = sorted(
            multi_column_values,
            key=lambda element: sum(
                map(
                    ord,
                    hashlib.md5(
                        str(tuple(zip(element.keys(), element.values()))).encode("utf-8")
                    ).hexdigest(),
                )
            ),
            reverse=reverse,
        )

        unique_multi_column_values: List[dict] = []

        hash_codes: List[str] = []
        hash_code: str
        dictionary_element: dict
        for dictionary_element in multi_column_values:
            hash_code = hashlib.md5(
                str(tuple(zip(dictionary_element.keys(), dictionary_element.values()))).encode(
                    "utf-8"
                )
            ).hexdigest()
            if hash_code not in hash_codes:
                unique_multi_column_values.append(dictionary_element)
                hash_codes.append(hash_code)

        if limit is None:
            return unique_multi_column_values

        return unique_multi_column_values[:limit]

    def get_divided_integer_test_column_values(self, divisor: int) -> List[Optional[Any]]:
        column_values: List[Optional[Any]] = self.get_test_column_values()

        column_value: Any
        column_values = [column_value // divisor for column_value in column_values]

        return list(set(column_values))

    def get_mod_integer_test_column_values(self, mod: int) -> List[Optional[Any]]:
        column_values: List[Optional[Any]] = self.get_test_column_values()

        column_value: Any
        column_values = [column_value % mod for column_value in column_values]

        return list(set(column_values))

    def get_hashed_test_column_values(self, hash_digits: int) -> List[Optional[Any]]:
        """
        hashlib.md5(string).hexdigest()
        hashlib.md5(str(tuple_).encode("utf-8")).hexdigest()
        [:num_digits]
        """
        column_values: List[Optional[Any]] = self.get_unique_sorted_test_column_values(
            reverse=False, move_null_to_front=False, limit=None
        )

        column_value: Any
        column_values = [
            hashlib.md5(str(column_value).encode("utf-8")).hexdigest()[-1 * hash_digits :]
            for column_value in column_values
        ]

        return list(sorted(set(column_values)))


@dataclass
class TaxiPartitioningTestCase:
    table_domain_test_case: (
        bool  # Use "MetricDomainTypes" when column-pair and multicolumn test cases are developed.
    )
    num_expected_batch_definitions: int
    num_expected_rows_in_first_batch_definition: int
    add_batch_definition_method_name: str
    add_batch_definition_kwargs: dict
    expected_column_values: List[Any] = field(default_factory=list)


class TaxiPartitioningTestCasesBase(ABC):
    def __init__(self, taxi_test_data: TaxiTestData):
        self._taxi_test_data = taxi_test_data

    @property
    def taxi_test_data(self) -> TaxiTestData:
        return self._taxi_test_data

    @property
    def test_df(self) -> pd.DataFrame:
        return self._taxi_test_data.test_df

    @property
    def test_column_name(self) -> str:
        return self._taxi_test_data.test_column_name

    @property
    def test_column_names(self) -> List[str]:
        return self._taxi_test_data.test_column_names

    @abstractmethod
    def test_cases(self) -> List[TaxiPartitioningTestCase]:
        pass


class TaxiPartitioningTestCasesWholeTable(TaxiPartitioningTestCasesBase):
    @override
    def test_cases(self) -> List[TaxiPartitioningTestCase]:
        return [
            TaxiPartitioningTestCase(
                table_domain_test_case=True,
                num_expected_batch_definitions=1,
                num_expected_rows_in_first_batch_definition=360,
                expected_column_values=[],
                add_batch_definition_method_name="add_batch_definition_whole_table",
                add_batch_definition_kwargs={},
            ),
        ]


class TaxiPartitioningTestCasesDateTime(TaxiPartitioningTestCasesBase):
    @override
    def test_cases(self) -> List[TaxiPartitioningTestCase]:
        return [
            TaxiPartitioningTestCase(
                table_domain_test_case=False,
                num_expected_batch_definitions=3,
                num_expected_rows_in_first_batch_definition=120,
                expected_column_values=self.taxi_test_data.year_batch_identifier_data(),
                add_batch_definition_method_name="add_batch_definition_yearly",
                add_batch_definition_kwargs={"column": self.taxi_test_data.test_column_name},
            ),
            TaxiPartitioningTestCase(
                table_domain_test_case=False,
                num_expected_batch_definitions=36,
                num_expected_rows_in_first_batch_definition=10,
                expected_column_values=self.taxi_test_data.year_month_batch_identifier_data(),
                add_batch_definition_method_name="add_batch_definition_monthly",
                add_batch_definition_kwargs={"column": self.taxi_test_data.test_column_name},
            ),
            TaxiPartitioningTestCase(
                table_domain_test_case=False,
                num_expected_batch_definitions=299,
                num_expected_rows_in_first_batch_definition=2,
                expected_column_values=self.taxi_test_data.year_month_day_batch_identifier_data(),
                add_batch_definition_method_name="add_batch_definition_daily",
                add_batch_definition_kwargs={"column": self.taxi_test_data.test_column_name},
            ),
        ]
