<script>
  import { onMount } from "svelte";
  import axios from "axios";
  import Layout from "../components/Layout.svelte";
  import { router } from "../stores/router.js";
  import { user } from "../stores/auth.js";
  import TeamDashboard from "../dashboards/Team.svelte";

  let showPage = false;
  let financeView = false;
  let loading = true;
  let error = "";
  let tasks = [];
  let metrics = [
    { label: "Active Grants", value: 0, accent: "text-blue-600" },
    { label: "Pending Tasks", value: 0, accent: "text-amber-600" },
    { label: "Budget Used", value: "0%", accent: "text-emerald-600" },
    { label: "Alerts", value: 0, accent: "text-rose-600" },
  ];
  let budgetProgress = 0;
  let alerts = [];
  let pendingTasks = [];

  let initialized = false;

  // Finance dashboard state
  let financeInitialized = false;
  let financeLoading = true;
  let financeError = "";
  let financeData = null;
  let financeInsights = null;

  $: showPage = $user?.role === "PI";
  $: financeView = $user?.role === "Finance";
  $: teamView = $user?.role === "Team";

  $: if (showPage && !initialized) {
    initialized = true;
    loadDashboard();
  }

  onMount(() => {
    if (financeView && !financeInitialized) {
      financeInitialized = true;
      loadFinanceDashboard();
    }
  });

  async function loadDashboard() {
    loading = true;
    error = "";
    try {
      const response = await axios.get("http://localhost:5000/api/tasks", {
        withCredentials: true,
      });
      tasks = response.data?.tasks || [];
      deriveInsights();
    } catch (err) {
      error =
        err.response?.data?.error ||
        "Unable to load dashboard data. Please try again.";
    } finally {
      loading = false;
    }
  }

  function deriveInsights() {
    const activeGrantIds = new Set();
    const pending = [];
    const alertList = [];
    let estimatedHours = 0;
    let approvedHours = 0;

    tasks.forEach((task) => {
      if (task.grant_id) activeGrantIds.add(task.grant_id);
      const status = (task.status || "").toLowerCase();
      const est = Number(task.estimated_hours) || 0;
      estimatedHours += est;
      if (status === "approved") approvedHours += est;
      if (status === "submitted") pending.push(task);
      if (status === "overdue") {
        alertList.push(`Task “${task.title}” is overdue`);
      }
    });

    budgetProgress = estimatedHours
      ? Math.min(100, Math.round((approvedHours / estimatedHours) * 100))
      : 0;
    if (budgetProgress >= 90) {
      alertList.push("Budget utilisation exceeds 90% across your portfolio");
    }

    metrics = [
      {
        label: "Active Grants",
        value: activeGrantIds.size,
        accent: "text-blue-600",
      },
      {
        label: "Pending Tasks",
        value: pending.length,
        accent: "text-amber-600",
      },
      {
        label: "Budget Used",
        value: `${budgetProgress}%`,
        accent: "text-emerald-600",
      },
      { label: "Alerts", value: alertList.length, accent: "text-rose-600" },
    ];

    alerts = alertList;
    pendingTasks = pending;
  }

  $: piName = $user?.name?.replace(/^Dr\.?\s*/i, "") || "PI";
  $: welcomeCopy = `Welcome back, Dr. ${piName}!`;

  const toUSD = (value) =>
    `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;

  async function loadFinanceDashboard() {
    financeLoading = true;
    financeError = "";

    try {
      const [dashboardRes, burnRateRes, fxRatesRes, deadlinesRes] =
        await Promise.all([
          axios.get("http://localhost:5000/api/finance/dashboard", {
            withCredentials: true,
          }),
          axios.get("http://localhost:5000/api/finance/burn-rate", {
            withCredentials: true,
          }),
          axios.get("http://localhost:5000/api/finance/fx-rates", {
            withCredentials: true,
          }),
          axios.get("http://localhost:5000/api/finance/deadlines", {
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
</script>

{#if showPage}
  <Layout>
    <div class="max-w-7xl mx-auto space-y-8 py-2">
      <section
        class="bg-white/60 backdrop-blur-xl border border-white/60 rounded-3xl p-8 shadow-lg"
      >
        <div class="flex flex-col gap-2">
          <h1 class="text-3xl md:text-4xl font-bold text-gray-900">
            {welcomeCopy}
          </h1>
          <p class="text-base text-gray-600">
            This command center keeps your grants compliant, on-budget, and
            audit-ready.
          </p>
          <div class="flex flex-wrap gap-3 pt-2 text-sm text-gray-600">
            <span class="px-3 py-1 rounded-full bg-blue-50 text-blue-700"
              >Principal Investigator Workspace</span
            >
            <span class="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700"
              >Real-time oversight</span
            >
          </div>
        </div>
      </section>

      <section class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {#each metrics as metric}
          <div
            class="bg-white/65 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-md"
          >
            <p class="text-sm text-gray-600">{metric.label}</p>
            <p class={`mt-2 text-3xl font-bold ${metric.accent}`}>
              {metric.value}
            </p>
          </div>
        {/each}
      </section>

      <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 space-y-6">
          <div
            class="bg-white/65 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-md"
          >
            <div class="flex items-center justify-between mb-4">
              <div>
                <h2 class="text-2xl font-semibold text-gray-900">
                  Pending approvals
                </h2>
                <p class="text-sm text-gray-600">
                  Tasks awaiting your sign-off.
                </p>
              </div>
              <button
                class="px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                on:click={loadDashboard}
                disabled={loading}
              >
                {loading ? "Refreshing…" : "Refresh data"}
              </button>
            </div>

            {#if error}
              <div
                class="mb-4 p-4 rounded-xl border border-red-100 bg-red-50 text-red-700"
              >
                {error}
              </div>
            {/if}

            {#if loading}
              <div class="py-10 text-center text-sm text-gray-500">
                Loading grant activity…
              </div>
            {:else if pendingTasks.length === 0}
              <div class="py-10 text-center text-sm text-gray-500">
                No tasks are waiting for PI approval.
              </div>
            {:else}
              <div class="space-y-4">
                {#each pendingTasks as task}
                  <div
                    class="p-4 rounded-2xl border border-gray-100 bg-white/80 shadow-sm"
                  >
                    <div class="flex flex-col gap-2">
                      <div class="flex items-center justify-between">
                        <div>
                          <p class="text-base font-semibold text-gray-900">
                            {task.title}
                          </p>
                          <p class="text-sm text-gray-500">
                            {task.grant_title || "Unnamed grant"}
                          </p>
                        </div>
                        <span
                          class="px-3 py-1 text-xs font-semibold rounded-full bg-amber-100 text-amber-700"
                          >Submitted</span
                        >
                      </div>
                      <div
                        class="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm text-gray-600"
                      >
                        <p>
                          <span class="font-semibold text-gray-900"
                            >Assignee:</span
                          >
                          {task.assigned_to_name || "Team member"}
                        </p>
                        <p>
                          <span class="font-semibold text-gray-900"
                            >Deadline:</span
                          >
                          {task.deadline
                            ? new Date(task.deadline).toLocaleDateString()
                            : "N/A"}
                        </p>
                        <p>
                          <span class="font-semibold text-gray-900"
                            >Estimated hours:</span
                          >
                          {task.estimated_hours || 0}
                        </p>
                      </div>
                      <div class="flex flex-wrap gap-3 pt-2">
                        <button
                          class="px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          on:click={() => router.goToReviewEvidence()}
                        >
                          Review evidence
                        </button>
                        <button
                          class="px-4 py-2 text-sm font-semibold text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100"
                          on:click={() => router.goToTasks()}
                        >
                          Open task log
                        </button>
                      </div>
                    </div>
                  </div>
                {/each}
              </div>
            {/if}
          </div>

          <div
            class="bg-white/65 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-md"
          >
            <h2 class="text-2xl font-semibold text-gray-900">
              Getting started
            </h2>
            <p class="text-sm text-gray-600 mb-4">
              Quick reminders for compliant post-award execution.
            </p>
            <ul class="space-y-3 text-gray-700">
              <li class="flex gap-3">
                <span class="text-blue-600 font-semibold">•</span>
                <span
                  ><strong>Manage grants</strong> – register new awards and monitor
                  deliverables.</span
                >
              </li>
              <li class="flex gap-3">
                <span class="text-blue-600 font-semibold">•</span>
                <span
                  ><strong>Track tasks</strong> – assign work, review evidence, and
                  keep deadlines visible.</span
                >
              </li>
              <li class="flex gap-3">
                <span class="text-blue-600 font-semibold">•</span>
                <span
                  ><strong>Control budget</strong> – approve expenses early and prevent
                  overspending.</span
                >
              </li>
            </ul>
          </div>
        </div>

        <div class="space-y-6">
          <div
            class="bg-white/65 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-md"
          >
            <h2 class="text-xl font-semibold text-gray-900">
              Budget utilisation
            </h2>
            <p class="text-sm text-gray-600 mb-4">Across all active grants.</p>
            <div class="relative h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                class="absolute inset-y-0 left-0 bg-emerald-500"
                style={`width: ${budgetProgress}%`}
              ></div>
            </div>
            <p class="mt-2 text-sm text-gray-600">
              <span class="font-semibold text-gray-900">{budgetProgress}%</span>
              of estimated effort certified.
            </p>
          </div>

          <div
            class="bg-white/65 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-md"
          >
            <h2 class="text-xl font-semibold text-gray-900">Alerts</h2>
            <p class="text-sm text-gray-600 mb-4">
              Audit triggers and urgent follow-ups.
            </p>
            {#if loading}
              <p class="text-sm text-gray-500">Scanning for risks…</p>
            {:else if alerts.length === 0}
              <p class="text-sm text-gray-500">
                No outstanding alerts. Keep up the accountability.
              </p>
            {:else}
              <ul class="space-y-3">
                {#each alerts as alert}
                  <li class="flex items-start gap-3 text-sm text-rose-700">
                    <span class="mt-1 h-2 w-2 rounded-full bg-rose-500"></span>
                    <span>{alert}</span>
                  </li>
                {/each}
              </ul>
            {/if}
          </div>
        </div>
      </section>
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
              on:click={loadFinanceDashboard}
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
                on:click={() => router.goToPendingExpenses()}
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
                    <p class="text-xs text-gray-500">{item.stage}</p>
                  </div>
                  <div class="text-right">
                    <p class="font-semibold">{toUSD(item.amount / 1000)}K</p>
                    <p class="text-xs text-gray-500">{item.age}</p>
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
                on:click={() => router.goToApprovedTransactions()}
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
        on:click={() =>
          router.goToRoleHome?.($user?.role) ?? router.goToLogin()}
      >
        Go to my workspace
      </button>
    </div>
  </Layout>
{/if}
