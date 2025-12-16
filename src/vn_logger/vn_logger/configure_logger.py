from loguru import logger
import queue
import threading
import requests
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


def _send_batch(batch: list, post, jsonrpc_url: str, project_id: str):
    """Send multiple logs in one request."""
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "method": "register_logs_batch",
        "params": {"params": {"logs": batch}, "project_id": project_id},
        "id": str(uuid.uuid4())
    }
    try:
        sender = post or requests.post
        sender(jsonrpc_url, json=jsonrpc_request, timeout=5)
    except requests.RequestException as e:
        logger.error(f"Batch send failed: {e}")


def log_worker(
    jsonrpc_url: str,
    initial_project_id: Optional[str] = None,
    post: Optional[Callable[..., object]] = None,
    batch_size: int = 10,
    flush_interval: float = 2.0,
):
    if initial_project_id is not None:
        project_id_var.set(initial_project_id)

    batch = []
    last_flush = time.time()

    def flush_batch():
        nonlocal batch, last_flush
        if not batch:
            return
        # Use current context project_id
        pid = project_id_var.get()
        _send_batch(batch, post, jsonrpc_url, pid)
        # Important: Mark tasks done after sending
        for _ in batch:
            log_queue.task_done()
        batch = []
        last_flush = time.time()

    while not stop_worker.is_set():
        try:
            timeout = max(0.1, flush_interval - (time.time() - last_flush))
            log_message_str = log_queue.get(block=True, timeout=timeout)

            project_id = project_id_var.get()
            record = json.loads(log_message_str)['record']
            extra = record['extra']

            log_id = extra.get('extra', {}).get('log_id') or str(uuid.uuid4())
            active_parent_log_id = extra.get('active_parent_log_id') or None
            event_type = extra.get("event_type", "log")

            params = {
                "function_id": extra.get('function_id'),
                "chain_id": extra.get('chain_id'),
                "timestamp": record['time']["timestamp"],
                "duration_ms": extra.get('duration_ms'),
                "id": log_id,
                "parent_log_id": active_parent_log_id,
                "event_type": event_type,
                "message": record['message'],
                "level_name": (record.get('level', {}) or {}).get('name'),
                "payload": None,
                "result": None,
                "error": None
            }

            if extra.get('parent_function_id') is not None:
                params["parent_function_id"] = extra.get('parent_function_id')

            if event_type == "enter":
                params["payload"] = {
                    "args": extra.get("args"),
                    "kwargs": extra.get("kwargs"),
                }
            elif event_type == "exit":
                params["result"] = extra.get("result")
            elif event_type == "error":
                if record.get('exception'):
                    exc = record['exception']
                    params["error"] = {
                        "type": exc.get('type'),
                        "message": str(exc.get('value')),
                        "stacktrace": exc.get('traceback', False),
                    }

            batch.append(params)

            if len(batch) >= batch_size:
                flush_batch()

        except queue.Empty:
            if (time.time() - last_flush) >= flush_interval:
                flush_batch()
            continue
        except Exception as e:
            logger.error(f"Worker error: {e}")
            # Ensure we don't block join() if a specific message fails processing
            log_queue.task_done()
            continue

    # Final cleanup when loop exits
    flush_batch()


def start_worker_thread(jsonrpc_url: str, post: Optional[Callable[..., object]] = None):
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
    # 1. Signal the event first so the loop knows to stop
    #    (Optional: depends if you want to process EVERYTHING in queue or just stop now.
    #     Usually, for logs, you want to drain the queue, so keep logic below).

    # Wait for queue to drain
    log_queue.join()

    # Signal thread to exit
    stop_worker.set()

    if worker_thread:
        worker_thread.join(timeout=5)


def json_sink(message):
    try:
        log_queue.put_nowait(message)
    except queue.Full:
        try:
            log_queue.get_nowait()
            log_queue.task_done()  # <--- FIXED: Must mark dropped item as done
            log_queue.put_nowait(message)
        except queue.Empty:
            pass


def _register_shutdown_hook() -> None:
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
    project_id_var.set(project_id)
    logger.remove()
    logger.add(json_sink, level="INFO", serialize=True)
    start_worker_thread(jsonrpc_url, post)
    _register_shutdown_hook()
