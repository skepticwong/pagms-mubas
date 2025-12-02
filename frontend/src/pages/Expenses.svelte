<script>
  import { onMount } from "svelte";
  import axios from "axios";
  import Layout from "../components/Layout.svelte";

  // axios defaults
  axios.defaults.withCredentials = true;

  let grants = [];
  let categories = [];
  let recentExpenses = [];
  let loading = true;
  let submitting = false;

  let formData = {
    grant_id: "",
    category: "",
    amount: "",
    expense_date: new Date().toISOString().split("T")[0],
    description: "",
    payment_method: "Bank Transfer",
  };
  let receiptFile = null;
  let message = { text: "", type: "" };

  onMount(async () => {
    await Promise.all([fetchGrants(), fetchExpenses()]);
    loading = false;
  });

  async function fetchGrants() {
    try {
      const res = await axios.get("http://localhost:5000/api/grants");
      grants = res.data;
    } catch (err) {
      console.error("Error fetching grants:", err);
    }
  }

  async function fetchExpenses() {
    try {
      const res = await axios.get("http://localhost:5000/api/expenses");
      recentExpenses = res.data.expenses;
    } catch (err) {
      console.error("Error fetching expenses:", err);
    }
  }

  $: if (formData.grant_id) {
    const selectedGrant = grants.find((g) => g.id == formData.grant_id);
    categories = selectedGrant ? selectedGrant.categories : [];
  }

  function handleFileChange(e) {
    receiptFile = e.target.files[0];
  }

  async function handleSubmit() {
    submitting = true;
    message = { text: "", type: "" };

    const data = new FormData();
    for (let key in formData) {
      data.append(key, formData[key]);
    }
    if (receiptFile) {
      data.append("receipt", receiptFile);
    }

    try {
      await axios.post("http://localhost:5000/api/expenses", data);
      message = { text: "Expense submitted successfully!", type: "success" };
      // Reset form
      formData = {
        grant_id: "",
        category: "",
        amount: "",
        expense_date: new Date().toISOString().split("T")[0],
        description: "",
        payment_method: "Bank Transfer",
      };
      receiptFile = null;
      fetchExpenses(); // Refresh list
    } catch (err) {
      const errorMsg = err.response?.data?.error || "Failed to submit expense";
      message = { text: errorMsg, type: "error" };
    } finally {
      submitting = false;
    }
  }

  function getStatusStyle(status) {
    switch (status?.toLowerCase()) {
      case "approved":
        return "bg-green-100 text-green-800";
      case "rejected":
        return "bg-red-100 text-red-800";
      default:
        return "bg-amber-100 text-amber-800";
    }
  }
</script>

