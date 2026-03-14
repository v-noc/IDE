from coverage import Coverage
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Set, List


class TestData(BaseModel):
    file_name: str
    lines: Set[int]


class CoverageData(BaseModel):
    test_id: str
    tests: List[TestData]


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
        self.all_coverage_datas = []

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

        for test_id in data.measured_contexts():
            if not test_id:  # Skip empty context (collection/setup phase)
                continue
            data.set_query_context(test_id)
            coverage_data = CoverageData(test_id=test_id, tests=[])

            for filename in data.measured_files():
                lines = data.lines(filename)

                coverage_data.tests.append(
                    TestData(file_name=filename, lines=lines))
            self.all_coverage_datas.append(coverage_data)

        return self.all_coverage_datas
