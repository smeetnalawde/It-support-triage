"""End-to-end test through the real ADK Runner. Self-skips without model creds
so CI stays green; runs locally after `gcloud auth application-default login`."""

import os

import pytest

_HAS_CREDS = bool(
    os.environ.get("GOOGLE_CLOUD_PROJECT")
    or os.environ.get("GOOGLE_API_KEY")
    or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
)

pytestmark = pytest.mark.skipif(not _HAS_CREDS, reason="no model credentials configured")


@pytest.mark.asyncio
async def test_multi_domain_fan_out_end_to_end():
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    from root_orch.agent import root_agent

    runner = InMemoryRunner(agent=root_agent, app_name="it-support-test")
    session = await runner.session_service.create_session(
        app_name="it-support-test", user_id="tester"
    )

    prompt = "I'm smeet — my VPN won't connect and I also need a figma license approved."
    message = types.Content(role="user", parts=[types.Part(text=prompt)])

    final_text = ""
    async for event in runner.run_async(
        user_id="tester", session_id=session.id, new_message=message
    ):
        if event.is_final_response() and event.content:
            final_text = "".join(p.text or "" for p in event.content.parts)

    assert final_text
    lowered = final_text.lower()
    assert "vpn" in lowered
    assert "figma" in lowered or "license" in lowered
