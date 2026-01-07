import functools
import uuid
import time
import asyncio
from contextvars import ContextVar
from loguru import logger
from .logger_core import project_id_var

# Context Variables for tracking hierarchy
chain_id_var = ContextVar("chain_id", default=None)
parent_function_id_var = ContextVar("parent_function_id", default=None)
active_parent_log_id_var = ContextVar("active_parent_log_id", default=None)


class LogScope:
    def __init__(self, function_id, function_name, args, kwargs, serializers):
        self.function_id = function_id
        self.function_name = function_name
        self.args = args
        self.kwargs = kwargs
        self.input_serializer = serializers[0]
        self.output_serializer = serializers[1]
        self.start_time = time.perf_counter()
        self.tokens = {}
        self.context_manager = None

    def __enter__(self):
        if not project_id_var.get():
            return self

        # 1. Chain/Trace ID logic
        chain_id = chain_id_var.get()
        if chain_id is None:
            chain_id = str(uuid.uuid4())
            self.tokens["chain_id"] = chain_id_var.set(chain_id)

        # 2. Capture parent IDs
        parent_func_id = parent_function_id_var.get()
        parent_log_id = active_parent_log_id_var.get()

        # 3. Create ID for this execution
        current_span_id = str(uuid.uuid4())

        # 4. Update context for children
        self.tokens["parent_function_id"] = parent_function_id_var.set(
            self.function_id)
        self.tokens["active_parent_log_id"] = active_parent_log_id_var.set(
            current_span_id)

        # 5. Contextualize all logs inside this scope
        self.context_manager = logger.contextualize(
            function_id=self.function_id,
            chain_id=chain_id,
            parent_function_id=parent_func_id,
            parent_log_id=current_span_id,  # links internal logs to this Enter
        )
        self.context_manager.__enter__()

        # 6. Log Enter
        logger.bind(
            log_id=current_span_id,
            parent_log_id=parent_log_id,
            event_type="enter",
            args=self._serialize(self.args, self.input_serializer),
            kwargs=self._serialize(self.kwargs, self.input_serializer),
        ).info(f"Enter {self.function_name}")

        return self

    def log_success(self, result):
        if not project_id_var.get():
            return
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        current_span_id = active_parent_log_id_var.get()

        logger.bind(
            log_id=str(uuid.uuid4()),
            parent_log_id=current_span_id,
            event_type="exit",
            result=self._serialize(result, self.output_serializer),
            duration_ms=duration_ms,
        ).info(f"Exit {self.function_name}")

    def log_error(self):
        if not project_id_var.get():
            return
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        current_span_id = active_parent_log_id_var.get()

        logger.bind(
            log_id=str(uuid.uuid4()),
            parent_log_id=current_span_id,
            event_type="error",
            duration_ms=duration_ms,
        ).exception(f"Error in {self.function_name}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not project_id_var.get():
            return

        if exc_type:
            self.log_error()

        if self.context_manager:
            self.context_manager.__exit__(exc_type, exc_val, exc_tb)

        # Reset only what we set
        for var_name, token in self.tokens.items():
            if var_name == "chain_id":
                chain_id_var.reset(token)
            elif var_name == "parent_function_id":
                parent_function_id_var.reset(token)
            elif var_name == "active_parent_log_id":
                active_parent_log_id_var.reset(token)

    def _serialize(self, obj, serializer):
        try:
            if serializer:
                return serializer(obj)
            if isinstance(obj, (list, tuple)):
                return [repr(x) for x in obj]
            if isinstance(obj, dict):
                return {k: repr(v) for k, v in obj.items()}
            return repr(obj)
        except Exception:
            return "[Serialization Error]"


def context_logger(function_id: str, input_serializer=None, output_serializer=None):
    serializers = (input_serializer, output_serializer)

    def decorator(func):
        function_name = func.__qualname__

        # Heuristic: if first parameter is named 'self' or 'cls' → bound method/classmethod
        is_bound = (
            func.__code__.co_argcount >= 1
            and func.__code__.co_varnames[0] in ("self", "cls")
        )

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                log_args = args[1:] if is_bound else args
                with LogScope(function_id, function_name, log_args, kwargs, serializers) as scope:
                    result = await func(*args, **kwargs)
                    scope.log_success(result)
                    return result

            return wrapper
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                log_args = args[1:] if is_bound else args
                with LogScope(function_id, function_name, log_args, kwargs, serializers) as scope:
                    result = func(*args, **kwargs)
                    scope.log_success(result)
                    return result

            return wrapper

    return decorator
