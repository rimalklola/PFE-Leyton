# main.py — Timesheet Pre-fill Service
import json
import os
import sys
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mock_data import MOCK_CALENDAR_EVENTS

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def generate_timesheet(consultant_data: dict) -> dict:
    """
    Takes calendar events for a consultant and generates
    a pre-filled timesheet grouped by date and client.
    """
    consultant = consultant_data["consultant"]
    email = consultant_data["email"]
    events = consultant_data["events"]

    # Group events by date
    by_date = defaultdict(list)
    for event in events:
        by_date[event["date"]].append(event)

    timesheet = {
        "consultant": consultant,
        "email": email,
        "generated_at": datetime.now().isoformat(),
        "status": "pre-filled — awaiting consultant validation",
        "days": []
    }

    total_hours = 0

    for date in sorted(by_date.keys()):
        day_events = by_date[date]
        day_total = sum(e["duration_hours"] for e in day_events)
        total_hours += day_total

        day_entry = {
            "date": date,
            "total_hours": day_total,
            "entries": [
                {
                    "client": e["client"] or "Internal",
                    "client_id": e["client_id"] or "N/A",
                    "activity": e["title"],
                    "category": e["category"],
                    "hours": e["duration_hours"]
                }
                for e in day_events
            ]
        }
        timesheet["days"].append(day_entry)

    timesheet["total_hours"] = total_hours
    return timesheet


def run():
    print(f"\n{'='*50}")
    print(f"  LEYTON — Timesheet Pre-fill Service")
    print(f"  Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    os.makedirs(OUTPUT_PATH, exist_ok=True)

    results = []
    for consultant_data in MOCK_CALENDAR_EVENTS:
        timesheet = generate_timesheet(consultant_data)
        results.append(timesheet)

        # Save to JSON file
        filename = f"timesheet_{consultant_data['consultant'].replace(' ', '_')}.json"
        filepath = os.path.join(OUTPUT_PATH, filename)
        with open(filepath, "w") as f:
            json.dump(timesheet, f, indent=2)

        print(f"[OK] {timesheet['consultant']}")
        print(f"   Total hours: {timesheet['total_hours']}h across {len(timesheet['days'])} days")
        print(f"   Saved to: {filepath}\n")

    print(f"{'='*50}")
    print(f"  Done. {len(results)} timesheets generated.")
    print(f"{'='*50}\n")

    return results


if __name__ == "__main__":
    run()