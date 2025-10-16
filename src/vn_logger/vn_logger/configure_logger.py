from loguru import logger
import queue
import threading
import requests  # or any other HTTP client
import json
import uuid
import atexit
from typing import Optional, Callable
from .logger import project_id_var

log_queue = queue.Queue()
worker_thread = None
stop_worker = threading.Event()
_shutdown_registered = False
_shutdown_lock = threading.Lock()


def log_worker(
    jsonrpc_url: str,
    initial_project_id: Optional[str] = None,
    post: Optional[Callable[..., object]] = None,
):
    """
    The worker function that runs in a background thread.
    """

    # Ensure the worker thread has the same project_id in its own context
    if initial_project_id is not None:
        project_id_var.set(initial_project_id)

    while not stop_worker.is_set():
        try:

            log_message_str = log_queue.get(block=True, timeout=1)
            project_id = project_id_var.get()

            record = json.loads(log_message_str)['record']
            extra = record['extra']

            # Get event_type directly from extra data. Default to "log".
            event_type = extra.get("event_type", "log")

            # Construct the base params object
            params = {
                "function_id": extra.get('function_id'),
                "project_id": project_id,

                "params": {
                    "chain_id": extra.get('chain_id'),
                    "timestamp": record['time']["timestamp"],
                    "duration_ms": extra.get('duration_ms'),
                    "event_type": event_type,
                    "message": record['message'],
                    "payload": None,
                    "result": None,
                    "error": None
                }
            }

            if extra.get('parent_function_id') is not None:
                params["parent_function_id"] = extra.get('parent_function_id')
            # Add event-specific fields based on the robust event_type
            inner = params["params"]
            if event_type == "enter":
                inner["payload"] = {
                    "args": extra.get("args"),
                    "kwargs": extra.get("kwargs"),
                }

            elif event_type == "exit":
                inner["result"] = extra.get("result")
            elif event_type == "error":
                if record.get('exception'):
                    exc = record['exception']
                    inner["error"] = {
                        "type": exc.get('type'),
                        "message": str(exc.get('value')),
                        "stacktrace": exc.get('traceback', False),
                    }

            jsonrpc_request = {
                "jsonrpc": "2.0",
                "method": "register_logs",
                "params": params,
                "id": str(uuid.uuid4())
            }

            try:
                sender = post or requests.post
                sender(jsonrpc_url, json=jsonrpc_request, timeout=5)

            except requests.RequestException as e:
                print(f"WORKER: Failed to send log - {e}")

            log_queue.task_done()
        except queue.Empty:
            # This is expected when the queue is empty.
            continue


def start_worker_thread(
    jsonrpc_url: str,
    post: Optional[Callable[..., object]] = None,
):
    """
    Starts the background worker thread.
    """
    global worker_thread

    if worker_thread is None or not worker_thread.is_alive():
        stop_worker.clear()
        worker_thread = threading.Thread(
            target=log_worker,
            args=(jsonrpc_url, project_id_var.get(), post),
            daemon=True,
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


def _register_shutdown_hook() -> None:
    """
    Register a process-exit hook to gracefully stop the background worker.
    Idempotent: safe to call multiple times.
    """
    global _shutdown_registered
    with _shutdown_lock:
        if _shutdown_registered:
            return
        atexit.register(stop_worker_thread)
        _shutdown_registered = True


def configure_logger(
    jsonrpc_url: str,
    project_id: str,
    post: Optional[Callable[..., object]] = None,
):
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
    start_worker_thread(jsonrpc_url, post)
    _register_shutdown_hook()
