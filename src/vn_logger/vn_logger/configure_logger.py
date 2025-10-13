from loguru import logger
import queue
import threading
import time
import requests  # or any other HTTP client
import json
import uuid
from .logger import project_id_var

log_queue = queue.Queue()
worker_thread = None
stop_worker = threading.Event()


def log_worker(jsonrpc_url: str):
    """
    The worker function that runs in a background thread.
    """

    while not stop_worker.is_set():
        try:
            log_message_str = log_queue.get(block=True, timeout=1)
            record = json.loads(log_message_str)['record']
            extra = record['extra']

            # Get event_type directly from extra data. Default to "log".
            event_type = extra.get("event_type", "log")

            # Construct the base params object
            params = {
                "function_id": extra.get('function_id'),
                "chain_id": extra.get('chain_id'),
                "parent_function_id": extra.get('parent_function_id'),
                "timestamp": record['time']['isoformat'],
                "duration_ms": extra.get('duration_ms'),
                "event_type": event_type,
                "message": record['message'],
                "payload": None,
                "result": None,
                "error": None
            }

            # Add event-specific fields based on the robust event_type
            if event_type == "enter":
                params["payload"] = {
                    "args": extra.get("args"),
                    "kwargs": extra.get("kwargs")
                }
            elif event_type == "exit":
                params["result"] = extra.get("result")
            elif event_type == "error":
                if record.get('exception'):
                    exc = record['exception']
                    params["error"] = {
                        "type": exc.get('type'),
                        "message": str(exc.get('value')),
                        "stacktrace": exc.get('traceback', False)
                    }

            jsonrpc_request = {
                "jsonrpc": "2.0",
                "method": "log.write",
                "params": params,
                "id": str(uuid.uuid4())
            }

            try:
                # (Request sending logic is unchanged)
                requests.post(jsonrpc_url, json=jsonrpc_request,
                              timeout=5).raise_for_status()
            except requests.RequestException as e:
                print(f"WORKER: Failed to send log - {e}")

            log_queue.task_done()
        except queue.Empty:
            # This is expected when the queue is empty.
            continue


def start_worker_thread(jsonrpc_url: str):
    """
    Starts the background worker thread.
    """
    global worker_thread
    if worker_thread is None or not worker_thread.is_alive():
        stop_worker.clear()
        worker_thread = threading.Thread(
            target=log_worker,
            args=(jsonrpc_url,),
            daemon=True
        )
        worker_thread.start()


def stop_worker_thread():
    """
    Stops the background worker thread gracefully.
    """
    # Wait for the queue to be empty
    log_queue.join()
    stop_worker.set()
    if worker_thread:
        worker_thread.join()


def json_sink(message):
    """
    Custom sink that puts log records into the queue.
    Loguru's `serialize=True` in the `logger.add` call will handle
    the conversion of the record to a JSON string.
    """
    log_queue.put(message)


def configure_logger(jsonrpc_url: str, project_id: str):
    """
    Configures loguru to use our custom sink.
    """

    project_id_var.set(project_id)
    logger.remove()  # Remove default handlers
    logger.add(
        json_sink,
        level="INFO",
        serialize=True  # IMPORTANT: This converts the record to JSON
    )
    start_worker_thread(jsonrpc_url)
