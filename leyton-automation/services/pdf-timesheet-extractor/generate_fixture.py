import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

FIXTURE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_timesheet.pdf")

FIXTURE_ROWS = [
    ("Alice Dubois", "75012587693", "P001", "January", "45.5"),
    ("Alice Dubois", "75012587693", "P001", "February", "50.0"),
    ("Alice Dubois", "75012587693", "P001", "March", "48.0"),
    ("Alice Dubois", "75012587693", "P002", "January", "20.0"),
    ("Alice Dubois", "75012587693", "P002", "February", "18.5"),
    ("Alice Dubois", "75012587693", "P002", "March", "22.0"),
    ("Bruno Lefevre", "82043612589", "P003", "January", "60.0"),
    ("Bruno Lefevre", "82043612589", "P003", "February", "55.0"),
    ("Bruno Lefevre", "82043612589", "P003", "March", "58.0"),
    ("Bruno Lefevre", "82043612589", "P004", "January", "30.0"),
    ("Bruno Lefevre", "82043612589", "P004", "February", "35.0"),
    ("Bruno Lefevre", "82043612589", "P004", "March", "28.0"),
    ("Claire Martin", "90123456789", "P002", "January", "35.0"),
    ("Claire Martin", "90123456789", "P002", "February", "40.0"),
    ("Claire Martin", "90123456789", "P002", "March", "38.0"),
    ("Claire Martin", "90123456789", "P005", "January", "25.0"),
    ("Claire Martin", "90123456789", "P005", "February", "22.0"),
    ("Claire Martin", "90123456789", "P005", "March", "28.0"),
    ("David Peeters", "88065478920", "P001", "April", "55.0"),
    ("David Peeters", "88065478920", "P001", "May", "52.0"),
    ("David Peeters", "88065478920", "P001", "June", "48.0"),
    ("David Peeters", "88065478920", "P004", "April", "25.0"),
    ("David Peeters", "88065478920", "P004", "May", "30.0"),
    ("David Peeters", "88065478920", "P004", "June", "28.0"),
]


def generate(output_path=None):
    path = output_path or FIXTURE_PATH
    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    story = []

    story.append(Paragraph("LEYTON BELGIUM SA", styles["Title"]))
    story.append(Paragraph("R&D Timesheet Export — HR System", styles["Heading2"]))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d')}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    headers = ["Employee Name", "National Registry", "Project Code", "Month", "Hours Worked"]
    table_data = [headers] + [list(row) for row in FIXTURE_ROWS]

    col_widths = [4.5 * cm, 3.5 * cm, 3.0 * cm, 2.5 * cm, 3.0 * cm]

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    story.append(t)
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        f"Confidential — LEYTON Belgium SA — {datetime.now().year}",
        styles["Normal"],
    ))

    doc.build(story)
    return path


if __name__ == "__main__":
    result = generate()
    print(f"Fixture generated: {result}")
