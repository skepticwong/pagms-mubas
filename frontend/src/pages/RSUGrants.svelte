<script>
  import axios from "axios";
  import { onMount, onDestroy } from "svelte";
  import Layout from "../components/Layout.svelte";
  import Icon from "../components/Icon.svelte";
  import { user } from "../stores/auth.js";
  import { router } from "../stores/router.js";
  import { showToast } from "../stores/toast.js";

  let grants = [];
  let filteredGrants = [];
  let isLoading = true;
  let searchTerm = "";
  let filterFunder = "all";
  let filterRisk = "all";
  let activeTab = "grants"; // "grants" or "extensions"
  let pendingExtensions = [];
  let isLoadingExtensions = false;

  // Institutional Summary
  let summary = {
    total: 0,
    amount: 0,
    critical: 0,
    active: 0
  };

  $: isRSU = $user?.role?.toString().toUpperCase() === "RSU";

  onMount(async () => {
    if (!isRSU) {
      router.goToDashboard();
      return;
    }
    await Promise.all([
      loadGrants(),
      loadExtensions()
    ]);
  });

  async function loadGrants() {
    try {
      isLoading = true;
      const res = await axios.get("/api/grants", { withCredentials: true });
      grants = res.data.grants || [];
      
      // Calculate Institutional Pulse
      summary.total = grants.length;
      summary.active = grants.filter(g => g.status === 'active').length;
      summary.critical = grants.filter(g => (g.spent_percent || 0) > 95).length;
      summary.amount = grants.reduce((sum, g) => sum + (g.total_budget || 0), 0) / 1000000; // in Millions

      applyFilters();
    } catch (err) {
      console.error(err);
      showToast("Failed to load institution grants.", "error");
    } finally {
      isLoading = false;
    }
  }

  async function loadExtensions() {
    try {
      isLoadingExtensions = true;
      const res = await axios.get("/api/extensions/pending", { withCredentials: true });
      pendingExtensions = res.data.extensions || [];
    } catch (err) {
      console.error(err);
      showToast("Failed to load extension requests.", "error");
    } finally {
      isLoadingExtensions = false;
    }
  }

  async function resolveExtension(extId, status) {
    const notes = prompt(`Comments for ${status}:`);
    if (notes === null) return;

    try {
      await axios.put(`/api/extensions/${extId}/resolve`, {
        status,
        notes
      }, { withCredentials: true });
      
      showToast(`Extension ${status} successfully.`, "success");
      await Promise.all([loadGrants(), loadExtensions()]);
    } catch (err) {
      showToast(err.response?.data?.error || "Failed to resolve extension.", "error");
    }
  }

  function applyFilters() {
    filteredGrants = grants.filter(g => {
      const matchSearch = g.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          g.grant_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          g.pi_id?.toString().includes(searchTerm);
      
      const matchFunder = filterFunder === "all" || g.funder === filterFunder;
      
      const risk = (g.spent_percent || 0);
      let matchRisk = true;
      if (filterRisk === "critical") matchRisk = risk >= 95;
      if (filterRisk === "at-risk") matchRisk = risk >= 80 && risk < 95;
      if (filterRisk === "on-track") matchRisk = risk < 80;

      return matchSearch && matchFunder && matchRisk;
    });
  }

  $: searchTerm, filterFunder, filterRisk, applyFilters();

  function formatMoney(amount, currency = "USD") {
    if (amount == null) return "-";
    return `${currency} ${amount.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
  }

  function getRiskLabel(percent) {
    if (percent >= 95) return { text: "Critical", class: "bg-rose-100 text-rose-700 border-rose-200", bar: "bg-rose-500", textClass: "text-rose-600" };
    if (percent >= 80) return { text: "At Risk", class: "bg-amber-100 text-amber-700 border-amber-200", bar: "bg-amber-500", textClass: "text-amber-500" };
    return { text: "On Track", class: "bg-emerald-100 text-emerald-700 border-emerald-200", bar: "bg-emerald-500", textClass: "text-gray-500" };
  }
</script>

<Layout>
  <div class="max-w-7xl mx-auto space-y-8">
    <!-- Header -->
    <header class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl shadow-lg p-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
      <div>
        <p class="text-xs uppercase tracking-[0.3em] text-blue-600 font-semibold mb-1">Institutional Oversight</p>
        <h1 class="text-3xl font-bold text-gray-900 tracking-tight">Master Grant List</h1>
        <p class="text-gray-600 mt-1 text-sm">Full lifecycle monitoring of the MUBAS research portfolio.</p>
      </div>
      
      <div class="flex items-center gap-3">
        <button 
          on:click={loadGrants}
          class="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-50 border border-gray-200 text-gray-700 hover:bg-gray-100 transition-all text-sm font-semibold"
        >
          <Icon name="refresh" size={16} />
          Refresh
        </button>
        <button 
          on:click={() => router.goToCreateGrant()}
          class="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 text-white hover:bg-blue-700 shadow-md shadow-blue-200 transition-all text-sm font-semibold"
        >
          <Icon name="plus" size={16} />
          Award New Grant
        </button>
      </div>
    </header>

    <!-- Institutional Pulse Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 p-5 rounded-2xl shadow-sm">
        <div class="flex justify-between items-start mb-3">
          <div class="p-2 bg-blue-50 rounded-lg text-blue-600">
            <Icon name="grant" size={20} />
          </div>
          <span class="text-[10px] font-bold text-blue-600 uppercase">Institutional</span>
        </div>
        <h3 class="text-2xl font-bold text-gray-900">{summary.total}</h3>
        <p class="text-xs text-gray-500 mt-1">Total grants awarded</p>
      </div>

      <div class="bg-white/70 backdrop-blur-xl border border-white/60 p-5 rounded-2xl shadow-sm">
        <div class="flex justify-between items-start mb-3">
          <div class="p-2 bg-emerald-50 rounded-lg text-emerald-600">
            <Icon name="money" size={20} />
          </div>
          <span class="text-[10px] font-bold text-emerald-600 uppercase">Funding</span>
        </div>
        <h3 class="text-2xl font-bold text-gray-900">${summary.amount.toFixed(1)}M</h3>
        <p class="text-xs text-gray-500 mt-1">Active portfolio value</p>
      </div>

      <div class="bg-white/70 backdrop-blur-xl border border-white/60 p-5 rounded-2xl shadow-sm">
        <div class="flex justify-between items-start mb-3">
          <div class="p-2 bg-rose-50 rounded-lg text-rose-600">
            <Icon name="warning" size={20} />
          </div>
          <span class="text-[10px] font-bold text-rose-600 uppercase">Audit Alert</span>
        </div>
        <h3 class="text-2xl font-bold text-gray-900">{summary.critical}</h3>
        <p class="text-xs text-gray-500 mt-1">Critical status (Burn &gt; 95%)</p>
      </div>

      <div class="bg-white/70 backdrop-blur-xl border border-white/60 p-5 rounded-2xl shadow-sm">
        <div class="flex justify-between items-start mb-3">
          <div class="p-2 bg-indigo-50 rounded-lg text-indigo-600">
            <Icon name="dashboard" size={20} />
          </div>
          <span class="text-[10px] font-bold text-indigo-600 uppercase">Live</span>
        </div>
        <h3 class="text-2xl font-bold text-gray-900">{summary.active}</h3>
        <p class="text-xs text-gray-500 mt-1">Active research projects</p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex gap-4 border-b border-gray-200">
      <button 
        on:click={() => activeTab = "grants"}
        class={`px-6 py-3 text-sm font-bold transition-all border-b-2 ${activeTab === 'grants' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
      >
        Institutional Portfolio
      </button>
      <button 
        on:click={() => activeTab = "extensions"}
        class={`px-6 py-3 text-sm font-bold transition-all border-b-2 flex items-center gap-2 ${activeTab === 'extensions' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
      >
        Extension Queue
        {#if pendingExtensions.length > 0}
          <span class="px-1.5 py-0.5 rounded-full bg-blue-100 text-blue-600 text-[10px]">{pendingExtensions.length}</span>
        {/if}
      </button>
    </div>

    <!-- Filters & Table -->
    <!-- Filters & Table -->
    {#if activeTab === 'grants'}
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl shadow-lg overflow-hidden">
        <div class="p-6 border-b border-gray-100 bg-gray-50/50 flex flex-wrap gap-4 items-center justify-between">
          <div class="flex flex-wrap gap-3 flex-1 min-w-[300px]">
            <div class="relative flex-1 max-w-sm">
              <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                <Icon name="search" size={16} />
              </span>
              <input 
                type="text" 
                placeholder="Search by code, title, or PI ID..."
                bind:value={searchTerm}
                class="w-full pl-10 pr-4 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm transition-all shadow-sm"
              />
            </div>
            <select 
              bind:value={filterFunder}
              class="px-4 py-2 rounded-xl border border-gray-200 text-sm outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="all">All Funders</option>
              <option value="wb">World Bank</option>
              <option value="nrf">NRF</option>
              <option value="usaid">USAID</option>
              <option value="dfid">DFID</option>
              <option value="gates">Gates Foundation</option>
            </select>
            <select 
              bind:value={filterRisk}
              class="px-4 py-2 rounded-xl border border-gray-200 text-sm outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="all">Any Risk Level</option>
              <option value="on-track">On Track (&lt; 80%)</option>
              <option value="at-risk">At Risk (80% - 95%)</option>
              <option value="critical">Critical (&gt; 95%)</option>
            </select>
          </div>
          
          <p class="text-xs font-semibold text-gray-500 bg-white px-3 py-1.5 rounded-lg border border-gray-100 shadow-sm">
            Showing {filteredGrants.length} of {grants.length} grants
          </p>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-gray-50/50 text-[10px] uppercase tracking-widest font-bold text-gray-500 border-b border-gray-100">
                <th class="px-6 py-4">Grant Identity</th>
                <th class="px-6 py-4">PI & Department</th>
                <th class="px-6 py-4 text-center">Lifecycle</th>
                <th class="px-6 py-4">Financial Status</th>
                <th class="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              {#each filteredGrants as grant}
                {@const risk = getRiskLabel(grant.spent_percent)}
                <tr class="hover:bg-blue-50/20 transition-colors group">
                  <td class="px-6 py-5">
                    <div class="flex flex-col">
                      <span class="text-xs font-black text-blue-600 mb-0.5 tracking-tighter">{grant.grant_code || "NEW-AWARD"}</span>
                      <span class="text-sm font-semibold text-gray-900 line-clamp-1">{grant.title}</span>
                      <div class="flex items-center gap-2 mt-1">
                        <span class="text-[10px] text-gray-400 capitalize bg-gray-100 px-1.5 py-0.5 rounded leading-none">{grant.funder}</span>
                        <span class="text-[10px] text-gray-400">Awarded: {new Date(grant.start_date).getFullYear()}</span>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-5">
                    <div class="flex items-center gap-3">
                      <div class="h-8 w-8 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center text-xs font-bold text-indigo-600 shadow-sm group-hover:scale-110 transition-transform">
                        PI
                      </div>
                      <div class="flex flex-col">
                        <span class="text-sm font-semibold text-gray-900 italic">PI ID: {grant.pi_id}</span>
                        <span class="text-xs text-gray-500">MUBAS Faculty</span>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-5 text-center">
                    <span class="px-2.5 py-1 rounded-full text-[10px] font-bold border {risk.class}">
                      {risk.text}
                    </span>
                  </td>
                  <td class="px-6 py-5">
                    <div class="flex flex-col w-48">
                      <div class="flex justify-between items-end mb-1.5">
                        <span class="text-xs font-bold text-gray-900">{formatMoney(grant.total_budget, grant.currency)}</span>
                        <span class="text-[10px] font-black {risk.textClass}">{grant.spent_percent?.toFixed(1)}%</span>
                      </div>
                      <div class="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden shadow-inner">
                        <div 
                          class="h-full rounded-full transition-all duration-1000 {risk.bar}"
                          style="width: {Math.min(grant.spent_percent || 0, 100)}%"
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-5 text-right">
                    <div class="flex justify-end gap-2">
                       <button 
                        class="p-2 rounded-lg hover:bg-white hover:shadow-md transition-all text-gray-400 hover:text-blue-600 border border-transparent hover:border-gray-100"
                        title="View Grant Detail"
                        on:click={() => router.goToGrantDetail(grant.id)}
                      >
                        <Icon name="approvals" size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              {:else}
                <tr>
                  <td colspan="5" class="py-20 text-center text-gray-500">
                    <Icon name="grant" size={48} className="mx-auto mb-4 text-gray-200" />
                    <p class="font-semibold text-lg">No institutional grants found</p>
                    <p class="text-sm">Try adjusting your filters or search term.</p>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    {:else}
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl shadow-lg overflow-hidden p-6">
        <div class="mb-6">
          <h2 class="text-xl font-bold text-gray-900">Timeline Adjustment Requests</h2>
          <p class="text-xs text-gray-500 mt-1">RSU verification of No-Cost Extensions (NCE)</p>
        </div>

        {#if isLoadingExtensions}
          <div class="py-20 text-center">
            <div class="w-10 h-10 border-4 border-blue-600/10 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
          </div>
        {:else if pendingExtensions.length === 0}
          <div class="py-20 text-center bg-gray-50 rounded-2xl border border-dashed border-gray-200">
             <Icon name="calendar" size={48} className="mx-auto mb-4 text-gray-200" />
             <p class="font-semibold text-gray-600">All extension requests resolved</p>
             <p class="text-sm text-gray-400">New requests from PIs will appear here.</p>
          </div>
        {:else}
          <div class="space-y-4">
            {#each pendingExtensions as ext}
              <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
                <div class="flex flex-col lg:flex-row justify-between gap-6">
                  <div class="flex-1">
                    <div class="flex items-center gap-3 mb-2">
                       <span class="text-xs font-black text-blue-600 tracking-tighter bg-blue-50 px-2 py-1 rounded">{ext.grant_code}</span>
                       <h3 class="text-sm font-bold text-gray-900">{ext.grant_title}</h3>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4 mt-4">
                      <div class="bg-gray-50 p-3 rounded-xl">
                        <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest">Current End Date</p>
                        <p class="text-sm font-semibold text-gray-600 line-through">{ext.current_end_date}</p>
                      </div>
                      <div class="bg-blue-50 p-3 rounded-xl border border-blue-100">
                        <p class="text-[10px] text-blue-400 uppercase font-bold tracking-widest">Requested End Date</p>
                        <p class="text-sm font-bold text-blue-700">{ext.requested_end_date}</p>
                      </div>
                    </div>

                    <div class="mt-4 p-4 bg-gray-50 rounded-xl">
                       <p class="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-1">PI Justification</p>
                       <p class="text-sm text-gray-700 italic">"{ext.justification}"</p>
                    </div>
                  </div>

                  <div class="flex flex-col justify-between items-end border-l border-gray-100 pl-6 lg:min-w-[200px]">
                    <div class="text-right">
                       <p class="text-xs font-bold text-gray-900">Submitted by</p>
                       <p class="text-xs text-gray-500">{ext.requester_name}</p>
                       <p class="text-[10px] text-gray-400 mt-1">{new Date(ext.created_at).toLocaleDateString()}</p>
                    </div>

                    <div class="flex gap-2 mt-6">
                       <button 
                         on:click={() => resolveExtension(ext.id, 'rejected')}
                         class="px-4 py-2 rounded-xl border border-red-200 text-red-600 text-xs font-bold hover:bg-red-50 transition-colors"
                       >
                         Reject
                       </button>
                       <button 
                         on:click={() => resolveExtension(ext.id, 'approved')}
                         class="px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-bold hover:bg-emerald-700 shadow-md shadow-emerald-100 transition-all"
                       >
                         Approve NCE
                       </button>
                    </div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}
  </div>
</Layout>

<style>
  /* Custom scrollbar for table */
  .overflow-x-auto::-webkit-scrollbar {
    height: 6px;
  }
  .overflow-x-auto::-webkit-scrollbar-track {
    background: transparent;
  }
  .overflow-x-auto::-webkit-scrollbar-thumb {
    background: #e2e8f0;
    border-radius: 10px;
  }
</style>
