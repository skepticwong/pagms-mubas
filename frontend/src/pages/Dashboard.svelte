<script>
  import { onMount } from "svelte";
  import axios from "axios";
  import Layout from "../components/Layout.svelte";
  import { showToast } from "../stores/toast.js";
  import { confirm } from "../stores/modals.js";
  import { router } from "../stores/router.js";
  import { user } from "../stores/auth.js";
  import TeamDashboard from "../dashboards/Team.svelte";
  import PIDashboard from "../dashboards/PI.svelte";

  let showPage = $derived(isRole("PI"));
  let financeView = $derived(isRole("Finance"));
  let teamView = $derived(isRole("Team") || isRole("Researcher"));

  let initialized = $state(false);

  // Finance dashboard state
  let financeInitialized = $state(false);
  let financeLoading = $state(true);
  let financeError = $state("");
  let financeData = $state(null);
  let financeInsights = $state(null);

  function isRole(target) {
    if (!$user?.role) return false;
    const current = $user.role.toString().toUpperCase();
    const t = target.toString().toUpperCase();
    return current.includes(t);
  }


  // Navigation for Finance
  $effect(() => {
    if (financeView && !financeInitialized) {
      financeInitialized = true;
      loadFinanceDashboard();
    }
  });

  const toUSD = (value) =>
    `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;

  async function loadFinanceDashboard() {
    financeLoading = true;
    financeError = "";

    try {
      const [dashboardRes, burnRateRes, fxRatesRes, deadlinesRes] =
        await Promise.all([
          axios.get("/api/finance/dashboard", {
            withCredentials: true,
          }),
          axios.get("/api/finance/burn-rate", {
            withCredentials: true,
          }),
          axios.get("/api/finance/fx-rates", {
            withCredentials: true,
          }),
          axios.get("/api/finance/deadlines", {
            withCredentials: true,
          }),
        ]);

      financeData = {
        headline: dashboardRes.data.headline,
        disbursementQueue: dashboardRes.data.disbursementQueue,
        exceptions: dashboardRes.data.exceptions,
        alerts: dashboardRes.data.alerts,
        burnRate: burnRateRes.data.burnRate,
        rates: fxRatesRes.data.rates,
        deadlines: deadlinesRes.data.deadlines,
      };

      financeInsights = dashboardRes.data.insights;
    } catch (err) {
      console.error("Failed to load finance dashboard:", err);
      financeError =
        err.response?.data?.error ||
        "Failed to load finance data. Please try again.";
    } finally {
      financeLoading = false;
    }
  }

  async function releaseDisbursement(item) {
    let detailLabel = "";
    if (item.type === 'single') detailLabel = "Full Payment";
    else if (item.type === 'tranche') detailLabel = "Manual Tranche";
    else if (item.type === 'milestone') detailLabel = "Milestone Release";

    if (!await confirm(`Are you sure you want to release funds for ${item.grant}?\nType: ${detailLabel}\nAmount: ${toUSD(item.amount)}`)) return;
    
    const itemId = item.type === 'tranche' ? item.tranche_id : 
                  item.type === 'milestone' ? item.milestone_id : null;

    try {
      await axios.post("/api/finance/release-disbursement", {
        grant_id: item.grant_id,
        type: item.type,
        item_id: itemId
      }, { withCredentials: true });
      showToast("Disbursement released successfully!", "success");
      loadFinanceDashboard();
    } catch (err) {
      showToast(err.response?.data?.error || "Failed to release disbursement", "error");
    }
  }
</script>

{#if showPage}
  <Layout>
    <div class="max-w-7xl mx-auto py-2">
      <PIDashboard />
    </div>
  </Layout>
{:else if financeView}
  <Layout>
    <div class="max-w-7xl mx-auto space-y-8 py-2">
      <section
        class="bg-white/60 backdrop-blur-xl border border-white/60 rounded-3xl p-8 shadow-lg"
      >
        <div class="flex flex-col gap-3">
          <div>
            <p
              class="text-xs uppercase tracking-[0.3em] text-blue-600 font-semibold"
            >
              Finance Mission Control
            </p>
            <h1 class="text-3xl md:text-4xl font-bold text-gray-900">
              Institutional Finance Command Center
            </h1>
            <p class="text-base text-gray-600">
              Monitor disbursements, approvals, FX exposure, and compliance
              railguards across all grants.
            </p>
          </div>
          <div class="flex flex-wrap gap-3 text-xs text-gray-600">
            <span class="px-3 py-1 rounded-full bg-blue-50 text-blue-700"
              >Treasury & Compliance</span
            >
            <span class="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700"
              >Cashflow reliability</span
            >
            <button
              class="ml-auto px-4 py-2 text-xs font-semibold rounded-full border border-gray-200 text-gray-700"
              type="button"
              onclick={loadFinanceDashboard}
              disabled={financeLoading}
            >
              {financeLoading ? "Refreshing…" : "Refresh data"}
            </button>
          </div>
        </div>
      </section>

      <section class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <div
          class="p-5 rounded-2xl bg-white/65 border border-white/60 shadow-sm"
        >
          <p class="text-sm text-gray-600">Total portfolio</p>
          <p class="text-3xl font-bold text-gray-900">
            {toUSD(financeData?.headline.totalPortfolio ?? 0)}M
          </p>
          <p class="text-xs text-gray-500">Active grant value</p>
        </div>
        <div
          class="p-5 rounded-2xl bg-white/65 border border-white/60 shadow-sm"
        >
          <p class="text-sm text-gray-600">Disbursed YTD</p>
          <p class="text-3xl font-bold text-emerald-600">
            {toUSD(financeData?.headline.disbursed ?? 0)}M
          </p>
          <p class="text-xs text-gray-500">50% of total envelope</p>
        </div>
        <div
          class="p-5 rounded-2xl bg-white/65 border border-white/60 shadow-sm"
        >
          <p class="text-sm text-gray-600">Pending claims</p>
          <p class="text-3xl font-bold text-amber-600">
            {financeData?.headline.pendingClaims ?? 0}
          </p>
          <p class="text-xs text-gray-500">Need review in &lt; 5 days</p>
        </div>
        <div
          class="p-5 rounded-2xl bg-white/65 border border-white/60 shadow-sm"
        >
          <p class="text-sm text-gray-600">Variance window</p>
          <p class="text-3xl font-bold text-rose-600">
            {Math.round((financeData?.headline.variances ?? 0) * 100)}%
          </p>
          <p class="text-xs text-gray-500">Spend vs plan</p>
        </div>
      </section>

      <section class="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div class="xl:col-span-2 space-y-6">
          <div
            class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-md"
          >
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-2xl font-semibold text-gray-900">
                  Disbursement pipeline
                </h2>
                <p class="text-sm text-gray-600">
                  Track every claim before cash leaves treasury.
                </p>
              </div>
              <button
                class="text-sm font-semibold text-blue-600"
                type="button"
                onclick={() => router.goToPendingExpenses()}
              >
                Open pending expenses →
              </button>
            </div>
            <div class="mt-4 divide-y divide-gray-100">
              {#each financeData?.disbursementQueue || [] as item}
                <div
                  class="py-4 flex flex-wrap gap-4 justify-between text-sm text-gray-700"
                >
                  <div>
                    <p class="font-semibold text-gray-900">{item.grant}</p>
                    {#if item.is_disbursement}
                      <span class={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        item.type === 'single' ? 'bg-blue-100 text-blue-700' :
                        item.type === 'milestone' ? 'bg-purple-100 text-purple-700' :
                        'bg-emerald-100 text-emerald-700'
                      }`}>
                        {item.type === 'single' ? 'Full Payment' : 
                         item.type === 'milestone' ? 'Milestone Release' : 
                         'Tranche Due'}
                      </span>
                      <p class="text-xs text-gray-500 mt-1">{item.stage}</p>
                    {:else}
                      <p class="text-xs text-gray-500">{item.stage}</p>
                    {/if}
                  </div>
                  <div class="flex items-center gap-4">
                    <div class="text-right">
                      <p class="font-semibold">{toUSD(item.amount)}</p>
                      <p class="text-xs text-gray-500">{item.age}</p>
                    </div>
                    {#if item.is_disbursement}
                      <button 
                        onclick={() => releaseDisbursement(item)}
                        class="px-3 py-1.5 bg-gray-900 text-white text-[10px] font-bold rounded-lg hover:bg-emerald-600 transition-colors"
                      >
                        Release
                      </button>
                    {/if}
                  </div>
                </div>
              {/each}
            </div>
          </div>

          <div
            class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-md"
          >
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-2xl font-semibold text-gray-900">
                  Exception log
                </h2>
                <p class="text-sm text-gray-600">
                  High-risk transactions and audits.
                </p>
              </div>
              <button
                class="text-sm font-semibold text-blue-600"
                type="button"
                onclick={() => router.goToApprovedTransactions()}
              >
                View approvals →
              </button>
            </div>
            <div class="mt-4 space-y-4">
              {#each financeData?.exceptions || [] as exception}
                <div
                  class="p-4 rounded-2xl border border-rose-100 bg-rose-50/60 text-sm text-rose-900"
                >
                  <p class="font-semibold">{exception.grant}</p>
                  <p>{exception.issue}</p>
                  <p class="text-xs text-rose-700">
                    Action: {exception.action} · Owner: {exception.owner}
                  </p>
                </div>
              {/each}
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div
            class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-md"
          >
            <h3 class="text-lg font-semibold text-gray-900 mb-3">
              Cash & exposure snapshot
            </h3>
            <ul class="space-y-3 text-sm text-gray-700">
              <li class="flex items-center justify-between">
                <span>Cash coverage</span><span class="font-semibold"
                  >{financeInsights?.cashCoverage ?? 0} months</span
                >
              </li>
              <li class="flex items-center justify-between">
                <span>FX exposure</span><span class="font-semibold"
                  >{Math.round((financeInsights?.fxExposure ?? 0) * 100)}%</span
                >
              </li>
              <li class="flex items-center justify-between">
                <span>Overdue invoices</span><span class="font-semibold"
                  >{financeInsights?.overdueInvoices ?? 0}</span
                >
              </li>
              <li class="flex items-center justify-between">
                <span>Avg processing</span><span class="font-semibold"
                  >{financeInsights?.avgProcessingDays ?? 0} days</span
                >
              </li>
            </ul>
          </div>

          <div
            class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-md"
          >
            <h3 class="text-lg font-semibold text-gray-900 mb-3">
              FX reference board
            </h3>
            <div class="space-y-3 text-sm text-gray-700">
              {#each Object.entries(financeData?.rates || {}) as [currency, rate]}
                <div class="flex items-center justify-between">
                  <span class="font-semibold uppercase">{currency}</span>
                  <span class="text-xs text-gray-500"
                    >Buying {rate.buying} / Selling {rate.selling}</span
                  >
                </div>
              {/each}
            </div>
            <p class="mt-3 text-xs text-gray-500">
              Feeds align with RBM spot+1% buffer.
            </p>
          </div>
        </div>
      </section>

      <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div
          class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-md"
        >
          <h3 class="text-xl font-semibold text-gray-900">
            Burn-rate vs forecast
          </h3>
          <p class="text-sm text-gray-600 mb-4">Quarterly glidepath</p>
          <div class="space-y-3 text-sm text-gray-700">
            {#each financeData?.burnRate || [] as point}
              <div class="flex items-center justify-between">
                <span class="font-semibold text-gray-900">{point.label}</span>
                <div class="flex items-center gap-2">
                  <span class="text-emerald-600"
                    >Actual {Math.round(point.actual * 100)}%</span
                  >
                  <span class="text-gray-500"
                    >Plan {Math.round(point.forecast * 100)}%</span
                  >
                </div>
              </div>
            {/each}
          </div>
        </div>

        <div
          class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-md"
        >
          <h3 class="text-xl font-semibold text-gray-900">Deadlines radar</h3>
          <p class="text-sm text-gray-600 mb-3">Upcoming funder touchpoints</p>
          <ul class="space-y-3 text-sm text-gray-700">
            {#each financeData?.deadlines || [] as deadline}
              <li class="flex items-center justify-between">
                <div>
                  <p class="font-semibold text-gray-900">{deadline.label}</p>
                  <p class="text-xs text-gray-500">{deadline.grants} grants</p>
                </div>
                <span class="text-sm font-semibold text-blue-600"
                  >{deadline.date}</span
                >
              </li>
            {/each}
          </ul>
        </div>

        <div
          class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-md"
        >
          <h3 class="text-xl font-semibold text-gray-900">Finance alerts</h3>
          <p class="text-sm text-gray-600 mb-3">Controls needing attention</p>
          {#if (financeData?.alerts || []).length === 0}
            <p class="text-sm text-gray-500">All signals green.</p>
          {:else}
            <ul class="space-y-3 text-sm text-rose-700">
              {#each financeData.alerts as alert}
                <li class="flex items-start gap-2">
                  <span class="mt-1 h-2 w-2 rounded-full bg-rose-500"></span>
                  <span>{alert}</span>
                </li>
              {/each}
            </ul>
          {/if}
        </div>
      </section>
    </div>
  </Layout>
{:else if teamView}
  <Layout>
    <div class="max-w-7xl mx-auto py-2">
      <TeamDashboard />
    </div>
  </Layout>
{:else}
  <Layout>
    <div
      class="max-w-4xl mx-auto bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl p-8 mt-10 text-center shadow-lg"
    >
      <h1 class="text-2xl font-bold text-gray-900 mb-2">Access restricted</h1>
      <p class="text-gray-600">
        Only authorized personnel can view this dashboard.
      </p>
      <button
        class="mt-6 px-4 py-2 rounded-xl bg-blue-600 text-white"
        onclick={() =>
          router.goToRoleHome?.($user?.role) ?? router.goToLogin()}
      >
        Go to my workspace
      </button>
    </div>
  </Layout>
{/if}
