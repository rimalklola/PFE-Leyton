# mock_data.py — Timesheet Pre-fill Service

# Projects with their R&D percentages
MOCK_PROJECTS = [
    {"code": "P001", "name": "AI Quality Control System", "client": "TechNova Solutions", "rd_percentage": 0.9},
    {"code": "P002", "name": "Smart Sensor Integration", "client": "TechNova Solutions", "rd_percentage": 0.5},
    {"code": "P003", "name": "Automated Safety Compliance", "client": "Acme Industries", "rd_percentage": 0.7},
    {"code": "P004", "name": "Explosion Risk Modelling", "client": "GreenBuild SA", "rd_percentage": 0.8},
    {"code": "P005", "name": "Process Hazard Analysis", "client": "GreenBuild SA", "rd_percentage": 0.5},
]

# Employee timesheets — hours worked per project per month
MOCK_TIMESHEETS = [
    {
        "employee": "Alice Dubois",
        "eligible": True,
        "diploma": "Master Industrial Engineering",
        "hours_per_project": {
            "P001": {"january": 45.5, "february": 50.0, "march": 48.0, "april": 42.0,
                     "may": 0, "june": 0, "july": 0, "august": 0,
                     "september": 0, "october": 0, "november": 0, "december": 0},
            "P002": {"january": 20.0, "february": 18.5, "march": 22.0, "april": 25.0,
                     "may": 0, "june": 0, "july": 0, "august": 0,
                     "september": 0, "october": 0, "november": 0, "december": 0},
        }
    },
    {
        "employee": "Bruno Lefevre",
        "eligible": True,
        "diploma": "Doctor of Applied Sciences",
        "hours_per_project": {
            "P003": {"january": 60.0, "february": 55.0, "march": 58.0, "april": 62.0,
                     "may": 50.0, "june": 48.0, "july": 0, "august": 0,
                     "september": 0, "october": 0, "november": 0, "december": 0},
            "P004": {"january": 30.0, "february": 35.0, "march": 28.0, "april": 32.0,
                     "may": 40.0, "june": 38.0, "july": 0, "august": 0,
                     "september": 0, "october": 0, "november": 0, "december": 0},
        }
    },
    {
        "employee": "Claire Martin",
        "eligible": True,
        "diploma": "Master Chemical Engineering",
        "hours_per_project": {
            "P002": {"january": 35.0, "february": 40.0, "march": 38.0, "april": 36.0,
                     "may": 42.0, "june": 44.0, "july": 0, "august": 0,
                     "september": 0, "october": 0, "november": 0, "december": 0},
            "P005": {"january": 25.0, "february": 22.0, "march": 28.0, "april": 30.0,
                     "may": 20.0, "june": 18.0, "july": 0, "august": 0,
                     "september": 0, "october": 0, "november": 0, "december": 0},
        }
    },
    {
        "employee": "David Peeters",
        "eligible": True,
        "diploma": "Bachelor Electromechanics",
        "hours_per_project": {
            "P001": {"january": 50.0, "february": 48.0, "march": 52.0, "april": 55.0,
                     "may": 0, "june": 0, "july": 0, "august": 0,
                     "september": 0, "october": 0, "november": 0, "december": 0},
            "P004": {"january": 20.0, "february": 22.0, "march": 18.0, "april": 25.0,
                     "may": 0, "june": 0, "july": 0, "august": 0,
                     "september": 0, "october": 0, "november": 0, "december": 0},
        }
    },
]

MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
]