<!-- frontend/src/pages/Grants.svelte -->
<script>
  import axios from "axios";
  import { onMount } from "svelte";
  import Layout from "../components/Layout.svelte";
  import { router } from "../stores/router.js";
  import { user } from "../stores/auth.js";
  import ReportModal from "../components/ReportModal.svelte";
  import DocumentTab from "../components/DocumentTab.svelte";
import MilestonesTab from "../components/MilestonesTab.svelte";

  let grants = [];
  let isLoading = true;
  let error = "";

  let selectedGrant = null;
  let showNewGrant = true;
  let showReportModal = false;
  let reportGrant = null;
  let activeTab = "overview"; // overview, documents, tasks, expenses

  const isRole = (target) => {
    if (!$user?.role) return false;
    const current = $user.role.toString().toUpperCase();
    const t = target.toString().toUpperCase();
    return current.includes(t);
  };

  onMount(async () => {
    if (!$user || (!isRole("PI") && !isRole("RSU") && !isRole("Finance"))) {
      router.goToDashboard();
      return;
    }

    try {
      const res = await axios.get("/api/grants", {
        withCredentials: true,
      });
      // Map backend fields to frontend expected fields
      grants = res.data.grants.map((g) => ({
        ...g,
        code: g.grant_code,
        total_usd: g.total_budget,
        agreement_url:
          "/api/uploads/agreements/" + g.agreement_filename,
      }));
    } catch (err) {
      console.error(err);
      error = "Failed to load grants.";
    } finally {
      isLoading = false;
    }
  });

  function formatMoney(amount) {
    if (amount == null) return "-";
    return amount.toLocaleString("en-US", { maximumFractionDigits: 0 });
  }

  function formatDate(dateStr) {
    if (!dateStr) return "N/A";
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  function spentBadgeClass(percent) {
    if (percent <= 70) return "bg-emerald-100 text-emerald-800";
    if (percent <= 90) return "bg-amber-100 text-amber-800";
    return "bg-rose-100 text-rose-800";
  }

  function spentBarClass(percent) {
    if (percent <= 70) return "bg-emerald-500";
    if (percent <= 90) return "bg-amber-500";
    return "bg-rose-500";
  }

  function openDetails(grant) {
    selectedGrant = grant;
  }

  function closeDetails() {
    selectedGrant = null;
  }

  function handleAssignTasks(grant) {
    // Later: pass grant id via store/route param
    router.goToTasks();
  }

  function handleSubmitExpense(grant) {
    router.goToExpenses();
  }

  function handleGenerateReport(grant) {
    reportGrant = grant;
    showReportModal = true;
  }
</script>

<Layout>
  <div class="p-4 md:p-6 lg:p-8">
    <div class="max-w-7xl mx-auto space-y-6">
      <!-- Header -->
      <div
        class="flex flex-col md:flex-row md:items-center md:justify-between gap-3"
      >
        <div>
          <h1 class="text-2xl md:text-3xl font-bold text-gray-900">
            My Grants
          </h1>
          <p class="text-sm text-gray-600">
            Overview of grants you lead, with budget, deadlines, and quick
            actions.
          </p>
        </div>
        {#if showNewGrant}
          <button
            type="button"
            class="inline-flex items-center justify-center px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-semibold shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            on:click={() => router.goToCreateGrant()}
          >
            + New Grant
          </button>
        {/if}
      </div>

      <!-- List vs details -->
      <!-- List vs details -->
      {#if isLoading}
        <div class="flex flex-col items-center justify-center py-24">
          <div
            class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"
          ></div>
          <p class="text-gray-500 font-medium">Loading your grants...</p>
        </div>
      {:else if error}
        <div
          class="p-8 text-center rounded-2xl bg-red-50 border border-red-200 text-red-700 mx-auto max-w-lg mt-8"
        >
          <span class="text-4xl block mb-4">⚠️</span>
          <h3 class="font-bold text-lg mb-2">Unable to load grants</h3>
          <p class="mb-6">{error}</p>
          <button
            class="px-5 py-2.5 bg-white border border-red-300 rounded-xl font-medium shadow-sm hover:bg-red-50 transition-colors"
            on:click={() => window.location.reload()}
          >
            Try Again
          </button>
        </div>
      {:else if !selectedGrant}
        {#if grants.length === 0}
          <div
            class="text-center py-20 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-300 mt-4"
          >
            <span class="text-5xl block mb-4">📂</span>
            <h3 class="text-xl font-bold text-gray-900 mb-2">
              No active grants found
            </h3>
            <p class="text-gray-500 mb-6 max-w-sm mx-auto">
              Get started by initializing your first grant project in the
              system.
            </p>
            <button
              type="button"
              class="px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold shadow-lg hover:bg-blue-700 transition-all transform hover:scale-105"
              on:click={() => router.goToCreateGrant()}
            >
              + Create First Grant
            </button>
          </div>
        {:else}
          <!-- Grant list view: mobile cards, desktop table -->
          <div class="space-y-4">
            <!-- Mobile: cards -->
            <div class="space-y-4 md:hidden">
              {#each grants as grant}
                <article
                  class="bg-white/80 backdrop-blur-xl border border-white/60 rounded-2xl shadow-sm p-4 space-y-3"
                >
                  <header class="flex items-start justify-between gap-2">
                    <div>
                      <h2 class="text-base font-semibold text-gray-900">
                        {grant.title}
                      </h2>
                      <p class="text-xs text-gray-600">
                        {grant.funder} •
                        <span class="font-mono text-gray-700">{grant.code}</span> •
                        <span class="font-semibold text-blue-600 uppercase tracking-tighter ml-1">
                          {grant.disbursement_type?.replace('_', ' ') || 'standard'}
                        </span>
                      </p>
                    </div>
                    <span
                      class="px-2 py-1 text-xs font-semibold rounded-full
                    {grant.status === 'active'
                        ? 'bg-emerald-100 text-emerald-800'
                        : grant.status === 'pending'
                          ? 'bg-amber-100 text-amber-800 animate-pulse'
                          : 'bg-gray-100 text-gray-700'}"
                    >
                      {grant.status === "pending"
                        ? "Pending Approval"
                        : grant.status.charAt(0).toUpperCase() +
                          grant.status.slice(1)}
                    </span>
                  </header>

                  <div class="grid grid-cols-2 gap-3 text-xs text-gray-700">
                    <div>
                      <p class="font-semibold text-gray-900">Duration</p>
                      <p>
                        {formatDate(grant.start_date)} – {formatDate(
                          grant.end_date,
                        )}
                      </p>
                    </div>
                    <div>
                      <p class="font-semibold text-gray-900">Total budget</p>
                      <p>${formatMoney(grant.total_usd)} USD</p>
                      <p>{formatMoney(grant.total_mwk)} MWK</p>
                    </div>
                    <div>
                      <p class="font-semibold text-gray-900">% spent</p>
                      <div class="flex items-center gap-2 mt-1">
                        <div
                          class="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden"
                          aria-hidden="true"
                        >
                          <div
                            class={"h-2 rounded-full " +
                              spentBarClass(grant.spent_percent)}
                            style={"width:" +
                              Math.min(grant.spent_percent, 100) +
                              "%"}
                          ></div>
                        </div>
                        <span
                          class={"px-2 py-0.5 rounded-full text-[11px] font-semibold " +
                            spentBadgeClass(grant.spent_percent)}
                        >
                          {grant.spent_percent}%
                        </span>
                      </div>
                    </div>
                    <div>
                      <p class="font-semibold text-gray-900">Project progress</p>
                      <div class="flex items-center gap-2 mt-1">
                        <div
                          class="flex-1 h-2 rounded-full bg-blue-50 overflow-hidden"
                          aria-hidden="true"
                        >
                          <div
                            class="h-2 rounded-full bg-blue-600"
                            style={"width:" +
                              Math.min(grant.project_progress_percentage, 100) +
                              "%"}
                          ></div>
                        </div>
                        <span
                          class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-100 text-blue-800"
                        >
                          {grant.project_progress_percentage}%
                        </span>
                      </div>
                    </div>
                    <div>
                      <p class="font-semibold text-gray-900">Next deadline</p>
                      <p>
                        {#if grant.next_deadline_date}
                          {grant.next_deadline_label}: {formatDate(
                            grant.next_deadline_date,
                          )}
                        {:else}
                          N/A
                        {/if}
                      </p>
                    </div>
                  </div>

                  <div class="flex flex-wrap gap-2 pt-2">
                    <button
                      type="button"
                      class="px-3 py-1.5 rounded-lg border border-gray-300 text-xs font-semibold text-gray-800 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      on:click={() => openDetails(grant)}
                    >
                      View Details
                    </button>
                    <button
                      type="button"
                      class="px-3 py-1.5 rounded-lg border border-blue-200 text-xs font-semibold text-blue-700 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      on:click={() => handleAssignTasks(grant)}
                    >
                      Assign Tasks
                    </button>
                    <button
                      type="button"
                      class="px-3 py-1.5 rounded-lg border border-emerald-200 text-xs font-semibold text-emerald-700 hover:bg-emerald-50 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      on:click={() => handleSubmitExpense(grant)}
                    >
                      Submit Expense
                    </button>
                    <button
                      type="button"
                      class="px-3 py-1.5 rounded-lg border border-amber-200 text-xs font-semibold text-amber-700 hover:bg-amber-50 focus:outline-none focus:ring-2 focus:ring-amber-500"
                      on:click={() => handleGenerateReport(grant)}
                    >
                      Generate Report
                    </button>
                  </div>
                </article>
              {/each}
            </div>

            <!-- Desktop: minimal table -->
            <div
              class="hidden md:block bg-white/80 backdrop-blur-xl border border-white/60 rounded-2xl shadow-sm overflow-hidden"
            >
              <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200 text-sm">
                  <thead class="bg-gray-50">
                    <tr>
                      <th
                        scope="col"
                        class="px-4 py-3 text-left font-semibold text-gray-700"
                        >Grant</th
                      >
                      <th
                        scope="col"
                        class="px-4 py-3 text-left font-semibold text-gray-700"
                        >Status</th
                      >
                      <th
                        scope="col"
                        class="px-4 py-3 text-left font-semibold text-gray-700"
                        >Duration</th
                      >
                      <th
                        scope="col"
                        class="px-4 py-3 text-left font-semibold text-gray-700"
                        >Budget (USD / MWK)</th
                      >
                      <th
                        scope="col"
                        class="px-4 py-3 text-left font-semibold text-gray-700"
                        >Next deadline</th
                      >
                      <th
                        scope="col"
                        class="px-4 py-3 text-left font-semibold text-gray-700"
                        >Metrics</th
                      >
                      <th
                        scope="col"
                        class="px-4 py-3 text-left font-semibold text-gray-700"
                        >Actions</th
                      >
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-100 bg-white">
                    {#each grants as grant (grant.id)}
                      <tr class="hover:bg-gray-50">
                        <td class="px-4 py-3 align-top">
                          <div class="font-semibold text-gray-900">
                            {grant.title}
                          </div>
                          <div class="text-xs text-gray-600">
                            {grant.funder} •
                            <span class="font-mono text-gray-700">{grant.code}</span> •
                            <span class="font-semibold text-blue-600 uppercase tracking-tighter">
                                {grant.disbursement_type?.replace('_', ' ') || 'standard'}
                            </span>
                          </div>
                        </td>
                        <td class="px-4 py-3 align-top">
                          <span
                            class="inline-flex px-2 py-1 text-xs font-semibold rounded-full
                          {grant.status === 'active'
                              ? 'bg-emerald-100 text-emerald-800'
                              : grant.status === 'pending'
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-gray-100 text-gray-700'}"
                          >
                            {grant.status === "pending"
                              ? "Pending Approval"
                              : grant.status.charAt(0).toUpperCase() +
                                grant.status.slice(1)}
                          </span>
                        </td>
                        <td class="px-4 py-3 align-top text-xs text-gray-700">
                          {formatDate(grant.start_date)}<br />
                          – {formatDate(grant.end_date)}
                        </td>
                        <td class="px-4 py-3 align-top text-xs text-gray-700">
                          ${formatMoney(grant.total_usd)} USD<br />
                          {formatMoney(grant.total_mwk)} MWK
                        </td>
                        <td class="px-4 py-3 align-top text-xs text-gray-700">
                          {#if grant.next_deadline_date}
                            <span class="font-semibold text-gray-900"
                              >{grant.next_deadline_label}</span
                            ><br />
                            {formatDate(grant.next_deadline_date)}
                          {:else}
                            N/A
                          {/if}
                        </td>
                        <td class="px-4 py-3 align-top min-w-[140px]">
                          <div class="space-y-2">
                             <!-- Spent bar -->
                             <div class="space-y-0.5">
                                <div class="flex items-center justify-between text-[10px] font-bold">
                                   <span class="text-gray-500 uppercase tracking-tighter">Spent</span>
                                   <span class={spentBadgeClass(grant.spent_percent)}>{grant.spent_percent}%</span>
                                </div>
                                <div class="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                                   <div class={"h-full " + spentBarClass(grant.spent_percent)} style={"width:" + Math.min(grant.spent_percent, 100) + "%"}></div>
                                </div>
                             </div>
                             <!-- Progress bar -->
                             <div class="space-y-0.5">
                                <div class="flex items-center justify-between text-[10px] font-bold">
                                   <span class="text-blue-500 uppercase tracking-tighter">Progress</span>
                                   <span class="text-blue-600">{grant.project_progress_percentage}%</span>
                                </div>
                                <div class="h-1.5 w-full bg-blue-50 rounded-full overflow-hidden">
                                   <div class="h-full bg-blue-600" style={"width:" + Math.min(grant.project_progress_percentage, 100) + "%"}></div>
                                </div>
                             </div>
                          </div>
                        </td>
                        <td class="px-4 py-3 align-top">
                          <div class="flex flex-wrap gap-1.5">
                            <button
                              type="button"
                              class="px-2.5 py-1 rounded-lg border border-gray-300 text-[11px] font-semibold text-gray-800 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                              on:click={() => openDetails(grant)}
                            >
                              View Details
                            </button>
                            <button
                              type="button"
                              class="px-2.5 py-1 rounded-lg border border-blue-200 text-[11px] font-semibold text-blue-700 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                              on:click={() => handleAssignTasks(grant)}
                            >
                              Assign Tasks
                            </button>
                            <button
                              type="button"
                              class="px-2.5 py-1 rounded-lg border border-emerald-200 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-50 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                              on:click={() => handleSubmitExpense(grant)}
                            >
                              Submit Expense
                            </button>
                            <button
                              type="button"
                              class="px-2.5 py-1 rounded-lg border border-amber-200 text-[11px] font-semibold text-amber-700 hover:bg-amber-50 focus:outline-none focus:ring-2 focus:ring-amber-500"
                              on:click={() => handleGenerateReport(grant)}
                            >
                              Generate Report
                            </button>
                          </div>
                        </td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        {/if}
      {:else}
        <!-- Grant detail view -->
        <section class="space-y-4">
          <button
            type="button"
            class="inline-flex items-center gap-1 text-sm text-blue-700 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
            on:click={closeDetails}
          >
            ← Back to My Grants
          </button>

          <div
            class="bg-white/80 backdrop-blur-xl border border-white/60 rounded-3xl shadow-sm p-4 md:p-6 space-y-6"
          >
            <!-- Tab Navigation -->
            <div
              class="flex flex-wrap gap-1 p-1 bg-gray-100/50 rounded-2xl w-fit"
            >
              <button
                on:click={() => (activeTab = "overview")}
                class="px-5 py-2 text-xs font-black uppercase tracking-widest rounded-xl transition-all {activeTab ===
                'overview'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'}"
              >
                Overview
              </button>
              <button
                on:click={() => (activeTab = "documents")}
                class="px-5 py-2 text-xs font-black uppercase tracking-widest rounded-xl transition-all {activeTab ===
                'documents'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'}"
              >
                Documents
              </button>
              <button
                on:click={() => (activeTab = "tasks")}
                class="px-5 py-2 text-xs font-black uppercase tracking-widest rounded-xl transition-all {activeTab ===
                'tasks'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'}"
              >
                Tasks
              </button>
              <button
                on:click={() => (activeTab = "expenses")}
                class="px-5 py-2 text-xs font-black uppercase tracking-widest rounded-xl transition-all {activeTab ===
                'expenses'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'}"
              >
                Expenses
              </button>
              <button
                on:click={() => (activeTab = "milestones")}
                class="px-5 py-2 text-xs font-black uppercase tracking-widest rounded-xl transition-all {activeTab ===
                'milestones'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'}"
              >
                Milestones
              </button>
            </div>

            {#if activeTab === "overview"}
              <!-- Header -->
              <header class="space-y-1 pt-2">
                <h2 class="text-xl md:text-2xl font-bold text-gray-900">
                  {selectedGrant.title}
                </h2>
                <p class="text-sm text-gray-700">
                  {selectedGrant.funder} •
                  <span class="font-mono text-gray-800"
                    >{selectedGrant.code}</span
                  >
                </p>
                <div class="flex flex-wrap items-center gap-2 pt-1">
                  <span
                    class="inline-flex px-2.5 py-1 text-xs font-semibold rounded-full
                  {selectedGrant.status === 'active'
                      ? 'bg-emerald-100 text-emerald-800'
                      : selectedGrant.status === 'pending'
                        ? 'bg-amber-100 text-amber-800 animate-pulse'
                        : 'bg-gray-100 text-gray-700'}"
                  >
                    {selectedGrant.status === "pending"
                      ? "Pending Approval"
                      : selectedGrant.status.charAt(0).toUpperCase() +
                        selectedGrant.status.slice(1)}
                  </span>
                  <span class="text-xs text-gray-600">
                    {formatDate(selectedGrant.start_date)} – {formatDate(
                      selectedGrant.end_date,
                    )}
                  </span>
                </div>
              </header>

              <!-- Agreement and exchange rate -->
              <div class="grid gap-4 md:grid-cols-2">
                <div class="space-y-2">
                  <h3 class="text-sm font-semibold text-gray-900">
                    Grant Agreement
                  </h3>
                  <a
                    href={selectedGrant.agreement_url}
                    class="inline-flex items-center text-sm text-blue-700 underline hover:text-blue-800"
                  >
                    View / Download agreement (PDF)
                  </a>
                </div>
                <div class="space-y-2">
                  <h3 class="text-sm font-semibold text-gray-900">
                    Budget &amp; Exchange Rate
                  </h3>
                  <p class="text-sm text-gray-700">
                    Total: <span class="font-semibold"
                      >${formatMoney(selectedGrant.total_usd)} USD</span
                    >
                    (<span class="font-semibold"
                      >{formatMoney(selectedGrant.total_mwk)} MWK</span
                    >)
                  </p>
                  <p class="text-sm text-gray-700">
                    {selectedGrant.exchange_rate_label}
                  </p>
                  <div class="mt-1 space-y-3">
                    <div>
                      <p class="text-[10px] font-black uppercase tracking-widest text-gray-500">Budget spent</p>
                      <div class="flex items-center gap-2 mt-1">
                        <div
                          class="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden"
                          aria-hidden="true"
                        >
                          <div
                            class={"h-2 rounded-full " +
                              spentBarClass(selectedGrant.spent_percent)}
                            style={"width:" +
                              Math.min(selectedGrant.spent_percent, 100) +
                              "%"}
                          ></div>
                        </div>
                        <span
                          class={"px-2 py-0.5 rounded-full text-[11px] font-semibold " +
                            spentBadgeClass(selectedGrant.spent_percent)}
                        >
                          {selectedGrant.spent_percent}%
                        </span>
                      </div>
                    </div>
                    <div>
                      <p class="text-[10px] font-black uppercase tracking-widest text-blue-500">Project progress</p>
                      <div class="flex items-center gap-2 mt-1">
                        <div
                          class="flex-1 h-2 rounded-full bg-blue-50 overflow-hidden"
                          aria-hidden="true"
                        >
                          <div
                            class="h-2 rounded-full bg-blue-600"
                            style={"width:" +
                              Math.min(selectedGrant.project_progress_percentage, 100) +
                              "%"}
                          ></div>
                        </div>
                        <span
                          class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-100 text-blue-800"
                        >
                          {selectedGrant.project_progress_percentage}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Budget breakdown -->
              <div class="space-y-2">
                <h3 class="text-sm font-semibold text-gray-900">
                  Budget breakdown by category
                </h3>
                <div class="space-y-2">
                  {#each selectedGrant.categories as cat}
                    {@const percent = Math.round(
                      (cat.spent / cat.allocated) * 100,
                    )}
                    <div class="space-y-1">
                      <div
                        class="flex items-center justify-between text-xs text-gray-700"
                      >
                        <span class="font-semibold text-gray-900"
                          >{cat.name}</span
                        >
                        <span>
                          {formatMoney(cat.spent)} / {formatMoney(
                            cat.allocated,
                          )} USD ({percent}%)
                        </span>
                      </div>
                      <div class="h-2 rounded-full bg-gray-100 overflow-hidden">
                        <div
                          class={"h-2 rounded-full " + spentBarClass(percent)}
                          style={"width:" + Math.min(percent, 100) + "%"}
                        ></div>
                      </div>
                    </div>
                  {/each}
                </div>
              </div>

              <!-- Tabs / sections summary -->
              <div class="border-t border-gray-100 pt-4 space-y-3">
                <h3 class="text-sm font-semibold text-gray-900">
                  Project activity overview
                </h3>
                <div
                  class="grid gap-3 md:grid-cols-2 lg:grid-cols-4 text-xs text-gray-700"
                >
                  <div class="p-3 rounded-xl bg-gray-50 border border-gray-100">
                    <p class="font-semibold text-gray-900 mb-1">Tasks</p>
                    <p>
                      View assigned and completed tasks linked to this grant.
                    </p>
                  </div>
                  <div class="p-3 rounded-xl bg-gray-50 border border-gray-100">
                    <p class="font-semibold text-gray-900 mb-1">Expenses</p>
                    <p>
                      See submitted and approved spending that uses this budget.
                    </p>
                  </div>
                  <div class="p-3 rounded-xl bg-gray-50 border border-gray-100">
                    <p class="font-semibold text-gray-900 mb-1">Deliverables</p>
                    <p>
                      Access verified fieldwork and activity deliverables from your
                      team.
                    </p>
                  </div>
                  <div class="p-3 rounded-xl bg-gray-50 border border-gray-100">
                    <p class="font-semibold text-gray-900 mb-1">Compliance</p>
                    <p>
                      Track upcoming deliverables, audits, and reporting
                      deadlines.
                    </p>
                  </div>
                </div>
              </div>

              <!-- Detail actions -->
              <div class="flex flex-wrap gap-2 pt-2">
                <button
                  type="button"
                  class="px-3 py-1.5 rounded-lg border border-blue-200 text-xs font-semibold text-blue-700 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  on:click={() => handleAssignTasks(selectedGrant)}
                >
                  Assign Tasks
                </button>
                <button
                  type="button"
                  class="px-3 py-1.5 rounded-lg border border-emerald-200 text-xs font-semibold text-emerald-700 hover:bg-emerald-50 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  on:click={() => handleSubmitExpense(selectedGrant)}
                >
                  Submit Expense
                </button>
                <button
                  type="button"
                  class="px-3 py-1.5 rounded-lg border border-amber-200 text-xs font-semibold text-amber-700 hover:bg-amber-50 focus:outline-none focus:ring-2 focus:ring-amber-500"
                  on:click={() => handleGenerateReport(selectedGrant)}
                >
                  Generate Report
                </button>
              </div>
            {:else if activeTab === "documents"}
              <DocumentTab
                grantId={selectedGrant.id}
                grantTitle={selectedGrant.title}
              />
            {:else if activeTab === "tasks"}
              <div
                class="p-12 text-center text-gray-500 bg-gray-50 rounded-2xl border border-dashed border-gray-200"
              >
                <p class="text-3xl mb-2">🔜</p>
                <p class="text-sm font-bold uppercase tracking-widest">
                  Task Management Integration
                </p>
                <p class="text-xs mt-1 italic">
                  This tab will feature contextual task assignments for this
                  grant module.
                </p>
              </div>
            {:else if activeTab === "expenses"}
              <div
                class="p-12 text-center text-gray-500 bg-gray-50 rounded-2xl border border-dashed border-gray-200"
              >
                <p class="text-3xl mb-2">💰</p>
                <p class="text-sm font-bold uppercase tracking-widest">
                  Expense Ledger Integration
                </p>
                <p class="text-xs mt-1 italic">
                  This tab will feature a filtered expense list specific to this
                  grant's budget categories.
                </p>
              </div>
            {:else if activeTab === "milestones"}
              <MilestonesTab
                grantId={selectedGrant.id}
                grantTitle={selectedGrant.title}
                disbursementType={selectedGrant.disbursement_type}
              />
            {/if}
          </div>
        </section>
      {/if}
    </div>
  </div>

  {#if showReportModal}
    <ReportModal
      grant={reportGrant}
      on:close={() => (showReportModal = false)}
    />
  {/if}
</Layout>
