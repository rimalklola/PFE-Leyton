import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
from mock_data import MOCK_HANDOVER_DATA

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

DARK_BLUE = "003366"
LIGHT_BLUE = "D9E1F2"
LIGHT_GREY = "F2F2F2"
WHITE = "FFFFFF"
GREEN = "E2EFDA"
RED = "FCE4D6"

def header_style(cell, bg=DARK_BLUE, fg=WHITE, bold=True):
    cell.fill = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
    cell.font = Font(color=fg, bold=bold)
    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    cell.border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

def section_style(cell, bg=LIGHT_BLUE):
    cell.fill = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
    cell.font = Font(bold=True, color="003366")
    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    cell.border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

def value_style(cell, bg=WHITE):
    cell.fill = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
    cell.font = Font(color="000000")
    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    cell.border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

def write_row(ws, row, label, value, label_bg=LIGHT_GREY):
    label_cell = ws.cell(row=row, column=1, value=label)
    section_style(label_cell, bg=label_bg)
    value_cell = ws.cell(row=row, column=2, value=value)
    value_style(value_cell)
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
    ws.row_dimensions[row].height = 30

def write_section_header(ws, row, title):
    cell = ws.cell(row=row, column=1, value=title)
    header_style(cell)
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
    ws.row_dimensions[row].height = 25

