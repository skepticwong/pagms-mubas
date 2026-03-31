<script>
  import axios from 'axios';
  import { createEventDispatcher } from 'svelte';

  export let grant;
  export let isOpen = false;

  const dispatch = createEventDispatcher();
  
  let requestedEndDate = "";
  let justification = "";
  let funderFile = null;
  let loading = false;
  let error = "";

  // Initialize with current end date + 6 months as suggestion
  $: if (isOpen && grant && !requestedEndDate) {
    try {
      const baseDate = grant.end_date ? new Date(grant.end_date) : new Date();
      if (isNaN(baseDate.getTime())) {
         requestedEndDate = new Date().toISOString().split('T')[0];
      } else {
         const current = new Date(baseDate);
         current.setMonth(current.getMonth() + 6);
         requestedEndDate = current.toISOString().split('T')[0];
      }
    } catch (e) {
      console.error("Date init error:", e);
      requestedEndDate = new Date().toISOString().split('T')[0];
    }
  }

  async function handleSubmit() {
    if (!requestedEndDate || !justification) {
      error = "Please provide both the new date and a justification.";
      return;
    }
    
    loading = true;
    error = "";
    
    // Use FormData for file upload
    const formData = new FormData();
    formData.append('grant_id', grant.id);
    formData.append('requested_end_date', requestedEndDate);
    formData.append('justification', justification);
    if (funderFile) {
      formData.append('funder_approval_doc', funderFile);
    }

    try {
      const response = await axios.post('http://localhost:5000/api/extensions/request', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        withCredentials: true
      });
      
      dispatch('success', response.data);
      close();
    } catch (err) {
      error = err.response?.data?.error || "Failed to submit extension request.";
    } finally {
      loading = false;
    }
  }

  function handleFileChange(e) {
    funderFile = e.target.files[0];
  }

  function close() {
    isOpen = false;
    dispatch('close');
    // Reset form
    requestedEndDate = "";
    justification = "";
    funderFile = null;
    error = "";
  }
</script>

{#if isOpen}
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm">
    <div class="bg-white/80 backdrop-blur-2xl border border-white/60 rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-200">
      <div class="p-6 border-b border-white/40 flex justify-between items-center bg-blue-50/30">
        <div>
          <h2 class="text-xl font-bold text-gray-900">Request No-Cost Extension</h2>
          <p class="text-xs text-gray-500 mt-1">Submit a formal project timeline adjustment</p>
        </div>
        <button on:click={close} class="p-2 hover:bg-gray-100 rounded-full transition-colors">
          <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>

      <div class="p-6 space-y-6">
        {#if error}
          <div class="p-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm flex items-center gap-2">
             <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
             {error}
          </div>
        {/if}

        <div class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">New Project End Date</label>
            <div class="grid grid-cols-2 gap-4 items-center">
              <div class="p-3 bg-gray-50 rounded-xl border border-gray-100">
                <p class="text-[10px] text-gray-400 uppercase font-bold">Current</p>
                <p class="text-sm font-semibold text-gray-600">{grant?.end_date}</p>
              </div>
              <input 
                type="date" 
                bind:value={requestedEndDate}
                class="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-shadow"
              />
            </div>
            <p class="text-[10px] text-blue-600 mt-2 font-medium bg-blue-50/50 p-2 rounded-lg border border-blue-100/50">
              ℹ️ On approval, all pending milestones will shift linearly by the same duration.
            </p>
          </div>

          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Justification for Extension</label>
            <textarea 
              bind:value={justification}
              placeholder="Explain delays (e.g. procurement, personnel recruitment, field access challenges)..."
              class="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-blue-500 outline-none h-32 resize-none transition-shadow"
            ></textarea>
          </div>

          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Funder Approval Letter (Optional)</label>
            <div class="relative group">
              <input 
                type="file" 
                on:change={handleFileChange}
                accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              />
              <div class="border-2 border-dashed border-gray-200 group-hover:border-blue-400 rounded-2xl p-6 text-center transition-colors bg-gray-50/30 group-hover:bg-blue-50/10">
                <div class="w-10 h-10 bg-white rounded-full shadow-sm flex items-center justify-center mx-auto mb-2 text-blue-500 group-hover:scale-110 transition-transform">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                </div>
                <p class="text-sm font-semibold text-gray-700">
                  {funderFile ? funderFile.name : "Upload Approval Letter"}
                </p>
                <p class="text-xs text-gray-400 mt-1">PDF, DOC, or Image (Max 10MB)</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="p-6 bg-gray-50/50 flex gap-3 border-t border-white/60">
        <button 
          on:click={close}
          class="flex-1 px-4 py-3 rounded-xl border border-gray-200 text-sm font-bold text-gray-600 hover:bg-white transition-all outline-none"
        >
          Cancel
        </button>
        <button 
          on:click={handleSubmit}
          disabled={loading}
          class="flex-[2] px-4 py-3 rounded-xl bg-blue-600 text-white text-sm font-bold shadow-lg shadow-blue-100 hover:bg-blue-700 transition-all flex items-center justify-center gap-2 disabled:bg-blue-300 disabled:shadow-none outline-none"
        >
          {#if loading}
            <div class="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
            Submitting...
          {:else}
            Submit Request
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  textarea:focus, input:focus {
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
  }
</style>
