from models import db, Grant, Milestone, ExpenseClaim, Task, User, GrantTeam, EvidenceSubmission, BudgetCategory
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
            submissions = db.session.query(EvidenceSubmission).join(Task).filter(
                Task.grant_id == grant_id,
                Task.assigned_to == entry.user_id,
                EvidenceSubmission.verification_status == 'verified'
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
            # If evidence_filename attribute exists (it might have been added in a patch)
            if hasattr(m, 'evidence_filename') and m.evidence_filename:
                item['evidence_url'] = f"http://localhost:5000/uploads/evidence/{m.evidence_filename}"
            else:
                item['evidence_url'] = "N/A"
            formatted_milestones.append(item)

        return {
            "grant": grant.to_dict(include_categories=True),
            "milestones": formatted_milestones,
            "expenses": [e.to_dict() for e in expenses],
            "effort": effort_data,
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
        header_style = ParagraphStyle('HeaderStyle', parent=styles['Heading2'], fontSize=16, spaceBefore=15, spaceAfter=10, color=colors.hexColor("#1e40af"))
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
            milestone_rows = [["Milestone", "Status", "Completion", "Evidence Link"]]
            for m in data['milestones']:
                status_icon = "✅ Completed" if m['status'] == 'completed' else "⏳ In Progress"
                milestone_rows.append([
                    m['title'],
                    status_icon,
                    m['completion_date'] or "N/A",
                    m['evidence_url'] if m['evidence_url'] != "N/A" else "None"
                ])
            mt = Table(milestone_rows, colWidths=[2.2*inch, 1.2*inch, 1.2*inch, 1.8*inch])
            mt.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.hexColor("#f3f4f6")),
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
        x_rate = data['grant']['exchange_rate']
        
        for cat in data['grant']['categories']:
            alloc = cat['allocated']
            spent = cat['spent']
            burn = round((spent/alloc)*100) if alloc > 0 else 0
            budget_rows.append([
                cat['name'],
                f"${alloc:,.0f}",
                f"${spent:,.0f}",
                f"K{spent * x_rate:,.0f}",
                f"{burn}%"
            ])
            total_usd_alloc += alloc
            total_usd_spent += spent
            
        total_burn = round((total_usd_spent/total_usd_alloc)*100) if total_usd_alloc > 0 else 0
        budget_rows.append([
            "TOTAL",
            f"${total_usd_alloc:,.0f}",
            f"${total_usd_spent:,.0f}",
            f"K{total_usd_spent * x_rate:,.0f}",
            f"{total_burn}%"
        ])
        
        bt = Table(budget_rows, colWidths=[1.8*inch, 1.1*inch, 1.1*inch, 1.4*inch, 0.8*inch])
        bt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.hexColor("#f3f4f6")),
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
                ('BACKGROUND', (0,0), (-1,0), colors.hexColor("#f3f4f6")),
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
                ('BACKGROUND', (0,0), (-1,0), colors.hexColor("#f3f4f6")),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 9),
            ]))
            elements.append(eft)
        
        elements.append(Spacer(1, 0.2 * inch))
        cert_text = f"<b>Statement of Certification:</b> All effort summarized above was performed as described and has been certified by the Principal Investigator on {datetime.now().strftime('%d %b %Y')}."
        elements.append(Paragraph(cert_text, styles['Normal']))

        # Footer
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph("<hr/>", styles['Normal']))
        elements.append(Paragraph("<i>This report contains only system-verified data. No manual edits were made.</i>", small_style))
        elements.append(Paragraph(f"PAGMS v1.0 | MUBAS Research Support Unit | System Timestamp: {data['report_info']['generated_at']}", small_style))

        doc.build(elements)
        return filename
