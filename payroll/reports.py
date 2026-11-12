import csv
import io
from decimal import Decimal
import datetime
from django.http import HttpResponse
from django.utils import timezone
import calendar

# OpenPyXL for Excel (.xlsx) export
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ReportLab for PDF (.pdf) export
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def export_payroll_csv(period, payslips):
    """
    Exports the complete Monthly Payroll Roster to a professional CSV file.
    Includes UTF-8 BOM so Excel opens currency symbols and formatting correctly.
    """
    month_name = period.get_month_display()
    filename = f"Payroll_Report_{month_name}_{period.year}.csv"

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Write UTF-8 Byte Order Mark for Excel compatibility
    response.write('\ufeff')

    writer = csv.writer(response)

    # 1. Company & Period Header Meta
    writer.writerow(["COMPANY HRMS ENTERPRISE - MONTHLY PAYROLL DISBURSEMENT REPORT"])
    writer.writerow([
        "Payroll Cycle:", f"{month_name} {period.year}",
        "Cycle Status:", period.get_status_display(),
        "Working Days in Month:", period.working_days,
        "Total Employees:", len(payslips)
    ])
    writer.writerow([
        "Shift Timings:", f"{period.office_start_time or '09:30'} - {period.office_end_time or '18:30'} ({period.required_daily_hours or 9.0} hrs/day)",
        "Overtime Compensation:", "Active" if period.allow_overtime_compensation else "Strict",
        "Generated Date:", timezone.localtime(timezone.now()).strftime('%d-%b-%Y %I:%M %p')
    ])
    writer.writerow([])

    # 2. Table Column Headers
    headers = [
        "Sl No",
        "Employee ID",
        "Employee Name",
        "Department",
        "Designation",
        "Bank Name",
        "Account Number",
        "Monthly Base Salary (INR)",
        "Per-Day Rate [Base/30] (INR)",
        "Daily Hours",
        "Per-Min Rate (INR)",
        "Working Days",
        "Payable Days",
        "Excess SL (Days)",
        "Excess CL (Days)",
        "Unexcused Absences (Days)",
        "Part A: Leave Deduction (INR)",
        "Late Arrival (Mins)",
        "Overtime (Mins)",
        "Net Shortfall (Mins)",
        "Part B: Shortfall Deduction (INR)",
        "Gross Formula Deduction (A+B) (INR)",
        "Part C: HR Deduction Waiver (INR)",
        "Waiver Reason / Justification",
        "Final Formula Deduction (INR)",
        "HRA (INR)",
        "Conveyance Allowance (INR)",
        "Medical Allowance (INR)",
        "Special Allowance (INR)",
        "Total Gross Earnings (INR)",
        "Provident Fund (INR)",
        "Professional Tax (INR)",
        "TDS Tax (INR)",
        "Total Deductions (INR)",
        "Net Payable Salary (INR)",
        "Disbursement Status"
    ]
    writer.writerow(headers)

    # 3. Employee Data Rows
    tot_base = Decimal('0.00')
    tot_leave_ded = Decimal('0.00')
    tot_shortfall_mins = 0
    tot_shortfall_ded = Decimal('0.00')
    tot_gross_ded = Decimal('0.00')
    tot_waivers = Decimal('0.00')
    tot_final_ded = Decimal('0.00')
    tot_gross = Decimal('0.00')
    tot_pf = Decimal('0.00')
    tot_pt = Decimal('0.00')
    tot_tds = Decimal('0.00')
    tot_deductions = Decimal('0.00')
    tot_net = Decimal('0.00')

    for idx, ps in enumerate(payslips, start=1):
        emp = ps.employee
        base = ps.basic_salary or Decimal('0.00')
        p_day = ps.per_day_rate or Decimal('0.00')
        p_min = ps.per_minute_rate or Decimal('0.0000')
        l_ded = ps.leave_deduction or Decimal('0.00')
        s_ded = ps.shortfall_deduction or Decimal('0.00')
        g_ded = ps.gross_deduction or (l_ded + s_ded)
        waiver = ps.hr_condoned_amount or Decimal('0.00')
        f_ded = ps.final_deduction or max(Decimal('0.00'), g_ded - waiver)
        pf = ps.provident_fund or Decimal('0.00')
        pt = ps.professional_tax or Decimal('0.00')
        tds = ps.tds or Decimal('0.00')
        t_ded = ps.total_deductions or Decimal('0.00')
        gross = ps.gross_earnings or Decimal('0.00')
        net = ps.net_payable or Decimal('0.00')

        tot_base += base
        tot_leave_ded += l_ded
        tot_shortfall_mins += (ps.net_shortfall_minutes or 0)
        tot_shortfall_ded += s_ded
        tot_gross_ded += g_ded
        tot_waivers += waiver
        tot_final_ded += f_ded
        tot_gross += gross
        tot_pf += pf
        tot_pt += pt
        tot_tds += tds
        tot_deductions += t_ded
        tot_net += net

        writer.writerow([
            idx,
            emp.emp_id,
            emp.full_name,
            emp.department.name if emp.department else "General",
            emp.designation.title if emp.designation else "Staff",
            emp.bank_name or "N/A",
            emp.bank_account_number or "N/A",
            f"{base:.2f}",
            f"{p_day:.2f}",
            f"{ps.required_daily_hours or 9.0}",
            f"{p_min:.4f}",
            ps.working_days_count or period.working_days,
            ps.payable_days,
            f"{ps.excess_sl or 0:.1f}",
            f"{ps.excess_cl or 0:.1f}",
            f"{ps.unexcused_absences or 0:.1f}",
            f"{l_ded:.2f}",
            ps.total_late_minutes or 0,
            ps.total_overtime_minutes or 0,
            ps.net_shortfall_minutes or 0,
            f"{s_ded:.2f}",
            f"{g_ded:.2f}",
            f"{waiver:.2f}",
            ps.condone_reason or "-",
            f"{f_ded:.2f}",
            f"{ps.hra or 0:.2f}",
            f"{ps.conveyance_allowance or 0:.2f}",
            f"{ps.medical_allowance or 0:.2f}",
            f"{ps.special_allowance or 0:.2f}",
            f"{gross:.2f}",
            f"{pf:.2f}",
            f"{pt:.2f}",
            f"{tds:.2f}",
            f"{t_ded:.2f}",
            f"{net:.2f}",
            ps.get_status_display()
        ])

    # 4. Total Summary Row
    writer.writerow([])
    writer.writerow([
        "TOTAL / SUMMARY",
        "",
        f"Total Employees: {len(payslips)}",
        "",
        "",
        "",
        "",
        f"{tot_base:.2f}",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        f"{tot_leave_ded:.2f}",
        "",
        "",
        tot_shortfall_mins,
        f"{tot_shortfall_ded:.2f}",
        f"{tot_gross_ded:.2f}",
        f"{tot_waivers:.2f}",
        "",
        f"{tot_final_ded:.2f}",
        "",
        "",
        "",
        "",
        f"{tot_gross:.2f}",
        f"{tot_pf:.2f}",
        f"{tot_pt:.2f}",
        f"{tot_tds:.2f}",
        f"{tot_deductions:.2f}",
        f"{tot_net:.2f}",
        ""
    ])

    return response


