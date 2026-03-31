<script>
  import { onMount } from 'svelte';
  import { showToast } from '../stores/toast.js';
  import Layout from '../components/Layout.svelte';
  import Icon from '../components/Icon.svelte';
  import AssetRequestModal from '../components/AssetRequestModal.svelte';
  import AssetMaintenanceModal from '../components/AssetMaintenanceModal.svelte';
  import { user } from '../stores/auth.js';
  import { router } from '../stores/router.js';

  let assets = [];
  let loading = true;
  let error = null;
  let selectedGrant = null;
  let grantAssets = [];
  let statistics = null;
  let showRequestModal = false;
  let selectedAsset = null;
  let showMaintenanceModal = false;
  let statusFilter = '';
  let userGrants = [];

  onMount(async () => {
    await loadUserGrants();
    if (userGrants.length > 0) {
      selectedGrant = userGrants[0];
      await loadAssets();
      await loadStatistics();
    }
  });

  async function loadUserGrants() {
    try {
      const response = await fetch('/api/grants', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });

      if (response.ok) {
        const text = await response.text();
        console.log('Raw response:', text);
        try {
          const data = JSON.parse(text);
          userGrants = data.grants || [];
        } catch (jsonErr) {
          console.error('Failed to parse JSON:', jsonErr);
          console.error('Response text:', text);
          error = 'Invalid response from server';
        }
      } else {
        console.error('Response not ok:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('Error response:', errorText);
        error = `Failed to load grants: ${response.status}`;
      }
    } catch (err) {
      console.error('Failed to load grants:', err);
      error = 'Network error loading grants';
    }
  }

  async function loadAssets() {
    if (!selectedGrant) return;
    
    loading = true;
    error = null;

    try {
      const url = statusFilter 
        ? `/api/assets/grant/${selectedGrant.id}?status=${statusFilter}`
        : `/api/assets/grant/${selectedGrant.id}`;
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });

      if (response.ok) {
        const data = await response.json();
        grantAssets = data.assets || [];
      } else {
        error = 'Failed to load assets';
      }
    } catch (err) {
      error = 'Network error loading assets';
      console.error('Assets error:', err);
    } finally {
      loading = false;
    }
  }

  async function loadStatistics() {
    if (!selectedGrant) return;

    try {
      const response = await fetch(`/api/assets/statistics/grant/${selectedGrant.id}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });

      if (response.ok) {
        statistics = await response.json();
      }
    } catch (err) {
      console.error('Failed to load statistics:', err);
    }
  }

  function getStatusColor(status) {
    switch (status) {
      case 'ACTIVE': return 'text-green-600 bg-green-100';
      case 'IN_REPAIR': return 'text-yellow-600 bg-yellow-100';
      case 'LENDED': return 'text-blue-600 bg-blue-100';
      case 'RETURNED': return 'text-gray-600 bg-gray-100';
      case 'TRANSFERRED': return 'text-purple-600 bg-purple-100';
      case 'DISPOSED': return 'text-red-600 bg-red-100';
      case 'LOST': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  }

  function getSourceTypeColor(sourceType) {
    switch (sourceType) {
      case 'PURCHASED': return 'text-blue-600 bg-blue-100';
      case 'LENDED': return 'text-orange-600 bg-orange-100';
      case 'UNIVERSITY_OWNED': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  }

  function getDaysUntilReturn(returnDate) {
    if (!returnDate) return null;
    const days = Math.ceil((new Date(returnDate) - new Date()) / (1000 * 60 * 60 * 24));
    return days;
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

  function handleAssetSubmitted() {
    closeRequestModal();
    loadAssets();
    loadStatistics();
    showToast('Asset request submitted successfully!');
  }

  function openAssetDetails(asset) {
    selectedAsset = asset;
  }

  function closeAssetDetails() {
    selectedAsset = null;
  }

  function openRequestModal() {
    showRequestModal = true;
  }

  function closeRequestModal() {
    showRequestModal = false;
  }

  function openMaintenanceModal(asset) {
    selectedAsset = asset;
    showMaintenanceModal = true;
  }

  function closeMaintenanceModal() {
    showMaintenanceModal = false;
    selectedAsset = null;
  }

  function handleMaintenanceCompleted() {
    closeMaintenanceModal();
    loadAssets(); // Refresh to show updated maintenance dates
    showToast('Maintenance recorded successfully!');
  }

  async function handleGrantChange() {
    await loadAssets();
    await loadStatistics();
  }

  function handleStatusFilter() {
    // The assets will be automatically filtered in the template based on statusFilter
    // This function can be used for additional filtering logic if needed
  }
</script>

<Layout>
  <div class="max-w-7xl mx-auto space-y-6">
    <!-- Header -->
    <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Asset Management</h1>
          <p class="text-gray-600 mt-1">Track and manage grant equipment and assets</p>
        </div>
        <button
          on:click={openRequestModal}
          class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
        >
          Request Asset
        </button>
      </div>
    </div>

    <!-- Grant Selection & Statistics -->
    {#if userGrants.length > 0}
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Grant Selector -->
        <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">Select Grant</h2>
          <select 
            bind:value={selectedGrant} 
            on:change={handleGrantChange}
            class="w-full border border-gray-300 rounded px-3 py-2"
          >
            {#each userGrants as grant}
              <option value={grant}>{grant.title} ({grant.grant_code})</option>
            {/each}
          </select>
        </div>

        <!-- Statistics -->
        {#if statistics}
          <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6 lg:col-span-2">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Asset Overview</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="text-center">
                <div class="text-2xl font-bold text-blue-600">{statistics.total_assets}</div>
                <div class="text-sm text-gray-600">Total Assets</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-green-600">{statistics.status_breakdown?.ACTIVE || 0}</div>
                <div class="text-sm text-gray-600">Active</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-yellow-600">{statistics.overdue_returns || 0}</div>
                <div class="text-sm text-gray-600">Overdue Returns</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-purple-600">{formatCurrency(statistics.total_value)}</div>
                <div class="text-sm text-gray-600">Total Value</div>
              </div>
            </div>
          </div>
        {/if}
      </div>

      <!-- Filters and Asset List -->
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-lg font-semibold text-gray-900">Assets</h2>
          <div class="flex items-center space-x-4">
            <select 
              bind:value={statusFilter} 
              on:change={handleStatusFilter}
              class="border border-gray-300 rounded px-3 py-2"
            >
              <option value="">All Statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="IN_REPAIR">In Repair</option>
              <option value="LENDED">Lended</option>
              <option value="RETURNED">Returned</option>
              <option value="TRANSFERRED">Transferred</option>
              <option value="DISPOSED">Disposed</option>
            </select>
          </div>
        </div>

        {#if loading}
          <div class="text-center py-12">
            <div class="animate-spin h-8 w-8 mx-auto border-b-2 border-blue-600"></div>
            <p class="mt-2 text-gray-500">Loading assets...</p>
          </div>
        {:else if error}
          <div class="text-center py-12">
            <div class="text-red-500 mb-4">
              <svg class="h-12 w-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
            <p class="text-gray-500">{error}</p>
          </div>
        {:else if grantAssets.length === 0}
          <div class="text-center py-12">
            <svg class="h-12 w-12 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
            </svg>
            <p class="text-gray-500 mt-2">No assets found for this grant</p>
            <button 
              on:click={openRequestModal}
              class="mt-4 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Request First Asset
            </button>
          </div>
        {:else}
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-white/50 border-b border-white/60 backdrop-blur-sm">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asset</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Custodian</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Return Date</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200">
                {#each grantAssets as asset}
                  <tr>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="flex items-start space-x-3">
                        <div class="flex-shrink-0">
                          <Icon name="asset" size={20} className="text-gray-400" />
                        </div>
                        <div>
                          <div class="text-sm font-medium text-gray-900">{asset.name}</div>
                          <div class="text-sm text-gray-500">Tag: {asset.asset_tag || 'N/A'}</div>
                          {#if asset.serial_number}
                            <div class="text-xs text-gray-400">S/N: {asset.serial_number}</div>
                          {/if}
                        </div>
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div>
                        <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full {getSourceTypeColor(asset.source_type)}">
                          {asset.source_type}
                        </span>
                        {#if asset.owner_name}
                          <div class="text-sm text-gray-500 mt-1">{asset.owner_name}</div>
                        {/if}
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {asset.custodian ? asset.custodian.name : 'Unassigned'}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full {getStatusColor(asset.status)}">
                        {asset.status}
                      </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(asset.purchase_cost)}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {#if asset.expected_return_date}
                        {@const daysUntil = getDaysUntilReturn(asset.expected_return_date)}
                        {#if daysUntil <= 0}
                          <span class="text-red-600 font-medium">Overdue</span>
                        {:else if daysUntil <= 7}
                          <span class="text-yellow-600 font-medium">{daysUntil} days</span>
                        {:else}
                          {formatDate(asset.expected_return_date)}
                        {/if}
                      {:else}
                        N/A
                      {/if}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button 
                        on:click={() => openAssetDetails(asset)}
                        class="text-blue-600 hover:text-blue-900 mr-3"
                      >
                        View
                      </button>
                      <button 
                        on:click={() => openMaintenanceModal(asset)}
                        class="text-green-600 hover:text-green-900 mr-3"
                      >
                        Maintenance
                      </button>
                      {#if asset.status === 'ACTIVE'}
                        <button class="text-orange-600 hover:text-orange-900">
                          Return
                        </button>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>
    {:else}
      <div class="bg-white/40 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-12 text-center">
        <svg class="h-12 w-12 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
        <p class="text-gray-500 mt-2">No grants found</p>
        <p class="text-sm text-gray-400 mt-1">You need to be assigned to a grant to manage assets</p>
      </div>
    {/if}

    <!-- Asset Details Modal -->
    {#if selectedAsset}
      <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div class="relative top-20 mx-auto p-5 border border-white/60 w-96 shadow-2xl rounded-2xl bg-white/90 backdrop-blur-2xl">
          <div class="mt-3">
            <h3 class="text-lg font-medium text-gray-900 mb-4">Asset Details</h3>
            
            <div class="space-y-3">
              <div>
                <label class="text-sm font-medium text-gray-700">Name</label>
                <p class="text-gray-900">{selectedAsset.name}</p>
              </div>
              
              <div>
                <label class="text-sm font-medium text-gray-700">Asset Tag</label>
                <p class="text-gray-900">{selectedAsset.asset_tag || 'N/A'}</p>
              </div>
              
              <div>
                <label class="text-sm font-medium text-gray-700">Status</label>
                <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full {getStatusColor(selectedAsset.status)}">
                  {selectedAsset.status}
                </span>
              </div>
              
              <div>
                <label class="text-sm font-medium text-gray-700">Source</label>
                <p class="text-gray-900">{selectedAsset.source_type}</p>
                {#if selectedAsset.owner_name}
                  <p class="text-sm text-gray-500">{selectedAsset.owner_name}</p>
                {/if}
              </div>
              
              <div>
                <label class="text-sm font-medium text-gray-700">Value</label>
                <p class="text-gray-900">{formatCurrency(selectedAsset.purchase_cost)}</p>
              </div>
              
              {#if selectedAsset.custodian}
                <div>
                  <label class="text-sm font-medium text-gray-700">Custodian</label>
                  <p class="text-gray-900">{selectedAsset.custodian.name}</p>
                </div>
              {/if}
              
              {#if selectedAsset.description}
                <div>
                  <label class="text-sm font-medium text-gray-700">Description</label>
                  <p class="text-gray-900">{selectedAsset.description}</p>
                </div>
              {/if}
            </div>
            
            <div class="flex justify-end space-x-3 mt-6">
              <button 
                on:click={closeAssetDetails}
                class="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    {/if}

    <!-- Asset Request Modal -->
    {#if showRequestModal}
      <AssetRequestModal 
        show={showRequestModal}
        grant={selectedGrant}
        user={$user}
        on:close={closeRequestModal}
        on:submitted={handleAssetSubmitted}
      />
    {/if}

    <!-- Asset Maintenance Modal -->
    {#if showMaintenanceModal}
      <AssetMaintenanceModal 
        show={showMaintenanceModal}
        asset={selectedAsset}
        user={$user}
        on:close={closeMaintenanceModal}
        on:completed={handleMaintenanceCompleted}
      />
    {/if}
  </div>
</Layout>

<style>
  /* Add any specific styles for the Assets page */
</style>
