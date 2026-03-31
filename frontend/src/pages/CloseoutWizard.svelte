<script>
  import { onMount } from "svelte";
  import { router } from "../stores/router.js";
  import { showToast } from "../stores/toast.js";
  import Layout from "../components/Layout.svelte";
  import Icon from "../components/Icon.svelte";

  let grants = [];
  let loadingGrants = true;
  let grantId = null;

  let statusData = null;
  let loading = false;
  let error = null;
  let isLocking = false;
  let lockSuccess = false;
  let finalReport = null;
  let archiveHash = null;
  let archivedAt = null;

  const authHeaders = () => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  });

  onMount(async () => {
    try {
      const res = await fetch("http://localhost:5000/api/grants", {
        credentials: "include",
        headers: authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        grants = data.grants || [];
        if (grants.length === 1) {
          grantId = grants[0].id;
          await fetchStatus();
        }
      } else {
        error = "Failed to load your grants.";
      }
    } catch (e) {
      error = "Network error loading grants.";
    } finally {
      loadingGrants = false;
    }
  });

  async function onGrantChange() {
    statusData = null;
    finalReport = null;
    archiveHash = null;
    archivedAt = null;
    lockSuccess = false;
    error = null;
    if (grantId) await fetchStatus();
  }

  async function fetchStatus() {
    loading = true;
    error = null;
    try {
      const res = await fetch(
        `http://localhost:5000/api/grants/${grantId}/closeout-status`,
        { credentials: "include", headers: authHeaders() }
      );
      if (res.ok) {
        statusData = await res.json();
        if (statusData.is_archived) await fetchFinalReport();
      } else {
        const err = await res.json();
        error = err.error || "Failed to fetch closeout status.";
      }
    } catch (e) {
      error = "Network connection failed.";
    } finally {
      loading = false;
    }
  }

  async function fetchFinalReport() {
    try {
      const res = await fetch(
        `http://localhost:5000/api/grants/${grantId}/final-report`,
        { credentials: "include", headers: authHeaders() }
      );
      if (res.ok) {
        const data = await res.json();
        finalReport = data.report;
        archiveHash = data.archive_hash;
        archivedAt = data.archived_at;
      }
    } catch (e) {
      console.error("Failed to fetch final report", e);
    }
  }

  async function lockArchive() {
    isLocking = true;
    try {
      const res = await fetch(
        `http://localhost:5000/api/grants/${grantId}/lock-archive`,
        { method: "POST", credentials: "include", headers: authHeaders() }
      );
      if (res.ok) {
        lockSuccess = true;
        await fetchFinalReport();
      } else {
        const err = await res.json();
        showToast("Failed to lock archive: " + err.error, "error");
      }
    } catch (e) {
      showToast("Network connection failed.", "error");
    } finally {
      isLocking = false;
    }
  }

  function resolveGate(key) {
    switch (key) {
      case 'financial':
        router.goToExpenses();
        break;
      case 'assets':
        router.goToAssets();
        break;
      case 'personnel':
        router.goToEffort();
        break;
      case 'deliverables':
        router.goToTasks();
        break;
      default:
        showToast("No resolution path specified for this gate.", "info");
    }
  }

  async function downloadDossier() {
    if (!grantId) return;
    try {
      const response = await fetch(
        `http://localhost:5000/api/grants/${grantId}/download-dossier`,
        { credentials: "include", headers: authHeaders() }
      );
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        
        // Find current grant for better filename
        const currentGrant = grants.find(g => g.id === grantId);
        const grantCode = currentGrant ? currentGrant.grant_code : grantId;
        
        a.download = `Closeout_Dossier_${grantCode}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        showToast("Dossier download started.", "success");
      } else {
        const err = await response.json();
        showToast("Failed to download dossier: " + (err.error || "Unknown error"), "error");
      }
    } catch (e) {
      showToast("Network error during download.", "error");
    }
  }
</script>

<Layout>
  <div class="max-w-5xl w-full mx-auto px-4 py-8">
    <button on:click={() => router.goToDashboard()} class="text-sm font-medium text-blue-600 mb-6 flex items-center hover:underline">
      ← Back to Dashboard
    </button>

    <!-- Grant Selector Card -->
    {#if loadingGrants}
      <div class="flex items-center gap-3 mb-6 p-4 bg-white/60 backdrop-blur-xl border border-white/60 rounded-2xl shadow-sm">
        <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
        <span class="text-sm text-gray-500">Loading your grants...</span>
      </div>
    {:else if grants.length === 0}
      <div class="mb-6 p-6 bg-amber-50/70 backdrop-blur-md border border-amber-200/60 rounded-2xl text-center shadow-sm">
        <Icon name="folder" size={32} class="text-amber-400 mx-auto mb-2" />
        <p class="text-sm font-bold text-amber-800">No grants found</p>
        <p class="text-xs text-amber-600 mt-1">You must be assigned to a grant to use the Closeout Wizard.</p>
      </div>
    {:else}
      <div class="mb-6 bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-5 shadow-md space-y-2">
        <label for="closeout-grant-selector" class="block text-xs font-black uppercase tracking-widest text-gray-500">
          <span class="flex items-center gap-2"><Icon name="folder" size={14} />Select Grant to Closeout</span>
        </label>
        <select
          id="closeout-grant-selector"
          bind:value={grantId}
          on:change={onGrantChange}
          class="w-full bg-white border border-gray-200 rounded-xl px-4 py-3 text-sm font-semibold text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none shadow-sm"
        >
          <option value={null} disabled>— Choose a grant —</option>
          {#each grants as grant}
            <option value={grant.id}>{grant.grant_code} — {grant.title}</option>
          {/each}
        </select>
      </div>
    {/if}

    {#if grantId}
    <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl shadow-lg overflow-hidden">
      <div class="px-6 py-8 border-b border-white/20 bg-gray-900/80 text-white backdrop-blur-xl">
        <div class="flex items-center justify-between mb-2">
          <h1 class="text-3xl font-bold font-serif text-primary">Grant Closeout Gate</h1>
          <div class="bg-blue-500/20 text-blue-100 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border border-blue-400/30">
            Closeout Wizard
          </div>
        </div>
        <p class="text-gray-300 max-w-3xl">
          The system enforces a strict "Hard Gate" policy. You cannot generate a fully verified closure report or archive this grant until all 4 compliance pillars are 100% resolved.
        </p>
      </div>

      <div class="p-6">
        {#if loading}
          <div class="flex items-center justify-center p-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        {:else if error}
          <div class="p-4 bg-red-50 text-red-600 rounded-md">{error}</div>
        {:else if finalReport}
          
          <!-- Final Report Immutable View -->
          <div class="space-y-8 animate-fade-in">
            <div class="bg-gradient-to-r from-emerald-800 to-indigo-900 rounded-xl p-8 text-white shadow-xl flex flex-col md:flex-row items-center gap-6 justify-between">
              <div>
                <h2 class="text-3xl font-bold font-serif">Immutable Archival Record</h2>
                <p class="text-emerald-100 mt-2">This grant has been successfully closed, reconciled, and mathematically sealed.</p>
              </div>
              <div class="bg-black/30 p-4 rounded-lg backdrop-blur border border-white/20 w-full md:w-auto">
                <p class="text-xs text-emerald-200 uppercase tracking-widest font-bold mb-1">SHA-256 Fingerprint</p>
                <code class="font-mono text-xs break-all text-white select-all">{archiveHash}</code>
                <p class="text-xs text-gray-300 mt-2">Sealed on: {new Date(archivedAt).toLocaleString()}</p>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <!-- Financials -->
              <div class="bg-white/50 backdrop-blur-md border border-white/60 rounded-2xl p-6 shadow-sm">
                <h3 class="text-xl font-bold text-gray-900 border-b pb-2 mb-4">Financial Reconciliation</h3>
                <div class="flex justify-between items-end mb-6">
                  <div>
                    <p class="text-sm text-gray-500 font-medium">Total Spend Utilization</p>
                    <p class="text-3xl font-bold text-indigo-600">{finalReport.financial_summary.overall_utilization}%</p>
                  </div>
                  <div class="text-right">
                    <p class="text-sm text-gray-500 font-medium">Total Spent</p>
                    <p class="text-lg font-bold text-gray-900">${finalReport.financial_summary.total_spent.toLocaleString()}</p>
                  </div>
                </div>
                <div class="space-y-3">
                  {#each finalReport.financial_summary.categories as cat}
                    <div class="flex justify-between text-sm">
                      <span class="text-gray-700 font-medium">{cat.category}</span>
                      <span class="text-gray-900">${cat.actual_spend.toLocaleString()} / <span class="text-gray-500">${cat.approved_amount.toLocaleString()}</span></span>
                    </div>
                    <div class="w-full bg-gray-100 rounded-full h-1.5 mb-4">
                      <div class="bg-indigo-600 h-1.5 rounded-full" style="width: {Math.min(cat.utilized_percent, 100)}%"></div>
                    </div>
                  {/each}
                </div>
              </div>

              <!-- KPIs & Assets -->
              <div class="space-y-6">
                <!-- Assets -->
                <div class="bg-white/50 backdrop-blur-md border border-white/60 rounded-2xl p-6 shadow-sm">
                  <h3 class="text-xl font-bold text-gray-900 border-b pb-2 mb-4">Asset Disposition Log</h3>
                  {#if finalReport.asset_disposition_log.length === 0}
                    <p class="text-sm text-gray-500 italic">No assets registered to this grant.</p>
                  {:else}
                    <ul class="space-y-3">
                      {#each finalReport.asset_disposition_log as asset}
                        <li class="flex justify-between items-center text-sm border-b border-gray-50 pb-2">
                          <div>
                            <p class="font-bold text-gray-800">{asset.name}</p>
                            <p class="text-xs text-gray-500">{asset.asset_tag}</p>
                          </div>
                          <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-bold rounded capitalize">{asset.final_status}</span>
                        </li>
                      {/each}
                    </ul>
                  {/if}
                </div>

                <!-- KPIs -->
                <div class="bg-white/50 backdrop-blur-md border border-white/60 rounded-2xl p-6 shadow-sm">
                  <h3 class="text-xl font-bold text-gray-900 border-b pb-2 mb-4">Impact Delivery</h3>
                  {#if finalReport.kpi_achievements.length === 0}
                    <p class="text-sm text-gray-500 italic">No KPIs tracked.</p>
                  {:else}
                    <ul class="space-y-3">
                      {#each finalReport.kpi_achievements as kpi}
                        <li class="text-sm">
                          <div class="flex justify-between font-bold text-gray-800 mb-1">
                            <span>{kpi.name}</span>
                            <span class="{kpi.achieved >= kpi.target ? 'text-green-600' : 'text-amber-600'} w-12 text-right">
                              {Math.round((kpi.achieved / kpi.target) * 100)}%
                            </span>
                          </div>
                          <p class="text-xs text-gray-500">{kpi.achieved} / {kpi.target} achieved</p>
                        </li>
                      {/each}
                    </ul>
                  {/if}
                </div>
              </div>
            </div>

            <div class="mt-8 flex justify-center">
              <button 
                on:click={downloadDossier}
                class="px-8 py-3 bg-gray-900 text-white font-bold rounded-lg shadow hover:bg-black hover:-translate-y-0.5 transition-all text-sm flex items-center gap-2"
              >
                <Icon name="download" size={20} />
                Download PDF Dossier
              </button>
            </div>
          </div>

        {:else if statusData}

          <!-- Gate Summary -->
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            {#each Object.entries(statusData.checklist) as [key, data]}
              <div class="p-4 rounded-2xl flex flex-col items-center justify-center text-center transition-colors shadow-sm backdrop-blur-md {data.ready ? 'border-green-200/60 bg-green-50/70 border' : 'border-red-200/60 bg-red-50/70 border'}">
                <div class="h-10 w-10 rounded-full flex items-center justify-center {data.ready ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'} mb-3">
                  {#if data.ready}
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                  {:else}
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                  {/if}
                </div>
                <h3 class="font-bold text-gray-800 capitalize">{key}</h3>
                <p class="text-xs font-medium mt-1 {data.ready ? 'text-green-600' : 'text-red-600'}">
                  {data.ready ? 'Cleared' : 'Blocked'}
                </p>
              </div>
            {/each}
          </div>

          <!-- detailed checklist -->
          <div class="space-y-6">
            {#each Object.entries(statusData.checklist) as [key, data]}
              <div class="p-5 border border-white/60 rounded-2xl bg-white/50 backdrop-blur-md shadow-sm">
                <div class="flex items-start justify-between">
                  <div>
                    <h3 class="text-lg font-bold text-gray-900 capitalize italic">{key} Accountability</h3>
                    {#if data.ready}
                      <p class="text-sm text-green-600 font-medium mt-1">All compliance checks passed.</p>
                    {:else}
                      <p class="text-sm text-red-600 font-medium mt-1">Outstanding actions required to clear this tier:</p>
                      <ul class="mt-3 space-y-2">
                        {#each data.blockers as blocker}
                          <li class="flex items-start gap-2 text-sm text-gray-700 bg-gray-50 p-2 rounded border border-gray-100">
                             <span class="text-red-500 mt-0.5">•</span>
                             {blocker}
                          </li>
                        {/each}
                      </ul>
                    {/if}
                  </div>
                  {#if data.ready}
                    <span class="px-3 py-1 bg-green-100 text-green-800 text-xs font-bold rounded-full">VERIFIED</span>
                  {:else}
                    <button 
                      on:click={() => resolveGate(key)}
                      class="text-xs font-medium text-blue-600 bg-blue-50 px-3 py-1 rounded hover:bg-blue-100 transition-all active:scale-95"
                    >
                      Resolve →
                    </button>
                  {/if}
                </div>
              </div>
            {/each}
          </div>

          <!-- Bottom Action Bar -->
          <div class="mt-10 pt-6 border-t border-gray-200 flex items-center justify-between">
            <p class="text-sm text-gray-500 max-w-xl">
              When all gates are green, you will be able to lock the grant and generate the final immutable reporting dossier.
            </p>

            {#if lockSuccess}
              <div class="px-4 py-2 bg-green-100 text-green-800 rounded font-bold flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                Archive Locked & Verified
              </div>
            {:else}
              <button 
                on:click={lockArchive}
                disabled={!statusData.is_ready || isLocking}
                class="px-6 py-3 rounded-lg font-bold text-white transition-all shadow-md
                  {statusData.is_ready ? 'bg-green-600 hover:bg-green-700 hover:shadow-lg' : 'bg-gray-300 cursor-not-allowed text-gray-500 shadow-none'}"
              >
                {isLocking ? 'Archiving...' : 'Lock Grant Archive'}
              </button>
            {/if}
          </div>

        {/if}
      </div>
    </div>
    {/if}
  </div>
</Layout>
