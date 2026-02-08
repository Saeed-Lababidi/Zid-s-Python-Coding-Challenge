import threading
import time
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

class SimpleMessageBroker:
    """
    A simple in-memory message broker to simulate asynchronous task processing.
    In a production environment, this would be replaced by Redis/Celery or RabbitMQ.
    """
    
    def __init__(self):
        self.queue = []
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()

    def enqueue(self, task: Callable, *args, **kwargs):
        """Add a task to the queue."""
        logger.info(f"Enqueuing task: {task.__name__}")
        self.queue.append((task, args, kwargs))

    def _process_queue(self):
        """Worker loop to process tasks."""
        while True:
            if self.queue:
                task, args, kwargs = self.queue.pop(0)
                try:
                    logger.info(f"Processing task: {task.__name__}")
                    task(*args, **kwargs)
                    logger.info(f"Task {task.__name__} completed successfully.")
                except Exception as e:
                    logger.error(f"Task {task.__name__} failed: {e}")
            else:
                time.sleep(1)

# Global instance
broker = SimpleMessageBroker()

def async_task(func):
    """Decorator to offload function execution to the broker."""
    def wrapper(*args, **kwargs):
        broker.enqueue(func, *args, **kwargs)
    return wrapper
