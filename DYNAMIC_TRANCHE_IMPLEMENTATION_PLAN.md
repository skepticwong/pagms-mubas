# 🚀 **Dynamic Tranche Configuration System - Implementation Plan**

## 📊 **Current State Analysis**

### ✅ **Already Implemented:**
- Basic Tranche model with amount, dates, status
- Grant creation with tranche setup
- Milestone-to-tranche linking
- Frontend tranche creation interface

### ❌ **Missing Components:**
- Flexible trigger system (milestone/report/date-based)
- Amendment workflow for post-creation edits
- Business rules enforcement
- Audit trail for changes

---

## 🎯 **Phase 1: Enhanced Tranche Data Model**

### **1.1 Update Tranche Model**
```python
class Tranche(db.Model):
    __tablename__ = 'tranches'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'))
    
    # Basic Info
    tranche_number = db.Column(db.Integer)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    description = db.Column(db.String(200))
    expected_date = db.Column(db.Date, nullable=False)
    
    # NEW: Flexible Triggers
    trigger_type = db.Column(db.String(20), default='milestone') # 'milestone', 'report', 'date', 'manual'
    triggering_milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=True)
    required_report_type = db.Column(db.String(50), nullable=True) # 'financial', 'progress', 'technical'
    trigger_date = db.Column(db.Date, nullable=True) # For date-based triggers
    
    # Status & Release
    status = db.Column(db.String(20), default='pending') # 'pending', 'ready', 'released', 'suspended'
    released_at = db.Column(db.DateTime)
    released_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # NEW: Amendment Tracking
    version = db.Column(db.Integer, default=1)
    parent_tranche_id = db.Column(db.Integer, db.ForeignKey('tranches.id'), nullable=True)
    amendment_reason = db.Column(db.Text, nullable=True)
    amendment_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    amendment_approved_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### **1.2 Add Tranche Amendment Model**
```python
class TrancheAmendment(db.Model):
    __tablename__ = 'tranche_amendments'
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'))
    tranche_id = db.Column(db.Integer, db.ForeignKey('tranches.id'))
    
    # Amendment Details
    amendment_type = db.Column(db.String(20)) # 'amount', 'trigger', 'date', 'delete'
    old_value = db.Column(db.Text) # JSON of old values
    new_value = db.Column(db.Text) # JSON of new values
    reason = db.Column(db.Text, nullable=False)
    
    # Supporting Documents
    supporting_docs = db.Column(db.Text) # JSON array of file paths
    
    # Approval Workflow
    status = db.Column(db.String(20), default='pending') # 'pending', 'approved', 'rejected'
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

---

## 🎯 **Phase 2: Enhanced Frontend Interface**

### **2.1 Tranche Configuration During Grant Setup**
```svelte
<!-- Enhanced tranche setup in CreateGrant.svelte -->
<div class="space-y-4">
    <h4 class="text-sm font-bold text-blue-900 uppercase">Payment Schedule Configuration</h4>
    
    {#each tranches as tranche, i}
        <div class="bg-white p-4 rounded-xl border border-blue-100">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <!-- Basic Info -->
                <div>
                    <label class="block text-xs font-bold text-gray-500">Description</label>
                    <input type="text" bind:value={tranche.description} placeholder="e.g., Initial Mobilization" />
                </div>
                
                <div>
                    <label class="block text-xs font-bold text-gray-500">Amount</label>
                    <input type="number" bind:value={tranche.amount} placeholder="0.00" />
                </div>
                
                <div>
                    <label class="block text-xs font-bold text-gray-500">Expected Date</label>
                    <input type="date" bind:value={tranche.expected_date} />
                </div>
                
                <!-- NEW: Trigger Configuration -->
                <div>
                    <label class="block text-xs font-bold text-gray-500">Release Trigger</label>
                    <select bind:value={tranche.trigger_type}>
                        <option value="milestone">Milestone Completion</option>
                        <option value="report">Report Submission</option>
                        <option value="date">Specific Date</option>
                        <option value="manual">Manual Release</option>
                    </select>
                </div>
            </div>
            
            <!-- Conditional Trigger Fields -->
            {#if tranche.trigger_type === 'milestone'}
                <div class="mt-3">
                    <label class="block text-xs font-bold text-gray-500">Required Milestone</label>
                    <select bind:value={tranche.triggering_milestone_id}>
                        <option value="">Select milestone...</option>
                        {#each availableMilestones as milestone}
                            <option value={milestone.id}>{milestone.title}</option>
                        {/each}
                    </select>
                </div>
            {:else if tranche.trigger_type === 'report'}
                <div class="mt-3">
                    <label class="block text-xs font-bold text-gray-500">Required Report Type</label>
                    <select bind:value={tranche.required_report_type}>
                        <option value="financial">Financial Report</option>
                        <option value="progress">Progress Report</option>
                        <option value="technical">Technical Report</option>
                    </select>
                </div>
            {:else if tranche.trigger_type === 'date'}
                <div class="mt-3">
                    <label class="block text-xs font-bold text-gray-500">Release Date</label>
                    <input type="date" bind:value={tranche.trigger_date} />
                </div>
            {/if}
        </div>
    {/each}
    
    <button type="button" on:click={addTranche} class="text-blue-600 text-sm font-bold">
        + Add Tranche
    </button>
</div>
```

