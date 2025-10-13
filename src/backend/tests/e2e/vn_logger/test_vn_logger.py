from vn_logger.configure_logger import configure_logger
from vn_logger.logger import context_logger


def test_vn_logger():
    configure_logger("http://localhost:8000/jsonrpc",
                     "c0f57cde-3283-47e2-b1c1-d23a40289615")

    @context_logger(function_id="973e9793-0b1d-4030-9a5a-7a689970c62f")
    def logger_function():
        return "test"

    logger_function()
