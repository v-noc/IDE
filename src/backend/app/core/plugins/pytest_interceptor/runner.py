from .coverage_plugin import CoveragePlugin, CoverageData
import pytest


def run_tests(test_path: str, root_path: str) -> tuple[int, list[CoverageData]]:
    coverage_plugin = CoveragePlugin(root_path)

    # Run pytest programmatically with your plugin
    exit_code = pytest.main(
        [test_path, "-s"],  # pytest arguments
        plugins=[coverage_plugin]     # Inject your coverage plugin
    )

    return exit_code, coverage_plugin.all_coverage_datas