<Layout>
  <div class="max-w-5xl mx-auto space-y-8 py-4">
    <div class="flex justify-between items-end">
      <div class="space-y-1">
        <h1 class="text-3xl font-extrabold text-gray-900 tracking-tight">
          Submit Expenses
        </h1>
        <p class="text-gray-600">
          Log project expenditures and upload supporting receipts for finance
          review.
        </p>
      </div>
    </div>

    {#if message.text}
      <div
        class={`p-4 rounded-xl border ${message.type === "success" ? "bg-green-50 border-green-200 text-green-800" : "bg-red-50 border-red-200 text-red-800"}`}
      >
        {message.text}
      </div>
    {/if}

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Submission Form -->
      <div class="lg:col-span-2">
        <div
          class="bg-white/80 backdrop-blur-xl border border-white/40 rounded-3xl shadow-xl overflow-hidden"
        >
          <div class="p-8 space-y-6">
            <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
              <span
                class="w-8 h-8 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke-width="1.5"
                  stroke="currentColor"
                  class="w-5 h-5"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M12 4.5v15m7.5-7.5h-15"
                  />
                </svg>
              </span>
              New Expense Entry
            </h2>

            <form on:submit|preventDefault={handleSubmit} class="space-y-5">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div class="space-y-1.5">
                  <label class="text-sm font-semibold text-gray-700 ml-1"
                    >Select Grant</label
                  >
                  <select
                    bind:value={formData.grant_id}
                    required
                    class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none bg-gray-50/50"
                  >
                    <option value="">-- Choose Grant --</option>
                    {#each grants as grant}
                      <option value={grant.id}
                        >{grant.grant_code} - {grant.title}</option
                      >
                    {/each}
                  </select>
                </div>

                <div class="space-y-1.5">
                  <label class="text-sm font-semibold text-gray-700 ml-1"
                    >Budget Category</label
                  >
                  <select
                    bind:value={formData.category}
                    required
                    disabled={!formData.grant_id}
                    class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none bg-gray-50/50 disabled:opacity-50"
                  >
                    <option value="">-- Choose Category --</option>
                    {#each categories as cat}
                      <option value={cat.name}
                        >{cat.name} (Rem: {cat.allocated - cat.spent})</option
                      >
                    {/each}
                  </select>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div class="space-y-1.5">
                  <label class="text-sm font-semibold text-gray-700 ml-1"
                    >Amount (MWK)</label
                  >
                  <input
                    type="number"
                    bind:value={formData.amount}
                    required
                    placeholder="0.00"
                    class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none bg-gray-50/50"
                  />
                </div>

                <div class="space-y-1.5">
                  <label class="text-sm font-semibold text-gray-700 ml-1"
                    >Date of Expense</label
                  >
                  <input
                    type="date"
                    bind:value={formData.expense_date}
                    required
                    class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none bg-gray-50/50"
                  />
                </div>
              </div>

              <div class="space-y-1.5">
                <label class="text-sm font-semibold text-gray-700 ml-1"
                  >Description</label
                >
                <textarea
                  bind:value={formData.description}
                  required
                  rows="2"
                  placeholder="What was this expense for?"
                  class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none bg-gray-50/50"
                ></textarea>
              </div>

              <div class="space-y-1.5">
                <label class="text-sm font-semibold text-gray-700 ml-1"
                  >Payment Method</label
                >
                <div class="flex flex-wrap gap-4 px-2">
                  {#each ["Cash", "Bank Transfer", "Mobile Money"] as method}
                    <label class="flex items-center gap-2 cursor-pointer group">
                      <input
                        type="radio"
                        bind:group={formData.payment_method}
                        value={method}
                        class="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                      />
                      <span
                        class="text-sm text-gray-600 group-hover:text-gray-900"
                        >{method}</span
                      >
                    </label>
                  {/each}
                </div>
              </div>

              <div class="space-y-1.5">
                <label class="text-sm font-semibold text-gray-700 ml-1"
                  >Receipt / Proof of Payment</label
                >
                <div class="relative group">
                  <div
                    class="flex items-center justify-center w-full px-4 py-6 border-2 border-dashed border-gray-200 rounded-2xl bg-gray-50/50 group-hover:border-blue-400 transition-all cursor-pointer"
                  >
                    <div class="text-center">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke-width="1.5"
                        stroke="currentColor"
                        class="w-10 h-10 mx-auto text-gray-400 group-hover:text-blue-500"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
                        />
                      </svg>
                      <p class="mt-2 text-sm text-gray-500">
                        {receiptFile
                          ? receiptFile.name
                          : "Click to upload or drag receipt file"}
                      </p>
                    </div>
                    <input
                      type="file"
                      on:change={handleFileChange}
                      class="absolute inset-0 opacity-0 cursor-pointer"
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                class="w-full py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-2xl font-bold shadow-lg shadow-blue-200 hover:shadow-blue-300 hover:scale-[1.01] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {#if submitting}
                  <svg
                    class="animate-spin h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      class="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      stroke-width="4"
                    ></circle>
                    <path
                      class="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                {/if}
                {submitting ? "Submitting..." : "Submit Expense Claim"}
              </button>
            </form>
          </div>
        </div>
      </div>

      <!-- Side List: Recent Submissions -->
      <div class="lg:col-span-1">
        <div
          class="bg-white/60 backdrop-blur-lg border border-white/50 rounded-3xl shadow-lg p-6 space-y-5"
        >
          <h2
            class="text-lg font-bold text-gray-900 border-b border-gray-100 pb-3"
          >
            Recent Claims
          </h2>
          <div class="space-y-4 max-h-[600px] overflow-y-auto pr-1">
            {#each recentExpenses.slice(0, 10) as claim}
              <div
                class="p-4 rounded-2xl bg-white border border-gray-100 shadow-sm space-y-2"
              >
                <div class="flex justify-between items-start">
                  <span
                    class="text-xs font-semibold uppercase tracking-wider text-gray-400"
                    >{claim.category}</span
                  >
                  <span
                    class={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${getStatusStyle(claim.status)}`}
                  >
                    {claim.status}
                  </span>
                </div>
                <p class="text-sm font-bold text-gray-900">
                  {claim.amount}
                  {claim.currency}
                </p>
                <p class="text-[11px] text-gray-500 line-clamp-2">
                  {claim.description}
                </p>
                <div
                  class="pt-1 flex items-center justify-between text-[10px] text-gray-400"
                >
                  <span
                    >{new Date(claim.expense_date).toLocaleDateString()}</span
                  >
                  <span class="font-medium text-blue-500"
                    >{claim.grant_title}</span
                  >
                </div>
              </div>
            {:else}
              <p class="text-center py-8 text-gray-500 text-sm">
                No recent claims found.
              </p>
            {/each}
          </div>
          <button
            class="w-full text-center text-sm font-semibold text-blue-600 hover:text-blue-700 py-1"
            >View Full History →</button
          >
        </div>
      </div>
    </div>
  </div>
</Layout>

<style>
  /* Custom scrollbar for recent list */
  ::-webkit-scrollbar {
    width: 4px;
  }
  ::-webkit-scrollbar-track {
    background: transparent;
  }
  ::-webkit-scrollbar-thumb {
    background: #e2e8f0;
    border-radius: 10px;
  }
</style>
