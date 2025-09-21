import logging
from typing import Callable, Dict, List, Any

class SimpleEventBus:
    def __init__(self):
        self._subs: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_name: str, handler: Callable[[Any], None]):
        self._subs.setdefault(event_name, []).append(handler)

    def publish(self, event_name: str, payload: Any):
        handlers = self._subs.get(event_name, [])
        for h in handlers:
            try:
                h(payload)
            except Exception:
                logging.exception("Event handler error for %s", event_name)

event_bus = SimpleEventBus()
