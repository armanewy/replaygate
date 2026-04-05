"""Generate real Temporal history fixtures for local replay tests."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from examples.temporal.fixture_workflows import LegacyWorkflow, PaymentWorkflow, RefundWorkflow

OUTPUT_DIR = Path(__file__).parent / "histories"


async def run_workflow(
    env: WorkflowEnvironment,
    workflow_run: Any,
    *args: Any,
    workflow_id: str,
    output_name: str,
) -> None:
    handle = await env.client.start_workflow(
        workflow_run,
        *args,
        id=workflow_id,
        task_queue="replay-gate-fixtures",
    )
    await handle.result()
    history = await handle.fetch_history()
    history_json = history.to_json_dict()
    workflow_type = history_json["events"][0]["workflowExecutionStartedEventAttributes"][
        "workflowType"
    ]["name"]

    envelope = {
        "workflow_id": workflow_id,
        "run_id": handle.result_run_id,
        "workflow_type": workflow_type,
        "history": history_json,
        "metadata": {
            "engine": "temporal",
            "generated_by": "examples/temporal/generate_histories.py",
            "sanitized": True,
        },
    }

    output_path = OUTPUT_DIR / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")


async def main() -> None:
    env = await WorkflowEnvironment.start_time_skipping()
    try:
        async with Worker(
            env.client,
            task_queue="replay-gate-fixtures",
            workflows=[PaymentWorkflow, RefundWorkflow, LegacyWorkflow],
        ):
            await run_workflow(
                env,
                PaymentWorkflow.run,
                1200,
                workflow_id="payment-demo",
                output_name="payment_history.json",
            )
            await run_workflow(
                env,
                RefundWorkflow.run,
                "refund-42",
                workflow_id="refund-demo",
                output_name="refund_history.json",
            )
            await run_workflow(
                env,
                LegacyWorkflow.run,
                "legacy-7",
                workflow_id="legacy-demo",
                output_name="legacy_history.json",
            )
    finally:
        await env.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
