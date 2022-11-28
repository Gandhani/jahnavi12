from typing import Optional

from great_expectations.core import (
    ExpectationConfiguration,
    ExpectationValidationResult,
)
from great_expectations.expectations.expectation import (
    TableExpectation,
    render_evaluation_parameter_string,
)
from great_expectations.render import LegacyDiagnosticRendererType, LegacyRendererType
from great_expectations.render.renderer.renderer import renderer


class ExpectColumnParameterizedDistributionKsTestPValueToBeGreaterThan(
    TableExpectation
):
    # This expectation is a stub - it needs migration to the modular expectation API

    # This dictionary contains metadata for display in the public gallery
    library_metadata = {
        "maturity": "production",
        "tags": [
            "core expectation",
            "column aggregate expectation",
            "needs migration to modular expectations api",
        ],
        "contributors": ["@great_expectations"],
        "requirements": [],
    }

    metric_dependencies = tuple()
    success_keys = ()
    default_kwarg_values = {}
    args_keys = ()

    @classmethod
    @renderer(renderer_type=LegacyRendererType.PRESCRIPTIVE)
    @render_evaluation_parameter_string
    def _prescriptive_renderer(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        language: Optional[str] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> None:
        pass

    @classmethod
    @renderer(renderer_type=LegacyDiagnosticRendererType.OBSERVED_VALUE)
    def _diagnostic_observed_value_renderer(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        language: Optional[str] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> None:
        pass
