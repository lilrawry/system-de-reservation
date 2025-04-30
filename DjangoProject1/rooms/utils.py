from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime

def generate_reservation_receipt(reservation):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Add title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    story.append(Paragraph("Reservation Receipt", title_style))
    story.append(Spacer(1, 20))

    # Add reservation details
    data = [
        ['Reservation Details', ''],
        ['Room Name:', reservation.room.name],
        ['Start Time:', reservation.start_time.strftime('%Y-%m-%d %H:%M')],
        ['End Time:', reservation.end_time.strftime('%Y-%m-%d %H:%M')],
        ['Total Price:', f'${reservation.total_price:.2f}'],
        ['Status:', reservation.status],
        ['', ''],
        ['User Information', ''],
        ['Name:', f'{reservation.user.first_name} {reservation.user.last_name}'],
        ['Email:', reservation.user.email],
    ]

    table = Table(data, colWidths=[3*inch, 3*inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, 7), (-1, 7), colors.lightgrey),
    ]))

    story.append(table)
    story.append(Spacer(1, 20))

    # Add footer
    footer_text = f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    story.append(Paragraph(footer_text, styles['Normal']))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
