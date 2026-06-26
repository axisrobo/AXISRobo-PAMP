from app.architecture_review.ai.agent_watch import AgentWatchAdapter


def test_agent_watch_adapter_is_safe_when_disabled(monkeypatch):
    # agent_watch reads `settings` locally via `from app.config import settings`, so patch the
    # settings object directly rather than a (non-existent) agent_watch.settings submodule.
    from app.config import settings
    monkeypatch.setattr(settings, "AGENT_WATCH_ENABLED", False)
    adapter = AgentWatchAdapter()

    assert adapter.enabled is False
    assert adapter.generate_trace_id()
    assert adapter.generate_span_id()

    adapter.send_request(action="noop")
    adapter.receive_request(action="noop")
    adapter.receive_response(action="noop")
