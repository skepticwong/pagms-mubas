<script>
  export let intelligence = null;
  export let currency = 'USD';

  function displayAmount(value) {
    const amount = currency === 'USD' ? value : value * 1705;
    const prefix = currency === 'USD' ? '$' : 'MK ';
    if (isNaN(amount)) return `${prefix}0`;
    return prefix + amount.toLocaleString(undefined, { maximumFractionDigits: 0 });
  }

  function getStatusColor(status) {
    switch (status) {
      case 'ON_TRACK':
      case 'HEALTHY':
        return 'text-emerald-600 bg-emerald-50 border-emerald-100';
      case 'UNDER_SPENDING':
      case 'TIGHT':
        return 'text-amber-600 bg-amber-50 border-amber-100';
      case 'OVER_SPENDING':
      case 'DEFICIT':
        return 'text-red-600 bg-red-50 border-red-100';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-100';
    }
  }

  $: burn = intelligence?.burn_rate || {};
  $: health = intelligence?.health || {};
  $: proj = intelligence?.projected_completion || {};
  
  $: healthScore = health?.health_score || 0;
  $: scoreColor = healthScore > 80 ? 'text-emerald-600' : healthScore > 50 ? 'text-amber-600' : 'text-red-600';
</script>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
  <!-- Main Health Score & Status -->
  <div class="bg-white rounded-3xl border border-gray-100 p-6 shadow-sm flex flex-col justify-between">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-bold text-gray-400 uppercase tracking-widest">Financial Health</h3>
      <span class={`px-3 py-1 rounded-full text-[10px] font-black border ${getStatusColor(health.forecast?.forecast_status)}`}>
        {health.forecast?.forecast_status || 'ANALYZING'}
      </span>
    </div>
    
    <div class="py-6 text-center">
      <div class="relative inline-flex items-center justify-center">
        <svg class="w-32 h-32 transform -rotate-90">
          <circle
            cx="64"
            cy="64"
            r="58"
            stroke="currentColor"
            stroke-width="12"
            fill="transparent"
            class="text-gray-100"
          />
          <circle
            cx="64"
            cy="64"
            r="58"
            stroke="currentColor"
            stroke-width="12"
            fill="transparent"
            stroke-dasharray="364.4"
            stroke-dashoffset={364.4 - (364.4 * healthScore) / 100}
            stroke-linecap="round"
            class={scoreColor}
          />
        </svg>
        <div class="absolute flex flex-col items-center">
          <span class={`text-4xl font-black ${scoreColor}`}>{healthScore}</span>
          <span class="text-[10px] text-gray-400 font-bold uppercase tracking-tighter">Score</span>
        </div>
      </div>
    </div>

    <div class="space-y-4">
      <div class="flex justify-between items-end">
        <div>
          <p class="text-[10px] text-gray-400 font-bold uppercase">Spending Pace</p>
          <p class="text-lg font-black text-gray-900">
            {burn.burn_rate_variance > 0 ? '+' : ''}{burn.burn_rate_variance}%
          </p>
        </div>
        <p class={`text-xs font-bold ${getStatusColor(burn.burn_rate_status).split(' ')[0]}`}>
          {burn.burn_rate_status?.replace('_', ' ')}
        </p>
      </div>
      <div class="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
        <div 
          class={`h-full transition-all duration-1000 ${burn.burn_rate_variance > 15 ? 'bg-red-500' : burn.burn_rate_variance < -15 ? 'bg-amber-500' : 'bg-emerald-500'}`} 
          style={`width: ${Math.min(100, Math.max(0, 50 + (burn.burn_rate_variance || 0)))}%`}
        ></div>
      </div>
    </div>
  </div>

  <!-- Forecasting & Runway -->
  <div class="bg-gray-900 rounded-3xl p-6 text-white shadow-xl flex flex-col justify-between">
    <div>
      <h3 class="text-sm font-bold text-gray-500 uppercase tracking-widest">Projection Hub</h3>
      <div class="mt-6 space-y-6">
        <div>
          <p class="text-xs text-gray-400 font-medium">Estimated Runway</p>
          <div class="flex items-baseline gap-2">
            <span class="text-5xl font-black">{proj.months_remaining || '—'}</span>
            <span class="text-sm text-gray-400 font-bold uppercase">Months</span>
          </div>
          <p class="text-[10px] text-emerald-400 font-bold mt-1 uppercase tracking-wider">
            {proj.confidence || 'LOW'} Confidence Estimate
          </p>
        </div>

        <div class="p-4 bg-white/5 rounded-2xl border border-white/10">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
              <svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            </div>
            <div>
              <p class="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Forecast Finish</p>
              <p class="text-sm font-bold">{proj.projected_completion === 'UNKNOWN' ? 'Incalculable' : 'Budget Exhaustion ' + proj.projected_completion}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="pt-6 border-t border-white/10 flex items-center justify-between">
      <div class="flex flex-col">
        <span class="text-[9px] text-gray-500 font-black uppercase tracking-tighter">Current Rate</span>
        <span class="text-xs font-bold text-gray-300">{proj.spending_rate || 0}x Timeline</span>
      </div>
      <div class="flex flex-col text-right">
        <span class="text-[9px] text-gray-500 font-black uppercase tracking-tighter">Utilization</span>
        <span class="text-xs font-bold text-gray-300">{health.utilization_rate || 0}%</span>
      </div>
    </div>
  </div>

  <!-- Smart Advice / Recommendations -->
  <div class="bg-white rounded-3xl border border-gray-100 p-6 shadow-sm overflow-hidden relative">
    <div class="absolute top-0 right-0 p-8 transform translate-x-4 -translate-y-4 opacity-5">
      <svg class="w-32 h-32" fill="currentColor" viewBox="0 0 24 24"><path d="M13 2L3 14h9v8l10-12h-9l10-10z"/></svg>
    </div>

    <h3 class="text-sm font-bold text-gray-400 uppercase tracking-widest mb-6">Actionable Insights</h3>
    
    <div class="space-y-4 overflow-y-auto max-h-[300px] pr-2">
      {#if health.recommendations && health.recommendations.length > 0}
        {#each health.recommendations as rec}
          <div class={`p-4 rounded-2xl border ${
            rec.type === 'CRITICAL' ? 'bg-red-50 border-red-100' : 
            rec.type === 'WARNING' ? 'bg-amber-50 border-amber-100' : 'bg-blue-50 border-blue-100'
          }`}>
            <div class="flex items-start gap-3">
              <span class="mt-0.5">
                {#if rec.type === 'CRITICAL'}
                  <svg class="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                {:else if rec.type === 'WARNING'}
                  <svg class="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                {:else}
                  <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                {/if}
              </span>
              <div>
                <p class={`text-xs font-black uppercase tracking-tight ${
                  rec.type === 'CRITICAL' ? 'text-red-700' : 
                  rec.type === 'WARNING' ? 'text-amber-700' : 'text-blue-700'
                }`}>{rec.title}</p>
                <p class="text-[11px] text-gray-600 font-medium mt-0.5 leading-relaxed">{rec.message}</p>
                <p class="text-[10px] text-gray-500 italic mt-2 border-t border-black/5 pt-2">
                  <span class="font-bold uppercase tracking-tighter text-[8px] not-italic mr-1">Tactic:</span> {rec.action}
                </p>
              </div>
            </div>
          </div>
        {/each}
      {:else}
        <div class="text-center py-12">
          <p class="text-xs text-gray-400 font-bold uppercase">No Alerts Generated</p>
        </div>
      {/if}
    </div>
  </div>
</div>

<div class="mt-4 flex items-center gap-2 px-4 py-2 bg-amber-50 text-amber-700 rounded-xl border border-amber-100">
  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
  <p class="text-[10px] font-bold">DISCLAIMER: Projections are based on current data patterns and are for planning purposes only.</p>
</div>

<style>
  /* Custom transition for gauge */
  circle {
    transition: stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1);
  }
</style>