def export_payroll_excel(period, payslips):
    """
    Exports the complete Monthly Payroll Roster to a formatted Microsoft Excel workbook (.xlsx).
    Features executive styling, color-coded formula sections, accounting number formats,
    and auto-fitted column widths using openpyxl.
    """
    month_name = period.get_month_display()
    filename = f"Payroll_Report_{month_name}_{period.year}.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"{month_name[:3]} {period.year} Payroll"

    # Define color fills & font styles
    navy_header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    dark_slate_fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
    accent_emerald_fill = PatternFill(start_color="ECFDF5", end_color="ECFDF5", fill_type="solid")
    accent_rose_fill = PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid")
    accent_amber_fill = PatternFill(start_color="FFFBEB", end_color="FFFBEB", fill_type="solid")
    accent_indigo_fill = PatternFill(start_color="EEF2FF", end_color="EEF2FF", fill_type="solid")
    totals_row_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

    font_title = Font(name="Calibri", size=15, bold=True, color="FFFFFF")
    font_sub = Font(name="Calibri", size=10, bold=False, color="64748B")
    font_kpi_val = Font(name="Calibri", size=13, bold=True, color="0F172A")
    font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_data = Font(name="Calibri", size=10, bold=False, color="0F172A")
    font_data_bold = Font(name="Calibri", size=10, bold=True, color="0F172A")
    font_total = Font(name="Calibri", size=11, bold=True, color="0F172A")
    font_net_payable = Font(name="Calibri", size=10, bold=True, color="047857")

    thin_border_side = Side(border_style="thin", color="CBD5E1")
    cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    double_bottom_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=Side(border_style="double", color="0F172A"))

    # 1. Company Banner (Row 1-2)
    ws.merge_cells("A1:Q1")
    title_cell = ws["A1"]
    title_cell.value = "COMPANY HRMS ENTERPRISE - MONTHLY PAYROLL DISBURSEMENT REPORT"
    title_cell.font = font_title
    title_cell.fill = navy_header_fill
    title_cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 34

    # Meta banner row 2
    ws.merge_cells("A2:Q2")
    sub_cell = ws["A2"]
    sub_cell.value = (
        f"Payroll Cycle: {month_name} {period.year}   |   Status: {period.get_status_display()}   |   "
        f"Working Days: {period.working_days}   |   Employees: {len(payslips)}   |   "
        f"Generated: {timezone.localtime(timezone.now()).strftime('%d-%b-%Y %I:%M %p')}"
    )
    sub_cell.font = Font(name="Calibri", size=10, color="CBD5E1", italic=True)
    sub_cell.fill = navy_header_fill
    sub_cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[2].height = 20

    # 2. Executive KPI Cards (Row 4)
    ws.row_dimensions[4].height = 36
    ws["B4"] = "NET OUTFLOW"
    ws["B4"].font = font_sub
    ws["C4"] = f"₹{period.total_net:,.2f}"
    ws["C4"].font = font_kpi_val
    ws["C4"].fill = accent_emerald_fill

    ws["E4"] = "PART A: LEAVE DED"
    ws["E4"].font = font_sub
    ws["F4"] = f"₹{period.total_leave_deductions or 0:,.2f}"
    ws["F4"].font = font_kpi_val
    ws["F4"].fill = accent_rose_fill

    ws["H4"] = "PART B: SHORTFALL"
    ws["H4"].font = font_sub
    ws["I4"] = f"₹{period.total_shortfall_deductions or 0:,.2f}"
    ws["I4"].font = font_kpi_val
    ws["I4"].fill = accent_amber_fill

    ws["K4"] = "PART C: HR WAIVERS"
    ws["K4"].font = font_sub
    ws["L4"] = f"₹{period.total_condoned_amount or 0:,.2f}"
    ws["L4"].font = font_kpi_val
    ws["L4"].fill = accent_indigo_fill

    # 3. Main Table Headers (Row 6)
    headers = [
        "Sl", "Emp ID", "Employee Name", "Department", "Designation",
        "Base Salary", "Per-Day Rate", "Daily Hours", "Per-Min Rate",
        "Working Days", "Payable Days",
        "Part A: Leave Ded", "Shortfall Mins", "Part B: Shortfall Ded",
        "Gross Formula Ded", "Part C: HR Waiver", "Final Formula Ded",
        "Total Allowances", "Total Gross",
        "PF", "PT", "TDS", "Total Deductions", "Net Payable", "Status"
    ]
    header_row_num = 6
    ws.row_dimensions[header_row_num].height = 28

    for col_idx, header_text in enumerate(headers, start=1):
        cell = ws.cell(row=header_row_num, column=col_idx, value=header_text)
        cell.font = font_header
        cell.fill = dark_slate_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = cell_border

    # 4. Data Rows (Starting at row 7)
    current_row = 7
    currency_fmt = "₹#,##0.00"

    tot_base = Decimal('0.00')
    tot_leave_ded = Decimal('0.00')
    tot_shortfall_mins = 0
    tot_shortfall_ded = Decimal('0.00')
    tot_gross_ded = Decimal('0.00')
    tot_waivers = Decimal('0.00')
    tot_final_ded = Decimal('0.00')
    tot_allowances = Decimal('0.00')
    tot_gross = Decimal('0.00')
    tot_pf = Decimal('0.00')
    tot_pt = Decimal('0.00')
    tot_tds = Decimal('0.00')
    tot_all_ded = Decimal('0.00')
    tot_net = Decimal('0.00')

    for idx, ps in enumerate(payslips, start=1):
        emp = ps.employee
        base = float(ps.basic_salary or Decimal('0.00'))
        p_day = float(ps.per_day_rate or Decimal('0.00'))
        p_min = float(ps.per_minute_rate or Decimal('0.0000'))
        l_ded = float(ps.leave_deduction or Decimal('0.00'))
        s_mins = int(ps.net_shortfall_minutes or 0)
        s_ded = float(ps.shortfall_deduction or Decimal('0.00'))
        g_ded = float(ps.gross_deduction or Decimal(l_ded + s_ded))
        waiver = float(ps.hr_condoned_amount or Decimal('0.00'))
        f_ded = float(ps.final_deduction or Decimal(max(0, g_ded - waiver)))
        allowances = float((ps.hra or Decimal(0)) + (ps.conveyance_allowance or Decimal(0)) + (ps.medical_allowance or Decimal(0)) + (ps.special_allowance or Decimal(0)))
        gross = float(ps.gross_earnings or Decimal(0))
        pf = float(ps.provident_fund or Decimal(0))
        pt = float(ps.professional_tax or Decimal(0))
        tds = float(ps.tds or Decimal(0))
        t_ded = float(ps.total_deductions or Decimal(0))
        net = float(ps.net_payable or Decimal(0))

        tot_base += Decimal(str(base))
        tot_leave_ded += Decimal(str(l_ded))
        tot_shortfall_mins += s_mins
        tot_shortfall_ded += Decimal(str(s_ded))
        tot_gross_ded += Decimal(str(g_ded))
        tot_waivers += Decimal(str(waiver))
        tot_final_ded += Decimal(str(f_ded))
        tot_allowances += Decimal(str(allowances))
        tot_gross += Decimal(str(gross))
        tot_pf += Decimal(str(pf))
        tot_pt += Decimal(str(pt))
        tot_tds += Decimal(str(tds))
        tot_all_ded += Decimal(str(t_ded))
        tot_net += Decimal(str(net))

        row_vals = [
            idx,
            emp.emp_id,
            emp.full_name,
            emp.department.name if emp.department else "General",
            emp.designation.title if emp.designation else "Staff",
            base,
            p_day,
            float(ps.required_daily_hours or 9.0),
            p_min,
            ps.working_days_count or period.working_days,
            float(ps.payable_days or 0),
            l_ded,
            s_mins,
            s_ded,
            g_ded,
            waiver,
            f_ded,
            allowances,
            gross,
            pf,
            pt,
            tds,
            t_ded,
            net,
            ps.get_status_display()
        ]

        ws.row_dimensions[current_row].height = 20
        for col_idx, val in enumerate(row_vals, start=1):
            cell = ws.cell(row=current_row, column=col_idx, value=val)
            cell.font = font_data
            cell.border = cell_border

            # Number formatting
            if col_idx in [6, 7, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]:
                cell.number_format = currency_fmt
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif col_idx == 9:
                cell.number_format = "₹#,##0.0000"
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif col_idx in [1, 2, 8, 10, 11, 13, 25]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

            # Color highlight for key formula columns
            if col_idx == 12 and l_ded > 0:
                cell.fill = accent_rose_fill
            elif col_idx == 14 and s_ded > 0:
                cell.fill = accent_amber_fill
            elif col_idx == 16 and waiver > 0:
                cell.fill = accent_indigo_fill
            elif col_idx == 24: # Net Payable
                cell.fill = accent_emerald_fill
                cell.font = font_net_payable

        current_row += 1

    # 5. Grand Totals Row
    ws.row_dimensions[current_row].height = 24
    totals_map = {
        1: "GRAND TOTAL",
        6: float(tot_base),
        12: float(tot_leave_ded),
        13: tot_shortfall_mins,
        14: float(tot_shortfall_ded),
        15: float(tot_gross_ded),
        16: float(tot_waivers),
        17: float(tot_final_ded),
        18: float(tot_allowances),
        19: float(tot_gross),
        20: float(tot_pf),
        21: float(tot_pt),
        22: float(tot_tds),
        23: float(tot_all_ded),
        24: float(tot_net),
    }

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=current_row, column=col_idx)
        val = totals_map.get(col_idx, "")
        cell.value = val
        cell.font = font_total
        cell.fill = totals_row_fill
        cell.border = double_bottom_border

        if col_idx in [6, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]:
            cell.number_format = currency_fmt
            cell.alignment = Alignment(horizontal="right", vertical="center")
        elif col_idx == 1:
            cell.alignment = Alignment(horizontal="center", vertical="center")

    # 6. Auto-fit column widths
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        # Check rows from 6 downwards (skipping title banners)
        for cell in col[5:]:
            val_str = str(cell.value or '')
            if cell.number_format == currency_fmt:
                val_str = f"₹{val_str}.00"
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 11)

    # First few columns specific spacing
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 24
    ws.column_dimensions["D"].width = 18
    ws.column_dimensions["E"].width = 20

    # Save to memory buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def export_payroll_pdf(period, payslips):
    """
    Exports an executive Monthly Payroll Disbursement Report as a PDF in Landscape orientation.
    Features corporate styling, executive KPI summary table, Unified Master Formula roster,
    and formal administrative sign-off blocks using ReportLab.
    """
    month_name = period.get_month_display()
    filename = f"Payroll_Report_{month_name}_{period.year}.pdf"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=24,
        leftMargin=24,
        topMargin=24,
        bottomMargin=24
    )

    elements = []
    styles = getSampleStyleSheet()

    # Typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#475569')
    )
    cell_bold = ParagraphStyle('CB', parent=styles['Normal'], fontSize=7.5, fontName='Helvetica-Bold', textColor=colors.HexColor('#0F172A'))
    cell_norm = ParagraphStyle('CN', parent=styles['Normal'], fontSize=7.5, fontName='Helvetica', textColor=colors.HexColor('#1E293B'))
    cell_right = ParagraphStyle('CR', parent=styles['Normal'], fontSize=7.5, fontName='Helvetica', alignment=2, textColor=colors.HexColor('#1E293B'))
    cell_right_bold = ParagraphStyle('CRB', parent=styles['Normal'], fontSize=7.5, fontName='Helvetica-Bold', alignment=2, textColor=colors.HexColor('#0F172A'))
    cell_net = ParagraphStyle('CNet', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', alignment=2, textColor=colors.HexColor('#047857'))

    # 1. Header Banner
    header_data = [
        [
            Paragraph("<b>COMPANY HRMS ENTERPRISE</b><br/><font size=9 color='#047857'><b>MONTHLY PAYROLL EXECUTIVE DISBURSEMENT REPORT</b></font>", title_style),
            Paragraph(
                f"<b>Payroll Cycle:</b> {month_name.upper()} {period.year}<br/>"
                f"<b>Status:</b> {period.get_status_display()}<br/>"
                f"<b>Generated:</b> {timezone.localtime(timezone.now()).strftime('%d-%b-%Y %I:%M %p')}",
                subtitle_style
            )
        ]
    ]
    header_table = Table(header_data, colWidths=[520, 224])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#047857'), spaceAfter=8))

    # 2. Executive KPI Summary Strip
    kpi_data = [
        [
            Paragraph("<b>Total Net Payout</b>", cell_bold),
            Paragraph("<b>Gross Earnings</b>", cell_bold),
            Paragraph("<b>Part A: Leave Ded</b>", cell_bold),
            Paragraph("<b>Part B: Shortfall Ded</b>", cell_bold),
            Paragraph("<b>Part C: HR Waivers</b>", cell_bold),
            Paragraph("<b>Total Deductions</b>", cell_bold),
            Paragraph("<b>Total Employees</b>", cell_bold),
        ],
        [
            Paragraph(f"<font color='#047857'><b>₹{period.total_net:,.2f}</b></font>", cell_bold),
            Paragraph(f"₹{period.total_gross:,.2f}", cell_norm),
            Paragraph(f"<font color='#DC2626'>₹{period.total_leave_deductions or 0:,.2f}</font>", cell_norm),
            Paragraph(f"<font color='#D97706'>₹{period.total_shortfall_deductions or 0:,.2f}</font>", cell_norm),
            Paragraph(f"<font color='#4F46E5'>-₹{period.total_condoned_amount or 0:,.2f}</font>", cell_norm),
            Paragraph(f"₹{period.total_deductions:,.2f}", cell_norm),
            Paragraph(f"<b>{len(payslips)} active</b>", cell_bold),
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[110, 105, 105, 105, 105, 105, 109])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#ECFDF5')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 10))

    # 3. Master Roster Table
    roster_headers = [
        Paragraph("<b>#</b>", cell_bold),
        Paragraph("<b>Emp ID</b>", cell_bold),
        Paragraph("<b>Employee Name</b>", cell_bold),
        Paragraph("<b>Department</b>", cell_bold),
        Paragraph("<b>Days</b>", cell_bold),
        Paragraph("<b>Base Salary</b>", cell_right_bold),
        Paragraph("<b>Leave Ded (A)</b>", cell_right_bold),
        Paragraph("<b>Shortfall (B)</b>", cell_right_bold),
        Paragraph("<b>Gross Ded</b>", cell_right_bold),
        Paragraph("<b>HR Waiver (C)</b>", cell_right_bold),
        Paragraph("<b>Total Ded</b>", cell_right_bold),
        Paragraph("<b>Net Payable</b>", cell_right_bold),
        Paragraph("<b>Status</b>", cell_bold),
    ]

    roster_rows = [roster_headers]

    tot_base = Decimal('0.00')
    tot_leave = Decimal('0.00')
    tot_shortfall = Decimal('0.00')
    tot_gross_ded = Decimal('0.00')
    tot_waiver = Decimal('0.00')
    tot_all_ded = Decimal('0.00')
    tot_net = Decimal('0.00')

    for idx, ps in enumerate(payslips, start=1):
        emp = ps.employee
        base = ps.basic_salary or Decimal('0.00')
        l_ded = ps.leave_deduction or Decimal('0.00')
        s_ded = ps.shortfall_deduction or Decimal('0.00')
        g_ded = ps.gross_deduction or (l_ded + s_ded)
        waiver = ps.hr_condoned_amount or Decimal('0.00')
        t_ded = ps.total_deductions or Decimal('0.00')
        net = ps.net_payable or Decimal('0.00')

        tot_base += base
        tot_leave += l_ded
        tot_shortfall += s_ded
        tot_gross_ded += g_ded
        tot_waiver += waiver
        tot_all_ded += t_ded
        tot_net += net

        roster_rows.append([
            Paragraph(str(idx), cell_norm),
            Paragraph(emp.emp_id, cell_bold),
            Paragraph(emp.full_name[:20], cell_norm),
            Paragraph(emp.department.code if emp.department else "-", cell_norm),
            Paragraph(f"{ps.payable_days}/{ps.working_days_count or period.working_days}", cell_norm),
            Paragraph(f"₹{base:,.0f}", cell_right),
            Paragraph(f"₹{l_ded:,.0f}", cell_right),
            Paragraph(f"₹{s_ded:,.0f}", cell_right),
            Paragraph(f"₹{g_ded:,.0f}", cell_right),
            Paragraph(f"-₹{waiver:,.0f}" if waiver > 0 else "-", cell_right),
            Paragraph(f"₹{t_ded:,.0f}", cell_right),
            Paragraph(f"₹{net:,.2f}", cell_net),
            Paragraph(ps.get_status_display()[:8], cell_norm)
        ])

    # Grand Total row
    roster_rows.append([
        Paragraph("<b>TOTAL</b>", cell_bold),
        Paragraph("", cell_bold),
        Paragraph(f"<b>{len(payslips)} Staff</b>", cell_bold),
        Paragraph("", cell_bold),
        Paragraph("", cell_bold),
        Paragraph(f"<b>₹{tot_base:,.0f}</b>", cell_right_bold),
        Paragraph(f"<b>₹{tot_leave:,.0f}</b>", cell_right_bold),
        Paragraph(f"<b>₹{tot_shortfall:,.0f}</b>", cell_right_bold),
        Paragraph(f"<b>₹{tot_gross_ded:,.0f}</b>", cell_right_bold),
        Paragraph(f"<b>-₹{tot_waiver:,.0f}</b>", cell_right_bold),
        Paragraph(f"<b>₹{tot_all_ded:,.0f}</b>", cell_right_bold),
        Paragraph(f"<b>₹{tot_net:,.2f}</b>", cell_net),
        Paragraph("", cell_bold)
    ])

    col_widths = [24, 52, 105, 50, 48, 68, 62, 60, 60, 60, 62, 75, 48]
    roster_table = Table(roster_rows, colWidths=col_widths)
    roster_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E2E8F0')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#F1F5F9')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ALIGN', (0, 0), (4, -1), 'CENTER'),
        ('ALIGN', (12, 0), (12, -1), 'CENTER'),
    ]))
    elements.append(roster_table)
    elements.append(Spacer(1, 14))

    # 4. Executive Sign-Off & Audit Block
    sign_data = [
        [
            Paragraph(
                f"<b>Processed By:</b><br/>"
                f"{period.processed_by.get_full_name() or period.processed_by.username}<br/>"
                f"<font size=7 color='#64748B'>HR Administration</font>",
                subtitle_style
            ),
            Paragraph(
                f"<b>Authorized & Approved By:</b><br/>"
                f"{period.approved_by.get_full_name() if period.approved_by else 'Awaiting Head Authorization'}<br/>"
                f"<font size=7 color='#64748B'>{period.approved_at.strftime('%d-%b-%Y') if period.approved_at else 'Sign-off Pending'}</font>",
                subtitle_style
            ),
            Paragraph(
                "<b>Corporate Finance Disclaimer:</b><br/>"
                "System-generated confidential payroll document verified by Unified Master Formula. Complies with statutory Provident Fund & Tax regulations.",
                subtitle_style
            )
        ]
    ]
    sign_table = Table(sign_data, colWidths=[240, 240, 264])
    sign_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(sign_table)

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

