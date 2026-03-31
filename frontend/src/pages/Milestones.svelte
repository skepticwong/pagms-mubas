<script>
  import { onMount } from "svelte";
  import axios from "axios";
  import Layout from "../components/Layout.svelte";
  import MilestonesTab from "../components/MilestonesTab.svelte";
  import Icon from "../components/Icon.svelte";

  axios.defaults.withCredentials = true;

  let grants = [];
  let selectedGrantId = null;
  let loading = true;

  async function fetchGrants() {
    try {
      const res = await axios.get("http://localhost:5000/api/grants");
      grants = res.data.grants || [];
      if (grants.length > 0) {
        selectedGrantId = grants[0].id;
      }
    } catch (error) {
      console.error("Error fetching grants for milestones page:", error);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchGrants();
  });

  $: selectedGrant = grants.find(g => g.id === selectedGrantId) || null;
</script>

<Layout>
  <div class="max-w-6xl mx-auto space-y-8 py-6 px-4">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
      <div class="space-y-2">
        <h1 class="text-4xl font-extrabold text-gray-900 tracking-tight flex items-center gap-3">
          <Icon name="mission" size={36} color="#2563eb" />
          Milestone Management
        </h1>
        <p class="text-lg text-gray-600 max-w-2xl">
          Track and manage project milestones, tranche triggers, and progress across all your grants.
        </p>
      </div>
    </div>

    {#if loading}
      <div class="flex flex-col items-center justify-center py-20 space-y-4">
        <div class="w-12 h-12 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin"></div>
        <p class="text-gray-500 font-medium tracking-wide">Loading projects...</p>
      </div>
    {:else if grants.length === 0}
      <div class="bg-white/60 backdrop-blur-xl border border-white/40 rounded-3xl p-12 text-center shadow-xl">
        <div class="w-20 h-20 bg-blue-50 text-blue-400 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <Icon name="folder" size={40} />
        </div>
        <h2 class="text-2xl font-bold text-gray-900 mb-2">No Active Grants Found</h2>
        <p class="text-gray-600 max-w-md mx-auto">
          You don't have any active grants assigned. Milestones are managed per grant project.
        </p>
      </div>
    {:else}
      <!-- Grant Selector -->
      <div class="bg-white/60 backdrop-blur-xl border border-white/40 rounded-3xl p-6 shadow-xl space-y-4">
        <label for="grant-selector" class="block text-sm font-black text-gray-500 uppercase tracking-widest ml-1">
          Select Project to Manage
        </label>
        <div class="flex flex-col md:flex-row gap-4">
          <select
            id="grant-selector"
            bind:value={selectedGrantId}
            class="flex-1 bg-white border border-gray-200 rounded-2xl px-6 py-4 text-lg font-semibold text-gray-900 focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none shadow-sm"
          >
            {#each grants as grant}
              <option value={grant.id}>{grant.grant_code} - {grant.title}</option>
            {/each}
          </select>
        </div>
      </div>

      <!-- Milestones Content -->
      {#if selectedGrantId}
        <div class="animate-in fade-in slide-in-from-bottom-4 duration-500">
          <MilestonesTab 
            grantId={selectedGrantId} 
            grantTitle={selectedGrant?.title || 'Selected Project'} 
            disbursementType={selectedGrant?.disbursement_type || "single"}
          />
        </div>
      {/if}
    {/if}
  </div>
</Layout>

<style>
  :global(body) {
    background-color: #f8fafc;
  }

  .animate-in {
    animation-fill-mode: both;
  }

  @keyframes slide-in-from-bottom-4 {
    from {
      transform: translateY(1rem);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
</style>
