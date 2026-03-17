import json
import os
import shlex
import subprocess
import textwrap
import uuid
from dataclasses import dataclass


@dataclass
class TestData:
    file_name: str
    lines: list[int]


@dataclass
class CoverageData:
    test_id: str
    tests: list[TestData]


def _build_omit_patterns(test_root: str | None) -> list[str]:
    """Build coverage omit patterns: temp runner file and files under test_root."""
    omit = ["*__ide_coverage_runner_*.py"]
    if test_root and test_root.strip():
        root = test_root.strip().replace("\\", "/").rstrip("/")
        if root:
            omit.append(f"*{root}/*")
    return omit


def _build_runner_script(
    test_path: str, result_path: str, test_root: str | None = None
) -> str:
    omit_patterns = _build_omit_patterns(test_root)
    omit_repr = repr(omit_patterns)
    return textwrap.dedent(
        f"""
        import json
        import os
        import sys
        from dataclasses import dataclass

        from coverage import Coverage
        import pytest

        @dataclass
        class TestData:
            file_name: str
            lines: list[int]

        @dataclass
        class CoverageData:
            test_id: str
            tests: list[TestData]

        class CoveragePlugin:
            def __init__(self, result_path: str):
                self.result_path = result_path
                self.cov = Coverage(
                    data_file=".coverage.ide",
                    omit={omit_repr},
                    branch=False,
                )
                self.all_coverage_datas: list[CoverageData] = []

            def pytest_sessionstart(self, session):
                self.cov.start()

            def pytest_runtest_setup(self, item):
                self.cov.switch_context(item.nodeid)

            def pytest_sessionfinish(self, session, exitstatus):
                self.cov.stop()
                self.cov.save()

                data = self.cov.get_data()
                for test_id in data.measured_contexts():
                    if not test_id:
                        continue

                    data.set_query_context(test_id)
                    tests: list[TestData] = []
                    for filename in data.measured_files():
                        lines = data.lines(filename)
                        if lines:
                            tests.append(
                                TestData(
                                    file_name=filename,
                                    lines=sorted(lines),
                                )
                            )

                    self.all_coverage_datas.append(
                        CoverageData(test_id=test_id, tests=tests)
                    )

                payload = {{
                    "exit_code": int(exitstatus),
                    "coverage": [
                        {{
                            "test_id": cov.test_id,
                            "tests": [
                                {{
                                    "file_name": test.file_name,
                                    "lines": test.lines
                                }}
                                for test in cov.tests
                            ],
                        }}
                        for cov in self.all_coverage_datas
                    ],
                }}
                temp_path = self.result_path + ".tmp"
                with open(temp_path, "w", encoding="utf-8") as fp:
                    json.dump(payload, fp)
                os.rename(temp_path, self.result_path)

        result_path = {result_path!r}
        test_path = {test_path!r}
        plugin = CoveragePlugin(result_path)
        exit_code = pytest.main([test_path, "-s"], plugins=[plugin])
        sys.exit(exit_code)
        """
    )


def _decode_coverage_payload(payload: dict) -> list[CoverageData]:
    result: list[CoverageData] = []
    for coverage_item in payload.get("coverage", []):
        tests = [
            TestData(
                file_name=test_item.get("file_name", ""),
                lines=list(test_item.get("lines", [])),
            )
            for test_item in coverage_item.get("tests", [])
        ]
        result.append(
            CoverageData(
                test_id=coverage_item.get("test_id", ""),
                tests=tests,
            )
        )
    return result


def _trim_output(output: str, max_chars: int = 800) -> str:
    text = (output or "").strip()
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars].rstrip()}..."


def _pick_best_output(stdout: str, stderr: str) -> str:
    stderr_text = _trim_output(stderr)
    if stderr_text:
        return stderr_text
    return _trim_output(stdout)


def _merge_raw_output(stdout: str, stderr: str) -> str | None:
    parts: list[str] = []
    if stdout:
        parts.append(stdout)
    if stderr:
        parts.append(stderr)
    if not parts:
        return None
    return "\n".join(parts)


def run_tests(
    test_path: str,
    project_root: str,
    python_executable: str | None = None,
    command_prefix: str | None = None,
    test_root: str | None = None,
) -> tuple[int, list[CoverageData], str | None, str | None]:
    python_cmd = python_executable or "python"
    probe_cmd = (
        shlex.split(command_prefix) + ["-c", "import coverage"]
        if command_prefix
        else [python_cmd, "-c", "import coverage"]
    )
    probe = subprocess.run(
        probe_cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if probe.returncode != 0:
        details = _pick_best_output(probe.stdout, probe.stderr)
        raw_output = _merge_raw_output(probe.stdout, probe.stderr)
        message = "Coverage pre-check failed: unable to import 'coverage'."
        if details:
            message = f"{message} {details}"
        return -1, [], message, raw_output

    run_id = str(uuid.uuid4())
    runner_path = os.path.join(
        project_root, f"__ide_coverage_runner_{run_id}.py"
    )
    result_path = os.path.join(
        project_root, f"__ide_coverage_result_{run_id}.json"
    )
    result_tmp_path = f"{result_path}.tmp"

    try:
        runner_script = _build_runner_script(
            test_path=test_path,
            result_path=result_path,
            test_root=test_root,
        )
        with open(runner_path, "w", encoding="utf-8") as fp:
            fp.write(runner_script)

        run_cmd = (
            shlex.split(command_prefix) + [runner_path]
            if command_prefix
            else [python_cmd, runner_path]
        )
        proc = subprocess.run(
            run_cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if not os.path.exists(result_path):
            if proc.returncode != 0:
                details = _pick_best_output(proc.stdout, proc.stderr)
                raw_output = _merge_raw_output(proc.stdout, proc.stderr)
                message = (
                    "Test subprocess failed before writing coverage "
                    "results."
                )
                if details:
                    message = f"{message} {details}"
                return proc.returncode, [], message, raw_output
            return proc.returncode, [], None, _merge_raw_output(
                proc.stdout, proc.stderr
            )

        with open(result_path, encoding="utf-8") as fp:
            payload = json.load(fp)

        exit_code = int(payload.get("exit_code", proc.returncode))
        coverage_datas = _decode_coverage_payload(payload)
        return exit_code, coverage_datas, None, _merge_raw_output(
            proc.stdout,
            proc.stderr,
        )
    except subprocess.TimeoutExpired:
        return -1, [], "Test subprocess timed out after 300 seconds.", None
    except Exception as exc:
        return -1, [], f"Test subprocess failed: {exc}", None
    finally:
        for path in (runner_path, result_path, result_tmp_path):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
