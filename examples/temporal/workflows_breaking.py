"""Intentionally incompatible candidate workflows for Replay Gate examples."""

from __future__ import annotations

from temporalio import workflow

from examples.temporal.fixture_workflows import RefundWorkflow


@workflow.defn(name="PaymentWorkflow")
class PaymentWorkflow:
    @workflow.run
    async def run(self, amount: int) -> str:
        return f"approved:{amount}"


__all__ = ["PaymentWorkflow", "RefundWorkflow"]
