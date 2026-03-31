<script>
  import { onMount } from 'svelte';
  import { showToast } from '../stores/toast.js';

  export let grantId = null;

  let burnRateData = null;
  let forecastData = null;
  let financialHealth = null;
  let loading = true;
  let error = null;

  onMount(async () => {
    if (grantId) {
      await loadFinancialData();
    }
  });

  async function loadFinancialData() {
    loading = true;
    error = null;

    try {
      // Load all financial data in parallel
      const [burnRateResponse, forecastResponse, healthResponse] = await Promise.all([
        fetch(`/api/rules/burn-rate/${grantId}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch(`/api/rules/forecast/${grantId}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch(`/api/rules/forecast/${grantId}/health`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
      ]);

      if (burnRateResponse.ok) {
        burnRateData = await burnRateResponse.json();
      }

      if (forecastResponse.ok) {
        forecastData = await forecastResponse.json();
      }

      if (healthResponse.ok) {
        financialHealth = await healthResponse.json();
      }

    } catch (err) {
      error = 'Failed to load financial data';
      console.error('Financial data error:', err);
    } finally {
      loading = false;
    }
  }

  async function refreshData() {
    await loadFinancialData();
    showToast('Financial data refreshed');
  }

  function getStatusColor(status) {
    switch (status) {
      case 'ON_TRACK': return 'text-green-600 bg-green-100';
      case 'OVER_SPENDING': return 'text-red-600 bg-red-100';
      case 'UNDER_SPENDING': return 'text-yellow-600 bg-yellow-100';
      case 'HEALTHY': return 'text-green-600 bg-green-100';
      case 'TIGHT': return 'text-yellow-600 bg-yellow-100';
      case 'DEFICIT': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  }

  function getRiskColor(score) {
    if (score >= 70) return 'text-red-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-green-600';
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount || 0);
  }
</script>

<div class="financial-metrics">
  <div class="flex justify-between items-center mb-6">
    <h2 class="text-2xl font-bold text-gray-900">Financial Health</h2>
    <button
      on:click={refreshData}
      class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
      disabled={loading}
    >
      {#if loading}
        <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      {:else}
        Refresh
      {/if}
    </button>
  </div>

  {#if loading}
    <div class="text-center py-8">
      <svg class="animate-spin h-8 w-8 mx-auto text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="text-gray-500 mt-2">Loading financial data...</p>
    </div>
  {:else if error}
    <div class="text-center py-8">
      <div class="text-red-500 mb-2">
        <svg class="h-8 w-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
      </div>
      <p class="text-gray-500">{error}</p>
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <!-- Burn Rate Card -->
      {#if burnRateData}
        <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Burn Rate Analysis</h3>
          
          <div class="space-y-4">
            <!-- Time vs Budget Progress -->
            <div>
              <div class="flex justify-between text-sm text-gray-600 mb-2">
                <span>Time Elapsed</span>
                <span>{burnRateData.burn_rate?.time_elapsed_percentage || 0}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div class="bg-blue-500 h-2 rounded-full" style="width: {burnRateData.burn_rate?.time_elapsed_percentage || 0}%"></div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-sm text-gray-600 mb-2">
                <span>Budget Spent</span>
                <span>{burnRateData.burn_rate?.budget_spent_percentage || 0}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div class="bg-red-500 h-2 rounded-full" style="width: {burnRateData.burn_rate?.budget_spent_percentage || 0}%"></div>
              </div>
            </div>

            <!-- Variance -->
            <div class="pt-2 border-t">
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Variance</span>
                <span class="text-sm font-medium">
                  {burnRateData.burn_rate?.burn_rate_variance > 0 ? '+' : ''}{burnRateData.burn_rate?.burn_rate_variance || 0}%
                </span>
              </div>
              <div class="mt-1">
                <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full {getStatusColor(burnRateData.burn_rate?.burn_rate_status)}">
                  {burnRateData.burn_rate?.burn_rate_status?.replace('_', ' ') || 'UNKNOWN'}
                </span>
              </div>
            </div>
          </div>
        </div>
      {/if}

      <!-- Forecast Card -->
      {#if forecastData}
        <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Budget Forecast</h3>
          
          <div class="space-y-4">
            <!-- Projected Remaining Balance -->
            <div>
              <div class="text-sm text-gray-600 mb-1">Projected Remaining Balance</div>
              <div class="text-2xl font-bold {getRiskColor(forecastData.forecast?.forecast_status)}">
                {formatCurrency(forecastData.forecast?.projected_remaining_balance)}
              </div>
              <div class="mt-1">
                <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full {getStatusColor(forecastData.forecast?.forecast_status)}">
                  {forecastData.forecast?.forecast_status || 'UNKNOWN'}
                </span>
              </div>
            </div>

            <!-- Projected Final Spend -->
            <div>
              <div class="text-sm text-gray-600 mb-1">Projected Final Spend</div>
              <div class="text-lg font-semibold text-gray-900">
                {formatCurrency(forecastData.forecast?.projected_final_spend)}
              </div>
            </div>

            <!-- Risk Score -->
            <div class="pt-2 border-t">
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Risk Score</span>
                <span class="text-sm font-medium {getRiskColor(forecastData.forecast?.risk_score)}">
                  {forecastData.forecast?.risk_score || 0}/100
                </span>
              </div>
            </div>
          </div>
        </div>
      {/if}

      <!-- Financial Health Card -->
      {#if financialHealth}
        <div class="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Health Indicators</h3>
          
          <div class="space-y-4">
            <!-- Health Score -->
            <div>
              <div class="text-sm text-gray-600 mb-1">Overall Health Score</div>
              <div class="text-2xl font-bold {getRiskColor(100 - (financialHealth.financial_health?.health_score || 0))}">
                {financialHealth.financial_health?.health_score || 0}/100
              </div>
            </div>

            <!-- Utilization Rate -->
            <div>
              <div class="text-sm text-gray-600 mb-1">Budget Utilization</div>
              <div class="text-lg font-semibold text-gray-900">
                {financialHealth.financial_health?.utilization_rate || 0}%
              </div>
            </div>

            <!-- Buffer Months -->
            <div>
              <div class="text-sm text-gray-600 mb-1">Financial Buffer</div>
              <div class="text-lg font-semibold text-gray-900">
                {financialHealth.financial_health?.buffer_months?.toFixed(1) || 0} months
              </div>
            </div>

            <!-- Stress Indicators -->
            {#if financialHealth.financial_health?.stress_indicators?.length > 0}
              <div class="pt-2 border-t">
                <div class="text-sm text-gray-600 mb-2">Stress Indicators</div>
                <div class="space-y-1">
                  {#each financialHealth.financial_health.stress_indicators as indicator}
                    <div class="text-xs text-yellow-600 bg-yellow-50 px-2 py-1 rounded">
                      {indicator.replace('_', ' ')}
                    </div>
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        </div>
      {/if}
    </div>

    <!-- Recommendations Section -->
    {#if financialHealth?.financial_health?.recommendations?.length > 0}
      <div class="mt-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Recommendations</h3>
        <div class="space-y-3">
          {#each financialHealth.financial_health.recommendations as recommendation}
            <div class="p-4 rounded-lg border-l-4 {
              recommendation.type === 'CRITICAL' ? 'border-red-500 bg-red-50' :
              recommendation.type === 'WARNING' ? 'border-yellow-500 bg-yellow-50' :
              recommendation.type === 'INFO' ? 'border-blue-500 bg-blue-50' :
              'border-green-500 bg-green-50'
            }">
              <div class="flex">
                <div class="flex-shrink-0">
                  {#if recommendation.type === 'CRITICAL'}
                    <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                  {:else if recommendation.type === 'WARNING'}
                    <svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                    </svg>
                  {:else}
                    <svg class="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                    </svg>
                  {/if}
                </div>
                <div class="ml-3">
                  <h4 class="text-sm font-medium text-gray-900">{recommendation.title}</h4>
                  <p class="text-sm text-gray-600 mt-1">{recommendation.message}</p>
                  {#if recommendation.action}
                    <p class="text-sm text-gray-500 mt-1">
                      <strong>Action:</strong> {recommendation.action}
                    </p>
                  {/if}
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  {/if}
</div>

<style>
  .financial-metrics {
    /* Component styles for financial metrics display */
  }
  
  .financial-metrics .grid {
    gap: 1.5rem;
  }
  
  .financial-metrics .bg-white {
    transition: box-shadow 0.2s ease-in-out;
  }
  
  .financial-metrics .bg-white:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  }
</style>
