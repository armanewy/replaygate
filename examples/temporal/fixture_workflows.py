"""Source workflows used to generate replay fixtures."""

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow


@workflow.defn
class PaymentWorkflow:
    @workflow.run
    async def run(self, amount: int) -> str:
        await workflow.sleep(timedelta(seconds=1))
        return f"approved:{amount}"


@workflow.defn
class RefundWorkflow:
    @workflow.run
    async def run(self, reference: str) -> str:
        await workflow.sleep(timedelta(seconds=1))
        return f"refunded:{reference}"


@workflow.defn
class LegacyWorkflow:
    @workflow.run
    async def run(self, reference: str) -> str:
        await workflow.sleep(timedelta(seconds=1))
        return f"legacy:{reference}"
