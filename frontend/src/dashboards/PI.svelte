<script>
  import { onMount } from "svelte";
  import axios from "axios";
  import { router } from "../stores/router.js";

  // Enable credentials for Flask sessions
  axios.defaults.withCredentials = true;

  let loading = true;
  let myGrants = [];
  let evidenceQueue = [];
  let expenses = [];
  let allTasks = []; // New variable for all tasks
  let effort = []; // We'll derive this from evidenceQueue or a separate endpoint if needed
  let notifications = [];

  // Overview stats derived from data
  $: activeGrantsCount = myGrants.filter((g) => g.status === "active").length;
  $: upcomingDeadlinesCount = myGrants.filter(
    (g) => g.next_deadline_date,
  ).length;
  $: budgetAlertsCount = myGrants.filter((g) => g.spent_percent > 85).length;
  // New task summary stats
  $: outstandingTasksCount = allTasks.filter(
    (t) => t.status === "assigned" || t.status === "in_progress",
  ).length;
  $: overdueTasksCount = allTasks.filter((t) => t.status === "overdue").length;

  async function fetchDashboardData() {
    loading = true;
    try {
      const [grantsRes, evidenceRes, expensesRes, tasksRes] = await Promise.all(
        [
          // Added tasksRes
          axios.get("http://localhost:5000/api/grants"),
          axios.get("http://localhost:5000/api/evidence?status=pending"),
          axios.get("http://localhost:5000/api/expenses"),
          axios.get("http://localhost:5000/api/tasks"), // Fetch all tasks for the PI
        ],
      );

      myGrants = grantsRes.data || [];
      evidenceQueue = (evidenceRes.data.submissions || []).map((e) => ({
        ...e,
        assignee_name: e.team_member, // Map for backward compatibility in UI
      }));
      expenses = expensesRes.data.expenses || [];
      allTasks = tasksRes.data.tasks || []; // Store fetched tasks

      // For now, certifiable effort is same as pending evidence
      effort = evidenceQueue.map((e) => ({
        name: e.assignee_name,
        hours: e.hours_worked,
        period: new Date(e.submitted_at).toLocaleDateString(undefined, {
          month: "short",
          year: "numeric",
        }),
        status: "Pending PI approval",
      }));

      // Simple notifications based on alerts
      notifications = [];
      myGrants.forEach((g) => {
        if (g.spent_percent > 85) {
          notifications.push(
            `Grant ${g.grant_code}: budget above 85% (${g.spent_percent}%)`,
          );
        }
      });
      if (evidenceQueue.length > 0) {
        notifications.push(
          `You have ${evidenceQueue.length} new evidence submissions to review`,
        );
      }
      // Add notification for overdue tasks
      if (overdueTasksCount > 0) {
        notifications.push(`You have ${overdueTasksCount} overdue tasks!`);
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
    if (s === "active") return "bg-green-100 text-green-800";
    if (s === "closed") return "bg-gray-100 text-gray-700";
    if (s === "low balance" || s === "pending")
      return "bg-amber-100 text-amber-800";
    return "bg-blue-100 text-blue-800";
  }

  function formatDate(dateStr) {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString();
  }
</script>

<div class="space-y-6">
  <div
    class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
  >
    <div>
      <h2 class="text-2xl font-bold text-gray-900">Principal Investigator</h2>
      <p class="text-sm text-gray-600">
        Overview of active grants, deadlines, budgets, and tasks.
      </p>
    </div>
    <div class="flex gap-2">
      <button
        on:click={() => router.goToCreateGrant()}
        class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
      >
        + Create Grant
      </button>
      <button
        on:click={() => router.goToAssignTasks()}
        class="px-4 py-2 border border-blue-200 text-blue-700 rounded-md hover:bg-blue-50"
      >
        Assign Tasks
      </button>
    </div>
  </div>

  <!-- Overview cards -->
  <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
    <!-- Changed to md:grid-cols-4 -->
    <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
      <h3 class="font-medium text-gray-900">Active Grants</h3>
      <p class="text-3xl mt-2 font-bold text-blue-700">{activeGrantsCount}</p>
      <p class="text-xs text-gray-500 mt-1">
        From total of {myGrants.length} grants
      </p>
    </div>
    <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
      <h3 class="font-medium text-gray-900">Upcoming Deadlines</h3>
      <p class="text-3xl mt-2 font-bold text-amber-600">
        {upcomingDeadlinesCount}
      </p>
      <p class="text-xs text-gray-500 mt-1">Includes reports and tasks</p>
    </div>
    <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
      <h3 class="font-medium text-gray-900">Outstanding Tasks</h3>
      <p class="text-3xl mt-2 font-bold text-indigo-700">
        {outstandingTasksCount}
      </p>
      <p class="text-xs text-gray-500 mt-1">Assigned or in progress</p>
    </div>
    <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
      <h3 class="font-medium text-gray-900">Overdue Tasks</h3>
      <p class="text-3xl mt-2 font-bold text-red-600">{overdueTasksCount}</p>
      <p class="text-xs text-gray-500 mt-1">Tasks past their deadline</p>
    </div>
    <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
      <h3 class="font-medium text-gray-900">Budget Alerts</h3>
      <p class="text-3xl mt-2 font-bold text-rose-600">{budgetAlertsCount}</p>
      <p class="text-xs text-gray-500 mt-1">
        Grants over 85% budget utilization
      </p>
    </div>
  </div>

  <!-- My Grants -->
  <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
    <div class="flex items-center justify-between mb-3">
      <div>
        <h3 class="font-semibold text-gray-900">My Grants</h3>
        <p class="text-sm text-gray-600">
          Grants you lead with status and deadlines
        </p>
      </div>
      <button
        class="text-sm text-blue-700 hover:underline"
        on:click={() => router.goToGrants()}>View all</button
      >
    </div>
    <div class="divide-y divide-gray-100">
      {#each myGrants as grant}
        <div
          class="py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
        >
          <div>
            <p class="font-semibold text-gray-900">{grant.title}</p>
            <p class="text-xs text-gray-600">{grant.grant_code}</p>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-sm text-gray-700"
              >Next: {grant.next_deadline_label} ({formatDate(
                grant.next_deadline_date,
              )})</span
            >
            <span
              class="px-2 py-1 text-xs font-semibold rounded-full {statusBadge(
                grant.status,
              )}">{grant.status}</span
            >
            {#if grant.spent_percent > 85}
              <span
                class="px-2 py-1 text-xs font-semibold rounded-full bg-amber-100 text-amber-800"
                >{grant.spent_percent}% Spent</span
              >
            {/if}
          </div>
        </div>
      {:else}
        <p class="py-4 text-center text-gray-500 text-sm">No grants found.</p>
      {/each}
    </div>
  </div>

  <!-- Assign Tasks & Review Evidence -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-semibold text-gray-900">Assign Tasks</h3>
        <button
          class="text-sm text-blue-700 hover:underline"
          on:click={() => router.goToAssignTasks()}>Open tasks</button
        >
      </div>
      <p class="text-sm text-gray-600 mb-3">
        Create and assign tasks to team members.
      </p>
      <button
        on:click={() => router.goToAssignTasks()}
        class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
      >
        Create / Assign
      </button>
    </div>

    <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-semibold text-gray-900">Review Evidence</h3>
        <button
          class="text-sm text-blue-700 hover:underline"
          on:click={() => router.goToReviewEvidence()}>Go to evidence</button
        >
      </div>
      <div class="space-y-2">
        {#each evidenceQueue as item}
          <div class="p-3 rounded-lg bg-gray-50 border border-gray-100">
            <p class="font-medium text-gray-900 text-sm">{item.task_title}</p>
            <p class="text-xs text-gray-600">
              By {item.assignee_name} • {formatDate(item.submitted_at)}
            </p>
            <span
              class="inline-block mt-1 px-2 py-1 text-xs rounded-full bg-amber-100 text-amber-800"
              >{item.status}</span
            >
          </div>
        {:else}
          <p class="text-center py-4 text-gray-500 text-sm">
            No pending evidence.
          </p>
        {/each}
      </div>
    </div>
  </div>

  <!-- Submit Expenses & Certify Effort -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-semibold text-gray-900">Expenses Overview</h3>
        <button class="text-sm text-blue-700 hover:underline">View all</button>
      </div>
      <div class="space-y-2">
        {#each expenses as exp}
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
              class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800"
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

    <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-semibold text-gray-900">Certify Effort</h3>
        <button
          class="text-sm text-blue-700 hover:underline"
          on:click={() => router.goToReviewEvidence()}>Approve hours</button
        >
      </div>
      <div class="space-y-2">
        {#each effort as row}
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
    <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
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

    <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
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
