<script>
    import { onMount } from "svelte";
    import axios from "axios";
    import { showToast } from "../stores/toast.js";
    import Icon from "./Icon.svelte";

    export let grantId;
    export let grantTitle;

    let tranches = [];
    let isLoading = true;
    let showAmendmentForm = false;
    let showHistoryModal = false;
    let selectedTranche = null;
    let amendmentHistory = [];
    
    // Amendment form state
    let amendment = {
        type: 'amount',
        reason: '',
        newAmount: 0,
        newTriggerType: 'milestone',
        newMilestoneId: '',
        newReportType: '',
        newDate: '',
        documents: []
    };

    onMount(() => {
        loadTranches();
    });

    async function loadTranches() {
        isLoading = true;
        try {
            const res = await axios.get(`http://localhost:5000/api/grants/${grantId}/tranches`, {
                withCredentials: true
            });
            tranches = res.data;
        } catch (err) {
            console.error("Failed to load tranches:", err);
        } finally {
            isLoading = false;
        }
    }

    function editTranche(tranche) {
        selectedTranche = tranche;
        amendment = {
            type: 'amount',
            reason: '',
            newAmount: tranche.amount,
            newTriggerType: tranche.trigger_type,
            newMilestoneId: tranche.triggering_milestone_id || '',
            newReportType: tranche.required_report_type || '',
            newDate: tranche.trigger_date || '',
            documents: []
        };
        showAmendmentForm = true;
    }

    async function submitAmendment() {
        try {
            const amendmentData = {
                type: amendment.type,
                reason: amendment.reason
            };

            // Add specific changes based on type
            if (amendment.type === 'amount') {
                amendmentData.amount = amendment.newAmount;
            } else if (amendment.type === 'trigger') {
                amendmentData.trigger_type = amendment.newTriggerType;
                if (amendment.newTriggerType === 'milestone') {
                    amendmentData.triggering_milestone_id = amendment.newMilestoneId;
                } else if (amendment.newTriggerType === 'report') {
                    amendmentData.required_report_type = amendment.newReportType;
                } else if (amendment.newTriggerType === 'date') {
                    amendmentData.trigger_date = amendment.newDate;
                }
            }

            const res = await axios.post(
                `http://localhost:5000/api/tranches/${selectedTranche.id}/amendments`,
                amendmentData,
                { withCredentials: true }
            );

            if (res.data.success) {
                showAmendmentForm = false;
                await loadTranches();
                showToast('Amendment request submitted successfully!', 'success');
            } else {
                showToast('Failed to submit amendment: ' + res.data.errors.join(', '), 'error');
            }
        } catch (err) {
            console.error("Failed to submit amendment:", err);
            showToast('Failed to submit amendment. Please try again.', 'error');
        }
    }

    async function viewHistory(tranche) {
        selectedTranche = tranche;
        try {
            const res = await axios.get(
                `http://localhost:5000/api/tranches/${tranche.id}/amendments`,
                { withCredentials: true }
            );
            amendmentHistory = res.data;
            showHistoryModal = true;
        } catch (err) {
            console.error("Failed to load amendment history:", err);
        }
    }

    function getTriggerDescription(tranche) {
        switch (tranche.trigger_type) {
            case 'milestone':
                return tranche.triggering_milestone 
                    ? `Milestone: ${tranche.triggering_milestone.title}` 
                    : 'No milestone assigned';
            case 'report':
                return `Report: ${tranche.required_report_type || 'Not specified'}`;
            case 'date':
                return `Date: ${formatDate(tranche.trigger_date)}`;
            case 'manual':
                return 'Manual release by RSU/Finance';
            default:
                return 'Not configured';
        }
    }

    function formatDate(dateString) {
        if (!dateString) return 'Not set';
        return new Date(dateString).toLocaleDateString('en-GB', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });
    }

    function getStatusBadge(status) {
        switch (status) {
            case 'pending':
                return 'bg-gray-100 text-gray-700';
            case 'ready':
                return 'bg-emerald-100 text-emerald-700';
            case 'released':
                return 'bg-blue-100 text-blue-700';
            case 'suspended':
                return 'bg-amber-100 text-amber-700';
            case 'archived':
                return 'bg-red-100 text-red-700';
            default:
                return 'bg-gray-100 text-gray-700';
        }
    }
</script>