### **2.2 Tranche Amendment Interface**
```svelte
<!-- New TrancheManagement.svelte component -->
<div class="space-y-6">
    <!-- Current Tranches -->
    <div class="bg-white rounded-xl p-6">
        <h3 class="text-lg font-bold mb-4">Current Payment Schedule</h3>
        
        {#each tranches as tranche}
            <div class="border rounded-lg p-4 mb-3">
                <div class="flex justify-between items-start">
                    <div>
                        <h4 class="font-bold">Tranche {tranche.tranche_number}: {tranche.description}</h4>
                        <p class="text-sm text-gray-600">${tranche.amount.toLocaleString()} - {tranche.expected_date}</p>
                        <p class="text-xs text-gray-500">Trigger: {getTriggerDescription(tranche)}</p>
                    </div>
                    
                    <div class="flex gap-2">
                        {#if tranche.status !== 'released'}
                            <button on:click={() => editTranche(tranche)} class="text-blue-600 text-sm">
                                Edit
                            </button>
                        {/if}
                        <button on:click={() => viewHistory(tranche)} class="text-gray-600 text-sm">
                            History
                        </button>
                    </div>
                </div>
            </div>
        {/each}
    </div>
    
    <!-- Amendment Request Form -->
    {#if showAmendmentForm}
        <div class="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
            <h3 class="text-lg font-bold mb-4">Request Tranche Amendment</h3>
            
            <form on:submit={submitAmendment}>
                <div class="space-y-4">
                    <div>
                        <label>Amendment Type</label>
                        <select bind:value={amendment.type}>
                            <option value="amount">Modify Amount</option>
                            <option value="trigger">Change Trigger</option>
                            <option value="date">Change Date</option>
                        </select>
                    </div>
                    
                    <div>
                        <label>Reason for Change</label>
                        <textarea bind:value={amendment.reason} required></textarea>
                    </div>
                    
                    <div>
                        <label>Supporting Documents</label>
                        <input type="file" multiple accept=".pdf,.doc,.docx" />
                    </div>
                    
                    <div class="flex gap-3">
                        <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded">
                            Submit Request
                        </button>
                        <button type="button" on:click={() => showAmendmentForm = false} class="bg-gray-300 px-4 py-2 rounded">
                            Cancel
                        </button>
                    </div>
                </div>
            </form>
        </div>
    {/if}
</div>
```

---

## 🎯 **Phase 3: Business Rules Engine**

### **3.1 Tranche Validation Service**
```python
class TrancheValidationService:
    @staticmethod
    def validate_tranche_amendment(grant_id, tranche_id, amendments):
        """Enforce business rules for tranche modifications"""
        errors = []
        
        # Rule 1: No retroactive unlocking
        if amendments.get('trigger_type') == 'milestone':
            new_milestone_id = amendments.get('triggering_milestone_id')
            milestone = Milestone.query.get(new_milestone_id)
            
            if milestone and milestone.completed_at:
                tranche = Tranche.query.get(tranche_id)
                if tranche.expected_date < milestone.completed_at.date():
                    errors.append("Cannot set retroactive trigger dates")
        
        # Rule 2: Total sum validation
        if amendments.get('amount'):
            new_amount = amendments.get('amount')
            grant = Grant.query.get(grant_id)
            other_tranches = Tranche.query.filter(
                Tranche.grant_id == grant_id,
                Tranche.id != tranche_id,
                Tranche.status != 'released'
            ).all()
            
            total_other = sum(t.amount for t in other_tranches)
            if total_other + new_amount > grant.total_budget:
                errors.append(f"Total tranches ({total_other + new_amount}) exceed grant budget ({grant.total_budget})")
        
        # Rule 3: Released tranches are locked
        tranche = Tranche.query.get(tranche_id)
        if tranche.status == 'released':
            if any(key in amendments for key in ['amount', 'trigger_type', 'triggering_milestone_id']):
                errors.append("Cannot modify amount or trigger for released tranches")
        
        return errors
```

