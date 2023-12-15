from __future__ import annotations

import datetime
import json
import logging
import uuid
from copy import deepcopy
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Type,
    Union,
)

from marshmallow import Schema, ValidationError, fields, post_dump, post_load, pre_dump

import great_expectations as gx
import great_expectations.exceptions as gx_exceptions
from great_expectations import __version__ as ge_version
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core._docs_decorators import (
    deprecated_argument,
    new_argument,
    public_api,
)
from great_expectations.core.evaluation_parameters import (
    _deduplicate_evaluation_parameter_dependencies,
)
from great_expectations.core.expectation_configuration import (
    ExpectationConfiguration,
    ExpectationConfigurationSchema,
    expectationConfigurationSchema,
)
from great_expectations.core.usage_statistics.events import UsageStatsEvents
from great_expectations.core.util import (
    convert_to_json_serializable,
    ensure_json_serializable,
    nested_update,
    parse_string_to_datetime,
)
from great_expectations.data_context.types.refs import GXCloudResourceRef
from great_expectations.data_context.util import instantiate_class_from_config
from great_expectations.expectations.registry import get_expectation_impl
from great_expectations.render import (
    AtomicPrescriptiveRendererType,
    RenderedAtomicContent,
)
from great_expectations.types import SerializableDictDot

if TYPE_CHECKING:
    from great_expectations.alias_types import JSONValues
    from great_expectations.data_context import AbstractDataContext
    from great_expectations.execution_engine import ExecutionEngine
    from great_expectations.expectations.expectation import Expectation
    from great_expectations.render.renderer.inline_renderer import InlineRendererConfig

logger = logging.getLogger(__name__)