<div class="space-y-6">
    <!-- Header -->
    <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-lg font-bold text-gray-900 flex items-center gap-2">
                    <Icon name="money" size={20} class="text-blue-600" />
                    Payment Schedule Management
                </h2>
                <p class="text-sm text-gray-600 mt-1">
                    Grant: {grantTitle}
                </p>
            </div>
            <div class="text-right">
                <p class="text-xs text-gray-500">Total Tranches</p>
                <p class="text-2xl font-bold text-blue-600">{tranches.length}</p>
            </div>
        </div>
    </div>

    <!-- Loading State -->
    {#if isLoading}
        <div class="flex flex-col items-center justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
            <p class="text-xs text-gray-500 font-medium">Loading payment schedule...</p>
        </div>
    {:else if tranches.length === 0}
        <div class="bg-yellow-50 border border-yellow-200 rounded-xl p-6 text-center">
            <Icon name="money" size={48} class="text-yellow-600 mx-auto mb-3" />
            <h3 class="text-lg font-bold text-yellow-800 mb-2">No Payment Schedule Configured</h3>
            <p class="text-sm text-yellow-600">This grant doesn't have any tranches set up yet.</p>
        </div>
    {:else}
        <!-- Tranches List -->
        <div class="space-y-4">
            {#each tranches as tranche}
                <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <!-- Tranche Header -->
                    <div class="p-4 border-b border-gray-100">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-3">
                                <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                                    <span class="text-sm font-bold text-blue-600">{tranche.tranche_number}</span>
                                </div>
                                <div>
                                    <h3 class="font-bold text-gray-900">
                                        {tranche.description || `Tranche ${tranche.tranche_number}`}
                                    </h3>
                                    <p class="text-sm text-gray-600">
                                        ${tranche.amount.toLocaleString()} • Due: {formatDate(tranche.expected_date)}
                                    </p>
                                </div>
                            </div>
                            
                            <div class="flex items-center gap-3">
                                <span class="px-3 py-1 rounded-full text-xs font-medium {getStatusBadge(tranche.status)}">
                                    {tranche.status.replace('_', ' ').toUpperCase()}
                                </span>
                                
                                <div class="flex gap-2">
                                    {#if tranche.status !== 'released'}
                                        <button 
                                            on:click={() => editTranche(tranche)}
                                            class="px-3 py-1.5 bg-blue-50 text-blue-600 text-xs font-medium rounded-lg hover:bg-blue-100 transition-colors flex items-center gap-1"
                                        >
                                            <Icon name="edit" size={12} />
                                            Edit
                                        </button>
                                    {/if}
                                    <button 
                                        on:click={() => viewHistory(tranche)}
                                        class="px-3 py-1.5 bg-gray-50 text-gray-600 text-xs font-medium rounded-lg hover:bg-gray-100 transition-colors flex items-center gap-1"
                                    >
                                        <Icon name="info" size={12} />
                                        History
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Trigger Information -->
                        <div class="mt-3 flex items-center gap-2 text-sm">
                            <Icon name="setting" size={16} class="text-gray-500" />
                            <span class="text-gray-600">Trigger:</span>
                            <span class="font-medium text-gray-900">{getTriggerDescription(tranche)}</span>
                        </div>
                    </div>
                    
                    <!-- Release Information -->
                    {#if tranche.released_at}
                        <div class="px-4 py-3 bg-emerald-50 border-t border-emerald-100">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                    <Icon name="check" size={16} class="text-emerald-600" />
                                    <span class="text-sm font-medium text-emerald-700">Released</span>
                                </div>
                                <div class="text-right">
                                    <p class="text-xs text-emerald-600">
                                        {formatDate(tranche.released_at)}
                                    </p>
                                    {#if tranche.released_by_user}
                                        <p class="text-xs text-emerald-500">
                                            by {tranche.released_by_user.name}
                                        </p>
                                    {/if}
                                </div>
                            </div>
                        </div>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}
</div>

<!-- Amendment Request Modal -->
{#if showAmendmentForm && selectedTranche}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm">
    <div class="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-xl bg-blue-100 flex items-center justify-center">
                    <Icon name="setting" size={16} class="text-blue-600" />
                </div>
                <h3 class="text-lg font-bold text-gray-900">Request Tranche Amendment</h3>
            </div>
            <button on:click={() => showAmendmentForm = false} class="text-gray-400 hover:text-gray-600 p-1 hover:bg-gray-100 rounded-lg">
                <Icon name="close" size={20} />
            </button>
        </div>
        
        <div class="p-6">
            <!-- Current Tranche Info -->
            <div class="bg-gray-50 rounded-lg p-4 mb-6">
                <h4 class="text-sm font-bold text-gray-700 mb-2">Current Tranche Details</h4>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <span class="text-gray-500">Amount:</span>
                        <span class="font-medium ml-2">${selectedTranche.amount.toLocaleString()}</span>
                    </div>
                    <div>
                        <span class="text-gray-500">Trigger:</span>
                        <span class="font-medium ml-2">{getTriggerDescription(selectedTranche)}</span>
                    </div>
                </div>
            </div>
            
            <!-- Amendment Form -->
            <form on:submit|preventDefault={submitAmendment} class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Amendment Type</label>
                    <select 
                        bind:value={amendment.type}
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="amount">Modify Amount</option>
                        <option value="trigger">Change Trigger</option>
                        <option value="date">Change Date</option>
                    </select>
                </div>
                
                {#if amendment.type === 'amount'}
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">New Amount (USD)</label>
                        <input 
                            type="number" 
                            bind:value={amendment.newAmount}
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="0.00"
                            required
                        />
                    </div>
                {:else if amendment.type === 'trigger'}
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">New Trigger Type</label>
                        <select 
                            bind:value={amendment.newTriggerType}
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="milestone">Milestone Completion</option>
                            <option value="report">Report Submission</option>
                            <option value="date">Specific Date</option>
                            <option value="manual">Manual Release</option>
                        </select>
                    </div>
                    
                    {#if amendment.newTriggerType === 'milestone'}
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Required Milestone</label>
                            <select 
                                bind:value={amendment.newMilestoneId}
                                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="">Select milestone...</option>
                                <!-- Milestones would be loaded dynamically -->
                            </select>
                        </div>
                    {:else if amendment.newTriggerType === 'report'}
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Required Report Type</label>
                            <select 
                                bind:value={amendment.newReportType}
                                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="financial">Financial Report</option>
                                <option value="progress">Progress Report</option>
                                <option value="technical">Technical Report</option>
                            </select>
                        </div>
                    {:else if amendment.newTriggerType === 'date'}
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Release Date</label>
                            <input 
                                type="date" 
                                bind:value={amendment.newDate}
                                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    {/if}
                {/if}
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Reason for Change <span class="text-red-500">*</span></label>
                    <textarea 
                        bind:value={amendment.reason}
                        rows="3"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Please explain why this amendment is needed..."
                        required
                    ></textarea>
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Supporting Documents (Optional)</label>
                    <input 
                        type="file" 
                        multiple
                        accept=".pdf,.doc,.docx"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p class="text-xs text-gray-500 mt-1">Upload any supporting documents (funder approval emails, etc.)</p>
                </div>
                
                <div class="flex gap-3 pt-4">
                    <button 
                        type="submit"
                        class="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        Submit Request
                    </button>
                    <button 
                        type="button"
                        on:click={() => showAmendmentForm = false}
                        class="px-6 py-2 bg-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-300 transition-colors"
                    >
                        Cancel
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{/if}

<!-- History Modal -->
{#if showHistoryModal && selectedTranche}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm">
    <div class="bg-white w-full max-w-3xl rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-xl bg-gray-100 flex items-center justify-center">
                    <Icon name="info" size={16} class="text-gray-600" />
                </div>
                <h3 class="text-lg font-bold text-gray-900">Amendment History</h3>
            </div>
            <button on:click={() => showHistoryModal = false} class="text-gray-400 hover:text-gray-600 p-1 hover:bg-gray-100 rounded-lg">
                <Icon name="close" size={20} />
            </button>
        </div>
        
        <div class="p-6">
            <div class="mb-4">
                <h4 class="text-sm font-bold text-gray-700">Tranche {selectedTranche.tranche_number}: {selectedTranche.description || 'No description'}</h4>
                <p class="text-sm text-gray-600">Current amount: ${selectedTranche.amount.toLocaleString()}</p>
            </div>
            
            {#if amendmentHistory.length === 0}
                <div class="text-center py-8">
                    <Icon name="info" size={48} class="text-gray-400 mx-auto mb-3" />
                    <p class="text-gray-500">No amendment history found</p>
                </div>
            {:else}
                <div class="space-y-4">
                    {#each amendmentHistory as amendment}
                        <div class="border border-gray-200 rounded-lg p-4">
                            <div class="flex items-center justify-between mb-2">
                                <div class="flex items-center gap-2">
                                    <span class="px-2 py-1 rounded-full text-xs font-medium {
                                        amendment.status === 'approved' ? 'bg-emerald-100 text-emerald-700' :
                                        amendment.status === 'rejected' ? 'bg-red-100 text-red-700' :
                                        'bg-amber-100 text-amber-700'
                                    }">
                                        {amendment.status.toUpperCase()}
                                    </span>
                                    <span class="text-sm font-medium text-gray-900">
                                        {amendment.amendment_type} amendment
                                    </span>
                                </div>
                                <span class="text-xs text-gray-500">
                                    {formatDate(amendment.created_at)}
                                </span>
                            </div>
                            
                            <p class="text-sm text-gray-700 mb-2">{amendment.reason}</p>
                            
                            {#if amendment.requested_by_user}
                                <p class="text-xs text-gray-500">
                                    Requested by: {amendment.requested_by_user.name}
                                </p>
                            {/if}
                            
                            {#if amendment.approved_by_user}
                                <p class="text-xs text-gray-500">
                                    Approved by: {amendment.approved_by_user.name} on {formatDate(amendment.approved_at)}
                                </p>
                            {/if}
                            
                            {#if amendment.rejection_reason}
                                <p class="text-xs text-red-600">
                                    Rejection reason: {amendment.rejection_reason}
                                </p>
                            {/if}
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
    </div>
</div>
{/if}

<style>
    /* Custom styles if needed */
</style>
