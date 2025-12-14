from contextvars import ContextVar
import functools
from loguru import logger
import time
import uuid
import asyncio

chain_id_var = ContextVar("chain_id", default=None)
parent_function_id_var = ContextVar("parent_function_id", default=None)

project_id_var = ContextVar("project_id", default=None)
active_parent_log_id_var = ContextVar("active_parent_log_id", default=None)


def context_logger(
        function_id: str,
        input_serializer=None,
        output_serializer=None):
    def decorator(func):
        # Check if function is async
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                chain_id_token = None
                parent_id_token = None
                project_id = project_id_var.get()

                if project_id is None:
                    return None

                try:
                    chain_id = chain_id_var.get()
                    if chain_id is None:
                        chain_id = str(uuid.uuid4())
                        chain_id_token = chain_id_var.set(chain_id)

                    parent_function_id = parent_function_id_var.get()
                    parent_id_token = parent_function_id_var.set(function_id)

                    parent_log_id = active_parent_log_id_var.get()

                    current_entry_log_id = str(uuid.uuid4())

                    token = active_parent_log_id_var.set(current_entry_log_id)

                    start_time = time.perf_counter()

                    with logger.contextualize(
                        function_id=function_id,
                        chain_id=chain_id,
                        parent_function_id=parent_function_id,
                    ):
                        try:
                            serialized_args = (
                                [input_serializer(arg) for arg in args]
                                if input_serializer
                                else [repr(arg) for arg in args]
                            )
                            serialized_kwargs = (
                                {k: input_serializer(v)
                                 for k, v in kwargs.items()}
                                if input_serializer
                                else {k: repr(v) for k, v in kwargs.items()}
                            )
                            logger.info(
                                f"Enter {func.__qualname__}",
                                event_type="enter",
                                extra={
                                    "log_id": current_entry_log_id,
                                    "parent_log_id": parent_log_id
                                },
                                args=serialized_args,
                                kwargs=serialized_kwargs,
                            )

                            result = await func(*args, **kwargs)

                            duration_ms = (
                                time.perf_counter() - start_time) * 1000
                            logger.info(
                                "Exit",
                                event_type="exit",
                                extra={
                                    # Exit gets its own ID
                                    "log_id": str(uuid.uuid4()),
                                    "parent_log_id": current_entry_log_id
                                },
                                result=(
                                    output_serializer(result)
                                    if output_serializer
                                    else repr(result)
                                ),
                                duration_ms=duration_ms,
                            )

                            return result

                        except Exception:
                            duration_ms = (
                                time.perf_counter() - start_time
                            ) * 1000
                            logger.exception(
                                "Error",
                                event_type="error",
                                extra={
                                    "log_id": str(uuid.uuid4()),
                                    "parent_log_id": current_entry_log_id
                                },
                                duration_ms=duration_ms,
                            )
                            raise

                finally:
                    if parent_id_token is not None:
                        parent_function_id_var.reset(parent_id_token)
                    if chain_id_token is not None:
                        chain_id_var.reset(chain_id_token)
                    if token is not None:
                        active_parent_log_id_var.reset(token)
            return async_wrapper

        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                chain_id_token = None
                parent_id_token = None
                project_id = project_id_var.get()

                if project_id is None:
                    return None

                try:
                    chain_id = chain_id_var.get()
                    if chain_id is None:
                        chain_id = str(uuid.uuid4())
                        chain_id_token = chain_id_var.set(chain_id)

                    # Get the parent's static ID from the context
                    parent_function_id = parent_function_id_var.get()

                    active_parent_log_id = active_parent_log_id_var.get()

                    current_entry_log_id = str(uuid.uuid4())

                    token = active_parent_log_id_var.set(current_entry_log_id)

                    # Set this function's ID as the parent context
                    parent_id_token = parent_function_id_var.set(
                        function_id
                    )

                    start_time = time.perf_counter()

                    with logger.contextualize(
                        function_id=function_id,
                        chain_id=chain_id,
                        parent_function_id=parent_function_id,
                        active_parent_log_id=active_parent_log_id,
                        function_name=func.__name__,
                    ):

                        try:
                            # Log entry event with a dedicated event_type
                            serialized_args = (
                                [input_serializer(arg) for arg in args]
                                if input_serializer
                                else [repr(arg) for arg in args]
                            )
                            serialized_kwargs = (
                                {k: input_serializer(v)
                                 for k, v in kwargs.items()}
                                if input_serializer
                                else {k: repr(v) for k, v in kwargs.items()}
                            )
                            logger.info(
                                f"Enter {func.__qualname__}",
                                event_type="enter",
                                extra={
                                    "log_id": current_entry_log_id,
                                    "parent_log_id": active_parent_log_id
                                },
                                args=serialized_args,
                                kwargs=serialized_kwargs,
                            )

                            result = func(*args, **kwargs)

                            duration_ms = (
                                time.perf_counter() - start_time) * 1000
                            serialized_result = (
                                output_serializer(result)
                                if output_serializer
                                else repr(result)
                            )

                            # Log exit event with a dedicated event_type
                            logger.info(
                                "Exit",
                                event_type="exit",
                                result=serialized_result,
                                extra={
                                    "log_id": str(uuid.uuid4()),
                                    "parent_log_id": current_entry_log_id
                                },
                                duration_ms=duration_ms,
                            )

                            return result

                        except Exception:
                            duration_ms = (
                                time.perf_counter() - start_time) * 1000
                            # Log error event with a dedicated event_type
                            logger.exception(
                                "Error",
                                event_type="error",
                                extra={
                                    "log_id": str(uuid.uuid4()),
                                    "parent_log_id": current_entry_log_id
                                },
                                duration_ms=duration_ms,
                            )
                            raise

                finally:
                    # Restore the context ONLY if the tokens were successfully set
                    if parent_id_token is not None:
                        parent_function_id_var.reset(parent_id_token)
                    if chain_id_token is not None:
                        chain_id_var.reset(chain_id_token)
                    if token is not None:
                        active_parent_log_id_var.reset(token)

            return wrapper

    return decorator
