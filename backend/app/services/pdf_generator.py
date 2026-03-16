"""
PDF Report Generator for MiroFish

Converts the markdown report into a polished, styled PDF automatically
after report generation completes.
"""

import os
import re
import logging
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable
)

logger = logging.getLogger(__name__)

# Color palette
ACCENT = HexColor("#1a73e8")
DARK = HexColor("#1a1a2e")
MUTED = HexColor("#555555")
LIGHT_BG = HexColor("#f0f4ff")
QUOTE_BG = HexColor("#f8f9fa")
QUOTE_BORDER = HexColor("#1a73e8")


def _get_styles():
    """Build the stylesheet for the PDF."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'CoverTitle', parent=styles['Title'],
        fontSize=28, leading=34, textColor=DARK,
        spaceAfter=12, alignment=TA_CENTER, fontName='Helvetica-Bold',
    ))
    styles.add(ParagraphStyle(
        'CoverSubtitle', parent=styles['Normal'],
        fontSize=14, leading=20, textColor=MUTED,
        alignment=TA_CENTER, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        'SectionHeading', parent=styles['Heading1'],
        fontSize=18, leading=24, textColor=ACCENT,
        spaceBefore=24, spaceAfter=12, fontName='Helvetica-Bold',
    ))
    styles.add(ParagraphStyle(
        'SubHeading', parent=styles['Heading2'],
        fontSize=13, leading=18, textColor=DARK,
        spaceBefore=14, spaceAfter=8, fontName='Helvetica-Bold',
    ))
    styles.add(ParagraphStyle(
        'BodyText2', parent=styles['Normal'],
        fontSize=10.5, leading=16, textColor=HexColor("#333333"),
        alignment=TA_JUSTIFY, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        'QuoteText', parent=styles['Normal'],
        fontSize=10, leading=15, textColor=HexColor("#444444"),
        leftIndent=24, rightIndent=12, spaceBefore=6, spaceAfter=10,
        fontName='Helvetica-Oblique',
    ))
    styles.add(ParagraphStyle(
        'MetaInfo', parent=styles['Normal'],
        fontSize=10, leading=16, textColor=MUTED, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        'TOCItem', parent=styles['Normal'],
        fontSize=11, leading=20, textColor=DARK, leftIndent=24,
    ))
    return styles


def _parse_markdown(md_text, styles):
    """Parse markdown into reportlab flowables."""
    story = []
    lines = md_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        if not line:
            i += 1
            continue

        # H1 - skip (cover title)
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
                width="100%", thickness=2, color=ACCENT, spaceAfter=4
            ))
            story.append(Paragraph(text, styles['SectionHeading']))
            i += 1
            continue

        # Bold subheading
        if line.startswith('**') and line.endswith('**') and len(line) > 4:
            text = line[2:-2]
            story.append(Paragraph(text, styles['SubHeading']))
            i += 1
            continue

        # Blockquote
        if line.startswith('> '):
            quote_text = line[2:].strip().strip('"')
            while i + 1 < len(lines) and lines[i + 1].startswith('> '):
                i += 1
                quote_text += ' ' + lines[i][2:].strip().strip('"')

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
                ('LINEBEFORE', (0, 0), (0, -1), 3, QUOTE_BORDER),
            ]))
            story.append(Spacer(1, 4))
            story.append(quote_table)
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Regular paragraph
        para_text = line
        while i + 1 < len(lines) and lines[i + 1].strip() and \
              not lines[i + 1].startswith('#') and \
              not lines[i + 1].startswith('>') and \
              not lines[i + 1].startswith('**') and \
              not lines[i + 1].strip() == '---':
            i += 1
            para_text += ' ' + lines[i].strip()

        para_text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', para_text)
        para_text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', para_text)
        story.append(Paragraph(para_text, styles['BodyText2']))
        i += 1

    return story


def _extract_h2_titles(md_text):
    """Extract H2 section titles from markdown for the table of contents."""
    return re.findall(r'^## (.+)$', md_text, re.MULTILINE)


def _add_header_footer(canvas, doc):
    """Header and footer on each page."""
    canvas.saveState()
    w, h = letter

    # Header
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(0.5)
    canvas.line(72, h - 50, w - 72, h - 50)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(72, h - 45, "MIROFISH SIMULATION REPORT")
    canvas.drawRightString(w - 72, h - 45, datetime.now().strftime("%B %d, %Y"))

    # Footer
    canvas.setStrokeColor(HexColor("#e0e0e0"))
    canvas.line(72, 50, w - 72, 50)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(72, 38, "Generated by MiroFish AI Simulation Platform")
    canvas.drawRightString(w - 72, 38, f"Page {doc.page}")

    canvas.restoreState()


def generate_pdf(report_folder: str, report_title: str = None,
                 simulation_stats: dict = None) -> str:
    """
    Generate a styled PDF from a completed MiroFish report.

    Args:
        report_folder: Path to the report folder containing full_report.md
        report_title: Optional custom title (extracted from markdown H1 if not provided)
        simulation_stats: Optional dict with keys like total_actions, twitter_actions,
                         reddit_actions, total_rounds, model_name

    Returns:
        Path to the generated PDF file
    """
    md_path = os.path.join(report_folder, "full_report.md")
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Report markdown not found: {md_path}")

    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # Extract title from H1 if not provided
    if not report_title:
        h1_match = re.search(r'^# (.+)$', md_text, re.MULTILINE)
        report_title = h1_match.group(1) if h1_match else "Simulation Report"

    # Split title if it has a colon
    title_parts = report_title.split(':', 1)
    main_title = title_parts[0].strip()
    subtitle = title_parts[1].strip() if len(title_parts) > 1 else None

    styles = _get_styles()
    pdf_path = os.path.join(report_folder, "report.pdf")

    doc = SimpleDocTemplate(
        pdf_path, pagesize=letter,
        topMargin=0.85 * inch, bottomMargin=0.75 * inch,
        leftMargin=1 * inch, rightMargin=1 * inch,
    )

    story = []

    # === Cover Page ===
    story.append(Spacer(1, 2.5 * inch))
    story.append(Paragraph(main_title, styles['CoverTitle']))

    if subtitle:
        story.append(Spacer(1, 8))
        story.append(Paragraph(subtitle, ParagraphStyle(
            'CoverTitle2', parent=styles['CoverTitle'],
            fontSize=22, textColor=ACCENT,
        )))

    story.append(Spacer(1, 24))

    # Summary line from markdown blockquote
    summary_match = re.search(r'^> (.+)$', md_text, re.MULTILINE)
    if summary_match:
        story.append(Paragraph(summary_match.group(1), styles['CoverSubtitle']))
        story.append(Spacer(1, 36))

    story.append(HRFlowable(width="40%", thickness=2, color=ACCENT, spaceAfter=16))

    # Metadata
    now_str = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(now_str, styles['MetaInfo']))

    if simulation_stats:
        total = simulation_stats.get('total_actions', '?')
        twitter = simulation_stats.get('twitter_actions', '?')
        reddit = simulation_stats.get('reddit_actions', '?')
        rounds = simulation_stats.get('total_rounds', '?')
        model = simulation_stats.get('model_name', 'GPT-4o-mini')
        story.append(Paragraph(
            f"{total} Agent Actions  |  {twitter} Twitter  |  {reddit} Reddit  |  {rounds} Rounds",
            styles['MetaInfo']
        ))
        story.append(Paragraph(f"Model: {model}  |  Platform: MiroFish", styles['MetaInfo']))

    story.append(PageBreak())

    # === Table of Contents ===
    section_titles = _extract_h2_titles(md_text)
    if section_titles:
        story.append(Paragraph("Table of Contents", styles['SectionHeading']))
        story.append(Spacer(1, 8))
        for idx, title in enumerate(section_titles, 1):
            story.append(Paragraph(f"{idx}. {title}", styles['TOCItem']))
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#e0e0e0")))
        story.append(Spacer(1, 12))

    # === Main Content ===
    content = _parse_markdown(md_text, styles)
    story.extend(content)

    # Build
    doc.build(story, onFirstPage=_add_header_footer, onLaterPages=_add_header_footer)
    logger.info(f"PDF report generated: {pdf_path}")
    return pdf_path
