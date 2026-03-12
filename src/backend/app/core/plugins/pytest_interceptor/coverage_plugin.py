from pathlib import Path
from coverage import Coverage
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Set


class TestData(BaseModel):
    target_qname: str
    lines: Set[int]


class CoverageData(BaseModel):
    test_id: str
    tests: Set[TestData]


class CoveragePlugin:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.cov = Coverage(
            data_file=".coverage.ide",
            omit=[""],
            branch=False,
        )
        self.tests = {}
        self.started_at = None
        self.finished_at = None

    def pytest_sessionstart(self, session):
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.cov.start()

    def pytest_runtest_setup(self, item):
        test_id = item.nodeid
        self.tests.setdefault(test_id, {
            "status": "unknown",
            "duration": 0.0,
            "files": {}
        })
        self.cov.switch_context(test_id)

    def pytest_sessionfinish(self, session, exitstatus):
        self.cov.stop()
        self.cov.save()
        self.finished_at = datetime.now(timezone.utc).isoformat()

        data = self.cov.get_data()

        coverage_datas = []

        for test_id in data.measured_contexts():
            if not test_id:  # Skip empty context (collection/setup phase)
                continue
            data.set_query_context(test_id)
            coverage_data = CoverageData(test_id=test_id, tests=set())

            for filename in data.measured_files():
                lines = data.lines(filename)
                qname = Path(filename).relative_to(
                    self.project_root).as_posix().replace("/", ".")
                coverage_data.tests.add(
                    TestData(target_qname=qname, lines=lines))
            coverage_datas.append(coverage_data)

        return coverage_datas
