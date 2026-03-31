<script>
  import { router } from "../stores/router.js";
  import { user, logout } from "../stores/auth.js";
  import { setRsuNavTarget } from "../stores/rsuNav.js";
  import Icon from "./Icon.svelte";
  import Toast from "./Toast.svelte";
  import Modal from "./Modal.svelte";
  import { notifications } from "../stores/notifications.js";

  let isMobileMenuOpen = false;

  async function handleLogout() {
    await logout();
    router.goToLogin();
  }

  function goToRsuSection(sectionId) {
    setRsuNavTarget(sectionId);
    router.goToRSU();
  }

  function toggleMobileMenu() {
    isMobileMenuOpen = !isMobileMenuOpen;
  }

  function closeMobileMenu() {
    isMobileMenuOpen = false;
  }

  function handleNav(fn) {
    fn();
    closeMobileMenu();
  }

  $: unreadCount = $notifications.filter(n => !n.read).length;

  // Helper to match roles case-insensitively and partially (e.g. "Finance Officer" matches "Finance")
  function isRole(target) {
    if (!$user?.role) return false;
    const current = $user.role.toString().toUpperCase();
    const t = target.toString().toUpperCase();
    return current.includes(t);
  }
</script>

<div
  class="min-h-screen bg-gradient-to-br from-sky-100 via-white to-cyan-100 text-gray-900 flex"
