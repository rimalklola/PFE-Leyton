# mock_data.py -- Galileo Reporter Service
# Simulates data from two sources:
#   1. MOCK_GALILEO_MISSIONS  -- what Galileo (CRM) knows about each mission
#   2. MOCK_SERVICE_STATES    -- what each of the 4 microservices has actually produced
#
# The reporter cross-references both to flag misalignments.

from datetime import date

# ---------------------------------------------------------------------------
# 1. GALILEO MISSION DATA (mirrors Galileo CRM records)
#    Stages: kickoff | audit | preparation | deliverables | internal
#    Status: active | on_hold | closed
# ---------------------------------------------------------------------------

MOCK_GALILEO_MISSIONS = [
    {
        "mission_id": "MSN-2025-001",
        "client_id": "CLI-001",
        "client_name": "Acme Industries",
        "consultant": "Sara Benali",
        "mission_type": "Belspo",
        "stage": "audit",
        "status": "active",
        "start_date": "2025-01-15",
        "expected_end_date": "2025-06-30",
        "belspo_notification_id": "BN-2025-001",
        "belspo_expiry_date": "2025-06-01",   # expiring soon -- should trigger alert
        "handover_required": False,
        "assigned_year": 2025
    },
    {
        "mission_id": "MSN-2025-002",
        "client_id": "CLI-002",
        "client_name": "TechNova Solutions",
        "consultant": "Karim Idrissi",
        "mission_type": "Belspo",
        "stage": "preparation",
        "status": "active",
        "start_date": "2025-02-01",
        "expected_end_date": "2025-09-30",
        "belspo_notification_id": "BN-2025-002",
        "belspo_expiry_date": "2025-12-31",
        "handover_required": True,             # consultant is leaving -- handover needed
        "assigned_year": 2025
    },
    {
        "mission_id": "MSN-2025-003",
        "client_id": "CLI-003",
        "client_name": "GreenBuild SA",
        "consultant": "Nadia Chraibi",
        "mission_type": "Belspo",
        "stage": "deliverables",
        "status": "active",
        "start_date": "2025-01-10",
        "expected_end_date": "2025-05-31",
        "belspo_notification_id": "BN-2025-003",
        "belspo_expiry_date": "2025-05-15",   # already expired (past today)
        "handover_required": False,
        "assigned_year": 2025
    },
    {
        "mission_id": "MSN-2025-004",
        "client_id": "CLI-004",
        "client_name": "Pharmatech NV",
        "consultant": "Youssef Amrani",
        "mission_type": "Belspo",
        "stage": "kickoff",
        "status": "active",
        "start_date": "2025-04-01",
        "expected_end_date": "2025-12-31",
        "belspo_notification_id": None,        # no notification filed yet
        "belspo_expiry_date": None,
        "handover_required": False,
        "assigned_year": 2025
    },
    {
        "mission_id": "MSN-2025-005",
        "client_id": "CLI-005",
        "client_name": "Solaris Energy",
        "consultant": "Leila Bennani",
        "mission_type": "Belspo",
        "stage": "internal",
        "status": "closed",
        "start_date": "2024-03-01",
        "expected_end_date": "2025-03-31",
        "belspo_notification_id": "BN-2024-007",
        "belspo_expiry_date": "2025-03-31",
        "handover_required": False,
        "assigned_year": 2024
    }
]

# ---------------------------------------------------------------------------
# 2. SERVICE STATE DATA
#    Simulates what each microservice has actually produced or recorded.
#    In a real deployment this would be read from a shared DB or service logs.
#    Here it is hardcoded to intentionally include gaps for the reporter to catch.
# ---------------------------------------------------------------------------

MOCK_SERVICE_STATES = {

    # folder-creator: did it create the client folder for this mission?
    "folder_creator": {
        "CLI-001": {"created": True,  "created_at": "2025-01-16", "stage_complete": ["01_Kickoff", "02_Audit"]},
        "CLI-002": {"created": True,  "created_at": "2025-02-02", "stage_complete": ["01_Kickoff"]},
        "CLI-003": {"created": True,  "created_at": "2025-01-11", "stage_complete": ["01_Kickoff", "02_Audit", "03_Preparation", "04_Deliverables"]},
        "CLI-004": {"created": False, "created_at": None,         "stage_complete": []},   # folder never created
        "CLI-005": {"created": True,  "created_at": "2024-03-02", "stage_complete": ["01_Kickoff", "02_Audit", "03_Preparation", "04_Deliverables", "05_Internal"]}
    },

    # timesheet-prefill: was a timesheet processed this year for this client?
    "timesheet_prefill": {
        "CLI-001": {"processed": True,  "last_run": "2025-03-31", "months_covered": ["january", "february", "march"]},
        "CLI-002": {"processed": False, "last_run": None,         "months_covered": []},   # no timesheet yet
        "CLI-003": {"processed": True,  "last_run": "2025-04-30", "months_covered": ["january", "february", "march", "april"]},
        "CLI-004": {"processed": False, "last_run": None,         "months_covered": []},
        "CLI-005": {"processed": True,  "last_run": "2025-03-31", "months_covered": ["january", "february", "march"]}
    },

    # belspo-extractor: was the Belspo notification extracted and up to date?
    "belspo_extractor": {
        "CLI-001": {"extracted": True,  "last_run": "2025-04-01", "notification_status": "new"},
        "CLI-002": {"extracted": True,  "last_run": "2025-04-01", "notification_status": "new"},
        "CLI-003": {"extracted": True,  "last_run": "2025-02-15", "notification_status": "already_processed"},  # old extraction, expiry passed
        "CLI-004": {"extracted": False, "last_run": None,         "notification_status": None},  # nothing filed
        "CLI-005": {"extracted": True,  "last_run": "2025-03-01", "notification_status": "already_processed"}
    },

    # handover-generator: was a handover sheet generated (only matters if handover_required=True)?
    "handover_generator": {
        "CLI-001": {"generated": False, "generated_at": None},
        "CLI-002": {"generated": False, "generated_at": None},   # handover required but NOT generated -- alert
        "CLI-003": {"generated": False, "generated_at": None},
        "CLI-004": {"generated": False, "generated_at": None},
        "CLI-005": {"generated": True,  "generated_at": "2025-03-28"}
    }
}

# Alert severity levels used in the report
SEVERITY = {
    "CRITICAL": "C1 - CRITICAL",
    "WARNING":  "C2 - WARNING",
    "INFO":     "C3 - INFO",
    "OK":       "OK"
}
