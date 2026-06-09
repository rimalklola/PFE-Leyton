import os
import sys
import json
import time
import shutil

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
    "_Inbox",  # unclassified files land here — nothing is ever lost
]

# ---------------------------------------------------------------------------
# File classification rules
# Each rule is (keywords, target_subfolder).
# The filename (lowercased, no extension) is checked against every keyword.
# First match wins. Files that match nothing go to _Inbox.
# ---------------------------------------------------------------------------
CLASSIFICATION_RULES = [
    # Timesheets
    (["timesheet", "feuille_de_temps", "feuille de temps", "pointage",
      "heures", "hours", "uren", "timetable"],
     "02_Audit/Timesheets"),

    # Diplomas / certificates
    (["diploma", "diplome", "diplôme", "certificat", "certificate",
      "degree", "master", "bachelor", "licence", "brevet"],
     "03_Preparation/Diplomas"),

    # Organigramme
    (["organi", "organigram", "organization", "organisation", "structure",
      "hierarchy", "hierarch"],
     "01_Kickoff/Organigramme"),

    # Personnel list
    (["personnel", "staff", "employees", "employes", "collaborat",
      "liste_employes", "liste employes", "team", "equipe"],
     "01_Kickoff/Personnel_List"),

    # Job descriptions
    (["job_description", "job description", "fiche_de_poste", "fiche de poste",
      "fonction", "jd_", "_jd", "poste", "role_description"],
     "02_Audit/Job_Descriptions"),

    # R&D / technical project info
    (["technique", "technical", "projet_rd", "project_rd", "r&d",
      "rd_project", "recherche", "research", "innovation"],
     "02_Audit/Technical_Info"),

    # Project list
    (["project_list", "liste_projets", "liste projets", "projects_overview",
      "liste_de_projets"],
     "02_Audit/Project_List"),

    # Individual accounts / comptes individuels
    (["compte_individuel", "compte individuel", "ci_", "_ci.", "fiche_paie",
      "fiche paie", "payslip", "pay_slip", "individual_account"],
     "03_Preparation/Comptes_Individuels"),

    # Invoices
    (["invoice", "facture", "billing", "payment", "paiement", "factuur"],
     "05_Internal/Invoices"),

    # Contracts / correspondence
    (["contract", "contrat", "accord", "agreement", "convention",
      "correspondence", "courrier", "letter", "lettre"],
     "05_Internal/Correspondence"),

    # Chiffrage / calculation sheets
    (["chiffrage", "budget", "calcul", "calculation", "cost", "cout",
      "estimation"],
     "04_Deliverables/Chiffrage"),

    # BELSPO notifications
    (["belspo", "notification_belspo", "belspo_notif"],
     "04_Deliverables/Belspo_Notifications"),

    # Technical report
    (["rapport_technique", "rapport technique", "technical_report",
      "rapport_dt", "dt_report"],
     "04_Deliverables/Rapport_Technique_DT"),

    # Structured project list (deliverable)
    (["liste_structuree", "structured_list", "liste_structurée"],
     "04_Deliverables/Liste_Structuree_Projets"),

    # RD Projects (kickoff)
    (["rd_projects", "projets_rd", "kickoff_projects", "rd_overview"],
     "01_Kickoff/RD_Projects"),
]


def classify_file(filename: str) -> str:
    """
    Return the subfolder path where this file should be placed.
    Matching is done on the lowercased filename (without extension).
    First matching rule wins. Falls back to _Inbox if nothing matches.
    """
    name_lower = os.path.splitext(filename)[0].lower()
    # normalise separators and common noise
    name_lower = name_lower.replace("-", "_").replace(" ", "_")

    for keywords, subfolder in CLASSIFICATION_RULES:
        for kw in keywords:
            kw_norm = kw.lower().replace(" ", "_").replace("-", "_")
            if kw_norm in name_lower:
                return subfolder

    return "_Inbox"


