<script>
  import { onMount } from "svelte";
  import axios from "axios";
  import Layout from "../components/Layout.svelte";
  import { router } from "../stores/router.js";

  axios.defaults.withCredentials = true;

  let loading = true;
  let error = "";
  let claims = [];
  let kpis = {
    avgTurnaround: 0,
    claimsOver7Days: 0,
    usdExposure: 0,
    policyExceptions: 0,
    avgAgeing: 0,
  };
  let filterStatus = "all";
  let searchTerm = "";
  let selectedCurrency = "USD";

  const filterOptions = [
    { label: "All", value: "all" },
    { label: "Awaiting Treasury", value: "Awaiting Treasury" },
    { label: "Compliance Review", value: "Compliance Review" },
    { label: "PI Clarification", value: "PI Clarification" },
  ];

  onMount(async () => {
    await loadClaims();
  });

  async function loadClaims() {
    loading = true;
    error = "";

    try {
      const response = await axios.get(
        "http://localhost:5000/api/finance/pending-expenses",
      );
      claims = response.data.claims || [];
      kpis = response.data.kpis || kpis;
    } catch (err) {
      console.error("Error loading pending expenses:", err);
      error =
        err.response?.data?.error ||
        "Failed to load pending expenses. Please try again.";
    } finally {
      loading = false;
    }
  }

  function filteredClaims() {
    return claims.filter((claim) => {
      const matchesStatus =
        filterStatus === "all" || claim.status === filterStatus;
      const matchesSearch = `${claim.grant} ${claim.id} ${claim.pi}`
        .toLowerCase()
        .includes(searchTerm.toLowerCase());
      return matchesStatus && matchesSearch;
    });
  }

  function formatAmount(value) {
    return value.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  async function approveClaim(expenseId) {
    if (!confirm("Are you sure you want to approve this expense claim?")) {
      return;
    }

    try {
      await axios.post(
        `http://localhost:5000/api/finance/expenses/${expenseId}/approve`,
      );
      alert("Expense approved successfully!");
      await loadClaims(); // Reload data
    } catch (err) {
      console.error("Error approving expense:", err);
      alert(
        err.response?.data?.error ||
          "Failed to approve expense. Please try again.",
      );
    }
  }

  async function escalateClaim(expenseId) {
    if (
      !confirm("Are you sure you want to reject/escalate this expense claim?")
    ) {
      return;
    }

    try {
      await axios.post(
        `http://localhost:5000/api/finance/expenses/${expenseId}/reject`,
      );
      alert("Expense rejected successfully!");
      await loadClaims(); // Reload data
    } catch (err) {
      console.error("Error rejecting expense:", err);
      alert(
        err.response?.data?.error ||
          "Failed to reject expense. Please try again.",
      );
    }
  }
</script>

<Layout>
  <div class="max-w-6xl mx-auto space-y-8 py-4">
    <section
      class="bg-white/60 backdrop-blur-xl border border-white/60 rounded-3xl p-8 shadow-lg"
    >
      <div class="flex flex-col gap-3">
        <div>
          <p
            class="text-xs uppercase tracking-[0.3em] text-blue-600 font-semibold"
          >
            Finance · Expenses
          </p>
          <h1 class="text-3xl font-bold text-gray-900">
            Pending expense approvals
          </h1>
          <p class="text-sm text-gray-600">
            Review receipts, validate policy compliance, and release cash
            without surprises.
          </p>
        </div>
        <div class="flex flex-wrap gap-3 text-xs text-gray-600">
          <span class="px-3 py-1 rounded-full bg-blue-50 text-blue-700"
            >Treasury queue</span
          >
          <span class="px-3 py-1 rounded-full bg-amber-50 text-amber-700"
            >Average ageing {kpis.avgAgeing} days</span
          >
          <button
            class="ml-auto px-4 py-2 rounded-full border border-gray-200 text-gray-700 text-xs font-semibold"
            type="button"
            on:click={loadClaims}
            disabled={loading}
          >
            {loading ? "Refreshing…" : "Refresh data"}
          </button>
        </div>
      </div>
    </section>

    <section
      class="bg-white/70 backdrop-blur-xl border border-white/40 rounded-2xl shadow-md p-6 space-y-6"
    >
      <div class="flex flex-wrap items-center gap-4">
        <div class="flex items-center gap-2 text-sm text-gray-700">
          <span class="text-gray-500">Filter:</span>
          <div class="flex gap-2">
            {#each filterOptions as option}
              <button
                class={`px-3 py-1 rounded-full border text-xs font-semibold ${filterStatus === option.value ? "bg-blue-600 text-white border-blue-600" : "border-gray-200 text-gray-600"}`}
                type="button"
                on:click={() => (filterStatus = option.value)}
              >
                {option.label}
              </button>
            {/each}
          </div>
        </div>
        <input
          class="flex-1 min-w-[220px] px-3 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          type="search"
          placeholder="Search by grant, PI, or claim id"
          bind:value={searchTerm}
        />
        <select
          class="px-3 py-2 rounded-xl border border-gray-200 text-sm text-gray-700"
          bind:value={selectedCurrency}
        >
          <option value="USD">USD</option>
          <option value="MWK">MKW</option>
        </select>
      </div>

      <div class="border border-dashed border-gray-200 rounded-2xl">
        <div
          class="grid grid-cols-12 text-xs font-semibold text-gray-500 uppercase tracking-wide px-5 py-3"
        >
          <span class="col-span-2">Claim ID</span>
          <span class="col-span-3">Grant</span>
          <span class="col-span-2">Category</span>
          <span class="col-span-2">Amount</span>
          <span class="col-span-1">Ageing</span>
          <span class="col-span-2 text-right">Actions</span>
        </div>
        {#if loading}
          <div class="p-8 text-center text-sm text-gray-500">
            Loading claims…
          </div>
        {:else if filteredClaims().length === 0}
          <div class="p-8 text-center text-sm text-gray-500">
            No expense claims match this filter.
          </div>
        {:else}
          {#each filteredClaims() as claim}
            <div
              class="grid grid-cols-12 px-5 py-4 border-t border-gray-100 text-sm text-gray-800"
            >
              <div class="col-span-2">
                <p class="font-semibold text-gray-900">{claim.id}</p>
                <p class="text-xs text-gray-500">{claim.status}</p>
              </div>
              <div class="col-span-3">
                <p class="font-semibold text-gray-900">{claim.grant}</p>
                <p class="text-xs text-gray-500">PI: {claim.pi}</p>
              </div>
              <div class="col-span-2">
                <p>{claim.category}</p>
                <p class="text-xs text-gray-500">
                  {claim.attachments} attachments
                </p>
              </div>
              <div class="col-span-2">
                {#if selectedCurrency === "USD"}
                  <p class="font-semibold">${formatAmount(claim.amountUSD)}</p>
                {:else}
                  <p class="font-semibold">
                    MK {formatAmount(claim.amountMWK)}
                  </p>
                {/if}
                <p class="text-xs text-gray-500">
                  Submitted {new Date(claim.submitted).toLocaleDateString()}
                </p>
              </div>
              <div class="col-span-1">
                <span
                  class={`px-2 py-1 rounded-full text-xs font-semibold ${claim.ageingDays > 7 ? "bg-rose-50 text-rose-700" : "bg-emerald-50 text-emerald-700"}`}
                >
                  {claim.ageingDays} days
                </span>
              </div>
              <div class="col-span-2 flex justify-end gap-2">
                <button
                  class="px-3 py-1 rounded-xl text-xs font-semibold border border-gray-200"
                  type="button"
                  on:click={() => router.goToReviewEvidence()}
                >
                  View docs
                </button>
                <button
                  class="px-3 py-1 rounded-xl text-xs font-semibold bg-emerald-600 text-white"
                  type="button"
                  on:click={() => approveClaim(claim.expense_id)}
                >
                  Approve
                </button>
                <button
                  class="px-3 py-1 rounded-xl text-xs font-semibold bg-rose-50 text-rose-700"
                  type="button"
                  on:click={() => escalateClaim(claim.expense_id)}
                >
                  Escalate
                </button>
              </div>
            </div>
          {/each}
        {/if}
      </div>
    </section>

    <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div
        class="bg-white/70 backdrop-blur-xl border border-white/40 rounded-2xl shadow-md p-6"
      >
        <h2 class="text-lg font-semibold text-gray-900">Policy reminders</h2>
        <ul class="mt-4 space-y-2 text-sm text-gray-700">
          <li>
            • Travel per diems must match funder ceilings – auto-flagged above
            $150/day.
          </li>
          <li>
            • All FX conversions use RBM reference + 1% buffer from Exchange
            Rates screen.
          </li>
          <li>• Equipment > $5K requires dual approval (Finance + RSU).</li>
        </ul>
      </div>
      <div
        <div
        class="bg-white/70 backdrop-blur-xl border border-white/40 rounded-2xl shadow-md p-6"
      >
        <h2 class="text-lg font-semibold text-gray-900">Processing KPIs</h2>
        <div class="grid grid-cols-2 gap-4 mt-4 text-sm text-gray-700">
          <div class="p-4 rounded-2xl border border-gray-100">
            <p class="text-xs text-gray-500">Avg turnaround</p>
            <p class="text-2xl font-semibold text-gray-900">
              {kpis.avgTurnaround} days
            </p>
          </div>
          <div class="p-4 rounded-2xl border border-gray-100">
            <p class="text-xs text-gray-500">Claims > 7 days</p>
            <p class="text-2xl font-semibold text-rose-600">
              {kpis.claimsOver7Days}
            </p>
          </div>
          <div class="p-4 rounded-2xl border border-gray-100">
            <p class="text-xs text-gray-500">USD exposure</p>
            <p class="text-2xl font-semibold text-emerald-600">
              ${formatAmount(kpis.usdExposure)}
            </p>
          </div>
          <div class="p-4 rounded-2xl border border-gray-100">
            <p class="text-xs text-gray-500">Policy exceptions</p>
            <p class="text-2xl font-semibold text-amber-600">
              {kpis.policyExceptions}
            </p>
          </div>
        </div>
      </div>
    </section>
  </div>
</Layout>
