"""Agent Watch adapter — delegates to EE module when enabled, no-op otherwise."""


class AgentWatchAdapter:
    def __init__(self):
        self._inner = None
        self._enabled = False
        self._initialized = False

    @property
    def enabled(self) -> bool:
        self._ensure_init()
        return self._enabled

    def _ensure_init(self):
        if self._initialized:
            return
        self._initialized = True
        from app.config import settings
        if settings.EE_ENABLED and settings.AGENT_WATCH_ENABLED:
            try:
                from app.ee.telemetry.agent_watch import agent_watch as _ee_aw
                self._inner = _ee_aw
                self._enabled = _ee_aw.enabled
            except Exception:
                pass

    def _call(self, method_name: str, payload: dict) -> None:
        self._ensure_init()
        if self._inner is not None:
            getattr(self._inner, method_name)(**payload)

    def generate_trace_id(self) -> str:
        self._ensure_init()
        if self._inner is not None:
            return self._inner.generate_trace_id()
        import uuid
        return uuid.uuid4().hex

    def generate_span_id(self) -> str:
        self._ensure_init()
        if self._inner is not None:
            return self._inner.generate_span_id()
        import uuid
        return uuid.uuid4().hex

    def send_request(self, **payload) -> None:
        self._call("send_request", payload)

    def receive_request(self, **payload) -> None:
        self._call("receive_request", payload)

    def receive_response(self, **payload) -> None:
        self._call("receive_response", payload)


agent_watch = AgentWatchAdapter()
