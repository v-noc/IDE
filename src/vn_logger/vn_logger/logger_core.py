import queue
import threading
import requests
import json
import uuid
import atexit
import time
from typing import Optional, Callable
from loguru import logger
from contextvars import ContextVar

# ContextVar to hold the project ID in the main thread/asynchronous tasks
project_id_var = ContextVar("project_id", default=None)

log_queue = queue.Queue(maxsize=10000)
stop_worker = threading.Event()
worker_thread = None
_shutdown_registered = False


def _send_batch(batch: list, post_func: Optional[Callable], jsonrpc_url: str, project_id: str):
    """Sends logs to the server using the specific JSON-RPC structure required."""
    if not batch:
        return

    # Match the FastAPI-JSONRPC expectation:
    # params contains 'params' (for the RegisterLogsBatchParams) and 'project_id'
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "method": "register_logs_batch",
        "params": {
            "params": {"logs": batch},
            "project_id": project_id
        },
        "id": str(uuid.uuid4())
    }

    try:
        sender = post_func or requests.post

        response = sender(jsonrpc_url, json=jsonrpc_request, timeout=5)

        if response.status_code != 200:
            print(f"Logger Error: Server returned {response.status_code}")
    except Exception as e:
        print(f"CRITICAL: Logger failed to send batch: {e}")


def log_worker(jsonrpc_url, default_project_id, post_func, batch_size=50, flush_interval=2.0):
    """Background thread processing the queue and batching requests."""
    batch = []
    last_flush = time.time()

    while not stop_worker.is_set() or not log_queue.empty():
        try:
            # Short timeout to keep the loop responsive
            message_str = log_queue.get(block=True, timeout=0.2)

            record = json.loads(message_str)["record"]
            extra = record.get("extra", {})

            # Map Loguru record to our database schema
            log_entry = {
                "id": extra.get("log_id") or str(uuid.uuid4()),
                "parent_log_id": extra.get("parent_log_id"),
                "function_id": extra.get("function_id"),
                "chain_id": extra.get("chain_id"),
                "parent_function_id": extra.get("parent_function_id"),
                "timestamp": record["time"]["timestamp"],
                "event_type": extra.get("event_type", "log"),
                "message": record["message"],
                "level_name": record["level"]["name"],
                "duration_ms": extra.get("duration_ms"),
                "payload": None,
                "result": extra.get("result"),
                "error": None
            }

            if log_entry["event_type"] == "enter":
                log_entry["payload"] = {"args": extra.get(
                    "args"), "kwargs": extra.get("kwargs")}

            if record.get("exception"):
                exc = record["exception"]
                log_entry["error"] = {
                    "type": exc.get("type"),
                    "message": str(exc.get("value")),
                    "stacktrace": exc.get("traceback")
                }

            batch.append(log_entry)
            log_queue.task_done()

        except queue.Empty:
            pass

        # Check if we should flush the batch
        now = time.time()
        if batch and (len(batch) >= batch_size or (now - last_flush) >= flush_interval):
            _send_batch(batch, post_func, jsonrpc_url, default_project_id)
            batch = []
            last_flush = now

    # Final sweep before the thread dies
    if batch:
        _send_batch(batch, post_func, jsonrpc_url, default_project_id)


def json_sink(message):
    """Bridge between Loguru and our internal thread-safe queue."""
    try:
        log_queue.put_nowait(message)
    except queue.Full:
        pass  # Drop logs if queue is full to prevent app lockup


def configure_logger(jsonrpc_url: str, project_id: str, post: Optional[Callable] = None):
    """Initializes logging. Must be called once at app startup."""
    project_id_var.set(project_id)
    logger.remove()
    logger.add(json_sink, level="INFO", serialize=True)

    global worker_thread
    if worker_thread is None or not worker_thread.is_alive():
        stop_worker.clear()
        worker_thread = threading.Thread(
            target=log_worker,
            args=(jsonrpc_url, project_id, post),
            daemon=True
        )
        worker_thread.start()

    global _shutdown_registered
    if not _shutdown_registered:
        atexit.register(stop_worker_thread)
        _shutdown_registered = True


def stop_worker_thread():
    """Signals the worker to finish and wait for it to join."""
    stop_worker.set()
    if worker_thread:
        worker_thread.join(timeout=5)
