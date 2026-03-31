<script>
  import axios from "axios";
  import { onMount, onDestroy } from "svelte";
  import Layout from "../components/Layout.svelte";
  import Icon from "../components/Icon.svelte";
  import { showToast } from "../stores/toast.js";
  import { confirm, prompt } from "../stores/modals.js";
  import { user } from "../stores/auth.js";
  import { router } from "../stores/router.js";

  let loading = true;
  let ethicsQueue = [];
  let ethicsLoading = false;
  let activeTab = "meetings"; // meetings, reviews, registry
  let searchTerm = "";

  $: isRSU = $user?.role?.toString().toUpperCase() === "RSU";

  onMount(async () => {
    if (!isRSU) {
      loading = false;
      return;
    }
    await loadEthicsQueue();
    loading = false;
  });

  async function loadEthicsQueue() {
    ethicsLoading = true;
    try {
      const res = await axios.get("/api/rsu/ethics-queue", { withCredentials: true });
      ethicsQueue = res.data.grants;
    } catch (err) {
      console.error("Failed to load ethics queue", err);
      showToast("Failed to load ethics queue", "error");
    } finally {
      ethicsLoading = false;
    }
  }

  // Derived collections
  $: meetingNeeded = ethicsQueue.filter(g => g.ethics_status === 'PENDING_MEETING');
  // Gap 3: Separate fresh submissions from post-expiry renewals
  $: freshReviews = ethicsQueue.filter(g =>
    (g.ethics_status === 'PENDING_ETHICS' || g.ethics_status === 'PENDING_VERIFICATION') &&
    g.status !== 'ETHICS_SUSPENDED'
  );
  $: renewalReviews = ethicsQueue.filter(g =>
    (g.ethics_status === 'PENDING_ETHICS' || g.ethics_status === 'PENDING_VERIFICATION') &&
    g.status === 'ETHICS_SUSPENDED'
  );
  $: reviewsNeeded = [...renewalReviews, ...freshReviews]; // Renewals first — higher urgency
  $: allEthicalGrants = ethicsQueue.filter(g => g.ethics_required);

  // Registry search
  $: filteredRegistry = ethicsQueue.filter(g => {
    if (!searchTerm) return true;
    return g.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
           g.grant_code?.toLowerCase().includes(searchTerm.toLowerCase());
  });

  async function handleVerifyEthics(grantId) {
    const grant = ethicsQueue.find(g => g.id === grantId);
    let approval_number = null;
    let expiry_date = null;

    if (grant?.ethics_status === 'PENDING_MEETING') {
      const confirmed = await confirm("Conducting REC Meeting: Would you like to approve this grant and assign a certificate now?");
      if (!confirmed) return;

      approval_number = await prompt("Enter Ethics Approval Number (assigned during meeting):");
      if (!approval_number) return;

      expiry_date = await prompt("Enter Expiry Date (YYYY-MM-DD):");
      if (!expiry_date) return;
    } else {
      const confirmed = await confirm("Verify this uploaded ethics certificate?");
      if (!confirmed) return;
    }

    const notes = await prompt("Enter verification notes (optional):");
    
    try {
      await axios.put(`/api/rsu/grants/${grantId}/verify-ethics`, { 
        notes,
        approval_number,
        expiry_date
      }, { withCredentials: true });
      showToast("Ethics verified. Grant unlocked.", "success");
      await loadEthicsQueue();
    } catch (err) {
      showToast("Verification failed: " + (err.response?.data?.error || err.message), "error");
    }
  }

  async function handleRejectEthics(grantId) {
    const reason = await prompt("Enter reason for rejection (required):");
    if (!reason) return;
    try {
      await axios.put(`/api/rsu/grants/${grantId}/reject-ethics`, { reason }, { withCredentials: true });
      showToast("Ethics certificate rejected.", "info");
      await loadEthicsQueue();
    } catch (err) {
      showToast("Rejection failed", "error");
    }
  }

  function getStatusColor(status) {
    switch (status) {
      case 'VERIFIED': return 'bg-emerald-100 text-emerald-700';
      case 'PENDING_MEETING': return 'bg-blue-100 text-blue-700';
      case 'PENDING_ETHICS': return 'bg-amber-100 text-amber-700';
      case 'SUSPENDED_ETHICS': return 'bg-rose-100 text-rose-700';
      case 'EXPIRED': return 'bg-gray-100 text-gray-700 font-bold';
      default: return 'bg-gray-100 text-gray-600';
    }
  }
