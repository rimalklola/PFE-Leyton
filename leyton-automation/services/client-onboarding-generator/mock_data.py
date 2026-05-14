MOCK_CONTRACTS = [
    {
        "client_id": "CLI-001",
        "client_name": "Acme Industries",
        "mission_type": "Belspo",
        "start_date": "2025-01-15",
        "consultant_name": "Sara Benali",
        "consultant_email": "sara.benali@leyton.com",
        "tl_name": "Mehdi Ouali",
        "tl_email": "mehdi.ouali@leyton.com",
    },
    {
        "client_id": "CLI-002",
        "client_name": "TechNova Solutions",
        "mission_type": "Belspo",
        "start_date": "2025-02-01",
        "consultant_name": "Karim Idrissi",
        "consultant_email": "karim.idrissi@leyton.com",
        "tl_name": "Mehdi Ouali",
        "tl_email": "mehdi.ouali@leyton.com",
    },
    {
        "client_id": "CLI-003",
        "client_name": "GreenBuild SA",
        "mission_type": "Belspo",
        "start_date": "2025-01-10",
        "consultant_name": "Nadia Chraibi",
        "consultant_email": "nadia.chraibi@leyton.com",
        "tl_name": "Mehdi Ouali",
        "tl_email": "mehdi.ouali@leyton.com",
    },
]

REQUIRED_DOCUMENTS = [
    {
        "document": "Employee Diplomas",
        "description": "Original or certified copy for each R&D-eligible employee",
        "format": "PDF",
        "deadline_days": 14,
    },
    {
        "document": "Individual Salary Accounts",
        "description": "Annual salary accounts per eligible employee",
        "format": "Excel / PDF",
        "deadline_days": 21,
    },
    {
        "document": "Timesheet System Description",
        "description": "HR system export or manual timesheet template",
        "format": "Excel / PDF",
        "deadline_days": 21,
    },
    {
        "document": "List of R&D Projects",
        "description": "Project names with brief technical descriptions",
        "format": "Excel / Word",
        "deadline_days": 7,
    },
    {
        "document": "Belspo VAT Number",
        "description": "Company VAT number used for Belspo filings",
        "format": "Text",
        "deadline_days": 7,
    },
    {
        "document": "Previous Belspo Notifications",
        "description": "Copies of any prior Belspo notifications (if applicable)",
        "format": "PDF",
        "deadline_days": 14,
    },
    {
        "document": "GDPR Consent Form",
        "description": "Signed GDPR consent form per eligible employee",
        "format": "PDF",
        "deadline_days": 14,
    },
]

TIMELINE = [
    {"milestone": "Kickoff Call", "offset_days": 0, "description": "Introduction call with client team"},
    {"milestone": "Belspo Notification Filing", "offset_days": 14,
     "description": "Submit Belspo notification — requires employee list and project info"},
    {"milestone": "SS Application", "offset_days": 30,
     "description": "Social security application for eligible employees"},
    {"milestone": "First Quarterly Review", "offset_days": 90,
     "description": "Review collected timesheets and validate R&D allocation"},
]
