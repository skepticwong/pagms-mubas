<script>
  import { router } from "../stores/router.js";
  import { user, logout } from "../stores/auth.js";
  import { setRsuNavTarget } from "../stores/rsuNav.js";
  import Icon from "./Icon.svelte";

  async function handleLogout() {
    await logout();
    router.goToLogin();
  }

  function goToRsuSection(sectionId) {
    setRsuNavTarget(sectionId);
    router.goToRSU();
  }
</script>

<div
  class="min-h-screen bg-gradient-to-br from-sky-100 via-white to-cyan-100 text-gray-900 flex"
>
  <aside
    class="w-64 hidden md:flex flex-col gap-2 bg-white/60 backdrop-blur-xl border-r border-white/40 p-6 shadow-lg sticky top-0 h-screen overflow-y-auto"
  >
    <div class="flex items-center gap-3 mb-6">
      <div
        class="h-12 w-12 rounded-2xl bg-blue-600 text-white flex items-center justify-center font-bold text-xl"
      >
        PAG
      </div>
      <div>
        <p class="text-sm text-gray-600">Post-Award</p>
        <p class="text-lg font-semibold text-gray-900">Grant Manager</p>
      </div>
    </div>

    <nav class="flex-1 space-y-1">
      {#if $user?.role === "PI"}
        <button
          class="nav-btn"
          class:active={$router === "dashboard"}
          on:click={() => router.goToDashboard()}
        >
          <span class="flex items-center gap-2"
            ><Icon name="dashboard" size={18} />Dashboard</span
          >
        </button>
        <button
          class="nav-btn"
          class:active={$router === "grants"}
          on:click={() => router.goToGrants()}
        >
          <span class="flex items-center gap-2"
            ><Icon name="folder" size={18} />Grants</span
          >
        </button>
        <button
          class="nav-btn"
          class:active={$router === "assign-tasks"}
          on:click={() => router.goToAssignTasks()}
        >
          <span class="flex items-center gap-2"
            ><Icon name="tasks" size={18} />Tasks</span
          >
        </button>
        <button
          class="nav-btn"
          class:active={$router === "grant-budgets"}
          on:click={() => router.goToGrantBudgets()}
        >
          <span class="flex items-center gap-2"
            ><Icon name="budget" size={18} />Budget</span
          >
        </button>
        <button
          class="nav-btn"
          class:active={$router === "expenses"}
          on:click={() => router.goToExpenses()}
        >
          <span class="flex items-center gap-2"
            ><Icon name="receipt" size={18} />Expenses</span
          >
        </button>
        <button
          class="nav-btn"
          class:active={$router === "team"}
          on:click={() => router.goToTeam()}
        >
          <span class="flex items-center gap-2"
            ><Icon name="users" size={18} />Team</span
          >
        </button>
        <button
          class="nav-btn"
          class:active={$router === "reports"}
          on:click={() => router.goToReports()}
        >
          <span class="flex items-center gap-2"
            ><Icon name="reports" size={18} />Reports</span
          >
        </button>
        <button
          class="nav-btn"
          class:active={$router === "audit-trail"}
          on:click={() => router.goToAuditTrail()}
        >
          <span class="flex items-center gap-2"
            ><Icon name="audit" size={18} />Audit Trail</span
          >
        </button>
        <button
          class="nav-btn"
          class:active={$router === "review-evidence"}
          on:click={() => router.goToReviewEvidence()}
        >
          <span class="flex items-center gap-2"
            ><Icon name="documentCheck" size={18} />Review Evidence</span
          >
        </button>
        <button
          class="nav-btn"
          class:active={$router === "documents"}
          on:click={() => router.goToDocuments()}
        >
          <span class="flex items-center gap-2"
            ><Icon name="document" size={18} />Documents</span
          >
        </button>
      {:else if $user?.role === "Team"}
        <button class="nav-btn" on:click={() => router.goToDashboard()}>
          <span class="flex items-center gap-2"
            ><Icon name="dashboard" size={18} />Dashboard</span
          >
        </button>
        <!-- <button class="nav-btn" on:click={() => router.goToDashboard()}>
          <span class="flex items-center gap-2"
            ><Icon name="tasks" size={18} />My Tasks</span
          >
        </button> -->
        <button class="nav-btn" on:click={() => router.goToTasks()}>
          <span class="flex items-center gap-2"
            ><Icon name="document" size={18} />My Tasks</span
          >
        </button>
        <button class="nav-btn" on:click={() => router.goToAuditTrail()}>
          <span class="flex items-center gap-2"
            ><Icon name="audit" size={18} />Audit Trail</span
          >
        </button>
        <button class="nav-btn" on:click={() => router.goToDocuments()}>
          <span class="flex items-center gap-2"
            ><Icon name="document" size={18} />Documents</span
          >
        </button>
      {:else if $user?.role === "Finance"}
        <button class="nav-btn" on:click={() => router.goToDashboard()}>
          <span class="flex items-center gap-2"
            ><Icon name="dashboard" size={18} />Dashboard</span
          >
        </button>
        <button class="nav-btn" on:click={() => router.goToPendingExpenses()}>
          <span class="flex items-center gap-2"
            ><Icon name="money" size={18} />Pending Expenses</span
          >
        </button>
        <button class="nav-btn" on:click={() => router.goToGrantBudgets()}>
          <span class="flex items-center gap-2"
            ><Icon name="budget" size={18} />Grant Budgets</span
          >
        </button>
        <button
          class="nav-btn"
          on:click={() => router.goToApprovedTransactions()}
        >
          <span class="flex items-center gap-2"
            ><Icon name="approvals" size={18} />Approved Transactions</span
          >
        </button>
        <button class="nav-btn" on:click={() => router.goToExchangeRates()}>
          <span class="flex items-center gap-2"
            ><Icon name="exchange" size={18} />Exchange Rates</span
          >
        </button>
        <button class="nav-btn" on:click={() => router.goToFinancialReports()}>
          <span class="flex items-center gap-2"
            ><Icon name="reports" size={18} />Financial Reports</span
          >
        </button>
        <button class="nav-btn" on:click={() => router.goToDocuments()}>
          <span class="flex items-center gap-2"
            ><Icon name="document" size={18} />Documents</span
          >
        </button>
      {:else if $user?.role === "RSU"}
        <button class="nav-btn" on:click={() => router.goToRSU()}>
          <span class="flex items-center gap-2">
            <Icon name="mission" size={18} />
            <span>Mission Control</span>
          </span>
        </button>
        <button class="nav-btn" on:click={() => router.goToGrants()}>
          <span class="flex items-center gap-2">
            <Icon name="folder" size={18} />
            <span>All Grants</span>
          </span>
        </button>
        <button
          class="nav-btn"
          on:click={() => goToRsuSection("pending-activations")}
        >
          <span class="flex items-center gap-2">
            <Icon name="pending" size={18} />
            <span>Pending Activations</span>
          </span>
        </button>
        <button
          class="nav-btn"
          on:click={() => goToRsuSection("compliance-center")}
        >
          <span class="flex items-center gap-2">
            <Icon name="compliance" size={18} />
            <span>Compliance</span>
          </span>
        </button>
        <button class="nav-btn" on:click={() => goToRsuSection("risk-monitor")}>
          <span class="flex items-center gap-2">
            <Icon name="risk" size={18} />
            <span>Risk Monitor</span>
          </span>
        </button>
        <button
          class="nav-btn"
          on:click={() => goToRsuSection("reports-deadlines")}
        >
          <span class="flex items-center gap-2">
            <Icon name="reports" size={18} />
            <span>Reports & Deadlines</span>
          </span>
        </button>
        <button class="nav-btn" on:click={() => goToRsuSection("audit-center")}>
          <span class="flex items-center gap-2">
            <Icon name="audit" size={18} />
            <span>Audit Center</span>
          </span>
        </button>
        <!-- <button class="nav-btn" on:click={() => goToRsuSection("field-map")}>
          <span class="flex items-center gap-2">
            <Icon name="field" size={18} />
            <span>Field Map</span>
          </span>
        </button> -->
        <button class="nav-btn" on:click={() => goToRsuSection("analytics")}>
          <span class="flex items-center gap-2">
            <Icon name="analytics" size={18} />
            <span>Analytics</span>
          </span>
        </button>
        <button
          class="nav-btn"
          on:click={() => goToRsuSection("user-management")}
        >
          <span class="flex items-center gap-2">
            <Icon name="users" size={18} />
            <span>User Management</span>
          </span>
        </button>
        <div class="pt-2 border-t border-white/40"></div>
        <button class="nav-btn" on:click={() => router.goToReports()}>
          <span class="flex items-center gap-2">
            <Icon name="reports" size={18} />
            <span>Compliance Reports</span>
          </span>
        </button>
        <button class="nav-btn" on:click={() => router.goToNotifications()}>
          <span class="flex items-center gap-2">
            <Icon name="warning" size={18} />
            <span>Notifications</span>
          </span>
        </button>
        <button class="nav-btn" on:click={() => router.goToDocuments()}>
          <span class="flex items-center gap-2">
            <Icon name="document" size={18} />
            <span>Documents</span>
          </span>
        </button>
      {/if}
    </nav>

    <div class="mt-auto space-y-2">
      <div class="rounded-xl bg-gray-100/80 p-3">
        <p class="text-xs text-gray-500">Signed in as</p>
        <p class="font-semibold text-gray-900">{$user?.name || "User"}</p>
        <p class="text-xs text-gray-600 truncate">{$user?.email || ""}</p>
      </div>
      <button
        class="w-full px-4 py-2 rounded-xl border border-gray-300 text-gray-700 hover:bg-gray-50"
        on:click={handleLogout}
      >
        Logout
      </button>
    </div>
  </aside>

  <div class="flex-1 flex flex-col">
    <header
      class="md:hidden flex items-center justify-between px-4 py-3 bg-white/70 backdrop-blur-xl border-b border-white/40 shadow-sm"
    >
      <div class="flex items-center gap-2">
        <div
          class="h-10 w-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-lg"
        >
          PAG
        </div>
        <div>
          <p class="text-sm font-semibold text-gray-900">Grant Manager</p>
          <p class="text-xs text-gray-600 truncate">
            {$user?.email || "Guest"}
          </p>
        </div>
      </div>
      <button
        class="px-3 py-2 rounded-lg bg-blue-600 text-white"
        on:click={() => router.goToDashboard()}
      >
        Home
      </button>
    </header>

    <main class="p-4 md:p-8">
      <slot />
    </main>
  </div>
</div>

<style>
  .nav-btn {
    width: 100%;
    text-align: left;
    padding: 0.85rem 1rem;
    border-radius: 12px;
    color: #1f2937;
    background: transparent;
    border: 1px solid transparent;
    font-weight: 600;
  }

  .nav-btn.active {
    background: #2563eb;
    color: white;
    box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.2);
  }

  .nav-btn:hover:not(.active) {
    background: rgba(59, 130, 246, 0.08);
    border-color: rgba(59, 130, 246, 0.15);
  }
</style>
