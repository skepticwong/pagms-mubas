<script>
  import { createEventDispatcher } from 'svelte';
  import { onMount } from 'svelte';
  import { showToast } from '../stores/toast.js';

  const dispatch = createEventDispatcher();

  export let show = false;
  export let grant = null;
  export let user = null;

  let formData = {
    task_id: '',
    name: '',
    description: '',
    category: 'Equipment',
    source_type: 'PURCHASED',
    owner_name: '',
    estimated_cost: 0,
    return_date: '',
    rental_fee: 0,
    lending_agreement: ''
  };

  let tasks = [];
  let loading = false;
  let errors = [];
  let sourceTypes = [];
  let categories = [];
  let ruleValidation = null;
  let validatingRules = false;
  let recommendations = [];

  onMount(async () => {
    if (grant) {
      await loadTasks();
      await loadOptions();
    }
  });

  async function loadTasks() {
    try {
      const response = await fetch(`/api/grants/${grant.id}/tasks`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });

      if (response.ok) {
        const data = await response.json();
        tasks = data.tasks || [];
      }
    } catch (error) {
      console.error('Failed to load tasks:', error);
    }
  }

  async function loadOptions() {
    try {
      // Load source types
      const sourceResponse = await fetch('/api/assets/source-types', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (sourceResponse.ok) {
        const data = await sourceResponse.json();
        sourceTypes = data.source_types || [];
      }

      // Load categories
      const categoryResponse = await fetch('/api/assets/categories', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (categoryResponse.ok) {
        const data = await categoryResponse.json();
        categories = data.categories || [];
      }
    } catch (error) {
      console.error('Failed to load options:', error);
    }
  }

  async function submitRequest() {
    errors = [];
    loading = true;

    try {
      // Basic validation
      if (!formData.task_id) {
        errors.push('Please select a task');
      }
      if (!formData.name.trim()) {
        errors.push('Asset name is required');
      }
      if (!formData.source_type) {
        errors.push('Source type is required');
      }

      // Source-specific validation
      if (formData.source_type === 'PURCHASED' && formData.estimated_cost <= 0) {
        errors.push('Estimated cost must be greater than 0 for purchased items');
      }
      if (formData.source_type === 'LENDED' && !formData.owner_name.trim()) {
        errors.push('Owner/lender name is required for lended items');
      }
      if (formData.source_type === 'LENDED' && !formData.return_date) {
        errors.push('Return date is required for lended items');
      }
      if (formData.source_type === 'UNIVERSITY_OWNED' && !formData.owner_name.trim()) {
        errors.push('Asset description is required for university items');
      }

      if (errors.length > 0) {
        loading = false;
        return;
      }

      const response = await fetch('/api/assets/request', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });

      const result = await response.json();

      if (response.ok) {
        if (result.approvals_needed) {
          showToast('Asset request submitted for approval', 'info');
          // Show approval requirements
          result.approvals_needed.forEach(reason => {
            showToast(reason, 'warning');
          });
        } else {
          showToast('Asset request created successfully!');
        }
        
        dispatch('submitted', { asset: result.asset });
        resetForm();
      } else {
        errors = [result.error || 'Failed to submit request'];
      }
    } catch (error) {
      errors = ['Network error. Please try again.'];
    } finally {
      loading = false;
    }
  }

  function resetForm() {
    formData = {
      task_id: '',
      name: '',
      description: '',
      category: 'Equipment',
      source_type: 'PURCHASED',
      owner_name: '',
      estimated_cost: 0,
      return_date: '',
      rental_fee: 0,
      lending_agreement: ''
    };
    errors = [];
  }

  function closeModal() {
    dispatch('close');
  }

  function handleSourceTypeChange() {
    // Reset source-specific fields when source type changes
    if (formData.source_type === 'UNIVERSITY_OWNED') {
      formData.owner_name = 'MUBAS';
      formData.estimated_cost = 0;
      formData.return_date = '';
      formData.rental_fee = 0;
    } else {
      formData.owner_name = '';
    }
    
    // Revalidate rules
    validateRules();
  }

  async function validateRules() {
    if (!formData.task_id || !formData.name || !formData.source_type) {
      ruleValidation = null;
      return;
    }

    validatingRules = true;
    
    try {
      const validationData = {
        ...formData,
        grant_id: grant.id
      };

      const response = await fetch('/api/assets/validate-request', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(validationData)
      });

      if (response.ok) {
        ruleValidation = await response.json();
        recommendations = ruleValidation.recommendations || [];
      } else {
        ruleValidation = { outcome: 'ERROR', error: 'Validation failed' };
      }
    } catch (error) {
      console.error('Rules validation error:', error);
      ruleValidation = { outcome: 'ERROR', error: 'Network error' };
    } finally {
      validatingRules = false;
    }
  }

  function getValidationColor(outcome) {
    switch (outcome) {
      case 'PASS': return 'text-green-600 bg-green-100';
      case 'WARN': return 'text-yellow-600 bg-yellow-100';
      case 'PRIOR_APPROVAL': return 'text-orange-600 bg-orange-100';
      case 'BLOCK': return 'text-red-600 bg-red-100';
      case 'ERROR': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  }

  function getValidationIcon(outcome) {
    switch (outcome) {
      case 'PASS': return '✅';
      case 'WARN': return '⚠️';
      case 'PRIOR_APPROVAL': return '📋';
      case 'BLOCK': return '🚫';
      case 'ERROR': return '❌';
      default: return '❓';
    }
  }
</script>

{#if show}
  <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div class="relative top-10 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-medium text-gray-900">Request Asset</h3>
        <button 
          on:click={closeModal}
          class="text-gray-400 hover:text-gray-600"
        >
          <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <form on:submit|preventDefault={submitRequest}>
        <!-- Grant Info -->
        <div class="mb-4 p-3 bg-gray-50 rounded">
          <p class="text-sm text-gray-600">
            <strong>Grant:</strong> {grant?.title} ({grant?.grant_code})
          </p>
        </div>

        <!-- Task Selection -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Task *</label>
          <select 
            bind:value={formData.task_id} 
            required 
            on:change={validateRules}
            class="w-full border border-gray-300 rounded px-3 py-2"
          >
            <option value="">Select a task...</option>
            {#each tasks as task}
              <option value={task.id}>{task.title}</option>
            {/each}
          </select>
        </div>

        <!-- Rules Validation Panel -->
        {#if validatingRules}
          <div class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
            <div class="flex items-center">
              <div class="animate-spin h-4 w-4 mr-2 border-b-2 border-blue-600"></div>
              <span class="text-blue-600 text-sm">Validating rules...</span>
            </div>
          </div>
        {:else if ruleValidation}
          <div class="mb-4 p-3 rounded {getValidationColor(ruleValidation.outcome)}">
            <div class="flex items-start">
              <span class="text-lg mr-2">{getValidationIcon(ruleValidation.outcome)}</span>
              <div class="flex-1">
                <div class="font-medium text-sm">
                  {#if ruleValidation.outcome === 'PASS'}
                    Request meets all requirements
                  {:else if ruleValidation.outcome === 'WARN'}
                    Request requires attention
                  {:else if ruleValidation.outcome === 'PRIOR_APPROVAL'}
                    Request requires prior approval
                  {:else if ruleValidation.outcome === 'BLOCK'}
                    Request blocked by rules
                  {:else}
                    Validation error
                  {/if}
                </div>
                
                {#if ruleValidation.outcome !== 'PASS'}
                  <div class="text-xs mt-1">
                    {#if ruleValidation.error}
                      {ruleValidation.error}
                    {:else if ruleValidation.block_reasons}
                      {#each ruleValidation.block_reasons as reason}
                        <div>• {reason}</div>
                      {/each}
                    {:else if ruleValidation.prior_approval_reasons}
                      {#each ruleValidation.prior_approval_reasons as reason}
                        <div>• {reason}</div>
                      {/each}
                    {/if}
                  </div>
                {/if}
              </div>
            </div>
          </div>
        {/if}

        <!-- Recommendations -->
        {#if recommendations.length > 0}
          <div class="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
            <div class="text-sm font-medium text-yellow-800 mb-2">Recommendations:</div>
            {#each recommendations as recommendation}
              <div class="text-xs text-yellow-700">• {recommendation}</div>
            {/each}
          </div>
        {/if}

        <!-- Asset Details -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Asset Name *</label>
            <input 
              type="text" 
              bind:value={formData.name} 
              required 
              on:blur={validateRules}
              class="w-full border border-gray-300 rounded px-3 py-2"
              placeholder="e.g., Dell Laptop, Soil Testing Kit"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select bind:value={formData.category} on:change={validateRules} class="w-full border border-gray-300 rounded px-3 py-2">
              {#each categories as category}
                <option value={category}>{category}</option>
              {/each}
            </select>
          </div>
        </div>

        <!-- Description -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea 
            bind:value={formData.description} 
            rows="3"
            class="w-full border border-gray-300 rounded px-3 py-2"
            placeholder="Why is this asset needed for the task?"
          ></textarea>
        </div>

        <!-- Source Type -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Source Type *</label>
          <select 
            bind:value={formData.source_type} 
            required 
            on:change={handleSourceTypeChange}
            class="w-full border border-gray-300 rounded px-3 py-2"
          >
            {#each sourceTypes as sourceType}
              <option value={sourceType.value}>{sourceType.label}</option>
            {/each}
          </select>
        </div>

        <!-- Conditional Fields Based on Source Type -->
        {#if formData.source_type === 'PURCHASED'}
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">Estimated Cost *</label>
            <input 
              type="number" 
              bind:value={formData.estimated_cost} 
              step="0.01"
              min="0"
              required
              on:blur={validateRules}
              class="w-full border border-gray-300 rounded px-3 py-2"
              placeholder="0.00"
            />
            <p class="text-xs text-gray-500 mt-1">Amount in USD</p>
          </div>
        {:else if formData.source_type === 'LENDED'}
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Owner/Lender Name *</label>
              <input 
                type="text" 
                bind:value={formData.owner_name} 
                required
                on:blur={validateRules}
                class="w-full border border-gray-300 rounded px-3 py-2"
                placeholder="e.g., Ministry of Agriculture"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Return Date *</label>
              <input 
                type="date" 
                bind:value={formData.return_date} 
                required
                on:change={validateRules}
                class="w-full border border-gray-300 rounded px-3 py-2"
              />
            </div>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Rental Fee (if any)</label>
              <input 
                type="number" 
                bind:value={formData.rental_fee} 
                step="0.01"
                min="0"
                on:blur={validateRules}
                class="w-full border border-gray-300 rounded px-3 py-2"
                placeholder="0.00"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Lending Agreement</label>
              <input 
                type="text" 
                bind:value={formData.lending_agreement} 
                class="w-full border border-gray-300 rounded px-3 py-2"
                placeholder="Agreement reference or notes"
              />
            </div>
          </div>
        {:else if formData.source_type === 'UNIVERSITY_OWNED'}
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">University Asset Description *</label>
            <input 
              type="text" 
              bind:value={formData.owner_name} 
              required
              on:blur={validateRules}
              class="w-full border border-gray-300 rounded px-3 py-2"
              placeholder="e.g., University Truck #4, Lab Room 201"
            />
          </div>
        {/if}

        <!-- Errors -->
        {#if errors.length > 0}
          <div class="mb-4 p-3 bg-red-50 border border-red-200 rounded">
            {#each errors as error}
              <p class="text-red-600 text-sm">• {error}</p>
            {/each}
          </div>
        {/if}

        <!-- Actions -->
        <div class="flex justify-end space-x-3">
          <button 
            type="button" 
            on:click={closeModal}
            class="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button 
            type="submit" 
            disabled={loading || (ruleValidation && ruleValidation.outcome === 'BLOCK')}
            class="px-4 py-2 rounded disabled:opacity-50 {
              ruleValidation && ruleValidation.outcome === 'BLOCK' 
                ? 'bg-gray-400 text-white cursor-not-allowed' 
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }"
          >
            {#if loading}
              <span class="flex items-center">
                <svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Submitting...
              </span>
            {:else if ruleValidation && ruleValidation.outcome === 'BLOCK'}
              Request Blocked
            {:else if ruleValidation && ruleValidation.outcome === 'PRIOR_APPROVAL'}
              Submit for Approval
            {:else}
              Submit Request
            {/if}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
