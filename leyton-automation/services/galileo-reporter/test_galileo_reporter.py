import os
import sys

_SVC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SVC_DIR)
for _k in list(sys.modules.keys()):
    if _k in ("mock_data", "generate_fixture", "main"):
        del sys.modules[_k]

from unittest.mock import patch
import openpyxl
import main
from mock_data import MOCK_GALILEO_MISSIONS, SEVERITY


def test_run_produces_rows_for_all_missions():
    with patch.object(main, "log_run"), \
            patch.object(main, "get_last_run", return_value=None), \
            patch.object(main, "was_run_this_month", return_value=False):
        rows = main.run()

    assert len(rows) == len(MOCK_GALILEO_MISSIONS)


def test_output_excel_created():
    with patch.object(main, "log_run"), \
            patch.object(main, "get_last_run", return_value=None), \
            patch.object(main, "was_run_this_month", return_value=False):
        main.run()

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    files = [f for f in os.listdir(output_dir) if f.startswith("Galileo_Report")]
    assert len(files) > 0

    wb = openpyxl.load_workbook(os.path.join(output_dir, files[-1]))
    assert "Alert Matrix" in wb.sheetnames


def test_critical_alert_for_missing_folder():
    with patch.object(main, "log_run"), \
            patch.object(main, "get_last_run", return_value=None), \
            patch.object(main, "was_run_this_month", return_value=False):
        rows = main.run()

    critical_rows = [r for r in rows if r["overall"][0] == SEVERITY["CRITICAL"]]
    assert len(critical_rows) > 0, "Expected at least one CRITICAL alert from mock data"


def test_registry_data_overrides_mock_when_present():
    fake_run = {"ran_at": "2026-05-01T10:00:00", "status": "success"}
    with patch.object(main, "log_run"), \
            patch.object(main, "get_last_run", return_value=fake_run), \
            patch.object(main, "was_run_this_month", return_value=True):
        rows = main.run()

    for r in rows:
        assert r["folder"][0] == "OK"
