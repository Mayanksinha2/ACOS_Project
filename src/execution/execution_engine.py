from typing import Dict

from models.execution_result import ExecutionResult
from models.negotiation_result import NegotiationResult
from negotiation.mocra import MOCRAResult
from simulator.product import Product


class ExecutionEngine:
    """
    Applies negotiated or MOCRA-selected decisions
    to products in the commerce environment.
    """

    def __init__(
        self,
        products: Dict[str, Product]
    ):
        self.products = products

    def execute_final_result(
        self,
        final_decision
    ) -> ExecutionResult:
        """
        Execute the output returned by
        DecisionManager.make_final_decision().
        """

        decision_type = final_decision.get(
            "decision_type"
        )

        result = final_decision.get(
            "result"
        )

        if decision_type == "NEGOTIATED":
            return self._execute_negotiated(
                result
            )

        if decision_type == "MOCRA":
            return self._execute_mocra(
                result
            )

        raise ValueError(
            f"Unsupported decision type: {decision_type}"
        )

    def _execute_negotiated(
        self,
        result: NegotiationResult
    ) -> ExecutionResult:

        product = self._get_product(
            result.target
        )

        previous_price = product.selling_price

        updated_price = (
            product.apply_price_percentage(
                operation=result.final_operation,
                percentage=result.final_value
            )
        )

        return ExecutionResult(
            target=result.target,
            action_type="PRICE_CHANGE",
            operation=result.final_operation,
            success=True,
            previous_state={
                "selling_price": previous_price
            },
            updated_state={
                "selling_price": updated_price
            },
            message=(
                "Negotiated price action executed "
                "successfully."
            ),
            source="NEGOTIATION"
        )

    def _execute_mocra(
        self,
        result: MOCRAResult
    ) -> ExecutionResult:

        decision = result.winning_decision
        action = decision.business_action

        product = self._get_product(
            action.target
        )

        previous_price = product.selling_price

        operation, value = (
            self._extract_price_action(
                action
            )
        )

        updated_price = (
            product.apply_price_percentage(
                operation=operation,
                percentage=value
            )
        )

        decision.execution_status = "EXECUTED"

        return ExecutionResult(
            target=action.target,
            action_type="PRICE_CHANGE",
            operation=operation,
            success=True,
            previous_state={
                "selling_price": previous_price
            },
            updated_state={
                "selling_price": updated_price
            },
            message=(
                "MOCRA-selected price action executed "
                "successfully."
            ),
            source="MOCRA"
        )

    def _get_product(
        self,
        target: str
    ) -> Product:

        product = self.products.get(
            target
        )

        if product is None:
            raise KeyError(
                f"Product not found: {target}"
            )

        return product

    @staticmethod
    def _extract_price_action(action):

        if action.action_type == "PRICE_CHANGE":
            return (
                action.operation,
                float(action.value or 0)
            )

        metadata = getattr(
            action,
            "metadata",
            None
        ) or {}

        if not isinstance(metadata, dict):
            raise TypeError(
                "BusinessAction metadata must be a dictionary."
            )

        recommended_operation = metadata.get(
            "recommended_price_operation"
        )

        recommended_value = metadata.get(
            "recommended_price_value", 0
        )

        if recommended_operation is None:
            raise ValueError(
                "The selected action does not contain "
                "an executable price recommendation."
            )

        return (
            recommended_operation,
            float(recommended_value)
        )