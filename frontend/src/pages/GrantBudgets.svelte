<script>
  import { onMount } from 'svelte';
  import Layout from '../components/Layout.svelte';
  import VirementModal from '../components/VirementModal.svelte';
  import NCERequestModal from '../components/NCERequestModal.svelte';
  import FinancialHealthWidget from '../components/FinancialHealthWidget.svelte';
  import axios from 'axios';

  axios.defaults.withCredentials = true; // Ensure cookies are sent

  let loading = true;
  let search = '';
  let currency = 'USD';
  let grants = [];
  let selectedGrant = null;
  let isVirementModalOpen = false;
  let summary = {
    total_allocated: 0,
    total_spent: 0,
    avg_burn: 0,
    active_funders: 0,
    ethics_protected_projects: 0
  };
  let virements = [];
  let loadingVirements = false;
  let intelligence = null;
  let loadingIntelligence = false;
  let extensions = [];
  let loadingExtensions = false;
  let isNCEModalOpen = false;

  onMount(async () => { // Made async
    try {
      const response = await axios.get('http://localhost:5000/api/pi-grants-budget'); // Fetch real data
      const data = response.data;
      
      summary = data.summary;

      // Map backend grant data to frontend expected structure
      grants = data.grants.map(g => ({
        id: g.id,
        code: g.grant_code,
        name: g.title,
        pi: g.pi.name,
        funder: g.funder,
        allocatedUSD: g.total_budget,
        spentUSD: g.total_budget * g.spent_percent / 100,
        spent_percent: g.spent_percent,
        end_date: g.end_date,
        categories: (g.categories || []).map(cat => ({
          label: cat.name,
          allocated: cat.allocated,
          spent: cat.spent
        }))
      }));

      if (grants.length > 0) {
        selectedGrant = grants[0];
      }
    } catch (error) {
      console.error('Failed to fetch PI grants budget data:', error);
      // Handle error, e.g., show an error message on the UI
    } finally {
      loading = false;
    }
  });

  function filteredGrants() {
    return grants.filter((grant) => `${grant.name} ${grant.code} ${grant.pi} ${grant.funder}`.toLowerCase().includes(search.toLowerCase()));
  }

  $: if (selectedGrant) {
    fetchVirements(selectedGrant.id);
    fetchIntelligence(selectedGrant.id);
    fetchExtensions(selectedGrant.id);
  }

  async function fetchIntelligence(grantId) {
    if (!grantId) return;
    loadingIntelligence = true;
    try {
      const response = await axios.get(`http://localhost:5000/api/grants/${grantId}/financial-intelligence`);
      intelligence = response.data;
    } catch (err) {
      console.error("Failed to fetch intelligence:", err);
      intelligence = null;
    } finally {
      loadingIntelligence = false;
    }
  }

  async function fetchVirements(grantId) {
    if (!grantId) return;
    loadingVirements = true;
    try {
      const response = await axios.get(`http://localhost:5000/api/virements/grant/${grantId}`);
      virements = response.data;
    } catch (err) {
      console.error("Failed to fetch virements:", err);
      virements = [];
    } finally {
      loadingVirements = false;
    }
  }

  async function fetchExtensions(grantId) {
    if (!grantId) return;
    loadingExtensions = true;
    try {
      const response = await axios.get(`http://localhost:5000/api/extensions/grant/${grantId}`);
      extensions = response.data.extensions;
    } catch (err) {
      console.error("Failed to fetch extensions:", err);
      extensions = [];
    } finally {
      loadingExtensions = false;
    }
  }

  async function refreshData() {
    // Re-fetch everything for a clean update
    loading = true;
    try {
      const response = await axios.get('http://localhost:5000/api/pi-grants-budget');
      const data = response.data;
      summary = data.summary;
      
      const newGrants = data.grants.map(g => ({
        id: g.id,
        code: g.grant_code,
        name: g.title,
        pi: g.pi.name,
        funder: g.funder,
        allocatedUSD: g.total_budget,
        spentUSD: g.total_budget * g.spent_percent / 100,
        spent_percent: g.spent_percent,
        end_date: g.end_date,
        categories: (g.categories || []).map(cat => ({
          label: cat.name,
          allocated: cat.allocated,
          spent: cat.spent
        }))
      }));

      // Update the selected grant too if it exists
      if (selectedGrant) {
        const updated = newGrants.find(g => g.id === selectedGrant.id);
        if (updated) selectedGrant = updated;
      }
      grants = newGrants;
      
      if (selectedGrant) {
        await fetchVirements(selectedGrant.id);
        await fetchIntelligence(selectedGrant.id);
        await fetchExtensions(selectedGrant.id);
      }
    } catch (err) {
      console.error("Refresh failed:", err);
    } finally {
      loading = false;
    }
  }

  function selectGrant(grant) {
    selectedGrant = grant;
  }

  function percent(value, total) {
    if (!total) return 0;
    return Math.min(100, Math.round((value / total) * 100));
  }

  function displayAmount(value) {
    const amount = currency === 'USD' ? value : value * 1705; // Assuming 1 USD = 1705 MWK
    const prefix = currency === 'USD' ? '$' : 'MK ';
    // Handle potential NaN if value is not a number
    if (isNaN(amount)) return `${prefix}0`;
    return prefix + amount.toLocaleString(undefined, { maximumFractionDigits: 0 });
  }
