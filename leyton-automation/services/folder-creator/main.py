import os
import sys
import json
import time

_SERVICES_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SERVICES_ROOT not in sys.path:
    sys.path.insert(0, _SERVICES_ROOT)

from datetime import datetime
from mock_data import MOCK_CONTRACTS
from shared.registry import log_run
from shared.logger import ServiceLogger

BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "clients")

SUBFOLDERS = [
    "01_Kickoff/Personnel_List",
    "01_Kickoff/Organigramme",
    "01_Kickoff/RD_Projects",
    "02_Audit/Project_List",
    "02_Audit/Timesheets",
    "02_Audit/Job_Descriptions",
    "02_Audit/Technical_Info",
    "03_Preparation/Diplomas",
    "03_Preparation/Comptes_Individuels",
    "04_Deliverables/Chiffrage",
    "04_Deliverables/Rapport_Technique_DT",
    "04_Deliverables/Liste_Structuree_Projets",
    "04_Deliverables/Belspo_Notifications",
    "05_Internal/Correspondence",
    "05_Internal/Invoices",
]


def create_client_folder(contract: dict) -> dict:
    client = contract["client"]
    mission = contract["mission"]
    contract_id = contract["contract_id"]

    client_folder = os.path.join(
        BASE_PATH,
        client["name"].replace(" ", "_"),
        f"{mission['type']}_{mission['year']}",
    )

    created_paths = []

    try:
        for subfolder in SUBFOLDERS:
            full_path = os.path.join(client_folder, subfolder)
            os.makedirs(full_path, exist_ok=True)
            created_paths.append(full_path)

        metadata = {
            "contract_id": contract_id,
            "client": client,
            "mission": mission,
            "created_at": datetime.now().isoformat(),
            "created_by": "leyton-automation",
        }

        with open(os.path.join(client_folder, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        return {
            "status": "success",
            "contract_id": contract_id,
            "client_name": client["name"],
            "folders_created": len(created_paths),
            "base_path": client_folder,
        }

    except Exception as exc:
        return {
            "status": "error",
            "contract_id": contract_id,
            "client_name": client["name"],
            "error": str(exc),
        }


def run():
    log = ServiceLogger("folder-creator")
    start = time.time()
    log.info("Service started")

    results = []
    try:
        for contract in MOCK_CONTRACTS:
            result = create_client_folder(contract)
            results.append(result)
            if result["status"] == "success":
                log.info("Folder created", client=result["client_name"],
                         folders=result["folders_created"], path=result["base_path"])
            else:
                log.warning("Folder creation failed", client=result["client_name"],
                            error=result.get("error"))

        ok = len([r for r in results if r["status"] == "success"])
        duration_ms = int((time.time() - start) * 1000)
        log_run("folder-creator", status="success", duration_ms=duration_ms)
        log.info("Service completed", processed=len(results), ok=ok, duration_ms=duration_ms)

    except Exception as exc:
        duration_ms = int((time.time() - start) * 1000)
        log.error("Service failed", error=str(exc))
        log_run("folder-creator", status="failed", error_message=str(exc), duration_ms=duration_ms)
        raise

    return results


if __name__ == "__main__":
    run()
