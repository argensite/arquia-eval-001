"""Exercise application-owned authorization guards through two native SDKs."""

import asyncio
import json
import platform
from importlib.metadata import version
from typing import TypedDict

from google.adk.agents import LlmAgent
from google.adk.models import BaseLlm, LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class Policy:
    """In-memory authority operated by the test harness outside the SDK state."""

    def __init__(self):
        self.current = "granted"
        self.reads = []

    def check(self, operation):
        current = self.current
        self.reads.append([operation, current])
        return current


class GraphState(TypedDict, total=False):
    decision: str


def exercise_langgraph(permission, human_approved=True):
    policy = Policy()
    effects = []

    def apply_change(state):
        if interrupt({"operation": "record_change"}) is not True:
            return {"decision": "not_approved"}
        decision = policy.check("record_change")
        if decision == "granted":
            effects.append("record_change")
        return {"decision": decision}

    graph = StateGraph(GraphState)
    graph.add_node("apply_change", apply_change)
    graph.add_edge(START, "apply_change")
    graph.add_edge("apply_change", END)
    app = graph.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "native-revocation-fixture"}}

    paused = app.invoke({}, config)
    pause_witness = [item.value for item in paused.get("__interrupt__", ())]
    before_resume = {"policy_reads": list(policy.reads), "effects": list(effects)}
    policy.current = permission
    result = app.invoke(Command(resume=human_approved), config)

    return {
        "interrupts": pause_witness,
        "before_resume": before_resume,
        "decision": result["decision"],
        "policy_reads": policy.reads,
        "effects": effects,
    }


class ScriptedModel(BaseLlm):
    """Supply tool requests from local fixture data, without a provider client."""

    async def generate_content_async(self, llm_request, stream=False):
        replies = [
            part.function_response.name
            for content in llm_request.contents
            for part in content.parts or ()
            if part.function_response is not None
        ]
        if not replies:
            part = types.Part.from_function_call(name="record_start", args={})
        elif replies == ["record_start"]:
            part = types.Part.from_function_call(name="record_finish", args={})
        else:
            part = types.Part.from_text(text="Fixture complete")
        yield LlmResponse(
            content=types.Content(role="model", parts=[part]),
            usage_metadata=types.GenerateContentResponseUsageMetadata(
                prompt_token_count=0, candidates_token_count=0, total_token_count=0
            ),
        )


async def exercise_adk(permission):
    policy = Policy()
    effects = []

    def record_start() -> dict:
        """Record the first marker in the in-memory test sink."""
        effects.append("record_start")
        return {"decision": "granted"}

    def record_finish() -> dict:
        """Record the second marker in the in-memory test sink."""
        effects.append("record_finish")
        return {"decision": "granted"}

    def before_tool(tool, args, tool_context):
        decision = policy.check(tool.name)
        if decision != "granted":
            return {"decision": decision}
        return None

    agent = LlmAgent(
        name="guarded_fixture",
        model=ScriptedModel(model="local-scripted"),
        tools=[record_start, record_finish],
        before_tool_callback=before_tool,
    )
    runner = InMemoryRunner(agent=agent, app_name="guarded_fixture")
    try:
        session = await runner.session_service.create_session(
            app_name=runner.app_name, user_id="fixture-operator"
        )
        replies = []
        invocation_ids = set()
        effects_before_change = []
        async for event in runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part(text="Run fixture")]),
        ):
            for reply in event.get_function_responses():
                if not event.invocation_id:
                    raise RuntimeError("Tool reply has no invocation identifier")
                invocation_ids.add(event.invocation_id)
                replies.append([reply.name, reply.response["decision"]])
                if reply.name == "record_start":
                    effects_before_change = list(effects)
                    policy.current = permission
        return {
            "tool_replies": replies,
            "tool_reply_invocations": len(invocation_ids),
            "effects_before_policy_change": effects_before_change,
            "policy_reads": policy.reads,
            "effects": effects,
        }
    finally:
        await runner.close()


def add_case(results, framework, case, expected, observed):
    results.append({
        "framework": framework,
        "case": case,
        "expected": expected,
        "observed": observed,
        "passed": observed == expected,
    })


def main():
    results = []
    for permission in ("granted", "revoked", "unavailable", "not_approved"):
        approved = permission != "not_approved"
        expected = {
            "interrupts": [{"operation": "record_change"}],
            "before_resume": {"policy_reads": [], "effects": []},
            "decision": permission,
            "policy_reads": [["record_change", permission]] if approved else [],
            "effects": ["record_change"] if permission == "granted" else [],
        }
        current = permission if approved else "granted"
        add_case(results, "langgraph", permission, expected, exercise_langgraph(current, approved))

    for permission in ("granted", "revoked", "unavailable"):
        expected = {
            "tool_replies": [["record_start", "granted"], ["record_finish", permission]],
            "tool_reply_invocations": 1,
            "effects_before_policy_change": ["record_start"],
            "policy_reads": [["record_start", "granted"], ["record_finish", permission]],
            "effects": ["record_start", "record_finish"] if permission == "granted" else ["record_start"],
        }
        add_case(results, "google-adk", permission, expected, asyncio.run(exercise_adk(permission)))

    print(json.dumps({
        "python": platform.python_version(),
        "sdk_versions": {name: version(name) for name in ("langgraph", "google-adk")},
        "cases": results,
    }, indent=2, sort_keys=True))
    return 0 if all(case["passed"] for case in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
