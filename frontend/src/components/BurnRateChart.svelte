<script>
  import { onMount, createEventDispatcher } from 'svelte';

  export let grantId = null;
  export let height = 300;

  const dispatch = createEventDispatcher();

  let chartElement = null;
  let burnRateData = null;
  let loading = true;
  let error = null;

  onMount(async () => {
    if (grantId) {
      await loadBurnRateData();
      if (burnRateData) {
        renderChart();
      }
    }
  });

  async function loadBurnRateData() {
    loading = true;
    error = null;

    try {
      const response = await fetch(`/api/rules/burn-rate/${grantId}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });

      if (response.ok) {
        const result = await response.json();
        burnRateData = result.burn_rate;
      } else {
        error = 'Failed to load burn rate data';
      }
    } catch (err) {
      error = 'Network error loading burn rate data';
      console.error('Burn rate data error:', err);
    } finally {
      loading = false;
    }
  }

  function renderChart() {
    if (!chartElement || !burnRateData) return;

    const canvas = chartElement;
    const ctx = canvas.getContext('2d');

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const padding = 40;
    const chartWidth = canvas.width - padding * 2;
    const chartHeight = canvas.height - padding * 2;

    // Draw axes
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, canvas.height - padding);
    ctx.lineTo(canvas.width - padding, canvas.height - padding);
    ctx.stroke();

    // Draw grid lines
    ctx.strokeStyle = '#f3f4f6';
    ctx.setLineDash([5, 5]);
    
    // Horizontal grid lines
    for (let i = 0; i <= 4; i++) {
      const y = padding + (chartHeight / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(canvas.width - padding, y);
      ctx.stroke();
    }

    // Vertical grid lines
    for (let i = 0; i <= 10; i++) {
      const x = padding + (chartWidth / 10) * i;
      ctx.beginPath();
      ctx.moveTo(x, padding);
      ctx.lineTo(x, canvas.height - padding);
      ctx.stroke();
    }

    ctx.setLineDash([]);

    // Draw data
    const timeElapsed = burnRateData.time_elapsed_percentage || 0;
    const budgetSpent = burnRateData.budget_spent_percentage || 0;

    // Time progress bar (blue)
    const timeBarHeight = (timeElapsed / 100) * chartHeight;
    ctx.fillStyle = '#3b82f6';
    ctx.fillRect(
      padding + 20,
      canvas.height - padding - timeBarHeight,
      30,
      timeBarHeight
    );

    // Budget spent bar (red)
    const budgetBarHeight = (budgetSpent / 100) * chartHeight;
    ctx.fillStyle = '#ef4444';
    ctx.fillRect(
      padding + 60,
      canvas.height - padding - budgetBarHeight,
      30,
      budgetBarHeight
    );

    // Draw labels
    ctx.fillStyle = '#374151';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';

    // X-axis labels
    ctx.fillText('Time', padding + 35, canvas.height - padding + 20);
    ctx.fillText('Budget', padding + 75, canvas.height - padding + 20);

    // Y-axis labels
    ctx.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
      const value = (100 / 4) * (4 - i);
      const y = padding + (chartHeight / 4) * i;
      ctx.fillText(`${value}%`, padding - 10, y + 4);
    }

    // Draw values on bars
    ctx.textAlign = 'center';
    ctx.fillStyle = '#1f2937';
    ctx.font = 'bold 14px sans-serif';
    
    // Time value
    ctx.fillText(
      `${timeElapsed.toFixed(1)}%`,
      padding + 35,
      canvas.height - padding - timeBarHeight - 10
    );

    // Budget value
    ctx.fillText(
      `${budgetSpent.toFixed(1)}%`,
      padding + 75,
      canvas.height - padding - budgetBarHeight - 10
    );

    // Draw variance line
    const variance = burnRateData.burn_rate_variance || 0;
    if (Math.abs(variance) > 1) {
      ctx.strokeStyle = variance > 0 ? '#ef4444' : '#eab308';
      ctx.lineWidth = 2;
      ctx.setLineDash([]);
      
      const y1 = canvas.height - padding - timeBarHeight;
      const y2 = canvas.height - padding - budgetBarHeight;
      
      ctx.beginPath();
      ctx.moveTo(padding + 50, y1);
      ctx.lineTo(padding + 50, y2);
      ctx.stroke();

      // Draw variance arc
      const arcRadius = 15;
      const arcStart = Math.atan2(y1 - (canvas.height - padding - chartHeight/2), 0);
      const arcEnd = Math.atan2(y2 - (canvas.height - padding - chartHeight/2), 0);
      
      ctx.beginPath();
      ctx.arc(padding + 50, canvas.height - padding - chartHeight/2, arcRadius, arcStart, arcEnd);
      ctx.stroke();

      // Variance label
      ctx.fillStyle = variance > 0 ? '#ef4444' : '#eab308';
      ctx.font = '12px sans-serif';
      const varianceY = Math.min(y1, y2) - 20;
      ctx.fillText(
        `${variance > 0 ? '+' : ''}${variance.toFixed(1)}%`,
        padding + 50,
        varianceY
      );
    }

    // Draw status indicator
    const status = burnRateData.burn_rate_status || 'UNKNOWN';
    let statusColor;
    switch (status) {
      case 'ON_TRACK': statusColor = '#10b981'; break;
      case 'OVER_SPENDING': statusColor = '#ef4444'; break;
      case 'UNDER_SPENDING': statusColor = '#eab308'; break;
      default: statusColor = '#6b7280';
    }

    ctx.fillStyle = statusColor;
    ctx.font = 'bold 16px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(status.replace('_', ' '), padding + 110, canvas.height - padding - chartHeight/2);
  }

  function getStatusColor(status) {
    switch (status) {
      case 'ON_TRACK': return 'text-green-600';
      case 'OVER_SPENDING': return 'text-red-600';
      case 'UNDER_SPENDING': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  }
</script>

<div class="burn-rate-chart">
  <h3 class="text-lg font-semibold text-gray-900 mb-4">Burn Rate Analysis</h3>
  
  {#if loading}
    <div class="flex items-center justify-center h-64">
      <svg class="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span class="ml-2 text-gray-500">Loading burn rate data...</span>
    </div>
  {:else if error}
    <div class="flex items-center justify-center h-64 text-red-500">
      <svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
      </svg>
      <span class="ml-2">{error}</span>
    </div>
  {:else if burnRateData}
    <div class="space-y-4">
      <!-- Chart Canvas -->
      <div class="bg-white p-4 rounded-lg border border-gray-200">
        <canvas bind:this={chartElement} width={400} height={height}></canvas>
      </div>

      <!-- Legend -->
      <div class="flex justify-center space-x-6 text-sm">
        <div class="flex items-center">
          <div class="w-4 h-4 bg-blue-500 rounded mr-2"></div>
          <span>Time Elapsed ({burnRateData.time_elapsed_percentage || 0}%)</span>
        </div>
        <div class="flex items-center">
          <div class="w-4 h-4 bg-red-500 rounded mr-2"></div>
          <span>Budget Spent ({burnRateData.budget_spent_percentage || 0}%)</span>
        </div>
      </div>

      <!-- Status Indicator -->
      <div class="text-center">
        <span class="inline-flex px-3 py-1 text-sm font-medium rounded-full {
          burnRateData.burn_rate_status === 'ON_TRACK' ? 'text-green-600 bg-green-100' :
          burnRateData.burn_rate_status === 'OVER_SPENDING' ? 'text-red-600 bg-red-100' :
          burnRateData.burn_rate_status === 'UNDER_SPENDING' ? 'text-yellow-600 bg-yellow-100' :
          'text-gray-600 bg-gray-100'
        }">
          {burnRateData.burn_rate_status?.replace('_', ' ') || 'UNKNOWN'}
        </span>
      </div>

      <!-- Variance Display -->
      {#if burnRateData.burn_rate_variance !== 0}
        <div class="text-center">
          <div class="text-sm text-gray-600">
            Variance: 
            <span class="font-medium {
              burnRateData.burn_rate_variance > 0 ? 'text-red-600' : 'text-yellow-600'
            }">
              {burnRateData.burn_rate_variance > 0 ? '+' : ''}{burnRateData.burn_rate_variance.toFixed(1)}%
            </span>
          </div>
          <div class="text-xs text-gray-500 mt-1">
            {burnRateData.burn_rate_variance > 0 ? 'Spending faster than time' : 'Spending slower than time'}
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .burn-rate-chart canvas {
    max-width: 100%;
    height: auto;
  }
</style>
