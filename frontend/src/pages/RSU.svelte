<script>
  import axios from "axios";
  import { onMount, onDestroy } from "svelte";
  import Layout from "../components/Layout.svelte";
  import Icon from "../components/Icon.svelte";
  import { user } from "../stores/auth.js";
  import { router } from "../stores/router.js";
  import { rsuNavTarget, clearRsuNavTarget } from "../stores/rsuNav.js";

  let loading = true;
  let error = "";
  // Initialize with safe defaults to prevent template errors
  let rsuData = {
    summary: {
      totalGrants: 0,
      onTrack: 0,
      atRisk: 0,
      critical: 0,
      totalFunding: 0,
      fundsUsed: 0,
      fundsAtRisk: 0,
      upcomingReports: 0,
      compliance: {
        auditsPending: 0,
        auditsPassed: 0,
        ethicsExpiring: 0,
        deadlinesQ2: 0,
      },
      exchangeRateNote: "",
    },
    mapHighlights: [],
    lifecycle: { pendingActivation: [], riskRadar: [], reports: [] },
    compliance: {
      byFunder: [],
      audits: { upcoming: "None", packageHints: [], auditors: [] },
    },
    reporting: { institutional: [], finance: [], risks: [] },
    interventions: [],
    knowledge: { templates: [], piPerformance: [], funderIntel: [] },
    systemAdmin: { registrations: 0, pendingActions: [], ruleConfig: [] },
    capacity: { trainings: [], resources: [] },
  };
  let activeSection = "dashboard";

  const sectionMeta = {
    dashboard: {
      title: "Institutional pulse",
      description:
        "High-level overview of grants, funds, deadlines, and alerts.",
      badge: "Overview",
    },
    "pending-activations": {
      title: "Pending grant activations",
      description: "Verify award packages and green-light research work.",
      badge: "Activation queue",
    },
    "compliance-center": {
      title: "Compliance cockpit",
      description: "Funder expectations, safeguards, and adherence checks.",
      badge: "Compliance",
    },
    "risk-monitor": {
      title: "Risk monitor",
      description: "Track stress signals and coordinate interventions.",
      badge: "Risk",
    },
    "reports-deadlines": {
      title: "Reports & deadlines",
      description: "Calendar of funder submissions and reminder workflow.",
      badge: "Reporting",
    },
    "audit-center": {
      title: "Audit center",
      description: "Assemble audit packs and manage auditor access.",
      badge: "Audit readiness",
    },
    "field-map": {
      title: "Field deployment map",
      description: "Spatial intelligence across all fieldwork locations.",
      badge: "Field ops",
    },
    analytics: {
      title: "Analytics & KPIs",
      description:
        "Institutional output, finance utilization, and impact metrics.",
      badge: "Analytics",
    },
    "user-management": {
      title: "User & knowledge management",
      description: "Accounts, rules, templates, and training insights.",
      badge: "Administration",
    },
  };

  const navSubscription = rsuNavTarget.subscribe((target) => {
    if (target) {
      activeSection = target;
      clearRsuNavTarget();
    }
  });

  onDestroy(() => {
    navSubscription?.();
  });

  function setSection(sectionId) {
    activeSection = sectionId;
  }

  $: currentSectionMeta = sectionMeta[activeSection] ?? sectionMeta.dashboard;

  $: isRSU = $user?.role === "RSU";

  onMount(async () => {
    if (!isRSU) {
      loading = false;
      return;
    }

    // FETCH REAL DATA
    try {
      const res = await axios.get("http://localhost:5000/api/grants", {
        withCredentials: true,
      });
      const grants = res.data || [];

      const totalFunding = grants.reduce(
        (sum, g) => sum + (g.total_budget || 0),
        0,
      );
      const totalSpent = grants.reduce(
        (sum, g) =>
          sum + ((g.spent_percent || 0) / 100) * (g.total_budget || 0),
        0,
      );

      // Mutate rsuData sub-properties to keep the structure intact
      rsuData.summary.totalGrants = grants.length;
      rsuData.summary.onTrack = grants.filter(
        (g) => (g.spent_percent || 0) < 80,
      ).length;
      rsuData.summary.atRisk = grants.filter(
        (g) => (g.spent_percent || 0) >= 80 && (g.spent_percent || 0) < 95,
      ).length;
      rsuData.summary.critical = grants.filter(
        (g) => (g.spent_percent || 0) >= 95,
      ).length;

      rsuData.summary.totalFunding = totalFunding / 1000000;
      rsuData.summary.fundsUsed = totalSpent / 1000000;
      rsuData.summary.fundsAtRisk =
        ((totalFunding - totalSpent) * 0.1) / 1000000;

      // 3. Map Upcoming Reports (Deadlines)
      const grantsWithDeadlines = grants
        .filter((g) => g.next_deadline_date && g.status === "active")
        .sort(
          (a, b) =>
            new Date(a.next_deadline_date) - new Date(b.next_deadline_date),
        )
        .slice(0, 5);

      rsuData.lifecycle.reports = grantsWithDeadlines.map((g) => ({
        date: new Date(g.next_deadline_date).toLocaleDateString("en-GB", {
          day: "numeric",
          month: "short",
        }),
        label: g.next_deadline_label || "Milestone",
        grants: 1,
        status:
          new Date(g.next_deadline_date) <
          new Date(new Date().setDate(new Date().getDate() + 30))
            ? "Urgent"
            : "On Track",
      }));

      // 4. Map Risk Radar
      const highBurnGrants = grants.filter(
        (g) => (g.spent_percent || 0) > 80 && g.status === "active",
      );
      rsuData.lifecycle.riskRadar = [
        {
          issue: "Budget Burn > 80%",
          grants: highBurnGrants.length,
          action: "Review Spending",
        },
        {
          issue: "Upcoming Deadlines (30 days)",
          grants: grantsWithDeadlines.length,
          action: "Send Reminders",
        },
      ].filter((r) => r.grants > 0);

      // 5. Compliance Breakdown
      const grantsByFunder = grants
        .filter((g) => g.status === "active")
        .reduce((acc, g) => {
          acc[g.funder] = (acc[g.funder] || 0) + 1;
          return acc;
        }, {});

      rsuData.compliance.byFunder = Object.entries(grantsByFunder).map(
        ([funder, count]) => ({
          name: funder,
          grants: count,
          checks: [
            { label: "Reporting", value: "Active", level: "ok" },
            {
              label: "Budget",
              value: "Monitor",
              level: count > 1 ? "warn" : "ok",
            },
          ],
        }),
      );

      // 6. Map Pending Activations
      rsuData.lifecycle.pendingActivation = grants
        .filter((g) => g.status === "pending")
        .map((g) => ({
          id: g.id,
          grant: g.title,
          pi: `PI ID: ${g.pi_id}`, // Ideally we'd have the name here, but PI ID is what we have for now
          amount: `${g.currency} ${g.total_budget.toLocaleString()}`,
          due: g.start_date,
        }));
    } catch (err) {
      console.error("Failed to fetch grants", err);
      error = "Failed to load dashboard data.";
    } finally {
      loading = false;
    }
  });

  async function approveGrant(grantId) {
    if (!confirm("Are you sure you want to approve this grant?")) return;
    loading = true;
    try {
      await axios.put(
        `http://localhost:5000/api/grants/${grantId}/approve`,
        {},
        { withCredentials: true },
      );
      alert("Grant approved successfully!");
      window.location.reload(); // Simple reload to refresh data
    } catch (err) {
      console.error("Failed to approve grant", err);
      alert(
        "Failed to approve grant: " +
          (err.response?.data?.error || err.message),
      );
    } finally {
      loading = false;
    }
  }
