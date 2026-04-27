# mock_data.py — Timesheet Pre-fill Service

from datetime import date

MOCK_CALENDAR_EVENTS = [
    {
        "consultant": "Sara Benali",
        "email": "s.benali@leyton.com",
        "events": [
            {
                "date": "2025-04-21",
                "title": "Kick-off meeting — Acme Industries",
                "client": "Acme Industries",
                "client_id": "CLI-001",
                "duration_hours": 2.0,
                "category": "Client Meeting"
            },
            {
                "date": "2025-04-21",
                "title": "R&D Analysis — Acme Industries",
                "client": "Acme Industries",
                "client_id": "CLI-001",
                "duration_hours": 3.0,
                "category": "Audit"
            },
            {
                "date": "2025-04-22",
                "title": "Technical Report writing — Acme Industries",
                "client": "Acme Industries",
                "client_id": "CLI-001",
                "duration_hours": 4.0,
                "category": "Report Writing"
            },
            {
                "date": "2025-04-22",
                "title": "Internal team meeting",
                "client": None,
                "client_id": None,
                "duration_hours": 1.0,
                "category": "Internal"
            }
        ]
    },
    {
        "consultant": "Karim Idrissi",
        "email": "k.idrissi@leyton.com",
        "events": [
            {
                "date": "2025-04-21",
                "title": "Audit session — TechNova Solutions",
                "client": "TechNova Solutions",
                "client_id": "CLI-002",
                "duration_hours": 3.5,
                "category": "Audit"
            },
            {
                "date": "2025-04-21",
                "title": "Timesheet review — TechNova Solutions",
                "client": "TechNova Solutions",
                "client_id": "CLI-002",
                "duration_hours": 2.0,
                "category": "Audit"
            },
            {
                "date": "2025-04-22",
                "title": "Belspo notification update — TechNova Solutions",
                "client": "TechNova Solutions",
                "client_id": "CLI-002",
                "duration_hours": 1.5,
                "category": "Belspo"
            }
        ]
    },
    {
        "consultant": "Nadia Chraibi",
        "email": "n.chraibi@leyton.com",
        "events": [
            {
                "date": "2025-04-21",
                "title": "Kick-off — GreenBuild SA",
                "client": "GreenBuild SA",
                "client_id": "CLI-003",
                "duration_hours": 2.0,
                "category": "Client Meeting"
            },
            {
                "date": "2025-04-22",
                "title": "R&D project analysis — GreenBuild SA",
                "client": "GreenBuild SA",
                "client_id": "CLI-003",
                "duration_hours": 3.0,
                "category": "Audit"
            },
            {
                "date": "2025-04-22",
                "title": "DT writing — GreenBuild SA",
                "client": "GreenBuild SA",
                "client_id": "CLI-003",
                "duration_hours": 2.5,
                "category": "Report Writing"
            }
        ]
    }
]