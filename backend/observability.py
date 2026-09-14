"""
ClaimBack Observability and Logging setup.
Provides structured logging and step tracing decorators.
"""
import logging
import json
import time
from functools import wraps

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("claimback")

def log_workflow_step(step_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.info(f"Starting workflow step: {step_name}")
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"Completed workflow step: {step_name} in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Failed workflow step: {step_name} after {duration:.3f}s - Error: {str(e)}")
                raise e
        return wrapper
    return decorator