</script>

{#if loading}
  <Layout>
    <div class="py-20 text-center text-gray-500">
      <div
        class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"
      ></div>
      <p>Loading RSU mission control…</p>
    </div>
  </Layout>
{:else if !isRSU}
  <Layout>
    <div
      class="max-w-4xl mx-auto mt-12 bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl p-10 text-center shadow-lg"
    >
      <h1 class="text-2xl font-bold text-gray-900 mb-2">Access restricted</h1>
      <p class="text-gray-600">
        The Research Support Unit module is only available to RSU officers.
      </p>
      <button
        class="mt-6 px-4 py-2 rounded-xl bg-blue-600 text-white"
        on:click={() =>
          router.goToRoleHome?.($user?.role) ?? router.goToLogin()}
      >
        Return to my workspace
      </button>
    </div>
  </Layout>
{:else}
  <Layout>
    <div class="max-w-7xl mx-auto space-y-8">
      <header
        class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl shadow-lg p-8 flex flex-col gap-4"
      >
        <div>
          <p
            class="text-xs uppercase tracking-[0.3em] text-blue-600 font-semibold"
          >
            RSU Mission Control
          </p>
          <h1 class="text-3xl md:text-4xl font-bold text-gray-900">
            {currentSectionMeta.title}
          </h1>
          <p class="text-gray-600 mt-2 text-sm">
            {currentSectionMeta.description}
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-3 text-xs text-gray-600">
          <span class="px-3 py-1 rounded-full bg-blue-50 text-blue-700"
            >{currentSectionMeta.badge}</span
          >
          <span class="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700"
            >Institution oversight</span
          >
          <span class="px-3 py-1 rounded-full bg-amber-50 text-amber-700"
            >Real-time alerts</span
          >
          {#if activeSection !== "dashboard"}
            <button
              class="ml-auto px-3 py-1 rounded-full border border-gray-200 text-gray-700"
              type="button"
              on:click={() => setSection("dashboard")}
            >
              ← Back to dashboard
            </button>
          {/if}
        </div>
      </header>

      {#if activeSection === "dashboard"}
        <section class="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div class="xl:col-span-2 space-y-4">
            <div
              class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
            >
              <div class="flex flex-wrap justify-between items-center gap-4">
                <div>
                  <p class="text-sm text-gray-600">Active Grants Summary</p>
                  <h2 class="text-2xl font-semibold text-gray-900">
                    {rsuData.summary.totalGrants} grants monitored
                  </h2>
                </div>
                <p class="text-xs text-gray-500">
                  {rsuData.summary.exchangeRateNote}
                </p>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
                <div
                  class="p-4 rounded-2xl border border-emerald-100 bg-emerald-50/70"
                >
                  <p class="text-sm text-gray-600">On track</p>
                  <div class="flex items-center gap-2 text-emerald-700">
                    <Icon
                      name="statusOn"
                      size={22}
                      className="text-emerald-600"
                      strokeWidth={0}
                    />
                    <p class="text-2xl font-bold">{rsuData.summary.onTrack}</p>
                  </div>
                  <p class="text-xs text-gray-500">71% of portfolio</p>
                </div>
                <div
                  class="p-4 rounded-2xl border border-amber-100 bg-amber-50/70"
                >
                  <p class="text-sm text-gray-600">At risk</p>
                  <div class="flex items-center gap-2 text-amber-700">
                    <Icon
                      name="statusWarn"
                      size={22}
                      className="text-amber-500"
                      strokeWidth={1.4}
                    />
                    <p class="text-2xl font-bold">{rsuData.summary.atRisk}</p>
                  </div>
                  <p class="text-xs text-gray-500">18% require attention</p>
                </div>
                <div
                  class="p-4 rounded-2xl border border-rose-100 bg-rose-50/70"
                >
                  <p class="text-sm text-gray-600">Critical</p>
                  <div class="flex items-center gap-2 text-rose-700">
                    <Icon
                      name="statusCritical"
                      size={22}
                      className="text-rose-600"
                      strokeWidth={1.6}
                    />
                    <p class="text-2xl font-bold">{rsuData.summary.critical}</p>
                  </div>
                  <p class="text-xs text-gray-500">11% escalated</p>
                </div>
              </div>
              <div
                class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6"
              >
                <div class="p-4 rounded-2xl bg-gray-50 border border-gray-100">
                  <p class="text-xs text-gray-500">Total funding</p>
                  <p class="text-xl font-semibold text-gray-900">
                    ${rsuData.summary.totalFunding.toFixed(1)}M
                  </p>
                </div>
                <div class="p-4 rounded-2xl bg-gray-50 border border-gray-100">
                  <p class="text-xs text-gray-500">Funds used</p>
                  <p class="text-xl font-semibold text-gray-900">
                    ${rsuData.summary.fundsUsed.toFixed(1)}M (50%)
                  </p>
                </div>
                <div class="p-4 rounded-2xl bg-gray-50 border border-gray-100">
                  <p class="text-xs text-gray-500">Funds at risk</p>
                  <p class="text-xl font-semibold text-gray-900">
                    ${Math.round(rsuData.summary.fundsAtRisk * 1000) / 1000}M
                  </p>
                </div>
                <div class="p-4 rounded-2xl bg-gray-50 border border-gray-100">
                  <p class="text-xs text-gray-500">Reports due (30 days)</p>
                  <p class="text-xl font-semibold text-gray-900">
                    {rsuData.summary.upcomingReports}
                  </p>
                </div>
              </div>
            </div>

            <div class="grid gap-4 lg:grid-cols-2">
              <div
                class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
              >
                <div class="flex items-center justify-between mb-4">
                  <h3 class="text-lg font-semibold text-gray-900">
                    Field intelligence snapshot
                  </h3>
                  <button
                    class="text-xs font-semibold text-blue-600"
                    type="button"
                    on:click={() => setSection("field-map")}
                  >
                    Open field map →
                  </button>
                </div>
                <div class="space-y-3 text-sm text-gray-700">
                  {#each rsuData.mapHighlights.slice(0, 3) as highlight}
                    <div
                      class="p-3 rounded-2xl border border-gray-100 bg-white/80"
                    >
                      <p class="text-xs uppercase tracking-wide text-gray-500">
                        {highlight.region}
                      </p>
                      <p class="font-semibold text-gray-900">
                        {highlight.details}
                      </p>
                      <p class="text-xs text-gray-500">
                        Status: {highlight.status}
                      </p>
                    </div>
                  {/each}
                </div>
              </div>

              <div
                class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
              >
                <div class="flex items-center justify-between mb-4">
                  <h3 class="text-lg font-semibold text-gray-900">
                    Upcoming obligations
                  </h3>
                  <button
                    class="text-xs font-semibold text-blue-600"
                    type="button"
                    on:click={() => setSection("reports-deadlines")}
                  >
                    View full calendar
                  </button>
                </div>
                <ul class="space-y-3 text-sm text-gray-700">
                  {#each rsuData.lifecycle.reports.slice(0, 3) as report}
                    <li class="flex items-center justify-between gap-3">
                      <div>
                        <p class="font-semibold text-gray-900">
                          {report.label}
                        </p>
                        <p class="text-xs text-gray-500">
                          {report.grants} grants
                        </p>
                      </div>
                      <div class="text-right">
                        <p class="text-sm font-semibold text-gray-900">
                          {report.date}
                        </p>
                        <p
                          class={`text-xs ${report.status === "Urgent" ? "text-rose-600" : report.status === "Needs PI Draft" ? "text-amber-600" : "text-emerald-600"}`}
                        >
                          {report.status}
                        </p>
                      </div>
                    </li>
                  {/each}
                </ul>
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <div
              class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
            >
              <h3 class="text-lg font-semibold text-gray-900 mb-3">
                Alert console
              </h3>
              <ul class="space-y-3 text-sm text-gray-700">
                <li class="flex items-center justify-between">
                  <div>
                    <p class="font-semibold text-gray-900">
                      Audits in pipeline
                    </p>
                    <p class="text-xs text-gray-500">
                      Pending vs passed this quarter
                    </p>
                  </div>
                  <span
                    class="px-3 py-1 rounded-full text-xs bg-blue-50 text-blue-700"
                  >
                    {rsuData.summary.compliance.auditsPending} / {rsuData
                      .summary.compliance.auditsPassed}
                  </span>
                </li>
                <li class="flex items-center justify-between">
                  <div>
                    <p class="font-semibold text-gray-900">Ethics expiring</p>
                    <p class="text-xs text-gray-500">Next 30 days</p>
                  </div>
                  <span
                    class="px-3 py-1 rounded-full text-xs bg-amber-50 text-amber-700"
                    >{rsuData.summary.compliance.ethicsExpiring}</span
                  >
                </li>
                <li class="flex items-center justify-between">
                  <div>
                    <p class="font-semibold text-gray-900">Q2 deadlines</p>
                    <p class="text-xs text-gray-500">Funder deliverables</p>
                  </div>
                  <span
                    class="px-3 py-1 rounded-full text-xs bg-emerald-50 text-emerald-700"
                    >{rsuData.summary.compliance.deadlinesQ2}</span
                  >
                </li>
              </ul>
            </div>

            <div
              class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
            >
              <h3 class="text-lg font-semibold text-gray-900 mb-3">
                Rapid actions
              </h3>
              <div class="space-y-2 text-sm text-gray-700">
                <button
                  class="w-full px-4 py-2 rounded-xl border border-gray-200 text-left font-semibold flex items-center gap-2"
                  type="button"
                  on:click={() => setSection("pending-activations")}
                >
                  <Icon name="search" size={18} />
                  <span>Review activation queue</span>
                </button>
                <button
                  class="w-full px-4 py-2 rounded-xl border border-gray-200 text-left font-semibold flex items-center gap-2"
                  type="button"
                  on:click={() => setSection("risk-monitor")}
                >
                  <Icon name="warning" size={18} className="text-amber-500" />
                  <span>Open risk monitor</span>
                </button>
                <button
                  class="w-full px-4 py-2 rounded-xl border border-gray-200 text-left font-semibold flex items-center gap-2"
                  type="button"
                  on:click={() => setSection("audit-center")}
                >
                  <Icon name="audit" size={18} />
                  <span>Prepare audit package</span>
                </button>
              </div>
            </div>
          </div>
        </section>
      {:else if activeSection === "field-map"}
        <section class="space-y-6">
          <div
            class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
          >
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-2xl font-semibold text-gray-900">
                  Field deployment intelligence
                </h2>
                <p class="text-sm text-gray-500">
                  Track which districts are active, delayed, or stalled.
                </p>
              </div>
              <button class="text-sm font-semibold text-blue-600" type="button"
                >Launch geospatial view</button
              >
            </div>
            <div class="grid md:grid-cols-3 gap-4 mt-6">
              {#each rsuData.mapHighlights as highlight}
                <div
                  class={`p-4 rounded-2xl border ${highlight.status === "Critical" ? "border-rose-200 bg-rose-50/70" : highlight.status === "Delayed" ? "border-amber-200 bg-amber-50/70" : "border-emerald-200 bg-emerald-50/70"}`}
                >
                  <p class="text-xs uppercase tracking-wide text-gray-500">
                    {highlight.region}
                  </p>
                  <p class="text-sm font-semibold text-gray-900">
                    {highlight.details}
                  </p>
                  <p class="text-xs text-gray-600">
                    Status: {highlight.status}
                  </p>
                </div>
              {/each}
            </div>
          </div>
        </section>
      {:else if activeSection === "pending-activations"}
        <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div
            class="lg:col-span-2 bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
          >
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-2xl font-semibold text-gray-900">
                Activation queue
              </h2>
              <button
                class="px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-semibold"
                >Bulk approve</button
              >
            </div>
            <ul class="space-y-3 text-sm text-gray-700">
              {#each rsuData.lifecycle.pendingActivation as activation}
                <li
                  class="flex items-center justify-between gap-3 p-4 rounded-2xl border border-gray-100 bg-white/80 shadow-sm"
                >
                  <div class="flex-1">
                    <p class="font-semibold text-gray-900">
                      {activation.grant}
                    </p>
                    <div class="flex items-center gap-3 mt-1">
                      <p class="text-xs text-gray-500">PI: {activation.pi}</p>
                      <p class="text-xs font-semibold text-blue-600">
                        {activation.amount}
                      </p>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <div class="text-right mr-4 hidden sm:block">
                      <p
                        class="text-[10px] text-gray-400 uppercase tracking-wider"
                      >
                        Start Date
                      </p>
                      <p class="text-xs font-medium text-gray-700">
                        {activation.due || "N/A"}
                      </p>
                    </div>
                    <button
                      class="px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-bold hover:bg-emerald-700 transition-colors shadow-sm active:scale-95 disabled:opacity-50"
                      on:click={() => approveGrant(activation.id)}
                      disabled={loading}
                    >
                      Approve
                    </button>
                  </div>
                </li>
              {/each}
              {#if rsuData.lifecycle.pendingActivation.length === 0}
                <li
                  class="py-12 text-center text-gray-500 bg-gray-50 rounded-2xl border border-dashed border-gray-200"
                >
                  <p>No grants pending activation.</p>
                </li>
              {/if}
            </ul>
          </div>
          <div class="space-y-4">
            <div
              class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
            >
              <h3 class="text-lg font-semibold text-gray-900 mb-3">
                Pre-activation checklist
              </h3>
              <ul class="space-y-2 text-sm text-gray-700">
                <li>• Verify award letter and uploaded docs</li>
                <li>• Confirm budget alignment with funder rules</li>
                <li>• Ensure ethics approvals are valid</li>
                <li>• Validate team credentials</li>
                <li>• Approve to unlock project workstreams</li>
              </ul>
            </div>
            <div
              class="bg-blue-50/70 border border-blue-100 rounded-2xl p-4 text-sm text-blue-900"
            >
              <p class="font-semibold mb-1">Automation tip</p>
              <p>
                Configure rule templates so new grant submissions auto-run
                validation before landing here.
              </p>
            </div>
          </div>
        </section>
      {:else if activeSection === "risk-monitor"}
        <section class="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div class="xl:col-span-2 space-y-4">
            <div
              class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
            >
              <h2 class="text-2xl font-semibold text-gray-900 mb-3">
                Risk radar
              </h2>
              <ul class="space-y-3 text-sm text-gray-700">
                {#each rsuData.lifecycle.riskRadar as risk}
                  <li class="flex items-center justify-between gap-3">
                    <div>
                      <p class="font-semibold text-gray-900">{risk.issue}</p>
                      <p class="text-xs text-gray-500">Action: {risk.action}</p>
                    </div>
                    <span
                      class="px-3 py-1 text-xs font-semibold rounded-full bg-rose-50 text-rose-600"
                      >{risk.grants} grants</span
                    >
                  </li>
                {/each}
              </ul>
            </div>
            <div
              class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
            >
              <h2 class="text-2xl font-semibold text-gray-900 mb-3">
                Intervention log
              </h2>
              <div class="space-y-4">
                {#each rsuData.interventions as intervention}
                  <div
                    class="p-4 rounded-2xl border border-gray-100 bg-white/80"
                  >
                    <p class="text-sm font-semibold text-gray-900">
                      {intervention.grant}
                    </p>
                    <p class="text-xs text-gray-500 mb-2">
                      {intervention.flag}
                    </p>
                    <ul class="text-xs text-gray-600 space-y-1">
                      {#each intervention.steps as step}
                        <li>• {step}</li>
                      {/each}
                    </ul>
                    <button class="mt-3 text-xs font-semibold text-blue-600"
                      >Log action</button
                    >
                  </div>
                {/each}
              </div>
            </div>
          </div>
          <div
            class="bg-rose-50/70 border border-rose-100 rounded-2xl p-6 shadow-md"
          >
            <h3 class="text-lg font-semibold text-rose-700 mb-3">
              Escalation playbook
            </h3>
            <ol
              class="text-sm text-rose-900 space-y-2 list-decimal list-inside"
            >
              <li>Investigate system timeline & financials.</li>
              <li>Reach out to PI and capture response in system.</li>
              <li>Decide on freeze / exception / escalation.</li>
              <li>Record outcome for institutional risk register.</li>
            </ol>
          </div>
        </section>
      {:else if activeSection === "reports-deadlines"}
        <section class="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div
            class="xl:col-span-2 bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
          >
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-2xl font-semibold text-gray-900">
                Upcoming reports calendar
              </h2>
              <button
                class="px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-semibold"
                >Send reminders</button
              >
            </div>
            <ul class="space-y-3 text-sm text-gray-700">
              {#each rsuData.lifecycle.reports as report}
                <li
                  class="flex items-center justify-between gap-3 p-3 rounded-2xl border border-gray-100"
                >
                  <div>
                    <p class="font-semibold text-gray-900">{report.label}</p>
                    <p class="text-xs text-gray-500">{report.grants} grants</p>
                  </div>
                  <div class="text-right">
                    <p class="text-sm font-semibold text-gray-900">
                      {report.date}
                    </p>
                    <p
                      class={`text-xs ${report.status === "Urgent" ? "text-rose-600" : report.status === "Needs PI Draft" ? "text-amber-600" : "text-emerald-600"}`}
                    >
                      {report.status}
                    </p>
                  </div>
                </li>
              {/each}
            </ul>
          </div>
          <div class="space-y-4">
            <div
              class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
            >
              <h3 class="text-lg font-semibold text-gray-900 mb-3">
                Cycle management
              </h3>
              <ul class="space-y-2 text-sm text-gray-700">
                <li>• Remind PIs 7 days before deadlines.</li>
                <li>• Review drafts and return comments.</li>
                <li>• Submit final package to funder.</li>
                <li>• Archive signed copies in PAGMS.</li>
              </ul>
            </div>
            <div
              class="bg-amber-50/70 border border-amber-100 rounded-2xl p-4 text-sm text-amber-900"
            >
              <p class="font-semibold mb-1">Deadlines risk register</p>
              <ul class="space-y-1">
                {#each rsuData.reporting.risks as risk}
                  <li>• {risk}</li>
                {/each}
              </ul>
            </div>
          </div>
        </section>
      {:else if activeSection === "compliance-center"}
        <section class="space-y-6">
          <div
            class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
          >
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-2xl font-semibold text-gray-900">
                Compliance status by funder
              </h2>
              <button class="text-sm text-blue-600 font-semibold" type="button"
                >Manage rulebook</button
              >
            </div>
            <div class="space-y-4">
              {#each rsuData.compliance.byFunder as funder}
                <div class="p-4 rounded-2xl border border-gray-100 bg-white/80">
                  <div class="flex items-center justify-between mb-2">
                    <div>
                      <p class="text-sm text-gray-500">
                        {funder.grants} grants
                      </p>
                      <p class="text-lg font-semibold text-gray-900">
                        {funder.name}
                      </p>
                    </div>
                    <button
                      class="text-xs font-semibold text-blue-600"
                      type="button">View dossier</button
                    >
                  </div>
                  <div class="grid sm:grid-cols-3 gap-3 text-xs text-gray-600">
                    {#each funder.checks as check}
                      <div
                        class={`p-3 rounded-xl border ${check.level === "alert" ? "border-rose-200 bg-rose-50/70 text-rose-700" : check.level === "warn" ? "border-amber-200 bg-amber-50/70 text-amber-700" : "border-emerald-200 bg-emerald-50/70 text-emerald-700"}`}
                      >
                        <p class="font-semibold">{check.label}</p>
                        <p>{check.value}</p>
                      </div>
                    {/each}
                  </div>
                </div>
              {/each}
            </div>
          </div>
        </section>
      {:else if activeSection === "audit-center"}
        <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div
            class="lg:col-span-2 bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
          >
            <div class="flex items-center justify-between mb-4">
              <div>
                <h2 class="text-2xl font-semibold text-gray-900">
                  Audit preparation
                </h2>
                <p class="text-sm text-gray-500">
                  Generate auditor-ready evidence packages instantly.
                </p>
              </div>
              <button
                class="px-4 py-2 rounded-xl bg-emerald-600 text-white text-sm font-semibold"
                >Generate audit package</button
              >
            </div>
            <div class="grid md:grid-cols-2 gap-4">
              <div class="p-4 rounded-2xl bg-gray-50 border border-gray-100">
                <p class="text-xs text-gray-500">Upcoming audit</p>
                <p class="text-lg font-semibold text-gray-900">
                  {rsuData.compliance.audits.upcoming}
                </p>
              </div>
              <div class="p-4 rounded-2xl bg-blue-50/70 border border-blue-100">
                <p class="text-xs text-blue-700 uppercase tracking-wide">
                  Package contents
                </p>
                <ul class="mt-2 text-xs text-blue-900 space-y-1">
                  {#each rsuData.compliance.audits.packageHints as item}
                    <li>• {item}</li>
                  {/each}
                </ul>
              </div>
            </div>
          </div>
          <div
            class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
          >
            <h3 class="text-lg font-semibold text-gray-900 mb-3">
              Auditor access
            </h3>
            <div class="space-y-2 text-sm text-gray-700">
              {#each rsuData.compliance.audits.auditors as auditor}
                <div class="flex items-center justify-between">
                  <p class="font-semibold text-gray-900">{auditor.name}</p>
                  <button class="text-xs font-semibold text-blue-600"
                    >{auditor.status}</button
                  >
                </div>
              {/each}
            </div>
          </div>
        </section>
      {:else if activeSection === "analytics"}
        <section class="space-y-6">
          <div
            class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
          >
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-2xl font-semibold text-gray-900">
                Institutional reporting
              </h2>
              <button class="text-sm text-blue-600 font-semibold" type="button"
                >Generate monthly report</button
              >
            </div>
            <div class="grid md:grid-cols-2 gap-6">
              <div class="space-y-3">
                <h3
                  class="text-sm font-semibold text-gray-700 uppercase tracking-wide"
                >
                  Research output
                </h3>
                <div class="grid grid-cols-2 gap-4">
                  {#each rsuData.reporting.institutional as metric}
                    <div
                      class="p-4 rounded-2xl bg-gray-50 border border-gray-100"
                    >
                      <p class="text-xs text-gray-500">{metric.label}</p>
                      <p class="text-xl font-semibold text-gray-900">
                        {metric.value}
                      </p>
                      <p class="text-xs text-gray-500">{metric.footnote}</p>
                    </div>
                  {/each}
                </div>
              </div>
              <div class="space-y-3">
                <h3
                  class="text-sm font-semibold text-gray-700 uppercase tracking-wide"
                >
                  Financial utilization
                </h3>
                <div class="space-y-3">
                  {#each rsuData.reporting.finance as finance}
                    <div
                      class="p-4 rounded-2xl bg-blue-50/70 border border-blue-100"
                    >
                      <p class="text-xs text-blue-700">{finance.label}</p>
                      <p class="text-xl font-semibold text-gray-900">
                        {finance.value}
                      </p>
                      <p class="text-xs text-blue-900">{finance.detail}</p>
                    </div>
                  {/each}
                </div>
                <div
                  class="p-4 rounded-2xl bg-amber-50/70 border border-amber-100"
                >
                  <p
                    class="text-xs uppercase tracking-wide text-amber-700 font-semibold"
                  >
                    Risk register
                  </p>
                  <ul class="mt-2 space-y-1 text-sm text-amber-900">
                    {#each rsuData.reporting.risks as risk}
                      <li>• {risk}</li>
                    {/each}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>
      {:else if activeSection === "user-management"}
        <section class="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div class="space-y-4">
            <div
              class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
            >
              <h3 class="text-lg font-semibold text-gray-900 mb-3">
                Knowledge hub
              </h3>
              <div class="space-y-3 text-sm text-gray-700">
                <div>
                  <p class="text-xs uppercase tracking-wide text-gray-500 mb-1">
                    Templates
                  </p>
                  <ul class="space-y-1">
                    {#each rsuData.knowledge.templates as template}
                      <li class="flex items-center gap-2">
                        <Icon
                          name="document"
                          size={16}
                          className="text-blue-600"
                        />
                        <span>{template}</span>
                      </li>
                    {/each}
                  </ul>
                </div>
                <div>
                  <p class="text-xs uppercase tracking-wide text-gray-500 mb-1">
                    PI performance
                  </p>
                  <ul class="space-y-1">
                    {#each rsuData.knowledge.piPerformance as note}
                      <li>• {note}</li>
                    {/each}
                  </ul>
                </div>
                <div>
                  <p class="text-xs uppercase tracking-wide text-gray-500 mb-1">
                    Funder intelligence
                  </p>
                  <ul class="space-y-1">
                    {#each rsuData.knowledge.funderIntel as intel}
                      <li>• {intel}</li>
                    {/each}
                  </ul>
                </div>
              </div>
            </div>

            <div
              class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
            >
              <h3 class="text-lg font-semibold text-gray-900 mb-3">
                Capacity building
              </h3>
              <div class="space-y-3 text-sm text-gray-700">
                <div class="p-4 rounded-2xl bg-gray-50 border border-gray-100">
                  <p class="text-xs uppercase tracking-wide text-gray-500 mb-2">
                    Training sessions
                  </p>
                  <ul class="space-y-1">
                    {#each rsuData.capacity.trainings as training}
                      <li class="flex items-center justify-between text-xs">
                        <span class="font-semibold text-gray-900"
                          >{training.title}</span
                        >
                        <span class="text-gray-500"
                          >{training.date} ({training.status})</span
                        >
                      </li>
                    {/each}
                  </ul>
                </div>
                <div
                  class="p-4 rounded-2xl bg-blue-50/70 border border-blue-100"
                >
                  <p class="text-xs uppercase tracking-wide text-blue-700 mb-2">
                    Resource center
                  </p>
                  <ul class="space-y-1 text-xs text-blue-900">
                    {#each rsuData.capacity.resources as resource}
                      <li>• {resource}</li>
                    {/each}
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div class="xl:col-span-2 space-y-4">
            <div
              class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6"
            >
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-900">
                  System administration
                </h3>
                <button
                  class="text-sm text-blue-600 font-semibold"
                  type="button">Open admin console</button
                >
              </div>
              <div class="grid md:grid-cols-3 gap-4">
                <div class="p-4 rounded-2xl bg-gray-50 border border-gray-100">
                  <p class="text-xs text-gray-500">Pending registrations</p>
                  <p class="text-2xl font-semibold text-gray-900">
                    {rsuData.systemAdmin.registrations}
                  </p>
                </div>
                <div
                  class="md:col-span-2 p-4 rounded-2xl bg-amber-50/70 border border-amber-100"
                >
                  <p
                    class="text-xs uppercase tracking-wide text-amber-700 mb-2"
                  >
                    Immediate actions
                  </p>
                  <ul class="space-y-1 text-sm text-amber-900">
                    {#each rsuData.systemAdmin.pendingActions as action}
                      <li>• {action}</li>
                    {/each}
                  </ul>
                </div>
              </div>
              <div
                class="mt-4 p-4 rounded-2xl bg-blue-50/70 border border-blue-100"
              >
                <p class="text-xs uppercase tracking-wide text-blue-700 mb-2">
                  Rule configuration
                </p>
                <ul class="space-y-1 text-sm text-blue-900">
                  {#each rsuData.systemAdmin.ruleConfig as rule}
                    <li>• {rule}</li>
                  {/each}
                </ul>
              </div>
            </div>
          </div>
        </section>
      {:else}
        <section
          class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow p-10 text-center text-sm text-gray-600"
        >
          This section is not yet implemented.
        </section>
      {/if}
    </div>
  </Layout>
{/if}
