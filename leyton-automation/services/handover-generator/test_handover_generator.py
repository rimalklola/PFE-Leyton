import os
import sys

_SVC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SVC_DIR)
for _k in list(sys.modules.keys()):
    if _k in ("mock_data", "generate_fixture", "main"):
        del sys.modules[_k]

from unittest.mock import patch
import main
from mock_data import MOCK_HANDOVER_DATA


def test_run_succeeds_and_logs_registry():
    with patch.object(main, "log_run") as mock_log:
        filepaths = main.run()

    assert filepaths is not None
    assert len(filepaths) > 0
    mock_log.assert_called()
    statuses = [c.kwargs.get("status") for c in mock_log.call_args_list]
    assert "success" in statuses


def test_output_files_exist():
    with patch.object(main, "log_run"):
        filepaths = main.run()

    for path in filepaths:
        assert os.path.isfile(path), f"Expected output file: {path}"


def test_one_file_per_contract():
    with patch.object(main, "log_run"):
        filepaths = main.run()
    assert len(filepaths) == len(MOCK_HANDOVER_DATA)
