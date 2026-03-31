<script>
  import axios from 'axios';
  import { createEventDispatcher } from 'svelte';

  export let grants = [];
  export let isOpen = false;

  const dispatch = createEventDispatcher();
  
  let selectedGrantId = "";
  let selectedCategory = "";
  let amount = 0;
  let justification = "";
  let loading = false;
  let error = "";
  let simulationResult = null;
  let simulationLoading = false;

  $: selectedGrant = grants.find(g => g.id === parseInt(selectedGrantId));
  $: categories = selectedGrant ? selectedGrant.categories || [] : [];

  // Real-time Simulation
  let debounceTimer;
  $: if (selectedGrantId && selectedCategory && amount > 0) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(simulateApproval, 500);
  }

  async function simulateApproval() {
    if (!selectedGrant || !selectedCategory || amount <= 0) return;
    
    simulationLoading = true;
    try {
      const response = await axios.post('http://localhost:5000/api/evaluate/simulate', {
        action_type: 'EXPENSE_PRE_APPROVAL',
        grant_id: selectedGrant.id,
        context: {
          amount: amount,
          category: selectedCategory.toLowerCase(),
          request_type: selectedCategory.toUpperCase()
        }
      });
      simulationResult = response.data;
    } catch (err) {
      console.error("Simulation failed", err);
    } finally {
      simulationLoading = false;
    }
  }

  async function handleSubmit() {
    if (!selectedGrantId || !selectedCategory || amount <= 0) {
      error = "Please fill in all fields.";
      return;
    }
    
    loading = true;
    error = "";
    try {
      const response = await axios.post('http://localhost:5000/api/prior-approvals/request', {
        grant_id: selectedGrantId,
        request_type: selectedCategory.toUpperCase(),
        category: selectedCategory,
        amount: amount,
        justification: justification
      });
      
      dispatch('success', response.data);
      close();
    } catch (err) {
      error = err.response?.data?.error || "Failed to submit request.";
    } finally {
      loading = false;
    }
  }

  function close() {
    isOpen = false;
    dispatch('close');
    // Reset form
    selectedGrantId = "";
    selectedCategory = "";
    amount = 0;
    justification = "";
    simulationResult = null;
  }
</script>

{#if isOpen}
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm">
    <div class="bg-white/80 backdrop-blur-2xl border border-white/60 rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-200">
      <div class="p-6 border-b border-white/40 flex justify-between items-center bg-gradient-to-r from-blue-50/50 to-transparent">
        <div>
          <h2 class="text-xl font-bold text-gray-900">Prior Approval Request</h2>
          <p class="text-xs text-gray-500">Authorization before you spend</p>
        </div>
        <button on:click={close} class="p-2 hover:bg-gray-100 rounded-full transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>

      <div class="p-6 space-y-4">
        {#if error}
          <div class="p-3 bg-red-50 border border-red-100 text-red-600 rounded-xl text-sm">
            {error}
          </div>
        {/if}

        <!-- Rule Feedback Banner (The "Gold Standard" Yellow Banner) -->
        {#if simulationResult && (simulationResult.outcome === 'PRIOR_APPROVAL' || simulationResult.outcome === 'WARN')}
          <div class="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex gap-3 animate-in slide-in-from-top-2 duration-300">
            <span class="text-xl">🛡️</span>
            <div>
              <p class="text-sm font-bold text-amber-800">Authorization Required</p>
              <p class="text-xs text-amber-700 mt-0.5">
                {simulationResult.triggered_rules?.[0]?.guidance_text || "This expense type requires RSU review before purchase."}
              </p>
            </div>
          </div>
        {:else if simulationResult && simulationResult.outcome === 'BLOCK'}
          <div class="p-4 bg-red-50 border border-red-200 rounded-2xl flex gap-3">
            <span class="text-xl">🛑</span>
            <div>
              <p class="text-sm font-bold text-red-800">Policy Violation</p>
              <p class="text-xs text-red-700 mt-0.5">
                {simulationResult.triggered_rules?.[0]?.guidance_text || "This expense is strictly prohibited under current rules."}
              </p>
            </div>
          </div>
        {:else if simulationResult && simulationResult.outcome === 'PASS'}
          <div class="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex gap-3">
            <span class="text-xl">✅</span>
            <div>
              <p class="text-sm font-bold text-emerald-800">Pre-Approved</p>
              <p class="text-xs text-emerald-700 mt-0.5">Standard request. Likely to be fast-tracked.</p>
            </div>
          </div>
        {/if}

        <div class="space-y-1">
          <label class="text-xs font-semibold text-gray-500 ml-1">Select Grant</label>
          <select bind:value={selectedGrantId} class="w-full px-4 py-2 bg-white/50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none">
            <option value="">Choose a grant...</option>
            {#each grants as grant}
              <option value={grant.id}>{grant.title}</option>
            {/each}
          </select>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1">
            <label class="text-xs font-semibold text-gray-500 ml-1">Expense Category</label>
            <select bind:value={selectedCategory} class="w-full px-4 py-2 bg-white/50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none">
              <option value="">Select type...</option>
              <option value="Travel">International Travel</option>
              <option value="Equipment">Equipment Purchase</option>
              <option value="Consultant">Consultant / Sub-contract</option>
              <option value="Personnel">Personnel Addition</option>
              <option value="Other">Other Extraordinary Item</option>
            </select>
          </div>
          <div class="space-y-1">
            <label class="text-xs font-semibold text-gray-500 ml-1">Estimated Amount (USD)</label>
            <input 
              type="number" 
              bind:value={amount} 
              placeholder="0.00"
              class="w-full px-4 py-2 bg-white/50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none font-semibold text-blue-600"
            />
          </div>
        </div>

        <div class="space-y-1">
          <label class="text-xs font-semibold text-gray-500 ml-1">Justification & Details</label>
          <textarea 
            bind:value={justification} 
            placeholder="Describe the purpose, dates, or specific equipment details..."
            class="w-full px-4 py-2 bg-white/50 border border-gray-200 rounded-xl text-sm min-h-[100px] focus:ring-2 focus:ring-blue-500 outline-none"
          ></textarea>
        </div>
      </div>

      <div class="p-6 bg-gray-50/50 border-t border-white/40 flex gap-3">
        <button on:click={close} class="flex-1 py-3 px-4 rounded-xl border border-gray-200 text-sm font-semibold text-gray-600 hover:bg-white transition-colors">
          Cancel
        </button>
        <button 
          on:click={handleSubmit}
          disabled={loading || simulationLoading || (simulationResult && simulationResult.outcome === 'BLOCK')}
          class="flex-[2] py-3 px-4 rounded-xl bg-purple-600 text-white text-sm font-semibold shadow-lg shadow-purple-200 hover:bg-purple-700 disabled:opacity-50 disabled:shadow-none transition-all flex items-center justify-center gap-2"
        >
          {#if loading}
            <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            Sending...
          {:else}
            Submit for Authorization
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}
