from models import db, Grant, Milestone, ExpenseClaim, Task, User, GrantTeam, DeliverableSubmission, BudgetCategory, Deliverable, Asset, GrantKPI
from datetime import datetime
import os
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch

class ReportService:
    @staticmethod
    def get_reporting_options(grant_id):
        """
        Logic to determine valid reporting periods based on grant dates.
        """
        grant = Grant.query.get(grant_id)
        if not grant:
            return []

        options = []
        today = datetime.now().date()
        
        # 1. Annual Reports
        start_year = grant.start_date.year
        end_year = grant.end_date.year
        for year in range(start_year, end_year + 1):
            if year <= today.year:
                options.append({
                    "id": f"annual_{year}",
                    "label": f"Annual Report – {year}",
                    "type": "Annual",
                    "value": str(year)
                })

        # 2. Interim / Quarterly Reports
        # Calculate quarters from start date to now
        curr_year = grant.start_date.year
        curr_month = grant.start_date.month
        
        while curr_year < today.year or (curr_year == today.year and curr_month <= today.month):
            # Determine quarter
            q = (curr_month - 1) // 3 + 1
            options.append({
                "id": f"interim_q{q}_{curr_year}",
                "label": f"Interim Report – Q{q} {curr_year}",
                "type": "Interim",
                "value": f"Q{q} {curr_year}"
            })
            
            # Advance to next quarter
            curr_month += 3
            if curr_month > 12:
                curr_month = 1
                curr_year += 1

        # 3. Final Report only if past end date
        if today >= grant.end_date:
            options.append({
                "id": "final",
                "label": "Final Project Report",
                "type": "Final",
                "value": "final"
            })
        
        # Deduplicate and sort (reverse chronological)
        unique_options = []
        seen_ids = set()
        for opt in reversed(options):
            if opt['id'] not in seen_ids:
                unique_options.append(opt)
                seen_ids.add(opt['id'])
        
        return unique_options

    @staticmethod
    def compile_report_data(grant_id, report_type, report_value):
        grant = Grant.query.get(grant_id)
        if not grant:
            raise ValueError("Grant not found")

        # Filtering logic
        milestones = Milestone.query.filter_by(grant_id=grant_id).all()
        expenses = ExpenseClaim.query.filter_by(grant_id=grant_id, status='approved').all()
        
        # If Annual, filter by year
        if report_type == "Annual":
            year = int(report_value)
            milestones = [m for m in milestones if m.due_date.year == year]
            expenses = [e for e in expenses if e.expense_date.year == year]
        
        # If Interim (e.g. Q1 2026), filter by quarter
        elif report_type == "Interim":
            # report_value format: "Q1 2026"
            parts = report_value.split(" ")
            q = int(parts[0][1])
            year = int(parts[1])
            start_month = (q - 1) * 3 + 1
            end_month = start_month + 2
            
            def in_quarter(dt):
                return dt.year == year and start_month <= dt.month <= end_month
            
            milestones = [m for m in milestones if in_quarter(m.due_date)]
            expenses = [e for e in expenses if in_quarter(e.expense_date)]

        # Effort / Team Data
        team_entries = GrantTeam.query.filter_by(grant_id=grant_id).all()
        effort_data = []
        for entry in team_entries:
            submissions = db.session.query(DeliverableSubmission).join(Task).filter(
                Task.grant_id == grant_id,
                Task.assigned_to == entry.user_id,
                DeliverableSubmission.verification_status == 'verified'
            ).all()
            
            # Submissions filtering based on period
            if report_type == "Annual":
                year = int(report_value)
                submissions = [s for s in submissions if s.submitted_at.year == year]
            elif report_type == "Interim":
                parts = report_value.split(" ")
                q = int(parts[0][1])
                year = int(parts[1])
                start_month = (q - 1) * 3 + 1
                end_month = start_month + 2
                submissions = [s for s in submissions if s.submitted_at.year == year and start_month <= s.submitted_at.month <= end_month]
            
            total_hours = sum(s.hours_worked for s in submissions)
            effort_data.append({
                "name": entry.user.name,
                "role": entry.role,
                "hours": total_hours,
                "rate": entry.user.pay_rate or 0,
                "total_pay": total_hours * (entry.user.pay_rate or 0)
            })

        formatted_milestones = []
        for m in milestones:
            item = m.to_dict()
            # If deliverable_filename attribute exists (it might have been added in a patch)
            if hasattr(m, 'deliverable_filename') and m.deliverable_filename:
                item['deliverable_url'] = f"http://localhost:5000/uploads/deliverables/{m.deliverable_filename}"
            else:
                item['deliverable_url'] = "N/A"
            formatted_milestones.append(item)

        # Calculate Indirect Costs for report data
        fa_rate = grant.indirect_cost_rate or 0
        total_spent = sum(e.amount or 0 for e in expenses)
        fa_amount = total_spent * (fa_rate / 100)

        # Deliverables for Annex
        deliverables = Deliverable.query.filter_by(grant_id=grant_id).all()
        # Filter by period if needed
        if report_type == "Annual":
            year = int(report_value)
            deliverables = [d for d in deliverables if d.created_at.year == year]
        elif report_type == "Interim":
            parts = report_value.split(" ")
            q = int(parts[0][1])
            year = int(parts[1])
            start_month = (q - 1) * 3 + 1
            end_month = start_month + 2
            deliverables = [d for d in deliverables if d.created_at.year == year and start_month <= d.created_at.month <= end_month]

        return {
            "grant": grant.to_dict(include_categories=True),
            "milestones": formatted_milestones,
            "expenses": [e.to_dict() for e in expenses],
            "effort": effort_data,
            "deliverables": [d.to_dict() for d in deliverables],
            "indirect_costs": {
                "rate": fa_rate,
                "amount": fa_amount
            },
            "report_info": {
                "type": report_type,
                "period": report_value,
                "generated_at": datetime.now().strftime("%d %b %Y, %H:%M:%S")
            }
        }

    @staticmethod
    def generate_pdf_report(data, filename):
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        styles = getSampleStyleSheet()
        elements = []

        # Styles
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=24, spaceAfter=20)
        header_style = ParagraphStyle('HeaderStyle', parent=styles['Heading2'], fontSize=16, spaceBefore=15, spaceAfter=10, color=colors.Color(0.11764705882352941, 0.25098039215686274, 0.6862745098039215))  # #1e40af
        small_style = ParagraphStyle('SmallStyle', parent=styles['Normal'], fontSize=8, color=colors.grey)
        
        # 1. Cover Page
        elements.append(Paragraph(f"{data['report_info']['type']} Progress Report", title_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        cover_data = [
            ["Grant Workspace:", data['grant']['title']],
            ["Funder:", data['grant']['funder']],
            ["Reference Number:", data['grant']['grant_code']],
            ["Reporting Period:", data['report_info']['period']],
            ["Principal Investigator:", data['grant']['pi']['name']],
            ["Generation Timestamp:", data['report_info']['generated_at']]
        ]
        ct = Table(cover_data, colWidths=[1.8*inch, 4*inch])
        ct.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(ct)
        elements.append(Spacer(1, 0.5 * inch))

        # Section 1: Milestone Progress
        elements.append(Paragraph("Section 1: Milestone Progress", header_style))
        if not data['milestones']:
            elements.append(Paragraph("No milestones recorded for this period.", styles['Normal']))
        else:
            milestone_rows = [["Milestone", "Status", "Completion", "Deliverable Link"]]
            for m in data['milestones']:
                status_icon = "✅ Completed" if m['status'] == 'completed' else "⏳ In Progress"
                milestone_rows.append([
                    m['title'],
                    status_icon,
                    m['completion_date'] or "N/A",
                    m['deliverable_url'] if m['deliverable_url'] != "N/A" else "None"
                ])
            mt = Table(milestone_rows, colWidths=[2.2*inch, 1.2*inch, 1.2*inch, 1.8*inch])
            mt.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.Color(0.9529411764705882, 0.9568627450980393, 0.9607843137254902)),  # #f3f4f6
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            elements.append(mt)
        
        # Section 2: Financial Summary
        elements.append(Paragraph("Section 2: Financial Summary", header_style))
        
        # Budget Analysis Table
        elements.append(Paragraph("Budget vs. Spent Analysis", styles['Heading4']))
        budget_rows = [["Category", "Allocated (USD)", "Spent (USD)", "Spent (MWK)", "Burn %"]]
        total_usd_alloc = 0
        total_usd_spent = 0
        x_rate = data['grant']['exchange_rate'] or 1  # Default to 1 if None
        
        for cat in data['grant']['categories']:
            alloc = cat['allocated'] or 0
            spent = cat['spent'] or 0
            burn = round((spent/alloc)*100) if alloc and alloc > 0 else 0
            budget_rows.append([
                cat['name'],
                f"${alloc:,.0f}",
                f"${spent:,.0f}",
                f"K{spent * x_rate:,.0f}",
                f"{burn}%"
            ])
            total_usd_alloc += alloc
            total_usd_spent += spent
            
        # Calculate Indirect Costs (F&A)
        fa_rate = data['grant'].get('indirect_cost_rate', 0)
        fa_amount = total_usd_spent * (fa_rate / 100)
        
        budget_rows.append([
            f"Indirect Costs (F&A @ {fa_rate}%)",
            "N/A",
            f"${fa_amount:,.0f}",
            f"K{fa_amount * x_rate:,.0f}",
            "N/A"
        ])

        total_burn = round(((total_usd_spent + fa_amount) / total_usd_alloc) * 100) if total_usd_alloc > 0 else 0
        budget_rows.append([
            "GRAND TOTAL (Direct + F&A)",
            f"${total_usd_alloc:,.0f}",
            f"${total_usd_spent + fa_amount:,.0f}",
            f"K{(total_usd_spent + fa_amount) * x_rate:,.0f}",
            f"{total_burn}%"
        ])
        
        bt = Table(budget_rows, colWidths=[1.8*inch, 1.1*inch, 1.1*inch, 1.4*inch, 0.8*inch])
        bt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.Color(0.9529411764705882, 0.9568627450980393, 0.9607843137254902)),  # #f3f4f6
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ]))
        elements.append(bt)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Approved Expenses
        elements.append(Paragraph("Approved Expenses in Period", styles['Heading4']))
        if not data['expenses']:
            elements.append(Paragraph("No approved expenses in this period.", styles['Normal']))
        else:
            exp_rows = [["Date", "Description", "Category", "Amount (USD)"]]
            for e in data['expenses']:
                exp_rows.append([
                    e['expense_date'],
                    e['description'][:40] + ("..." if len(e['description']) > 40 else ""),
                    e['category'],
                    f"${e['amount']:,.2f}"
                ])
            et = Table(exp_rows, colWidths=[1*inch, 2.5*inch, 1.5*inch, 1.2*inch])
            et.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.Color(0.9529411764705882, 0.9568627450980393, 0.9607843137254902)),  # #f3f4f6
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 8),
            ]))
            elements.append(et)

        # Section 3: Effort Certification
        elements.append(Paragraph("Section 3: Effort Certification", header_style))
        if not data['effort']:
            elements.append(Paragraph("No verified effort recorded in this period.", styles['Normal']))
        else:
            eff_rows = [["Team Member", "Role", "Hours", "Total USD"]]
            for ef in data['effort']:
                eff_rows.append([ef['name'], ef['role'], ef['hours'], f"${ef['total_pay']:,.2f}"])
            eft = Table(eff_rows, colWidths=[2.2*inch, 1.8*inch, 1*inch, 1.2*inch])
            eft.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.Color(0.9529411764705882, 0.9568627450980393, 0.9607843137254902)),  # #f3f4f6
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 9),
            ]))
            elements.append(eft)
        
        elements.append(Spacer(1, 0.2 * inch))
        cert_text = f"<b>Statement of Project Certification:</b> All effort, expenses, and deliverables summarized above have been verified as accurate and directly related to the project objectives. This report is certified by the Principal Investigator on {datetime.now().strftime('%d %b %Y')}."
        elements.append(Paragraph(cert_text, styles['Normal']))

        # Appendix A: Deliverables Annex
        elements.append(Paragraph("Appendix A: Deliverables Annex", header_style))
        if not data.get('deliverables'):
            elements.append(Paragraph("No specific deliverables recorded for this period.", styles['Normal']))
        else:
            del_rows = [["Deliverable Title", "Type", "Status", "Reference / Link"]]
            for d in data['deliverables']:
                del_rows.append([
                    d['title'],
                    d['deliverable_type'],
                    d['status'],
                    d['external_url'] or d['file_path'] or "N/A"
                ])
            dt = Table(del_rows, colWidths=[2.2*inch, 1.0*inch, 1.0*inch, 2.0*inch])
            dt.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.Color(0.9529411764705882, 0.9568627450980393, 0.9607843137254902)),  # #f3f4f6
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 8),
            ]))
            elements.append(dt)

        # Footer
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph("<hr/>", styles['Normal']))
        elements.append(Paragraph("<i>This report contains only system-verified data. No manual edits were made.</i>", small_style))
        elements.append(Paragraph(f"PAGMS v1.0 | MUBAS Research Support Unit | System Timestamp: {data['report_info']['generated_at']}", small_style))

        doc.build(elements)
        return filename

    @staticmethod
    def generate_closeout_dossier_pdf(grant_id, filename):
        """
        Generates a formal, immutable Grant Closeout Dossier PDF.
        """
        from services.closeout_service import generate_final_report
        data = generate_final_report(grant_id)
        if not data:
            return None

        grant = Grant.query.get(grant_id)
        
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        styles = getSampleStyleSheet()
        elements = []

        # Custom Styles
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=28, spaceAfter=8, alignment=1, color=colors.Color(0.12, 0.16, 0.23)) # #1e293b
        subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontSize=11, spaceAfter=24, alignment=1, color=colors.Color(0.4, 0.45, 0.5), leading=14)
        header_style = ParagraphStyle('HeaderStyle', parent=styles['Heading2'], fontSize=15, spaceBefore=20, spaceAfter=12, color=colors.Color(0.15, 0.39, 0.92), fontName='Helvetica-Bold') # #2563eb
        label_style = ParagraphStyle('LabelStyle', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', color=colors.Color(0.2, 0.2, 0.2))
        value_style = ParagraphStyle('ValueStyle', parent=styles['Normal'], fontSize=10, color=colors.Color(0.1, 0.1, 0.1))
        small_style = ParagraphStyle('SmallStyle', parent=styles['Normal'], fontSize=8, color=colors.grey)

        # 1. Header Area
        elements.append(Paragraph("GRANT CLOSEOUT DOSSIER", title_style))
        elements.append(Paragraph(f"Official Project Termination & Archival Record", subtitle_style))
        elements.append(Spacer(1, 0.1 * inch))

        # 2. Project Identity
        elements.append(Paragraph("I. Project Identity & Archival Metadata", header_style))
        id_data = [
            [Paragraph("Grant Title", label_style), Paragraph(data['title'], value_style)],
            [Paragraph("Reference Code", label_style), Paragraph(data['grant_code'], value_style)],
            [Paragraph("Funding Agency", label_style), Paragraph(data['funder'], value_style)],
            [Paragraph("Principal Investigator", label_style), Paragraph(grant.pi.name if grant.pi else "N/A", value_style)],
            [Paragraph("Termination Date", label_style), Paragraph(data['end_date'] or "N/A", value_style)],
            [Paragraph("Archival Timestamp", label_style), Paragraph(grant.archived_at.strftime("%Y-%m-%d %H:%M:%S UTC") if grant.archived_at else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"), value_style)]
        ]
        idt = Table(id_data, colWidths=[2.2*inch, 3.8*inch])
        idt.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.Color(0.9, 0.9, 0.9)),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ]))
        elements.append(idt)
        elements.append(Spacer(1, 0.4 * inch))

        # 3. Final Financial Summary
        elements.append(Paragraph("I. Final Financial Reconciliation", header_style))
        fin = data['financial_summary']
        fin_summary = [
            ["Total Approved Allocation:", f"${fin['total_approved']:,.2f}"],
            ["Total Cumulative Spend:", f"${fin['total_spent']:,.2f}"],
            ["Overall Utilization Rate:", f"{fin['overall_utilization']}%"]
        ]
        fst = Table(fin_summary, colWidths=[2.5*inch, 3.5*inch])
        fst.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(fst)
        elements.append(Spacer(1, 0.1 * inch))

        cat_rows = [["Budget Category", "Approved", "Actual Spend", "Utilization"]]
        for cat in fin['categories']:
            cat_rows.append([
                cat['category'],
                f"${cat['approved_amount']:,.0f}",
                f"${cat['actual_spend']:,.0f}",
                f"{cat['utilized_percent']}%"
            ])
        ct = Table(cat_rows, colWidths=[2.2*inch, 1.2*inch, 1.2*inch, 1.4*inch])
        ct.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.Color(0.9, 0.9, 0.95)),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ]))
        elements.append(ct)
        elements.append(Spacer(1, 0.3 * inch))

        # 4. Asset Disposition Log
        elements.append(Paragraph("II. Asset Accountability & Disposition", header_style))
        if not data['asset_disposition_log']:
            elements.append(Paragraph("No physical assets were registered for this project.", styles['Normal']))
        else:
            asset_rows = [["Asset Tag", "Description", "Final Status", "Date"]]
            for a in data['asset_disposition_log']:
                asset_rows.append([a['asset_tag'], a['name'], a['final_status'], a['disposition_date'] or "---"])
            at = Table(asset_rows, colWidths=[1.1*inch, 2.5*inch, 1.2*inch, 1.2*inch])
            at.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.Color(0.9, 0.95, 0.9)),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 8),
            ]))
            elements.append(at)
        elements.append(Spacer(1, 0.3 * inch))

        # 5. KPI Achievement
        elements.append(Paragraph("III. Project Impact Delivery (KPIs)", header_style))
        if not data['kpi_achievements']:
             elements.append(Paragraph("No specific KPIs were formalised for this project record.", styles['Normal']))
        else:
            kpi_rows = [["KPI Indicator", "Target", "Actual", "Status"]]
            for k in data['kpi_achievements']:
                kpi_rows.append([k['name'], str(k['target']), str(k['achieved']), k['status']])
            kt = Table(kpi_rows, colWidths=[2.8*inch, 1.0*inch, 1.0*inch, 1.2*inch])
            kt.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.Color(0.95, 0.9, 0.9)),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 9),
            ]))
            elements.append(kt)
        elements.append(Spacer(1, 0.5 * inch))

        # 6. Cryptographic Seal
        elements.append(Paragraph("IV. System Verification & Integrity", header_style))
        elements.append(Paragraph("This document represents an immutable snapshot of the project state at the time of archival. The integrity of this record is protected by a SHA-256 cryptographic seal.", styles['Normal']))
        elements.append(Spacer(1, 0.1 * inch))
        
        seal_box = [
            [Paragraph("<b>ARCHIVE HASH (SHA-256):</b>", value_style)],
            [Paragraph(f"<font face='Courier' size='8'>{grant.archive_hash or 'NOT_YET_SEALED'}</font>", value_style)]
        ]
        st = Table(seal_box, colWidths=[6*inch])
        st.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.Color(0.95, 0.95, 0.95)),
            ('BOX', (0,0), (-1,-1), 1, colors.black),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 15),
        ]))
        elements.append(st)

        # Bottom Footer
        elements.append(Spacer(1, 1 * inch))
        elements.append(Paragraph("<hr/>", styles['Normal']))
        elements.append(Paragraph("PAGMS Automated Closeout Service | MUBAS Research Support Unit (RSU)", small_style))

        doc.build(elements)
        return filename