def create_client_folder(contract: dict, input_files: list = None) -> dict:
    """
    Create the standard folder hierarchy for a client mission.
    If input_files is provided, classify and copy each file into
    the appropriate subfolder. Unrecognised files go to _Inbox.
    """
    client      = contract["client"]
    mission     = contract["mission"]
    contract_id = contract["contract_id"]

    client_folder = os.path.join(
        BASE_PATH,
        client["name"].replace(" ", "_"),
        f"{mission['type']}_{mission['year']}",
    )

    created_paths = []
    try:
        # Create every subfolder
        for subfolder in SUBFOLDERS:
            full_path = os.path.join(client_folder, subfolder)
            os.makedirs(full_path, exist_ok=True)
            created_paths.append(full_path)

        # Write mission metadata
        metadata = {
            "contract_id":  contract_id,
            "client":       client,
            "mission":      mission,
            "created_at":   datetime.now().isoformat(),
            "created_by":   "leyton-automation",
        }
        with open(os.path.join(client_folder, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        # Classify and copy uploaded files
        file_log = []
        if input_files:
            for src_path in input_files:
                if not os.path.isfile(src_path):
                    continue
                filename   = os.path.basename(src_path)
                subfolder  = classify_file(filename)
                dest_dir   = os.path.join(client_folder, subfolder)
                dest_path  = os.path.join(dest_dir, filename)
                shutil.copy2(src_path, dest_path)
                file_log.append({"file": filename, "placed_in": subfolder})

        return {
            "status":          "success",
            "contract_id":     contract_id,
            "client_name":     client["name"],
            "folders_created": len(created_paths),
            "files_placed":    len(file_log),
            "file_log":        file_log,
            "base_path":       client_folder,
        }

    except Exception as exc:
        return {
            "status":      "error",
            "contract_id": contract_id,
            "client_name": client["name"],
            "error":       str(exc),
        }


def _contract_from_params() -> dict:
    """Build a contract dict from consultant-provided env vars."""
    g = lambda k, d="": os.environ.get(f"PARAM_{k.upper()}", d)
    return {
        "contract_id": f"CTR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "signed_date": datetime.now().strftime("%Y-%m-%d"),
        "client": {
            "name":          g("CLIENT_NAME", "New Client"),
            "id":            f"CLI-{datetime.now().strftime('%Y%m%d')}",
            "contact_name":  g("CONTACT_NAME", "—"),
            "contact_email": g("CONTACT_EMAIL", "—"),
            "country":       g("COUNTRY", "Belgium"),
        },
        "mission": {
            "type":       g("MISSION_TYPE", "Belspo"),
            "year":       int(g("YEAR", str(datetime.now().year))),
            "consultant": g("CONSULTANT", "—"),
            "status":     "active",
        },
    }


def run():
    log   = ServiceLogger("folder-creator")
    start = time.time()
    log.info("Service started")

    results = []
    try:
        # Resolve uploaded files from INPUT_FILES env var (set by API on upload)
        input_files = None
        env_files   = os.environ.get("INPUT_FILES")
        if env_files:
            input_files = json.loads(env_files)
            log.info("Files to classify", count=len(input_files))

        if os.environ.get("PARAM_CLIENT_NAME"):
            contracts = [_contract_from_params()]
            log.info("Running with consultant-provided parameters")
        else:
            contracts = MOCK_CONTRACTS[:1]
            log.info("Running in demo mode with mock data")

        for contract in contracts:
            result = create_client_folder(contract, input_files=input_files)
            results.append(result)
            if result["status"] == "success":
                log.info(
                    "Folder created",
                    client=result["client_name"],
                    folders=result["folders_created"],
                    files_placed=result["files_placed"],
                    path=result["base_path"],
                )
                for entry in result.get("file_log", []):
                    log.info(
                        "File classified",
                        file=entry["file"],
                        destination=entry["placed_in"],
                    )
            else:
                log.warning("Folder creation failed",
                            client=result["client_name"],
                            error=result.get("error"))

        ok           = len([r for r in results if r["status"] == "success"])
        duration_ms  = int((time.time() - start) * 1000)
        output_file  = results[0].get("base_path") if results else None
        log_run("folder-creator", status="success",
                output_file=output_file, duration_ms=duration_ms)
        log.info("Service completed",
                 processed=len(results), ok=ok, duration_ms=duration_ms)

        # Write a summary file so the API can pass it back to the UI
        summary = {
            "base_path":    results[0].get("base_path", "") if results else "",
            "client_name":  results[0].get("client_name", "") if results else "",
            "files_placed": sum(r.get("files_placed", 0) for r in results),
            "file_log":     [e for r in results for e in r.get("file_log", [])],
        }
        summary_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(summary_dir, exist_ok=True)
        with open(os.path.join(summary_dir, "last_result.json"), "w") as f:
            json.dump(summary, f, indent=2)

    except Exception as exc:
        duration_ms = int((time.time() - start) * 1000)
        log.error("Service failed", error=str(exc))
        log_run("folder-creator", status="failed",
                error_message=str(exc), duration_ms=duration_ms)
        raise

    return results


if __name__ == "__main__":
    run()