</script>

<Layout>
  <div class="max-w-7xl mx-auto space-y-8 py-4">
    <section class="bg-white/60 backdrop-blur-xl border border-white/60 rounded-3xl p-8 shadow-lg">
      <div class="flex flex-col gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.3em] text-blue-600 font-semibold">Finance · Budgets</p>
          <h1 class="text-3xl font-bold text-gray-900">Grant budget control room</h1>
          <p class="text-sm text-gray-600">Track allocations, approvals, and burn rate per funder portfolio.</p>
        </div>
        <div class="flex flex-wrap gap-3 text-xs text-gray-600">
          <span class="px-3 py-1 rounded-full bg-blue-50 text-blue-700">{summary.active_funders} active funders</span>
          <span class="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700">Avg burn {summary.avg_burn}%</span>
          <select class="ml-auto px-3 py-2 rounded-full border border-gray-200 text-xs" bind:value={currency}>
            <option value="USD">USD</option>
            <option value="MKW">MKW</option>
          </select>
        </div>
      </div>
    </section>

    <section class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      <div class="p-5 rounded-2xl bg-white/65 border border-white/60">
        <p class="text-sm text-gray-500">Total allocated</p>
        <p class="text-3xl font-bold text-gray-900">{displayAmount(summary.total_allocated)}</p>
        <p class="text-xs text-gray-500">Across active grants</p>
      </div>
      <div class="p-5 rounded-2xl bg-white/65 border border-white/60">
        <p class="text-sm text-gray-500">Certified spend</p>
        <p class="text-3xl font-bold text-emerald-600">{displayAmount(summary.total_spent)}</p>
        <p class="text-xs text-gray-500">{Math.round(summary.avg_burn)}% utilisation</p>
      </div>
      <div class="p-5 rounded-2xl bg-white/65 border border-white/60">
        <p class="text-sm text-gray-500">Variance cushion</p>
        <p class="text-3xl font-bold text-amber-600">{displayAmount(summary.total_allocated - summary.total_spent)}</p>
        <p class="text-xs text-gray-500">Available headroom</p>
      </div>
      <div class="p-5 rounded-2xl bg-white/65 border border-white/60">
        <p class="text-sm text-gray-500">Ethics-protected</p>
        <p class="text-3xl font-bold text-blue-600">{summary.ethics_protected_projects} projects</p>
        <p class="text-xs text-gray-500">Require RSU sign-off</p>
      </div>
    </section>

    {#if selectedGrant}
      <section class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6 space-y-6">
        <div class="flex flex-wrap items-center gap-4">
          <div>
            <p class="text-sm text-gray-500">Grant focus</p>
            <h2 class="text-2xl font-semibold text-gray-900">{selectedGrant.name}</h2>
            <p class="text-xs text-gray-500">{selectedGrant.code} · {selectedGrant.funder}</p>
          </div>
          <button 
            on:click={() => isVirementModalOpen = true}
            class="px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-semibold shadow-lg shadow-blue-100 hover:bg-blue-700 transition-all flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path></svg>
            Reallocate Funds
          </button>
          <button 
            on:click={() => isNCEModalOpen = true}
            class="px-4 py-2 rounded-xl bg-white border border-gray-200 text-gray-700 text-sm font-semibold shadow-sm hover:bg-gray-50 transition-all flex items-center gap-2"
          >
            <svg class="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            Request Extension
          </button>
          <div class="ml-auto flex gap-4 text-sm text-gray-700">
            <div>
              <p class="text-xs text-gray-500">Allocated</p>
              <p class="text-lg font-semibold">{displayAmount(selectedGrant.allocatedUSD)}</p>
            </div>
            <div>
              <p class="text-xs text-gray-500">Spent</p>
              <p class="text-lg font-semibold text-emerald-600">{displayAmount(selectedGrant.spentUSD)}</p>
            </div>
            <div>
              <p class="text-xs text-gray-500">Balance</p>
              <p class="text-lg font-semibold text-amber-600">{displayAmount(selectedGrant.allocatedUSD - selectedGrant.spentUSD)}</p>
            </div>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {#each selectedGrant.categories as cat}
            <div class="p-4 rounded-2xl border border-gray-100">
              <p class="text-xs text-gray-500">{cat.label}</p>
              <p class="text-lg font-semibold text-gray-900">{displayAmount(cat.spent)}</p>
              <div class="mt-2 h-2 rounded-full bg-gray-100 overflow-hidden">
                <div class="h-full bg-blue-500" style={`width: ${percent(cat.spent, cat.allocated)}%`}></div>
              </div>
              <p class="text-xs text-gray-500 mt-1">{percent(cat.spent, cat.allocated)}% of {displayAmount(cat.allocated)}</p>
            </div>
          {/each}
        </div>

        <!-- Intelligence & Forecasting -->
        <div class="pt-6 border-t border-gray-100">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-sm font-bold text-gray-900 uppercase tracking-tight">Intelligence & Forecasting</h3>
            <span class="text-[10px] text-gray-400 font-medium italic">Simulated vs Actual Forecast</span>
          </div>

          {#if loadingIntelligence}
            <div class="flex items-center justify-center py-12">
              <div class="w-8 h-8 border-4 border-blue-600/10 border-t-blue-600 rounded-full animate-spin"></div>
            </div>
          {:else if intelligence}
            <FinancialHealthWidget {intelligence} {currency} />
          {:else}
            <div class="p-8 text-center bg-gray-50 rounded-3xl border border-dashed border-gray-200">
              <p class="text-sm text-gray-500 font-medium">Unable to load financial forecasting at this time.</p>
            </div>
          {/if}
        </div>

        <!-- Reallocation History -->
        <div class="pt-6 border-t border-gray-100">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-gray-900 uppercase tracking-tight">Recent Reallocations</h3>
            <span class="text-[10px] text-gray-400 font-medium">Full Audit Trail</span>
          </div>
          
          {#if loadingVirements}
            <div class="flex items-center justify-center py-8">
              <div class="w-5 h-5 border-2 border-blue-600/20 border-t-blue-600 rounded-full animate-spin"></div>
            </div>
          {:else if virements.length === 0}
            <div class="bg-gray-50 rounded-2xl p-8 text-center border border-dashed border-gray-200">
              <div class="w-10 h-10 bg-white rounded-full flex items-center justify-center mx-auto mb-3 shadow-sm">
                <svg class="w-5 h-5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              </div>
              <p class="text-xs text-gray-500 font-medium">No budget shifts recorded yet.</p>
            </div>
          {:else}
            <div class="space-y-3">
              {#each virements as v}
                <div class="group bg-gray-50/50 hover:bg-white border border-gray-100 rounded-2xl p-4 transition-all hover:shadow-sm">
                  <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div class="flex items-center gap-4">
                      <div class="flex flex-col items-center justify-center px-3 py-1 bg-white border border-gray-200 rounded-xl min-w-[70px]">
                        <p class="text-[9px] font-black text-gray-400 uppercase tracking-tighter leading-none">Status</p>
                        <p class={`text-[10px] font-bold mt-1 uppercase ${
                          v.status === 'approved' ? 'text-emerald-600' : 
                          v.status === 'pending' ? 'text-amber-600' : 'text-red-600'
                        }`}>
                          {v.status}
                        </p>
                      </div>
                      <div>
                        <div class="flex items-center gap-2">
                          <span class="text-xs font-bold text-gray-700">{v.from_category_name}</span>
                          <svg class="w-3 h-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                          <span class="text-xs font-bold text-gray-700">{v.to_category_name}</span>
                        </div>
                        <p class="text-[10px] text-gray-500 mt-0.5">Requested by {v.requester_name} • {new Date(v.created_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                    
                    <div class="flex items-center gap-6">
                      <div class="text-right">
                        <p class="text-sm font-black text-gray-900">{displayAmount(v.amount)}</p>
                        <p class="text-[9px] text-gray-400 font-bold uppercase tracking-widest">Amount Shifted</p>
                      </div>
                      
                      {#if v.justification || v.resolver_comment}
                        <div class="w-px h-8 bg-gray-200 hidden md:block"></div>
                        <div class="max-w-[200px] hidden md:block">
                          <p class="text-[10px] text-gray-600 italic line-clamp-2">
                            "{v.resolver_comment || v.justification}"
                          </p>
                        </div>
                      {/if}
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
        <!-- Extension Timeline -->
        <div class="pt-6 border-t border-gray-100">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-gray-900 uppercase tracking-tight">Extension Timeline</h3>
            <span class="text-[10px] text-gray-400 font-medium">NCE Audit Trail</span>
          </div>
          
          {#if loadingExtensions}
            <div class="flex items-center justify-center py-8">
              <div class="w-5 h-5 border-2 border-blue-600/20 border-t-blue-600 rounded-full animate-spin"></div>
            </div>
          {:else if extensions.length === 0}
            <div class="bg-gray-50 rounded-2xl p-8 text-center border border-dashed border-gray-200">
              <p class="text-xs text-gray-500 font-medium">Original project timeline remains unchanged.</p>
            </div>
          {:else}
            <div class="space-y-3">
              {#each extensions as ext}
                <div class="group bg-gray-50/50 hover:bg-white border border-gray-100 rounded-2xl p-4 transition-all hover:shadow-sm">
                  <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div class="flex items-center gap-4">
                      <div class={`px-3 py-1 rounded-full text-[10px] font-bold uppercase ${
                        ext.status === 'approved' ? 'bg-emerald-50 text-emerald-700' : 
                        ext.status === 'pending' ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700'
                      }`}>
                        {ext.status}
                      </div>
                      <div>
                        <div class="flex items-center gap-2">
                          <span class="text-xs font-bold text-gray-500 line-through">{ext.current_end_date}</span>
                          <svg class="w-3 h-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                          <span class="text-xs font-bold text-blue-600">{ext.requested_end_date}</span>
                        </div>
                        <p class="text-[10px] text-gray-500 mt-0.5">
                          Requested by {ext.requester_name} • {new Date(ext.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    
                    <div class="flex items-center gap-4">
                      {#if ext.justification}
                        <div class="max-w-[200px] hidden md:block">
                          <p class="text-[10px] text-gray-600 italic line-clamp-1">"{ext.justification}"</p>
                        </div>
                      {/if}
                      {#if ext.document_id}
                         <a href={`http://localhost:5000/api/documents/${ext.document_id}/download`} target="_blank" class="p-2 bg-white border border-gray-200 rounded-lg text-blue-600 hover:text-blue-700 shadow-sm">
                           <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                         </a>
                      {/if}
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </section>
    {/if}

    <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6 space-y-4">
        <div class="flex flex-wrap items-center gap-3">
          <input
            class="flex-1 min-w-[220px] px-4 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            type="search"
            placeholder="Search grant, PI, or funder"
            bind:value={search}
          />
        </div>
        <div class="border border-dashed border-gray-200 rounded-2xl">
          <div class="grid grid-cols-12 px-5 py-3 text-xs font-semibold text-gray-500 uppercase">
            <span class="col-span-3">Grant</span>
            <span class="col-span-3">Funder / PI</span>
            <span class="col-span-2">Allocated</span>
            <span class="col-span-2">Spent</span>
            <span class="col-span-1">Burn</span>
            <span class="col-span-1"></span>
          </div>
          {#if loading}
            <div class="p-8 text-center text-sm text-gray-500">Loading budgets…</div>
          {:else}
            {#each filteredGrants() as grant}
              <div class="grid grid-cols-12 px-5 py-4 border-t border-gray-100 text-sm text-gray-800">
                <div class="col-span-3">
                  <p class="font-semibold text-gray-900">{grant.name}</p>
                  <p class="text-xs text-gray-500">{grant.code}</p>
                </div>
                <div class="col-span-3">
                  <p>{grant.funder}</p>
                  <p class="text-xs text-gray-500">PI: {grant.pi}</p>
                </div>
                <div class="col-span-2">
                  <p class="font-semibold">{displayAmount(grant.allocatedUSD)}</p>
                </div>
                <div class="col-span-2">
                  <p class="font-semibold text-emerald-600">{displayAmount(grant.spentUSD)}</p>
                </div>
                <div class="col-span-1">
                  <span class={`px-2 py-1 rounded-full text-xs font-semibold ${grant.spent_percent > 80 ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'}`}>
                    {Math.round(grant.spent_percent)}%
                  </span>
                </div>
                <div class="col-span-1 flex justify-end">
                  <button class="text-xs font-semibold text-blue-600" type="button" on:click={() => selectGrant(grant)}>View</button>
                </div>
              </div>
            {/each}
          {/if}
        </div>
      </div>

      <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6">
        <h2 class="text-lg font-semibold text-gray-900">Portfolio notes</h2>
        <ul class="mt-4 space-y-2 text-sm text-gray-700">
          <li>• USAID grants trending +5% FX exposure vs plan.</li>
          <li>• World Bank projects need IFR reconciliations by 12 Feb.</li>
          <li>• STEM labs roll-out awaiting MKW top-up from Treasury.</li>
        </ul>
      </div>
    </section>
  </div>

  {#if selectedGrant}
    <VirementModal 
      grant={selectedGrant} 
      bind:isOpen={isVirementModalOpen} 
      on:success={() => {
        refreshData();
      }}
    />
    <NCERequestModal 
      grant={selectedGrant}
      bind:isOpen={isNCEModalOpen}
      on:success={() => {
        refreshData();
      }}
    />
  {/if}
</Layout>

<style>
  /* Custom transition for gauge */
  circle {
    transition: stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1);
  }
</style>

