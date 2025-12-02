<script>
  import { onMount } from "svelte";
  import { get } from "svelte/store";
  import { router } from "./stores/router.js";
  import { checkAuth, isAuthenticated, user } from "./stores/auth.js";
  import Login from "./pages/Login.svelte";
  import Register from "./pages/Register.svelte";
  import Dashboard from "./pages/Dashboard.svelte";
  import CreateGrant from "./pages/CreateGrant.svelte";
  import Grants from "./pages/Grants.svelte";
  import Tasks from "./pages/Tasks.svelte";
  import PIExpenses from "./pages/PIExpenses.svelte";
  import Effort from "./pages/Effort.svelte";
  import Reports from "./pages/Reports.svelte";
  import Notifications from "./pages/Notifications.svelte";
  import Team from "./pages/Team.svelte";
  import Payments from "./pages/Payments.svelte";
  import PendingExpenses from "./pages/PendingExpenses.svelte";
  import GrantBudgets from "./pages/GrantBudgets.svelte";
  import ApprovedTransactions from "./pages/ApprovedTransactions.svelte";
  import ExchangeRates from "./pages/ExchangeRates.svelte";
  import FinancialReports from "./pages/FinancialReports.svelte";
  import AuditTrail from "./pages/AuditTrail.svelte";
  import ReviewEvidence from "./pages/ReviewEvidence.svelte";
  import AssignTasks from "./pages/AssignTasks.svelte"; // Import the new component
  import Documents from "./pages/Documents.svelte";

  onMount(async () => {
    await checkAuth();
    if (get(isAuthenticated)) {
      const currentUser = get(user);
      if (router.goToRoleHome) {
        router.goToRoleHome(currentUser?.role);
      } else {
        router.goToDashboard();
      }
    }
  });
</script>

{#if $router === "login"}
  <Login />
{:else if $router === "register"}
  <Register />
{:else if $router === "dashboard"}
  <Dashboard />
{:else if $router === "create-grant"}
  <CreateGrant />
{:else if $router === "grants"}
  <!-- NEW -->
  <Grants />
{:else if $router === "tasks"}
  <Tasks />
{:else if $router === "assign-tasks"}
  <!-- Add this new conditional block -->
  <AssignTasks />
{:else if $router === "expenses"}
  <PIExpenses />
{:else if $router === "effort"}
  <Effort />
{:else if $router === "reports"}
  <Reports />
{:else if $router === "notifications"}
  <Notifications />
{:else if $router === "team"}
  <Team />
{:else if $router === "payments"}
  <Payments />
{:else if $router === "pending-expenses"}
  <PendingExpenses />
{:else if $router === "grant-budgets"}
  <GrantBudgets />
{:else if $router === "approved-transactions"}
  <ApprovedTransactions />
{:else if $router === "exchange-rates"}
  <ExchangeRates />
{:else if $router === "financial-reports"}
  <FinancialReports />
{:else if $router === "audit-trail"}
  <AuditTrail />
{:else if $router === "review-evidence"}
  <ReviewEvidence />
{:else if $router === "rsu"}
  <RSU />
{:else if $router === "documents"}
  <Documents />
{/if}