### **3.2 Amendment Approval Workflow**
```python
class TrancheAmendmentService:
    @staticmethod
    def submit_amendment(user_id, grant_id, tranche_id, amendment_data):
        """Submit a tranche amendment for approval"""
        
        # Validate business rules
        errors = TrancheValidationService.validate_tranche_amendment(grant_id, tranche_id, amendment_data)
        if errors:
            return {'success': False, 'errors': errors}
        
        # Create amendment record
        amendment = TrancheAmendment(
            grant_id=grant_id,
            tranche_id=tranche_id,
            amendment_type=amendment_data['type'],
            old_value=json.dumps(get_current_tranche_values(tranche_id)),
            new_value=json.dumps(amendment_data),
            reason=amendment_data['reason'],
            supporting_docs=json.dumps(amendment_data.get('documents', [])),
            requested_by=user_id
        )
        
        db.session.add(amendment)
        
        # Notify RSU/Finance approvers
        NotificationService.notify_tranche_amendment(amendment)
        
        db.session.commit()
        return {'success': True, 'amendment_id': amendment.id}
    
    @staticmethod
    def approve_amendment(approver_id, amendment_id):
        """Approve and apply a tranche amendment"""
        amendment = TrancheAmendment.query.get(amendment_id)
        
        if amendment.status != 'pending':
            return {'success': False, 'error': 'Amendment already processed'}
        
        # Apply changes
        tranche = Tranche.query.get(amendment.tranche_id)
        new_values = json.loads(amendment.new_value)
        
        # Create new version of tranche
        new_tranche = Tranche(
            grant_id=tranche.grant_id,
            tranche_number=tranche.tranche_number,
            parent_tranche_id=tranche.id,
            version=tranche.version + 1,
            **{k: v for k, v in new_values.items() if k in ['amount', 'trigger_type', 'triggering_milestone_id', 'expected_date']}
        )
        
        # Update amendment
        amendment.status = 'approved'
        amendment.approved_by = approver_id
        amendment.approved_at = datetime.utcnow()
        
        # Archive old tranche
        tranche.status = 'archived'
        
        db.session.add(new_tranche)
        db.session.commit()
        
        # Log audit trail
        AuditLog.create(
            user_id=approver_id,
            action='tranche_amendment_approved',
            resource_type='tranche',
            resource_id=new_tranche.id,
            details=f"Tranche {new_tranche.tranche_number} amended: {amendment.reason}"
        )
        
        return {'success': True, 'new_tranche_id': new_tranche.id}
```

---

## 🎯 **Phase 4: API Endpoints**

### **4.1 Tranche Management Endpoints**
```python
@tranches_bp.route('/grants/<int:grant_id>/tranches', methods=['GET'])
def get_tranches(grant_id):
    """Get all tranches for a grant with amendment history"""
    tranches = Tranche.query.filter_by(grant_id=grant_id, status='active').all()
    return jsonify([t.to_dict(include_amendments=True) for t in tranches])

@tranches_bp.route('/tranches/<int:tranche_id>/amendments', methods=['POST'])
def submit_amendment(tranche_id):
    """Submit a tranche amendment request"""
    data = request.get_json()
    result = TrancheAmendmentService.submit_amendment(
        user_id=session['user_id'],
        tranche_id=tranche_id,
        amendment_data=data
    )
    return jsonify(result)

@tranches_bp.route('/amendments/<int:amendment_id>/approve', methods=['POST'])
def approve_amendment(amendment_id):
    """Approve a tranche amendment"""
    result = TrancheAmendmentService.approve_amendment(
        approver_id=session['user_id'],
        amendment_id=amendment_id
    )
    return jsonify(result)
```

---

## 🎯 **Implementation Timeline**

### **Week 1: Data Model Enhancement**
- Update Tranche model with new fields
- Create TrancheAmendment model
- Add database migrations

### **Week 2: Frontend Enhancement**  
- Enhance grant creation interface
- Build tranche management component
- Add amendment request forms

### **Week 3: Business Rules & API**
- Implement validation service
- Build amendment workflow
- Create API endpoints

### **Week 4: Testing & Deployment**
- Unit tests for business rules
- Integration testing
- User acceptance testing

---

## 🎯 **Success Criteria**

✅ **Flexible Triggers**: Support milestone, report, date, and manual triggers
✅ **Amendment Workflow**: Complete request → approve → apply process  
✅ **Business Rules**: Prevent retroactive changes and budget overruns
✅ **Audit Trail**: Complete history of all tranche modifications
✅ **User Experience**: Intuitive interface for PI and RSU users

**This implementation will transform the static tranche system into a dynamic, enterprise-grade payment schedule management system!** 🚀
