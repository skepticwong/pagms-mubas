"""
Asset Barcode/QR Code Service - Barcode and QR code generation and scanning
Handles asset identification, tracking, and mobile scanning capabilities
"""

import os
import uuid
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional
from werkzeug.utils import secure_filename
from models import db, Asset, User
from services.notification_service import NotificationService

# Try to import optional dependencies
try:
    import qrcode
    QR_CODE_AVAILABLE = True
except ImportError:
    QR_CODE_AVAILABLE = False

try:
    from barcode import get_barcode_class
    from barcode.writer import ImageWriter
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class AssetBarcodeService:
    """Service for managing asset barcodes and QR codes"""
    
    @staticmethod
    def generate_asset_barcode(asset_id: int, barcode_type: str = 'code128') -> Dict:
        """Generate barcode for an asset"""
        if not BARCODE_AVAILABLE:
            raise ImportError("Barcode library not installed. Install with: pip install barcode")
        
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        # Generate barcode data
        barcode_data = f"AST-{asset.id:06d}" if not asset.asset_tag else asset.asset_tag
        
        # Create barcode
        barcode_class = get_barcode_class(barcode_type)
        barcode = barcode_class(barcode_data, writer=ImageWriter())
        
        # Generate barcode image
        barcode_image = barcode.render()
        
        # Add asset information to barcode
        annotated_image = AssetBarcodeService._annotate_barcode(barcode_image, asset)
        
        # Save barcode image
        barcode_dir = os.path.join('uploads', 'barcodes')
        os.makedirs(barcode_dir, exist_ok=True)
        
        barcode_filename = f"barcode_{asset_id}_{uuid.uuid4().hex[:8]}.png"
        barcode_path = os.path.join(barcode_dir, barcode_filename)
        
        annotated_image.save(barcode_path)
        
        # Update asset with barcode information
        if not asset.barcode_data:
            asset.barcode_data = {}
        
        asset.barcode_data.update({
            'barcode_type': barcode_type,
            'barcode_data': barcode_data,
            'barcode_filename': barcode_filename,
            'barcode_path': barcode_path,
            'generated_at': datetime.utcnow().isoformat()
        })
        
        db.session.commit()
        
        return {
            'barcode_data': barcode_data,
            'barcode_type': barcode_type,
            'barcode_filename': barcode_filename,
            'barcode_path': barcode_path,
            'asset_tag': asset.asset_tag
        }
    
    @staticmethod
    def generate_asset_qrcode(asset_id: int, include_details: bool = True) -> Dict:
        """Generate QR code for an asset"""
        if not QR_CODE_AVAILABLE:
            raise ImportError("QR code library not installed. Install with: pip install qrcode[pil]")
        
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        # Generate QR code data
        qr_data = AssetBarcodeService._generate_qr_data(asset, include_details)
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Generate QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Add asset information to QR code
        annotated_qr = AssetBarcodeService._annotate_qrcode(qr_image, asset)
        
        # Save QR code image
        qr_dir = os.path.join('uploads', 'qrcodes')
        os.makedirs(qr_dir, exist_ok=True)
        
        qr_filename = f"qrcode_{asset_id}_{uuid.uuid4().hex[:8]}.png"
        qr_path = os.path.join(qr_dir, qr_filename)
        
        annotated_qr.save(qr_path)
        
        # Update asset with QR code information
        if not asset.qrcode_data:
            asset.qrcode_data = {}
        
        asset.qrcode_data.update({
            'qr_data': qr_data,
            'qr_filename': qr_filename,
            'qr_path': qr_path,
            'include_details': include_details,
            'generated_at': datetime.utcnow().isoformat()
        })
        
        db.session.commit()
        
        return {
            'qr_data': qr_data,
            'qr_filename': qr_filename,
            'qr_path': qr_path,
            'include_details': include_details
        }
    
    @staticmethod
    def scan_asset_barcode(barcode_data: str, user_id: int) -> Dict:
        """Process barcode scan and return asset information"""
        # Parse barcode data
        asset_id = AssetBarcodeService._parse_barcode_data(barcode_data)
        
        if not asset_id:
            return {'error': 'Invalid barcode format', 'barcode_data': barcode_data}
        
        asset = Asset.query.get(asset_id)
        if not asset:
            return {'error': 'Asset not found', 'asset_id': asset_id}
        
        # Create scan log
        scan_log = {
            'scan_time': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'barcode_data': barcode_data,
            'asset_id': asset_id,
            'asset_status': asset.status,
            'location': asset.custodian_user_id
        }
        
        # Add to asset scan history
        if not asset.scan_history:
            asset.scan_history = []
        
        asset.scan_history.append(scan_log)
        asset.last_scanned = datetime.utcnow().isoformat()
        
        db.session.commit()
        
        return {
            'asset': asset.to_dict(),
            'scan_log': scan_log,
            'message': 'Asset scanned successfully'
        }
    
    @staticmethod
    def get_asset_by_barcode(barcode_data: str) -> Dict:
        """Get asset information by barcode/QR code data"""
        asset_id = AssetBarcodeService._parse_barcode_data(barcode_data)
        
        if not asset_id:
            return {'error': 'Invalid barcode format', 'barcode_data': barcode_data}
        
        asset = Asset.query.get(asset_id)
        if not asset:
            return {'error': 'Asset not found', 'asset_id': asset_id}
        
        return {
            'asset': asset.to_dict(),
            'barcode_type': 'barcode' if barcode_data.startswith('AST-') else 'qrcode'
        }
    
    @staticmethod
    def generate_batch_barcodes(grant_id: int, barcode_type: str = 'code128') -> List[Dict]:
        """Generate barcodes for all assets in a grant"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        batch_results = []
        
        for asset in assets:
            try:
                barcode_info = AssetBarcodeService.generate_asset_barcode(asset.id, barcode_type)
                batch_results.append({
                    'asset_id': asset.id,
                    'asset_name': asset.name,
                    'barcode_info': barcode_info,
                    'status': 'success'
                })
            except Exception as e:
                batch_results.append({
                    'asset_id': asset.id,
                    'asset_name': asset.name,
                    'error': str(e),
                    'status': 'error'
                })
        
        return batch_results
    
    @staticmethod
    def generate_batch_qrcodes(grant_id: int, include_details: bool = True) -> List[Dict]:
        """Generate QR codes for all assets in a grant"""
        assets = Asset.query.filter_by(grant_id=grant_id).all()
        
        batch_results = []
        
        for asset in assets:
            try:
                qr_info = AssetBarcodeService.generate_asset_qrcode(asset.id, include_details)
                batch_results.append({
                    'asset_id': asset.id,
                    'asset_name': asset.name,
                    'qr_info': qr_info,
                    'status': 'success'
                })
            except Exception as e:
                batch_results.append({
                    'asset_id': asset.id,
                    'asset_name': asset.name,
                    'error': str(e),
                    'status': 'error'
                })
        
        return batch_results
    
    @staticmethod
    def get_scan_statistics(grant_id: int = None, days: int = 30) -> Dict:
        """Get scanning statistics"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        query = Asset.query
        if grant_id:
            query = query.filter_by(grant_id=grant_id)
        
        assets = query.all()
        
        stats = {
            'total_scans': 0,
            'unique_assets_scanned': 0,
            'scans_by_day': {},
            'scans_by_user': {},
            'most_scanned_assets': [],
            'scan_frequency': {},
            'period_days': days
        }
        
        for asset in assets:
            if asset.scan_history:
                asset_scans = 0
                for scan in asset.scan_history:
                    scan_date = datetime.fromisoformat(scan['scan_time']).date()
                    
                    # Filter by date range
                    if start_date <= scan_date <= end_date:
                        stats['total_scans'] += 1
                        asset_scans += 1
                        
                        # Scans by day
                        day_str = scan_date.isoformat()
                        stats['scans_by_day'][day_str] = stats['scans_by_day'].get(day_str, 0) + 1
                        
                        # Scans by user
                        user_id = scan['user_id']
                        stats['scans_by_user'][user_id] = stats['scans_by_user'].get(user_id, 0) + 1
                
                if asset_scans > 0:
                    stats['unique_assets_scanned'] += 1
                    stats['scan_frequency'][asset.id] = asset_scans
        
        # Most scanned assets
        sorted_assets = sorted(stats['scan_frequency'].items(), key=lambda x: x[1], reverse=True)
        for asset_id, scan_count in sorted_assets[:10]:
            asset = Asset.query.get(asset_id)
            if asset:
                stats['most_scanned_assets'].append({
                    'asset_id': asset_id,
                    'asset_name': asset.name,
                    'scan_count': scan_count
                })
        
        return stats
    
    @staticmethod
    def validate_barcode_data(barcode_data: str) -> Dict:
        """Validate barcode data format"""
        validation = {
            'is_valid': False,
            'barcode_type': None,
            'asset_id': None,
            'format': None,
            'errors': []
        }
        
        # Check for asset tag barcode format
        if barcode_data.startswith('AST-'):
            try:
                asset_id = int(barcode_data[4:])
                validation['is_valid'] = True
                validation['barcode_type'] = 'asset_tag'
                validation['asset_id'] = asset_id
                validation['format'] = 'AST-XXXXXX'
            except ValueError:
                validation['errors'].append('Invalid asset tag barcode format')
        
        # Check for QR code format (JSON)
        elif barcode_data.startswith('{') and barcode_data.endswith('}'):
            try:
                import json
                qr_data = json.loads(barcode_data)
                
                if 'asset_id' in qr_data:
                    validation['is_valid'] = True
                    validation['barcode_type'] = 'qrcode'
                    validation['asset_id'] = qr_data['asset_id']
                    validation['format'] = 'JSON'
                else:
                    validation['errors'].append('QR code missing asset_id field')
            except json.JSONDecodeError:
                validation['errors'].append('Invalid QR code JSON format')
        
        else:
            validation['errors'].append('Unknown barcode format')
        
        return validation
    
    @staticmethod
    def _generate_qr_data(asset: Asset, include_details: bool = True) -> str:
        """Generate QR code data for an asset"""
        import json
        
        qr_data = {
            'asset_id': asset.id,
            'asset_tag': asset.asset_tag,
            'name': asset.name,
            'category': asset.category,
            'status': asset.status
        }
        
        if include_details:
            qr_data.update({
                'grant_id': asset.grant_id,
                'source_type': asset.source_type,
                'purchase_cost': asset.purchase_cost,
                'custodian': asset.custodian_user_id,
                'generated_at': datetime.utcnow().isoformat()
            })
        
        return json.dumps(qr_data)
    
    @staticmethod
    def _annotate_barcode(image: Image.Image, asset: Asset) -> Image.Image:
        """Add asset information to barcode image"""
        # Create a larger image to accommodate barcode and text
        width, height = image.size
        new_height = height + 60
        annotated = Image.new('RGB', (width, new_height), 'white')
        
        # Paste barcode at the top
        annotated.paste(image, (0, 0))
        
        # Add text below barcode
        draw = ImageDraw.Draw(annotated)
        
        try:
            # Try to use a default font
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            # Use default font if Arial is not available
            font = ImageFont.load_default()
        
        # Add asset information
        text_lines = [
            f"ID: {asset.id}",
            f"Tag: {asset.asset_tag or 'N/A'}",
            f"Name: {asset.name[:30]}{'...' if len(asset.name) > 30 else ''}"
        ]
        
        y_offset = height + 5
        for line in text_lines:
            draw.text((5, y_offset), line, fill='black', font=font)
            y_offset += 15
        
        return annotated
    
    @staticmethod
    def _annotate_qrcode(image: Image.Image, asset: Asset) -> Image.Image:
        """Add asset information to QR code image"""
        # Create a larger image to accommodate QR code and text
        width, height = image.size
        new_height = height + 60
        annotated = Image.new('RGB', (width, new_height), 'white')
        
        # Paste QR code at the top
        annotated.paste(image, (0, 0))
        
        # Add text below QR code
        draw = ImageDraw.Draw(annotated)
        
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        # Add asset information
        text_lines = [
            f"ID: {asset.id}",
            f"Tag: {asset.asset_tag or 'N/A'}",
            f"Name: {asset.name[:30]}{'...' if len(asset.name) > 30 else ''}"
        ]
        
        y_offset = height + 5
        for line in text_lines:
            draw.text((5, y_offset), line, fill='black', font=font)
            y_offset += 15
        
        return annotated
    
    @staticmethod
    def _parse_barcode_data(barcode_data: str) -> Optional[int]:
        """Parse barcode data and extract asset ID"""
        validation = AssetBarcodeService.validate_barcode_data(barcode_data)
        
        if validation['is_valid']:
            return validation['asset_id']
        
        return None
    
    @staticmethod
    def get_asset_barcode(asset_id: int) -> Dict:
        """Get existing barcode information for an asset"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        if not asset.barcode_data:
            return {'error': 'No barcode generated for this asset'}
        
        return asset.barcode_data
    
    @staticmethod
    def get_asset_qrcode(asset_id: int) -> Dict:
        """Get existing QR code information for an asset"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        if not asset.qrcode_data:
            return {'error': 'No QR code generated for this asset'}
        
        return asset.qrcode_data
    
    @staticmethod
    def delete_asset_barcode(asset_id: int, user_id: int) -> bool:
        """Delete barcode for an asset"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        if asset.barcode_data and asset.barcode_data.get('barcode_path'):
            # Delete barcode file
            try:
                os.remove(asset.barcode_data['barcode_path'])
            except:
                pass  # File might not exist
        
        # Clear barcode data
        asset.barcode_data = {}
        asset.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return True
    
    @staticmethod
    def delete_asset_qrcode(asset_id: int, user_id: int) -> bool:
        """Delete QR code for an asset"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        if asset.qrcode_data and asset.qrcode_data.get('qr_path'):
            # Delete QR code file
            try:
                os.remove(asset.qrcode_data['qr_path'])
            except:
                pass  # File might not exist
        
        # Clear QR code data
        asset.qrcode_data = {}
        asset.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return True
    
    @staticmethod
    def get_supported_barcode_types() -> List[str]:
        """Get supported barcode types"""
        return [
            'code128',
            'code39',
            'ean13',
            'upc',
            'isbn',
            'issn'
        ]
    
    @staticmethod
    def generate_asset_label(asset_id: int, label_format: str = 'standard') -> Dict:
        """Generate comprehensive asset label with barcode and QR code"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        # Generate both barcode and QR code
        barcode_info = AssetBarcodeService.generate_asset_barcode(asset.id)
        qr_info = AssetBarcodeService.generate_asset_qrcode(asset.id, True)
        
        # Create label image
        label_image = AssetBarcodeService._create_asset_label(asset, barcode_info, qr_info, label_format)
        
        # Save label image
        label_dir = os.path.join('uploads', 'labels')
        os.makedirs(label_dir, exist_ok=True)
        
        label_filename = f"label_{asset_id}_{uuid.uuid4().hex[:8]}.png"
        label_path = os.path.join(label_dir, label_filename)
        
        label_image.save(label_path)
        
        return {
            'label_filename': label_filename,
            'label_path': label_path,
            'label_format': label_format,
            'barcode_info': barcode_info,
            'qr_info': qr_info
        }
    
    @staticmethod
    def _create_asset_label(asset: Asset, barcode_info: Dict, qr_info: Dict, label_format: str) -> Image.Image:
        """Create comprehensive asset label"""
        # Load barcode and QR code images
        barcode_image = Image.open(barcode_info['barcode_path'])
        qr_image = Image.open(qr_info['qr_path'])
        
        # Create label canvas
        if label_format == 'standard':
            label_width = 400
            label_height = 300
        elif label_format == 'compact':
            label_width = 300
            label_height = 200
        else:  # detailed
            label_width = 500
            label_height = 400
        
        label = Image.new('RGB', (label_width, label_height), 'white')
        draw = ImageDraw.Draw(label)
        
        try:
            font_title = ImageFont.truetype("arial.ttf", 16)
            font_text = ImageFont.truetype("arial.ttf", 12)
        except:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
        
        # Add asset information
        y_offset = 10
        
        # Title
        draw.text((10, y_offset), f"Asset: {asset.name}", fill='black', font=font_title)
        y_offset += 25
        
        # Asset details
        details = [
            f"ID: {asset.id}",
            f"Tag: {asset.asset_tag or 'N/A'}",
            f"Category: {asset.category or 'N/A'}",
            f"Status: {asset.status}"
        ]
        
        for detail in details:
            draw.text((10, y_offset), detail, fill='black', font=font_text)
            y_offset += 15
        
        # Add barcode
        y_offset += 10
        barcode_resized = barcode_image.resize((200, 60), Image.Resampling.LANCZOS)
        label.paste(barcode_resized, (10, y_offset))
        
        # Add QR code
        qr_resized = qr_image.resize((80, 80), Image.Resampling.LANCZOS)
        label.paste(qr_resized, (250, y_offset))
        
        # Add generation date
        y_offset += 70
        draw.text((10, y_offset), f"Generated: {datetime.utcnow().strftime('%Y-%m-%d')}", fill='gray', font=font_text)
        
        return label
