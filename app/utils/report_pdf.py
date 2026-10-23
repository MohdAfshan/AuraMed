from datetime import datetime
from pathlib import Path
from typing import Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from xml.sax.saxutils import escape


SectionRows = Sequence[tuple[str, ...] | str]


def generate_report_pdf(
    file_path: str | Path,
    hospital_name: str,
    patient_name: str,
    patient_code: str,
    report_title: str,
    report_date: datetime,
    sections: Sequence[tuple[str, SectionRows]],
) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Letterhead",
            parent=styles["Heading2"],
            alignment=TA_CENTER,
            fontSize=16,
            leading=19,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="HospitalContact",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            fontSize=8.5,
            textColor=colors.HexColor("#4b5563"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportHeading",
            parent=styles["Heading1"],
            fontSize=15,
            leading=18,
            spaceBefore=14,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading3"],
            fontSize=10.5,
            leading=13,
            spaceBefore=10,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FooterDisclaimer",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor("#6b7280"),
            italic=True,
        )
    )

    story = [
        Paragraph(escape(hospital_name), styles["Letterhead"]),
        Paragraph(
            "125 Meridian Avenue, Suite 200, Springfield, NY 10001 | "
            "(555) 014-2026",
            styles["HospitalContact"],
        ),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1f4e79")),
        Spacer(1, 10),
    ]

    report_type = _report_type_for_title(report_title)
    patient_info = [
        [
            Paragraph("<b>Patient Name</b>", styles["BodySmall"]),
            Paragraph(escape(patient_name), styles["BodySmall"]),
            Paragraph("<b>Patient ID</b>", styles["BodySmall"]),
            Paragraph(escape(patient_code), styles["BodySmall"]),
        ],
        [
            Paragraph("<b>Report Date</b>", styles["BodySmall"]),
            Paragraph(report_date.strftime("%d-%b-%Y"), styles["BodySmall"]),
            Paragraph("<b>Report Type</b>", styles["BodySmall"]),
            Paragraph(escape(report_type), styles["BodySmall"]),
        ],
    ]
    info_table = Table(patient_info, colWidths=[1.05 * inch, 2.15 * inch, 1.05 * inch, 2.15 * inch])
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf1f8")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#eaf1f8")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#9ca3af")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d1d5db")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([info_table, Paragraph(escape(report_title), styles["ReportHeading"])])

    for section_title, rows in sections:
        row_list = list(rows)
        story.append(Paragraph(escape(section_title), styles["SectionHeading"]))
        if _is_lab_section(row_list):
            lab_rows = [
                [
                    Paragraph("<b>Test</b>", styles["BodySmall"]),
                    Paragraph("<b>Result</b>", styles["BodySmall"]),
                    Paragraph("<b>Reference Range</b>", styles["BodySmall"]),
                ]
            ]
            lab_rows.extend(
                [
                    Paragraph(escape(row[0]), styles["BodySmall"]),
                    Paragraph(escape(row[1]), styles["BodySmall"]),
                    Paragraph(escape(row[2]), styles["BodySmall"]),
                ]
                for row in row_list
            )
            section_table = Table(lab_rows, colWidths=[2.4 * inch, 1.8 * inch, 2.2 * inch])
            section_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbe7f2")),
                        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#6b7280")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#9ca3af")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.append(section_table)
        else:
            for row in row_list:
                text = row if isinstance(row, str) else " - ".join(row)
                story.append(
                    Paragraph(f"&bull;&nbsp;&nbsp;{escape(text)}", styles["BodySmall"])
                )

    story.extend(
        [
            Spacer(1, 24),
            Paragraph("<b>Reviewing Physician: Dr. A. Mehta, MD</b>", styles["BodySmall"]),
            Spacer(1, 8),
            HRFlowable(width=2.2 * inch, thickness=0.6, color=colors.black, hAlign=TA_LEFT),
            Spacer(1, 12),
            Paragraph(
                "This is a computer-generated mock report for development/testing purposes.",
                styles["FooterDisclaimer"],
            ),
        ]
    )

    document = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=report_title,
        author=hospital_name,
    )
    document.build(story)


def _is_lab_section(rows: list[tuple[str, ...] | str]) -> bool:
    return bool(rows) and all(isinstance(row, tuple) and len(row) == 3 for row in rows)


def _report_type_for_title(title: str) -> str:
    normalized_title = title.lower()
    if "blood" in normalized_title or "cbc" in normalized_title:
        return "BLOOD"
    if "ecg" in normalized_title:
        return "ECG"
    if "prescription" in normalized_title:
        return "PRESCRIPTION"
    return "CLINICAL REVIEW"
