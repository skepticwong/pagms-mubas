"""
Asset Maintenance Service - Maintenance scheduling and tracking
Handles maintenance planning, scheduling, and compliance tracking
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models import db, Asset, AssetMaintenance, User
from services.notification_service import NotificationService

class AssetMaintenanceService:
    """Service for managing asset maintenance and scheduling"""
    
    # Maintenance intervals by asset category (in days)
    MAINTENANCE_INTERVALS = {
        'Vehicle': 90,        # Quarterly
        'IT Equipment': 180,  # Semi-annual
        'Lab Equipment': 365, # Annual
        'Office Equipment': 365, # Annual
        'Equipment': 365,     # Default annual
        'Tools': 180,         # Semi-annual
        'Other': 365          # Default annual
    }
    
    @staticmethod
    def schedule_initial_maintenance(asset_id: int, user_id: int) -> Optional[AssetMaintenance]:
        """Schedule initial maintenance for a new asset"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        # Get maintenance interval based on category
        interval_days = AssetMaintenanceService.MAINTENANCE_INTERVALS.get(
            asset.category, 
            AssetMaintenanceService.MAINTENANCE_INTERVALS['Equipment']
        )
        
        # Calculate next maintenance date
        next_maintenance_date = datetime.utcnow().date() + timedelta(days=interval_days)
        
        # Create initial maintenance record
        maintenance = AssetMaintenance(
            asset_id=asset_id,
            maintenance_type='Scheduled',
            description=f'Initial {asset.category} maintenance check',
            performed_date=datetime.utcnow().date(),
            next_due_date=next_maintenance_date,
            notes=f'Asset requires {asset.category} maintenance every {interval_days} days',
            created_by_user_id=user_id
        )
        
        db.session.add(maintenance)
        
        # Update asset maintenance dates
        asset.last_maintenance_date = maintenance.performed_date
        asset.next_maintenance_date = maintenance.next_due_date
        
        db.session.commit()
        
        # Schedule notification reminder
        AssetMaintenanceService._schedule_maintenance_reminder(asset, maintenance)
        
        return maintenance
    
    @staticmethod
    def create_maintenance_record(asset_id: int, maintenance_data: Dict, user_id: int) -> AssetMaintenance:
        """Create maintenance record and schedule next maintenance"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        maintenance = AssetMaintenance(
            asset_id=asset_id,
            maintenance_type=maintenance_data.get('type', 'Scheduled'),
            description=maintenance_data.get('description', ''),
            cost=maintenance_data.get('cost', 0.0),
            performed_by=maintenance_data.get('performed_by', ''),
            performed_date=datetime.strptime(maintenance_data['performed_date'], '%Y-%m-%d').date() if maintenance_data.get('performed_date') else datetime.utcnow().date(),
            next_due_date=datetime.strptime(maintenance_data['next_due_date'], '%Y-%m-%d').date() if maintenance_data.get('next_due_date') else None,
            notes=maintenance_data.get('notes', ''),
            created_by_user_id=user_id
        )
        
        db.session.add(maintenance)
        
        # Update asset maintenance dates
        asset.last_maintenance_date = maintenance.performed_date
        if maintenance.next_due_date:
            asset.next_maintenance_date = maintenance.next_due_date
        else:
            # Auto-calculate next maintenance date
            interval_days = AssetMaintenanceService.MAINTENANCE_INTERVALS.get(
                asset.category, 
                AssetMaintenanceService.MAINTENANCE_INTERVALS['Equipment']
            )
            asset.next_maintenance_date = maintenance.performed_date + timedelta(days=interval_days)
            maintenance.next_due_date = asset.next_maintenance_date
        
        db.session.commit()
        
        # Schedule reminder for next maintenance
        AssetMaintenanceService._schedule_maintenance_reminder(asset, maintenance)
        
        return maintenance
    
    @staticmethod
    def get_upcoming_maintenance(grant_id: int = None, days_ahead: int = 30) -> List[Dict]:
        """Get assets with upcoming maintenance"""
        cutoff_date = datetime.utcnow().date() + timedelta(days=days_ahead)
        
        query = Asset.query.filter(
            Asset.next_maintenance_date <= cutoff_date,
            Asset.status == 'ACTIVE'
        )
        
        if grant_id:
            query = query.filter(Asset.grant_id == grant_id)
        
        assets = query.all()
        
        upcoming_maintenance = []
        for asset in assets:
            days_until = (asset.next_maintenance_date - datetime.utcnow().date()).days
            urgency = 'high' if days_until <= 7 else 'medium' if days_until <= 14 else 'low'
            
            upcoming_maintenance.append({
                'asset': asset.to_dict(),
                'next_maintenance_date': asset.next_maintenance_date.isoformat(),
                'days_until_maintenance': days_until,
                'urgency': urgency,
                'last_maintenance_date': asset.last_maintenance_date.isoformat() if asset.last_maintenance_date else None
            })
        
        # Sort by urgency and days until
        urgency_order = {'high': 0, 'medium': 1, 'low': 2}
        upcoming_maintenance.sort(key=lambda x: (urgency_order.get(x['urgency'], 3), x['days_until_maintenance']))
        
        return upcoming_maintenance
    
    @staticmethod
    def get_overdue_maintenance(grant_id: int = None) -> List[Dict]:
        """Get assets with overdue maintenance"""
        today = datetime.utcnow().date()
        
        query = Asset.query.filter(
            Asset.next_maintenance_date < today,
            Asset.status == 'ACTIVE'
        )
        
        if grant_id:
            query = query.filter(Asset.grant_id == grant_id)
        
        assets = query.all()
        
        overdue_maintenance = []
        for asset in assets:
            days_overdue = (today - asset.next_maintenance_date).days
            
            overdue_maintenance.append({
                'asset': asset.to_dict(),
                'next_maintenance_date': asset.next_maintenance_date.isoformat(),
                'days_overdue': days_overdue,
                'last_maintenance_date': asset.last_maintenance_date.isoformat() if asset.last_maintenance_date else None,
                'severity': 'critical' if days_overdue > 90 else 'high' if days_overdue > 30 else 'medium'
            })
        
        # Sort by severity and days overdue
        severity_order = {'critical': 0, 'high': 1, 'medium': 2}
        overdue_maintenance.sort(key=lambda x: (severity_order.get(x['severity'], 3), x['days_overdue']), reverse=True)
        
        return overdue_maintenance
    
    @staticmethod
    def get_maintenance_history(asset_id: int) -> List[Dict]:
        """Get maintenance history for an asset"""
        maintenance_records = AssetMaintenance.query.filter_by(asset_id=asset_id).order_by(AssetMaintenance.performed_date.desc()).all()
        
        return [record.to_dict() for record in maintenance_records]
    
    @staticmethod
    def get_maintenance_statistics(grant_id: int = None) -> Dict:
        """Get maintenance statistics"""
        query = Asset.query.filter(Asset.status == 'ACTIVE')
        if grant_id:
            query = query.filter(Asset.grant_id == grant_id)
        
        assets = query.all()
        
        stats = {
            'total_assets': len(assets),
            'assets_with_maintenance_scheduled': 0,
            'assets_overdue': 0,
            'assets_due_soon': 0,
            'average_days_between_maintenance': 0,
            'total_maintenance_cost': 0,
            'last_maintenance_date': None,
            'next_maintenance_date': None
        }
        
        today = datetime.utcnow().date()
        total_maintenance_intervals = []
        maintenance_costs = []
        
        for asset in assets:
            if asset.next_maintenance_date:
                stats['assets_with_maintenance_scheduled'] += 1
                
                if asset.next_maintenance_date < today:
                    stats['assets_overdue'] += 1
                elif asset.next_maintenance_date <= today + timedelta(days=30):
                    stats['assets_due_soon'] += 1
                
                # Track next maintenance date
                if not stats['next_maintenance_date'] or asset.next_maintenance_date < stats['next_maintenance_date']:
                    stats['next_maintenance_date'] = asset.next_maintenance_date
            
            if asset.last_maintenance_date:
                # Track last maintenance date
                if not stats['last_maintenance_date'] or asset.last_maintenance_date > stats['last_maintenance_date']:
                    stats['last_maintenance_date'] = asset.last_maintenance_date
                
                # Calculate maintenance intervals
                maintenance_records = AssetMaintenance.query.filter_by(asset_id=asset.id).order_by(AssetMaintenance.performed_date).all()
                for i in range(1, len(maintenance_records)):
                    interval = (maintenance_records[i].performed_date - maintenance_records[i-1].performed_date).days
                    total_maintenance_intervals.append(interval)
            
            # Get maintenance costs
            maintenance_records = AssetMaintenance.query.filter_by(asset_id=asset.id).all()
            for record in maintenance_records:
                maintenance_costs.append(record.cost)
        
        # Calculate averages
        if total_maintenance_intervals:
            stats['average_days_between_maintenance'] = sum(total_maintenance_intervals) / len(total_maintenance_intervals)
        
        if maintenance_costs:
            stats['total_maintenance_cost'] = sum(maintenance_costs)
        
        # Convert dates to strings
        if stats['last_maintenance_date']:
            stats['last_maintenance_date'] = stats['last_maintenance_date'].isoformat()
        if stats['next_maintenance_date']:
            stats['next_maintenance_date'] = stats['next_maintenance_date'].isoformat()
        
        return stats
    
    @staticmethod
    def schedule_maintenance_for_asset(asset_id: int, maintenance_date: datetime, maintenance_type: str = 'Scheduled', user_id: int = None) -> AssetMaintenance:
        """Schedule specific maintenance for an asset"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        maintenance = AssetMaintenance(
            asset_id=asset_id,
            maintenance_type=maintenance_type,
            description=f'Scheduled {asset.category} maintenance',
            next_due_date=maintenance_date.date(),
            notes=f'Maintenance scheduled for {maintenance_date.strftime("%Y-%m-%d")}',
            created_by_user_id=user_id
        )
        
        db.session.add(maintenance)
        
        # Update asset next maintenance date
        asset.next_maintenance_date = maintenance_date.date()
        
        db.session.commit()
        
        # Schedule reminder
        AssetMaintenanceService._schedule_maintenance_reminder(asset, maintenance)
        
        return maintenance
    
    @staticmethod
    def complete_maintenance(maintenance_id: int, completion_data: Dict, user_id: int) -> AssetMaintenance:
        """Complete a scheduled maintenance"""
        maintenance = AssetMaintenance.query.get(maintenance_id)
        if not maintenance:
            raise ValueError("Maintenance record not found")
        
        # Update maintenance record with completion details
        maintenance.performed_date = datetime.strptime(completion_data['performed_date'], '%Y-%m-%d').date() if completion_data.get('performed_date') else datetime.utcnow().date()
        maintenance.performed_by = completion_data.get('performed_by', '')
        maintenance.cost = completion_data.get('cost', 0.0)
        maintenance.notes = completion_data.get('notes', '')
        maintenance.description = completion_data.get('description', maintenance.description)
        
        # Update asset
        asset = maintenance.asset
        asset.last_maintenance_date = maintenance.performed_date
        
        # Schedule next maintenance
        interval_days = AssetMaintenanceService.MAINTENANCE_INTERVALS.get(
            asset.category, 
            AssetMaintenanceService.MAINTENANCE_INTERVALS['Equipment']
        )
        next_maintenance_date = maintenance.performed_date + timedelta(days=interval_days)
        
        # Create next maintenance record
        next_maintenance = AssetMaintenance(
            asset_id=asset.id,
            maintenance_type='Scheduled',
            description=f'Next scheduled {asset.category} maintenance',
            next_due_date=next_maintenance_date,
            notes=f'Next maintenance scheduled based on {interval_days}-day interval',
            created_by_user_id=user_id
        )
        
        db.session.add(next_maintenance)
        asset.next_maintenance_date = next_maintenance_date
        
        db.session.commit()
        
        # Schedule reminder for next maintenance
        AssetMaintenanceService._schedule_maintenance_reminder(asset, next_maintenance)
        
        return maintenance
    
    @staticmethod
    def get_maintenance_recommendations(asset_id: int) -> List[Dict]:
        """Get maintenance recommendations for an asset"""
        asset = Asset.query.get(asset_id)
        if not asset:
            return []
        
        recommendations = []
        
        # Check if maintenance is overdue
        if asset.next_maintenance_date and asset.next_maintenance_date < datetime.utcnow().date():
            days_overdue = (datetime.utcnow().date() - asset.next_maintenance_date).days
            recommendations.append({
                'type': 'overdue',
                'title': 'Maintenance Overdue',
                'description': f'Maintenance is {days_overdue} days overdue',
                'priority': 'high',
                'action': 'Schedule maintenance immediately'
            })
        
        # Check if no maintenance scheduled
        if not asset.next_maintenance_date:
            recommendations.append({
                'type': 'no_schedule',
                'title': 'No Maintenance Scheduled',
                'description': 'This asset has no maintenance schedule',
                'priority': 'medium',
                'action': 'Create maintenance schedule'
            })
        
        # Category-specific recommendations
        category = asset.category.lower()
        if 'vehicle' in category:
            recommendations.append({
                'type': 'vehicle_specific',
                'title': 'Vehicle Maintenance',
                'description': 'Ensure regular oil changes, tire rotations, and safety inspections',
                'priority': 'medium',
                'action': 'Schedule comprehensive vehicle service'
            })
        elif 'it' in category or 'computer' in category:
            recommendations.append({
                'type': 'it_specific',
                'title': 'IT Equipment Maintenance',
                'description': 'Regular software updates, virus scans, and hardware checks',
                'priority': 'low',
                'action': 'Schedule IT maintenance check'
            })
        elif 'lab' in category:
            recommendations.append({
                'type': 'lab_specific',
                'title': 'Lab Equipment Calibration',
                'description': 'Regular calibration and certification required',
                'priority': 'high',
                'action': 'Schedule calibration service'
            })
        
        return recommendations
    
    @staticmethod
    def _schedule_maintenance_reminder(asset: Asset, maintenance: AssetMaintenance):
        """Schedule maintenance reminder (in production, this would integrate with notification system)"""
        if maintenance.next_due_date:
            # Schedule reminders 7 days and 1 day before
            reminder_dates = [
                maintenance.next_due_date - timedelta(days=7),
                maintenance.next_due_date - timedelta(days=1)
            ]
            
            for reminder_date in reminder_dates:
                if reminder_date > datetime.utcnow().date():
                    # In production, this would create actual notifications
                    print(f"Maintenance reminder scheduled: Asset {asset.name} on {reminder_date}")
    
    @staticmethod
    def generate_maintenance_report(grant_id: int) -> Dict:
        """Generate comprehensive maintenance report for a grant"""
        assets = Asset.query.filter_by(grant_id=grant_id, status='ACTIVE').all()
        
        report = {
            'grant_id': grant_id,
            'total_assets': len(assets),
            'maintenance_statistics': AssetMaintenanceService.get_maintenance_statistics(grant_id),
            'upcoming_maintenance': AssetMaintenanceService.get_upcoming_maintenance(grant_id, 30),
            'overdue_maintenance': AssetMaintenanceService.get_overdue_maintenance(grant_id),
            'recommendations': []
        }
        
        # Add overall recommendations
        if report['overdue_maintenance']:
            report['recommendations'].append("Address overdue maintenance immediately to ensure asset reliability")
        
        if len(report['upcoming_maintenance']) > 5:
            report['recommendations'].append("Consider scheduling maintenance in batches to improve efficiency")
        
        return report
