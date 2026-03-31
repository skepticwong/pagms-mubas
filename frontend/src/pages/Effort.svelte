<script>
    import { onMount } from "svelte";
    import axios from "axios";
    import Layout from "../components/Layout.svelte";
    import { user } from "../stores/auth.js";
    import Icon from "../components/Icon.svelte";

    axios.defaults.withCredentials = true;

    let selectedGrant = "";
    let grants = [];
    let effortData = null;
    let loading = false;
    let error = "";
    let success = "";
    let status = { is_locked: false, message: "", severity: "info" };
    let selectedMonth = new Date().getMonth() + 1;
    let selectedYear = new Date().getFullYear();

    // Form for current user
    let certPercentage = "";
    let signature = "";
    let submitting = false;
    const monthOptions = Array.from({ length: 12 }, (_, i) => i + 1);
    const yearOptions = Array.from({ length: 6 }, (_, i) => new Date().getFullYear() - 4 + i);

    function monthName(month) {
        return new Date(2000, month - 1, 1).toLocaleString("en-US", { month: "long" });
    }

    onMount(async () => {
        await loadGrants();
    });

    async function loadGrants() {
        try {
            const response = await axios.get("/api/grants", { withCredentials: true });
            grants = response.data.grants || [];
            if (grants.length > 0) {
                selectedGrant = grants[0].id;
                await loadEffortData();
            }
        } catch (err) {
            error = "Failed to load grants";
        }
    }

    async function loadEffortData() {
        if (!selectedGrant) return;
        loading = true;
        error = "";
        try {
            // 1. Load Status (Lock/Warn)
            const statusRes = await axios.get(`/api/effort/status/${selectedGrant}`, {
                params: { month: selectedMonth, year: selectedYear }
            });
            status = statusRes.data;

            // 2. Load Effort Records
            const effortRes = await axios.get(`/api/effort/pending/${selectedGrant}`, {
                params: { month: selectedMonth, year: selectedYear }
            });
            effortData = effortRes.data;
            
            // Pre-fill form if self record exists
            const self = effortData.effort_records.find(r => r.is_self);
            if (self && self.certification) {
                certPercentage = self.certification.certified_percentage;
                signature = self.certification.signature_text;
            } else {
                certPercentage = "";
                signature = "";
            }
        } catch (err) {
            error = "Failed to load effort data";
        } finally {
            loading = false;
        }
    }

    async function submitCertification() {
        if (!certPercentage || !signature) {
            error = "Please provide both percentage and signature.";
            return;
        }

        submitting = true;
        error = "";
        success = "";

        try {
            const response = await axios.post("/api/effort/certify", {
                grant_id: selectedGrant,
                year: effortData.period.year,
                month: effortData.period.month,
                percentage: certPercentage,
                signature: signature,
                user_id: $user.id
            });
            success = "Effort certified successfully!";
            await loadEffortData();
        } catch (err) {
            error = err.response?.data?.error || "Failed to submit certification";
        } finally {
            submitting = false;
        }
    }

    $: canCertify = effortData && effortData.effort_records.every(r => r.is_self || r.is_certified);
</script>

