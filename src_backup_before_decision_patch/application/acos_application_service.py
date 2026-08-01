"""
Central application service for executing the ACOS
multi-agent decision pipeline.
"""

from __future__ import annotations

from typing import Any, Iterable, List, Optional

from agents.inventory_agent import InventoryAgent
from agents.marketing_agent import MarketingAgent
from agents.pricing_agent import PricingAgent
from kernel.decision_manager import DecisionManager
from models.acos_run_result import ACOSRunResult
from models.business_state import BusinessState
from models.commerce_decision import CommerceDecision
from reasoning.inventory_reasoner import InventoryReasoner
from reasoning.marketing_reasoner import MarketingReasoner
from reasoning.rule_reasoner import RuleReasoner


class ACOSApplicationService:
    """
    Main orchestration service for one ACOS decision cycle.

    The service:

    1. Sends BusinessState to all agents
    2. Generates CommerceDecision proposals
    3. Registers proposals with DecisionManager
    4. Detects conflicts
    5. Runs negotiation when required
    6. Runs MOCRA resolution
    7. Produces the final decision
    """

    def __init__(
        self,
        agents: Optional[Iterable[Any]] = None,
        decision_manager: Optional[
            DecisionManager
        ] = None,
        fail_fast: bool = True,
    ) -> None:
        self.agents = list(
            agents or self._build_default_agents()
        )

        if not self.agents:
            raise ValueError(
                "At least one ACOS agent is required."
            )

        self.decision_manager = (
            decision_manager
            or DecisionManager()
        )

        self.fail_fast = fail_fast

    @staticmethod
    def _build_default_agents() -> List[Any]:
        return [
            PricingAgent(
                RuleReasoner()
            ),
            InventoryAgent(
                InventoryReasoner()
            ),
            MarketingAgent(
                MarketingReasoner()
            ),
        ]

    def run(
        self,
        business_state: BusinessState,
    ) -> ACOSRunResult:
        """
        Execute a complete ACOS decision cycle.
        """

        self._validate_business_state(
            business_state
        )

        result = ACOSRunResult(
            business_state=business_state,
            status="RUNNING",
            metadata={
                "agent_names": [
                    self._get_agent_name(agent)
                    for agent in self.agents
                ],
                "negotiation_required": False,
            },
        )

        try:
            self._clear_previous_pending_proposals()

            proposals = self._generate_proposals(
                business_state=business_state,
                result=result,
            )

            result.proposals = proposals

            self._register_proposals(
                proposals
            )

            conflicts = (
                self.decision_manager
                .detect_conflicts()
            )

            result.conflicts = list(
                conflicts or []
            )

            negotiation_required = bool(
                self.decision_manager
                .has_negotiation_required()
            )

            result.metadata[
                "negotiation_required"
            ] = negotiation_required

            if negotiation_required:
                result.negotiation_result = (
                    self.decision_manager
                    .negotiate_pending_proposals()
                )

            result.mocra_result = (
                self.decision_manager
                .resolve_pending_proposals()
            )

            result.final_decision = (
                self.decision_manager
                .make_final_decision()
            )

            if result.final_decision is None:
                raise RuntimeError(
                    "DecisionManager did not produce "
                    "a final decision."
                )

            result.status = "COMPLETED"

        except Exception as error:
            result.status = "FAILED"
            result.errors.append(
                f"{type(error).__name__}: {error}"
            )

            if self.fail_fast:
                raise

        return result

    def run_safely(
        self,
        business_state: BusinessState,
    ) -> ACOSRunResult:
        """
        Execute ACOS without propagating runtime errors.

        Useful for experiments and batch simulations where
        one failed scenario should not stop the full batch.
        """

        original_fail_fast = self.fail_fast

        try:
            self.fail_fast = False

            return self.run(
                business_state
            )

        finally:
            self.fail_fast = original_fail_fast

    def generate_proposals_only(
        self,
        business_state: BusinessState,
    ) -> List[CommerceDecision]:
        """
        Generate agent proposals without running negotiation
        or final decision selection.
        """

        self._validate_business_state(
            business_state
        )

        temporary_result = ACOSRunResult(
            business_state=business_state,
            status="RUNNING",
        )

        return self._generate_proposals(
            business_state=business_state,
            result=temporary_result,
        )

    def _generate_proposals(
        self,
        *,
        business_state: BusinessState,
        result: ACOSRunResult,
    ) -> List[CommerceDecision]:
        proposals: List[
            CommerceDecision
        ] = []

        for agent in self.agents:
            agent_name = self._get_agent_name(
                agent
            )

            try:
                agent.observe(
                    business_state
                )

                agent.analyze()

                proposal = (
                    agent.generate_decision()
                )

                if not isinstance(
                    proposal,
                    CommerceDecision,
                ):
                    raise TypeError(
                        f"{agent_name} returned "
                        f"{type(proposal).__name__}; "
                        "expected CommerceDecision."
                    )

                proposals.append(
                    proposal
                )

            except Exception as error:
                error_message = (
                    f"{agent_name} failed: "
                    f"{type(error).__name__}: "
                    f"{error}"
                )

                result.errors.append(
                    error_message
                )

                if self.fail_fast:
                    raise RuntimeError(
                        error_message
                    ) from error

        if not proposals:
            raise RuntimeError(
                "No agent proposals were generated."
            )

        return proposals

    def _register_proposals(
        self,
        proposals: Iterable[
            CommerceDecision
        ],
    ) -> None:
        for proposal in proposals:
            self.decision_manager.add_proposal(
                proposal
            )

    def _clear_previous_pending_proposals(
        self,
    ) -> None:
        """
        Remove pending proposals left by a previous run.

        This allows the same application-service instance to
        be reused safely for multiple decision cycles.
        """

        pending = list(
            self.decision_manager
            .get_pending_proposals()
            or []
        )

        for proposal in pending:
            proposal_id = getattr(
                proposal,
                "proposal_id",
                None,
            )

            if proposal_id:
                self.decision_manager.remove_proposal(
                    proposal_id
                )

    @staticmethod
    def _get_agent_name(
        agent: Any,
    ) -> str:
        name = getattr(
            agent,
            "name",
            None,
        )

        if name:
            return str(name)

        agent_name_method = getattr(
            agent,
            "agent_name",
            None,
        )

        if callable(agent_name_method):
            return str(
                agent_name_method()
            )

        return agent.__class__.__name__

    @staticmethod
    def _validate_business_state(
        business_state: BusinessState,
    ) -> None:
        if business_state is None:
            raise ValueError(
                "business_state cannot be None."
            )

        if not isinstance(
            business_state,
            BusinessState,
        ):
            raise TypeError(
                "business_state must be a "
                "BusinessState instance."
            )

        if not isinstance(
            business_state.metrics,
            dict,
        ):
            raise TypeError(
                "business_state.metrics must "
                "be a dictionary."
            )

        if not isinstance(
            business_state.market,
            dict,
        ):
            raise TypeError(
                "business_state.market must "
                "be a dictionary."
            )

        required_metrics = {
            "product_id",
            "inventory",
            "conversion_rate",
        }

        required_market = {
            "demand",
            "advertising_cost",
        }

        missing_metrics = (
            required_metrics
            - business_state.metrics.keys()
        )

        missing_market = (
            required_market
            - business_state.market.keys()
        )

        if missing_metrics:
            raise ValueError(
                "BusinessState is missing metrics: "
                + ", ".join(
                    sorted(missing_metrics)
                )
            )

        if missing_market:
            raise ValueError(
                "BusinessState is missing market values: "
                + ", ".join(
                    sorted(missing_market)
                )
            )