<script>
  import { onMount } from 'svelte';
  import { showToast } from '../stores/toast.js';
  import NCERequestModal from '../components/NCERequestModal.svelte';
  import FinancialMetrics from '../components/FinancialMetrics.svelte';
  import BurnRateChart from '../components/BurnRateChart.svelte';
  import ComplianceHealthWidget from '../components/ComplianceHealthWidget.svelte';

  export let grantId = null;
  export let user = null;

  let grant = null;
  let amendments = [];
  let showNCEModal = false;
  let loading = true;
  let error = null;
  let daysRemaining = 0;

  // Ethics Reinstatement State
  let showEthicsForm = false;
  let ethicsFile = null;
  let ethicsApprovalNum = '';
  let ethicsExpiryDate = '';
  let ethicsSubmitting = false;
  let ethicsSubmitted = false;    // tracks post-submission "pending" state
  let ethicsUploadedFilename = ''; // shown as confirmation after submit

  onMount(async () => {
    if (grantId) {
      await loadGrantData();
    }
  });

  async function loadGrantData() {
    loading = true;
    error = null;

    try {
      // Use session cookies (withCredentials) — consistent with rest of the app
      const grantResponse = await fetch(`/api/grants/${grantId}`, {
        credentials: 'include'
      });

      if (grantResponse.ok) {
        grant = await grantResponse.json();

        // Calculate days remaining
        if (grant.end_date) {
          const endDate = new Date(grant.end_date);
          const today = new Date();
          daysRemaining = Math.ceil((endDate - today) / (1000 * 60 * 60 * 24));
        }

        // Load amendments
        await loadAmendments();
      } else {
        error = 'Failed to load grant data';
      }
    } catch (err) {
      error = 'Network error loading grant data';
      console.error('Grant data error:', err);
    } finally {
      loading = false;
    }
  }

  async function loadAmendments() {
    try {
      const response = await fetch(`/api/amendments/grant/${grantId}/amendments`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        amendments = data.amendments || [];
      }
    } catch (err) {
      console.error('Amendments error:', err);
    }
  }

  function openNCEModal() {
    showNCEModal = true;
  }

  function handleNCESubmitted(event) {
    showToast('Extension request submitted successfully!');
    loadAmendments(); // Refresh amendments list
  }

  function handleEthicsFileChange(e) {
    ethicsFile = e.target.files[0];
  }

  async function submitReinstatement() {
    if (!ethicsFile || !ethicsApprovalNum || !ethicsExpiryDate) {
      showToast('Please fill all ethics fields and upload the certificate.', 'error');
      return;
    }

    ethicsSubmitting = true;
    const formData = new FormData();
    formData.append('ethics_certificate', ethicsFile);
    formData.append('ethics_approval_number', ethicsApprovalNum);
    formData.append('ethics_expiry_date', ethicsExpiryDate);

    try {
      const response = await fetch(`/api/grants/${grantId}/ethics-reinstatement`, {
        method: 'PUT',
        credentials: 'include',   // session cookie auth (consistent with rest of app)
        body: formData
      });

      if (response.ok) {
        showToast('Reinstatement request submitted. Awaiting RSU verification.', 'success');
        showEthicsForm = false;
        ethicsSubmitted = true;                         // Stay on banner, show pending state
        ethicsUploadedFilename = ethicsFile.name;       // Show filename as confirmation
        await loadGrantData();
      } else {
        const errorData = await response.json();
        showToast(errorData.error || 'Failed to submit reinstatement', 'error');
      }
    } catch (err) {
      showToast('Network error during submission', 'error');
    } finally {
      ethicsSubmitting = false;
    }
  }

  function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
  }

  function getStatusColor(status) {
    switch (status) {
      case 'PENDING': return 'text-yellow-600 bg-yellow-100';
      case 'APPROVED': return 'text-green-600 bg-green-100';
      case 'REJECTED': return 'text-red-600 bg-red-100';
      case 'WITHDRAWN': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  }

  function getDaysRemainingColor(days) {
    if (days <= 30) return 'text-red-600';
    if (days <= 60) return 'text-yellow-600';
    return 'text-green-600';
  }
</script>

<div class="grant-dashboard">
  {#if loading}
    <div class="text-center py-12">
      <svg class="animate-spin h-12 w-12 mx-auto text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="text-gray-500 mt-4">Loading grant dashboard...</p>
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
  {:else if grant}
    <!-- Grant Header -->
    <div class="bg-white rounded-lg shadow-md p-6 mb-6">
      <div class="flex justify-between items-start">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">{grant.title}</h1>
          <p class="text-gray-600 mt-1">Grant Code: {grant.grant_code}</p>
          <p class="text-gray-600">Funder: {grant.funder}</p>
        </div>
        <div class="text-right">
          <div class="text-sm text-gray-600">Total Budget</div>
          <div class="text-2xl font-bold text-gray-900">
            ${new Intl.NumberFormat('en-US').format(grant.total_budget || 0)}
          </div>
        </div>
      </div>

      <!-- Grant Status Bar -->
      <div class="mt-6 pt-6 border-t grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <div class="text-sm text-gray-600">Status</div>
          <div class="font-medium text-gray-900">{grant.status}</div>
        </div>
        <div>
          <div class="text-sm text-gray-600">Start Date</div>
          <div class="font-medium text-gray-900">{formatDate(grant.start_date)}</div>
        </div>
        <div>
          <div class="text-sm text-gray-600">End Date</div>
          <div class="font-medium text-gray-900">{formatDate(grant.end_date)}</div>
        </div>
        <div>
          <div class="text-sm text-gray-600">Days Remaining</div>
          <div class="font-medium {getDaysRemainingColor(daysRemaining)}">
            {daysRemaining > 0 ? daysRemaining : 'Expired'}
          </div>
        </div>
      </div>
    </div>

    <!-- Ethics Reinstatement Status Link -->
    {#if grant.ethics_required && grant.ethics_status !== 'VERIFIED'}
      <div class="bg-amber-50 border border-amber-100 rounded-2xl p-4 mb-6 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center text-amber-600 font-bold">!</div>
          <div>
            <p class="text-sm font-bold text-amber-900">Ethics Action Required</p>
            <p class="text-xs text-amber-700">Grant compliance status is currently <strong>{grant.ethics_status?.replace('_', ' ')}</strong>.</p>
          </div>
        </div>
        <button 
          on:click={() => router.goToPIEthics()}
          class="px-4 py-2 bg-amber-600 text-white rounded-xl text-xs font-bold hover:bg-amber-700 transition-colors shadow-sm"
        >
          Go to Ethics Hub
        </button>
      </div>
    {/if}

    <!-- Dashboard Grid: Financials & Compliance -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <FinancialMetrics grantId={grantId} />
      <ComplianceHealthWidget grantId={grantId} />
    </div>

    <!-- Burn Rate Chart -->
    <div class="mb-6">
      <BurnRateChart grantId={grantId} height={250} />
    </div>

    <!-- Recent Amendments -->
    <div class="bg-white rounded-lg shadow-md p-6">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-semibold text-gray-900">Recent Amendments</h2>
        <button
          on:click={openNCEModal}
          class="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 transition-colors"
        >
          Request Extension
        </button>
      </div>

      {#if amendments.length === 0}
        <div class="text-center py-8">
          <svg class="h-12 w-12 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          <p class="text-gray-500 mt-2">No amendments requested</p>
        </div>
      {:else}
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Requested</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Extension Days</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              {#each amendments.slice(0, 5) as amendment}
                <tr>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                      {amendment.amendment_type}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(amendment.requested_at)}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full {getStatusColor(amendment.status)}">
                      {amendment.status}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {amendment.extension_days || 'N/A'}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button class="text-blue-600 hover:text-blue-900">View Details</button>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
          {#if amendments.length > 5}
            <div class="text-center py-3 border-t">
              <button class="text-blue-600 hover:text-blue-900 text-sm font-medium">
                View all {amendments.length} amendments
              </button>
            </div>
          {/if}
        </div>
      {/if}
    </div>

    <!-- NCE Modal -->
    {#if showNCEModal}
      <NCERequestModal 
        show={showNCEModal}
        grant={grant}
        user={user}
        on:close={() => showNCEModal = false}
        on:submitted={handleNCESubmitted}
      />
    {/if}
  {/if}
</div>

<style>
  .grant-dashboard {
    max-width: 7xl;
    margin: 0 auto;
    padding: 1rem;
  }
  
  .grant-dashboard .bg-white {
    transition: box-shadow 0.2s ease-in-out;
  }
  
  .grant-dashboard .bg-white:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  }
</style>
