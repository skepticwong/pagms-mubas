"""
services/audit_export_service.py
Provides CSV and PDF export utilities for the AuditLog trail,
plus a save_scheduled_export() helper that is called by the background scheduler.
"""
import csv
import io
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


# ── directory where scheduled exports are persisted ──────────────────────────
EXPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'exports', 'audit')


class AuditExportService:
    """Exports audit log data to CSV or PDF, and manages scheduled exports."""

    # ── CSV ───────────────────────────────────────────────────────────────────
    @staticmethod
    def export_csv(logs: list) -> str:
        """
        Convert a list of audit log dicts to a UTF-8 CSV string.

        Expected keys per dict:
          id, user_name, action, resource_type, resource_id, details, timestamp
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'ID', 'User', 'Action', 'Resource Type',
            'Resource ID', 'Details', 'Timestamp (UTC)'
        ])

        for log in logs:
            writer.writerow([
                log.get('id', ''),
                log.get('user_name', ''),
                log.get('action', ''),
                log.get('resource_type', ''),
                log.get('resource_id', ''),
                log.get('details', ''),
                log.get('timestamp', ''),
            ])

        return output.getvalue()

    # ── PDF ───────────────────────────────────────────────────────────────────
    @staticmethod
    def export_pdf(logs: list, title: str = 'Audit Trail Export') -> io.BytesIO:
        """
        Build a PDF table of audit logs using reportlab.
        Returns an in-memory BytesIO (positioned at 0) containing the PDF.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )
        styles = getSampleStyleSheet()
        elements = []

        # ── Title ──────────────────────────────────────────────────────────
        elements.append(Paragraph(f'<b>{title}</b>', styles['Title']))
        elements.append(Paragraph(
            f'Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")} '
            f'| Total records: {len(logs)}',
            styles['Normal']
        ))
        elements.append(Spacer(1, 0.25 * inch))

        # ── Table data ─────────────────────────────────────────────────────
        header = ['ID', 'User', 'Action', 'Resource', 'Res. ID', 'Details', 'Timestamp (UTC)']
        data = [header]

        for log in logs:
            details = log.get('details', '') or ''
            # Truncate long detail strings so they fit in the cell
            details_short = (details[:80] + '…') if len(details) > 80 else details
            data.append([
                str(log.get('id', '')),
                log.get('user_name', ''),
                log.get('action', '').replace('_', ' '),
                log.get('resource_type', ''),
                str(log.get('resource_id', '')),
                details_short,
                log.get('timestamp', '')[:19] if log.get('timestamp') else '',
            ])

        col_widths = [0.4 * inch, 1.1 * inch, 1.6 * inch, 1.0 * inch,
                      0.55 * inch, 3.2 * inch, 1.5 * inch]

        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            # Body rows
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4ff')]),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return buffer

    # ── Scheduled / persistent export ─────────────────────────────────────────
    @staticmethod
    def save_scheduled_export(app) -> str:
        """
        Run inside the Flask app context: query all audit logs for the RSU role,
        write a dated CSV to EXPORTS_DIR, and log the action to the AuditLog table.

        Returns the filename that was written.
        """
        with app.app_context():
            from models import AuditLog, User, db

            # Collect all logs (RSU-level view)
            raw_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(5000).all()

            logs_list = []
            for log in raw_logs:
                u = User.query.get(log.user_id)
                logs_list.append({
                    'id': log.id,
                    'user_name': u.name if u else 'Unknown',
                    'action': log.action,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'details': log.details,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else '',
                })

            csv_content = AuditExportService.export_csv(logs_list)

            # Persist to disk
            os.makedirs(EXPORTS_DIR, exist_ok=True)
            date_str = datetime.utcnow().strftime('%Y-%m-%d')
            filename = f'audit_trail_{date_str}.csv'
            filepath = os.path.join(EXPORTS_DIR, filename)

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                f.write(csv_content)

            # Log to console (AuditLog.user_id is NOT NULL so no system-user entry)
            print(f'[AuditExport] Saved {filename} ({len(logs_list)} records)')
            return filename

    # ── List saved exports ────────────────────────────────────────────────────
    @staticmethod
    def list_saved_exports() -> list:
        """Return a list of dicts describing each file in EXPORTS_DIR."""
        if not os.path.isdir(EXPORTS_DIR):
            return []
        files = []
        for name in sorted(os.listdir(EXPORTS_DIR), reverse=True):
            if name.startswith('audit_trail_') and name.endswith('.csv'):
                path = os.path.join(EXPORTS_DIR, name)
                stat = os.stat(path)
                files.append({
                    'filename': name,
                    'size_bytes': stat.st_size,
                    'created_at': datetime.utcfromtimestamp(stat.st_ctime).isoformat(),
                })
        return files
