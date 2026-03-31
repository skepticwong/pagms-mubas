<script>
    import { onMount } from 'svelte';
    import axios from 'axios';
    import Icon from './Icon.svelte';
    import KPIManagementModal from './KPIManagementModal.svelte';
    import { showToast } from "../stores/toast.js";

    export let grantId;
    export let grantTitle;
    export let disbursementType = "single";

    let milestones = [];
    let tranches = [];
    let trancheReadiness = {};
    let isLoading = true;
    let isLoadingTranches = false;
    let releasingTrancheId = null;
    let error = "";
    
    // Dashboard data
    let milestoneKPIs = {};
    let milestoneMetrics = {};
    $: expandedMilestones = new Set();

    // Grant KPIs state
    let grantKPIs = [];
    let showGrantKPIDetails = false;
    let isLoadingGrantKPIs = false;

    // KPI Management state
    let showKPIManagement = false;
    let selectedMilestone = null;
    let selectedMilestoneId = null;

    /** In-app confirm (replaces window.confirm) */
    let releaseConfirmTranche = null;
    let deleteConfirmId = null;
    let reopenConfirmId = null;
    
    // Modal state
    let showModal = false;
    let editingMilestone = null;
    let isSaving = false;
    
    // Form state
    let milestoneForm = {
        title: "",
        description: "",
        due_date: "",
        reporting_period: "",
        triggers_tranche: null,
        funding_amount: 0
    };

    onMount(async () => {
        console.log("🚀 MilestonesTab component mounted");
        console.log("📋 Grant ID:", grantId);
        
        if (grantId) {
            fetchMilestones();
            fetchTranches();
            fetchGrantKPIs();
        }
    });

    // Reactive statement to fetch data when grantId changes
    $: if (grantId) {
        fetchMilestones();
        fetchTranches();
        fetchGrantKPIs();
    }

    async function fetchMilestones() {
        isLoading = true;
        error = "";
        console.log("📊 Fetching milestones for grant:", grantId);
        
        try {
            const res = await axios.get(`http://localhost:5000/api/grants/${grantId}/milestones`, {
                withCredentials: true
            });
            milestones = res.data;
            console.log("✅ Milestones loaded:", milestones.length, "milestones");
            
            // Fetch dashboard data after milestones are loaded
            if (milestones && milestones.length > 0) {
                console.log("📈 Fetching dashboard data for", milestones.length, "milestones");
                await fetchMilestoneDashboardData();
            } else {
                console.log("⚠️ No milestones available - skipping dashboard fetch");
            }
        } catch (err) {
            console.error("❌ Error fetching milestones:", err);
            error = "Failed to load milestones.";
        } finally {
            isLoading = false;
        }
    }

    async function fetchMilestoneDashboardData() {
        // Only fetch dashboard data if milestones exist
        if (!milestones || milestones.length === 0) {
            console.log("No milestones to fetch dashboard data for");
            return;
        }
        
        try {
            console.log("🚀 Starting dashboard data fetch for", milestones.length, "milestones");
            
            // Fetch real KPI data and dashboard metrics for all milestones
            const dashboardPromises = milestones.map(async (milestone) => {
                try {
                    console.log(`📊 Fetching dashboard for milestone ${milestone.id}`);
                    
                    const [kpiRes, metricsRes] = await Promise.all([
                        axios.get(`http://localhost:5000/api/milestone-kpis/milestone/${milestone.id}`, {
                            withCredentials: true
                        }),
                        axios.get(`http://localhost:5000/api/dashboard/milestone/${milestone.id}/operational`, {
                            withCredentials: true
                        })
                    ]);
                    
                    console.log(`✅ Dashboard data received for milestone ${milestone.id}:`, {
                        kpis: kpiRes.data,
                        metrics: metricsRes.data
                    });
                    
                    return {
                        milestoneId: milestone.id,
                        kpis: kpiRes.data,
                        metrics: metricsRes.data
                    };
                } catch (err) {
                    console.error(`❌ Failed to fetch dashboard for milestone ${milestone.id}:`, err);
                    console.error('Error details:', {
                        status: err.response?.status,
                        statusText: err.response?.statusText,
                        data: err.response?.data,
                        message: err.message
                    });
                    return {
                        milestoneId: milestone.id,
                        kpis: null,
                        metrics: null,
                        error: err.response?.data?.message || err.message || 'Dashboard fetch failed'
                    };
                }
            });
            
            const dashboardData = await Promise.all(dashboardPromises);
            console.log("🎯 All dashboard data fetched:", dashboardData);
            
            // Store dashboard data
            dashboardData.forEach(({ milestoneId, kpis, metrics, error }) => {
                if (error) {
                    console.error(`💥 Dashboard error for milestone ${milestoneId}:`, error);
                    milestoneKPIs[milestoneId] = { error, kpis: [] };
                    milestoneMetrics[milestoneId] = { error, metrics: {} };
                } else {
                    milestoneKPIs[milestoneId] = kpis;
                    milestoneMetrics[milestoneId] = metrics;
                    console.log(`💾 Stored dashboard data for milestone ${milestoneId}:`, { kpis, metrics });
                }
            });
        } catch (err) {
            console.error("💥 Critical error in fetchMilestoneDashboardData:", err);
        }
    }

    async function fetchTranches() {
        if (disbursementType !== 'tranches') {
            tranches = [];
            return;
        }
        
        isLoadingTranches = true;
        try {
            const res = await axios.get(`http://localhost:5000/api/grants/${grantId}/tranches`, {
                withCredentials: true
            });
            tranches = res.data;
            await fetchTrancheReadiness();
        } catch (err) {
            console.error("Failed to fetch tranches:", err);
            tranches = []; // Empty array on error
            trancheReadiness = {};
        } finally {
            isLoadingTranches = false;
        }
    }

    async function fetchTrancheReadiness() {
        if (!tranches.length) {
            trancheReadiness = {};
            return;
        }

        try {
            const readinessResponses = await Promise.all(
                tranches.map(async (tranche) => {
                    try {
                        const res = await axios.get(
                            `http://localhost:5000/api/tranches/${tranche.id}/release-check`,
                            { withCredentials: true }
                        );
                        return [tranche.id, res.data];
                    } catch (readinessError) {
                        return [tranche.id, { ready: false, error: "Could not check readiness" }];
                    }
                })
            );

            trancheReadiness = Object.fromEntries(readinessResponses);
        } catch (err) {
            console.error("Failed to load tranche readiness:", err);
            trancheReadiness = {};
        }
    }

    async function fetchGrantKPIs() {
        isLoadingGrantKPIs = true;
        try {
            const response = await axios.get(`http://localhost:5000/api/grant-kpis/grant/${grantId}`, {
                withCredentials: true
            });
            grantKPIs = response.data.kpis || [];
            console.log("✅ Grant KPIs loaded:", grantKPIs.length, "KPIs");
        } catch (error) {
            console.error("Failed to fetch grant KPIs:", error);
            grantKPIs = [];
        } finally {
            isLoadingGrantKPIs = false;
        }
    }

    function calculateKPIAchievement(kpi) {
        if (!kpi.grant_wide_target || kpi.grant_wide_target === 0) return 0;
        const actual = kpi.total_actual || 0;
        return (actual / parseFloat(kpi.grant_wide_target)) * 100;
    }

    function getAchievementColor(achievement) {
        if (achievement >= 90) return '#10b981'; // emerald-500
        if (achievement >= 75) return '#3b82f6'; // blue-500
        if (achievement >= 50) return '#f59e0b'; // amber-500
        return '#ef4444'; // red-500
    }

    function getTrancheReadinessMessage(trancheId) {
        const readiness = trancheReadiness[trancheId];
        if (!readiness) return "Checking release status...";
        return readiness.trigger_details || readiness.error || "Not ready for release";
    }

    /** Human-readable API error for alerts and console */
    function formatApiError(err, fallback = "Request failed") {
        const data = err.response?.data;
        if (typeof data === "string" && data.trim()) return data;
        if (data && typeof data === "object") {
            const det = data.details;
            const extra =
                det && typeof det === "object"
                    ? det.trigger_details || det.error
                    : null;
            if (data.error && extra) return `${data.error}: ${extra}`;
            if (data.error) return String(data.error);
            if (data.message) return String(data.message);
        }
        return err.message || fallback;
    }

    function openReleaseConfirm(tranche) {
        releaseConfirmTranche = tranche;
    }

    function cancelReleaseConfirm() {
        releaseConfirmTranche = null;
    }

    async function executeReleaseTranche() {
        const tranche = releaseConfirmTranche;
        if (!tranche || releasingTrancheId) return;
        releaseConfirmTranche = null;

        releasingTrancheId = tranche.id;

        try {
            const res = await axios.post(
                `http://localhost:5000/api/tranches/${Number(tranche.id)}/release`,
                {},
                { withCredentials: true }
            );

            const data = res.data || {};
            const ok =
                res.status >= 200 &&
                res.status < 300 &&
                data.success !== false &&
                data.error == null;

            if (ok) {
                await fetchTranches();
                showToast(
                    data.message || "Tranche released successfully.",
                    "success"
                );
            } else {
                showToast(data.error || "Failed to release tranche.", "error");
            }
        } catch (err) {
            console.error("Failed to release tranche:", err.response?.data || err);
            showToast(formatApiError(err, "Failed to release tranche."), "error");
        } finally {
            releasingTrancheId = null;
        }
    }

    function openAddModal() {
        editingMilestone = null;
        milestoneForm = {
            title: "",
            description: "",
            due_date: "",
            reporting_period: "",
            triggers_tranche: null,
            funding_amount: 0
        };
        showModal = true;
    }

    function openEditModal(milestone) {
        editingMilestone = milestone;
        milestoneForm = {
            title: milestone.title,
            description: milestone.description || "",
            due_date: milestone.due_date,
            reporting_period: milestone.reporting_period || "",
            triggers_tranche: milestone.triggers_tranche,
            funding_amount: milestone.funding_amount || 0
        };
        showModal = true;
    }

    async function handleSave() {
        if (!milestoneForm.title || !milestoneForm.due_date) {
            showToast("Title and Due Date are required.", "error");
            return;
        }

        isSaving = true;
        try {
            if (editingMilestone) {
                await axios.put(`http://localhost:5000/api/milestones/${editingMilestone.id}`, {
                    ...milestoneForm,
                    grant_id: grantId
                }, { withCredentials: true });
            } else {
                await axios.post(`http://localhost:5000/api/milestones`, {
                    ...milestoneForm,
                    grant_id: grantId
                }, { withCredentials: true });
            }
            showModal = false;
            fetchMilestones();
            showToast("Milestone saved.", "success");
        } catch (err) {
            console.error(err);
            showToast(err.response?.data?.error || "Failed to save milestone.", "error");
        } finally {
            isSaving = false;
        }
    }

    function promptDeleteMilestone(milestoneId) {
        deleteConfirmId = milestoneId;
    }

    function cancelDeleteMilestone() {
        deleteConfirmId = null;
    }

    async function confirmDeleteMilestone() {
        const milestoneId = deleteConfirmId;
        if (milestoneId == null) return;
        deleteConfirmId = null;

        try {
            await axios.delete(`http://localhost:5000/api/milestones/${milestoneId}`, {
                withCredentials: true
            });
            fetchMilestones();
            showToast("Milestone deleted.", "success");
        } catch (err) {
            console.error(err);
            showToast(err.response?.data?.error || "Failed to delete milestone.", "error");
        }
    }

    function promptReopenMilestone(milestoneId) {
        reopenConfirmId = milestoneId;
    }

    function cancelReopenMilestone() {
        reopenConfirmId = null;
    }

    async function confirmReopenMilestone() {
        const milestoneId = reopenConfirmId;
        if (milestoneId == null) return;
        reopenConfirmId = null;

        try {
            await axios.put(`http://localhost:5000/api/milestones/${milestoneId}/reopen`, {}, {
                withCredentials: true
            });
            fetchMilestones();
            showToast("Milestone reopened.", "success");
        } catch (err) {
            console.error(err);
            showToast(err.response?.data?.error || "Failed to reopen milestone.", "error");
        }
    }

    async function moveMilestone(index, direction) {
        const newMilestones = [...milestones];
        const newIndex = index + direction;
        
        if (newIndex < 0 || newIndex >= newMilestones.length) return;
        
        const temp = newMilestones[index];
        newMilestones[index] = newMilestones[newIndex];
        newMilestones[newIndex] = temp;
        
        milestones = newMilestones;
        
        // Persist to backend
        try {
            await axios.post(`http://localhost:5000/api/grants/${grantId}/milestones/reorder`, {
                ordered_ids: milestones.map(m => m.id)
            }, { withCredentials: true });
        } catch (err) {
            console.error(err);
            error = "Failed to save new order.";
        }
    }

    function getStatusBadge(status) {
        switch (status.toLowerCase()) {
            case 'completed':
                return 'bg-emerald-100 text-emerald-700';
            case 'in_progress':
                return 'bg-blue-100 text-blue-700';
            case 'not_started':
                return 'bg-gray-100 text-gray-700';
            default:
                return 'bg-gray-100 text-gray-700';
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

    function getTriggeredTranches(milestoneId) {
        const mid = Number(milestoneId);
        return tranches.filter(
            (tranche) =>
                tranche.trigger_type === "milestone" &&
                Number(tranche.triggering_milestone_id) === mid
        );
    }

    function formatDate(dateStr) {
        if (!dateStr) return "N/A";
        return new Date(dateStr).toLocaleDateString("en-GB", {
            day: "2-digit",
            month: "short",
            year: "numeric"
        });
    }

    // Dashboard helper functions
    function toggleMilestoneExpansion(milestoneId) {
        console.log(`Toggling milestone ${milestoneId}, current KPIs:`, milestoneKPIs[milestoneId]);
        if (expandedMilestones.has(milestoneId)) {
            expandedMilestones.delete(milestoneId);
        } else {
            expandedMilestones.add(milestoneId);
        }
    }

    function openKPIManagement(milestone) {
        selectedMilestone = milestone;
        selectedMilestoneId = milestone.id;
        showKPIManagement = true;
    }

    function onKPIUpdated() {
        // Refresh dashboard data when KPIs are updated
        fetchMilestoneDashboardData();
    }

    function getKPIStatusColor(status) {
        switch (status) {
            case 'ACHIEVED': return '#22c55e';
            case 'PARTIAL': return '#f59e0b';
            case 'MISSED': return '#ef4444';
            default: return '#9ca3af';
        }
    }

    function getKPIStatusIcon(status) {
        switch (status) {
            case 'ACHIEVED': return '🟢';
            case 'PARTIAL': return '🟡';
            case 'MISSED': return '🔴';
            default: return '⚪';
        }
    }

    function getMetricStatusColor(status) {
        return status.includes('🟢') ? '#22c55e' : 
               status.includes('🟡') ? '#f59e0b' : 
               status.includes('🔴') ? '#ef4444' : '#9ca3af';
    }
</script>

<!-- KPI Management Modal -->
<KPIManagementModal 
    bind:show={showKPIManagement}
    milestoneId={selectedMilestoneId}
    milestone={selectedMilestone}
    onKPIUpdated={onKPIUpdated}
/>

<div class="space-y-6">
    <div class="flex items-center justify-between">
        <div>
            <h2 class="text-lg font-bold text-gray-900">Project Milestones</h2>
            <p class="text-xs text-gray-600">Define and track execution phases for {grantTitle}.</p>
        </div>
        <button 
            on:click={openAddModal}
            class="px-4 py-2 bg-blue-600 text-white text-xs font-bold rounded-xl shadow-sm hover:bg-blue-700 transition-all flex items-center gap-2"
        >
            <Icon name="plus" size={14} />
            Add Milestone
        </button>
    </div>

    <!-- Grant KPIs Progress Overview -->
    <div class="bg-white border border-emerald-100 rounded-3xl p-6 text-gray-900 shadow-xl">
        <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center">
                    <Icon name="chart" size={20} class="text-emerald-600" />
                </div>
                <div>
                    <h3 class="text-sm font-bold">Grant KPIs Progress</h3>
                    <p class="text-[10px] text-emerald-600 uppercase tracking-widest font-bold">Overall Impact Tracking</p>
                </div>
            </div>
            <button 
                on:click={() => showGrantKPIDetails = !showGrantKPIDetails}
                class="px-3 py-1 bg-emerald-50 hover:bg-emerald-100 rounded-lg text-xs font-semibold text-emerald-700 transition-all flex items-center gap-1"
            >
                <Icon name="eye" size={12} />
                {showGrantKPIDetails ? 'Hide' : 'Show'} Details
            </button>
        </div>

        {#if grantKPIs && grantKPIs.length > 0}
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                {#each grantKPIs as kpi}
                    {@const achievement = calculateKPIAchievement(kpi)}
                    <div class="p-4 rounded-2xl bg-emerald-50/30 border border-emerald-100">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-xs font-bold text-emerald-700">{kpi.name}</span>
                            <span class="text-xs text-gray-500">{kpi.unit}</span>
                        </div>
                        <div class="flex items-end justify-between">
                            <div>
                                <div class="text-lg font-bold text-gray-900">
                                    {kpi.total_actual || 0}
                                </div>
                                <div class="text-xs text-emerald-600 font-medium">of {kpi.grant_wide_target}</div>
                            </div>
                            <div class="text-right">
                                <div class="text-lg font-black" style="color: {getAchievementColor(achievement)}">
                                    {achievement.toFixed(1)}%
                                </div>
                                <div class="text-xs text-gray-500 font-medium">Achieved</div>
                            </div>
                        </div>
                        <div class="mt-2 w-full bg-emerald-100 rounded-full h-2 overflow-hidden">
                            <div 
                                class="h-full transition-all duration-500" 
                                style="width: {achievement}%; background-color: {getAchievementColor(achievement)}"
                            ></div>
                        </div>
                    </div>
                {/each}
            </div>

            {#if showGrantKPIDetails}
                <div class="mt-4 p-4 bg-emerald-50/30 rounded-2xl border border-emerald-100">
                    <h4 class="text-sm font-bold text-emerald-700 mb-3 flex items-center gap-2">
                        <Icon name="info" size={14} class="text-emerald-600" />
                        KPI Performance Details
                    </h4>
                    <div class="space-y-2">
                        {#each grantKPIs as kpi}
                            {@const achievement = calculateKPIAchievement(kpi)}
                            <div class="flex items-center justify-between p-2 bg-white/60 rounded-lg border border-emerald-50">
                                <div class="flex items-center gap-3">
                                    <div class="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center">
                                        <span class="text-xs font-bold text-emerald-700">{achievement.toFixed(0)}%</span>
                                    </div>
                                    <div>
                                        <div class="text-sm font-bold text-gray-900">{kpi.name}</div>
                                        <div class="text-xs text-emerald-600 font-medium">{kpi.description}</div>
                                    </div>
                                </div>
                                <div class="text-right">
                                    <div class="text-sm font-bold text-gray-900">{kpi.total_actual || 0} / {kpi.grant_wide_target}</div>
                                    <div class="text-xs text-gray-500">{kpi.unit}</div>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
        {:else}
            <div class="text-center py-6 bg-emerald-50/30 rounded-2xl border border-emerald-100">
                <Icon name="chart" size={32} class="text-emerald-500 mx-auto mb-2" />
                <h4 class="text-sm font-bold text-gray-900 mb-1">No Grant KPIs Defined</h4>
                <p class="text-xs text-emerald-600 font-medium">Grant KPIs should be defined during grant creation for comprehensive impact tracking.</p>
            </div>
        {/if}
    </div>

    <!-- Funding Overview (Conditional) -->
    {#if disbursementType === 'milestone_based'}
    <div class="bg-gradient-to-br from-indigo-900 to-purple-900 rounded-3xl p-6 text-white shadow-xl">
        <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center backdrop-blur-md">
                    <Icon name="target" size={20} />
                </div>
                <div>
                    <h3 class="text-sm font-bold">Milestone-Based Funding</h3>
                    <p class="text-[10px] text-indigo-200 uppercase tracking-widest font-bold">Release on Completion</p>
                </div>
            </div>
            <div class="text-right">
                <p class="text-[10px] text-indigo-300 uppercase font-black">Total Allocated</p>
                <p class="text-xl font-bold">${milestones.reduce((acc, m) => acc + (m.funding_amount || 0), 0).toLocaleString()}</p>
            </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
            <div class="p-3 rounded-2xl bg-white/5 border border-white/10">
                <div class="flex items-center gap-2 mb-1">
                    <Icon name="check-circle" size={14} class="text-emerald-400" />
                    <p class="text-[10px] text-indigo-200 font-bold uppercase">Total Released</p>
                </div>
                <p class="text-lg font-bold text-emerald-400">${milestones.filter(m => m.release_status === 'released').reduce((acc, m) => acc + (m.funding_amount || 0), 0).toLocaleString()}</p>
            </div>
            <div class="p-3 rounded-2xl bg-white/5 border border-white/10">
                <div class="flex items-center gap-2 mb-1">
                    <Icon name="clock" size={14} class="text-amber-400" />
                    <p class="text-[10px] text-indigo-200 font-bold uppercase">Pending Completion</p>
                </div>
                <p class="text-lg font-bold text-amber-400">${milestones.filter(m => m.status !== 'COMPLETED').reduce((acc, m) => acc + (m.funding_amount || 0), 0).toLocaleString()}</p>
            </div>
        </div>
    </div>
    {:else if disbursementType === 'tranches'}
    <!-- Enhanced Tranche View with Milestone Assignments -->
    <div class="space-y-6">
        <!-- Tranche Summary Header -->
        <div class="bg-white border border-blue-100 rounded-3xl p-6 text-gray-900 shadow-xl">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
                        <Icon name="money" size={20} class="text-blue-600" />
                    </div>
                    <div>
                        <h3 class="text-sm font-bold">Tranche Release Schedule</h3>
                        <p class="text-[10px] text-blue-600 uppercase tracking-widest font-bold">Milestone-based funding releases</p>
                    </div>
                </div>
                <div class="text-right">
                    <div class="flex items-center gap-2 justify-end mb-1">
                        <Icon name="layers" size={14} class="text-blue-500" />
                        <p class="text-[10px] text-blue-600 font-bold">Total Tranches</p>
                    </div>
                    <p class="text-2xl font-bold text-gray-900">{tranches.length}</p>
                </div>
            </div>
        </div>

        <!-- Individual Tranche Cards -->
        {#if tranches.length === 0}
        <div class="bg-yellow-50/70 backdrop-blur-md border border-yellow-200/60 rounded-2xl p-6 text-center shadow-sm">
                <Icon name="money" size={32} class="text-yellow-600 mx-auto mb-2" />
                <h4 class="text-lg font-bold text-yellow-800 mb-2">No Tranches Configured</h4>
                <p class="text-sm text-yellow-600">This grant is set up for tranche disbursement but no installment schedules have been created yet.</p>
                <p class="text-xs text-yellow-500 mt-2">Contact RSU to configure tranche schedules for this grant.</p>
            </div>
        {:else}
            {#each tranches as tranche}
                {@const tid = Number(tranche.id)}
                {@const assignedMilestones = milestones.filter(
                    (m) => Number(m.triggers_tranche) === tid
                )}
                {@const completedMilestones = assignedMilestones.filter(
                    (m) => (m.status || "").toUpperCase() === "COMPLETED"
                )}
                {@const backendReady = trancheReadiness[tid]?.ready === true}
                {@const normalizedStatus = (tranche.status || "").toLowerCase()}
                {@const statusReady = normalizedStatus === "ready"}
                {@const isReady =
                    backendReady ||
                    statusReady ||
                    (assignedMilestones.length > 0 &&
                        completedMilestones.length === assignedMilestones.length)}
                {@const isReleased = normalizedStatus === "released"}
                {@const canRelease = !isReleased && isReady}
                
                <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-lg border overflow-hidden">
                    <!-- Tranche Header -->
                    <div class={"p-4 border-b " + (isReady ? "bg-emerald-50/70 border-emerald-200/60" : "bg-white/50 border-white/40")}>
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-3">
                                <div class={"w-10 h-10 rounded-full flex items-center justify-center " + (isReady ? "bg-emerald-500 text-white" : "bg-blue-500 text-white")}>
                                    <span class="text-sm font-bold">{tranche.tranche_number}</span>
                                </div>
                                <div>
                                    <h4 class="font-bold text-gray-900">Tranche {tranche.tranche_number}</h4>
                                    <p class="text-sm text-gray-600">Due: {new Date(tranche.expected_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
                                </div>
                            </div>
                            <div class="text-right">
                                <p class="text-2xl font-bold text-gray-900">${tranche.amount.toLocaleString()}</p>
                                <div class="flex items-center gap-1">
                                    {#if isReleased}
                                        <span class="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">Released</span>
                                    {:else if isReady}
                                        <span class="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-full">Ready for Release</span>
                                    {:else if assignedMilestones.length === 0}
                                        <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-full">No Milestones Assigned</span>
                                    {:else}
                                        <span class="px-2 py-1 bg-amber-100 text-amber-700 text-xs font-medium rounded-full">{completedMilestones.length}/{assignedMilestones.length} Completed</span>
                                    {/if}
                                </div>
                            </div>
                        </div>
                        
                        <!-- NEW: Enhanced Trigger Information -->
                        <div class="flex items-center gap-4 text-[10px] text-gray-500 font-medium pt-1">
                            <span class="flex items-center gap-1">
                                <Icon name="setting" size={12} />
                                Trigger: {getTriggerDescription(tranche)}
                            </span>
                            <span class="flex items-center gap-1">
                                <Icon name="info" size={12} />
                                {getTrancheReadinessMessage(tranche.id)}
                            </span>
                            {#if tranche.trigger_type === 'milestone' && tranche.triggering_milestone}
                                <span class="flex items-center gap-1">
                                    <Icon name="check" size={12} />
                                    Milestone Status: {tranche.triggering_milestone.status.replace('_', ' ').toUpperCase()}
                                </span>
                            {/if}
                        </div>
                    </div>
                    
                    <!-- Assigned Milestones -->
                    <div class="p-4">
                        {#if !isReleased}
                            <div class="mb-4 flex justify-end">
                                <button
                                    on:click={() => openReleaseConfirm(tranche)}
                                    disabled={!canRelease || releasingTrancheId === tranche.id}
                                    class="px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 border disabled:opacity-60 disabled:cursor-not-allowed bg-emerald-600 text-white border-emerald-600 hover:bg-emerald-700"
                                >
                                    {#if releasingTrancheId === tranche.id}
                                        <span class="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></span>
                                        Releasing...
                                    {:else}
                                        <Icon name="check" size={12} />
                                        Release Tranche
                                    {/if}
                                </button>
                            </div>
                        {/if}

                        <div class="flex items-center justify-between mb-3">
                            <h5 class="text-sm font-bold text-gray-700 flex items-center gap-2">
                                <Icon name="setting" size={16} />
                                Assigned Milestones
                            </h5>
                            <span class="text-xs text-gray-500">{assignedMilestones.length} milestones</span>
                        </div>
                        
                        {#if assignedMilestones.length === 0}
                            <div class="text-center py-6 bg-gray-50 rounded-xl">
                                <Icon name="flag" size={24} class="text-gray-400 mx-auto mb-2" />
                                <p class="text-sm text-gray-500">No milestones assigned to this tranche</p>
                                <p class="text-xs text-gray-400 mt-1">Assign milestones to trigger this tranche release</p>
                            </div>
                        {:else}
                            <div class="space-y-2">
                                {#each assignedMilestones as milestone}
                                    {@const ms = (milestone.status || "").toUpperCase()}
                                    <div class="flex items-center justify-between p-3 bg-white/40 backdrop-blur-sm rounded-xl hover:bg-white/60 transition-colors">
                                        <div class="flex items-center gap-3">
                                            <div class={"w-6 h-6 rounded-full flex items-center justify-center " + (ms === 'COMPLETED' ? "bg-emerald-500" : ms === 'IN_PROGRESS' ? "bg-blue-500" : "bg-gray-400")}>
                                                {#if ms === 'COMPLETED'}
                                                    <span class="text-white text-xs">✓</span>
                                                {:else}
                                                    <span class="text-white text-xs">•</span>
                                                {/if}
                                            </div>
                                            <div>
                                                <p class="text-sm font-medium text-gray-900">{milestone.title}</p>
                                                <p class="text-xs text-gray-500">Due: {new Date(milestone.due_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}</p>
                                            </div>
                                        </div>
                                        <div class="text-right">
                                            <span class={"px-2 py-1 text-xs font-medium rounded-full " + 
                                                (ms === 'COMPLETED' ? "bg-emerald-100 text-emerald-700" : 
                                                 ms === 'IN_PROGRESS' ? "bg-blue-100 text-blue-700" : 
                                                 "bg-gray-100 text-gray-600")}>
                                                {milestone.status}
                                            </span>
                                        </div>
                                    </div>
                                {/each}
                            </div>
                        {/if}
                    </div>
                </div>
            {/each}
        {/if}
    </div>
    {/if}

    {#if isLoading}
        <div class="flex flex-col items-center justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
            <Icon name="loader" size={16} class="text-blue-600 mb-2" />
            <p class="text-xs text-gray-500 font-medium">Loading milestones...</p>
        </div>
    {:else if milestones.length === 0}
        <div class="text-center py-16 bg-white/40 backdrop-blur-md rounded-2xl border-2 border-dashed border-white/60 shadow-sm">
            <Icon name="flag" size={48} class="text-gray-400 mx-auto mb-3" />
            <h3 class="text-sm font-bold text-gray-900">No Milestones Set</h3>
            <p class="text-xs text-gray-500 mb-6">Break down your project into manageable phases.</p>
            <button 
                on:click={openAddModal}
                class="px-4 py-2 border border-blue-600 text-blue-600 text-xs font-bold rounded-xl hover:bg-blue-50 transition-all flex items-center gap-2 mx-auto"
            >
                <Icon name="plus" size={14} />
                Create Your First Milestone
            </button>
        </div>
    {:else}
        <div class="space-y-6">
            <!-- Milestones Header -->
            <div class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl p-6 mb-6 shadow-xl">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <Icon name="flag" size={24} />
                        <div>
                            <h2 class="text-2xl font-bold">Project Milestones</h2>
                            <p class="text-blue-100 text-sm mt-1">Track your project progress and KPI achievements</p>
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="flex items-center gap-2 justify-end mb-1">
                            <Icon name="flag" size={14} class="text-blue-100" />
                            <p class="text-[10px] text-blue-100">Total Milestones</p>
                        </div>
                        <div class="text-3xl font-bold">{milestones.length}</div>
                    </div>
                </div>
            </div>

            {#each milestones as milestone, i}
                <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300">
                    <!-- Milestone Header -->
                    <div class="bg-white/50 border-b border-white/60 p-6 backdrop-blur-sm">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-4">
                                <!-- Milestone Number -->
                                <div class="w-12 h-12 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-lg shadow-lg">
                                    {milestone.sequence || i + 1}
                                </div>
                                
                                <!-- Milestone Info -->
                                <div>
                                    <h3 class="text-xl font-bold text-gray-900 mb-1">{milestone.title}</h3>
                                    <div class="flex items-center gap-3 text-sm">
                                        <span class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide flex items-center gap-1 {getStatusBadge(milestone.status)}">
                                            {#if milestone.status === 'COMPLETED'}
                                                <Icon name="check" size={12} />
                                            {:else if milestone.status === 'IN_PROGRESS'}
                                                <Icon name="setting" size={12} />
                                            {:else}
                                                <Icon name="clock" size={12} />
                                            {/if}
                                            {milestone.status.replace('_', ' ')}
                                        </span>
                                        
                                        {#if milestone.triggers_tranche}
                                            {@const triggeredTranches = getTriggeredTranches(milestone.id)}
                                            {#if triggeredTranches.length > 0}
                                                <span class="px-3 py-1 rounded-full bg-amber-100 text-amber-800 text-xs font-bold flex items-center gap-1">
                                                    <Icon name="money" size={12} />
                                                    Unlocks {triggeredTranches.length} Tranche{triggeredTranches.length > 1 ? 's' : ''}
                                                </span>
                                            {/if}
                                        {/if}
                                        
                                        {#if milestone.funding_amount > 0}
                                            <span class="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold flex items-center gap-1">
                                                <Icon name="money" size={12} />
                                                ${milestone.funding_amount.toLocaleString()} 
                                                {milestone.release_status === 'released' ? '(Released)' : '(Funded)'}
                                            </span>
                                        {/if}
                                    </div>
                                    
                                    <div class="text-gray-600 text-sm mt-2">
                                        <p><strong>Due:</strong> {new Date(milestone.due_date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
                                        {#if milestone.description}
                                            <p class="mt-1"><strong>Description:</strong> {milestone.description}</p>
                                        {/if}
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Order Controls -->
                            <div class="flex gap-2">
                                <button 
                                    on:click={() => moveMilestone(i, -1)}
                                    disabled={i === 0}
                                    class="p-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-30 transition-colors"
                                    title="Move Up"
                                >
                                    <Icon name="chevron-up" size={16} />
                                </button>
                                <button 
                                    on:click={() => moveMilestone(i, 1)}
                                    disabled={i === milestones.length - 1}
                                    class="p-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-30 transition-colors"
                                    title="Move Down"
                                >
                                    <Icon name="chevron-down" size={16} />
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Progress Section -->
                    <div class="p-6 bg-white/40 border-b border-white/60 backdrop-blur-sm">
                        {#if milestone.task_stats && milestone.task_stats.total > 0}
                            <div class="mb-4">
                                <div class="flex items-center justify-between mb-2">
                                    <h4 class="text-sm font-bold text-gray-700 flex items-center gap-2">
                                        <Icon name="setting" size={14} />
                                        Task Progress
                                    </h4>
                                    <span class="text-sm text-gray-600">
                                        {milestone.task_stats.completed} / {milestone.task_stats.total} tasks completed
                                    </span>
                                </div>
                                <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                                    <div 
                                        class="bg-gradient-to-r from-blue-500 to-blue-600 h-full transition-all duration-500" 
                                        style={`width: ${(milestone.task_stats.completed / milestone.task_stats.total) * 100}%`}
                                    ></div>
                                </div>
                            </div>
                        {/if}
                    </div>

                    <!-- Dashboard Section - Always Visible -->
                    <div class="p-6">
                        <!-- Dashboard Header -->
                        <div class="flex items-center justify-between mb-6">
                            <h4 class="text-lg font-bold text-gray-900 flex items-center gap-2">
                                <Icon name="chart" size={18} />
                                Performance Dashboard
                            </h4>
                            <button 
                                on:click={() => toggleMilestoneExpansion(milestone.id)}
                                class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
                            >
                                <Icon name="chart" size={14} />
                                {expandedMilestones.has(milestone.id) ? 'Hide Details' : 'Show Details'}
                            </button>
                        </div>

                        <!-- KPI Impact Scorecard -->
                        {#if milestoneKPIs[milestone.id] && milestoneKPIs[milestone.id].kpis}
                            <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100 mb-6">
                                <h5 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                                    <Icon name="target" size={18} />
                                    KPI Impact Scorecard
                                </h5>
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {#each milestoneKPIs[milestone.id].kpis as kpi}
                                        <div class="bg-white/60 backdrop-blur-md rounded-lg p-4 shadow-sm border border-white/50">
                                            <div class="flex items-center justify-between mb-3">
                                                <div class="flex items-center gap-2">
                                                    <span class="font-medium text-gray-900">{kpi.name}</span>
                                                    <span class="text-sm text-gray-500">({kpi.unit})</span>
                                                </div>
                                                <div class="flex items-center gap-2">
                                                    <span class="text-sm font-medium px-3 py-1 rounded-full" style="background-color: {kpi.status_color}20; color: {kpi.status_color};">
                                                        {kpi.achievement_pct || 0}%
                                                    </span>
                                                    <span style="color: {kpi.status_color}">
                                                        {kpi.status_indicator}
                                                    </span>
                                                </div>
                                            </div>
                                            <div class="space-y-2">
                                                <div class="flex justify-between items-center">
                                                    <span class="text-sm text-gray-600">Target:</span>
                                                    <span class="font-bold text-gray-900">{kpi.target_value}</span>
                                                </div>
                                                <div class="flex justify-between items-center">
                                                    <span class="text-sm text-gray-600">Actual:</span>
                                                    <span class="font-bold text-lg text-gray-900">{kpi.actual_value || 0}</span>
                                                </div>
                                            </div>
                                        </div>
                                    {/each}
                                </div>
                            </div>
                        {:else}
                            <div class="bg-white/40 backdrop-blur-md rounded-xl p-6 border border-white/60 mb-6">
                                <div class="text-center text-gray-500">
                                    <Icon name="chart" size={32} class="mx-auto mb-2 opacity-50" />
                                    <p class="text-sm">No KPI data available for this milestone</p>
                                    <p class="text-xs text-gray-400 mt-1">KPI data will appear here once milestone activities are tracked</p>
                                </div>
                            </div>
                        {/if}

                        <!-- Operational Metrics -->
                        {#if milestoneMetrics[milestone.id] && expandedMilestones.has(milestone.id)}
                            <div class="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-6 border border-amber-100">
                                <h5 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                                    <Icon name="settings" size={18} />
                                    Operational Metrics
                                </h5>
                                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    <!-- Asset Integrity -->
                                    <div class="bg-white/60 backdrop-blur-md border border-white/50 rounded-lg p-3">
                                        <div class="flex items-center gap-2 mb-2">
                                            <Icon name="shield" size={14} />
                                            <span class="text-xs font-medium text-gray-700">Asset Integrity</span>
                                        </div>
                                        <div class="text-center">
                                            <div class="text-lg font-bold" style="color: {getMetricStatusColor(milestoneMetrics[milestone.id].asset_integrity?.status)}">
                                                {milestoneMetrics[milestone.id].asset_integrity?.return_rate || 0}%
                                            </div>
                                            <div class="text-xs text-gray-600">{milestoneMetrics[milestone.id].asset_integrity?.status || 'N/A'}</div>
                                        </div>
                                    </div>
                                    
                                    <!-- Utilization Rate -->
                                    <div class="bg-white/60 backdrop-blur-md border border-white/50 rounded-lg p-3">
                                        <div class="flex items-center gap-2 mb-2">
                                            <Icon name="activity" size={14} />
                                            <span class="text-xs font-medium text-gray-700">Utilization</span>
                                        </div>
                                        <div class="text-center">
                                            <div class="text-lg font-bold" style="color: {getMetricStatusColor(milestoneMetrics[milestone.id].utilization?.status)}">
                                                {milestoneMetrics[milestone.id].utilization?.utilization_rate || 0}%
                                            </div>
                                            <div class="text-xs text-gray-600">{milestoneMetrics[milestone.id].utilization?.status || 'N/A'}</div>
                                        </div>
                                    </div>
                                    
                                    <!-- Productivity -->
                                    <div class="bg-white/60 backdrop-blur-md border border-white/50 rounded-lg p-3">
                                        <div class="flex items-center gap-2 mb-2">
                                            <Icon name="trending-up" size={14} />
                                            <span class="text-xs font-medium text-gray-700">Productivity</span>
                                        </div>
                                        <div class="text-center">
                                            <div class="text-lg font-bold" style="color: {getMetricStatusColor(milestoneMetrics[milestone.id].productivity?.status)}">
                                                {milestoneMetrics[milestone.id].productivity?.completion_rate || 0}%
                                            </div>
                                            <div class="text-xs text-gray-600">{milestoneMetrics[milestone.id].productivity?.status || 'N/A'}</div>
                                        </div>
                                    </div>
                                    
                                    <!-- Conflict Status -->
                                    {#if milestoneMetrics[milestone.id]?.conflicts?.total_conflicts > 0}
                                        <div class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                                            <div class="flex items-center gap-2">
                                                <Icon name="alert-triangle" size={14} class="text-red-600" />
                                                <span class="text-sm font-medium text-red-800">
                                                    {milestoneMetrics[milestone.id].conflicts.total_conflicts} conflict(s) reported
                                                </span>
                                            </div>
                                        </div>
                                    {/if}
                                </div>
                            </div>
                        {/if}
                    </div>

                    <!-- Actions Footer -->
                    <div class="px-6 py-4 bg-white/40 backdrop-blur-sm border-t border-white/60 flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            {#if milestone.status === 'COMPLETED'}
                                <button 
                                    on:click={() => promptReopenMilestone(milestone.id)}
                                    class="flex items-center gap-1 px-3 py-1.5 bg-amber-50 text-amber-700 text-[10px] font-bold rounded-xl border border-amber-200 hover:bg-amber-100 transition-all"
                                    title="Reopen to add more tasks"
                                >
                                    <Icon name="refresh" size={12} />
                                    Reopen
                                </button>
                            {/if}
                            <button 
                                on:click={() => openEditModal(milestone)}
                                class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all"
                                title="Edit"
                            >
                                <Icon name="edit" size={16} />
                            </button>
                            <button 
                                on:click={() => promptDeleteMilestone(milestone.id)}
                                class="p-2 text-gray-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-all"
                                title="Delete"
                            >
                                <Icon name="trash" size={16} />
                            </button>
                        </div>

                        <div class="flex items-center gap-4 text-[10px] text-gray-500 font-medium">
                            <span class="flex items-center gap-1">
                                <Icon name="calendar" size={12} />
                                Due: {formatDate(milestone.due_date)}
                            </span>
                            {#if milestone.reporting_period}
                                <span class="flex items-center gap-1">
                                    <Icon name="info" size={12} />
                                    Period: {milestone.reporting_period}
                                </span>
                            {/if}
                        </div>
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>

<!-- Confirm: release tranche -->
{#if releaseConfirmTranche}
    <div
        class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm"
        role="presentation"
        on:click|self={cancelReleaseConfirm}
    >
        <div
            class="bg-white/90 backdrop-blur-2xl w-full max-w-md rounded-3xl shadow-2xl overflow-hidden border border-white/60"
            role="dialog"
            aria-modal="true"
            aria-labelledby="rel-title"
        >
            <div class="px-6 py-4 border-b border-gray-100">
                <h3 id="rel-title" class="text-lg font-bold text-gray-900">Release tranche?</h3>
                <p class="text-sm text-gray-600 mt-1">
                    Release Tranche {releaseConfirmTranche.tranche_number} for
                    <span class="font-semibold"
                        >${Number(releaseConfirmTranche.amount || 0).toLocaleString()}</span
                    >? This records the disbursement in the system.
                </p>
            </div>
            <div class="px-6 py-4 bg-gray-50/80 flex justify-end gap-3">
                <button
                    type="button"
                    class="px-4 py-2 text-sm font-bold text-gray-600 hover:bg-gray-100 rounded-xl"
                    on:click={cancelReleaseConfirm}
                >
                    Cancel
                </button>
                <button
                    type="button"
                    class="px-4 py-2 text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl"
                    on:click={executeReleaseTranche}
                >
                    Release
                </button>
            </div>
        </div>
    </div>
{/if}

<!-- Confirm: delete milestone -->
{#if deleteConfirmId != null}
    <div
        class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm"
        role="presentation"
        on:click|self={cancelDeleteMilestone}
    >
        <div
            class="bg-white/90 backdrop-blur-2xl w-full max-w-md rounded-3xl shadow-2xl overflow-hidden border border-white/60"
            role="dialog"
            aria-modal="true"
        >
            <div class="px-6 py-4 border-b border-gray-100">
                <h3 class="text-lg font-bold text-gray-900">Delete milestone?</h3>
                <p class="text-sm text-gray-600 mt-1">This cannot be undone.</p>
            </div>
            <div class="px-6 py-4 bg-gray-50/80 flex justify-end gap-3">
                <button
                    type="button"
                    class="px-4 py-2 text-sm font-bold text-gray-600 hover:bg-gray-100 rounded-xl"
                    on:click={cancelDeleteMilestone}
                >
                    Cancel
                </button>
                <button
                    type="button"
                    class="px-4 py-2 text-sm font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-xl"
                    on:click={confirmDeleteMilestone}
                >
                    Delete
                </button>
            </div>
        </div>
    </div>
{/if}

<!-- Confirm: reopen milestone -->
{#if reopenConfirmId != null}
    <div
        class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm"
        role="presentation"
        on:click|self={cancelReopenMilestone}
    >
        <div
            class="bg-white/90 backdrop-blur-2xl w-full max-w-md rounded-3xl shadow-2xl overflow-hidden border border-white/60"
            role="dialog"
            aria-modal="true"
        >
            <div class="px-6 py-4 border-b border-gray-100">
                <h3 class="text-lg font-bold text-gray-900">Reopen milestone?</h3>
                <p class="text-sm text-gray-600 mt-1">
                    You can add more tasks to this phase after reopening.
                </p>
            </div>
            <div class="px-6 py-4 bg-gray-50/80 flex justify-end gap-3">
                <button
                    type="button"
                    class="px-4 py-2 text-sm font-bold text-gray-600 hover:bg-gray-100 rounded-xl"
                    on:click={cancelReopenMilestone}
                >
                    Cancel
                </button>
                <button
                    type="button"
                    class="px-4 py-2 text-sm font-bold text-white bg-amber-600 hover:bg-amber-700 rounded-xl"
                    on:click={confirmReopenMilestone}
                >
                    Reopen
                </button>
            </div>
        </div>
    </div>
{/if}

<!-- Modal -->
{#if showModal}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm">
    <div class="bg-white/90 backdrop-blur-2xl w-full max-w-md rounded-3xl shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200 border border-white/60">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-xl bg-blue-100 flex items-center justify-center">
                    <Icon name="setting" size={16} class="text-blue-600" />
                </div>
                <h3 class="text-lg font-bold text-gray-900">
                    {editingMilestone ? 'Edit Milestone' : 'Add New Milestone'}
                </h3>
            </div>
            <button on:click={() => showModal = false} class="text-gray-400 hover:text-gray-600 transition-all p-1 hover:bg-gray-100 rounded-lg">
                <Icon name="close" size={20} />
            </button>
        </div>
        
        <div class="p-6 space-y-4">
            <div class="space-y-1">
                <label for="m-title" class="text-[10px] font-black uppercase tracking-widest text-gray-500">Title</label>
                <input 
                    id="m-title"
                    bind:value={milestoneForm.title}
                    type="text" 
                    placeholder="Phase 1: Research Initiation"
                    class="w-full px-4 py-3 bg-gray-50 border-0 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500/20"
                />
            </div>

            <div class="space-y-1">
                <label for="m-desc" class="text-[10px] font-black uppercase tracking-widest text-gray-500">Description</label>
                <textarea 
                    id="m-desc"
                    bind:value={milestoneForm.description}
                    rows="3"
                    placeholder="Key deliverables and goals for this phase..."
                    class="w-full px-4 py-3 bg-gray-50 border-0 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500/20"
                ></textarea>
            </div>

            <div class="grid grid-cols-2 gap-4">
                <div class="space-y-1">
                    <label for="m-due" class="text-[10px] font-black uppercase tracking-widest text-gray-500">Due Date</label>
                    <input 
                        id="m-due"
                        bind:value={milestoneForm.due_date}
                        type="date"
                        class="w-full px-4 py-3 bg-gray-50 border-0 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500/20"
                    />
                </div>
                <div class="space-y-1">
                    <label for="m-period" class="text-[10px] font-black uppercase tracking-widest text-gray-500">Reporting Period</label>
                    <input 
                        id="m-period"
                        bind:value={milestoneForm.reporting_period}
                        type="text"
                        placeholder="e.g. Q1 Year 1"
                        class="w-full px-4 py-3 bg-gray-50 border-0 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500/20"
                    />
                </div>
            </div>

            <div class="space-y-1">
                <label for="m-tranche" class="text-[10px] font-black uppercase tracking-widest text-gray-500">
                    {disbursementType === 'milestone_based' ? 'Release Funding Amount' : 'Tranche Release Trigger'}
                </label>
                {#if disbursementType === 'milestone_based'}
                    <div class="relative">
                        <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
                        <input 
                            id="m-funding"
                            bind:value={milestoneForm.funding_amount}
                            type="number" 
                            step="0.01"
                            class="w-full pl-8 pr-4 py-3 bg-gray-50 border-0 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500/20"
                        />
                    </div>
                {:else}
                    <select 
                        id="m-tranche"
                        bind:value={milestoneForm.triggers_tranche}
                        class="w-full px-4 py-3 bg-gray-50 border-0 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500/20"
                    >
                        <option value={null}>None - No tranche trigger</option>
                        {#each tranches as tranche}
                            <option value={tranche.id}>
                                Tranche {tranche.tranche_number}: {tranche.description || 'No description'} 
                                - ${tranche.amount.toLocaleString()} 
                                ({getTriggerDescription(tranche)})
                            </option>
                        {/each}
                    </select>
                {/if}
                <p class="text-[10px] text-gray-400 italic">
                    {disbursementType === 'milestone_based' 
                        ? 'Completing this milestone will mark this amount as ready for release.' 
                        : 'Completing this milestone will be a requirement for this tranche release.'}
                </p>
            </div>
        </div>

        <!-- FIXED: Modal Footer -->
        <div class="px-6 py-4 bg-gray-50/50 flex items-center justify-end gap-3">
            <button 
                on:click={() => showModal = false}
                class="px-5 py-2 text-xs font-bold text-gray-500 hover:text-gray-700 transition-all flex items-center gap-2"
            >
                <Icon name="close" size={14} />
                Cancel
            </button>
            <button 
                on:click={handleSave}
                disabled={isSaving}
                class="px-6 py-2 bg-blue-600 text-white text-xs font-bold rounded-xl shadow-lg hover:bg-blue-700 disabled:opacity-50 transition-all flex items-center gap-2"
            >
                {#if isSaving}
                    <div class="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                {:else}
                    <Icon name="plus" size={14} />
                {/if}
                {isSaving ? 'Saving...' : editingMilestone ? 'Update Milestone' : 'Create Milestone'}
            </button>
        </div>
    </div>
</div>
{/if}

<style lang="scss">
    /* Add any custom animations if needed */
    .line-clamp-1 {
        display: -webkit-box;
        -webkit-line-clamp: 1;
        line-clamp: 1;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>