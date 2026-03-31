# Asset & Equipment Management Implementation Plan
## PAGMS - Post-Award Grant Management System

---

## 🎯 **Executive Summary**

This implementation plan outlines a comprehensive **Asset & Equipment Management System** for PAGMS that tracks every piece of equipment used in grant-funded projects. The system handles three distinct sources: **Grant-Purchased**, **University-Owned**, and **Lended/Borrowed** assets, ensuring full audit compliance and liability management.

---

## 📋 **Table of Contents**

1. [Scope & Requirements](#-scope--requirements)
2. [System Architecture](#-system-architecture)
3. [Database Design](#-database-design)
4. [Backend Implementation](#-backend-implementation)
5. [Frontend Implementation](#-frontend-implementation)
6. [Rules Engine Integration](#-rules-engine-integration)
7. [User Interface Design](#-user-interface-design)
8. [Implementation Phases](#-implementation-phases)
9. [Testing Strategy](#-testing-strategy)
10. [Rollout Plan](#-rollout-plan)

---

## 🔍 **Scope & Requirements**

### **What We Track**
**The Golden Rule:** If an item is used for the project, it gets an **Asset Record**.

| Source Type | Description | Tracking Goal |
|-------------|-------------|---------------|
| **Grant-Purchased** | Bought with grant funds (Laptop, Microscope) | **Audit:** Prove existence, prevent private sale, ensure proper disposal |
| **University-Owned** | Existing uni asset assigned to grant (Vehicle, Lab Space) | **Costing:** Calculate depreciation/use-costs, ensure return to pool |
| **Lended/External** | Borrowed from partners, NGOs, other departments | **Liability:** Ensure timely return to avoid penalties |

### **Key Requirements**
- ✅ **Full Lifecycle Tracking** - From acquisition to disposal
- ✅ **Multi-Source Management** - Handle all three asset sources
- ✅ **Audit Compliance** - Complete audit trail for all assets
- ✅ **Closeout Enforcement** - Cannot close grant with unaccounted assets
- ✅ **Rules Integration** - Smart procurement and usage rules
- ✅ **Alert System** - Return deadlines, maintenance reminders

---

## 🏗️ **System Architecture**

### **Component Overview**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI   │    │  Backend API    │    │   Database      │
│                 │    │                 │    │                 │
│ • Asset Dashboard│◄──►│ • Asset Service │◄──►│ • Assets Table  │
│ • Request Modal  │    │ • Rules Engine  │    │ • Tasks Link    │
│ • Closeout Gate  │    │ • Alert System  │    │ • Expenses Link │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Integration Points**
- **Tasks System** - Asset requests linked to specific tasks
- **Expenses System** - Purchased assets linked to expense records
- **Rules Engine** - Smart procurement and usage validation
- **Alert System** - Return deadlines and compliance notifications
- **Grant Management** - Closeout enforcement and asset disposition

---

## 🗄️ **Database Design**

### **Core Asset Table**

```python
class Asset(db.Model):
    __tablename__ = 'assets'
    
    # Primary Identification
    id = db.Column(db.Integer, primary_key=True)
    asset_tag = db.Column(db.String(50), unique=True)  # Internal ID
    serial_number = db.Column(db.String(100))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # 'Vehicle', 'IT', 'Lab Equipment'
    
    # Grant Context
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    grant = db.relationship('Grant', backref='assets')
    
    # Source & Ownership
    source_type = db.Column(db.String(20), nullable=False)  # 'PURCHASED', 'LENDED', 'UNIVERSITY_OWNED'
    owner_name = db.Column(db.String(200))  # "MUBAS", "Ministry of Health", "USAID"
    lending_agreement = db.Column(db.Text)  # Details of lending arrangement
    
    # Financial Information
    purchase_cost = db.Column(db.Float, default=0.0)
    linked_expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'))
    rental_fee_total = db.Column(db.Float, default=0.0)
    depreciation_value = db.Column(db.Float, default=0.0)
    
    # Lifecycle Management
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, IN_REPAIR, LOST, RETURNED, TRANSFERRED, DISPOSED
    custodian_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    custodian = db.relationship('User', foreign_keys=[custodian_user_id])
    assigned_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    assigned_task = db.relationship('Task')
    
    # Important Dates
    acquisition_date = db.Column(db.Date)
    expected_return_date = db.Column(db.Date)  # Critical for LENDED items
    actual_return_date = db.Column(db.Date)
    last_maintenance_date = db.Column(db.Date)
    next_maintenance_date = db.Column(db.Date)
    
    # Disposition (Closeout)
    disposition_method = db.Column(db.String(50))  # 'Transfer to Uni', 'Return to Donor', 'Sold', 'Destroyed'
    disposition_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    disposition_approver = db.relationship('User', foreign_keys=[disposition_approved_by])
    disposition_date = db.Column(db.Date)
    disposition_notes = db.Column(db.Text)
    
    # Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Documents & Attachments
    supporting_documents = db.Column(db.JSON)  # Receipts, agreements, photos
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_tag': self.asset_tag,
            'serial_number': self.serial_number,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'grant_id': self.grant_id,
            'source_type': self.source_type,
            'owner_name': self.owner_name,
            'purchase_cost': self.purchase_cost,
            'rental_fee_total': self.rental_fee_total,
            'status': self.status,
            'custodian': self.custodian.to_dict() if self.custodian else None,
            'assigned_task': self.assigned_task.to_dict() if self.assigned_task else None,
            'acquisition_date': self.acquisition_date.isoformat() if self.acquisition_date else None,
            'expected_return_date': self.expected_return_date.isoformat() if self.expected_return_date else None,
            'actual_return_date': self.actual_return_date.isoformat() if self.actual_return_date else None,
            'disposition_method': self.disposition_method,
            'supporting_documents': self.supporting_documents
        }
```

### **Supporting Tables**

```python
# Asset Maintenance Records
class AssetMaintenance(db.Model):
    __tablename__ = 'asset_maintenance'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    maintenance_type = db.Column(db.String(50))  # 'Scheduled', 'Repair', 'Inspection'
    description = db.Column(db.Text)
    cost = db.Column(db.Float, default=0.0)
    performed_by = db.Column(db.String(200))
    performed_date = db.Column(db.Date)
    next_due_date = db.Column(db.Date)
    notes = db.Column(db.Text)

# Asset Transfer Records
class AssetTransfer(db.Model):
    __tablename__ = 'asset_transfers'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    transfer_date = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(db.Text)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
```

---

## ⚙️ **Backend Implementation**

### **1. Asset Service (`services/asset_service.py`)**

```python
class AssetService:
    
    @staticmethod
    def create_asset_request(task_id, request_data, user_id):
        """Create new asset request from task"""
        task = Task.query.get(task_id)
        if not task:
            raise ValueError("Task not found")
        
        asset = Asset(
            grant_id=task.grant_id,
            name=request_data['name'],
            description=request_data.get('description', ''),
            category=request_data.get('category', 'Equipment'),
            source_type=request_data['source_type'],  # PURCHASED, LENDED, UNIVERSITY_OWNED
            owner_name=request_data.get('owner_name'),
            custodian_user_id=user_id,
            assigned_task_id=task_id,
            acquisition_date=datetime.utcnow().date(),
            created_by_user_id=user_id
        )
        
        # Handle different source types
        if request_data['source_type'] == 'PURCHASED':
            asset.purchase_cost = request_data.get('estimated_cost', 0)
            # Trigger expense workflow
            AssetService._create_purchase_expense(asset, request_data, user_id)
            
        elif request_data['source_type'] == 'LENDED':
            asset.expected_return_date = request_data['return_date']
            asset.rental_fee_total = request_data.get('rental_fee', 0)
            # Schedule return reminders
            AssetService._schedule_return_reminders(asset)
        
        db.session.add(asset)
        db.session.commit()
        
        # Apply rules engine
        rule_result = RuleService.evaluate_action('ASSET_ACQUISITION', {
            'category': asset.category,
            'source_type': asset.source_type,
            'cost': asset.purchase_cost,
            'rental_fee': asset.rental_fee_total
        }, task.grant_id)
        
        return asset, rule_result
    
    @staticmethod
    def update_asset_status(asset_id, new_status, user_id, notes=None):
        """Update asset status with audit trail"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")
        
        old_status = asset.status
        asset.status = new_status
        asset.updated_at = datetime.utcnow()
        
        # Handle specific status changes
        if new_status == 'RETURNED':
            asset.actual_return_date = datetime.utcnow().date()
            # Clear custodian
            asset.custodian_user_id = None
            asset.assigned_task_id = None
            
        elif new_status == 'TRANSFERRED':
            asset.disposition_date = datetime.utcnow().date()
            asset.disposition_approved_by = user_id
            
        # Create transfer record if changing custodian
        if old_status != new_status and asset.custodian_user_id != user_id:
            transfer = AssetTransfer(
                asset_id=asset_id,
                from_user_id=asset.custodian_user_id,
                to_user_id=user_id,
                reason=notes or f"Status change: {old_status} → {new_status}"
            )
            db.session.add(transfer)
        
        db.session.commit()
        return asset
    
    @staticmethod
    def get_grant_assets(grant_id, status_filter=None):
        """Get all assets for a grant with optional status filter"""
        query = Asset.query.filter_by(grant_id=grant_id)
        if status_filter:
            query = query.filter_by(status=status_filter)
        return query.all()
    
    @staticmethod
    def check_closeout_compliance(grant_id):
        """Check if all assets are properly disposed for grant closeout"""
        active_assets = Asset.query.filter(
            Asset.grant_id == grant_id,
            Asset.status.in_(['ACTIVE', 'IN_REPAIR'])
        ).count()
        
        if active_assets > 0:
            return {
                'compliant': False,
                'message': f'{active_assets} assets still need disposition',
                'assets': AssetService.get_grant_assets(grant_id, 'ACTIVE')
            }
        
        return {'compliant': True, 'message': 'All assets properly disposed'}
```

### **2. Asset Routes (`routes/assets.py`)**

```python
assets_bp = Blueprint('assets', __name__)

@assets_bp.route('/assets/request', methods=['POST'])
@token_required
def request_asset(user):
    """Request new asset from task"""
    data = request.get_json()
    
    try:
        asset, rule_result = AssetService.create_asset_request(
            data['task_id'], data, user.id
        )
        
        # Handle rule outcomes
        if rule_result['outcome'] == 'BLOCK':
            return jsonify({
                'error': 'Asset request blocked',
                'reasons': rule_result['block_reasons']
            }), 403
        elif rule_result['outcome'] == 'PRIOR_APPROVAL':
            return jsonify({
                'message': 'Asset request requires prior approval',
                'asset': asset.to_dict(),
                'approvals_needed': rule_result['prior_approval_reasons']
            }), 202
        
        return jsonify({
            'message': 'Asset request created',
            'asset': asset.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to create asset request'}), 500

@assets_bp.route('/assets/grant/<int:grant_id>', methods=['GET'])
@token_required
def get_grant_assets(user, grant_id):
    """Get all assets for a grant"""
    assets = AssetService.get_grant_assets(grant_id)
    return jsonify({
        'assets': [asset.to_dict() for asset in assets]
    }), 200

@assets_bp.route('/assets/<int:asset_id>/status', methods=['PUT'])
@token_required
def update_asset_status(user, asset_id):
    """Update asset status"""
    data = request.get_json()
    
    try:
        asset = AssetService.update_asset_status(
            asset_id, data['status'], user.id, data.get('notes')
        )
        return jsonify({'asset': asset.to_dict()}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@assets_bp.route('/assets/closeout-check/<int:grant_id>', methods=['GET'])
@token_required
def check_closeout_compliance(user, grant_id):
    """Check asset compliance for grant closeout"""
    compliance = AssetService.check_closeout_compliance(grant_id)
    return jsonify(compliance), 200
```

---

## 🎨 **Frontend Implementation**

### **1. Navigation Integration**

Add to main navigation:
```javascript
// src/components/Navigation.svelte
const navItems = [
  // ... existing items
  {
    title: 'Asset Management',
    icon: 'package',
    path: '/assets',
    roles: ['PI', 'Team', 'RSU', 'Finance']
  }
];
```

### **2. Asset Dashboard Component**

```svelte
<!-- src/components/AssetDashboard.svelte -->
<script>
  import { onMount } from 'svelte';
  import { showToast } from '../stores/toast.js';
  
  export let grantId = null;
  
  let assets = [];
  let loading = true;
  let showRequestModal = false;
  let selectedAsset = null;
  
  onMount(async () => {
    await loadAssets();
  });
  
  async function loadAssets() {
    try {
      const response = await fetch(`/api/assets/grant/${grantId}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        assets = data.assets;
      }
    } catch (error) {
      showToast('Failed to load assets', 'error');
    } finally {
      loading = false;
    }
  }
  
  function getStatusColor(status) {
    switch (status) {
      case 'ACTIVE': return 'text-green-600 bg-green-100';
      case 'LENDED': return 'text-blue-600 bg-blue-100';
      case 'RETURNED': return 'text-gray-600 bg-gray-100';
      case 'IN_REPAIR': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  }
  
  function getDaysUntilReturn(returnDate) {
    if (!returnDate) return null;
    const days = Math.ceil((new Date(returnDate) - new Date()) / (1000 * 60 * 60 * 24));
    return days;
  }
</script>

<div class="asset-dashboard">
  <div class="flex justify-between items-center mb-6">
    <h2 class="text-2xl font-bold">Asset Management</h2>
    <button 
      on:click={() => showRequestModal = true}
      class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
    >
      Request Asset
    </button>
  </div>
  
  {#if loading}
    <div class="text-center py-8">
      <div class="animate-spin h-8 w-8 mx-auto"></div>
      <p class="mt-2">Loading assets...</p>
    </div>
  {:else if assets.length === 0}
    <div class="text-center py-8">
      <svg class="h-12 w-12 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
      </svg>
      <p class="text-gray-500 mt-2">No assets registered for this grant</p>
    </div>
  {:else}
    <div class="bg-white rounded-lg shadow overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Asset</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Custodian</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Return Date</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          {#each assets as asset}
            <tr>
              <td class="px-6 py-4 whitespace-nowrap">
                <div>
                  <div class="text-sm font-medium text-gray-900">{asset.name}</div>
                  <div class="text-sm text-gray-500">Tag: {asset.asset_tag || 'N/A'}</div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{asset.source_type}</div>
                <div class="text-sm text-gray-500">{asset.owner_name || 'N/A'}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {asset.custodian ? asset.custodian.name : 'Unassigned'}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full {getStatusColor(asset.status)}">
                  {asset.status}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {#if asset.expected_return_date}
                  {@const daysUntil = getDaysUntilReturn(asset.expected_return_date)}
                  {#if daysUntil <= 0}
                    <span class="text-red-600 font-medium">Overdue</span>
                  {:else if daysUntil <= 7}
                    <span class="text-yellow-600 font-medium">{daysUntil} days</span>
                  {:else}
                    {asset.expected_return_date}
                  {/if}
                {:else}
                  N/A
                {/if}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button 
                  on:click={() => selectedAsset = asset}
                  class="text-blue-600 hover:text-blue-900 mr-3"
                >
                  View
                </button>
                {#if asset.status === 'ACTIVE'}
                  <button class="text-green-600 hover:text-green-900">
                    Return
                  </button>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
  
  <!-- Asset Request Modal -->
  {#if showRequestModal}
    <AssetRequestModal 
      show={showRequestModal}
      grantId={grantId}
      on:close={() => showRequestModal = false}
      on:submitted={() => {
        showRequestModal = false;
        loadAssets();
        showToast('Asset request submitted successfully!');
      }}
    />
  {/if}
</div>
```

### **3. Asset Request Modal**

```svelte
<!-- src/components/AssetRequestModal.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';
  import { showToast } from '../stores/toast.js';
  
  const dispatch = createEventDispatcher();
  
  export let show = false;
  export let grantId = null;
  
  let formData = {
    task_id: '',
    name: '',
    description: '',
    category: 'Equipment',
    source_type: 'PURCHASED',
    owner_name: '',
    estimated_cost: 0,
    return_date: '',
    rental_fee: 0,
    supporting_docs: []
  };
  
  let tasks = [];
  let loading = false;
  let errors = [];
  
  async function submitRequest() {
    errors = [];
    loading = true;
    
    try {
      const response = await fetch('/api/assets/request', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });
      
      const result = await response.json();
      
      if (response.ok) {
        dispatch('submitted', { asset: result.asset });
      } else {
        errors = [result.error || 'Failed to submit request'];
      }
    } catch (error) {
      errors = ['Network error. Please try again.'];
    } finally {
      loading = false;
    }
  }
</script>

{#if show}
  <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
      <div class="mt-3">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Request Asset</h3>
        
        <form on:submit|preventDefault={submitRequest}>
          <!-- Task Selection -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">Task</label>
            <select bind:value={formData.task_id} required class="w-full border rounded px-3 py-2">
              <option value="">Select a task...</option>
              {#each tasks as task}
                <option value={task.id}>{task.title}</option>
              {/each}
            </select>
          </div>
          
          <!-- Asset Details -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">Asset Name</label>
            <input 
              type="text" 
              bind:value={formData.name} 
              required 
              class="w-full border rounded px-3 py-2"
              placeholder="e.g., Dell Laptop, Soil Testing Kit"
            />
          </div>
          
          <!-- Source Type -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">Source Type</label>
            <select bind:value={formData.source_type} required class="w-full border rounded px-3 py-2">
              <option value="PURCHASED">Purchase New</option>
              <option value="LENDED">Lend/Rent External</option>
              <option value="UNIVERSITY_OWNED">Use University Asset</option>
            </select>
          </div>
          
          <!-- Conditional Fields -->
          {#if formData.source_type === 'PURCHASED'}
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">Estimated Cost</label>
              <input 
                type="number" 
                bind:value={formData.estimated_cost} 
                step="0.01"
                class="w-full border rounded px-3 py-2"
                placeholder="0.00"
              />
            </div>
          {:else if formData.source_type === 'LENDED'}
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">Owner/Lender Name</label>
              <input 
                type="text" 
                bind:value={formData.owner_name} 
                required
                class="w-full border rounded px-3 py-2"
                placeholder="e.g., Ministry of Agriculture"
              />
            </div>
            
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">Return Date</label>
              <input 
                type="date" 
                bind:value={formData.return_date} 
                required
                class="w-full border rounded px-3 py-2"
              />
            </div>
            
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">Rental Fee (if any)</label>
              <input 
                type="number" 
                bind:value={formData.rental_fee} 
                step="0.01"
                class="w-full border rounded px-3 py-2"
                placeholder="0.00"
              />
            </div>
          {:else if formData.source_type === 'UNIVERSITY_OWNED'}
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">University Asset Description</label>
              <input 
                type="text" 
                bind:value={formData.owner_name} 
                required
                class="w-full border rounded px-3 py-2"
                placeholder="e.g., University Truck #4, Lab Room 201"
              />
            </div>
          {/if}
          
          <!-- Description -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">Description/Justification</label>
            <textarea 
              bind:value={formData.description} 
              rows="3"
              class="w-full border rounded px-3 py-2"
              placeholder="Why is this asset needed for the task?"
            ></textarea>
          </div>
          
          <!-- Errors -->
          {#if errors.length > 0}
            <div class="mb-4 p-3 bg-red-50 border border-red-200 rounded">
              {#each errors as error}
                <p class="text-red-600 text-sm">{error}</p>
              {/each}
            </div>
          {/if}
          
          <!-- Actions -->
          <div class="flex justify-end space-x-3">
            <button 
              type="button" 
              on:click={() => dispatch('close')}
              class="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              disabled={loading}
              class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Submitting...' : 'Submit Request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
{/if}
```

---

## ⚡ **Rules Engine Integration**

### **Asset-Specific Rules**

```python
# Add to rules.py or create asset_rules.py

ASSET_RULES = [
    {
        'name': 'High-Value Procurement Threshold',
        'category': 'procurement',
        'logic_config': {
            'field': 'purchase_cost',
            'operator': 'greater_than',
            'value': 5000,
            'applies_to': 'equipment'
        },
        'outcome': 'PRIOR_APPROVAL',
        'guidance_text': 'Equipment purchases over $5,000 require prior approval from RSU',
        'priority_level': 2
    },
    {
        'name': 'Unallowable Equipment Categories',
        'category': 'procurement',
        'logic_config': {
            'field': 'category',
            'operator': 'in_list',
            'value': ['Luxury Vehicle', 'Entertainment', 'Personal Use']
        },
        'outcome': 'BLOCK',
        'guidance_text': 'This equipment category is not allowable under grant terms',
        'priority_level': 1
    },
    {
        'name': 'Rental vs Purchase Analysis',
        'category': 'cost_effectiveness',
        'logic_config': {
            'field': 'rental_fee_total',
            'operator': 'greater_than',
            'value': 1000
        },
        'outcome': 'WARN',
        'guidance_text': 'Consider purchasing instead of renting for long-term cost savings',
        'priority_level': 3
    },
    {
        'name': 'Asset Closeout Compliance',
        'category': 'closeout',
        'logic_config': {
            'field': 'status',
            'operator': 'not_in_list',
            'value': ['RETURNED', 'TRANSFERRED', 'DISPOSED']
        },
        'outcome': 'BLOCK',
        'guidance_text': 'Cannot close grant until all assets are properly disposed',
        'priority_level': 1
    }
]
```

---

## 📅 **Implementation Phases**

### **Phase 1: Foundation (Week 1-2)**
- ✅ **Database Schema** - Create Asset, AssetMaintenance, AssetTransfer tables
- ✅ **Basic Asset Service** - CRUD operations for assets
- ✅ **Asset Routes** - Basic API endpoints
- ✅ **Navigation Integration** - Add Asset Management to main nav

### **Phase 2: Core Workflows (Week 3-4)**
- ✅ **Asset Request Modal** - Integration with Tasks
- ✅ **Source Type Handling** - Purchase, Lend, University workflows
- ✅ **Rules Engine Integration** - Asset-specific rules
- ✅ **Basic Dashboard** - Asset listing and status tracking

### **Phase 3: Advanced Features (Week 5-6)**
- ✅ **Maintenance Tracking** - Service records and reminders
- ✅ **Transfer Management** - Custodian changes and audit trail
- ✅ **Alert System** - Return deadlines, maintenance reminders
- ✅ **Document Management** - Receipts, agreements, photos

### **Phase 4: Closeout Integration (Week 7)**
- ✅ **Closeout Gates** - Asset compliance checking
- ✅ **Disposition Workflows** - Transfer, return, disposal processes
- ✅ **Reporting** - Asset audit reports
- ✅ **Testing & Rollout** - User training and deployment

---

## 🧪 **Testing Strategy**

### **Unit Tests**
- Asset Service CRUD operations
- Rules Engine evaluation for asset scenarios
- Status change workflows
- Closeout compliance checking

### **Integration Tests**
- Asset request → Expense workflow integration
- Task → Asset assignment linkage
- Rules enforcement during asset creation
- Closeout prevention with active assets

### **User Acceptance Tests**
- PI can request assets from tasks
- Finance can approve high-value purchases
- RSU can track all grant assets
- Closeout process requires asset disposition

### **Performance Tests**
- Large asset registers (1000+ assets)
- Concurrent asset requests
- Rules engine evaluation speed
- Dashboard loading performance

---

## 🚀 **Rollout Plan**

### **Pre-Launch**
1. **Data Migration** - Import existing asset records if any
2. **User Training** - PI, Finance, RSU training sessions
3. **Documentation** - User guides and SOPs
4. **Rules Configuration** - Set up funder-specific asset rules

### **Launch Phase**
1. **Pilot Testing** - Start with 2-3 active grants
2. **Feedback Collection** - User experience and workflow feedback
3. **Bug Fixes** - Address any issues found during pilot
4. **Feature Refinement** - Adjust based on user feedback

### **Full Rollout**
1. **All Grants** - Enable for all active grants
2. **Monitoring** - Track usage and compliance
3. **Continuous Improvement** - Regular updates and enhancements
4. **Audit Preparation** - Ensure full audit trail compliance

---

## 📊 **Success Metrics**

### **Compliance Metrics**
- ✅ **100% Asset Registration** - All grant assets tracked
- ✅ **Zero Audit Findings** - No asset-related audit issues
- ✅ **Timely Returns** - 95% of lended assets returned on time

### **User Adoption**
- ✅ **90% Task Integration** - Assets requested from tasks
- ✅ **85% Rule Compliance** - Users follow asset rules
- ✅ **Positive Feedback** - User satisfaction > 4/5

### **Operational Efficiency**
- ✅ **50% Faster Asset Tracking** - vs manual processes
- ✅ **Automated Compliance** - Reduced manual checking
- ✅ **Real-time Visibility** - RSU can see all assets instantly

---

## 🎯 **Conclusion**

This comprehensive Asset & Equipment Management system will:

1. **Eliminate Audit Risk** - Complete tracking of all grant assets
2. **Improve Compliance** - Automated rules and closeout enforcement
3. **Enhance Visibility** - Real-time asset status for all stakeholders
4. **Streamline Workflows** - Integrated with existing tasks and expenses
5. **Reduce Liability** - Proactive return deadline management

The system integrates seamlessly with existing PAGMS components while adding powerful new capabilities for asset lifecycle management. The phased approach ensures successful implementation with minimal disruption to ongoing operations.

**Implementation Timeline: 7 weeks**
**Development Effort: Medium-High**
**User Impact: High**
**Audit Value: Very High**
