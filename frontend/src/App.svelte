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
  import Expenses from "./pages/Expenses.svelte";
  import Assets from "./pages/Assets.svelte";
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
  import ReviewDeliverables from "./pages/ReviewDeliverables.svelte";
  import AssignTasks from "./pages/AssignTasks.svelte"; // Import new component
  import Documents from "./pages/Documents.svelte";
  import RSU from "./pages/RSU.svelte";
  import RulesManagement from "./pages/RulesManagement.svelte";
  import RSUDecisionCenter from "./pages/RSUDecisionCenter.svelte";
import Milestones from "./pages/Milestones.svelte";
import CloseoutWizard from "./pages/CloseoutWizard.svelte";
import MyCalendar from "./pages/MyCalendar.svelte";
import MyInventory from "./pages/MyInventory.svelte";
import ImpactReport from "./pages/ImpactReport.svelte";
import RSUGrants from "./pages/RSUGrants.svelte";
import REC from "./pages/REC.svelte";
import PIEthics from "./pages/PIEthics.svelte";

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
{:else if $router === "assets"}
  <Assets />
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
{:else if $router === "budget"}
  <GrantBudgets />
{:else if $router === "approved-transactions"}
  <ApprovedTransactions />
{:else if $router === "exchange-rates"}
  <ExchangeRates />
{:else if $router === "financial-reports"}
  <FinancialReports />
{:else if $router === "audit-trail"}
  <AuditTrail />
{:else if $router === 'review-deliverables'}
  <ReviewDeliverables />
{:else if $router === "rsu"}
  <RSU />
{:else if $router === "rules-management"}
  <RulesManagement />
{:else if $router === "rsu-grants"}
  <RSUGrants />
{:else if $router === "documents"}
  <Documents />
{:else if $router === "decision-center"}
  <RSUDecisionCenter />
{:else if $router === "milestones"}
  <Milestones />
{:else if $router === "closeout-wizard"}
  <CloseoutWizard />
{:else if $router === "my-calendar"}
  <MyCalendar />
{:else if $router === "my-inventory"}
  <MyInventory />
{:else if $router === "impact-report"}
  <ImpactReport />
{:else if $router === "rec"}
  <REC />
{:else if $router === "pi-ethics"}
  <PIEthics />
{/if}
