<!-- components/AssetUtilizationMetrics.svelte -->
<script>
    export let grantId;
    export let dateRange = 'all'; // 'all', '30days', '90days', 'year'
    
    let metrics = {
        asset_utilization_rate: 0,
        asset_turnaround_time: 0,
        missing_asset_risk: 0,
        total_assignments: 0,
        returned_assignments: 0,
        tasks_with_assets: 0,
        total_tasks: 0
    };
    
    let loading = true;
    let error = null;
    
    import { onMount } from 'svelte';
    
    onMount(async () => {
        await loadMetrics();
    });
    
    async function loadMetrics() {
        loading = true;
        error = null;
        
        try {
            const response = await fetch(`/api/analytics/asset-utilization/${grantId}?range=${dateRange}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (response.ok) {
                metrics = await response.json();
            } else {
                error = 'Failed to load asset utilization metrics';
            }
        } catch (err) {
            error = 'Network error loading metrics';
            console.error('Metrics error:', err);
        } finally {
            loading = false;
        }
    }
    
    function getUtilizationColor(rate) {
        if (rate >= 80) return 'text-green-600';
        if (rate >= 60) return 'text-yellow-600';
        return 'text-red-600';
    }
    
    function getRiskColor(risk) {
        if (risk === 0) return 'text-green-600';
        if (risk <= 2) return 'text-yellow-600';
        return 'text-red-600';
    }
    
    function formatDays(days) {
        return `${days.toFixed(1)} days`;
    }
</script>

<div class="bg-white p-6 rounded-lg shadow">
    <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-semibold text-gray-900">Asset Utilization Metrics</h2>
        <select
            bind:value={dateRange}
            on:change={loadMetrics}
            class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
            <option value="all">All Time</option>
            <option value="30days">Last 30 Days</option>
            <option value="90days">Last 90 Days</option>
            <option value="year">Last Year</option>
        </select>
    </div>
    
    {#if loading}
        <div class="flex items-center justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span class="ml-3 text-gray-600">Loading metrics...</span>
        </div>
    {:else if error}
        <div class="text-center py-12">
            <div class="text-red-600">{error}</div>
            <button 
                on:click={loadMetrics}
                class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
                Retry
            </button>
        </div>
    {:else}
        <!-- Key Metrics Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <!-- Asset Utilization Rate -->
            <div class="bg-gray-50 p-6 rounded-lg">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                            <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h6a2 2 0 002-2zm-2 0v6a2 2 0 002 2h6a2 2 0 002-2V9a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2z"/>
                            </svg>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-500">Utilization Rate</p>
                        <p class="text-2xl font-semibold {getUtilizationColor(metrics.asset_utilization_rate)}">
                            {metrics.asset_utilization_rate}%
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- Asset Turnaround Time -->
            <div class="bg-gray-50 p-6 rounded-lg">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                            <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m0 0l-3-3m-3 3v4m0 0v4m0 0v4m9-3V9a3 3 0 00-3-3H9a3 3 0 00-3 3v12a3 3 0 003 3h12a3 3 0 003-3V9a3 3 0 00-3-3h-2zm-1 2a1 1 0 110-2H7a1 1 0 110 2v8a1 1 0 110 2h8a1 1 0 110-2V7a1 1 0 00-1-1z"/>
                            </svg>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-500">Avg Turnaround</p>
                        <p class="text-2xl font-semibold text-gray-900">
                            {formatDays(metrics.asset_turnaround_time)}
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- Missing Asset Risk -->
            <div class="bg-gray-50 p-6 rounded-lg">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                            <svg class="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h.138a2 2 0 002 2v12a2 2 0 01-2 2H9.938a2 2 0 01-2-2V7a2 2 0 012-2h6.124a2 2 0 002 2v12a2 2 0 002-2z"/>
                            </svg>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-500">Missing Assets</p>
                        <p class="text-2xl font-semibold {getRiskColor(metrics.missing_asset_risk)}">
                            {metrics.missing_asset_risk}
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- Total Assignments -->
            <div class="bg-gray-50 p-6 rounded-lg">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                            <svg class="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2h14a2 2 0 012 2z"/>
                            </svg>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-500">Total Assignments</p>
                        <p class="text-2xl font-semibold text-gray-900">
                            {metrics.total_assignments}
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Detailed Breakdown -->
        <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Tasks with Assets -->
            <div class="bg-white p-6 rounded-lg border border-gray-200">
                <h3 class="text-lg font-medium text-gray-900 mb-4">Task Coverage</h3>
                <div class="space-y-3">
                    <div class="flex justify-between items-center">
                        <span class="text-gray-600">Tasks with Assets:</span>
                        <span class="font-semibold text-gray-900">{metrics.tasks_with_assets}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-600">Total Tasks:</span>
                        <span class="font-semibold text-gray-900">{metrics.total_tasks}</span>
                    </div>
                    <div class="mt-2">
                        <div class="w-full bg-gray-200 rounded-full h-2">
                            <div 
                                class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                style="width: {metrics.total_tasks > 0 ? (metrics.tasks_with_assets / metrics.total_tasks * 100) : 0}%"
                            ></div>
                        </div>
                        <p class="text-xs text-gray-600 mt-1">
                            {metrics.total_tasks > 0 ? Math.round(metrics.tasks_with_assets / metrics.total_tasks * 100) : 0}% of tasks have assigned assets
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- Assignment Status -->
            <div class="bg-white p-6 rounded-lg border border-gray-200">
                <h3 class="text-lg font-medium text-gray-900 mb-4">Assignment Status</h3>
                <div class="space-y-3">
                    <div class="flex justify-between items-center">
                        <span class="text-gray-600">Returned:</span>
                        <span class="font-semibold text-green-600">{metrics.returned_assignments}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-600">Pending:</span>
                        <span class="font-semibold text-yellow-600">{metrics.total_assignments - metrics.returned_assignments}</span>
                    </div>
                    <div class="mt-2">
                        <div class="w-full bg-gray-200 rounded-full h-2">
                            <div 
                                class="bg-green-600 h-2 rounded-full transition-all duration-300"
                                style="width: {metrics.total_assignments > 0 ? (metrics.returned_assignments / metrics.total_assignments * 100) : 0}%"
                            ></div>
                        </div>
                        <p class="text-xs text-gray-600 mt-1">
                            {metrics.total_assignments > 0 ? Math.round(metrics.returned_assignments / metrics.total_assignments * 100) : 0}% of assignments completed
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Alert for Missing Assets -->
        {#if metrics.missing_asset_risk > 0}
            <div class="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
                <div class="flex items-center">
                    <svg class="w-5 h-5 text-red-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h.138a2 2 0 002 2v12a2 2 0 01-2 2H9.938a2 2 0 01-2-2V7a2 2 0 012-2h6.124a2 2 0 002 2v12a2 2 0 002-2z"/>
                    </svg>
                    <div class="ml-3">
                        <h4 class="text-red-800 font-medium">Missing Asset Alert</h4>
                        <p class="mt-1 text-red-700">
                            {metrics.missing_asset_risk} asset(s) have not been returned and are considered missing. 
                            Please contact the assigned team members to ensure equipment is returned.
                        </p>
                    </div>
                </div>
            </div>
        {/if}
    {/if}
</div>
