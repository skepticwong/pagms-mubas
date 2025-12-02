<script>
  import axios from "axios";
  import { onMount } from "svelte";
  import Layout from "../components/Layout.svelte";
  import { user } from "../stores/auth.js";
  import { router } from "../stores/router.js";
  import ReportModal from "../components/ReportModal.svelte";
  import Icon from "../components/Icon.svelte";

  let grants = [];
  let isLoading = true;
  let error = "";
  let showReportModal = false;
  let reportGrant = null;

  onMount(async () => {
    if (!$user || $user.role !== "PI") {
      router.goToDashboard();
      return;
    }

    try {
      const res = await axios.get("http://localhost:5000/api/grants", {
        withCredentials: true,
      });
      grants = res.data;
    } catch (err) {
      console.error(err);
      error = "Failed to load grants for reporting.";
    } finally {
      isLoading = false;
    }
  });

  function handleGenerateReport(grant) {
    reportGrant = grant;
    showReportModal = true;
  }
</script>

<Layout>
  <div class="max-w-6xl mx-auto space-y-8">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div class="space-y-1">
        <h1 class="text-3xl font-black text-gray-900 tracking-tight">
          Reports Hub
        </h1>
        <p class="text-gray-500 font-medium">
          Select a grant to generate system-verified progress and financial
          reports.
        </p>
      </div>
    </div>

    {#if isLoading}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#each Array(3) as _}
          <div
            class="h-48 bg-white/50 border border-white/40 rounded-3xl animate-pulse"
          ></div>
        {/each}
      </div>
    {:else if error}
      <div
        class="p-8 bg-rose-50 border border-rose-100 rounded-3xl text-center space-y-3"
      >
        <div
          class="mx-auto w-12 h-12 bg-rose-100 text-rose-600 rounded-2xl flex items-center justify-center"
        >
          <Icon name="warning" size={24} />
        </div>
        <p class="text-rose-800 font-bold">{error}</p>
        <button
          on:click={() => window.location.reload()}
          class="text-sm text-rose-600 font-black uppercase tracking-widest hover:underline"
          >Retry</button
        >
      </div>
    {:else if grants.length === 0}
      <div
        class="p-16 bg-white/40 backdrop-blur-xl border border-dashed border-gray-200 rounded-[2.5rem] text-center space-y-4"
      >
        <div
          class="mx-auto w-20 h-20 bg-gray-100 text-gray-400 rounded-3xl flex items-center justify-center"
        >
          <Icon name="folder" size={40} />
        </div>
        <div class="space-y-1">
          <h3 class="text-xl font-bold text-gray-900">No Grants Found</h3>
          <p class="text-gray-500 max-w-xs mx-auto">
            You'll see your grants here once they are assigned or approved.
          </p>
        </div>
      </div>
    {:else}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#each grants as grant}
          <div
            class="group bg-white/70 backdrop-blur-xl border border-white/40 rounded-[2rem] p-6 shadow-sm hover:shadow-xl hover:shadow-blue-900/5 transition-all duration-300 flex flex-col justify-between"
          >
            <div class="space-y-4">
              <div class="flex items-start justify-between">
                <div
                  class="px-3 py-1 bg-blue-50 text-blue-700 rounded-xl text-[10px] font-black uppercase tracking-widest"
                >
                  {grant.grant_code}
                </div>
                <div
                  class="text-[10px] font-bold text-gray-400 uppercase tracking-tighter"
                >
                  {grant.funder}
                </div>
              </div>

              <div class="space-y-1">
                <h3
                  class="text-lg font-black text-gray-900 leading-tight group-hover:text-blue-600 transition-colors"
                >
                  {grant.title}
                </h3>
              </div>
            </div>

            <div class="mt-8">
              <button
                on:click={() => handleGenerateReport(grant)}
                class="w-full py-3 bg-gray-900 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest hover:bg-blue-600 transition-all shadow-lg shadow-gray-200 hover:shadow-blue-200 flex items-center justify-center gap-2"
              >
                <Icon name="reports" size={14} />
                Generate Report
              </button>
            </div>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Notice -->
    <div
      class="p-6 bg-blue-50/50 border border-blue-100/50 rounded-3xl flex gap-4 items-center"
    >
      <div
        class="flex-shrink-0 w-10 h-10 bg-blue-100 text-blue-600 rounded-2xl flex items-center justify-center"
      >
        <Icon name="info" size={20} />
      </div>
      <p class="text-xs text-blue-800 font-medium leading-relaxed">
        <strong>Report Generation:</strong> Reports are compiled using live, system-verified
        data from milestones, approved expenses, and verified effort records. No
        manual edits are allowed to ensure audit-proof compliance.
      </p>
    </div>
  </div>
</Layout>

{#if showReportModal}
  <ReportModal
    grant={reportGrant}
    on:close={() => {
      showReportModal = false;
      reportGrant = null;
    }}
  />
{/if}
