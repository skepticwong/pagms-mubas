<script>
  import { createEventDispatcher } from 'svelte';
  import { onMount } from 'svelte';
  import { showToast } from '../stores/toast.js';

  const dispatch = createEventDispatcher();

  export let show = false;
  export let asset = null;
  export let user = null;

  let formData = {
    type: 'Scheduled',
    description: '',
    cost: 0,
    performed_by: '',
    performed_date: '',
    next_due_date: '',
    notes: ''
  };

  let maintenanceHistory = [];
  let recommendations = [];
  let loading = false;
  let errors = [];
  let maintenanceTypes = ['Scheduled', 'Repair', 'Inspection', 'Calibration', 'Cleaning'];

  onMount(async () => {
    if (asset) {
      await loadMaintenanceHistory();
      await loadRecommendations();
      // Set default performed date to today
      formData.performed_date = new Date().toISOString().split('T')[0];
    }
  });

  async function loadMaintenanceHistory() {
    try {
      const response = await fetch(`/api/assets/${asset.id}/maintenance/history`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });

      if (response.ok) {
        const data = await response.json();
        maintenanceHistory = data.history || [];
      }
    } catch (error) {
      console.error('Failed to load maintenance history:', error);
    }
  }

  async function loadRecommendations() {
    try {
      const response = await fetch(`/api/assets/${asset.id}/maintenance/recommendations`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });

      if (response.ok) {
        const data = await response.json();
        recommendations = data.recommendations || [];
      }
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    }
  }

  async function submitMaintenance() {
    errors = [];
    loading = true;

    try {
      // Basic validation
      if (!formData.description.trim()) {
        errors.push('Description is required');
      }
      if (!formData.performed_date) {
        errors.push('Performed date is required');
      }
      if (!formData.performed_by.trim()) {
        errors.push('Performed by is required');
      }

      if (errors.length > 0) {
        loading = false;
        return;
      }

      const response = await fetch(`/api/assets/${asset.id}/maintenance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });

      const result = await response.json();

      if (response.ok) {
        showToast('Maintenance record created successfully!');
        
        // Reload history
        await loadMaintenanceHistory();
        
        // Reset form
        resetForm();
        
        dispatch('completed', { maintenance: result.maintenance });
      } else {
        errors = [result.error || 'Failed to create maintenance record'];
      }
    } catch (error) {
      errors = ['Network error. Please try again.'];
    } finally {
      loading = false;
    }
  }

  function resetForm() {
    formData = {
      type: 'Scheduled',
      description: '',
      cost: 0,
      performed_by: '',
      performed_date: new Date().toISOString().split('T')[0],
      next_due_date: '',
      notes: ''
    };
    errors = [];
  }

  function closeModal() {
    dispatch('close');
  }

  function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  }

  function getMaintenanceTypeColor(type) {
    switch (type) {
      case 'Scheduled': return 'text-blue-600 bg-blue-100';
      case 'Repair': return 'text-red-600 bg-red-100';
      case 'Inspection': return 'text-yellow-600 bg-yellow-100';
      case 'Calibration': return 'text-purple-600 bg-purple-100';
      case 'Cleaning': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  }

  async function completeScheduledMaintenance(maintenanceId) {
    try {
      const completionData = {
        performed_date: new Date().toISOString().split('T')[0],
        performed_by: user.name,
        cost: 0,
        notes: 'Completed scheduled maintenance'
      };

      const response = await fetch(`/api/assets/maintenance/${maintenanceId}/complete`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(completionData)
      });

      if (response.ok) {
        showToast('Maintenance completed successfully!');
        await loadMaintenanceHistory();
      } else {
        showToast('Failed to complete maintenance', 'error');
      }
    } catch (error) {
      showToast('Network error', 'error');
    }
  }
</script>

{#if show}
  <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div class="relative top-10 mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-medium text-gray-900">Asset Maintenance</h3>
        <button 
          on:click={closeModal}
          class="text-gray-400 hover:text-gray-600"
        >
          <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Asset Info -->
      <div class="mb-4 p-3 bg-gray-50 rounded">
        <p class="text-sm text-gray-600">
          <strong>Asset:</strong> {asset?.name} ({asset?.asset_tag || 'N/A'})
        </p>
        <p class="text-sm text-gray-600">
          <strong>Last Maintenance:</strong> {asset?.last_maintenance_date ? formatDate(asset.last_maintenance_date) : 'Never'}
        </p>
        <p class="text-sm text-gray-600">
          <strong>Next Due:</strong> {asset?.next_maintenance_date ? formatDate(asset.next_maintenance_date) : 'Not scheduled'}
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Maintenance Form -->
        <div>
          <h4 class="text-md font-semibold text-gray-900 mb-3">Record Maintenance</h4>
          
          <form on:submit|preventDefault={submitMaintenance}>
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Maintenance Type</label>
                <select bind:value={formData.type} class="w-full border border-gray-300 rounded px-3 py-2">
                  {#each maintenanceTypes as type}
                    <option value={type}>{type}</option>
                  {/each}
                </select>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Description *</label>
                <textarea 
                  bind:value={formData.description} 
                  rows="2"
                  required
                  class="w-full border border-gray-300 rounded px-3 py-2"
                  placeholder="What maintenance was performed?"
                ></textarea>
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Performed By *</label>
                  <input 
                    type="text" 
                    bind:value={formData.performed_by} 
                    required
                    class="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="Technician name"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Date *</label>
                  <input 
                    type="date" 
                    bind:value={formData.performed_date} 
                    required
                    class="w-full border border-gray-300 rounded px-3 py-2"
                  />
                </div>
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Cost</label>
                  <input 
                    type="number" 
                    bind:value={formData.cost} 
                    step="0.01"
                    min="0"
                    class="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="0.00"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Next Due Date</label>
                  <input 
                    type="date" 
                    bind:value={formData.next_due_date} 
                    class="w-full border border-gray-300 rounded px-3 py-2"
                  />
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea 
                  bind:value={formData.notes} 
                  rows="2"
                  class="w-full border border-gray-300 rounded px-3 py-2"
                  placeholder="Additional notes or observations"
                ></textarea>
              </div>
            </div>

            <!-- Errors -->
            {#if errors.length > 0}
              <div class="mt-4 p-3 bg-red-50 border border-red-200 rounded">
                {#each errors as error}
                  <p class="text-red-600 text-sm">• {error}</p>
                {/each}
              </div>
            {/if}

            <!-- Actions -->
            <div class="flex justify-end space-x-3 mt-4">
              <button 
                type="button" 
                on:click={resetForm}
                class="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
              >
                Clear
              </button>
              <button 
                type="submit" 
                disabled={loading}
                class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {#if loading}
                  <span class="flex items-center">
                    <svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Saving...
                  </span>
                {:else}
                  Record Maintenance
                {/if}
              </button>
            </div>
          </form>

          <!-- Recommendations -->
          {#if recommendations.length > 0}
            <div class="mt-6">
              <h4 class="text-md font-semibold text-gray-900 mb-2">Recommendations</h4>
              <div class="space-y-2">
                {#each recommendations as recommendation}
                  <div class="p-2 bg-yellow-50 border border-yellow-200 rounded">
                    <div class="text-sm font-medium text-yellow-800">{recommendation.title}</div>
                    <div class="text-xs text-yellow-700">{recommendation.description}</div>
                    {#if recommendation.action}
                      <div class="text-xs text-yellow-600 mt-1">Action: {recommendation.action}</div>
                    {/if}
                  </div>
                {/each}
              </div>
            </div>
          {/if}
        </div>
        </div>

        <!-- Maintenance History -->
        <div>
          <h4 class="text-md font-semibold text-gray-900 mb-3">Maintenance History</h4>
          
          <div class="max-h-96 overflow-y-auto">
            {#if maintenanceHistory.length === 0}
              <div class="text-center py-8 text-gray-500">
                <svg class="h-12 w-12 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                <p class="mt-2">No maintenance records found</p>
              </div>
            {:else}
              <div class="space-y-3">
                {#each maintenanceHistory as record}
                  <div class="border rounded-lg p-3">
                    <div class="flex justify-between items-start">
                      <div>
                        <div class="flex items-center space-x-2">
                          <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full {getMaintenanceTypeColor(record.maintenance_type)}">
                            {record.maintenance_type}
                          </span>
                          {#if record.cost > 0}
                            <span class="text-sm text-gray-600">{formatCurrency(record.cost)}</span>
                          {/if}
                        </div>
                        <div class="text-sm text-gray-900 mt-1">{record.description}</div>
                        <div class="text-xs text-gray-500 mt-1">
                          By: {record.performed_by || 'Unknown'} on {formatDate(record.performed_date)}
                        </div>
                        {#if record.notes}
                          <div class="text-xs text-gray-600 mt-1">{record.notes}</div>
                        {/if}
                      </div>
                      {#if record.maintenance_type === 'Scheduled' && !record.performed_date}
                        <button 
                          on:click={() => completeScheduledMaintenance(record.id)}
                          class="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700"
                        >
                          Complete
                        </button>
                      {/if}
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
