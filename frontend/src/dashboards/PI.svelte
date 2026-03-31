<script>
  import { onMount } from "svelte";
  import axios from "axios";
  import { router } from "../stores/router.js";
  import { user } from "../stores/auth.js";
  import Chart from "../components/Chart.svelte";
  import { notifications, addNotification, clearAll } from "../stores/notifications.js";
  import { activeCloseoutGrantId } from "../stores/closeout.js";

  // Enable credentials for Flask sessions
  axios.defaults.withCredentials = true;

  let loading = $state(true);
  let rawResponse = $state(null);
  let showDebug = $state(false);
  let myGrants = $state([]);
  let deliverablesQueue = $state([]);
  let expenses = $state([]);
  let allTasks = $state([]); 
  let effort = $state([]); 
  let actionItems = $state({
    my_custody_assets: [],
    overdue_team_assets: [],
    ready_tranches: [],
    pending_deliverables_count: 0
  });

  // Pagination for Dashboard sections
  let taskPage = $state(1);
  const dashboardPageSize = 5;

  // Overview stats derived from data
  let activeGrantsCount = $derived(myGrants.filter((g) => g.status === "active").length);
  let upcomingDeadlinesCount = $derived(myGrants.filter(
    (g) => g.next_deadline_date,
  ).length);
  
  // Calculate spending status from first grant (or aggregate across grants)
  let spendingStatus = $derived(myGrants.length > 0 ? (myGrants[0].spending_status || myGrants[0].spending_lock) : { status: 'unlocked', color: 'green', text: 'All good', is_locked: false });
  
  // Calculate overall asset integrity across all grants
  let totalPendingAssets = $derived(myGrants.reduce((sum, grant) => sum + (grant.asset_integrity?.pending_returns || 0), 0));
  let assetIntegrityStatus = $derived(totalPendingAssets === 0 ? 'healthy' : 'warning');
  function normTaskStatus(s) {
    return (s || "").toLowerCase().replace(/-/g, "_");
  }

  // Task summary stats (case-insensitive; matches backend + legacy rows)
  let sortedAllTasks = $derived([...allTasks].sort((a, b) => {
    const dateA = new Date(a.created_at || a.id);
    const dateB = new Date(b.created_at || b.id);
    return dateB - dateA;
  }));

  let outstandingTasksCount = $derived(sortedAllTasks.filter((t) =>
    ["assigned", "in_progress", "revision_requested", "pending"].includes(
      normTaskStatus(t.status),
    ),
  ).length);

  let overdueTasksCount = $derived(sortedAllTasks.filter(
    (t) => normTaskStatus(t.status) === "overdue",
  ).length);

  // Deadlines within next 14 days
  let upcoming14Days = $derived(sortedAllTasks.filter(t => {
    if (!t.deadline || normTaskStatus(t.status) === 'completed') return false;
    const due = new Date(t.deadline);
    const now = new Date();
    const diff = (due - now) / (1000 * 60 * 60 * 24);
    return diff >= 0 && diff <= 14;
  }));

  // Aggregate stats across all grants

  // Aggregate stats across all grants
  let totalRuleViolations = $derived(myGrants.reduce((sum, g) => sum + (g.compliance_summary?.violations_count || 0), 0));
  let globalSpendingLock = $derived(myGrants.some(g => g.spending_lock?.is_locked) ? 'locked' : myGrants.some(g => g.spending_lock?.severity === 'warning') ? 'warning' : 'unlocked');

  // Closeout Grants Detection
  let closingGrants = $derived(myGrants.filter(g => {
    if (g.status === 'closing' || g.status === 'closed') return true;
    if (g.end_date) {
      const end = new Date(g.end_date);
      const now = new Date();
      const daysLeft = (end - now) / (1000 * 60 * 60 * 24);
      return daysLeft <= 30 && daysLeft >= -365; // Within 30 days of ending or recently ended
    }
    return false;
  }));

  function startCloseout(grantId) {
    activeCloseoutGrantId.set(grantId);
    router.goToCloseoutWizard();
  }

  /** Tasks assigned to the logged-in PI that still need work submitted */
  let myOwnTasks = $derived(sortedAllTasks.filter((t) => {
    const uid = $user?.id != null ? Number($user.id) : NaN;
    if (!Number.isFinite(uid) || Number(t.assigned_to) !== uid) return false;
    const s = normTaskStatus(t.status);
    return (
      s === "assigned" ||
      s === "in_progress" ||
      s === "overdue" ||
      s === "revision_requested" ||
      s === "pending"
    );
  }));

  async function fetchDashboardData() {
    loading = true;
    try {
      console.log("Fetching PI dashboard data...");
      const grantsRes = await axios.get("http://localhost:5000/api/grants").catch(e => { console.error("Grants API failed:", e); return { data: { grants: [] } }; });
      const deliverablesRes = await axios.get("http://localhost:5000/api/deliverables?status=pending").catch(e => { console.error("Deliverables API failed:", e); return { data: { submissions: [] } }; });
      const expensesRes = await axios.get("http://localhost:5000/api/expenses").catch(e => { console.error("Expenses API failed:", e); return { data: { expenses: [] } }; });
      const tasksRes = await axios.get("http://localhost:5000/api/tasks").catch(e => { console.error("Tasks API failed:", e); return { data: { tasks: [] } }; });
      const actionItemsRes = await axios.get("http://localhost:5000/api/pi-dashboard/action-items").catch(e => { console.error("Action Items API failed:", e); return { data: {} }; });

      console.log("Dashboard data raw response:", { grantsRes, tasksRes, deliverablesRes, expensesRes, actionItemsRes });

      rawResponse = JSON.stringify({
        grants: grantsRes.data,
        deliverables: deliverablesRes.data,
        expenses: expensesRes.data,
        tasks: tasksRes.data,
        actionItems: actionItemsRes.data
      }, null, 2);

      const rawGrants = grantsRes.data;
      myGrants = Array.isArray(rawGrants)
        ? rawGrants
        : rawGrants?.grants ?? [];

      deliverablesQueue = (deliverablesRes.data.submissions || []).map((e) => ({
        ...e,
        assignee_name: e.team_member, // Map for backward compatibility in UI
      }));
      expenses = expensesRes.data.expenses || [];
      allTasks = tasksRes.data.tasks || []; // Store fetched tasks
      actionItems = actionItemsRes.data || { my_custody_assets: [], overdue_team_assets: [], ready_tranches: [], pending_deliverables_count: 0 };

      // DEBUG: Log the data structure
      console.log('PI Dashboard - myGrants:', myGrants);
      if (myGrants.length > 0) {
        console.log('First grant data:', myGrants[0]);
        console.log('Has burn_rate:', 'burn_rate' in myGrants[0]);
        console.log('Has asset_integrity:', 'asset_integrity' in myGrants[0]);
        console.log('Has kpi_summary:', 'kpi_summary' in myGrants[0]);
        console.log('Has spending_status:', 'spending_status' in myGrants[0]);
      }
      deliverablesQueue = (deliverablesRes.data.submissions || []).map((e) => ({
        ...e,
        assignee_name: e.team_member, // Map for backward compatibility in UI
      }));
      expenses = expensesRes.data.expenses || [];
      allTasks = tasksRes.data.tasks || []; // Store fetched tasks

      // For now, certifiable effort is same as pending deliverables
      effort = deliverablesQueue.map((e) => ({
        name: e.assignee_name,
        hours: e.hours_worked,
        period: new Date(e.submitted_at).toLocaleDateString(undefined, {
          month: "short",
          year: "numeric",
        }),
        status: "Pending PI approval",
      }));

      // Simple notifications based on alerts
      myGrants.forEach((g) => {
        if (g.spent_percent > 85) {
          addNotification('budget', `Grant ${g.grant_code}: budget above 85% (${g.spent_percent}%)`, g.grant_code);
        }
      });
      if (deliverablesQueue.length > 0) {
        addNotification('milestone', `You have ${deliverablesQueue.length} new deliverables submissions to review`, '');
      }
      // Add notification for overdue tasks
      if (overdueTasksCount > 0) {
        addNotification('task', `You have ${overdueTasksCount} overdue tasks!`, '');
      }
    } catch (err) {
      console.error("Failed to fetch PI dashboard data:", err);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchDashboardData();
  });

  function statusBadge(status) {
    const s = status?.toLowerCase();
    if (s === "active" || s === "approved" || s === "completed") return "bg-green-100 text-green-800";
    if (s === "closed" || s === "archived") return "bg-gray-100 text-gray-700";
    if (s === "low balance" || s === "pending" || s === "awaiting_approval" || s === "revision_requested")
      return "bg-amber-100 text-amber-800";
    if (s === "rejected" || s === "overdue" || s === "at risk") return "bg-red-100 text-red-800";
    return "bg-blue-100 text-blue-800";
  }

  function getDaysRemaining(dateStr) {
    if (!dateStr) return null;
    const end = new Date(dateStr);
    const now = new Date();
    const diff = Math.ceil((end - now) / (1000 * 60 * 60 * 24));
    return diff;
  }

  function formatDate(dateStr) {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString();
  }

  let piName = $derived($user?.name?.replace(/^Dr\.?\s*/i, "") || "PI");
  let welcomeCopy = $derived(`Welcome back, Dr. ${piName}!`);

  let burnRateChartOptions = $derived({
    series: [
      { name: 'Time Elapsed %', data: myGrants.slice(0, 3).map(g => g.burn_rate?.time_elapsed_pct || 0) },
      { name: 'Budget Spent %', data: myGrants.slice(0, 3).map(g => g.spent_percent || 0) }
    ],
    chart: { type: 'bar', height: 250, toolbar: { show: false }, fontFamily: 'inherit' },
    plotOptions: { bar: { horizontal: true, dataLabels: { position: 'top' }, borderRadius: 4 } },
    dataLabels: { enabled: true, formatter: (val) => val + '%', offsetX: 20, style: { colors: ['#374151'] } },
    stroke: { show: true, width: 2, colors: ['#fff'] },
    xaxis: { categories: myGrants.slice(0, 3).map(g => g.grant_code), max: 100 },
    colors: [
      '#e5e7eb',
      function({ value, seriesIndex, dataPointIndex, w }) {
        if (seriesIndex === 1) {
          const status = myGrants[dataPointIndex]?.burn_rate?.status;
          if (status === 'high') return '#ef4444';
          if (status === 'low') return '#f59e0b';
          return '#10b981';
        }
        return '#e5e7eb';
      }
    ]
  });

  let complianceDonutOptions = $derived({
    series: [
      myGrants.length, 
      (actionItems?.ready_tranches?.length || 0) + deliverablesQueue.length, 
      (actionItems?.overdue_team_assets?.length || 0) + totalRuleViolations
    ],
    chart: { type: 'donut', height: 280, fontFamily: 'inherit' },
    labels: ['Healthy Modules', 'Warnings (Actionable)', 'Hard Blocks (Overdue/Violations)'],
    colors: ['#10b981', '#f59e0b', '#ef4444'],
    plotOptions: {
      pie: {
        donut: {
          labels: {
            show: true,
            name: { show: true },
            value: { show: true },
            total: {
              show: true,
              label: 'Critical Actions',
              color: '#ef4444',
              formatter: () => (actionItems?.overdue_team_assets?.length || 0) + totalRuleViolations
            }
          }
        }
      }
    },
    dataLabels: { enabled: false },
    legend: { position: 'bottom' }
  });

  let kpiStackedOptions = $derived({
    series: [
      { name: 'Achieved', data: myGrants.slice(0,4).flatMap(g => g.kpi_summary || []).slice(0,4).map(k => k.actual_value) },
      { name: 'Remaining to Target', data: myGrants.slice(0,4).flatMap(g => g.kpi_summary || []).slice(0,4).map(k => Math.max(0, k.target_value - k.actual_value)) }
    ],
    chart: { type: 'bar', height: 350, stacked: true, toolbar: { show: false }, fontFamily: 'inherit' },
    plotOptions: { bar: { horizontal: false, borderRadius: 4 } },
    xaxis: { categories: myGrants.slice(0,4).flatMap(g => g.kpi_summary || []).slice(0,4).map(k => k.name.length > 12 ? k.name.substring(0, 12) + '...' : k.name) },
    colors: ['#3b82f6', '#e5e7eb'],
    dataLabels: { enabled: false },
    legend: { position: 'top' }
  });

  let timelineOptions = $derived({
    series: [
      {
        data: upcoming14Days.slice(0, 5).map(t => ({
          x: t.title.length > 20 ? t.title.substring(0, 20) + '...' : t.title,
          y: [
            new Date().getTime(),
            new Date(t.deadline).getTime()
          ],
          fillColor: (t.status === 'completed') ? '#0C85B7' : (t.status === 'overdue' ? '#ef4444' : '#095E8F')
        }))
      }
    ],
    chart: { type: 'rangeBar', height: 250, toolbar: { show: false }, fontFamily: 'inherit' },
    plotOptions: { bar: { horizontal: true, borderRadius: 4 } },
    xaxis: { type: 'datetime' },
    tooltip: {
      custom: function({ seriesIndex, dataPointIndex, w }) {
        const title = upcoming14Days[dataPointIndex]?.title;
        const deadline = new Date(w.globals.seriesRangeEnd[seriesIndex][dataPointIndex]).toLocaleDateString();
        return '<div class="p-2 text-xs font-sans"><b>' + title + '</b><br/>Deadline: ' + deadline + '</div>';
      }
    }
  });
