<script>
  import { onMount } from "svelte";
  import axios from "axios";
  import Layout from "../components/Layout.svelte";
  import Icon from "../components/Icon.svelte";
  import { showToast } from "../stores/toast.js";
  import { user } from "../stores/auth.js";

  let loading = true;
  let grants = [];
  let stats = {
    total: 0,
    active: 0,
    suspended: 0,
    expired: 0,
    pending: 0
  };

  // Upload state
  let selectedGrant = null;
  let showUploadModal = false;
  let ethicsFile = null;
  let ethicsApprovalNum = '';
  let ethicsExpiryDate = '';
  let submitting = false;

  onMount(async () => {
    await loadData();
  });

  async function loadData() {
    loading = true;
    try {
      // Re-using the budget overview endpoint which now includes ethics data
      const res = await axios.get("/api/pi-grants-budget", { withCredentials: true });
      // Filter for grants that actually require ethics
      grants = (res.data.grants || []).filter(g => g.ethics_required);
      
      calculateStats();
    } catch (err) {
      console.error("Failed to load ethics data", err);
      showToast("Failed to load compliance data", "error");
    } finally {
      loading = false;
    }
  }

  function calculateStats() {
    stats = {
      total: grants.length,
      active: grants.filter(g => g.ethics_status === 'VERIFIED').length,
      suspended: grants.filter(g => g.ethics_status === 'SUSPENDED_ETHICS').length,
      expired: grants.filter(g => g.ethics_status === 'EXPIRED').length,
      pending: grants.filter(g => g.ethics_status === 'PENDING_ETHICS').length
    };
  }

  function getDaysToExpiry(expiryDate) {
    if (!expiryDate) return null;
    const diff = new Date(expiryDate) - new Date();
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
  }

  function getStatusColor(status) {
    switch (status) {
      case 'VERIFIED': return 'bg-emerald-100 text-emerald-700';
      case 'PENDING_ETHICS': return 'bg-blue-100 text-blue-700';
      case 'SUSPENDED_ETHICS': return 'bg-rose-100 text-rose-700';
      case 'EXPIRED': return 'bg-rose-100 text-rose-700 font-bold border border-rose-200';
      case 'NOT_SUBMITTED': return 'bg-amber-100 text-amber-700';
      default: return 'bg-gray-100 text-gray-600';
    }
  }

  function openUploadModal(grant) {
    selectedGrant = grant;
    ethicsApprovalNum = grant.ethics_approval_number || '';
    ethicsExpiryDate = grant.ethics_expiry_date || '';
    showUploadModal = true;
  }

  function handleFileChange(e) {
    ethicsFile = e.target.files[0];
  }

  async function handleSubmitRenewal() {
    if (!ethicsFile || !ethicsApprovalNum || !ethicsExpiryDate) {
      showToast("Please fill all fields and upload the certificate", "error");
      return;
    }

    submitting = true;
    const formData = new FormData();
    formData.append('ethics_certificate', ethicsFile);
    formData.append('ethics_approval_number', ethicsApprovalNum);
    formData.append('ethics_expiry_date', ethicsExpiryDate);

    try {
      await axios.put(`/api/grants/${selectedGrant.id}/ethics-reinstatement`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        withCredentials: true
      });
      showToast("Renewal request submitted for RSU verification", "success");
      showUploadModal = false;
      await loadData();
    } catch (err) {
      const msg = err.response?.data?.error || "Failed to submit renewal";
      showToast(msg, "error");
    } finally {
      submitting = false;
      ethicsFile = null;
    }
  }

  // Sort grants by expiration proximity
  $: sortedGrants = [...grants].sort((a, b) => {
    const daysA = getDaysToExpiry(a.ethics_expiry_date) ?? 9999;
    const daysB = getDaysToExpiry(b.ethics_expiry_date) ?? 9999;
    return daysA - daysB;
  });

</script>

