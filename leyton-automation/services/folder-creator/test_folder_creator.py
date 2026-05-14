import os
import sys

_SVC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SVC_DIR)
for _k in list(sys.modules.keys()):
    if _k in ("mock_data", "generate_fixture", "main"):
        del sys.modules[_k]

from unittest.mock import patch
import main
from mock_data import MOCK_CONTRACTS


def test_run_succeeds_and_logs_registry():
    with patch.object(main, "log_run") as mock_log:
        results = main.run()

    assert results is not None
    assert len(results) > 0
    mock_log.assert_called()
    statuses = [c.kwargs.get("status") for c in mock_log.call_args_list]
    assert "success" in statuses


def test_all_contracts_processed():
    with patch.object(main, "log_run"):
        results = main.run()
    assert len(results) == len(MOCK_CONTRACTS)


def test_success_results_have_base_path():
    with patch.object(main, "log_run"):
        results = main.run()
    for r in results:
        if r["status"] == "success":
            assert "base_path" in r
            assert os.path.isdir(r["base_path"])
