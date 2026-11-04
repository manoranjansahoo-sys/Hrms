import io
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def generate_payslip_pdf(payslip):
    """
    Generates a professional corporate PDF payslip using ReportLab.
    Returns a BytesIO buffer containing the PDF bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1B5E20'),
        alignment=1, # Center
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4B5563'),
        alignment=1
    )
    header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#1B5E20'),
        fontName='Helvetica-Bold'
    )
    cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor('#1F2937'))
    cell_normal = ParagraphStyle('CellNormal', parent=styles['Normal'], fontSize=9, fontName='Helvetica', textColor=colors.HexColor('#374151'))
    cell_right = ParagraphStyle('CellRight', parent=styles['Normal'], fontSize=9, alignment=2, textColor=colors.HexColor('#1F2937'))
    cell_right_bold = ParagraphStyle('CellRightBold', parent=styles['Normal'], fontSize=9, alignment=2, fontName='Helvetica-Bold', textColor=colors.HexColor('#1F2937'))

    # 1. Company Header
    elements.append(Paragraph("COMPANY HRMS ENTERPRISE", title_style))
    elements.append(Paragraph("Embassy Tech Village, Outer Ring Road, Bengaluru, Karnataka 560103", subtitle_style))
    month_str = payslip.payroll_period.get_month_display()
    elements.append(Paragraph(f"<b>CONFIDENTIAL SALARY PAYSLIP - {month_str.upper()} {payslip.year}</b>", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1B5E20'), spaceAfter=12))

    # 2. Employee Details Grid
    emp = payslip.employee
    emp_info_data = [
        [
            Paragraph("<b>Employee ID:</b>", cell_normal), Paragraph(emp.emp_id, cell_bold),
            Paragraph("<b>Employee Name:</b>", cell_normal), Paragraph(emp.full_name, cell_bold)
        ],
        [
            Paragraph("<b>Department:</b>", cell_normal), Paragraph(emp.department.name if emp.department else "N/A", cell_normal),
            Paragraph("<b>Designation:</b>", cell_normal), Paragraph(emp.designation.title if emp.designation else "N/A", cell_normal)
        ],
        [
            Paragraph("<b>Site Location:</b>", cell_normal), Paragraph(emp.site.name if emp.site else "Bengaluru HQ", cell_normal),
            Paragraph("<b>Date of Joining:</b>", cell_normal), Paragraph(emp.joining_date.strftime('%d-%b-%Y') if emp.joining_date else "N/A", cell_normal)
        ],
        [
            Paragraph("<b>Bank Name:</b>", cell_normal), Paragraph(emp.bank_name or "N/A", cell_normal),
            Paragraph("<b>Bank Account:</b>", cell_normal), Paragraph(emp.masked_account_number, cell_normal)
        ],
        [
            Paragraph("<b>PAN Number:</b>", cell_normal), Paragraph(emp.pan_number or "N/A", cell_normal),
            Paragraph("<b>Payment Status:</b>", cell_normal), Paragraph(f"<b>{payslip.get_status_display()}</b>", cell_bold)
        ]
    ]

    emp_table = Table(emp_info_data, colWidths=[100, 170, 100, 170])
    emp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#F3F4F6')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 10))

    # 3. Attendance Summary
    att_data = [
        [
            Paragraph("<b>Total Month Days</b>", cell_bold),
            Paragraph("<b>Present Days</b>", cell_bold),
            Paragraph("<b>Paid Leaves</b>", cell_bold),
            Paragraph("<b>Loss of Pay (LOP)</b>", cell_bold),
            Paragraph("<b>Payable Days</b>", cell_bold),
        ],
        [
            Paragraph(str(payslip.total_working_days), cell_normal),
            Paragraph(str(payslip.present_days), cell_normal),
            Paragraph(str(payslip.paid_leaves), cell_normal),
            Paragraph(str(payslip.loss_of_pay_days), cell_normal),
            Paragraph(f"<b>{payslip.payable_days}</b>", cell_bold),
        ]
    ]
    att_table = Table(att_data, colWidths=[108, 108, 108, 108, 108])
    att_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8F5E9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#C8E6C9')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E8F5E9')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(att_table)
    elements.append(Spacer(1, 12))

    # 4. Earnings & Deductions Comparison Table
    earn_ded_data = [
        [Paragraph("<b>EARNINGS</b>", cell_bold), Paragraph("<b>AMOUNT (INR)</b>", cell_right_bold),
         Paragraph("<b>DEDUCTIONS</b>", cell_bold), Paragraph("<b>AMOUNT (INR)</b>", cell_right_bold)],
        [Paragraph("Basic Salary", cell_normal), Paragraph(f"₹{payslip.basic_salary:,.2f}", cell_right),
         Paragraph("Provident Fund (PF)", cell_normal), Paragraph(f"₹{payslip.provident_fund:,.2f}", cell_right)],
        [Paragraph("House Rent Allowance (HRA)", cell_normal), Paragraph(f"₹{payslip.hra:,.2f}", cell_right),
         Paragraph("Professional Tax", cell_normal), Paragraph(f"₹{payslip.professional_tax:,.2f}", cell_right)],
        [Paragraph("Conveyance Allowance", cell_normal), Paragraph(f"₹{payslip.conveyance_allowance:,.2f}", cell_right),
         Paragraph("TDS / Income Tax", cell_normal), Paragraph(f"₹{payslip.tds:,.2f}", cell_right)],
        [Paragraph("Medical Allowance", cell_normal), Paragraph(f"₹{payslip.medical_allowance:,.2f}", cell_right),
         Paragraph("Other Deductions", cell_normal), Paragraph(f"₹{payslip.other_deductions:,.2f}", cell_right)],
        [Paragraph("Special Allowance", cell_normal), Paragraph(f"₹{payslip.special_allowance:,.2f}", cell_right),
         Paragraph("-", cell_normal), Paragraph("-", cell_right)],
        [Paragraph("Performance Bonus / Incentives", cell_normal), Paragraph(f"₹{payslip.bonus:,.2f}", cell_right),
         Paragraph("-", cell_normal), Paragraph("-", cell_right)],
        [Paragraph("<b>TOTAL GROSS EARNINGS</b>", cell_bold), Paragraph(f"<b>₹{payslip.gross_earnings:,.2f}</b>", cell_right_bold),
         Paragraph("<b>TOTAL DEDUCTIONS</b>", cell_bold), Paragraph(f"<b>₹{payslip.total_deductions:,.2f}</b>", cell_right_bold)],
    ]

    earn_table = Table(earn_ded_data, colWidths=[170, 100, 170, 100])
    earn_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#E8F5E9')),
        ('BACKGROUND', (2, 0), (3, 0), colors.HexColor('#FEE2E2')),
        ('BACKGROUND', (0, -1), (1, -1), colors.HexColor('#E8F5E9')),
        ('BACKGROUND', (2, -1), (3, -1), colors.HexColor('#FEE2E2')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(earn_table)
    elements.append(Spacer(1, 14))

    # 5. Net Salary Highlight Card
    net_data = [
        [
            Paragraph("<b>NET PAYABLE AMOUNT:</b>", ParagraphStyle('NetLbl', parent=styles['Normal'], fontSize=12, fontName='Helvetica-Bold', textColor=colors.HexColor('#1B5E20'))),
            Paragraph(f"<b>₹{payslip.net_payable:,.2f}</b>", ParagraphStyle('NetVal', parent=styles['Normal'], fontSize=15, fontName='Helvetica-Bold', textColor=colors.HexColor('#1B5E20'), alignment=2))
        ]
    ]
    net_table = Table(net_data, colWidths=[270, 270])
    net_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E8F5E9')),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2E7D32')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(net_table)
    elements.append(Spacer(1, 20))

    # 6. Footer Disclaimer & Signature
    footer_text = Paragraph(
        "<i>Note: This is a system-generated document issued by Company HRMS and does not require a physical signature when verified online. For discrepancies, raise an HR query within 5 business days.</i>",
        subtitle_style
    )
    elements.append(footer_text)

    doc.build(elements)
    buffer.seek(0)
    return buffer

