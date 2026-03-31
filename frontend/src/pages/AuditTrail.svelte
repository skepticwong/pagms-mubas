<script>
  import { onMount } from "svelte";
  import axios from "axios";
  import Layout from "../components/Layout.svelte";
  import { router } from "../stores/router.js";
  import { user } from "../stores/auth.js";

  axios.defaults.withCredentials = true;

  let auditLogs = [];
  let filteredLogs = [];
  let isLoading = true;
  let error = "";

  // Filters
  let searchQuery = "";
  let selectedAction = "all";
  let selectedResource = "all";

  // Stats
  $: todayCount = auditLogs.filter((log) => isToday(log.timestamp)).length;
  $: evidenceCount = auditLogs.filter((log) =>
    log.action.includes("evidence") || log.action.includes("deliverable"),
  ).length;
  $: expenseCount = auditLogs.filter((log) =>
    log.action.includes("expense"),
  ).length;
  $: teamActionCount = auditLogs.filter(
    (log) => log.user_id !== $user?.id,
  ).length;

  // Get unique action types and resource types
  $: actionTypes = ["all", ...new Set(auditLogs.map((log) => log.action))];
  $: resourceTypes = [
    "all",
    ...new Set(auditLogs.map((log) => log.resource_type)),
  ];

  // Apply filters
  $: {
    filteredLogs = auditLogs.filter((log) => {
      const matchesSearch =
        searchQuery === "" ||
        log.details?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.user_name?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesAction =
        selectedAction === "all" || log.action === selectedAction;
      const matchesResource =
        selectedResource === "all" || log.resource_type === selectedResource;
      return matchesSearch && matchesAction && matchesResource;
    });
  }

  onMount(async () => {
    try {
      const me = await axios.get("http://localhost:5000/api/me");
      if (!me.data) {
        router.goToLogin();
        return;
      }
      await fetchAuditLogs();
    } catch (err) {
      router.goToLogin();
    }
  });

  async function fetchAuditLogs() {
    isLoading = true;
    error = "";
    try {
      const response = await axios.get("http://localhost:5000/api/audit-logs");
      auditLogs = response.data.audit_logs || [];
    } catch (err) {
      console.error("Error fetching audit logs:", err);
      error = "Failed to load audit logs. Please try again.";
    } finally {
      isLoading = false;
    }
  }

  function isToday(timestampString) {
    if (!timestampString) return false;
    const date = new Date(timestampString);
    const today = new Date();
    return date.toDateString() === today.toDateString();
  }

  function formatTimestamp(timestampString) {
    if (!timestampString) return "N/A";
    const date = new Date(timestampString);
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function getRelativeTime(timestampString) {
    if (!timestampString) return "";
    const date = new Date(timestampString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return formatTimestamp(timestampString);
  }

  function getActionIcon(action) {
    if (action.includes("evidence") || action.includes("deliverable")) return "📋";
    if (action.includes("expense")) return "💰";
    if (action.includes("task")) return "✓";
    if (action.includes("grant")) return "📁";
    if (action.includes("team")) return "👥";
    return "📌";
  }

  function getActionColor(action) {
    if (action.includes("approved"))
      return "text-green-700 bg-green-50 border-green-200";
    if (action.includes("rejected") || action.includes("deleted"))
      return "text-red-700 bg-red-50 border-red-200";
    if (action.includes("revision"))
      return "text-amber-700 bg-amber-50 border-amber-200";
    if (action.includes("submitted") || action.includes("created"))
      return "text-blue-700 bg-blue-50 border-blue-200";
    return "text-gray-700 bg-gray-50 border-gray-200";
  }

  function formatActionName(action) {
    return action.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
  }
</script>

<Layout>
  <div class="max-w-7xl mx-auto space-y-6">
    <!-- Header -->
    <div
      class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
    >
      <div>
        <h1 class="text-3xl font-bold text-gray-900">Audit Trail</h1>
        <p class="text-gray-600 mt-1">
          Track all activities across your grants
        </p>
      </div>
      <button
        on:click={fetchAuditLogs}
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        disabled={isLoading}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2"
          stroke="currentColor"
          class="w-4 h-4"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
          />
        </svg>
        Refresh
      </button>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white/70 backdrop-blur-xl p-4 rounded-2xl shadow-md border border-white/60">
        <h3 class="font-medium text-gray-900">Today's Activity</h3>
        <p class="text-3xl mt-2 font-bold text-blue-700">{todayCount}</p>
        <p class="text-xs text-gray-500 mt-1">Actions logged today</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl p-4 rounded-2xl shadow-md border border-white/60">
        <h3 class="font-medium text-gray-900">Deliverable Actions</h3>
        <p class="text-3xl mt-2 font-bold text-green-600">{evidenceCount}</p>
        <p class="text-xs text-gray-500 mt-1">Submissions & approvals</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl p-4 rounded-2xl shadow-md border border-white/60">
        <h3 class="font-medium text-gray-900">Expense Actions</h3>
        <p class="text-3xl mt-2 font-bold text-amber-600">{expenseCount}</p>
        <p class="text-xs text-gray-500 mt-1">Claims & approvals</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl p-4 rounded-2xl shadow-md border border-white/60">
        <h3 class="font-medium text-gray-900">Team Actions</h3>
        <p class="text-3xl mt-2 font-bold text-indigo-700">{teamActionCount}</p>
        <p class="text-xs text-gray-500 mt-1">By team members</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label
            for="search"
            class="block text-sm font-medium text-gray-700 mb-1">Search</label
          >
          <input
            id="search"
            type="text"
            bind:value={searchQuery}
            placeholder="Search details or user..."
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label
            for="action"
            class="block text-sm font-medium text-gray-700 mb-1"
            >Action Type</label
          >
          <select
            id="action"
            bind:value={selectedAction}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {#each actionTypes as action}
              <option value={action}
                >{action === "all"
                  ? "All Actions"
                  : formatActionName(action)}</option
              >
            {/each}
          </select>
        </div>
        <div>
          <label
            for="resource"
            class="block text-sm font-medium text-gray-700 mb-1"
            >Resource Type</label
          >
          <select
            id="resource"
            bind:value={selectedResource}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {#each resourceTypes as resource}
              <option value={resource}
                >{resource === "all"
                  ? "All Resources"
                  : resource.charAt(0).toUpperCase() +
                    resource.slice(1)}</option
              >
            {/each}
          </select>
        </div>
      </div>
    </div>

    {#if error}
      <div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
        <p class="text-red-700">{error}</p>
      </div>
    {/if}

    {#if isLoading}
      <div class="flex flex-col items-center justify-center py-12">
        <div
          class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"
        ></div>
        <p class="text-gray-600">Loading audit logs...</p>
      </div>
    {:else if filteredLogs.length === 0}
      <div
        class="bg-white/40 backdrop-blur-xl border border-white/30 rounded-2xl shadow-lg p-12 text-center"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          class="w-16 h-16 mx-auto text-gray-400 mb-4"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
          />
        </svg>
        <h3 class="text-xl font-semibold text-gray-900 mb-2">No Audit Logs</h3>
        <p class="text-gray-600">
          {auditLogs.length === 0
            ? "Actions you take will appear here."
            : "No logs match your filters."}
        </p>
      </div>
    {:else}
      <div
        class="bg-white/70 backdrop-blur-xl rounded-2xl shadow-md border border-white/60 overflow-hidden"
      >
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-white/50 border-b border-white/60 backdrop-blur-sm">
              <tr>
                <th
                  class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider"
                  >User</th
                >
                <th
                  class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider"
                  >Action</th
                >
                <th
                  class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider"
                  >Resource</th
                >
                <th
                  class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider"
                  >Details</th
                >
                <th
                  class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider"
                  >Time</th
                >
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              {#each filteredLogs as log}
                <tr class="hover:bg-blue-50/50 transition-colors duration-150">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center gap-2">
                      <div
                        class="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-semibold text-sm"
                      >
                        {log.user_name?.charAt(0) || "U"}
                      </div>
                      <div>
                        <div class="text-sm font-medium text-gray-900">
                          {log.user_name || "Unknown"}
                        </div>
                        {#if log.user_id === $user?.id}
                          <div class="text-xs text-blue-600">You</div>
                        {/if}
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center gap-2">
                      <span class="text-lg">{getActionIcon(log.action)}</span>
                      <span
                        class="px-2 py-1 text-xs font-semibold rounded border {getActionColor(
                          log.action,
                        )}"
                      >
                        {formatActionName(log.action)}
                      </span>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-700 capitalize">
                      {log.resource_type}
                    </div>
                    {#if log.resource_id}
                      <div class="text-xs text-gray-500">
                        ID: {log.resource_id}
                      </div>
                    {/if}
                  </td>
                  <td class="px-6 py-4">
                    <div class="text-sm text-gray-700 max-w-md">
                      {log.details || "-"}
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-700">
                      {getRelativeTime(log.timestamp)}
                    </div>
                    <div class="text-xs text-gray-500">
                      {formatTimestamp(log.timestamp)}
                    </div>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
        <div
          class="px-6 py-3 bg-white/40 backdrop-blur-sm border-t border-white/60 text-sm text-gray-600"
        >
          Showing {filteredLogs.length} of {auditLogs.length} logs
        </div>
      </div>
    {/if}
  </div>
</Layout>
