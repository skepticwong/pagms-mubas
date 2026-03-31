<!-- KPI Management Modal for Milestones -->
<script>
    import { onMount } from 'svelte';
    import axios from 'axios';
    import { confirm } from '../stores/modals.js';
    import Icon from './Icon.svelte';

    export let show = false;
    export let milestoneId = null;
    export let milestone = null;
    export let onKPIUpdated = () => {};

    let kpis = [];
    let isLoading = false;
    let showAddKPI = false;
    let editingKPI = null;
    let newKPI = {
        name: '',
        description: '',
        target_value: '',
        unit: 'count'
    };

    // KPI templates for quick setup
    let kpiTemplates = [
        { name: 'Publications', description: 'Research papers published', unit: 'papers', target_value: 5 },
        { name: 'Students Trained', description: 'Number of students supervised', unit: 'students', target_value: 10 },
        { name: 'Workshops Conducted', description: 'Training workshops delivered', unit: 'sessions', target_value: 3 },
        { name: 'Equipment Procured', description: 'Research equipment purchased', unit: 'items', target_value: 2 },
        { name: 'Beneficiaries Reached', description: 'People directly impacted', unit: 'people', target_value: 100 }
    ];

    onMount(() => {
        if (show && milestoneId) {
            fetchKPIs();
        }
    });

    async function fetchKPIs() {
        isLoading = true;
        try {
            const response = await axios.get(`http://localhost:5000/api/milestone-kpis/milestone/${milestoneId}`, {
                withCredentials: true
            });
            kpis = response.data.kpis || [];
        } catch (error) {
            console.error('Failed to fetch KPIs:', error);
        } finally {
            isLoading = false;
        }
    }

    async function addKPI() {
        if (!newKPI.name || !newKPI.target_value) return;

        try {
            const response = await axios.post(`http://localhost:5000/api/milestone-kpis`, {
                milestone_id: milestoneId,
                name: newKPI.name,
                description: newKPI.description,
                target_value: parseFloat(newKPI.target_value),
                unit: newKPI.unit
            }, {
                withCredentials: true
            });

            kpis.push(response.data);
            newKPI = { name: '', description: '', target_value: '', unit: 'count' };
            showAddKPI = false;
            onKPIUpdated();
        } catch (error) {
            console.error('Failed to add KPI:', error);
        }
    }

    async function updateKPI(kpi) {
        try {
            await axios.put(`http://localhost:5000/api/milestone-kpis/${kpi.id}`, {
                actual_value: kpi.actual_value
            }, {
                withCredentials: true
            });
            onKPIUpdated();
        } catch (error) {
            console.error('Failed to update KPI:', error);
        }
    }

    async function deleteKPI(kpi) {
        if (!await confirm('Delete this KPI?')) return;

        try {
            await axios.delete(`http://localhost:5000/api/milestone-kpis/${kpi.id}`, {
                withCredentials: true
            });
            kpis = kpis.filter(k => k.id !== kpi.id);
            onKPIUpdated();
        } catch (error) {
            console.error('Failed to delete KPI:', error);
        }
    }

    function applyTemplate(template) {
        newKPI = {
            name: template.name,
            description: template.description,
            target_value: template.target_value,
            unit: template.unit
        };
    }

    function getKPIStatus(kpi) {
        if (!kpi.actual_value) return 'PENDING';
        const achievement = (kpi.actual_value / kpi.target_value) * 100;
        if (achievement >= 100) return 'ACHIEVED';
        if (achievement >= 50) return 'PARTIAL';
        return 'MISSED';
    }

    function getKPIStatusColor(status) {
        switch (status) {
            case 'ACHIEVED': return '#22c55e';
            case 'PARTIAL': return '#f59e0b';
            case 'MISSED': return '#ef4444';
            default: return '#9ca3af';
        }
    }
</script>