<Layout>
  <div class="max-w-7xl mx-auto space-y-8 bg-transparent">
    <!-- Header -->
    <header class="bg-white border border-gray-100 rounded-3xl shadow-md p-8">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <p class="text-[10px] uppercase tracking-[0.3em] text-blue-600 font-bold mb-1">Compliance Management</p>
          <h1 class="text-3xl md:text-4xl font-bold text-gray-900 tracking-tight">Ethics Hub</h1>
          <p class="text-gray-500 mt-1 text-sm">Centralized oversight for your research ethics certifications.</p>
        </div>
        
        <!-- Stats Summary -->
        <div class="flex gap-3 flex-wrap">
          <div class="px-5 py-3 bg-emerald-50 border border-emerald-100 rounded-2xl text-center min-w-[80px]">
            <p class="text-[10px] text-emerald-600 font-bold uppercase tracking-wider">Active</p>
            <p class="text-2xl font-black text-emerald-900">{stats.active}</p>
          </div>
          <div class="px-5 py-3 bg-rose-50 border border-rose-100 rounded-2xl text-center min-w-[80px]">
            <p class="text-[10px] text-rose-600 font-bold uppercase tracking-wider">Critical</p>
            <p class="text-2xl font-black text-rose-900">{stats.expired + stats.suspended}</p>
          </div>
          <div class="px-5 py-3 bg-blue-50 border border-blue-100 rounded-2xl text-center min-w-[80px]">
            <p class="text-[10px] text-blue-600 font-bold uppercase tracking-wider">Pending</p>
            <p class="text-2xl font-black text-blue-900">{stats.pending}</p>
          </div>
        </div>
      </div>
    </header>

    {#if loading}
      <div class="py-20 text-center text-gray-500">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p>Synchronizing compliance registry...</p>
      </div>
    {:else if grants.length === 0}
       <div class="bg-white border border-gray-100 rounded-3xl p-16 text-center shadow-md">
          <div class="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
             <Icon name="compliance" size={40} className="text-gray-300" />
          </div>
          <h2 class="text-xl font-bold text-gray-900">No Ethics Records Found</h2>
          <p class="text-gray-500 mt-2 max-w-md mx-auto">None of your projects require ethical certification.</p>
       </div>
    {:else}
      <!-- Ethics Timeline Section -->
      <section class="space-y-4">
        <h2 class="text-lg font-bold text-gray-900 flex items-center gap-2 px-2">
          <Icon name="calendar" size={20} className="text-blue-600" />
          Renewal Timeline
        </h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {#each sortedGrants as grant}
            {@const days = getDaysToExpiry(grant.ethics_expiry_date)}
            <div class="bg-white border border-gray-100 rounded-3xl p-6 shadow-sm hover:shadow-md transition-all duration-300">
               <div class="flex justify-between items-start mb-4">
                  <span class={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-widest ${getStatusColor(grant.ethics_status)}`}>
                    {grant.ethics_status?.replace('_', ' ')}
                  </span>
                  {#if days !== null}
                    <div class="text-right">
                       <p class={`text-sm font-bold ${days < 30 ? 'text-rose-600' : 'text-gray-900'}`}>
                         {days > 0 ? `${days} days left` : days === 0 ? 'Expires today' : 'Expired'}
                       </p>
                       <p class="text-[10px] text-gray-400 font-bold uppercase">{grant.ethics_expiry_date}</p>
                    </div>
                  {/if}
               </div>

               <h3 class="font-bold text-gray-900 mb-1 truncate">{grant.title}</h3>
               <p class="text-xs text-gray-400 font-mono mb-4">{grant.grant_code}</p>

               {#if days !== null && days > -365}
                 {@const progress = Math.max(0, Math.min(100, (days / 365) * 100))}
                 <div class="w-full h-1.5 bg-gray-50 rounded-full mb-6 overflow-hidden">
                    <div 
                      class={`h-full rounded-full transition-all duration-1000 ${days < 30 ? 'bg-rose-500' : days < 90 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                      style={`width: ${progress}%`}
                    ></div>
                 </div>
               {/if}

               <button 
                 on:click={() => openUploadModal(grant)}
                 class="w-full py-3 bg-blue-600 text-white rounded-2xl text-xs font-bold hover:bg-blue-700 transition-colors shadow-lg shadow-blue-100"
               >
                 Upload New Certificate
               </button>
            </div>
          {/each}
        </div>
      </section>

      <!-- Detailed Registry -->
      <section class="space-y-4 pt-8">
        <h2 class="text-lg font-bold text-gray-900 flex items-center gap-2 px-2">
          <Icon name="folder" size={20} className="text-blue-600" />
          Institutional Records
        </h2>

        <div class="bg-white border border-gray-100 rounded-3xl shadow-md overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm text-left">
              <thead>
                <tr class="text-[10px] text-gray-400 uppercase tracking-widest border-b border-gray-50">
                  <th class="px-6 py-5 font-black">Project / Grant Code</th>
                  <th class="px-6 py-5 font-black">Approval Number</th>
                  <th class="px-6 py-5 font-black">Status</th>
                  <th class="px-6 py-5 font-black">Expiry Date</th>
                  <th class="px-6 py-5 font-black text-right">Certificate</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                {#each grants as grant}
                  <tr class="hover:bg-gray-50/50 transition-colors">
                    <td class="px-6 py-6 font-bold text-gray-900">
                      {grant.title}
                      <p class="text-[10px] text-gray-400 mt-0.5 tracking-tight">{grant.grant_code}</p>
                    </td>
                    <td class="px-6 py-6 font-mono text-xs text-gray-500">
                      {grant.ethics_approval_number || 'Awaiting Submission'}
                    </td>
                    <td class="px-6 py-6">
                      <span class={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${getStatusColor(grant.ethics_status)}`}>
                        {grant.ethics_status?.replace('_', ' ')}
                      </span>
                    </td>
                    <td class="px-6 py-6 text-gray-600 font-medium">
                      {grant.ethics_expiry_date || '—'}
                    </td>
                    <td class="px-6 py-6 text-right">
                      {#if grant.ethics_certificate_filename}
                        <a 
                          href={`/api/uploads/ethics/${grant.ethics_certificate_filename}`} 
                          target="_blank"
                          class="px-3 py-1.5 bg-blue-50 text-blue-600 rounded-lg text-[10px] font-bold hover:bg-blue-100 transition-colors"
                        >
                          VIEW PDF
                        </a>
                      {:else}
                        <span class="text-xs italic text-gray-300">No file</span>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    {/if}
  </div>

  <!-- Upload Modal -->
  {#if showUploadModal}
    <div class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm">
      <div class="bg-white rounded-[2rem] shadow-2xl w-full max-w-xl overflow-hidden">
        <div class="p-8 md:p-10 space-y-6">
          <header class="flex justify-between items-start border-b border-gray-50 pb-6">
            <div>
              <p class="text-[10px] font-black text-blue-600 uppercase tracking-widest mb-1">Institutional Review</p>
              <h2 class="text-2xl font-bold text-gray-900">Renew Ethics Certificate</h2>
              <p class="text-xs text-gray-500 mt-1 truncate max-w-[300px]">{selectedGrant?.title}</p>
            </div>
            <button on:click={() => showUploadModal = false} class="p-2 hover:bg-gray-100 rounded-full transition-colors">
              <Icon name="close" size={20} />
            </button>
          </header>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-1">
              <label class="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Approval Number</label>
              <input 
                type="text" 
                bind:value={ethicsApprovalNum}
                placeholder="REC/2026/..."
                class="w-full px-5 py-4 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:bg-white outline-none transition-all text-sm"
              />
            </div>
            <div class="space-y-1">
              <label class="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Expiry Date</label>
              <input 
                type="date" 
                bind:value={ethicsExpiryDate}
                class="w-full px-5 py-4 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:bg-white outline-none transition-all text-sm"
              />
            </div>
          </div>

          <div class="space-y-1">
            <label class="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Certificate PDF</label>
            <div class={`relative border-2 border-dashed rounded-3xl p-8 text-center transition-all ${ethicsFile ? 'border-emerald-200 bg-emerald-50/50' : 'border-gray-200 hover:border-blue-200 bg-gray-50'}`}>
               <input 
                 type="file" 
                 accept=".pdf" 
                 on:change={handleFileChange}
                 class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
               />
               {#if ethicsFile}
                 <div class="flex flex-col items-center">
                    <div class="w-10 h-10 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-2">
                       <Icon name="check" size={20} />
                    </div>
                    <p class="text-sm font-bold text-gray-900">{ethicsFile.name}</p>
                    <p class="text-xs text-emerald-600 mt-1">Ready for submission</p>
                 </div>
               {:else}
                 <div class="flex flex-col items-center">
                    <div class="w-10 h-10 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mb-2">
                       <Icon name="upload" size={20} />
                    </div>
                    <p class="text-sm font-bold text-gray-600 tracking-tight">Click to upload certificate</p>
                    <p class="text-xs text-gray-400 mt-1">PDF format (max 10MB)</p>
                 </div>
               {/if}
            </div>
          </div>

          <div class="flex gap-4 pt-4">
            <button 
              on:click={() => showUploadModal = false}
              class="flex-1 py-4 bg-gray-100 text-gray-600 rounded-2xl text-sm font-bold hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button 
              on:click={handleSubmitRenewal}
              disabled={submitting}
              class="flex-2 py-4 bg-blue-600 text-white rounded-2xl text-sm font-bold hover:bg-blue-700 transition-all shadow-lg shadow-blue-100 disabled:opacity-50 px-8"
            >
              {submitting ? 'Submitting...' : 'Submit to RSU'}
            </button>
          </div>
        </div>
      </div>
    </div>
  {/if}
</Layout>


<style>
  /* Premium animation classes */
  .fade-in {
    animation: fadeIn 0.2s ease-out;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .zoom-in-95 {
    animation: zoomIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  @keyframes zoomIn {
    from { opacity: 0; transform: scale(0.95) translateY(10px); }
    to { opacity: 1; transform: scale(1) translateY(0); }
  }

  .flex-2 { flex: 2; }
</style>