<Layout>
    <div class="max-w-6xl mx-auto space-y-6 pb-12">
        <!-- Header -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="space-y-1">
                <h1 class="text-3xl font-extrabold text-slate-900 tracking-tight">Effort Certification</h1>
                <p class="text-slate-500">Review and certify professional effort for audit compliance.</p>
            </div>
            
            <div class="flex flex-wrap items-center gap-3">
                <label for="grant-select" class="text-sm font-semibold text-slate-700">Grant:</label>
                <select 
                    id="grant-select"
                    bind:value={selectedGrant} 
                    on:change={loadEffortData}
                    class="pl-4 pr-10 py-2.5 bg-white border border-slate-200 rounded-xl shadow-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all cursor-pointer font-medium text-slate-700"
                >
                    {#each grants as grant}
                        <option value={grant.id}>{grant.grant_code} - {grant.title}</option>
                    {/each}
                </select>

                <label for="month-select" class="text-sm font-semibold text-slate-700">Month:</label>
                <select
                    id="month-select"
                    bind:value={selectedMonth}
                    on:change={loadEffortData}
                    class="pl-4 pr-10 py-2.5 bg-white border border-slate-200 rounded-xl shadow-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all cursor-pointer font-medium text-slate-700"
                >
                    {#each monthOptions as month}
                        <option value={month}>{monthName(month)}</option>
                    {/each}
                </select>

                <label for="year-select" class="text-sm font-semibold text-slate-700">Year:</label>
                <select
                    id="year-select"
                    bind:value={selectedYear}
                    on:change={loadEffortData}
                    class="pl-4 pr-10 py-2.5 bg-white border border-slate-200 rounded-xl shadow-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all cursor-pointer font-medium text-slate-700"
                >
                    {#each yearOptions as year}
                        <option value={year}>{year}</option>
                    {/each}
                </select>
            </div>
        </div>

        <!-- Compliance Status Alert -->
        {#if effortData}
            <div class={`p-5 rounded-2xl border flex items-start gap-4 shadow-sm animate-in fade-in slide-in-from-top-4 duration-500 ${
                status.severity === 'error' ? 'bg-red-50 border-red-200 text-red-800' : 
                status.severity === 'warning' ? 'bg-amber-50 border-amber-200 text-amber-800' : 
                'bg-emerald-50 border-emerald-200 text-emerald-800'
            }`}>
                <div class="mt-0.5">
                    {#if status.severity === 'error'}<Icon name="alert-circle" size="24" />
                    {:else if status.severity === 'warning'}<Icon name="alert-triangle" size="24" />
                    {:else}<Icon name="check-circle" size="24" />{/if}
                </div>
                <div class="flex-1">
                    <h3 class="font-bold text-lg leading-tight">{status.is_locked ? 'Spending Blocked' : 'Compliance Status'}</h3>
                    <p class="mt-1 opacity-90 font-medium">{status.message}</p>
                    {#if status.is_locked}
                        <p class="mt-2 text-sm bg-red-100/50 p-2 rounded-lg border border-red-200/50 inline-block">
                            Complete certification to unlock expense submissions.
                        </p>
                    {/if}
                </div>
            </div>
        {/if}

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <!-- Team Progress Tracker -->
            <div class="lg:col-span-2 space-y-6">
                <div class="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
                    <div class="px-6 py-5 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
                        <h2 class="font-bold text-slate-800 flex items-center gap-2">
                            <Icon name="users" size="18" class="text-indigo-500" />
                            Effort Records: {effortData?.period?.month_name} {effortData?.period?.year}
                        </h2>
                        {#if effortData}
                            <span class="text-xs px-2.5 py-1 bg-white border border-slate-200 rounded-full font-bold text-slate-500 uppercase tracking-wider">
                                Period: {effortData.period.month}/{effortData.period.year}
                            </span>
                        {/if}
                    </div>

                    <div class="overflow-x-auto">
                        <table class="w-full text-left">
                            <thead>
                                <tr class="text-slate-400 text-xs font-bold uppercase tracking-widest bg-slate-50/30">
                                    <th class="px-6 py-4">Participant</th>
                                    <th class="px-6 py-4">Role</th>
                                    <th class="px-6 py-4">Logged Hours</th>
                                    <th class="px-6 py-4">Certified %</th>
                                    <th class="px-6 py-4">Status</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100">
                                {#if effortData && effortData.effort_records && effortData.effort_records.length > 0}
                                    {#each effortData.effort_records as record}
                                        <tr class={`hover:bg-slate-50/80 transition-colors ${record.is_self ? 'bg-indigo-50/30' : ''}`}>
                                            <td class="px-6 py-5">
                                                <div class="font-bold text-slate-800">
                                                    {record.user_name}
                                                    {#if record.is_self}
                                                        <span class="ml-2 text-[10px] bg-indigo-100 text-indigo-600 px-1.5 py-0.5 rounded-md uppercase">You</span>
                                                    {/if}
                                                </div>
                                            </td>
                                            <td class="px-6 py-5 text-slate-600 capitalize">{record.role}</td>
                                            <td class="px-6 py-5 font-mono text-slate-600 text-sm">{record.logged_hours}h</td>
                                            <td class="px-6 py-5 font-bold text-slate-800">
                                                {record.certification?.certified_percentage ? record.certification.certified_percentage + '%' : '—'}
                                            </td>
                                            <td class="px-6 py-5">
                                                {#if record.is_certified}
                                                    <span class="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-bold ring-1 ring-inset ring-emerald-200/50">
                                                        <Icon name="check" size="12" /> Certified
                                                    </span>
                                                {:else}
                                                    <span class="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 text-slate-500 rounded-full text-xs font-bold ring-1 ring-inset ring-slate-200/50">
                                                        Pending
                                                    </span>
                                                {/if}
                                            </td>
                                        </tr>
                                    {/each}
                                {:else if effortData}
                                    <tr>
                                        <td colspan="5" class="px-6 py-20 text-center text-slate-400 font-medium italic">
                                            No team members found for this grant.
                                        </td>
                                    </tr>
                                {:else}
                                    <tr>
                                        <td colspan="5" class="px-6 py-20 text-center">
                                            <div class="flex flex-col items-center gap-3 text-slate-400">
                                                <Icon name="loader" class="animate-spin" size="32" />
                                                <p class="font-medium">Loading effort records...</p>
                                            </div>
                                        </td>
                                    </tr>
                                {/if}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Certification Form -->
            <div class="lg:col-span-1">
                <div class="bg-white rounded-3xl shadow-lg border border-indigo-100 p-8 space-y-6 sticky top-6">
                    <h2 class="text-xl font-bold text-slate-900 border-b border-indigo-50 pb-4">My Certification</h2>

                    {#if error}
                        <div class="p-4 bg-red-50 border border-red-100 text-red-700 text-sm font-medium rounded-2xl flex items-center gap-3">
                            <Icon name="alert-circle" size="18" /> {error}
                        </div>
                    {/if}
                    {#if success}
                        <div class="p-4 bg-emerald-50 border border-emerald-100 text-emerald-700 text-sm font-medium rounded-2xl flex items-center gap-3">
                            <Icon name="check" size="18" /> {success}
                        </div>
                    {/if}

                    <div class="space-y-4">
                        <div>
                            <label for="cert-percentage" class="block text-sm font-bold text-slate-700 mb-2">Certified Effort %</label>
                            <div class="relative">
                                <input 
                                    id="cert-percentage"
                                    type="number" 
                                    step="0.1"
                                    bind:value={certPercentage}
                                    placeholder="e.g. 37.5"
                                    class="w-full pl-5 pr-12 py-3 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-indigo-500/10 focus:bg-white transition-all font-bold text-lg"
                                />
                                <span class="absolute right-5 top-1/2 -translate-y-1/2 font-bold text-slate-400">%</span>
                            </div>
                            <p class="mt-2 text-[11px] text-slate-400 font-medium">
                                This should reflect your total professional effort for this grant, regardless of logged hours.
                            </p>
                        </div>

                        <div>
                            <label for="cert-signature" class="block text-sm font-bold text-slate-700 mb-2">Digital Signature</label>
                            <input 
                                id="cert-signature"
                                type="text" 
                                bind:value={signature}
                                placeholder="Type your full name"
                                class="w-full px-5 py-3 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-indigo-500/10 focus:bg-white transition-all italic font-serif"
                            />
                        </div>

                        <div class="p-5 bg-indigo-50/50 rounded-2xl border border-indigo-100/50 space-y-3">
                            <label class="flex items-start gap-3 cursor-pointer group">
                                <input type="checkbox" class="mt-1 w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 border-indigo-300 transition-colors" />
                                <span class="text-[11px] text-indigo-900/70 font-medium leading-relaxed group-hover:text-indigo-950 transition-colors">
                                    I certify that the effort represented above reflects my total professional activity for this period. 
                                    I understand that false certification may be subject to legal and institutional action.
                                </span>
                            </label>
                        </div>

                        <button 
                            on:click={submitCertification}
                            disabled={submitting || !canCertify}
                            class={`w-full py-4 rounded-2xl font-extrabold text-white shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center gap-2 ${
                                canCertify ? 'bg-indigo-600 hover:bg-indigo-700 hover:-translate-y-0.5 active:scale-95' : 'bg-slate-300 cursor-not-allowed'
                            }`}
                        >
                            {#if submitting}
                                <Icon name="loader" class="animate-spin" size="20" /> Submitting...
                            {:else}
                                <Icon name="lock" size="18" /> Complete Certification
                            {/if}
                        </button>

                        {#if effortData && !canCertify && $user.role === 'PI'}
                            <div class="flex items-start gap-2 text-[10px] text-amber-600 font-bold bg-amber-50 p-3 rounded-xl border border-amber-100">
                                <Icon name="alert-triangle" size="14" class="mt-0.5 flex-shrink-0" />
                                <div>
                                    TEAM FIRST RULE: You cannot certify your effort until all team members have completed theirs.
                                </div>
                            </div>
                        {/if}
                    </div>
                </div>
            </div>
        </div>
    </div>
</Layout>

<style>
    :global(body) {
        background-color: #f8fafc;
    }
</style>
