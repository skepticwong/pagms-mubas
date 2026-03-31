<script>
    import { onMount } from "svelte";
    import axios from "axios";
    import { user } from "../stores/auth.js";
    import Icon from "../components/Icon.svelte";
    import Layout from "../components/Layout.svelte";

    let pendingApprovals = [];
    let loading = true;
    let error = "";
    let success = "";

    // RSU Effort Override state
    let lockedGrants = [];
    let loadingLocks = true;
    let isOverrideModalOpen = false;
    let selectedLockedGrant = null;
    let overrideJustification = "";
    let submittingOverride = false;

    // Action Modal State
    let isActionModalOpen = false;
    let selectedWorkflow = null;
    let actionType = ""; // APPROVE | REJECT
    let comment = "";
    let processingAction = false;

    onMount(async () => {
        await Promise.all([loadPendingApprovals(), loadLockedGrants()]);
    });

    async function loadPendingApprovals() {
        loading = true;
        try {
            const res = await axios.get("http://localhost:5000/api/approvals/pending", { withCredentials: true });
            pendingApprovals = res.data;
        } catch (err) {
            console.error("Error loading approvals:", err);
            error = "Failed to load pending approvals.";
        } finally {
            loading = false;
        }
    }

    function openActionModal(workflow, type) {
        selectedWorkflow = workflow;
        actionType = type;
        comment = "";
        isActionModalOpen = true;
    }

    async function submitAction() {
        if (!selectedWorkflow || processingAction) return;
        
        processingAction = true;
        try {
            await axios.post(`http://localhost:5000/api/approvals/${selectedWorkflow.workflow_id}/action`, {
                action: actionType,
                comment: comment
            }, { withCredentials: true });
            
            success = `Successfully ${actionType.toLowerCase()}ed request.`;
            isActionModalOpen = false;
            await loadPendingApprovals();
            
            setTimeout(() => success = "", 3000);
        } catch (err) {
            console.error("Action error:", err);
            error = err.response?.data?.error || "Failed to process action.";
        } finally {
            processingAction = false;
        }
    }

    function formatDate(dateStr) {
        return new Date(dateStr).toLocaleDateString('en-GB', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    }

    async function loadLockedGrants() {
        loadingLocks = true;
        try {
            const res = await axios.get("http://localhost:5000/api/effort/locked-grants", { withCredentials: true });
            lockedGrants = res.data.locked_grants || [];
        } catch (err) {
            // Not an RSU user or backend error — silently ignore
            lockedGrants = [];
        } finally {
            loadingLocks = false;
        }
    }

    function openOverrideModal(grant) {
        selectedLockedGrant = grant;
        overrideJustification = "";
        isOverrideModalOpen = true;
    }

    async function applyOverride() {
        if (!overrideJustification.trim()) {
            error = "Please provide a justification for the override.";
            return;
        }
        submittingOverride = true;
        error = "";
        try {
            await axios.post("http://localhost:5000/api/effort/override", {
                grant_id: selectedLockedGrant.grant_id,
                year: selectedLockedGrant.prev_year,
                month: selectedLockedGrant.prev_month,
                justification: overrideJustification
            }, { withCredentials: true });
            success = `Override applied for ${selectedLockedGrant.grant_code}. Spending is now unlocked.`;
            isOverrideModalOpen = false;
            await loadLockedGrants();
            setTimeout(() => success = "", 5000);
        } catch (err) {
            error = err.response?.data?.error || "Failed to apply override.";
        } finally {
            submittingOverride = false;
        }
    }

    function getStatusColor(type) {
        switch(type) {
            case 'VIREMENT': return 'bg-purple-100 text-purple-700 border-purple-200';
            case 'PRIOR_APPROVAL': return 'bg-amber-100 text-amber-700 border-amber-200';
            case 'EXPENSE': return 'bg-blue-100 text-blue-700 border-blue-200';
            default: return 'bg-gray-100 text-gray-700 border-gray-200';
        }
    }
</script>

<Layout>
    <div class="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-700">
    <!-- Header Section -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white/40 backdrop-blur-xl p-6 rounded-3xl border border-white/40 shadow-sm">
        <div>
            <h1 class="text-3xl font-extrabold text-gray-900 tracking-tight">Decision Center</h1>
            <p class="text-gray-500 mt-1 font-medium">Consolidated Approval Pipeline for {($user?.role || 'Staff')}</p>
        </div>
        
        <div class="flex gap-3">
            <div class="px-5 py-2.5 bg-blue-600/10 border border-blue-600/20 rounded-2xl">
                <p class="text-[10px] uppercase font-bold text-blue-600 tracking-widest">Pending Items</p>
                <p class="text-2xl font-black text-blue-700 leading-none mt-1">{pendingApprovals.length}</p>
            </div>
            <button 
                on:click={loadPendingApprovals}
                class="p-4 bg-white/80 hover:bg-white border border-gray-200 rounded-2xl transition-all shadow-sm active:scale-95"
            >
                <Icon name="refresh" size={20} />
            </button>
        </div>
    </div>

    {#if error}
        <div class="p-4 bg-red-50 border border-red-100 text-red-700 rounded-2xl flex items-center gap-3 animate-bounce">
            <Icon name="warning" size={20} />
            <p class="font-semibold">{error}</p>
        </div>
    {/if}

    {#if success}
        <div class="p-4 bg-emerald-50 border border-emerald-100 text-emerald-700 rounded-2xl flex items-center gap-3 animate-in slide-in-from-top-4">
            <Icon name="check" size={20} />
            <p class="font-semibold">{success}</p>
        </div>
    {/if}

    <!-- Main Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        <!-- Pending List -->
        <div class="lg:col-span-3 space-y-4">
            {#if loading}
                <div class="flex flex-col items-center justify-center py-20 bg-white/30 backdrop-blur-md rounded-3xl border border-white/40">
                    <div class="w-12 h-12 border-4 border-blue-600/20 border-t-blue-600 rounded-full animate-spin"></div>
                    <p class="mt-4 text-gray-500 font-bold uppercase tracking-widest text-xs">Assembling Queue...</p>
                </div>
            {:else if pendingApprovals.length === 0}
                <div class="text-center py-20 bg-white/30 backdrop-blur-md rounded-3xl border border-white/40">
                    <div class="w-20 h-20 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Icon name="check" size={40} />
                    </div>
                    <h3 class="text-xl font-bold text-gray-900">Clear Skies!</h3>
                    <p class="text-gray-500 mt-2">All approval queues are currently empty.</p>
                </div>
            {:else}
                {#each pendingApprovals as item (item.workflow_id)}
                    <div class="group bg-white/70 backdrop-blur-xl border border-white/40 p-6 rounded-3xl shadow-sm hover:shadow-xl transition-all duration-300 hover:translate-y-[-2px]">
                        <div class="flex flex-col md:flex-row gap-6">
                            <!-- Left: Category & Type -->
                            <div class="flex flex-row md:flex-col items-center md:items-start justify-between min-w-[140px]">
                                <span class={`px-3 py-1 text-[10px] font-black uppercase tracking-tighter rounded-full border ${getStatusColor(item.item_type)}`}>
                                    {item.item_type}
                                </span>
                                <div class="mt-4 hidden md:block text-gray-400">
                                    <p class="text-[10px] font-bold uppercase tracking-widest">Received</p>
                                    <p class="text-sm font-bold text-gray-600">{formatDate(item.created_at)}</p>
                                </div>
                            </div>

                            <!-- Middle: Context -->
                            <div class="flex-1">
                                <h3 class="text-lg font-bold text-gray-900 leading-tight mb-1">{item.item_data.title}</h3>
                                <div class="flex items-center gap-2 mb-3">
                                    <span class="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-lg">{item.item_data.grant_title}</span>
                                    <span class="text-gray-300">•</span>
                                    <span class="text-xs font-medium text-gray-500">Requested by <b class="text-gray-700">{item.item_data.requester}</b></span>
                                </div>
                                <p class="text-sm text-gray-600 bg-gray-50/50 p-4 rounded-2xl italic border border-gray-100">
                                    "{item.item_data.justification || 'No justification provided.'}"
                                </p>
                            </div>

                            <!-- Right: Actions -->
                            <div class="flex md:flex-col items-center justify-center gap-3 md:min-w-[160px]">
                                <button 
                                    on:click={() => openActionModal(item, 'APPROVE')}
                                    class="flex-1 w-full flex items-center justify-center gap-2 px-6 py-3 bg-emerald-600 text-white font-bold rounded-2xl hover:bg-emerald-700 shadow-lg shadow-emerald-200 transition-all active:scale-95"
                                >
                                    <Icon name="check" size={18} /> Approve
                                </button>
                                <button 
                                    on:click={() => openActionModal(item, 'REJECT')}
                                    class="flex-1 w-full flex items-center justify-center gap-2 px-6 py-3 bg-white text-red-600 border border-red-100 font-bold rounded-2xl hover:bg-red-50 transition-all active:scale-95"
                                >
                                    <Icon name="close" size={18} /> Reject
                                </button>
                            </div>
                        </div>
                    </div>
                {/each}
            {/if}
        </div>
    </div>

    <!-- RSU Effort Override Panel -->
    <div class="bg-white/70 backdrop-blur-xl border border-rose-100 rounded-3xl shadow-sm overflow-hidden">
        <div class="px-6 py-5 border-b border-rose-50 bg-rose-50/40 flex items-center justify-between">
            <div>
                <h2 class="font-bold text-rose-900 flex items-center gap-2">
                    <Icon name="lock" size="18" class="text-rose-500" />
                    Spending-Locked Grants
                </h2>
                <p class="text-xs text-rose-600 mt-1">Grants blocked from new expense submissions due to overdue effort certification.</p>
            </div>
            <span class="px-3 py-1 bg-rose-100 text-rose-700 text-xs font-bold rounded-full">{lockedGrants.length} locked</span>
        </div>
        <div class="p-4">
            {#if loadingLocks}
                <p class="text-sm text-gray-400 text-center py-6">Checking lock status...</p>
            {:else if lockedGrants.length === 0}
                <div class="text-center py-8 text-emerald-600">
                    <Icon name="check-circle" size="32" class="mx-auto mb-2" />
                    <p class="font-semibold text-sm">All grants are compliant — no locks active.</p>
                </div>
            {:else}
                <div class="space-y-3">
                    {#each lockedGrants as grant}
                        <div class="flex items-center justify-between p-4 bg-rose-50 border border-rose-100 rounded-2xl">
                            <div>
                                <p class="font-bold text-gray-900 text-sm">{grant.grant_code}</p>
                                <p class="text-xs text-gray-500 mt-0.5 truncate max-w-xs">{grant.title}</p>
                                <p class="text-xs text-rose-600 mt-1 font-medium">Overdue: {grant.month_name} {grant.prev_year} certification</p>
                            </div>
                            <button
                                on:click={() => openOverrideModal(grant)}
                                class="ml-4 shrink-0 px-4 py-2 bg-rose-600 text-white text-xs font-bold rounded-xl hover:bg-rose-700 transition-all active:scale-95 shadow-sm shadow-rose-200"
                            >
                                Apply Override
                            </button>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
    </div>

</div>

<!-- Decision Modal -->
{#if isActionModalOpen}
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
        <!-- Backdrop -->
        <button 
            type="button"
            class="absolute inset-0 w-full h-full bg-gray-900/60 backdrop-blur-md animate-in fade-in duration-300 border-none outline-none cursor-default"
            on:click={() => !processingAction && (isActionModalOpen = false)}
            aria-label="Close modal"
        ></button>
        
        <!-- Modal Content -->
        <div class="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div class={`p-8 ${actionType === 'APPROVE' ? 'bg-emerald-600' : 'bg-red-600'} text-white`}>
                <h3 class="text-2xl font-black">Confirm {actionType === 'APPROVE' ? 'Approval' : 'Rejection'}</h3>
                <p class="text-white/80 font-medium mt-1">Reviewing {selectedWorkflow.item_data.title}</p>
            </div>
            
            <div class="p-8">
                <label for="comment" class="block text-sm font-bold text-gray-700 mb-2 uppercase tracking-tight">Internal Comments / Feedback</label>
                <textarea 
                    id="comment"
                    bind:value={comment}
                    placeholder="Add a reason for your decision..."
                    rows="4"
                    class="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-gray-700 font-medium"
                ></textarea>
                
                <div class="mt-8 flex gap-3">
                    <button 
                        on:click={() => isActionModalOpen = false}
                        disabled={processingAction}
                        class="flex-1 px-6 py-4 bg-gray-100 text-gray-700 font-bold rounded-2xl hover:bg-gray-200 transition-all active:scale-95 disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button 
                        on:click={submitAction}
                        disabled={processingAction}
                        class={`flex-[2] px-6 py-4 ${actionType === 'APPROVE' ? 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-200' : 'bg-red-600 hover:bg-red-700 shadow-red-200'} text-white font-bold rounded-2xl shadow-lg transition-all active:scale-95 flex items-center justify-center gap-2`}
                    >
                        {#if processingAction}
                            <div class="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                            Processing...
                        {:else}
                            <Icon name={actionType === 'APPROVE' ? 'check' : 'close'} size={20} />
                            Confirm {actionType.toLowerCase()}
                        {/if}
                    </button>
                </div>
            </div>
        </div>
    </div>
{/if}

<!-- RSU Override Modal -->
{#if isOverrideModalOpen && selectedLockedGrant}
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
        <button
            type="button"
            class="absolute inset-0 w-full h-full bg-gray-900/60 backdrop-blur-md border-none outline-none cursor-default"
            on:click={() => !submittingOverride && (isOverrideModalOpen = false)}
            aria-label="Close modal"
        ></button>
        <div class="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div class="p-8 bg-rose-600 text-white">
                <h3 class="text-2xl font-black">Apply RSU Override</h3>
                <p class="text-white/80 font-medium mt-1">{selectedLockedGrant.grant_code} — {selectedLockedGrant.month_name} {selectedLockedGrant.prev_year}</p>
            </div>
            <div class="p-8 space-y-5">
                <div class="p-4 bg-amber-50 border border-amber-100 rounded-2xl text-amber-800 text-sm">
                    <p class="font-bold mb-1">⚠️ This will unlock spending for this grant.</p>
                    <p class="text-xs">An RSU override bypasses the effort certification requirement for this period. This action is logged and auditable.</p>
                </div>
                <div>
                    <label for="override-justification" class="block text-sm font-bold text-gray-700 mb-2 uppercase tracking-tight">Justification (required)</label>
                    <textarea
                        id="override-justification"
                        bind:value={overrideJustification}
                        placeholder="Explain why this override is necessary (e.g. PI is on medical leave)..."
                        rows="4"
                        class="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-rose-500/10 focus:border-rose-500 transition-all outline-none text-gray-700 font-medium"
                    ></textarea>
                </div>
                <div class="flex gap-3 mt-2">
                    <button
                        on:click={() => isOverrideModalOpen = false}
                        disabled={submittingOverride}
                        class="flex-1 px-6 py-4 bg-gray-100 text-gray-700 font-bold rounded-2xl hover:bg-gray-200 transition-all active:scale-95 disabled:opacity-50"
                    >Cancel</button>
                    <button
                        on:click={applyOverride}
                        disabled={submittingOverride}
                        class="flex-[2] px-6 py-4 bg-rose-600 hover:bg-rose-700 text-white font-bold rounded-2xl shadow-lg shadow-rose-200 transition-all active:scale-95 flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                        {#if submittingOverride}
                            <div class="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                            Applying...
                        {:else}
                            <Icon name="lock" size={18} /> Confirm Override
                        {/if}
                    </button>
                </div>
            </div>
        </div>
    </div>
{/if}

</Layout>

<style>
    /* Custom scrollbar for glass aside if needed, but here we are in main */
    :global(body) {
        background-color: #f8fafc;
    }
</style>
