import threading
from traffic_counter.main import main


class CounterWorker:
    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()

    def start(self) -> bool:
        if self.is_running():
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=main,
            kwargs={"stop_event": self._stop_event},
            daemon=True,
        )
        self._thread.start()
        return True

    def stop(self) -> bool:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)
        return True

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
