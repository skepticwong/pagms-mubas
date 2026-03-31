<script>
  import { onMount } from 'svelte';
  import { showToast } from '../stores/toast.js';

  let systemOverview = null;
  let burnRateSummary = null;
  let forecastSummary = null;
  let criticalGrants = [];
  let alerts = [];
  let loading = true;
  let error = null;
  let selectedTab = 'overview';

  onMount(async () => {
    await loadSystemData();
  });

  async function loadSystemData() {
    loading = true;
    error = null;

    try {
      const response = await fetch('/api/rules/system-financial-overview', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });

      if (response.ok) {
        const data = await response.json();
        systemOverview = data;
        burnRateSummary = data.burn_rate_summary;
        forecastSummary = data.forecast_summary;
        criticalGrants = data.critical_grants || [];
        alerts = data.alerts || [];
      } else {
        error = 'Failed to load system financial overview';
      }
    } catch (err) {
      error = 'Network error loading system data';
      console.error('System overview error:', err);
    } finally {
      loading = false;
    }
  }

  async function refreshData() {
    await loadSystemData();
    showToast('System data refreshed');
  }

  function getStatusColor(status) {
    switch (status) {
      case 'HEALTHY': return 'text-green-600 bg-green-100';
      case 'TIGHT': return 'text-yellow-600 bg-yellow-100';
      case 'DEFICIT': return 'text-red-600 bg-red-100';
      case 'ON_TRACK': return 'text-green-600 bg-green-100';
      case 'OVER_SPENDING': return 'text-red-600 bg-red-100';
      case 'UNDER_SPENDING': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  }

  function getAlertColor(type) {
    switch (type) {
      case 'CRITICAL': return 'border-red-500 bg-red-50';
      case 'WARNING': return 'border-yellow-500 bg-yellow-50';
      case 'SYSTEM': return 'border-blue-500 bg-blue-50';
      default: return 'border-gray-500 bg-gray-50';
    }
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount || 0);
  }

  function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
  }
</script>