@public_api
@deprecated_argument(argument_name="data_asset_type", version="0.14.0")
@new_argument(
    argument_name="ge_cloud_id",
    version="0.13.33",
    message="Used in GX Cloud deployments.",
)
class ExpectationSuite(SerializableDictDot):
    """Set-like collection of Expectations.

    Args:
        name: Name of the Expectation Suite
        expectation_suite_name (deprecated): Name of the Expectation Suite.
        data_context: Data Context associated with this Expectation Suite.
        expectations: Expectation Configurations to associate with this Expectation Suite.
        evaluation_parameters: Evaluation parameters to be substituted when evaluating Expectations.
        data_asset_type: Type of data asset to associate with this suite.
        execution_engine_type: Name of the execution engine type.
        meta: Metadata related to the suite.
        ge_cloud_id: Great Expectations Cloud id for this Expectation Suite.
    """

    def __init__(  # noqa: PLR0913
        self,
        name: Optional[str] = None,
        data_context: Optional[AbstractDataContext] = None,
        expectations: Optional[Sequence[Union[dict, ExpectationConfiguration]]] = None,
        evaluation_parameters: Optional[dict] = None,
        data_asset_type: Optional[str] = None,
        execution_engine_type: Optional[Type[ExecutionEngine]] = None,
        meta: Optional[dict] = None,
        ge_cloud_id: Optional[str] = None,
        expectation_suite_name: Optional[
            str
        ] = None,  # for backwards compatibility - remove
    ) -> None:
        if name:
            assert isinstance(name, str), "Name is a required field."
            self.expectation_suite_name = name
        else:
            assert isinstance(expectation_suite_name, str), "Name is a required field."
            self.expectation_suite_name = expectation_suite_name
        self.ge_cloud_id = ge_cloud_id
        self._data_context = data_context

        if expectations is None:
            expectations = []
        self.expectation_configurations = [
            ExpectationConfiguration(**expectation)
            if isinstance(expectation, dict)
            else expectation
            for expectation in expectations
        ]
        if evaluation_parameters is None:
            evaluation_parameters = {}
        self.evaluation_parameters = evaluation_parameters
        self.data_asset_type = data_asset_type
        self.execution_engine_type = execution_engine_type
        if meta is None:
            meta = {"great_expectations_version": ge_version}
        if (
            "great_expectations.__version__" not in meta.keys()
            and "great_expectations_version" not in meta.keys()
        ):
            meta["great_expectations_version"] = ge_version
        # We require meta information to be serializable, but do not convert until necessary
        ensure_json_serializable(meta)
        self.meta = meta

        from great_expectations import project_manager

        self._store = project_manager.get_expectations_store()

    @property
    def name(self) -> str:
        return self.expectation_suite_name

    @property
    def expectations(self) -> list[Expectation]:
        return [
            self._build_expectation(expectation_configuration=expectation_configuration)
            for expectation_configuration in self.expectation_configurations
        ]

    @public_api
    def add(self, expectation: Expectation) -> Expectation:
        """Add an Expectation to the collection."""
        if not any(
            expectation.configuration == existing_config
            for existing_config in self.expectation_configurations
        ):
            self.expectation_configurations.append(expectation.configuration)
        else:
            pass  # suite is a set-like collection

        if self._has_been_saved():
            # only persist on add if the suite has already been saved
            try:
                self.save()
            except Exception as exc:
                # rollback this change
                self.expectation_configurations.pop()
                raise exc

        return expectation

    @public_api
    def delete(self, expectation: Expectation) -> Expectation:
        """Delete an Expectation from the collection.

        Raises:
            KeyError: Expectation not found in suite.
        """
        remaining_expectation_configs = [
            exp_config
            for exp_config in self.expectation_configurations
            if exp_config != expectation.configuration
        ]
        if (
            len(remaining_expectation_configs)
            != len(self.expectation_configurations) - 1
        ):
            raise KeyError("No matching expectation was found.")
        self.expectation_configurations = remaining_expectation_configs

        if self._has_been_saved():
            # only persist on delete if the suite has already been saved
            try:
                self.save()
            except Exception as exc:
                # rollback this change
                # expectation suite is set-like so order of expectations doesn't matter
                self.expectation_configurations.append(expectation.configuration)
                raise exc

        return expectation

    @public_api
    def save(self) -> None:
        """Save this ExpectationSuite."""
        key = self._store.get_key(suite=self)
        res = self._store.add_or_update(key=key, value=self)
        if self.ge_cloud_id is None and isinstance(res, GXCloudResourceRef):
            self.ge_cloud_id = res.response["data"]["id"]

    def _has_been_saved(self) -> bool:
        """Has this ExpectationSuite been persisted to a DataContext?"""
        key = self._store.get_key(suite=self)
        return self._store.has_key(key=key)

    def add_citation(  # noqa: PLR0913
        self,
        comment: str,
        batch_request: Optional[
            Union[str, Dict[str, Union[str, Dict[str, Any]]]]
        ] = None,
        batch_definition: Optional[dict] = None,
        batch_spec: Optional[dict] = None,
        batch_kwargs: Optional[dict] = None,
        batch_markers: Optional[dict] = None,
        batch_parameters: Optional[dict] = None,
        profiler_config: Optional[dict] = None,
        citation_date: Optional[Union[str, datetime.datetime]] = None,
    ) -> None:
        if "citations" not in self.meta:
            self.meta["citations"] = []

        citation_date_obj: datetime.datetime
        _citation_date_types = (type(None), str, datetime.datetime)

        if citation_date is None:
            citation_date_obj = datetime.datetime.now(datetime.timezone.utc)
        elif isinstance(citation_date, str):
            citation_date_obj = parse_string_to_datetime(datetime_string=citation_date)
        elif isinstance(citation_date, datetime.datetime):
            citation_date_obj = citation_date
        else:
            raise gx_exceptions.GreatExpectationsTypeError(
                f"citation_date should be of type - {' '.join(str(t) for t in _citation_date_types)}"
            )

        citation: Dict[str, Any] = {
            "citation_date": citation_date_obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "batch_request": batch_request,
            "batch_definition": batch_definition,
            "batch_spec": batch_spec,
            "batch_kwargs": batch_kwargs,
            "batch_markers": batch_markers,
            "batch_parameters": batch_parameters,
            "profiler_config": profiler_config,
            "comment": comment,
        }
        gx.util.filter_properties_dict(
            properties=citation, clean_falsy=True, inplace=True
        )
        self.meta["citations"].append(citation)

    # noinspection PyPep8Naming
    def isEquivalentTo(self, other):
        """
        ExpectationSuite equivalence relies only on expectations and evaluation parameters. It does not include:
        - data_asset_name
        - expectation_suite_name
        - meta
        - data_asset_type
        """
        if not isinstance(other, self.__class__):
            if isinstance(other, dict):
                try:
                    # noinspection PyNoneFunctionAssignment,PyTypeChecker
                    other_dict: dict = expectationSuiteSchema.load(other)
                    other = ExpectationSuite(
                        **other_dict, data_context=self._data_context
                    )
                except ValidationError:
                    logger.debug(
                        "Unable to evaluate equivalence of ExpectationConfiguration object with dict because "
                        "dict other could not be instantiated as an ExpectationConfiguration"
                    )
                    return NotImplemented
            else:
                # Delegate comparison to the other instance
                return NotImplemented

        exp_count_is_equal = len(self.expectation_configurations) == len(
            other.expectation_configurations
        )

        exp_configs_are_equal = all(
            mine.isEquivalentTo(theirs)
            for (mine, theirs) in zip(
                self.expectation_configurations, other.expectation_configurations
            )
        )

        return exp_count_is_equal and exp_configs_are_equal

    def __eq__(self, other):
        """ExpectationSuite equality ignores instance identity, relying only on properties."""
        if not isinstance(other, self.__class__):
            # Delegate comparison to the other instance's __eq__.
            return NotImplemented
        return all(
            (
                self.expectation_suite_name == other.expectation_suite_name,
                self.expectation_configurations == other.expectation_configurations,
                self.evaluation_parameters == other.evaluation_parameters,
                self.data_asset_type == other.data_asset_type,
                self.meta == other.meta,
            )
        )

    def __ne__(self, other):
        # By using the == operator, the returned NotImplemented is handled correctly.
        return not self == other

    def __repr__(self):
        return json.dumps(self.to_json_dict(), indent=2)

    def __str__(self):
        return json.dumps(self.to_json_dict(), indent=2)

    def __deepcopy__(self, memo: dict):
        cls = self.__class__
        result = cls.__new__(cls)

        memo[id(self)] = result

        attributes_to_copy = set(ExpectationSuiteSchema().fields.keys())
        # map expectations to expectation_configurations
        attributes_to_copy.remove("expectations")
        attributes_to_copy.add("expectation_configurations")
        for key in attributes_to_copy:
            setattr(result, key, deepcopy(getattr(self, key)))

        result._data_context = self._data_context

        return result

    @public_api
    @override
    def to_json_dict(self) -> Dict[str, JSONValues]:
        """Returns a JSON-serializable dict representation of this ExpectationSuite.

        Returns:
            A JSON-serializable dict representation of this ExpectationSuite.
        """
        myself = expectationSuiteSchema.dump(self)
        # NOTE - JPC - 20191031: migrate to expectation-specific schemas that subclass result with properly-typed
        # schemas to get serialization all-the-way down via dump
        myself["expectations"] = convert_to_json_serializable(
            self.expectation_configurations
        )
        try:
            myself["evaluation_parameters"] = convert_to_json_serializable(
                myself["evaluation_parameters"]
            )
        except KeyError:
            pass  # Allow evaluation parameters to be missing if empty
        myself["meta"] = convert_to_json_serializable(myself["meta"])
        return myself

    def get_evaluation_parameter_dependencies(self) -> dict:
        dependencies: dict = {}
        for expectation in self.expectation_configurations:
            t = expectation.get_evaluation_parameter_dependencies()
            nested_update(dependencies, t)

        dependencies = _deduplicate_evaluation_parameter_dependencies(dependencies)
        return dependencies

    def get_citations(
        self,
        sort: bool = True,
        require_batch_kwargs: bool = False,
        require_batch_request: bool = False,
        require_profiler_config: bool = False,
    ) -> List[Dict[str, Any]]:
        citations: List[Dict[str, Any]] = self.meta.get("citations", [])
        if require_batch_kwargs:
            citations = self._filter_citations(
                citations=citations, filter_key="batch_kwargs"
            )
        if require_batch_request:
            citations = self._filter_citations(
                citations=citations, filter_key="batch_request"
            )
        if require_profiler_config:
            citations = self._filter_citations(
                citations=citations, filter_key="profiler_config"
            )
        if not sort:
            return citations
        return self._sort_citations(citations=citations)

    @staticmethod
    def _filter_citations(
        citations: List[Dict[str, Any]], filter_key
    ) -> List[Dict[str, Any]]:
        citations_with_bk: List[Dict[str, Any]] = []
        for citation in citations:
            if filter_key in citation and citation.get(filter_key):
                citations_with_bk.append(citation)

        return citations_with_bk

    @staticmethod
    def _sort_citations(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(citations, key=lambda x: x["citation_date"])

    # CRUD methods #

    def append_expectation(self, expectation_config) -> None:
        """Appends an expectation.

           Args:
               expectation_config (ExpectationConfiguration): \
                   The expectation to be added to the list.

           Notes:
               May want to add type-checking in the future.
        """
        self.expectation_configurations.append(expectation_config)

    @public_api
    @new_argument(
        argument_name="ge_cloud_id",
        version="0.13.33",
        message="Used in cloud deployments.",
    )
    def remove_expectation(
        self,
        expectation_configuration: Optional[ExpectationConfiguration] = None,
        match_type: str = "domain",
        remove_multiple_matches: bool = False,
        ge_cloud_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> List[ExpectationConfiguration]:
        """Remove an ExpectationConfiguration from the ExpectationSuite.

        Args:
            expectation_configuration: A potentially incomplete (partial) Expectation Configuration to match against.
            match_type: This determines what kwargs to use when matching. Options are 'domain' to match based
                on the data evaluated by that expectation, 'success' to match based on all configuration parameters
                that influence whether an expectation succeeds based on a given batch of data, and 'runtime' to match
                based on all configuration parameters.
            remove_multiple_matches: If True, will remove multiple matching expectations.
            ge_cloud_id: Great Expectations Cloud id for an Expectation.

        Returns:
            The list of deleted ExpectationConfigurations.

        Raises:
            TypeError: Must provide either expectation_configuration or ge_cloud_id.
            ValueError: No match or multiple matches found (and remove_multiple_matches=False).
        """
        if expectation_configuration is None and ge_cloud_id is None:
            raise TypeError(
                "Must provide either expectation_configuration or ge_cloud_id"
            )

        found_expectation_indexes = self.find_expectation_indexes(
            expectation_configuration=expectation_configuration,
            match_type=match_type,
            ge_cloud_id=ge_cloud_id,  # type: ignore[arg-type]
        )
        if len(found_expectation_indexes) < 1:
            raise ValueError("No matching expectation was found.")

        elif len(found_expectation_indexes) > 1:
            if remove_multiple_matches:
                removed_expectations = []
                for index in sorted(found_expectation_indexes, reverse=True):
                    removed_expectations.append(
                        self.expectation_configurations.pop(index)
                    )
                return removed_expectations
            else:
                raise ValueError(
                    "More than one matching expectation was found. Specify more precise matching criteria,"
                    "or set remove_multiple_matches=True"
                )

        else:
            return [self.expectation_configurations.pop(found_expectation_indexes[0])]

    def remove_all_expectations_of_type(
        self, expectation_types: Union[List[str], str]
    ) -> List[ExpectationConfiguration]:
        if isinstance(expectation_types, str):
            expectation_types = [expectation_types]

        removed_expectations = [
            expectation
            for expectation in self.expectation_configurations
            if expectation.expectation_type in expectation_types
        ]
        self.expectation_configurations = [
            expectation
            for expectation in self.expectation_configurations
            if expectation.expectation_type not in expectation_types
        ]

        return removed_expectations

    def find_expectation_indexes(
        self,
        expectation_configuration: Optional[ExpectationConfiguration] = None,
        match_type: str = "domain",
        ge_cloud_id: Optional[str] = None,
    ) -> List[int]:
        """
        Find indexes of Expectations matching the given ExpectationConfiguration on the given match_type.
        If a ge_cloud_id is provided, match_type is ignored and only indexes of Expectations
        with matching ge_cloud_id are returned.

        Args:
            expectation_configuration: A potentially incomplete (partial) Expectation Configuration to match against to
                find the index of any matching Expectation Configurations on the suite.
            match_type: This determines what kwargs to use when matching. Options are 'domain' to match based
                on the data evaluated by that expectation, 'success' to match based on all configuration parameters
                 that influence whether an expectation succeeds based on a given batch of data, and 'runtime' to match
                 based on all configuration parameters
            ge_cloud_id: Great Expectations Cloud id

        Returns: A list of indexes of matching ExpectationConfiguration

        Raises:
            InvalidExpectationConfigurationError

        """
        if expectation_configuration is None and ge_cloud_id is None:
            raise TypeError(
                "Must provide either expectation_configuration or ge_cloud_id"
            )

        if expectation_configuration and not isinstance(
            expectation_configuration, ExpectationConfiguration
        ):
            raise gx_exceptions.InvalidExpectationConfigurationError(
                "Ensure that expectation configuration is valid."
            )

        match_indexes = []
        for idx, expectation in enumerate(self.expectation_configurations):
            if ge_cloud_id is not None:
                if expectation.ge_cloud_id == ge_cloud_id:
                    match_indexes.append(idx)
            else:  # noqa: PLR5501
                if expectation.isEquivalentTo(
                    other=expectation_configuration, match_type=match_type  # type: ignore[arg-type]
                ):
                    match_indexes.append(idx)

        return match_indexes

    @public_api
    def find_expectations(
        self,
        expectation_configuration: Optional[ExpectationConfiguration] = None,
        match_type: str = "domain",
        ge_cloud_id: Optional[str] = None,
    ) -> List[ExpectationConfiguration]:
        """
        Find Expectations matching the given ExpectationConfiguration on the given match_type.
        If a ge_cloud_id is provided, match_type is ignored and only Expectations with matching
        ge_cloud_id are returned.

        Args:
            expectation_configuration: A potentially incomplete (partial) Expectation Configuration to match against to
                find the index of any matching Expectation Configurations on the suite.
            match_type: This determines what kwargs to use when matching. Options are 'domain' to match based
                on the data evaluated by that expectation, 'success' to match based on all configuration parameters
                 that influence whether an expectation succeeds based on a given batch of data, and 'runtime' to match
                 based on all configuration parameters
            ge_cloud_id: Great Expectations Cloud id

        Returns: A list of matching ExpectationConfigurations
        """

        if expectation_configuration is None and ge_cloud_id is None:
            raise TypeError(
                "Must provide either expectation_configuration or ge_cloud_id"
            )

        found_expectation_indexes: List[int] = self.find_expectation_indexes(
            expectation_configuration, match_type, ge_cloud_id
        )

        if len(found_expectation_indexes) > 0:
            return [
                self.expectation_configurations[idx]
                for idx in found_expectation_indexes
            ]

        return []

    def replace_expectation(
        self,
        new_expectation_configuration: Union[ExpectationConfiguration, dict],
        existing_expectation_configuration: Optional[ExpectationConfiguration] = None,
        match_type: str = "domain",
        ge_cloud_id: Optional[str] = None,
    ) -> None:
        """
        Find Expectations matching the given ExpectationConfiguration on the given match_type.
        If a ge_cloud_id is provided, match_type is ignored and only Expectations with matching
        ge_cloud_id are returned.

        Args:
            expectation_configuration: A potentially incomplete (partial) Expectation Configuration to match against to
                find the index of any matching Expectation Configurations on the suite.
            match_type: This determines what kwargs to use when matching. Options are 'domain' to match based
                on the data evaluated by that expectation, 'success' to match based on all configuration parameters
                 that influence whether an expectation succeeds based on a given batch of data, and 'runtime' to match
                 based on all configuration parameters
            ge_cloud_id: Great Expectations Cloud id

        Returns: A list of matching ExpectationConfigurations
        """
        if existing_expectation_configuration is None and ge_cloud_id is None:
            raise TypeError(
                "Must provide either existing_expectation_configuration or ge_cloud_id"
            )

        if isinstance(new_expectation_configuration, dict):
            new_expectation_configuration = expectationConfigurationSchema.load(
                new_expectation_configuration
            )

        found_expectation_indexes = self.find_expectation_indexes(
            existing_expectation_configuration, match_type, ge_cloud_id
        )
        if len(found_expectation_indexes) > 1:
            raise ValueError(
                "More than one matching expectation was found. Please be more specific with your search "
                "criteria"
            )
        elif len(found_expectation_indexes) == 0:
            raise ValueError("No matching Expectation was found.")

        self.expectation_configurations[found_expectation_indexes[0]] = new_expectation_configuration  # type: ignore[assignment]

    def _add_expectation(
        self,
        expectation_configuration: ExpectationConfiguration,
        send_usage_event: bool = True,
        match_type: str = "domain",
        overwrite_existing: bool = True,
    ) -> ExpectationConfiguration:
        """
        This is a private method for adding expectations that allows for usage_events to be suppressed when
        Expectations are added through internal processing (ie. while building profilers, rendering or validation). It
        takes in send_usage_event boolean.  If successful, upserts ExpectationConfiguration into this ExpectationSuite.

        Args:
            expectation_configuration: The ExpectationConfiguration to add or update
            send_usage_event: Whether to send a usage_statistics event. When called through ExpectationSuite class'
                public add_expectation() method, this is set to `True`.
            match_type: The criteria used to determine whether the Suite already has an ExpectationConfiguration
                and so whether we should add or replace.
            overwrite_existing: If the expectation already exists, this will overwrite if True and raise an error if
                False.

        Returns:
            The ExpectationConfiguration to add or replace.

        Raises:
            More than one match
            One match if overwrite_existing = False
        """

        found_expectation_indexes = self.find_expectation_indexes(
            expectation_configuration, match_type
        )

        if len(found_expectation_indexes) > 1:
            if send_usage_event:
                self.send_usage_event(success=False)
            raise ValueError(
                "More than one matching expectation was found. Please be more specific with your search "
                "criteria"
            )
        elif len(found_expectation_indexes) == 1:
            # Currently, we completely replace the expectation_configuration, but we could potentially use patch_expectation
            # to update instead. We need to consider how to handle meta in that situation.
            # patch_expectation = jsonpatch.make_patch(self.expectations[found_expectation_index] \
            #   .kwargs, expectation_configuration.kwargs)
            # patch_expectation.apply(self.expectations[found_expectation_index].kwargs, in_place=True)
            if overwrite_existing:
                # if existing Expectation has a ge_cloud_id, add it back to the new Expectation Configuration
                existing_expectation_ge_cloud_id = self.expectation_configurations[
                    found_expectation_indexes[0]
                ].ge_cloud_id
                if existing_expectation_ge_cloud_id is not None:
                    expectation_configuration.ge_cloud_id = (
                        existing_expectation_ge_cloud_id
                    )

                self.expectation_configurations[
                    found_expectation_indexes[0]
                ] = expectation_configuration
            else:
                if send_usage_event:
                    self.send_usage_event(success=False)

                raise gx_exceptions.DataContextError(
                    "A matching ExpectationConfiguration already exists. If you would like to overwrite this "
                    "ExpectationConfiguration, set overwrite_existing=True"
                )
        else:
            self.append_expectation(expectation_configuration)

        if send_usage_event:
            self.send_usage_event(success=True)

        return expectation_configuration

    def send_usage_event(self, success: bool) -> None:
        usage_stats_event_payload: dict = {}
        if self._data_context is not None:
            self._data_context.send_usage_message(
                event=UsageStatsEvents.EXPECTATION_SUITE_ADD_EXPECTATION,
                event_payload=usage_stats_event_payload,
                success=success,
            )

    def add_expectation_configurations(
        self,
        expectation_configurations: List[ExpectationConfiguration],
        send_usage_event: bool = True,
        match_type: str = "domain",
        overwrite_existing: bool = True,
    ) -> List[ExpectationConfiguration]:
        """Upsert a list of ExpectationConfigurations into this ExpectationSuite.

        Args:
            expectation_configurations: The List of candidate new/modifed "ExpectationConfiguration" objects for Suite.
            send_usage_event: Whether to send a usage_statistics event. When called through ExpectationSuite class'
                public add_expectation() method, this is set to `True`.
            match_type: The criteria used to determine whether the Suite already has an "ExpectationConfiguration"
                object, matching the specified criteria, and thus whether we should add or replace (i.e., "upsert").
            overwrite_existing: If "ExpectationConfiguration" already exists, this will cause it to be overwritten if
                True and raise an error if False.

        Returns:
            The List of "ExpectationConfiguration" objects attempted to be added or replaced (can differ from the list
            of "ExpectationConfiguration" objects in "self.expectations" at the completion of this method's execution).

        Raises:
            More than one match
            One match if overwrite_existing = False
        """
        expectation_configuration: ExpectationConfiguration
        expectation_configurations_attempted_to_be_added: List[
            ExpectationConfiguration
        ] = [
            self.add_expectation(
                expectation_configuration=expectation_configuration,
                send_usage_event=send_usage_event,
                match_type=match_type,
                overwrite_existing=overwrite_existing,
            )
            for expectation_configuration in expectation_configurations
        ]
        return expectation_configurations_attempted_to_be_added

    @public_api
    def add_expectation(
        self,
        expectation_configuration: ExpectationConfiguration,
        send_usage_event: bool = True,
        match_type: str = "domain",
        overwrite_existing: bool = True,
    ) -> ExpectationConfiguration:
        """Upsert specified ExpectationConfiguration into this ExpectationSuite.

        Args:
            expectation_configuration: The ExpectationConfiguration to add or update.
            send_usage_event: Whether to send a usage_statistics event. When called through ExpectationSuite class'
                public add_expectation() method, this is set to `True`.
            match_type: The criteria used to determine whether the Suite already has an ExpectationConfiguration
                and so whether we should add or replace.
            overwrite_existing: If the expectation already exists, this will overwrite if True and raise an error if
                False.

        Returns:
            The ExpectationConfiguration to add or replace.

        Raises:
            ValueError: More than one match
            DataContextError: One match if overwrite_existing = False

        # noqa: DAR402
        """
        self._build_expectation(expectation_configuration)
        return self._add_expectation(
            expectation_configuration=expectation_configuration,
            send_usage_event=send_usage_event,
            match_type=match_type,
            overwrite_existing=overwrite_existing,
        )

    def _build_expectation(
        self, expectation_configuration: ExpectationConfiguration
    ) -> Expectation:
        try:
            class_ = get_expectation_impl(expectation_configuration.expectation_type)
            expectation = class_(
                meta=expectation_configuration.meta, **expectation_configuration.kwargs
            )  # Implicitly validates in constructor
            return expectation
        except (
            gx_exceptions.ExpectationNotFoundError,
            gx_exceptions.InvalidExpectationConfigurationError,
        ) as e:
            raise gx_exceptions.InvalidExpectationConfigurationError(
                f"Could not add expectation; provided configuration is not valid: {e.message}"
            ) from e

    def render(self) -> None:
        """
        Renders content using the atomic prescriptive renderer for each expectation configuration associated with
           this ExpectationSuite to ExpectationConfiguration.rendered_content.
        """
        for expectation_configuration in self.expectation_configurations:
            inline_renderer_config: InlineRendererConfig = {
                "class_name": "InlineRenderer",
                "render_object": expectation_configuration,
            }
            module_name = "great_expectations.render.renderer.inline_renderer"
            inline_renderer = instantiate_class_from_config(
                config=inline_renderer_config,
                runtime_environment={},
                config_defaults={"module_name": module_name},
            )
            if not inline_renderer:
                raise gx_exceptions.ClassInstantiationError(
                    module_name=module_name,
                    package_name=None,
                    class_name=inline_renderer_config["class_name"],
                )

            rendered_content: List[
                RenderedAtomicContent
            ] = inline_renderer.get_rendered_content()

            expectation_configuration.rendered_content = inline_renderer.replace_or_keep_existing_rendered_content(
                existing_rendered_content=expectation_configuration.rendered_content,
                new_rendered_content=rendered_content,
                failed_renderer_type=AtomicPrescriptiveRendererType.FAILED,
            )


class ExpectationSuiteSchema(Schema):
    expectation_suite_name = fields.Str()
    ge_cloud_id = fields.UUID(required=False, allow_none=True)
    expectations = fields.List(fields.Nested(ExpectationConfigurationSchema))
    evaluation_parameters = fields.Dict(allow_none=True)
    data_asset_type = fields.Str(allow_none=True)
    meta = fields.Dict()

    # NOTE: 20191107 - JPC - we may want to remove clean_empty and update tests to require the other fields;
    # doing so could also allow us not to have to make a copy of data in the pre_dump method.
    # noinspection PyMethodMayBeStatic
    def clean_empty(self, data):
        if isinstance(data, ExpectationSuite):
            if not hasattr(data, "evaluation_parameters"):
                pass
            elif len(data.evaluation_parameters) == 0:
                del data.evaluation_parameters

            if not hasattr(data, "meta"):
                pass
            elif data.meta is None or data.meta == []:
                pass
            elif len(data.meta) == 0:
                del data.meta
        elif isinstance(data, dict):
            if not data.get("evaluation_parameters"):
                pass
            elif len(data.get("evaluation_parameters")) == 0:
                data.pop("evaluation_parameters")

            if not data.get("meta"):
                pass
            elif data.get("meta") is None or data.get("meta") == []:
                pass
            elif len(data.get("meta")) == 0:
                data.pop("meta")
        return data

    # noinspection PyUnusedLocal
    @pre_dump
    def prepare_dump(self, data, **kwargs):
        data = deepcopy(data)
        for key in data:
            if key.startswith("_"):
                continue
            data[key] = convert_to_json_serializable(data[key])

        data = self.clean_empty(data)
        return data

    @post_dump(pass_original=True)
    def insert_expectations(self, data, original_data, **kwargs) -> dict:
        if isinstance(original_data, dict):
            expectations = original_data.get("expectations", [])
        else:
            expectations = original_data.expectation_configurations
        data["expectations"] = convert_to_json_serializable(expectations)
        return data

    @post_load
    def _convert_uuids_to_str(self, data, **kwargs):
        """
        Utilize UUID for data validation but convert to string before usage in business logic
        """
        attr = "ge_cloud_id"
        uuid_val = data.get(attr)
        if uuid_val:
            data[attr] = str(uuid_val)
        return data


expectationSuiteSchema = ExpectationSuiteSchema()
