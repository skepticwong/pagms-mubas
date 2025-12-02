<script>
  import { onMount } from 'svelte';
  import Layout from '../components/Layout.svelte';
  import axios from 'axios'; // Import axios

  axios.defaults.withCredentials = true; // Ensure cookies are sent

  let loading = true;
  let search = '';
  let currency = 'USD';
  let grants = [];
  let selectedGrant = null;
  let summary = {
    total_allocated: 0,
    total_spent: 0,
    avg_burn: 0,
    active_funders: 0,
    ethics_protected_projects: 0
  };

  onMount(async () => { // Made async
    try {
      const response = await axios.get('http://localhost:5000/api/pi-grants-budget'); // Fetch real data
      const data = response.data;
      
      summary = data.summary;

      // Map backend grant data to frontend expected structure
      grants = data.grants.map(g => ({
        id: g.id, // Keep original ID for selection
        code: g.grant_code,
        name: g.title,
        pi: g.pi.name, // Access PI name from relationship
        funder: g.funder,
        allocatedUSD: g.total_budget,
        spentUSD: g.total_budget * g.spent_percent / 100, // Derive spentUSD
        spent_percent: g.spent_percent, // Keep spent_percent for burn calculation
        categories: g.categories.map(cat => ({
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

    {#if selectedGrant}
      <section class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6 space-y-6">
        <div class="flex flex-wrap items-center gap-4">
          <div>
            <p class="text-sm text-gray-500">Grant focus</p>
            <h2 class="text-2xl font-semibold text-gray-900">{selectedGrant.name}</h2>
            <p class="text-xs text-gray-500">{selectedGrant.code} · {selectedGrant.funder}</p>
          </div>
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
      </section>
    {/if}
  </div>
</Layout>