{#if show}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
            <!-- Header -->
            <div class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6">
                <div class="flex justify-between items-center">
                    <div>
                        <h2 class="text-2xl font-bold">KPI Management</h2>
                        <p class="text-blue-100">Milestone: {milestone?.title || 'Loading...'}</p>
                    </div>
                    <button on:click={() => show = false} class="text-white hover:text-blue-200">
                        <Icon name="x" size={24} />
                    </button>
                </div>
            </div>

            <!-- Content -->
            <div class="p-6 overflow-y-auto max-h-[60vh]">
                <!-- Add KPI Section -->
                <div class="mb-6">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold text-gray-900">Key Performance Indicators</h3>
                        <button on:click={() => showAddKPI = !showAddKPI} 
                                class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2">
                            <Icon name="plus" size={16} />
                            Add KPI
                        </button>
                    </div>

                    <!-- Add KPI Form -->
                    {#if showAddKPI}
                        <div class="bg-gray-50 rounded-lg p-4 mb-4">
                            <h4 class="font-medium text-gray-900 mb-3">Add New KPI</h4>
                            
                            <!-- Quick Templates -->
                            <div class="mb-4">
                                <p class="text-sm text-gray-600 mb-2">Quick Templates:</p>
                                <div class="flex flex-wrap gap-2">
                                    {#each kpiTemplates as template}
                                        <button on:click={() => applyTemplate(template)}
                                                class="bg-white border border-gray-300 px-3 py-1 rounded text-sm hover:bg-gray-50">
                                            {template.name}
                                        </button>
                                    {/each}
                                </div>
                            </div>

                            <!-- KPI Form -->
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">KPI Name</label>
                                    <input type="text" bind:value={newKPI.name} 
                                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                           placeholder="e.g., Publications">
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">Target Value</label>
                                    <input type="number" bind:value={newKPI.target_value} 
                                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                           placeholder="e.g., 5">
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">Unit</label>
                                    <select bind:value={newKPI.unit} 
                                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                                        <option value="count">Count</option>
                                        <option value="percentage">Percentage</option>
                                        <option value="currency">Currency</option>
                                        <option value="hours">Hours</option>
                                        <option value="papers">Papers</option>
                                        <option value="students">Students</option>
                                        <option value="people">People</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                                    <input type="text" bind:value={newKPI.description} 
                                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                           placeholder="Brief description">
                                </div>
                            </div>

                            <div class="flex gap-2 mt-4">
                                <button on:click={addKPI} 
                                        class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700">
                                    Add KPI
                                </button>
                                <button on:click={() => showAddKPI = false} 
                                        class="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400">
                                    Cancel
                                </button>
                            </div>
                        </div>
                    {/if}

                    <!-- KPIs List -->
                    {#if isLoading}
                        <div class="text-center py-8">
                            <p class="text-gray-500">Loading KPIs...</p>
                        </div>
                    {:else if kpis.length === 0}
                        <div class="text-center py-8 bg-gray-50 rounded-lg">
                            <Icon name="target" size={48} class="text-gray-400 mx-auto mb-4" />
                            <p class="text-gray-500">No KPIs defined for this milestone</p>
                            <p class="text-sm text-gray-400">Add KPIs to track milestone performance</p>
                        </div>
                    {:else}
                        <div class="space-y-4">
                            {#each kpis as kpi}
                                <div class="bg-white border border-gray-200 rounded-lg p-4">
                                    <div class="flex justify-between items-start mb-3">
                                        <div class="flex-1">
                                            <h4 class="font-semibold text-gray-900">{kpi.name}</h4>
                                            <p class="text-sm text-gray-600">{kpi.description}</p>
                                        </div>
                                        <div class="flex items-center gap-2">
                                            <span class="px-2 py-1 rounded-full text-xs font-medium"
                                                  style="background-color: {getKPIStatusColor(getKPIStatus(kpi))}20; color: {getKPIStatusColor(getKPIStatus(kpi))}">
                                                {getKPIStatus(kpi)}
                                            </span>
                                            <button on:click={() => deleteKPI(kpi)} class="text-red-500 hover:text-red-700">
                                                <Icon name="trash-2" size={16} />
                                            </button>
                                        </div>
                                    </div>

                                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        <div>
                                            <label class="block text-sm font-medium text-gray-700 mb-1">Target</label>
                                            <div class="text-lg font-bold text-gray-900">
                                                {kpi.target_value} {kpi.unit}
                                            </div>
                                        </div>
                                        <div>
                                            <label class="block text-sm font-medium text-gray-700 mb-1">Actual</label>
                                            <input type="number" bind:value={kpi.actual_value} 
                                                   on:blur={() => updateKPI(kpi)}
                                                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                                   placeholder="Enter actual value">
                                        </div>
                                        <div>
                                            <label class="block text-sm font-medium text-gray-700 mb-1">Achievement</label>
                                            <div class="text-lg font-bold" style="color: {getKPIStatusColor(getKPIStatus(kpi))}">
                                                {kpi.actual_value ? Math.round((kpi.actual_value / kpi.target_value) * 100) : 0}%
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            {/each}
                        </div>
                    {/if}
                </div>
            </div>
        </div>
    </div>
{/if}
