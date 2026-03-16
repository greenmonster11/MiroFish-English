#!/usr/bin/env python3
"""Generate a polished PDF from the MiroFish simulation report."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib import colors
import re
from datetime import datetime


ACCENT = HexColor("#1a73e8")
DARK = HexColor("#1a1a2e")
MUTED = HexColor("#555555")
LIGHT_BG = HexColor("#f0f4ff")
QUOTE_BG = HexColor("#f8f9fa")
QUOTE_BORDER = HexColor("#1a73e8")


def get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'CoverTitle',
        parent=styles['Title'],
        fontSize=28,
        leading=34,
        textColor=DARK,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    ))

    styles.add(ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        leading=20,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading1'],
        fontSize=18,
        leading=24,
        textColor=ACCENT,
        spaceBefore=24,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderPadding=0,
    ))

    styles.add(ParagraphStyle(
        'SubHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=18,
        textColor=DARK,
        spaceBefore=14,
        spaceAfter=8,
        fontName='Helvetica-Bold',
    ))

    styles.add(ParagraphStyle(
        'BodyText2',
        parent=styles['Normal'],
        fontSize=10.5,
        leading=16,
        textColor=HexColor("#333333"),
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        'QuoteText',
        parent=styles['Normal'],
        fontSize=10,
        leading=15,
        textColor=HexColor("#444444"),
        leftIndent=24,
        rightIndent=12,
        spaceBefore=6,
        spaceAfter=10,
        fontName='Helvetica-Oblique',
        borderWidth=0,
    ))

    styles.add(ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontSize=10.5,
        leading=16,
        textColor=HexColor("#333333"),
        leftIndent=24,
        spaceAfter=4,
        bulletIndent=12,
    ))

    return styles


def parse_markdown(md_text, styles):
    """Parse markdown text into reportlab flowables."""
    story = []
    lines = md_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # H1 - skip (used as cover title)
        if line.startswith('# ') and not line.startswith('## '):
            i += 1
            continue

        # Horizontal rule
        if line.strip() == '---':
            story.append(Spacer(1, 6))
            story.append(HRFlowable(
                width="100%", thickness=1, color=HexColor("#e0e0e0"),
                spaceAfter=6, spaceBefore=6
            ))
            i += 1
            continue

        # H2 - Section heading
        if line.startswith('## '):
            text = line[3:].strip()
            story.append(Spacer(1, 8))
            story.append(HRFlowable(
                width="100%", thickness=2, color=ACCENT,
                spaceAfter=4, spaceBefore=0
            ))
            story.append(Paragraph(text, styles['SectionHeading']))
            i += 1
            continue

        # Bold subheading line (e.g., **Something**)
        if line.startswith('**') and line.endswith('**') and len(line) > 4:
            text = line[2:-2]
            story.append(Paragraph(text, styles['SubHeading']))
            i += 1
            continue

        # Blockquote (> prefix) - styled summary box
        if line.startswith('> '):
            quote_text = line[2:].strip().strip('"')
            # Check for multi-line quotes
            while i + 1 < len(lines) and lines[i + 1].startswith('> '):
                i += 1
                quote_text += ' ' + lines[i][2:].strip().strip('"')

            # Create a styled quote with left border
            quote_table = Table(
                [[Paragraph(f'"{quote_text}"', styles['QuoteText'])]],
                colWidths=[6.2 * inch],
            )
            quote_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), QUOTE_BG),
                ('LEFTPADDING', (0, 0), (-1, -1), 16),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LINEBEFOREDECL', (0, 0), (0, -1), 3, QUOTE_BORDER),
                ('LINEBEFORE', (0, 0), (0, -1), 3, QUOTE_BORDER),
            ]))
            story.append(Spacer(1, 4))
            story.append(quote_table)
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Regular paragraph - collect continuation lines
        para_text = line
        while i + 1 < len(lines) and lines[i + 1].strip() and \
              not lines[i + 1].startswith('#') and \
              not lines[i + 1].startswith('>') and \
              not lines[i + 1].startswith('**') and \
              not lines[i + 1].strip() == '---':
            i += 1
            para_text += ' ' + lines[i].strip()

        # Convert inline markdown bold to reportlab tags
        para_text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', para_text)
        para_text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', para_text)

        story.append(Paragraph(para_text, styles['BodyText2']))
        i += 1

    return story


def add_header_footer(canvas, doc):
    """Add header and footer to each page."""
    canvas.saveState()

    # Header line
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(0.5)
    canvas.line(72, letter[1] - 50, letter[0] - 72, letter[1] - 50)

    # Header text
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(72, letter[1] - 45, "MIROFISH SIMULATION REPORT")
    canvas.drawRightString(letter[0] - 72, letter[1] - 45, "March 15, 2026")

    # Footer
    canvas.setStrokeColor(HexColor("#e0e0e0"))
    canvas.line(72, 50, letter[0] - 72, 50)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(72, 38, "Generated by MiroFish AI Simulation Platform")
    canvas.drawRightString(letter[0] - 72, 38, f"Page {doc.page}")

    canvas.restoreState()


def build_cover_page(styles):
    """Create a cover page."""
    story = []
    story.append(Spacer(1, 2.5 * inch))

    # Title
    story.append(Paragraph(
        "Future Prediction Report",
        styles['CoverTitle']
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Options Plays in a Volatile Market",
        ParagraphStyle(
            'CoverTitle2',
            parent=styles['CoverTitle'],
            fontSize=22,
            textColor=ACCENT,
        )
    ))

    story.append(Spacer(1, 24))

    # Subtitle / summary
    story.append(Paragraph(
        "AI-powered multi-agent simulation analyzing stock options strategies<br/>"
        "amid the Iran-Israel military conflict and FOMC policy decisions",
        styles['CoverSubtitle']
    ))

    story.append(Spacer(1, 36))

    # Divider
    story.append(HRFlowable(
        width="40%", thickness=2, color=ACCENT,
        spaceAfter=16, spaceBefore=0
    ))

    # Metadata
    meta_style = ParagraphStyle(
        'MetaInfo',
        parent=styles['Normal'],
        fontSize=10,
        leading=16,
        textColor=MUTED,
        alignment=TA_CENTER,
    )
    story.append(Paragraph("March 15, 2026", meta_style))
    story.append(Paragraph("337 Agent Actions  |  190 Twitter  |  147 Reddit  |  72 Rounds", meta_style))
    story.append(Paragraph("Model: GPT-4o-mini  |  Platform: MiroFish", meta_style))

    story.append(Spacer(1, 1.5 * inch))

    # Key metrics box
    metrics_data = [
        ["SPY", "$662.29", "VIX", "27.28", "WTI", "~$94"],
        ["Brent", "~$100", "Jobs", "-92K", "Sentiment", "55.5"],
    ]
    metrics_table = Table(metrics_data, colWidths=[1.0*inch, 0.9*inch] * 3)
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('TEXTCOLOR', (0, 0), (0, -1), ACCENT),
        ('TEXTCOLOR', (2, 0), (2, -1), ACCENT),
        ('TEXTCOLOR', (4, 0), (4, -1), ACCENT),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTNAME', (4, 0), (4, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#d0d8f0")),
        ('BOX', (0, 0), (-1, -1), 1, ACCENT),
    ]))
    story.append(metrics_table)

    story.append(PageBreak())
    return story


def main():
    report_path = "/Users/macbookpro/Desktop/untitled folder 2/backend/uploads/reports/report_41a3824447b5/full_report.md"
    output_path = "/Users/macbookpro/Desktop/MiroFish_Report_Iran_Options.pdf"

    with open(report_path, 'r') as f:
        md_text = f.read()

    styles = get_styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        topMargin=0.85 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
    )

    story = []

    # Cover page
    story.extend(build_cover_page(styles))

    # Table of contents style header
    story.append(Paragraph("Table of Contents", styles['SectionHeading']))
    story.append(Spacer(1, 8))
    toc_items = [
        "1. Market Dynamics and Price Influences",
        "2. Agent Reactions and Strategic Movements",
        "3. Emerging Trends in Trading Behavior",
        "4. Potential Risks and Market Volatility",
    ]
    for item in toc_items:
        story.append(Paragraph(item, ParagraphStyle(
            'TOCItem',
            parent=styles['Normal'],
            fontSize=11,
            leading=20,
            textColor=DARK,
            leftIndent=24,
        )))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#e0e0e0")))
    story.append(Spacer(1, 12))

    # Parse and add main content
    content = parse_markdown(md_text, styles)
    story.extend(content)

    # Build PDF
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    print(f"PDF saved to: {output_path}")


if __name__ == '__main__':
    main()
