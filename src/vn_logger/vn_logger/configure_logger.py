from loguru import logger
import queue
import threading
import requests  # or any other HTTP client
import json
import uuid
import atexit
from typing import Optional, Callable
from .logger import project_id_var
import time

log_queue = queue.Queue(maxsize=10000)
worker_thread = None
stop_worker = threading.Event()
_shutdown_registered = False
_shutdown_lock = threading.Lock()


def log_worker(
    jsonrpc_url: str,
    initial_project_id: Optional[str] = None,
    post: Optional[Callable[..., object]] = None,
    batch_size: int = 10,  # New parameter
    flush_interval: float = 2.0,  # seconds
):
    """
    The worker function that runs in a background thread.
    """

    # Ensure the worker thread has the same project_id in its own context
    if initial_project_id is not None:
        project_id_var.set(initial_project_id)

    batch = []
    last_flush = time.time()

    while not stop_worker.is_set():
        try:
            timeout = max(0.1, flush_interval - (time.time() - last_flush))
            log_message_str = log_queue.get(block=True, timeout=timeout)
            project_id = project_id_var.get()

            record = json.loads(log_message_str)['record']
            extra = record['extra']

            log_id = extra.get('log_id') or str(
                uuid.uuid4())  # Fallback if missing
            parent_log_id = extra.get(
                'parent_log_id') or None   # Can be None for root

            # Get event_type directly from extra data. Default to "log".
            event_type = extra.get("event_type", "log")

            # Construct the base params object
            params = {
                "project_id": project_id,
                "params": {
                    "function_id": extra.get('function_id'),
                    "chain_id": extra.get('chain_id'),
                    "timestamp": record['time']["timestamp"],
                    "duration_ms": extra.get('duration_ms'),
                    "id": log_id,
                    "parent_log_id": parent_log_id,
                    "event_type": event_type,
                    "message": record['message'],
                    "level_name": (record.get('level', {}) or {}).get('name'),
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
            batch.append(params)

            if len(batch) >= batch_size:
                _send_batch(batch, post, jsonrpc_url)
                for _ in batch:
                    log_queue.task_done()
                batch = []
                last_flush = time.time()
        except queue.Empty:
            # Flush on timeout even if batch isn't full
            if batch and (time.time() - last_flush) >= flush_interval:
                _send_batch(batch, post, jsonrpc_url)
                for _ in batch:
                    log_queue.task_done()
                batch = []
                last_flush = time.time()
            continue
        except Exception as e:
            logger.error(f"Worker error: {e}")

            log_queue.task_done()  # Still mark as done even on error
            continue


def _send_batch(batch: list, post, jsonrpc_url: str):
    """Send multiple logs in one request."""
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "method": "register_logs_batch",
        "params": {"logs": batch},
        "id": str(uuid.uuid4())
    }
    try:
        sender = post or requests.post
        sender(jsonrpc_url, json=jsonrpc_request, timeout=5)
    except requests.RequestException as e:
        logger.error(f"Batch send failed: {e}")


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
        worker_thread.join(timeout=5)


def json_sink(message):
    """
    Custom sink that puts log records into the queue.
    Loguru's `serialize=True` in the `logger.add` call will handle
    the conversion of the record to a JSON string.
    """
    try:
        log_queue.put_nowait(message)
    except queue.Full:
        # Drop the oldest log to make room
        try:
            log_queue.get_nowait()
            log_queue.put_nowait(message)
        except queue.Empty:
            pass


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
