<script>
  import { onMount } from 'svelte';
  import Layout from '../components/Layout.svelte';
  import axios from 'axios';
  import Icon from '../components/Icon.svelte';

  let assets = [];
  let loading = true;
  let error = null;
  let returnModalOpen = false;
  let selectedAsset = null;
  let returnNote = '';
  let returnFile = null;
  let submitting = false;
  let successMsg = null;

  onMount(async () => {
    await fetchInventory();
  });

  async function fetchInventory() {
    loading = true;
    error = null;
    try {
      const res = await axios.get('/api/me/my-inventory', { withCredentials: true });
      assets = res.data.assets || [];
    } catch (e) {
      error = 'Could not load your inventory. Please try again.';
    } finally {
      loading = false;
    }
  }

  function daysUntilReturn(dateStr) {
    if (!dateStr) return null;
    const now = new Date(); now.setHours(0,0,0,0);
    const d = new Date(dateStr); d.setHours(0,0,0,0);
    return Math.round((d - now) / (1000 * 60 * 60 * 24));
  }

  function returnDaysClass(days) {
    if (days === null) return 'text-gray-400';
    if (days < 0) return 'text-red-600 font-bold animate-pulse';
    if (days <= 2) return 'text-red-500 font-semibold';
    if (days <= 7) return 'text-orange-500 font-semibold';
    return 'text-green-600';
  }

  function returnDaysLabel(days) {
    if (days === null) return 'No return date';
    if (days < 0) return `${Math.abs(days)} day${Math.abs(days) !== 1 ? 's' : ''} OVERDUE`;
    if (days === 0) return 'Return today!';
    if (days === 1) return 'Return tomorrow';
    return `Return in ${days} days`;
  }

  function openReturnModal(asset) {
    selectedAsset = asset;
    returnNote = '';
    returnFile = null;
    returnModalOpen = true;
    successMsg = null;
  }

  function closeModal() {
    returnModalOpen = false;
    selectedAsset = null;
  }

  async function submitReturn() {
    if (!selectedAsset) return;
    submitting = true;
    try {
      const formData = new FormData();
      formData.append('notes', returnNote);
      if (returnFile) formData.append('proof', returnFile);

      await axios.put(`/api/assets/${selectedAsset.id}/status`,
        { status: 'RETURNED', notes: `Returned by user. ${returnNote}` },
        { withCredentials: true }
      );

      successMsg = `${selectedAsset.name} marked as returned.`;
      closeModal();
      await fetchInventory();
    } catch (e) {
      alert('Failed to mark asset as returned. Please try again.');
    } finally {
      submitting = false;
    }
  }

  function formatDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  }

  function onFileChange(e) {
    returnFile = e.target.files[0] || null;
  }
</script>