</script>

<Layout>
  {#if loading}
    <div class="py-20 text-center text-gray-500">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600 mx-auto mb-4"></div>
      <p>Opening REC Management Hub…</p>
    </div>
  {:else if !isRSU}
    <div class="max-w-4xl mx-auto mt-12 bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl p-10 text-center shadow-lg">
      <h1 class="text-2xl font-bold text-gray-900 mb-2">Access restricted</h1>
      <p class="text-gray-600">The REC Management module is only available to certified RSU officers.</p>
    </div>
  {:else}
    <div class="max-w-7xl mx-auto space-y-8">
      <!-- Header -->
      <header class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl shadow-lg p-8">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <p class="text-xs uppercase tracking-[0.3em] text-amber-600 font-semibold mb-1">Institutional Integrity</p>
            <h1 class="text-3xl md:text-4xl font-bold text-gray-900">REC Management Hub</h1>
            <p class="text-gray-600 mt-1 text-sm">Oversee Research Ethics Committee meetings, certifications, and compliance registry.</p>
          </div>
          
          <!-- Stats Summary -->
          <div class="flex gap-3 flex-wrap">
            <div class="px-5 py-3 bg-blue-50 border border-blue-100 rounded-2xl text-center">
              <p class="text-xs text-blue-600 font-bold uppercase">Meeting Queue</p>
              <p class="text-2xl font-black text-blue-900">{meetingNeeded.length}</p>
            </div>
            <div class="px-5 py-3 bg-rose-50 border border-rose-100 rounded-2xl text-center">
              <p class="text-xs text-rose-600 font-bold uppercase">Renewals</p>
              <p class="text-2xl font-black text-rose-900">{renewalReviews.length}</p>
            </div>
            <div class="px-5 py-3 bg-amber-50 border border-amber-100 rounded-2xl text-center">
              <p class="text-xs text-amber-600 font-bold uppercase">Fresh Reviews</p>
              <p class="text-2xl font-black text-amber-900">{freshReviews.length}</p>
            </div>
          </div>
        </div>
      </header>

      <!-- Main Workspace -->
      <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        <!-- Sidebar Navigation -->
        <aside class="space-y-2">
          <button 
            class={`w-full px-5 py-4 rounded-2xl text-left font-bold transition-all flex items-center justify-between ${activeTab === 'meetings' ? 'bg-amber-600 text-white shadow-lg shadow-amber-200' : 'bg-white/70 hover:bg-white text-gray-700'}`}
            on:click={() => activeTab = 'meetings'}
          >
            <div class="flex items-center gap-3">
              <Icon name="calendar" size={20} />
              <span>Meeting Manager</span>
            </div>
            {#if meetingNeeded.length > 0}
              <span class={`px-2 py-0.5 rounded-full text-[10px] ${activeTab === 'meetings' ? 'bg-white text-amber-600' : 'bg-amber-100 text-amber-700'}`}>{meetingNeeded.length}</span>
            {/if}
          </button>
          
          <button 
            class={`w-full px-5 py-4 rounded-2xl text-left font-bold transition-all flex items-center justify-between ${activeTab === 'reviews' ? 'bg-amber-600 text-white shadow-lg shadow-amber-200' : 'bg-white/70 hover:bg-white text-gray-700'}`}
            on:click={() => activeTab = 'reviews'}
          >
            <div class="flex items-center gap-3">
              <Icon name="document" size={20} />
              <span>Review Queue</span>
            </div>
            <div class="flex items-center gap-1">
              {#if renewalReviews.length > 0}
                <span class={`px-2 py-0.5 rounded-full text-[10px] font-black ${activeTab === 'reviews' ? 'bg-white text-rose-600' : 'bg-rose-100 text-rose-700'}`}>{renewalReviews.length}R</span>
              {/if}
              {#if freshReviews.length > 0}
                <span class={`px-2 py-0.5 rounded-full text-[10px] ${activeTab === 'reviews' ? 'bg-white text-amber-600' : 'bg-amber-100 text-amber-700'}`}>{freshReviews.length}</span>
              {/if}
            </div>
          </button>

          <button 
            class={`w-full px-5 py-4 rounded-2xl text-left font-bold transition-all flex items-center gap-3 ${activeTab === 'registry' ? 'bg-amber-600 text-white shadow-lg shadow-amber-200' : 'bg-white/70 hover:bg-white text-gray-700'}`}
            on:click={() => activeTab = 'registry'}
          >
            <Icon name="search" size={20} />
            <span>Ethics Registry</span>
          </button>

          <div class="pt-6">
            <div class="p-4 bg-amber-50 border border-amber-100 rounded-2xl">
              <h3 class="text-xs font-bold text-amber-800 uppercase mb-2">Institutional Rules</h3>
              <p class="text-[10px] text-amber-700 leading-relaxed">
                All grants involving human subjects, animals, or hazardous materials must be cleared by REC before any funds are released.
              </p>
            </div>
          </div>
        </aside>

        <!-- Content Area -->
        <main class="lg:col-span-3">
          <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl shadow-md p-8 min-h-[600px]">
            
            {#if activeTab === 'meetings'}
              <div class="space-y-6">
                <header>
                  <h2 class="text-2xl font-bold text-gray-900">Meeting Manager</h2>
                  <p class="text-sm text-gray-500">Grants awaiting formal Research Ethics Committee review.</p>
                </header>

                {#if ethicsLoading}
                   <div class="py-20 text-center text-gray-500">
                     <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600 mx-auto mb-2"></div>
                     <p>Refreshing queue...</p>
                   </div>
                {:else if meetingNeeded.length === 0}
                  <div class="py-20 text-center bg-gray-50/50 rounded-3xl border border-dashed border-gray-200">
                    <p class="text-gray-400 font-medium font-italic">No meetings currently scheduled.</p>
                  </div>
                {:else}
                  <div class="grid gap-4">
                    {#each meetingNeeded as grant}
                      <div class="p-6 rounded-2xl border border-blue-100 bg-blue-50/20 flex flex-col md:flex-row justify-between gap-6 hover:shadow-md transition-shadow">
                        <div class="flex-1">
                          <div class="flex items-center gap-3 mb-2">
                             <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 uppercase tracking-widest">Meeting Needed</span>
                             <h3 class="text-lg font-bold text-gray-900">{grant.title}</h3>
                          </div>
                          <div class="grid grid-cols-2 gap-4 text-xs text-gray-600">
                            <p><span class="text-gray-400 uppercase font-semibold">Grant Code:</span> {grant.grant_code}</p>
                            <p><span class="text-gray-400 uppercase font-semibold">Total Budget:</span> {grant.currency} {grant.total_budget?.toLocaleString()}</p>
                          </div>
                        </div>
                        <div class="flex items-center gap-3">
                          <button 
                            class="px-5 py-3 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 transition-colors shadow-lg shadow-blue-100"
                            on:click={() => handleVerifyEthics(grant.id)}
                          >
                            Conduct Meeting & Verify
                          </button>
                        </div>
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>

            {:else if activeTab === 'reviews'}
              <div class="space-y-6">
                <header>
                  <h2 class="text-2xl font-bold text-gray-900">Certificate Review Queue</h2>
                  <p class="text-sm text-gray-500">Verify certificates uploaded by PIs for active oversight.</p>
                </header>

                {#if ethicsLoading}
                   <div class="py-20 text-center text-gray-500">
                     <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600 mx-auto mb-2"></div>
                     <p>Refreshing queue...</p>
                   </div>
                {:else if reviewsNeeded.length === 0}
                  <div class="py-20 text-center bg-gray-50/50 rounded-3xl border border-dashed border-gray-200">
                    <p class="text-gray-400 font-medium font-italic">All certificate reviews are complete.</p>
                  </div>
                {:else}
                  <!-- Gap 3: Renewals (urgent) shown first with distinct rose styling -->
                  {#if renewalReviews.length > 0}
                    <div class="mb-4">
                      <p class="text-[10px] font-black uppercase tracking-widest text-rose-600 mb-3 flex items-center gap-2">
                        <span class="inline-block w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
                        Post-Expiry Renewals — Grant Currently Suspended
                      </p>
                      <div class="grid gap-4">
                        {#each renewalReviews as grant}
                          <div class="p-6 rounded-2xl border-2 border-rose-200 bg-rose-50/30 flex flex-col md:flex-row justify-between gap-6 hover:shadow-md transition-shadow">
                            <div class="flex-1">
                              <div class="flex items-center gap-3 mb-2 flex-wrap">
                                <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 uppercase tracking-widest">🔄 RENEWAL</span>
                                <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 uppercase tracking-widest">{grant.ethics_status}</span>
                                <h3 class="text-lg font-bold text-gray-900">{grant.title}</h3>
                              </div>
                              <div class="grid grid-cols-2 gap-x-8 gap-y-2 text-xs text-gray-600">
                                <p><span class="text-gray-400 uppercase font-semibold">Grant Code:</span> {grant.grant_code}</p>
                                <p><span class="text-gray-400 uppercase font-semibold">New Approval #:</span> {grant.ethics_approval_number || 'TBD'}</p>
                                <p><span class="text-gray-400 uppercase font-semibold">New Expiry Date:</span> {grant.ethics_expiry_date || 'TBD'}</p>
                                <div class="flex items-center gap-2">
                                  <span class="text-gray-400 uppercase font-semibold">Certificate:</span>
                                  {#if grant.ethics_certificate_filename}
                                    <a href={`/api/uploads/ethics/${grant.ethics_certificate_filename}`} target="_blank" class="text-blue-600 font-bold hover:underline">📄 View PDF</a>
                                  {:else}
                                    <span class="italic text-red-500">No file uploaded</span>
                                  {/if}
                                </div>
                              </div>
                            </div>
                            <div class="flex items-center gap-3">
                              <button
                                class="px-4 py-2 bg-rose-50 text-rose-700 rounded-xl text-xs font-bold hover:bg-rose-100 shadow-sm"
                                on:click={() => handleRejectEthics(grant.id)}
                              >Reject</button>
                              <button
                                class="px-4 py-2 bg-emerald-600 text-white rounded-xl text-xs font-bold hover:bg-emerald-700 transition-colors shadow-lg shadow-emerald-100"
                                on:click={() => handleVerifyEthics(grant.id)}
                              >Verify & Reinstate</button>
                            </div>
                          </div>
                        {/each}
                      </div>
                    </div>
                  {/if}

                  <!-- Fresh (first-time) submissions -->
                  {#if freshReviews.length > 0}
                    {#if renewalReviews.length > 0}
                      <p class="text-[10px] font-black uppercase tracking-widest text-amber-600 mb-3">New Submissions</p>
                    {/if}
                    <div class="grid gap-4">
                      {#each freshReviews as grant}
                        <div class="p-6 rounded-2xl border border-amber-100 bg-amber-50/20 flex flex-col md:flex-row justify-between gap-6 hover:shadow-md transition-shadow">
                          <div class="flex-1">
                            <div class="flex items-center gap-3 mb-2">
                              <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 uppercase tracking-widest">{grant.ethics_status}</span>
                              <h3 class="text-lg font-bold text-gray-900">{grant.title}</h3>
                            </div>
                            <div class="grid grid-cols-2 gap-x-8 gap-y-2 text-xs text-gray-600">
                              <p><span class="text-gray-400 uppercase font-semibold">Approval #:</span> {grant.ethics_approval_number || 'TBD'}</p>
                              <p><span class="text-gray-400 uppercase font-semibold">Expiry Date:</span> {grant.ethics_expiry_date || 'TBD'}</p>
                              <div class="flex items-center gap-2">
                                <span class="text-gray-400 uppercase font-semibold">Certificate:</span>
                                {#if grant.ethics_certificate_filename}
                                  <a href={`/api/uploads/ethics/${grant.ethics_certificate_filename}`} target="_blank" class="text-blue-600 font-bold hover:underline">📄 View PDF</a>
                                {:else}
                                  <span class="italic">No file</span>
                                {/if}
                              </div>
                            </div>
                          </div>
                          <div class="flex items-center gap-3">
                            <button
                              class="px-4 py-2 bg-rose-50 text-rose-700 rounded-xl text-xs font-bold hover:bg-rose-100 shadow-sm"
                              on:click={() => handleRejectEthics(grant.id)}
                            >Reject</button>
                            <button
                              class="px-4 py-2 bg-emerald-600 text-white rounded-xl text-xs font-bold hover:bg-emerald-700 transition-colors shadow-lg shadow-emerald-100"
                              on:click={() => handleVerifyEthics(grant.id)}
                            >Verify & Unlock</button>
                          </div>
                        </div>
                      {/each}
                    </div>
                  {/if}
                {/if}
              </div>

            {:else if activeTab === 'registry'}
              <div class="space-y-6">
                <header class="flex justify-between items-end">
                  <div>
                    <h2 class="text-2xl font-bold text-gray-900">Ethics Registry</h2>
                    <p class="text-sm text-gray-500">Comprehensive list of all projects requiring ethical oversight.</p>
                  </div>
                  <div class="relative min-w-[300px]">
                    <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400 pointer-events-none">
                      <Icon name="search" size={16} />
                    </span>
                    <input 
                      type="text" 
                      placeholder="Search grants or codes..." 
                      class="w-full pl-10 pr-4 py-2 bg-gray-100 border-none rounded-xl text-sm focus:ring-2 focus:ring-amber-500"
                      bind:value={searchTerm}
                    />
                  </div>
                </header>

                <div class="overflow-x-auto">
                  <table class="w-full text-sm text-left">
                    <thead>
                      <tr class="text-xs text-gray-400 uppercase tracking-wider border-b border-gray-100">
                        <th class="px-4 py-3 font-semibold">Grant / Code</th>
                        <th class="px-4 py-3 font-semibold text-center">Status</th>
                        <th class="px-4 py-3 font-semibold">Approval #</th>
                        <th class="px-4 py-3 font-semibold">Expiry</th>
                        <th class="px-4 py-3 font-semibold text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-50 font-medium">
                      {#each filteredRegistry as grant}
                        <tr class="hover:bg-gray-50/50 transition-colors">
                          <td class="px-4 py-4">
                            <p class="text-gray-900 font-bold">{grant.title}</p>
                            <p class="text-[10px] text-gray-400">{grant.grant_code}</p>
                          </td>
                          <td class="px-4 py-4 text-center">
                            <span class={`px-2 py-0.5 rounded-full text-[10px] uppercase font-bold ${getStatusColor(grant.ethics_status)}`}>
                              {grant.ethics_status?.replace('_', ' ')}
                            </span>
                          </td>
                          <td class="px-4 py-4 text-gray-600">{grant.ethics_approval_number || '—'}</td>
                          <td class="px-4 py-4 text-gray-600">{grant.ethics_expiry_date || '—'}</td>
                          <td class="px-4 py-4 text-right">
                             <button class="p-2 hover:bg-amber-100 rounded-lg text-amber-600" title="Edit Metadata">
                               <Icon name="edit" size={14} />
                             </button>
                          </td>
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                </div>
              </div>
            {/if}

          </div>
        </main>
      </div>
    </div>
  {/if}
</Layout>