>
  <!-- Desktop Sidebar -->
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

    <nav class="flex-1 space-y-4">
      {#if isRole("PI")}
        <!-- Grant Management Section -->
        <div>
          <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Grant Management</p>
          <div class="space-y-1">
            <button class="nav-btn" class:active={$router === "dashboard"} on:click={() => router.goToDashboard()}>
              <span class="flex items-center gap-2"><Icon name="dashboard" size={18} />Dashboard</span>
            </button>
            <button class="nav-btn" class:active={$router === "grants"} on:click={() => router.goToGrants()}>
              <span class="flex items-center gap-2"><Icon name="folder" size={18} />Grants</span>
            </button>
            <button class="nav-btn" class:active={$router === "milestones"} on:click={() => router.goToMilestones()}>
              <span class="flex items-center gap-2"><Icon name="mission" size={18} />Milestones</span>
            </button>
            <button class="nav-btn" class:active={$router === "assign-tasks"} on:click={() => router.goToAssignTasks()}>
              <span class="flex items-center gap-2"><Icon name="tasks" size={18} />Tasks</span>
            </button>
            <button class="nav-btn" class:active={$router === "review-deliverables"} on:click={() => router.goToReviewDeliverables()}>
              <span class="flex items-center gap-2"><Icon name="documentCheck" size={18} />Deliverables</span>
            </button>
          </div>
        </div>

        <!-- Financial Section -->
        <div>
          <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Financial</p>
          <div class="space-y-1">
            <button class="nav-btn" class:active={$router === "grant-budgets"} on:click={() => router.goToGrantBudgets()}>
              <span class="flex items-center gap-2"><Icon name="budget" size={18} />Budget</span>
            </button>
            <button class="nav-btn" class:active={$router === "expenses"} on:click={() => router.goToExpenses()}>
              <span class="flex items-center gap-2"><Icon name="receipt" size={18} />Expenses</span>
            </button>
            <button class="nav-btn" class:active={$router === "assets"} on:click={() => router.goToAssets()}>
              <span class="flex items-center gap-2"><Icon name="asset" size={18} />Assets</span>
            </button>
          </div>
        </div>

        <!-- Compliance Section -->
        <div>
          <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Compliance</p>
          <div class="space-y-1">
            <button class="nav-btn" class:active={$router === "effort"} on:click={() => router.goToEffort()}>
              <span class="flex items-center gap-2"><Icon name="audit" size={18} />Effort Certification</span>
            </button>
            <button class="nav-btn" class:active={$router === "pi-ethics"} on:click={() => router.goToPIEthics()}>
              <span class="flex items-center gap-2"><Icon name="compliance" size={18} />Ethics Hub</span>
            </button>
            <button class="nav-btn" class:active={$router === "audit-trail"} on:click={() => router.goToAuditTrail()}>
              <span class="flex items-center gap-2"><Icon name="audit" size={18} />Audit Trail</span>
            </button>
            <button class="nav-btn" class:active={$router === "reports"} on:click={() => router.goToReports()}>
              <span class="flex items-center gap-2"><Icon name="reports" size={18} />Reports</span>
            </button>
          </div>
        </div>

        <!-- Admin Section -->
        <div>
          <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Admin</p>
          <div class="space-y-1">
            <button class="nav-btn" class:active={$router === "team"} on:click={() => router.goToTeam()}>
              <span class="flex items-center gap-2"><Icon name="users" size={18} />Team</span>
            </button>
            <button class="nav-btn" class:active={$router === "notifications"} on:click={() => router.goToNotifications()}>
              <span class="flex items-center justify-between w-full">
                <span class="flex items-center gap-2"><Icon name="warning" size={18} />Notifications</span>
                {#if unreadCount > 0}
                  <span class="px-1.5 py-0.5 bg-red-500 text-white text-[9px] font-black rounded-lg shadow-sm animate-pulse">
                    {unreadCount}
                  </span>
                {/if}
              </span>
            </button>
            <button class="nav-btn" class:active={$router === "documents"} on:click={() => router.goToDocuments()}>
              <span class="flex items-center gap-2"><Icon name="document" size={18} />Documents</span>
            </button>
          </div>
        </div>
      {:else if isRole("Team") || isRole("Researcher")}
        <!-- Team Member Sections -->
        <div>
          <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Work & Flow</p>
          <div class="space-y-1">
            <button class="nav-btn" class:active={$router === "dashboard"} on:click={() => router.goToDashboard()}>
              <span class="flex items-center gap-2"><Icon name="dashboard" size={18} />Dashboard</span>
            </button>
            <button class="nav-btn" class:active={$router === "tasks"} on:click={() => router.goToTasks()}>
              <span class="flex items-center gap-2"><Icon name="document" size={18} />My Tasks</span>
            </button>
            <button class="nav-btn" class:active={$router === "notifications"} on:click={() => router.goToNotifications()}>
              <span class="flex items-center justify-between w-full">
                <span class="flex items-center gap-2"><Icon name="warning" size={18} />Notifications</span>
                {#if unreadCount > 0}
                  <span class="px-1.5 py-0.5 bg-red-500 text-white text-[9px] font-black rounded-lg shadow-sm animate-pulse">
                    {unreadCount}
                  </span>
                {/if}
              </span>
            </button>
          </div>
        </div>
        <div>
          <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Planning</p>
          <div class="space-y-1">
            <button class="nav-btn" class:active={$router === "my-calendar"} on:click={() => router.goToMyCalendar()}>
              <span class="flex items-center gap-2"><Icon name="calendar" size={18} />My Calendar</span>
            </button>
            <button class="nav-btn" class:active={$router === "impact-report"} on:click={() => router.goToImpact()}>
              <span class="flex items-center gap-2"><Icon name="analytics" size={18} />My Impact</span>
            </button>
          </div>
        </div>
        <div>
          <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Equipment</p>
          <div class="space-y-1">
            <button class="nav-btn" class:active={$router === "my-inventory"} on:click={() => router.goToMyInventory()}>
              <span class="flex items-center gap-2"><Icon name="asset" size={18} />My Inventory</span>
            </button>
          </div>
        </div>
        <div>
          <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Compliance</p>
          <div class="space-y-1">
            <button class="nav-btn" class:active={$router === "effort"} on:click={() => router.goToEffort()}>
              <span class="flex items-center gap-2"><Icon name="audit" size={18} />Effort Certification</span>
            </button>
            <button class="nav-btn" class:active={$router === "audit-trail"} on:click={() => router.goToAuditTrail()}>
              <span class="flex items-center gap-2"><Icon name="audit" size={18} />Audit Trail</span>
            </button>
          </div>
        </div>
        <div>
          <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Documents</p>
          <div class="space-y-1">
            <button class="nav-btn" class:active={$router === "documents"} on:click={() => router.goToDocuments()}>
              <span class="flex items-center gap-2"><Icon name="document" size={18} />My Documents</span>
            </button>
          </div>
        </div>
      {:else if isRole("Finance")}
         <div>
          <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Pipeline</p>
          <div class="space-y-1">
            <button class="nav-btn" class:active={$router === "dashboard"} on:click={() => router.goToDashboard()}>
              <span class="flex items-center gap-2"><Icon name="dashboard" size={18} />Dashboard</span>
            </button>
            <button class="nav-btn" class:active={$router === "decision-center"} on:click={() => router.goToDecisionCenter()}>
              <span class="flex items-center gap-2"><Icon name="approvals" size={18} />Decision Center</span>
            </button>
            <button class="nav-btn" class:active={$router === "pending-expenses"} on:click={() => router.goToPendingExpenses()}>
              <span class="flex items-center gap-2"><Icon name="money" size={18} />Disbursements</span>
            </button>
          </div>
        </div>
        <div>
          <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Reports & FX</p>
          <div class="space-y-1">
            <button class="nav-btn" class:active={$router === "grant-budgets"} on:click={() => router.goToGrantBudgets()}>
              <span class="flex items-center gap-2"><Icon name="budget" size={18} />Grant Budgets</span>
            </button>
            <button class="nav-btn" class:active={$router === "exchange-rates"} on:click={() => router.goToExchangeRates()}>
              <span class="flex items-center gap-2"><Icon name="exchange" size={18} />Exchange Rates</span>
            </button>
            <button class="nav-btn" class:active={$router === "financial-reports"} on:click={() => router.goToFinancialReports()}>
              <span class="flex items-center gap-2"><Icon name="reports" size={18} />Financial Reports</span>
            </button>
          </div>
        </div>
        <div>
          <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Inbound</p>
          <div class="space-y-1">
            <button class="nav-btn" class:active={$router === "notifications"} on:click={() => router.goToNotifications()}>
              <span class="flex items-center justify-between w-full">
                <span class="flex items-center gap-2"><Icon name="warning" size={18} />Notifications</span>
                {#if unreadCount > 0}
                  <span class="px-1.5 py-0.5 bg-red-500 text-white text-[9px] font-black rounded-lg shadow-sm animate-pulse">
                    {unreadCount}
                  </span>
                {/if}
              </span>
            </button>
            <button class="nav-btn" class:active={$router === "documents"} on:click={() => router.goToDocuments()}>
              <span class="flex items-center gap-2"><Icon name="document" size={18} />Documents</span>
            </button>
          </div>
        </div>
      {:else if isRole("RSU")}
        <div>
          <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Mission Control</p>
          <div class="space-y-1">
            <button class="nav-btn" class:active={$router === "rsu"} on:click={() => router.goToRSU()}>
              <span class="flex items-center gap-2"><Icon name="mission" size={18} />Mission Control</span>
            </button>
            <button class="nav-btn" class:active={$router === "decision-center"} on:click={() => router.goToDecisionCenter()}>
              <span class="flex items-center gap-2"><Icon name="approvals" size={18} />Decision Center</span>
            </button>
            <button class="nav-btn" class:active={$router === "review-deliverables"} on:click={() => router.goToReviewDeliverables()}>
              <span class="flex items-center gap-2"><Icon name="documentCheck" size={18} />Deliverables</span>
            </button>
            <button class="nav-btn" class:active={$router === "grants"} on:click={() => router.goToGrants()}>
              <span class="flex items-center gap-2"><Icon name="folder" size={18} />All Grants</span>
            </button>
            <button class="nav-btn" class:active={$router === "rec"} on:click={() => router.goToREC()}>
              <span class="flex items-center gap-2"><Icon name="compliance" size={18} />REC Management</span>
            </button>
          </div>
        </div>
        <div>
          <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Governance</p>
          <div class="space-y-1">
            <button class="nav-btn" class:active={$router === "rules-management"} on:click={() => router.goToRulesManagement()}>
              <span class="flex items-center gap-2"><Icon name="setting" size={18} />Rules Engine</span>
            </button>
            <button class="nav-btn" class:active={$router === "notifications"} on:click={() => router.goToNotifications()}>
              <span class="flex items-center justify-between w-full">
                <span class="flex items-center gap-2"><Icon name="warning" size={18} />Notifications</span>
                {#if unreadCount > 0}
                  <span class="px-1.5 py-0.5 bg-red-500 text-white text-[9px] font-black rounded-lg shadow-sm animate-pulse">
                    {unreadCount}
                  </span>
                {/if}
              </span>
            </button>
            <button class="nav-btn" class:active={$router === "documents"} on:click={() => router.goToDocuments()}>
              <span class="flex items-center gap-2"><Icon name="document" size={18} />Documents</span>
            </button>
          </div>
        </div>
      {/if}
    </nav>

    <div class="mt-auto space-y-2">
      <div class="rounded-xl bg-gray-100/80 p-3">
        <p class="text-xs text-gray-500">Signed in as</p>
        <p class="font-semibold text-gray-900">{$user?.name || "User"}</p>
        <p class="text-xs text-gray-600 truncate">{$user?.email || ""}</p>
      </div>
      <button
        class="w-full px-4 py-2 rounded-xl border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
        on:click={handleLogout}
      >
        Logout
      </button>
    </div>
  </aside>

  <!-- Mobile Menu Drawer -->
  {#if isMobileMenuOpen}
    <div 
      class="fixed inset-0 z-50 md:hidden bg-gray-900/50 backdrop-blur-sm"
      on:click={closeMobileMenu}
    ></div>
    <aside 
      class="fixed inset-y-0 left-0 z-50 w-72 bg-white flex flex-col p-6 shadow-2xl md:hidden border-r border-gray-100 animate-in slide-in-from-left duration-300"
    >
      <div class="flex items-center justify-between mb-8">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-lg">PAG</div>
          <p class="font-bold text-gray-900">Grant Manager</p>
        </div>
        <button on:click={closeMobileMenu} class="p-2 rounded-lg bg-gray-100 text-gray-500">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>
      
      <nav class="flex-1 space-y-4 overflow-y-auto pr-2">
        {#if isRole("PI")}
          <div>
            <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest">Grant Management</p>
            <div class="space-y-1">
              <button class="nav-btn" class:active={$router === "dashboard"} on:click={() => handleNav(router.goToDashboard)}>
                <span class="flex items-center gap-2"><Icon name="dashboard" size={18} />Dashboard</span>
              </button>
              <button class="nav-btn" class:active={$router === "grants"} on:click={() => handleNav(router.goToGrants)}>
                <span class="flex items-center gap-2"><Icon name="folder" size={18} />Grants</span>
              </button>
            </div>
          </div>
          <div>
            <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest">Financial & Alerts</p>
            <div class="space-y-1">
              <button class="nav-btn" class:active={$router === "grant-budgets"} on:click={() => handleNav(router.goToGrantBudgets)}>
                <span class="flex items-center gap-2"><Icon name="budget" size={18} />Budget</span>
              </button>
              <button class="nav-btn" class:active={$router === "notifications"} on:click={() => handleNav(router.goToNotifications)}>
                <span class="flex items-center justify-between w-full">
                  <span class="flex items-center gap-2"><Icon name="warning" size={18} />Notifications</span>
                  {#if unreadCount > 0}
                    <span class="px-2 py-0.5 bg-red-500 text-white text-[10px] font-black rounded-lg">
                      {unreadCount}
                    </span>
                  {/if}
                </span>
              </button>
            </div>
          </div>
        {:else if isRole("Team") || isRole("Researcher")}
          <div>
            <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest">Work & Sync</p>
            <div class="space-y-1">
              <button class="nav-btn" class:active={$router === "dashboard"} on:click={() => handleNav(router.goToDashboard)}>
                <span class="flex items-center gap-2"><Icon name="dashboard" size={18} />Dashboard</span>
              </button>
              <button class="nav-btn" class:active={$router === "tasks"} on:click={() => handleNav(router.goToTasks)}>
                <span class="flex items-center gap-2"><Icon name="document" size={18} />My Tasks</span>
              </button>
              <button class="nav-btn" class:active={$router === "notifications"} on:click={() => handleNav(router.goToNotifications)}>
                <span class="flex items-center justify-between w-full">
                  <span class="flex items-center gap-2"><Icon name="warning" size={18} />Notifications</span>
                  {#if unreadCount > 0}
                    <span class="px-2 py-0.5 bg-red-500 text-white text-[10px] font-black rounded-lg">
                      {unreadCount}
                    </span>
                  {/if}
                </span>
              </button>
            </div>
          </div>
        {:else if isRole("Finance")}
          <div>
            <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest">Pipeline & Operations</p>
            <div class="space-y-1">
              <button class="nav-btn" class:active={$router === "dashboard"} on:click={() => handleNav(router.goToDashboard)}>
                <span class="flex items-center gap-2"><Icon name="dashboard" size={18} />Dashboard</span>
              </button>
              <button class="nav-btn" class:active={$router === "pending-expenses"} on:click={() => handleNav(router.goToPendingExpenses)}>
                <span class="flex items-center gap-2"><Icon name="money" size={18} />Disbursements</span>
              </button>
            </div>
          </div>
          <div class="pt-2">
            <button class="nav-btn" class:active={$router === "notifications"} on:click={() => handleNav(router.goToNotifications)}>
              <span class="flex items-center justify-between w-full">
                <span class="flex items-center gap-2"><Icon name="warning" size={18} />Notifications</span>
                {#if unreadCount > 0}
                  <span class="px-2 py-0.5 bg-red-500 text-white text-[10px] font-black rounded-lg">{unreadCount}</span>
                {/if}
              </span>
            </button>
            <button class="nav-btn text-rose-600 mt-4" on:click={handleLogout}>Logout</button>
          </div>
        {:else if isRole("RSU")}
          <div>
            <p class="px-3 mb-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest">Governance & Control</p>
            <div class="space-y-1">
              <button class="nav-btn" class:active={$router === "rsu"} on:click={() => handleNav(router.goToRSU)}>
                <span class="flex items-center gap-2"><Icon name="mission" size={18} />Mission Control</span>
              </button>
              <button class="nav-btn" class:active={$router === "rsu-grants"} on:click={() => handleNav(router.goToRSUGrants)}>
                <span class="flex items-center gap-2"><Icon name="grant" size={18} />Master Grant List</span>
              </button>
              <button class="nav-btn" class:active={$router === "decision-center"} on:click={() => handleNav(router.goToDecisionCenter)}>
                <span class="flex items-center gap-2"><Icon name="approvals" size={18} />Decision Center</span>
              </button>
            </div>
          </div>
          <div class="pt-2">
             <button class="nav-btn" class:active={$router === "notifications"} on:click={() => handleNav(router.goToNotifications)}>
              <span class="flex items-center justify-between w-full">
                <span class="flex items-center gap-2"><Icon name="warning" size={18} />Notifications</span>
                {#if unreadCount > 0}
                  <span class="px-2 py-0.5 bg-red-500 text-white text-[10px] font-black rounded-lg">{unreadCount}</span>
                {/if}
              </span>
            </button>
            <button class="nav-btn text-rose-600 mt-4" on:click={handleLogout}>Logout</button>
          </div>
        {:else}
          <button class="nav-btn" on:click={() => handleNav(router.goToDashboard)}>Dashboard</button>
          <button class="nav-btn text-rose-600 mt-4" on:click={handleLogout}>Logout</button>
        {/if}
      </nav>
    </aside>
  {/if}

  <div class="flex-1 flex flex-col h-screen overflow-hidden">
    <header
      class="md:hidden flex items-center justify-between px-4 py-3 bg-white/70 backdrop-blur-xl border-b border-white/40 shadow-sm"
    >
      <button 
        on:click={toggleMobileMenu}
        class="h-10 w-10 flex items-center justify-center rounded-xl bg-gray-100 text-gray-600"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
      </button>
      
      <div class="flex items-center gap-2">
        <div class="h-8 w-8 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs">PAG</div>
        <p class="text-sm font-bold text-gray-900">Grant Manager</p>
      </div>
      
      <button
        class="h-10 w-10 flex items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm"
        on:click={() => router.goToDashboard()}
      >
        <Icon name="dashboard" size={20} />
      </button>
    </header>

    <main class="flex-1 overflow-y-auto p-4 md:p-8">
      <slot />
    </main>
  </div>
  <Toast />
  <Modal />
</div>

<style>
  .nav-btn {
    width: 100%;
    text-align: left;
    padding: 0.75rem 1rem;
    border-radius: 12px;
    color: #4b5563;
    background: transparent;
    border: 1px solid transparent;
    font-size: 0.875rem;
    font-weight: 500;
    transition: all 0.2s;
  }

  .nav-btn.active {
    background: #2563eb;
    color: white;
    box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.1);
  }

  .nav-btn:hover:not(.active) {
    background: rgba(59, 130, 246, 0.08);
    color: #2563eb;
  }
</style>
