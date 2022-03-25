from typing import Any, Optional

from great_expectations.core.usage_statistics.anonymizers.base import BaseAnonymizer
from great_expectations.validation_operators.validation_operators import (
    ValidationOperator,
)


class ValidationOperatorAnonymizer(BaseAnonymizer):
    def __init__(
        self,
        salt: Optional[str],
        aggregate_anonymizer: Optional["Anonymizer"] = None,  # noqa: F821
    ) -> None:
        super().__init__(salt=salt)

        if aggregate_anonymizer:
            self._aggregate_anonymizer = aggregate_anonymizer
        else:
            from great_expectations.core.usage_statistics.anonymizers.anonymizer import (
                Anonymizer,
            )

            self._aggregate_anonymizer = Anonymizer(salt=salt)

    def anonymize(
        self,
        validation_operator_obj: ValidationOperator,
        validation_operator_name: str,
        obj: Optional[object] = None,
    ) -> Any:
        anonymized_info_dict: dict = {
            "anonymized_name": self._anonymize_string(validation_operator_name)
        }
        actions_dict: dict = validation_operator_obj.actions

        anonymized_info_dict.update(
            self._anonymize_object_info(
                object_=validation_operator_obj,
                anonymized_info_dict=anonymized_info_dict,
            )
        )

        if actions_dict:
            anonymized_info_dict["anonymized_action_list"] = [
                self._aggregate_anonymizer.anonymize(
                    action_name=action_name, action_obj=action_obj
                )
                for action_name, action_obj in actions_dict.items()
            ]

        return anonymized_info_dict

    @staticmethod
    def can_handle(obj: Optional[object] = None, **kwargs) -> bool:
        return (
            obj is not None
            and isinstance(obj, ValidationOperator)
            and "validation_operator_name" in kwargs
        )
