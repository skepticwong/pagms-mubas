<script>
  import axios from 'axios';
  import { createEventDispatcher } from 'svelte';

  export let grant;
  export let isOpen = false;

  const dispatch = createEventDispatcher();
  
  let fromCategoryId = "";
  let toCategoryId = "";
  let amount = 0;
  let justification = "";
  let loading = false;
  let error = "";
  let simulationResult = null;
  let simulationLoading = false;

  $: categories = grant ? grant.categories : [];
  $: fromCategory = categories.find(c => c.id === fromCategoryId);
  $: toCategory = categories.find(c => c.id === toCategoryId);

  // Real-time Simulation
  let debounceTimer;
  $: if (fromCategoryId && toCategoryId && amount > 0) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(simulateVirement, 500);
  }

  async function simulateVirement() {
    if (!fromCategory || !toCategory || amount <= 0) return;
    
    simulationLoading = true;
    try {
      // Calculate percent of total budget
      const percentOfTotal = amount / grant.allocatedUSD;
      
      const response = await axios.post('http://localhost:5000/api/evaluate/simulate', {
        action_type: 'BUDGET_REALLOCATION',
        grant_id: grant.id,
        context: {
          amount: amount,
          percent_of_total: percentOfTotal,
          source_category: fromCategory.label.toLowerCase(),
          dest_category: toCategory.label.toLowerCase(),
          category: 'virement'
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
    if (!fromCategoryId || !toCategoryId || amount <= 0) {
      error = "Please fill in all fields.";
      return;
    }
    
    loading = true;
    error = "";
    try {
      const response = await axios.post('http://localhost:5000/api/virements/request', {
        grant_id: grant.id,
        from_category_id: fromCategoryId,
        to_category_id: toCategoryId,
        amount: amount,
        justification: justification
      });
      
      dispatch('success', response.data);
      close();
    } catch (err) {
      error = err.response?.data?.error || "Failed to process virement.";
    } finally {
      loading = false;
    }
  }

  function close() {
    isOpen = false;
    dispatch('close');
    // Reset form
    fromCategoryId = "";
    toCategoryId = "";
    amount = 0;
    justification = "";
    simulationResult = null;
  }
</script>

{#if isOpen}
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm">
    <div class="bg-white/80 backdrop-blur-2xl border border-white/60 rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-200">
      <div class="p-6 border-b border-white/40 flex justify-between items-center">
        <div>
          <h2 class="text-xl font-bold text-gray-900">Reallocate Funds</h2>
          <p class="text-xs text-gray-500">{grant.name}</p>
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
        {#if simulationResult && simulationResult.outcome === 'PRIOR_APPROVAL'}
          <div class="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex gap-3 animate-in slide-in-from-top-2 duration-300">
            <span class="text-xl">⚠️</span>
            <div>
              <p class="text-sm font-bold text-amber-800">Prior Approval Required</p>
              <p class="text-xs text-amber-700 mt-0.5">
                {simulationResult.triggered_rules?.[0]?.guidance_text || "This reallocation exceeds funder-defined thresholds and requires RSU review."}
              </p>
            </div>
          </div>
        {:else if simulationResult && simulationResult.outcome === 'BLOCK'}
          <div class="p-4 bg-red-50 border border-red-200 rounded-2xl flex gap-3">
            <span class="text-xl">🛑</span>
            <div>
              <p class="text-sm font-bold text-red-800">Policy Violation</p>
              <p class="text-xs text-red-700 mt-0.5">
                {simulationResult.triggered_rules?.[0]?.guidance_text || "This transfer is not allowed under current funder rules."}
              </p>
            </div>
          </div>
        {:else if simulationResult && (simulationResult.outcome === 'PASS' || simulationResult.outcome === 'WARN')}
          <div class="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex gap-3">
            <span class="text-xl">✅</span>
            <div>
              <p class="text-sm font-bold text-emerald-800">Auto-Approval Eligible</p>
              <p class="text-xs text-emerald-700 mt-0.5">Low-impact shift. Funds will move immediately upon submission.</p>
            </div>
          </div>
        {/if}

        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1">
            <label class="text-xs font-semibold text-gray-500 ml-1">From Category</label>
            <select bind:value={fromCategoryId} class="w-full px-4 py-2 bg-white/50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none">
              <option value="">Select source</option>
              {#each categories as cat}
                <option value={cat.id}>{cat.label}</option>
              {/each}
            </select>
          </div>
          <div class="space-y-1">
            <label class="text-xs font-semibold text-gray-500 ml-1">To Category</label>
            <select bind:value={toCategoryId} class="w-full px-4 py-2 bg-white/50 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none">
              <option value="">Select destination</option>
              {#each categories as cat}
                <option value={cat.id}>{cat.label}</option>
              {/each}
            </select>
          </div>
        </div>

        <div class="space-y-1">
          <label class="text-xs font-semibold text-gray-500 ml-1">Amount (USD)</label>
          <div class="relative">
            <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">$</span>
            <input 
              type="number" 
              bind:value={amount} 
              placeholder="0.00"
              class="w-full pl-8 pr-4 py-3 bg-white/50 border border-gray-200 rounded-xl text-lg font-bold focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          {#if fromCategory}
            <p class="text-[10px] text-gray-400 ml-1 italic">Available: ${fromCategory.allocated - fromCategory.spent}</p>
          {/if}
        </div>

        <div class="space-y-1">
          <label class="text-xs font-semibold text-gray-500 ml-1">Justification</label>
          <textarea 
            bind:value={justification} 
            placeholder="Why is this reallocation necessary?"
            class="w-full px-4 py-2 bg-white/50 border border-gray-200 rounded-xl text-sm min-h-[80px] focus:ring-2 focus:ring-blue-500 outline-none"
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
          class="flex-[2] py-3 px-4 rounded-xl bg-blue-600 text-white text-sm font-semibold shadow-lg shadow-blue-200 hover:bg-blue-700 disabled:opacity-50 disabled:shadow-none transition-all flex items-center justify-center gap-2"
        >
          {#if loading}
            <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            Processing...
          {:else}
            Submit Reallocation
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}
