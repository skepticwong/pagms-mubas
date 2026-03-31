"""
Asset Export/Import Service - Data export and import functionality
Handles asset data export in various formats and import from external sources
"""

import csv
import json
import io
import os
from datetime import datetime
from typing import Dict, List, Optional
from werkzeug.datastructures import FileStorage
from models import db, Asset, Grant, User
from services.asset_analytics_service import AssetAnalyticsService

class AssetExportService:
    """Service for exporting and importing asset data"""
    
    @staticmethod
    def export_assets_to_csv(grant_id: int, include_details: bool = True) -> Dict:
        """Export assets to CSV format"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        # Create CSV data
        output = io.StringIO()
        
        if include_details:
            fieldnames = [
                'id', 'name', 'asset_tag', 'category', 'source_type', 'status',
                'purchase_cost', 'depreciation_value', 'custodian_user_id',
                'assigned_task_id', 'acquisition_date', 'last_maintenance_date',
                'next_maintenance_date', 'expected_return_date', 'actual_return_date',
                'owner_name', 'rental_fee_total', 'created_at', 'updated_at'
            ]
        else:
            fieldnames = [
                'id', 'name', 'asset_tag', 'category', 'source_type', 'status',
                'purchase_cost', 'custodian_user_id', 'created_at'
            ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for asset in assets:
            row = {}
            for field in fieldnames:
                value = getattr(asset, field, '')
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif value is None:
                    value = ''
                row[field] = value
            
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return {
            'format': 'csv',
            'filename': f'assets_export_{grant_id}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv',
            'content': csv_content,
            'record_count': len(assets)
        }
    
    @staticmethod
    def export_assets_to_json(grant_id: int, include_details: bool = True) -> Dict:
        """Export assets to JSON format"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        export_data = {
            'export_info': {
                'grant_id': grant_id,
                'export_date': datetime.utcnow().isoformat(),
                'format': 'json',
                'include_details': include_details,
                'record_count': len(assets)
            },
            'assets': []
        }
        
        for asset in assets:
            asset_data = asset.to_dict()
            
            if not include_details:
                # Include only basic fields
                asset_data = {
                    'id': asset.id,
                    'name': asset.name,
                    'asset_tag': asset.asset_tag,
                    'category': asset.category,
                    'source_type': asset.source_type,
                    'status': asset.status,
                    'purchase_cost': asset.purchase_cost,
                    'custodian_user_id': asset.custodian_user_id,
                    'created_at': asset.created_at.isoformat() if asset.created_at else None
                }
            
            export_data['assets'].append(asset_data)
        
        json_content = json.dumps(export_data, indent=2, default=str)
        
        return {
            'format': 'json',
            'filename': f'assets_export_{grant_id}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json',
            'content': json_content,
            'record_count': len(assets)
        }
    
    @staticmethod
    def export_assets_to_excel(grant_id: int, include_details: bool = True) -> Dict:
        """Export assets to Excel format (placeholder)"""
        # This would use a library like openpyxl or pandas
        # For now, return JSON content
        json_export = AssetExportService.export_assets_to_json(grant_id, include_details)
        
        return {
            'format': 'excel',
            'filename': f'assets_export_{grant_id}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.xlsx',
            'content': json_export['content'],
            'record_count': json_export['record_count']
        }
    
    @staticmethod
    def export_analytics_to_csv(grant_id: int) -> Dict:
        """Export analytics data to CSV format"""
        analytics = AssetAnalyticsService.get_comprehensive_analytics(grant_id)
        
        output = io.StringIO()
        
        # Export overview metrics
        writer = csv.writer(output)
        writer.writerow(['Analytics Export'])
        writer.writerow(['Grant ID', grant_id])
        writer.writerow(['Export Date', datetime.utcnow().isoformat()])
        writer.writerow([])
        
        # Overview metrics
        writer.writerow(['Overview Metrics'])
        writer.writerow(['Metric', 'Value'])
        
        overview = analytics['overview']
        for key, value in overview.items():
            if key not in ['asset_categories', 'source_types', 'status_distribution']:
                writer.writerow([key, value])
        
        writer.writerow([])
        
        # Asset categories
        writer.writerow(['Asset Categories'])
        writer.writerow(['Category', 'Count'])
        for category, count in overview['asset_categories'].items():
            writer.writerow([category, count])
        
        writer.writerow([])
        
        # Source types
        writer.writerow(['Source Types'])
        writer.writerow(['Source Type', 'Count'])
        for source_type, count in overview['source_types'].items():
            writer.writerow([source_type, count])
        
        csv_content = output.getvalue()
        output.close()
        
        return {
            'format': 'csv',
            'filename': f'asset_analytics_{grant_id}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv',
            'content': csv_content
        }
    
    @staticmethod
    def import_assets_from_csv(file: FileStorage, grant_id: int, user_id: int, update_existing: bool = False) -> Dict:
        """Import assets from CSV file"""
        try:
            # Read CSV file
            csv_content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            results = {
                'imported': 0,
                'updated': 0,
                'errors': [],
                'total_rows': 0
            }
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 to account for header
                results['total_rows'] += 1
                
                try:
                    # Validate required fields
                    if not row.get('name'):
                        results['errors'].append(f'Row {row_num}: Name is required')
                        continue
                    
                    # Check if asset exists (for updates)
                    existing_asset = None
                    if row.get('id') and update_existing:
                        try:
                            existing_asset = Asset.query.get(int(row['id']))
                        except ValueError:
                            pass
                    
                    if existing_asset and update_existing:
                        # Update existing asset
                        AssetExportService._update_asset_from_csv_row(existing_asset, row)
                        results['updated'] += 1
                    else:
                        # Create new asset
                        asset = AssetExportService._create_asset_from_csv_row(row, grant_id, user_id)
                        db.session.add(asset)
                        results['imported'] += 1
                
                except Exception as e:
                    results['errors'].append(f'Row {row_num}: {str(e)}')
            
            db.session.commit()
            
            return results
            
        except Exception as e:
            db.session.rollback()
            return {
                'imported': 0,
                'updated': 0,
                'errors': [f'File processing error: {str(e)}'],
                'total_rows': 0
            }
    
    @staticmethod
    def import_assets_from_json(file: FileStorage, grant_id: int, user_id: int, update_existing: bool = False) -> Dict:
        """Import assets from JSON file"""
        try:
            # Read JSON file
            json_content = file.read().decode('utf-8')
            data = json.loads(json_content)
            
            results = {
                'imported': 0,
                'updated': 0,
                'errors': [],
                'total_assets': 0
            }
            
            assets_data = data.get('assets', [])
            results['total_assets'] = len(assets_data)
            
            for asset_data in assets_data:
                try:
                    # Validate required fields
                    if not asset_data.get('name'):
                        results['errors'].append(f'Asset: Name is required')
                        continue
                    
                    # Check if asset exists (for updates)
                    existing_asset = None
                    if asset_data.get('id') and update_existing:
                        existing_asset = Asset.query.get(asset_data['id'])
                    
                    if existing_asset and update_existing:
                        # Update existing asset
                        AssetExportService._update_asset_from_json_data(existing_asset, asset_data)
                        results['updated'] += 1
                    else:
                        # Create new asset
                        asset = AssetExportService._create_asset_from_json_data(asset_data, grant_id, user_id)
                        db.session.add(asset)
                        results['imported'] += 1
                
                except Exception as e:
                    results['errors'].append(f'Asset {asset_data.get("name", "Unknown")}: {str(e)}')
            
            db.session.commit()
            
            return results
            
        except json.JSONDecodeError as e:
            return {
                'imported': 0,
                'updated': 0,
                'errors': [f'Invalid JSON format: {str(e)}'],
                'total_assets': 0
            }
        except Exception as e:
            db.session.rollback()
            return {
                'imported': 0,
                'updated': 0,
                'errors': [f'File processing error: {str(e)}'],
                'total_assets': 0
            }
    
    @staticmethod
    def export_template(format_type: str = 'csv') -> Dict:
        """Export import template"""
        template_data = [
            {
                'id': '',
                'name': 'Sample Asset Name',
                'asset_tag': 'AST-000001',
                'category': 'Equipment',
                'source_type': 'PURCHASED',
                'status': 'ACTIVE',
                'purchase_cost': '1000.00',
                'depreciation_value': '800.00',
                'custodian_user_id': '1',
                'assigned_task_id': '1',
                'acquisition_date': '2025-01-01',
                'last_maintenance_date': '2025-03-01',
                'next_maintenance_date': '2025-06-01',
                'expected_return_date': '',
                'actual_return_date': '',
                'owner_name': '',
                'rental_fee_total': '0.00',
                'created_at': '2025-01-01T00:00:00',
                'updated_at': '2025-01-01T00:00:00'
            }
        ]
        
        if format_type == 'csv':
            output = io.StringIO()
            
            fieldnames = list(template_data[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in template_data:
                writer.writerow(row)
            
            csv_content = output.getvalue()
            output.close()
            
            return {
                'format': 'csv',
                'filename': f'asset_import_template_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv',
                'content': csv_content
            }
        
        elif format_type == 'json':
            json_content = json.dumps({
                'template_info': {
                    'description': 'Asset Import Template',
                    'format': 'json',
                    'created_date': datetime.utcnow().isoformat()
                },
                'assets': template_data
            }, indent=2)
            
            return {
                'format': 'json',
                'filename': f'asset_import_template_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json',
                'content': json_content
            }
    
    @staticmethod
    def validate_import_data(file: FileStorage, format_type: str) -> Dict:
        """Validate import data without importing"""
        try:
            if format_type == 'csv':
                csv_content = file.read().decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(csv_content))
                
                validation = {
                    'is_valid': True,
                    'errors': [],
                    'warnings': [],
                    'row_count': 0,
                    'required_fields': ['name'],
                    'optional_fields': ['asset_tag', 'category', 'source_type', 'status', 'purchase_cost']
                }
                
                # Check required fields
                if not csv_reader.fieldnames:
                    validation['errors'].append('CSV file is empty or has no headers')
                    validation['is_valid'] = False
                    return validation
                
                missing_required = [field for field in validation['required_fields'] if field not in csv_reader.fieldnames]
                if missing_required:
                    validation['errors'].append(f'Missing required fields: {", ".join(missing_required)}')
                    validation['is_valid'] = False
                
                # Validate data rows
                for row_num, row in enumerate(csv_reader, start=2):
                    validation['row_count'] += 1
                    
                    # Check required fields in each row
                    for field in validation['required_fields']:
                        if not row.get(field):
                            validation['errors'].append(f'Row {row_num}: {field} is required')
                            validation['is_valid'] = False
                
                return validation
            
            elif format_type == 'json':
                json_content = file.read().decode('utf-8')
                data = json.loads(json_content)
                
                validation = {
                    'is_valid': True,
                    'errors': [],
                    'warnings': [],
                    'asset_count': 0,
                    'required_fields': ['name'],
                    'optional_fields': ['asset_tag', 'category', 'source_type', 'status', 'purchase_cost']
                }
                
                assets_data = data.get('assets', [])
                validation['asset_count'] = len(assets_data)
                
                for i, asset_data in enumerate(assets_data):
                    # Check required fields
                    for field in validation['required_fields']:
                        if field not in asset_data:
                            validation['errors'].append(f'Asset {i+1}: {field} is required')
                            validation['is_valid'] = False
                
                return validation
        
        except Exception as e:
            return {
                'is_valid': False,
                'errors': [f'Validation error: {str(e)}'],
                'warnings': [],
                'row_count': 0,
                'asset_count': 0
            }
    
    @staticmethod
    def _create_asset_from_csv_row(row: Dict, grant_id: int, user_id: int) -> Asset:
        """Create asset from CSV row data"""
        asset = Asset(
            grant_id=grant_id,
            name=row['name'],
            asset_tag=row.get('asset_tag') or None,
            category=row.get('category') or 'Equipment',
            source_type=row.get('source_type') or 'PURCHASED',
            status=row.get('status') or 'ACTIVE',
            purchase_cost=float(row.get('purchase_cost', 0)) if row.get('purchase_cost') else None,
            depreciation_value=float(row.get('depreciation_value', 0)) if row.get('depreciation_value') else None,
            custodian_user_id=int(row.get('custodian_user_id')) if row.get('custodian_user_id') else None,
            assigned_task_id=int(row.get('assigned_task_id')) if row.get('assigned_task_id') else None,
            owner_name=row.get('owner_name') or None,
            rental_fee_total=float(row.get('rental_fee_total', 0)) if row.get('rental_fee_total') else None,
            created_by_user_id=user_id,
            updated_by_user_id=user_id
        )
        
        # Parse dates
        if row.get('acquisition_date'):
            asset.acquisition_date = datetime.fromisoformat(row['acquisition_date']).date()
        
        if row.get('last_maintenance_date'):
            asset.last_maintenance_date = datetime.fromisoformat(row['last_maintenance_date']).date()
        
        if row.get('next_maintenance_date'):
            asset.next_maintenance_date = datetime.fromisoformat(row['next_maintenance_date']).date()
        
        if row.get('expected_return_date'):
            asset.expected_return_date = datetime.fromisoformat(row['expected_return_date']).date()
        
        if row.get('actual_return_date'):
            asset.actual_return_date = datetime.fromisoformat(row['actual_return_date']).date()
        
        return asset
    
    @staticmethod
    def _update_asset_from_csv_row(asset: Asset, row: Dict):
        """Update asset from CSV row data"""
        if 'name' in row and row['name']:
            asset.name = row['name']
        
        if 'asset_tag' in row and row['asset_tag']:
            asset.asset_tag = row['asset_tag']
        
        if 'category' in row and row['category']:
            asset.category = row['category']
        
        if 'source_type' in row and row['source_type']:
            asset.source_type = row['source_type']
        
        if 'status' in row and row['status']:
            asset.status = row['status']
        
        if 'purchase_cost' in row and row['purchase_cost']:
            asset.purchase_cost = float(row['purchase_cost'])
        
        if 'depreciation_value' in row and row['depreciation_value']:
            asset.depreciation_value = float(row['depreciation_value'])
        
        if 'custodian_user_id' in row and row['custodian_user_id']:
            asset.custodian_user_id = int(row['custodian_user_id'])
        
        if 'assigned_task_id' in row and row['assigned_task_id']:
            asset.assigned_task_id = int(row['assigned_task_id'])
        
        if 'owner_name' in row and row['owner_name']:
            asset.owner_name = row['owner_name']
        
        if 'rental_fee_total' in row and row['rental_fee_total']:
            asset.rental_fee_total = float(row['rental_fee_total'])
        
        # Update dates
        if 'acquisition_date' in row and row['acquisition_date']:
            asset.acquisition_date = datetime.fromisoformat(row['acquisition_date']).date()
        
        if 'last_maintenance_date' in row and row['last_maintenance_date']:
            asset.last_maintenance_date = datetime.fromisoformat(row['last_maintenance_date']).date()
        
        if 'next_maintenance_date' in row and row['next_maintenance_date']:
            asset.next_maintenance_date = datetime.fromisoformat(row['next_maintenance_date']).date()
        
        if 'expected_return_date' in row and row['expected_return_date']:
            asset.expected_return_date = datetime.fromisoformat(row['expected_return_date']).date()
        
        if 'actual_return_date' in row and row['actual_return_date']:
            asset.actual_return_date = datetime.fromisoformat(row['actual_return_date']).date()
        
        asset.updated_at = datetime.utcnow()
    
    @staticmethod
    def _create_asset_from_json_data(asset_data: Dict, grant_id: int, user_id: int) -> Asset:
        """Create asset from JSON data"""
        asset = Asset(
            grant_id=grant_id,
            name=asset_data['name'],
            asset_tag=asset_data.get('asset_tag'),
            category=asset_data.get('category', 'Equipment'),
            source_type=asset_data.get('source_type', 'PURCHASED'),
            status=asset_data.get('status', 'ACTIVE'),
            purchase_cost=asset_data.get('purchase_cost'),
            depreciation_value=asset_data.get('depreciation_value'),
            custodian_user_id=asset_data.get('custodian_user_id'),
            assigned_task_id=asset_data.get('assigned_task_id'),
            owner_name=asset_data.get('owner_name'),
            rental_fee_total=asset_data.get('rental_fee_total'),
            created_by_user_id=user_id,
            updated_by_user_id=user_id
        )
        
        # Parse dates
        if asset_data.get('acquisition_date'):
            asset.acquisition_date = datetime.fromisoformat(asset_data['acquisition_date']).date()
        
        if asset_data.get('last_maintenance_date'):
            asset.last_maintenance_date = datetime.fromisoformat(asset_data['last_maintenance_date']).date()
        
        if asset_data.get('next_maintenance_date'):
            asset.next_maintenance_date = datetime.fromisoformat(asset_data['next_maintenance_date']).date()
        
        if asset_data.get('expected_return_date'):
            asset.expected_return_date = datetime.fromisoformat(asset_data['expected_return_date']).date()
        
        if asset_data.get('actual_return_date'):
            asset.actual_return_date = datetime.fromisoformat(asset_data['actual_return_date']).date()
        
        return asset
    
    @staticmethod
    def _update_asset_from_json_data(asset: Asset, asset_data: Dict):
        """Update asset from JSON data"""
        if 'name' in asset_data:
            asset.name = asset_data['name']
        
        if 'asset_tag' in asset_data:
            asset.asset_tag = asset_data['asset_tag']
        
        if 'category' in asset_data:
            asset.category = asset_data['category']
        
        if 'source_type' in asset_data:
            asset.source_type = asset_data['source_type']
        
        if 'status' in asset_data:
            asset.status = asset_data['status']
        
        if 'purchase_cost' in asset_data:
            asset.purchase_cost = asset_data['purchase_cost']
        
        if 'depreciation_value' in asset_data:
            asset.depreciation_value = asset_data['depreciation_value']
        
        if 'custodian_user_id' in asset_data:
            asset.custodian_user_id = asset_data['custodian_user_id']
        
        if 'assigned_task_id' in asset_data:
            asset.assigned_task_id = asset_data['assigned_task_id']
        
        if 'owner_name' in asset_data:
            asset.owner_name = asset_data['owner_name']
        
        if 'rental_fee_total' in asset_data:
            asset.rental_fee_total = asset_data['rental_fee_total']
        
        # Update dates
        if 'acquisition_date' in asset_data:
            asset.acquisition_date = datetime.fromisoformat(asset_data['acquisition_date']).date()
        
        if 'last_maintenance_date' in asset_data:
            asset.last_maintenance_date = datetime.fromisoformat(asset_data['last_maintenance_date']).date()
        
        if 'next_maintenance_date' in asset_data:
            asset.next_maintenance_date = datetime.fromisoformat(asset_data['next_maintenance_date']).date()
        
        if 'expected_return_date' in asset_data:
            asset.expected_return_date = datetime.fromisoformat(asset_data['expected_return_date']).date()
        
        if 'actual_return_date' in asset_data:
            asset.actual_return_date = datetime.fromisoformat(asset_data['actual_return_date']).date()
        
        asset.updated_at = datetime.utcnow()
    
    @staticmethod
    def get_export_formats() -> List[str]:
        """Get available export formats"""
        return ['csv', 'json', 'excel']
    
    @staticmethod
    def get_import_formats() -> List[str]:
        """Get available import formats"""
        return ['csv', 'json']
