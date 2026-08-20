import threading
import time

class RateLimiter:
    def __init__(self, max_calls, period=60):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = threading.Lock()

    def wait_if_needed(self):
        with self.lock:
            now = time.time()
            self.calls = [c for c in self.calls if now - c < self.period]
            
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            self.calls.append(time.time())

from backend.config import NIM_MAX_RPM, GEMINI_MAX_RPM
nim_limiter = RateLimiter(max_calls=NIM_MAX_RPM, period=60)
gemini_limiter = RateLimiter(max_calls=GEMINI_MAX_RPM, period=60)

