// src/stores/router.js
import { writable } from 'svelte/store';

const roleLanding = {
  PI: 'dashboard',
  TEAM: 'tasks',
  FINANCE: 'pending-expenses',
  RSU: 'rsu'
};

function resolveLanding(role) {
  if (!role) return 'login';
  const normalized = role.toString().trim().toUpperCase();
  return roleLanding[normalized] || 'dashboard';
}

// Start at login — auth will redirect after real login
const { subscribe, set } = writable('login');

export const router = {
  subscribe,
  navigate: (page) => set(page),
  goToLogin: () => {

    set('login');
  },
  goToRegister: () => set('register'),
  goToDashboard: () => set('dashboard'),
  goToCreateGrant: () => set('create-grant'),
  goToMyGrants: () => set('grants'),
  goToGrants: () => set('grants'),
  goToTasks: () => set('tasks'),
  goToExpenses: () => set('expenses'),
  goToAssets: () => set('assets'),
  goToEffort: () => set('effort'),
  goToReports: () => set('reports'),
  goToNotifications: () => set('notifications'),
  goToPayments: () => set('payments'),
  goToPendingExpenses: () => set('pending-expenses'),
  goToGrantBudgets: () => set('grant-budgets'),
  goToApprovedTransactions: () => set('approved-transactions'),
  goToExchangeRates: () => set('exchange-rates'),
  goToFinancialReports: () => set('financial-reports'),
  goToBudget: () => set('budget'),
  goToCreateTask: () => set('assign-tasks'), // PI task assignment page
  goToAssignTasks: () => set('assign-tasks'),
  goToTeam: () => set('team'),
  goToReviewDeliverables: () => set('review-deliverables'),
  goToAuditTrail: () => set('audit-trail'),
  goToRSUGrants: () => set('rsu-grants'),
  goToRSU: () => set('rsu'),
  goToRulesManagement: () => set('rules-management'),
  goToDocuments: () => set('documents'),
  goToMilestones: () => set('milestones'),
  goToDecisionCenter: () => set('decision-center'),
  goToCloseoutWizard: () => set('closeout-wizard'),
  goToMyCalendar: () => set('my-calendar'),
  goToMyInventory: () => set('my-inventory'),
  goToImpact: () => set('impact-report'),
  goToREC: () => set('rec'),
  goToPIEthics: () => set('pi-ethics'),
  goToRoleHome: (role) => set(resolveLanding(role))
};

export { resolveLanding };