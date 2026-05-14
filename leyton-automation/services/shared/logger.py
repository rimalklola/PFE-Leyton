import json
import uuid
from datetime import datetime


class ServiceLogger:
    def __init__(self, service_name, correlation_id=None):
        self.service = service_name
        self.correlation_id = correlation_id or str(uuid.uuid4())

    def _emit(self, level, message, **kwargs):
        entry = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            "service": self.service,
            "level": level,
            "message": message,
            "correlation_id": self.correlation_id,
        }
        entry.update(kwargs)
        print(json.dumps(entry))

    def info(self, message, **kwargs):
        self._emit("INFO", message, **kwargs)

    def warning(self, message, **kwargs):
        self._emit("WARNING", message, **kwargs)

    def error(self, message, **kwargs):
        self._emit("ERROR", message, **kwargs)