def generate_handover(data: dict) -> str:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Handover Sheet"

    ws.column_dimensions["A"].width = 35
    ws.column_dimensions["B"].width = 40
    ws.column_dimensions["C"].width = 20
    ws.column_dimensions["D"].width = 20

    row = 1

    # Title
    title_cell = ws.cell(row=row, column=1,
        value=f"HANDOVER FILE - {data['account_name'].upper()}")
    title_cell.font = Font(bold=True, size=14, color=WHITE)
    title_cell.fill = PatternFill(start_color=DARK_BLUE, end_color=DARK_BLUE, fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
    ws.row_dimensions[row].height = 35
    row += 1

    # Generated date
    date_cell = ws.cell(row=row, column=1,
        value=f"Generated on: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    date_cell.font = Font(italic=True, color="666666")
    date_cell.alignment = Alignment(horizontal="right")
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
    row += 2

    # Team Composition
    write_section_header(ws, row, "TEAM COMPOSITION")
    row += 1
    write_row(ws, row, "HO Done With", data["team"]["ho_done_with"])
    row += 1
    write_row(ws, row, "Tax Consultant", data["team"]["tax_consultant"])
    row += 1
    write_row(ws, row, "Sales", data["team"]["sales"])
    row += 2

    # Company Info
    write_section_header(ws, row, "COMPANY INFORMATION")
    row += 1
    ci = data["company_info"]
    write_row(ws, row, "Sector of Activity", ci["sector"])
    row += 1
    write_row(ws, row, "Type of Company", ci["type"])
    row += 1
    write_row(ws, row, "Account History", ci["account_history"])
    row += 1
    write_row(ws, row, "Belspo VAT Number", ci["belspo_vat"])
    row += 1
    write_row(ws, row, "Belspo Password", ci["belspo_password"])
    row += 1
    write_row(ws, row, "Belspo Notification", ci["belspo_notification"])
    row += 1
    write_row(ws, row, "Previous Control", ci["previous_control"])
    row += 2

    # Contract Info
    write_section_header(ws, row, "CONTRACT INFORMATION")
    row += 1
    co = data["contract_info"]
    write_row(ws, row, "Tax Measure", co["tax_measure"])
    row += 1
    write_row(ws, row, "Expected Year of Application", co["expected_year"])
    row += 1
    write_row(ws, row, "Remuneration System", co["remuneration_system"])
    row += 1
    write_row(ws, row, "GDPR", co["gdpr"])
    row += 2

    # POCs
    write_section_header(ws, row, "POINTS OF CONTACT")
    row += 1
    poc = data["pocs"]
    write_row(ws, row, "Technical Contact", poc["technical_contact"])
    row += 1
    write_row(ws, row, "HR Contact", poc["hr_contact"])
    row += 1
    write_row(ws, row, "Social Secretary", poc["social_secretary"])
    row += 2

    # Previous Mission Info
    write_section_header(ws, row, "PREVIOUS MISSION INFORMATION")
    row += 1
    pm = data["previous_mission"]
    write_row(ws, row, "Technical Report", pm["technical_report"])
    row += 1
    write_row(ws, row, "Timesheets", pm["timesheets"])
    row += 1
    write_row(ws, row, "Number of Projects", str(pm["nbr_projects"]))
    row += 1
    write_row(ws, row, "Number of Eligible Employees", str(pm["nbr_eligible_employees"]))
    row += 1
    write_row(ws, row, "Structural Research Certificate", pm["structural_research_certificate"])
    row += 1
    write_row(ws, row, "Mission Status", pm["mission_status"])
    row += 1
    write_row(ws, row, "Control", pm["control"])
    row += 1
    write_row(ws, row, "General Comments", pm["general_comments"])
    row += 1
    write_row(ws, row, "Next Step", pm["next_step"])
    row += 1
    write_row(ws, row, "Introduction Email", pm["introduction_email"])
    row += 2

    # Belspo Notifications
    write_section_header(ws, row, "BELSPO NOTIFICATIONS")
    row += 1
    for col, h in enumerate(["Notification ID", "Project Title", "Status", "Covers Until"], 1):
        cell = ws.cell(row=row, column=col, value=h)
        header_style(cell, bg=LIGHT_BLUE, fg="003366")
    row += 1
    for notif in data["belspo_notifications"]:
        ws.cell(row=row, column=1, value=notif["notification_id"])
        ws.cell(row=row, column=2, value=notif["project_title"])
        ws.cell(row=row, column=3, value=notif["status"])
        ws.cell(row=row, column=4, value=notif["covers_until"])
        for col in range(1, 5):
            value_style(ws.cell(row=row, column=col))
        row += 1
    row += 1

    # Employees
    write_section_header(ws, row, "ELIGIBLE EMPLOYEES")
    row += 1
    for col, h in enumerate(["Employee Name", "Diploma", "R&D %", ""], 1):
        cell = ws.cell(row=row, column=col, value=h)
        header_style(cell, bg=LIGHT_BLUE, fg="003366")
    row += 1
    for emp in data["employees"]:
        ws.cell(row=row, column=1, value=emp["name"])
        ws.cell(row=row, column=2, value=emp["diploma"])
        ws.cell(row=row, column=3, value=f"{emp['rd_percentage']}%")
        for col in range(1, 4):
            value_style(ws.cell(row=row, column=col))
        row += 1
    row += 1

    # Data Checklist
    write_section_header(ws, row, "DATA CHECKLIST")
    row += 1
    checklist = data["data_checklist"]
    items = {
        "Calculation Sheets": checklist["calculation_sheets"],
        "Control Documents": checklist["control_documents"],
        "Diplomas": checklist["diplomas"],
        "Individual Accounts": checklist["individual_accounts"]
    }
    for label, done in items.items():
        label_cell = ws.cell(row=row, column=1, value=label)
        section_style(label_cell, bg=LIGHT_GREY)
        status = "OK" if done else "MISSING"
        status_cell = ws.cell(row=row, column=2, value=status)
        bg = GREEN if done else RED
        value_style(status_cell, bg=bg)
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
        ws.row_dimensions[row].height = 25
        row += 1

    os.makedirs(OUTPUT_PATH, exist_ok=True)
    filename = f"Handover_{data['account_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    filepath = os.path.join(OUTPUT_PATH, filename)
    wb.save(filepath)
    return filepath


def run():
    print(f"\n{'='*50}")
    print(f"  LEYTON - Handover Sheet Generator")
    print(f"  Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    for data in MOCK_HANDOVER_DATA:
        filepath = generate_handover(data)
        print(f"[OK] {data['account_name']} - Handover sheet generated")
        print(f"  Saved to: {filepath}\n")

    print(f"{'='*50}")
    print(f"  Done. {len(MOCK_HANDOVER_DATA)} handover sheet(s) generated.")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    run()