<Layout>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-8">
      <div class="h-12 w-12 rounded-2xl bg-gradient-to-br from-orange-400 to-pink-500 flex items-center justify-center text-white shadow-lg">
        <Icon name="asset" size={28} />
      </div>
      <div>
        <h1 class="text-3xl font-black text-gray-900">My Inventory</h1>
        <p class="text-gray-500 text-sm">Equipment and assets currently in your custody.</p>
      </div>
    </div>

    {#if successMsg}
      <div class="mb-6 bg-green-50 border border-green-200 text-green-700 rounded-2xl px-5 py-4 text-sm font-semibold flex items-center gap-2">
        <Icon name="check-circle" size={18} />
        <span>{successMsg}</span>
      </div>
    {/if}

    {#if loading}
      <div class="grid gap-4">
        {#each [1,2,3] as _}
          <div class="h-32 bg-gray-100 rounded-2xl animate-pulse"></div>
        {/each}
      </div>
    {:else if error}
      <div class="bg-red-50 border border-red-200 rounded-2xl p-6 text-center text-red-600">{error}</div>
    {:else if assets.length === 0}
      <div class="text-center py-20 bg-white/60 backdrop-blur-xl rounded-3xl border border-white/40 shadow flex flex-col items-center">
        <div class="text-gray-300 mb-3">
          <Icon name="asset" size={64} />
        </div>
        <h3 class="font-bold text-gray-700 text-xl">No Equipment in Custody</h3>
        <p class="text-gray-500 text-sm mt-1">You currently have no assets checked out to you.</p>
      </div>
    {:else}
      <!-- Stats -->
      {@const overdue = assets.filter(a => { const d = daysUntilReturn(a.expected_return_date); return d !== null && d < 0; })}
      {#if overdue.length > 0}
        <div class="mb-6 flex items-center gap-3 bg-gradient-to-r from-red-500 to-pink-500 text-white rounded-2xl px-5 py-4 shadow-lg">
          <Icon name="alert-triangle" size={28} />
          <div>
            <p class="font-bold">{overdue.length} overdue item{overdue.length > 1 ? 's' : ''}!</p>
            <p class="text-xs text-red-100">Please arrange return immediately to avoid a flag on your account.</p>
          </div>
        </div>
      {/if}

      <div class="grid gap-5">
        {#each assets as asset}
          {@const days = daysUntilReturn(asset.expected_return_date)}
          <div class="bg-white/80 backdrop-blur-xl border border-white/50 rounded-2xl shadow-sm hover:shadow-md transition-all p-6 flex flex-col sm:flex-row sm:items-center gap-5">
            <!-- Asset Icon / Category -->
            <div class="h-16 w-16 rounded-2xl bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center flex-shrink-0 shadow-lg text-white">
              <Icon name={
                asset.category === 'Vehicle' ? 'truck' :
                asset.category === 'IT Equipment' ? 'laptop' :
                asset.category === 'Lab Equipment' ? 'microscope' :
                'asset'
              } size={32} />
            </div>

            <!-- Details -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1 flex-wrap">
                <h3 class="font-bold text-gray-900 text-lg">{asset.name}</h3>
                <span class="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">{asset.category || 'General'}</span>
              </div>
              <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-500 mt-2">
                <span class="flex items-center gap-1"><Icon name="tag" size={12} /> Tag: <strong class="text-gray-700">{asset.asset_tag || '—'}</strong></span>
                <span class="flex items-center gap-1"><Icon name="hash" size={12} /> Serial: <strong class="text-gray-700">{asset.serial_number || '—'}</strong></span>
                <span class="flex items-center gap-1"><Icon name="calendar" size={12} /> Checked Out: <strong class="text-gray-700">{formatDate(asset.assigned_at || asset.purchase_date)}</strong></span>
                <span class="flex items-center gap-1"><Icon name="calendar" size={12} /> Return By: <strong class="text-gray-700">{formatDate(asset.expected_return_date)}</strong></span>
              </div>
            </div>

            <!-- Return Status & Action -->
            <div class="flex flex-col items-end gap-3 flex-shrink-0">
              <span class="text-sm {returnDaysClass(days)}">
                {returnDaysLabel(days)}
              </span>
              <button
                onclick={() => openReturnModal(asset)}
                class="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-sm font-semibold rounded-xl hover:opacity-90 active:scale-95 transition-all shadow"
              >
                Mark as Returned
              </button>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</Layout>

<!-- Return Modal -->
{#if returnModalOpen && selectedAsset}
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
    <div class="bg-white rounded-3xl shadow-2xl max-w-md w-full p-8 animate-in zoom-in duration-200">
      <div class="flex items-center gap-3 mb-6">
        <div class="h-12 w-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white">
          <Icon name="asset" size={24} />
        </div>
        <div>
          <h2 class="text-xl font-black text-gray-900">Confirm Return</h2>
          <p class="text-sm text-gray-500">{selectedAsset.name}</p>
        </div>
      </div>

      <div class="space-y-4">
        <div>
          <label for="return-notes" class="block text-sm font-semibold text-gray-700 mb-2">Handover Notes (optional)</label>
          <textarea
            id="return-notes"
            bind:value={returnNote}
            rows="3"
            placeholder="e.g. Returned in good condition to lab office..."
            class="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 outline-none resize-none"
          ></textarea>
        </div>

        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2 flex items-center gap-1">Proof of Return <Icon name="camera" size={14} /></label>
          <label for="return-proof" class="flex items-center justify-center gap-2 w-full border-2 border-dashed border-gray-200 rounded-xl p-4 cursor-pointer hover:border-indigo-400 hover:bg-indigo-50 transition-all text-sm text-gray-500">
            <Icon name="document" size={16} />
            <span>{returnFile ? returnFile.name : 'Upload photo or PDF of handover'}</span>
            <input id="return-proof" type="file" accept="image/*,.pdf" onchange={onFileChange} class="hidden" />
          </label>
        </div>
      </div>

      <div class="flex gap-3 mt-6">
        <button
          onclick={closeModal}
          class="flex-1 py-3 rounded-xl border border-gray-200 text-gray-600 text-sm font-semibold hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
          <button
            onclick={submitReturn}
            disabled={submitting}
            class="flex-1 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-sm font-bold hover:opacity-90 disabled:opacity-50 transition-all shadow flex items-center justify-center gap-2"
          >
            {#if !submitting}<Icon name="check" size={18} />{/if}
            {submitting ? 'Submitting...' : 'Confirm Return'}
          </button>
      </div>
    </div>
  </div>
{/if}

<style>
  :global(body) { font-family: 'Inter', sans-serif; }
</style>