</script>

<div class="space-y-6">
  <section
    class="bg-white/60 backdrop-blur-xl border border-white/60 rounded-3xl p-8 shadow-lg mb-8"
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
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-white/70 backdrop-blur-xl border border-white/60 p-4 rounded-2xl shadow-md">
    <div>
      <h2 class="text-xl font-bold text-gray-800">Portfolio Actions</h2>
      <p class="text-xs text-gray-500">Quickly manage your team and grants.</p>
    </div>
    <div class="flex gap-2">
      <button
        onclick={() => router.goToCreateGrant()}
        class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium shadow-sm transition-all active:scale-95"
      >
        + Create Grant
      </button>
      <button
        onclick={() => router.goToAssignTasks()}
        class="px-4 py-2 border border-blue-200 text-blue-700 bg-white rounded-md hover:bg-blue-50 text-sm font-medium shadow-sm transition-all active:scale-95"
      >
        Assign Tasks
      </button>
    </div>
  </div>

  <!-- Consolidated Closeout Tracker -->
  {#if closingGrants.length > 0}
    <div class="mb-8 p-6 bg-white/70 backdrop-blur-xl border border-indigo-100 rounded-3xl shadow-lg relative overflow-hidden">
      <!-- Decorative background element -->
      <div class="absolute top-0 right-0 -mt-10 -mr-10 w-64 h-64 bg-indigo-50/50 rounded-full blur-3xl"></div>
      
      <div class="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
        <div class="flex items-start gap-4">
          <div class="w-14 h-14 bg-indigo-50 rounded-2xl flex items-center justify-center shrink-0 border border-indigo-100 shadow-sm">
            <svg class="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h2 class="text-2xl font-bold text-gray-900">Priority Closeouts</h2>
            <p class="text-gray-600 mt-1 max-w-2xl text-sm">
              You have {closingGrants.length} projects heading for final reporting. Action is required to generate immutable dossiers for audit archiving.
            </p>
          </div>
        </div>
      </div>

      <div class="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 relative z-10">
        {#each closingGrants as grant}
          <div class="bg-white/50 backdrop-blur-md rounded-2xl p-4 border border-indigo-50 hover:border-indigo-200 hover:bg-white/80 transition-all group shadow-sm">
            <div class="flex flex-col h-full">
              <div class="flex justify-between items-start mb-3">
                <span class="px-2 py-1 bg-indigo-50 text-indigo-700 border border-indigo-100 rounded text-[10px] font-bold tracking-wider uppercase">{grant.grant_code}</span>
                {#if getDaysRemaining(grant.end_date) !== null}
                  <span class="text-xs font-semibold {getDaysRemaining(grant.end_date) < 7 ? 'text-rose-600' : 'text-indigo-600'}">
                    {getDaysRemaining(grant.end_date) < 0 ? 'Ended' : `${getDaysRemaining(grant.end_date)} days left`}
                  </span>
                {/if}
              </div>
              <h3 class="font-bold text-sm text-gray-900 line-clamp-1 mb-4 transition-colors">
                {grant.title}
              </h3>
              <button 
                onclick={() => startCloseout(grant.id)}
                class="mt-auto px-4 py-2 bg-indigo-600 text-white rounded-xl font-bold text-xs shadow-md hover:bg-indigo-700 active:scale-95 transition-all text-center"
              >
                Launch Closeout Wizard →
              </button>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Overview cards -->
  <div class="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-6 gap-4">
    <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-4 shadow-md">
      <h3 class="font-medium text-gray-500 text-xs uppercase tracking-wider">Active Grants</h3>
      <p class="text-2xl mt-1 font-bold text-gray-900">{activeGrantsCount}</p>
      <p class="text-[10px] text-gray-500 mt-1">Lead or Co-PI role</p>
    </div>

    <!-- Spending Lock Card -->
    <div class="p-4 rounded-2xl shadow-md backdrop-blur-xl {globalSpendingLock === 'locked' ? 'border-red-200 bg-red-50/70' : globalSpendingLock === 'warning' ? 'border-amber-200 bg-amber-50/70' : 'border-white/60 bg-white/70'}">
      <h3 class="font-medium text-gray-500 text-xs uppercase tracking-wider">Spending Lock</h3>
      <div class="flex items-center gap-2 mt-1">
        <div class="w-2 h-2 rounded-full {globalSpendingLock === 'locked' ? 'bg-red-500' : globalSpendingLock === 'warning' ? 'bg-amber-500' : 'bg-green-500'} animate-pulse"></div>
        <p class="text-xl font-bold {globalSpendingLock === 'locked' ? 'text-red-700' : globalSpendingLock === 'warning' ? 'text-amber-700' : 'text-green-700'}">
          {globalSpendingLock === 'locked' ? 'HARD LOCKED' : globalSpendingLock === 'warning' ? 'WARNING' : 'UNLOCKED'}
        </p>
      </div>
      <p class="text-[10px] text-gray-500 mt-1">Based on effort certs</p>
    </div>

    <!-- Asset Integrity Card -->
    <div class="p-4 rounded-2xl shadow-md backdrop-blur-xl {totalPendingAssets > 0 ? 'border-amber-200 bg-amber-50/70' : 'border-white/60 bg-white/70'}">
      <h3 class="font-medium text-gray-500 text-xs uppercase tracking-wider">Missing Assets</h3>
      <p class="text-2xl mt-1 font-bold {totalPendingAssets > 0 ? 'text-amber-600' : 'text-gray-900'}">{totalPendingAssets}</p>
      <p class="text-[10px] text-gray-500 mt-1">Overdue for return</p>
    </div>

    <!-- Rule Violations Card -->
    <div class="p-4 rounded-2xl shadow-md backdrop-blur-xl {totalRuleViolations > 0 ? 'border-red-200 bg-red-50/70' : 'border-white/60 bg-white/70'}">
      <h3 class="font-medium text-gray-500 text-xs uppercase tracking-wider">Rule Violations</h3>
      <p class="text-2xl mt-1 font-bold {totalRuleViolations > 0 ? 'text-red-600' : 'text-gray-900'}">{totalRuleViolations}</p>
      <p class="text-[10px] text-gray-500 mt-1">Across all active projects</p>
    </div>

    <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-4 shadow-md">
      <h3 class="font-medium text-gray-500 text-xs uppercase tracking-wider">Tranches Ready</h3>
      <p class="text-2xl mt-1 font-bold text-indigo-700">{actionItems?.ready_tranches?.length || 0}</p>
      <p class="text-[10px] text-gray-500 mt-1">Available to request</p>
    </div>

    <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-4 shadow-md">
      <h3 class="font-medium text-gray-500 text-xs uppercase tracking-wider">Audit Score</h3>
      <p class="text-2xl mt-1 font-bold text-blue-700">
        {myGrants.length > 0 ? Math.round(myGrants.reduce((avg, g) => avg + (g.audit_readiness_score || 0), 0) / myGrants.length) : 0}%
      </p>
      <p class="text-[10px] text-gray-500 mt-1">Avg readiness avg</p>
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Compliance Health Card -->
    <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-4 shadow-md flex flex-col">
      <div class="flex items-center justify-between mb-3">
        <div>
          <h3 class="font-semibold text-gray-900">Compliance Health</h3>
          <p class="text-sm text-gray-600">
            Overall system status and asset integrity
          </p>
        </div>
      </div>
      <div class="mt-4 flex-1 min-h-[300px]">
        <Chart options={complianceDonutOptions} />
      </div>
    </div>

    <!-- Burn Rate Chart -->
    <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-4 shadow-md flex flex-col">
      <div class="flex items-center justify-between mb-3">
        <div>
          <h3 class="font-semibold text-gray-900">Budget Utilisation (Burn Rate)</h3>
          <p class="text-sm text-gray-600">
            Time elapsed vs budget spent comparison
          </p>
        </div>
      </div>
      {#if myGrants.length > 0}
        <div class="mt-4 flex-1 min-h-[300px]">
          <Chart options={burnRateChartOptions} />
        </div>
      {:else}
        <p class="text-center py-4 text-gray-500 text-sm flex-1">
          No grant data available for burn rate analysis.
        </p>
      {/if}

      <!-- Debug Mode Toggle (Hidden in production usually, but helpful now) -->
      <div class="mt-12 pt-8 border-t border-gray-200">
        <button 
          onclick={() => showDebug = !showDebug}
          class="text-xs text-gray-400 hover:text-gray-600 underline"
        >
          {showDebug ? 'Hide Debug Info' : 'Show Debug Info'}
        </button>

        {#if showDebug}
          <div class="mt-4 p-4 bg-gray-900 text-green-400 rounded-lg overflow-auto max-h-96 text-xs font-mono">
            <h3 class="text-white font-bold mb-2">Raw API Response Context:</h3>
            <pre>{JSON.stringify(rawResponse, null, 2)}</pre>
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- My Grants (Financial & Timeline Overview) -->
  <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl p-6 shadow-lg">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="text-xl font-bold text-gray-900">Portfolio Financial Overview</h3>
        <p class="text-sm text-gray-600">Real-time spend tracking and deadline proximity</p>
      </div>
      <button
        class="px-4 py-2 text-sm font-bold text-blue-600 border border-blue-100 rounded-xl hover:bg-blue-50 transition-colors"
        onclick={() => router.goToGrants()}
      >
        Manage Portfolio →
      </button>
    </div>
    
    <div class="overflow-x-auto">
      <table class="w-full text-left border-separate border-spacing-y-2">
        <thead>
          <tr class="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-4">
            <th class="pb-2 pl-4">Grant Details</th>
            <th class="pb-2 text-right">Budget Utilization</th>
            <th class="pb-2 text-right">Days Left</th>
            <th class="pb-2 text-center">Risk</th>
            <th class="pb-2 pr-4 text-center">Status</th>
          </tr>
        </thead>
        <tbody>
          {#each myGrants.slice(0, 5) as grant}
            <tr class="bg-white/40 hover:bg-white/80 transition-all rounded-2xl group shadow-sm">
              <td class="py-4 pl-4 rounded-l-2xl border-l border-white/60">
                <div class="flex items-center gap-3">
                  <div class="hidden sm:flex w-10 h-10 rounded-xl bg-blue-50 text-blue-600 items-center justify-center font-bold text-xs border border-blue-100">
                    {grant.grant_code?.slice(-2)}
                  </div>
                  <div>
                    <p class="text-sm font-bold text-gray-900 group-hover:text-blue-600 transition-colors">{grant.title}</p>
                    <p class="text-[10px] font-mono text-gray-500 uppercase">{grant.grant_code} • {grant.next_deadline_label}</p>
                  </div>
                </div>
              </td>
              <td class="py-4 text-right">
                <div class="flex flex-col items-end gap-1.5 min-w-[140px]">
                  <span class="text-xs font-bold text-gray-900">{grant.spent_percent}% spent</span>
                  <div class="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                    <div 
                      class="h-full rounded-full transition-all duration-500 {grant.spent_percent > 90 ? 'bg-rose-500' : grant.spent_percent > 75 ? 'bg-amber-500' : 'bg-emerald-500'}" 
                      style="width: {grant.spent_percent}%"
                    ></div>
                  </div>
                </div>
              </td>
              <td class="py-4 text-right">
                {#if getDaysRemaining(grant.end_date) !== null}
                  <div class="flex flex-col items-end">
                    <span class="text-sm font-bold {getDaysRemaining(grant.end_date) < 30 ? 'text-rose-600' : 'text-gray-900'}">
                      {getDaysRemaining(grant.end_date)}
                    </span>
                    <span class="text-[10px] text-gray-400 uppercase">Days Left</span>
                  </div>
                {:else}
                  <span class="text-sm text-gray-300">N/A</span>
                {/if}
              </td>
              <td class="py-4 text-center">
                <div class="inline-flex items-center gap-1.5 px-2 py-1 rounded-lg {grant.burn_rate?.status === 'high' ? 'bg-rose-50 text-rose-700' : grant.burn_rate?.status === 'low' ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'}">
                  <div class="w-1.5 h-1.5 rounded-full {grant.burn_rate?.status === 'high' ? 'bg-rose-500' : grant.burn_rate?.status === 'low' ? 'bg-amber-500' : 'bg-emerald-500'}"></div>
                  <span class="text-[10px] font-bold uppercase tracking-tighter">{grant.burn_rate?.status || 'On Track'}</span>
                </div>
              </td>
              <td class="py-4 pr-4 text-center rounded-r-2xl border-r border-white/60">
                <span class="px-2 py-1 text-[10px] font-bold rounded-lg uppercase {statusBadge(grant.status)}">
                  {grant.status}
                </span>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Milestone & Asset Flow Timeline -->
  <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-5 shadow-md mb-6">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-gray-900 flex items-center gap-2">
          <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          Milestone & Asset Flow
        </h3>
        <p class="text-sm text-gray-600">Upcoming task deadlines and flow</p>
      </div>
    </div>
    
    {#if upcoming14Days.length > 0}
      <div class="mt-4">
        <Chart options={timelineOptions} />
      </div>
    {:else}
      <div class="text-center py-8 text-gray-500 text-sm bg-gray-50 rounded-lg">
        No upcoming milestones or tasks in the immediate horizon.
      </div>
    {/if}
  </div>

  <!-- Actionable Work Queue -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-5 shadow-md">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-bold text-gray-900 flex items-center gap-2">
          <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
          </svg>
          Actionable Work Queue
        </h3>
        <div class="flex items-center gap-2">
          <button 
            onclick={() => taskPage = Math.max(1, taskPage - 1)}
            disabled={taskPage === 1}
            class="p-1 rounded hover:bg-gray-100 disabled:opacity-30"
          >
            ←
          </button>
          <span class="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Page {taskPage}</span>
          <button 
            onclick={() => taskPage++}
            class="p-1 rounded hover:bg-gray-100"
          >
            →
          </button>
        </div>
      </div>
      
      <div class="space-y-4 max-h-[500px] overflow-y-auto pr-2">
        <!-- Tranche Readiness (Paginated) -->
        {#each (actionItems?.ready_tranches || []).slice((taskPage - 1) * dashboardPageSize, taskPage * dashboardPageSize) as tranche}
          <div class="p-3 rounded-lg bg-indigo-50 border border-indigo-100 border-l-4 border-l-indigo-500">
            <div class="flex justify-between items-start">
              <div>
                <p class="text-sm font-bold text-indigo-900">Tranche {tranche.tranche_number} Ready</p>
                <p class="text-xs text-indigo-700">{tranche.grant_title}</p>
                <p class="text-[10px] text-indigo-600 mt-1">Gating milestones completed. Ready to request disbursement.</p>
              </div>
              <p class="text-sm font-bold text-indigo-900">{tranche.amount} {tranche.currency}</p>
            </div>
            <button class="mt-2 text-xs font-bold text-indigo-700 hover:underline">Request Release →</button>
          </div>
        {/each}

        <!-- Asset Return Overdue (Team) (Paginated) -->
        {#each (actionItems?.overdue_team_assets || []).slice((taskPage - 1) * dashboardPageSize, taskPage * dashboardPageSize) as asset}
          <div class="p-3 rounded-lg bg-red-50 border border-red-100 border-l-4 border-l-red-500">
            <div class="flex justify-between items-start">
              <div>
                <p class="text-sm font-bold text-red-900">Asset Return Overdue: {asset.name}</p>
                <p class="text-xs text-red-700">Held by: {asset.assigned_to}</p>
                <p class="text-[10px] text-red-600 mt-1">Task: {asset.task_title}</p>
              </div>
              <span class="text-[10px] uppercase font-bold text-red-500 flex items-center gap-1">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
                Critical
              </span>
            </div>
            <div class="mt-2 flex gap-2">
              <button class="text-xs font-bold text-red-700 hover:underline">Ping Member</button>
              <button class="text-xs font-bold text-gray-600 hover:underline">View Task</button>
            </div>
          </div>
        {/each}

        <!-- Pending Deliverable Approvals (Paginated) -->
        {#each deliverablesQueue.slice((taskPage - 1) * dashboardPageSize, taskPage * dashboardPageSize) as item}
          <div class="p-3 rounded-lg bg-white border border-gray-200 hover:border-blue-300 transition-colors shadow-sm">
            <div class="flex justify-between items-start">
              <div class="flex-1">
                <p class="text-sm font-bold text-gray-900">{item.task_title}</p>
                <p class="text-xs text-gray-600">By {item.assignee_name} • {formatDate(item.last_updated || item.submitted_at)}</p>
              </div>
              {#if item.unreturned_assets > 0}
                <span class="px-2 py-0.5 bg-amber-100 text-amber-800 text-[10px] font-bold rounded-full flex items-center gap-1">
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
                  </svg>
                  {item.unreturned_assets} ASSETS PENDING
                </span>
              {/if}
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider {statusBadge(item.status)}">{item.status}</span>
              <button 
                class="px-3 py-1 bg-gray-900 text-white text-xs font-bold rounded hover:bg-gray-800"
                onclick={() => router.goToReviewDeliverables()}
              >
                Review & Certify
              </button>
            </div>
          </div>
        {/each}

        <!-- Upcoming Deadlines (Paginated) -->
        {#each upcoming14Days.slice((taskPage - 1) * dashboardPageSize, taskPage * dashboardPageSize) as t}
          <div class="p-3 rounded-lg bg-amber-50 border border-amber-100 border-l-4 border-l-amber-500">
            <div class="flex justify-between items-start">
              <div>
                <p class="text-sm font-bold text-amber-900">Upcoming Deadline: {t.title}</p>
                <p class="text-xs text-amber-700">Due: {formatDate(t.deadline)}</p>
                <p class="text-[10px] text-amber-600 mt-1">Status: {t.status}</p>
              </div>
              <span class="text-[10px] uppercase font-bold text-amber-500 flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                14 Days
              </span>
            </div>
            <button class="mt-2 text-xs font-bold text-amber-700 hover:underline">Complete Task →</button>
          </div>
        {/each}

        {#if (actionItems?.ready_tranches || []).length === 0 && (actionItems?.overdue_team_assets || []).length === 0 && deliverablesQueue.length === 0 && upcoming14Days.length === 0}
          <div class="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-200">
            <p class="text-sm text-gray-400">All caught up! No critical actions pending.</p>
          </div>
        {/if}
      </div>
    </div>

    <!-- Personally Custodied Assets & Team Alerts -->
    <div class="space-y-6">
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-5 shadow-md">
        <h3 class="font-bold text-gray-900 mb-4 flex items-center gap-2">
          <svg class="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
          </svg>
          Personally Custodied Assets
        </h3>
        <div class="space-y-2 max-h-[300px] overflow-y-auto">
          {#each (actionItems.my_custody_assets || []).slice(0, 5) as asset}
            <div class="flex items-center justify-between p-3 rounded-lg border border-gray-100 bg-gray-50">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded bg-orange-100 flex items-center justify-center text-orange-600 font-bold text-xs">
                  {asset.asset_tag.slice(-2)}
                </div>
                <div>
                  <p class="text-sm font-bold text-gray-800">{asset.name}</p>
                  <p class="text-[10px] text-gray-500">{asset.asset_tag} • {asset.category}</p>
                </div>
              </div>
              <button class="text-xs font-bold text-blue-600 hover:underline">Initiate Return</button>
            </div>
          {:else}
            <p class="text-sm text-gray-400 text-center py-4">No assets currently assigned to you.</p>
          {/each}
        </div>
      </div>

      <!-- Audit Readiness & Documentation Checklist -->
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-5 shadow-md">
        <h3 class="font-bold text-gray-900 mb-4 flex items-center gap-2">
          <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          Audit Readiness Checklist
        </h3>
        <div class="space-y-3 max-h-[350px] overflow-y-auto">
          {#each myGrants.slice(0, 5) as grant}
            <div class="p-3 rounded-lg border border-gray-100">
              <div class="flex justify-between items-center mb-2">
                <span class="text-xs font-bold text-gray-700">{grant.grant_code}</span>
                <span class="text-xs font-bold {grant.audit_readiness_score > 80 ? 'text-green-600' : 'text-amber-600'}">{grant.audit_readiness_score}% Readiness</span>
              </div>
              <div class="w-full bg-gray-100 rounded-full h-1.5 mb-2">
                <div class="h-1.5 rounded-full {grant.audit_readiness_score > 80 ? 'bg-green-500' : 'bg-amber-500'}" style="width: {grant.audit_readiness_score}%"></div>
              </div>
              {#if grant.missing_docs_count > 0}
                <p class="text-[10px] text-red-500 font-bold flex items-center gap-1">
                  <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                  </svg>
                  {grant.missing_docs_count} REQUIRED DOCUMENTS MISSING (AGREEMENTS/EVIDENCE)
                </p>
              {:else}
                <p class="text-[10px] text-green-600 font-bold flex items-center gap-1">
                  <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                  </svg>
                  ALL KEY DOCUMENTATION VERIFIED
                </p>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    </div>
  </div>

  <!-- Strategic Impact (KPIs) -->
  <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-md">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="text-lg font-bold text-gray-900">Strategic Impact Metrics</h3>
        <p class="text-sm text-gray-600">
          Target vs. Actual achievement across all grant portfolios
        </p>
      </div>
      <div class="flex gap-2">
        <span class="flex items-center gap-1 text-xs text-green-600 font-bold"><span class="w-2 h-2 rounded-full bg-green-500"></span> On Track</span>
        <span class="flex items-center gap-1 text-xs text-amber-600 font-bold"><span class="w-2 h-2 rounded-full bg-amber-500"></span> At Risk</span>
      </div>
    </div>
    
    <div class="mt-4">
      <Chart options={kpiStackedOptions} />
    </div>
  </div>

  <!-- Submit Expenses & Certify Effort -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-4 shadow-md">
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-semibold text-gray-900">Expenses Overview</h3>
        <button class="text-sm text-blue-700 hover:underline">View all</button>
      </div>
      <div class="space-y-2 max-h-[300px] overflow-y-auto">
        {#each expenses.slice(0, 5) as exp}
          <div
            class="flex items-center justify-between p-3 rounded-lg bg-gray-50 border border-gray-100"
          >
            <div>
              <p class="text-sm font-medium text-gray-900">{exp.category}</p>
              <p class="text-xs text-gray-600">
                {exp.amount}
                {exp.currency} • {exp.grant_title}
              </p>
            </div>
            <span
              class="px-2 py-1 text-xs font-bold rounded-lg uppercase {statusBadge(exp.status)}"
              >{exp.status}</span
            >
          </div>
        {:else}
          <p class="text-center py-4 text-gray-500 text-sm">
            No expenses found.
          </p>
        {/each}
      </div>
    </div>

    <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-4 shadow-md">
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-semibold text-gray-900">Certify Effort</h3>
        <button
          class="text-sm text-blue-700 hover:underline"
          onclick={() => router.goToReviewDeliverables()}>Approve hours</button
        >
      </div>
      <div class="space-y-2 max-h-[300px] overflow-y-auto">
        {#each effort.slice(0, 5) as row}
          <div
            class="flex items-center justify-between p-3 rounded-lg bg-gray-50 border border-gray-100"
          >
            <div>
              <p class="text-sm font-medium text-gray-900">{row.name}</p>
              <p class="text-xs text-gray-600">
                {row.period} • {row.hours} hrs
              </p>
            </div>
            <span
              class="px-2 py-1 text-xs rounded-full bg-amber-100 text-amber-800"
              >{row.status}</span
            >
          </div>
        {:else}
          <p class="text-center py-4 text-gray-500 text-sm">
            No effort to certify.
          </p>
        {/each}
      </div>
    </div>
  </div>

  <!-- Generate Reports & Notifications -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-4 shadow-md">
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-semibold text-gray-900">Generate Reports</h3>
        <button class="text-sm text-blue-700 hover:underline"
          >Draft report</button
        >
      </div>
      <p class="text-sm text-gray-600 mb-3">
        Auto-filled progress and financial reports.
      </p>
      <div class="flex gap-2">
        <button
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >Progress</button
        >
        <button
          class="px-4 py-2 border border-blue-200 text-blue-700 rounded-md hover:bg-blue-50"
          >Financial</button
        >
      </div>
    </div>

    <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-4 shadow-md">
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-semibold text-gray-900">Notifications</h3>
        <button class="text-sm text-blue-700 hover:underline">View all</button>
      </div>
      <ul class="space-y-2">
        {#each notifications as note}
          <li
            class="p-3 rounded-lg bg-gray-50 border border-gray-100 text-sm text-gray-800"
          >
            {note}
          </li>
        {:else}
          <p class="text-center py-4 text-gray-500 text-sm">
            No new notifications.
          </p>
        {/each}
      </ul>
    </div>
  </div>
</div>
