<!-- frontend/src/components/ComplianceHealthWidget.svelte -->
<script>
  import { onMount } from 'svelte';
  import axios from 'axios';
  import Icon from './Icon.svelte';

  export let grantId;
  
  let health = {
    score: 100,
    risk_level: 'LOW',
    financial_risk: 0,
    operational_risk: 0,
    reporting_risk: 0,
    last_calculated: null
  };
  let loading = true;

  onMount(async () => {
    if (grantId) {
      try {
        const response = await axios.get(`http://localhost:5000/api/grants/${grantId}/health`, { withCredentials: true });
        health = response.data;
      } catch (err) {
        console.error("Failed to fetch health score", err);
      } finally {
        loading = false;
      }
    }
  });

  $: scoreColor = getScoreColor(health.score);
  $: riskLabel = health.risk_level || 'LOW';

  function getScoreColor(score) {
    if (score >= 80) return '#10b981'; // Emerald 500
    if (score >= 50) return '#f59e0b'; // Amber 500
    if (score >= 30) return '#f97316'; // Orange 500
    return '#ef4444'; // Red 500
  }

  function getBgColor(score) {
    if (score >= 80) return 'bg-emerald-50 border-emerald-200';
    if (score >= 50) return 'bg-amber-50 border-amber-200';
    if (score >= 30) return 'bg-orange-50 border-orange-200';
    return 'bg-red-50 border-red-200';
  }

  $: dashArray = (health.score / 100) * 251.2; // 2 * PI * r (where r=40)
</script>

<div class="compliance-health-widget {getBgColor(health.score)} border rounded-2xl p-6 shadow-sm">
  <div class="flex items-center justify-between mb-6">
    <h3 class="text-gray-900 font-bold flex items-center gap-2 text-lg">
      <Icon name="compliance" size={24} /> Compliance Health
    </h3>
    {#if health.last_calculated}
      <span class="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">
        Last sync: {new Date(health.last_calculated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </span>
    {/if}
  </div>

  <div class="flex flex-col md:flex-row items-center gap-8">
    <!-- Gauge Chart -->
    <div class="relative w-32 h-32 flex items-center justify-center">
      <svg class="w-full h-full transform -rotate-90">
        <circle
          cx="64"
          cy="64"
          r="40"
          stroke="currentColor"
          stroke-width="12"
          fill="transparent"
          class="text-gray-200"
        />
        <circle
          cx="64"
          cy="64"
          r="40"
          stroke={scoreColor}
          stroke-width="12"
          stroke-dasharray="251.2"
          stroke-dashoffset={251.2 - dashArray}
          stroke-linecap="round"
          fill="transparent"
          class="transition-all duration-1000 ease-out"
        />
      </svg>
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <span class="text-3xl font-black text-gray-900 leading-none">{health.score}</span>
        <span class="text-[10px] font-bold text-gray-500 uppercase mt-1">Health index</span>
      </div>
    </div>

    <!-- Risk Breakdown -->
    <div class="flex-1 w-full flex flex-col justify-center">
      <div class="flex items-center gap-2 mb-4">
        <span class="px-3 py-1 rounded-full text-xs font-black uppercase tracking-widest text-white" style="background-color: {scoreColor}">
          {riskLabel} RISK
        </span>
        <span class="text-xs text-gray-600 font-medium italic">Forensic reliability: High</span>
      </div>

      <div class="space-y-3">
        <!-- Financial Risk -->
        <div class="space-y-1">
          <div class="flex justify-between text-[11px] font-bold text-gray-700 uppercase">
            <span>Financial Compliance</span>
            <span class={health.financial_risk > 0 ? 'text-red-600' : 'text-emerald-600'}>
               {health.financial_risk > 0 ? '-' + health.financial_risk : 'Secure'}
            </span>
          </div>
          <div class="h-1.5 w-full bg-gray-200 rounded-full overflow-hidden">
            <div class="h-full {health.financial_risk > 20 ? 'bg-red-500' : health.financial_risk > 0 ? 'bg-amber-500' : 'bg-emerald-500'}" style="width: {100 - health.financial_risk}%"></div>
          </div>
        </div>

        <!-- Operational Risk -->
        <div class="space-y-1">
          <div class="flex justify-between text-[11px] font-bold text-gray-700 uppercase">
            <span>Personnel & Scope</span>
            <span class={health.operational_risk > 0 ? 'text-red-600' : 'text-emerald-600'}>
               {health.operational_risk > 0 ? '-' + health.operational_risk : 'Secure'}
            </span>
          </div>
          <div class="h-1.5 w-full bg-gray-200 rounded-full overflow-hidden">
            <div class="h-full {health.operational_risk > 20 ? 'bg-red-500' : health.operational_risk > 0 ? 'bg-amber-500' : 'bg-emerald-500'}" style="width: {100 - health.operational_risk}%"></div>
          </div>
        </div>

        <!-- Reporting Risk -->
        <div class="space-y-1">
          <div class="flex justify-between text-[11px] font-bold text-gray-700 uppercase">
            <span>Reporting Integrity</span>
            <span class={health.reporting_risk > 0 ? 'text-red-600' : 'text-emerald-600'}>
               {health.reporting_risk > 0 ? '-' + health.reporting_risk : 'Secure'}
            </span>
          </div>
          <div class="h-1.5 w-full bg-gray-200 rounded-full overflow-hidden">
            <div class="h-full {health.reporting_risk > 20 ? 'bg-red-500' : health.reporting_risk > 0 ? 'bg-amber-500' : 'bg-emerald-500'}" style="width: {100 - health.reporting_risk}%"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .compliance-health-widget {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .compliance-health-widget:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
  }
</style>