<div class="rsu-financial-overview">
  <div class="flex justify-between items-center mb-6">
    <h1 class="text-3xl font-bold text-gray-900">Financial Overview</h1>
    <button
      on:click={refreshData}
      class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
      disabled={loading}
    >
      {#if loading}
        <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span class="ml-2">Refreshing...</span>
      {:else}
        Refresh Data
      {/if}
    </button>
  </div>

  {#if loading}
    <div class="text-center py-12">
      <svg class="animate-spin h-12 w-12 mx-auto text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="text-gray-500 mt-4">Loading system financial data...</p>
    </div>
  {:else if error}
    <div class="text-center py-12">
      <div class="text-red-500 mb-4">
        <svg class="h-12 w-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
      </div>
      <p class="text-gray-500">{error}</p>
    </div>
  {:else}
    <!-- Tab Navigation -->
    <div class="border-b border-gray-200 mb-6">
      <nav class="-mb-px flex space-x-8">
        <button
          class="py-2 px-1 border-b-2 font-medium text-sm {
            selectedTab === 'overview' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }"
          on:click={() => selectedTab = 'overview'}
        >
          Overview
        </button>
        <button
          class="py-2 px-1 border-b-2 font-medium text-sm {
            selectedTab === 'burn-rate' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }"
          on:click={() => selectedTab = 'burn-rate'}
        >
          Burn Rate Analysis
        </button>
        <button
          class="py-2 px-1 border-b-2 font-medium text-sm {
            selectedTab === 'forecast' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }"
          on:click={() => selectedTab = 'forecast'}
        >
          Budget Forecasting
        </button>
        <button
          class="py-2 px-1 border-b-2 font-medium text-sm {
            selectedTab === 'alerts' 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }"
          on:click={() => selectedTab = 'alerts'}
        >
          Alerts ({alerts.length})
        </button>
      </nav>
    </div>

    <!-- Overview Tab -->
    {#if selectedTab === 'overview'}
      <div class="space-y-6">
        <!-- System Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <!-- Total Grants -->
          <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <div class="text-sm text-gray-600 mb-2">Total Active Grants</div>
            <div class="text-3xl font-bold text-gray-900">{burnRateSummary?.total_grants || 0}</div>
          </div>

          <!-- Critical Grants -->
          <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <div class="text-sm text-gray-600 mb-2">Critical Grants</div>
            <div class="text-3xl font-bold text-red-600">{criticalGrants.length}</div>
            <div class="text-xs text-red-600 mt-1">Requires attention</div>
          </div>

          <!-- Average Variance -->
          <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <div class="text-sm text-gray-600 mb-2">Average Burn Rate Variance</div>
            <div class="text-3xl font-bold {
              (burnRateSummary?.average_variance || 0) > 15 ? 'text-red-600' :
              (burnRateSummary?.average_variance || 0) < -15 ? 'text-yellow-600' :
              'text-green-600'
            }">
              {burnRateSummary?.average_variance > 0 ? '+' : ''}{burnRateSummary?.average_variance || 0}%
            </div>
          </div>

          <!-- System Health -->
          <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <div class="text-sm text-gray-600 mb-2">System Health</div>
            <div class="text-3xl font-bold {
              criticalGrants.length > 5 ? 'text-red-600' :
              criticalGrants.length > 2 ? 'text-yellow-600' :
              'text-green-600'
            }">
              {criticalGrants.length > 5 ? 'Critical' : criticalGrants.length > 2 ? 'Warning' : 'Healthy'}
            </div>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Burn Rate Status Distribution -->
          <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Burn Rate Status</h3>
            <div class="space-y-3">
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">On Track</span>
                <span class="font-medium text-green-600">{burnRateSummary?.on_track || 0}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Over-spending</span>
                <span class="font-medium text-red-600">{burnRateSummary?.over_spending || 0}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Under-spending</span>
                <span class="font-medium text-yellow-600">{burnRateSummary?.under_spending || 0}</span>
              </div>
            </div>
          </div>

          <!-- Forecast Status Distribution -->
          <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Budget Forecast Status</h3>
            <div class="space-y-3">
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Healthy</span>
                <span class="font-medium text-green-600">{forecastSummary?.healthy || 0}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Tight</span>
                <span class="font-medium text-yellow-600">{forecastSummary?.tight || 0}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Deficit</span>
                <span class="font-medium text-red-600">{forecastSummary?.deficit || 0}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Critical Grants Preview -->
        {#if criticalGrants.length > 0}
          <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Critical Grants Requiring Attention</h3>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Grant</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issue</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  {#each criticalGrants.slice(0, 5) as grant}
                    <tr>
                      <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {grant.grant_title}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full {getStatusColor(grant.status)}">
                          {grant.status?.replace('_', ' ') || 'UNKNOWN'}
                        </span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {grant.variance ? `${grant.variance > 0 ? '+' : ''}${grant.variance.toFixed(1)}%` : 
                         grant.risk_score ? `${grant.risk_score}/100` : 'N/A'}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button class="text-blue-600 hover:text-blue-900">View Details</button>
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
              {#if criticalGrants.length > 5}
                <div class="text-center py-3 border-t">
                  <button class="text-blue-600 hover:text-blue-900 text-sm font-medium">
                    View all {criticalGrants.length} critical grants
                  </button>
                </div>
              {/if}
            </div>
          </div>
        {/if}
      </div>
    {/if}

    <!-- Burn Rate Tab -->
    {#if selectedTab === 'burn-rate'}
      <div class="space-y-6">
        <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">System Burn Rate Analysis</h3>
          
          {#if burnRateSummary}
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div class="text-center">
                <div class="text-3xl font-bold text-blue-600">{burnRateSummary.over_spending}</div>
                <div class="text-sm text-gray-600 mt-1">Over-spending Grants</div>
              </div>
              <div class="text-center">
                <div class="text-3xl font-bold text-yellow-600">{burnRateSummary.under_spending}</div>
                <div class="text-sm text-gray-600 mt-1">Under-spending Grants</div>
              </div>
              <div class="text-center">
                <div class="text-3xl font-bold text-green-600">{burnRateSummary.on_track}</div>
                <div class="text-sm text-gray-600 mt-1">On-track Grants</div>
              </div>
            </div>

            <div class="mt-6 pt-6 border-t">
              <div class="text-sm text-gray-600">
                <strong>Average Variance:</strong> 
                <span class="font-medium {
                  (burnRateSummary.average_variance || 0) > 15 ? 'text-red-600' :
                  (burnRateSummary.average_variance || 0) < -15 ? 'text-yellow-600' :
                  'text-green-600'
                }">
                  {burnRateSummary.average_variance > 0 ? '+' : ''}{burnRateSummary.average_variance || 0}%
                </span>
              </div>
              <div class="text-sm text-gray-600 mt-2">
                <strong>Last Updated:</strong> {formatDate(systemOverview.overview_generated_at)}
              </div>
            </div>
          {/if}
        </div>

        <!-- Critical Grants by Burn Rate -->
        {#if criticalGrants.filter(g => g.critical_type === 'BURN_RATE').length > 0}
          <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Burn Rate Critical Issues</h3>
            <div class="space-y-3">
              {#each criticalGrants.filter(g => g.critical_type === 'BURN_RATE') as grant}
                <div class="p-4 border-l-4 border-red-500 bg-red-50">
                  <div class="flex justify-between items-start">
                    <div>
                      <h4 class="font-medium text-gray-900">{grant.grant_title}</h4>
                      <p class="text-sm text-gray-600 mt-1">
                        Variance: {grant.variance > 0 ? '+' : ''}{grant.variance.toFixed(1)}%
                      </p>
                      <p class="text-sm text-gray-600">
                        Time: {grant.time_elapsed}% | Budget: {grant.budget_spent}%
                      </p>
                    </div>
                    <button class="text-blue-600 hover:text-blue-900 text-sm">Review</button>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/if}

    <!-- Forecast Tab -->
    {#if selectedTab === 'forecast'}
      <div class="space-y-6">
        <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Budget Forecast Summary</h3>
          
          {#if forecastSummary}
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div class="text-center">
                <div class="text-3xl font-bold text-green-600">{forecastSummary.healthy}</div>
                <div class="text-sm text-gray-600 mt-1">Healthy Grants</div>
              </div>
              <div class="text-center">
                <div class="text-3xl font-bold text-yellow-600">{forecastSummary.tight}</div>
                <div class="text-sm text-gray-600 mt-1">Tight Budget Grants</div>
              </div>
              <div class="text-center">
                <div class="text-3xl font-bold text-red-600">{forecastSummary.deficit}</div>
                <div class="text-sm text-gray-600 mt-1">Deficit Grants</div>
              </div>
            </div>

            <div class="mt-6 pt-6 border-t">
              <div class="text-sm text-gray-600">
                <strong>Total Projected Spend:</strong> 
                <span class="font-medium">{formatCurrency(forecastSummary.total_projected_spend)}</span>
              </div>
              <div class="text-sm text-gray-600 mt-2">
                <strong>Total Remaining Balance:</strong> 
                <span class="font-medium {forecastSummary.total_remaining_balance < 0 ? 'text-red-600' : 'text-green-600'}">
                  {formatCurrency(forecastSummary.total_remaining_balance)}
                </span>
              </div>
              <div class="text-sm text-gray-600 mt-2">
                <strong>Average Risk Score:</strong> 
                <span class="font-medium {
                  (forecastSummary.average_risk_score || 0) > 70 ? 'text-red-600' :
                  (forecastSummary.average_risk_score || 0) > 40 ? 'text-yellow-600' :
                  'text-green-600'
                }">
                  {forecastSummary.average_risk_score || 0}/100
                </span>
              </div>
            </div>
          {/if}
        </div>

        <!-- High Risk Grants by Forecast -->
        {#if criticalGrants.filter(g => g.critical_type === 'FORECAST_RISK').length > 0}
          <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">High Risk Forecast Issues</h3>
            <div class="space-y-3">
              {#each criticalGrants.filter(g => g.critical_type === 'FORECAST_RISK') as grant}
                <div class="p-4 border-l-4 border-red-500 bg-red-50">
                  <div class="flex justify-between items-start">
                    <div>
                      <h4 class="font-medium text-gray-900">{grant.grant_title}</h4>
                      <p class="text-sm text-gray-600 mt-1">
                        Risk Score: {grant.risk_score}/100
                      </p>
                      <p class="text-sm text-gray-600">
                        Projected Remaining: {formatCurrency(grant.projected_remaining)}
                      </p>
                      {#if grant.risk_factors?.length > 0}
                        <div class="mt-2">
                          <span class="text-xs text-gray-500">Risk Factors:</span>
                          <div class="flex flex-wrap gap-1 mt-1">
                            {#each grant.risk_factors as factor}
                              <span class="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                                {factor.replace('_', ' ')}
                              </span>
                            {/each}
                          </div>
                        </div>
                      {/if}
                    </div>
                    <button class="text-blue-600 hover:text-blue-900 text-sm">Review</button>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/if}

    <!-- Alerts Tab -->
    {#if selectedTab === 'alerts'}
      <div class="space-y-4">
        {#if alerts.length === 0}
          <div class="text-center py-12 bg-white rounded-lg border border-gray-200">
            <svg class="h-12 w-12 mx-auto text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <h3 class="mt-4 text-lg font-medium text-gray-900">No alerts</h3>
            <p class="mt-2 text-sm text-gray-500">All grants are performing within acceptable parameters.</p>
          </div>
        {:else}
          {#each alerts as alert}
            <div class="p-4 rounded-lg border-l-4 {getAlertColor(alert.type)}">
              <div class="flex">
                <div class="flex-shrink-0">
                  {#if alert.type === 'CRITICAL'}
                    <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                  {:else if alert.type === 'WARNING'}
                    <svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                    </svg>
                  {:else}
                    <svg class="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                    </svg>
                  {/if}
                </div>
                <div class="ml-3 flex-1">
                  <h4 class="text-sm font-medium text-gray-900">{alert.message}</h4>
                  <p class="text-sm text-gray-600 mt-1">
                    Grant: {alert.grant_title}
                  </p>
                  <p class="text-sm text-gray-500 mt-1">
                    Action Required: {alert.action_required}
                  </p>
                </div>
                <div class="ml-4">
                  <button class="text-blue-600 hover:text-blue-900 text-sm">View Grant</button>
                </div>
              </div>
            </div>
          {/each}
        {/if}
      </div>
    {/if}
  {/if}
</div>

<style>
  .rsu-financial-overview {
    padding: 1rem;
  }
  
  .rsu-financial-overview .grid {
    gap: 1.5rem;
  }
  
  .rsu-financial-overview .bg-white {
    transition: box-shadow 0.2s ease-in-out;
  }
  
  .rsu-financial-overview .bg-white:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  }
</style>
