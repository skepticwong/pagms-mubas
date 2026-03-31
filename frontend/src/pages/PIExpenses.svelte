<script>
    import { onMount } from "svelte";
    import axios from "axios";
    import Layout from "../components/Layout.svelte";
    import PriorApprovalModal from "../components/PriorApprovalModal.svelte";
    import Icon from "../components/Icon.svelte";
    import { confirm } from "../stores/modals.js";
    import { router } from "../stores/router.js";
    import { user } from "../stores/auth.js";

    axios.defaults.withCredentials = true;

    // Form state
    let selectedGrant = "";
    let selectedCategory = "";
    let amount = "";
    let expenseDate = "";
    let description = "";
    let receiptFile = null;

    // Data
    let grants = [];
    let budgetCategories = [];
    let expenses = [];
    let priorApprovals = [];
    let selectedPriorApprovalId = "";

    // UI state
    let loading = false;
    let error = "";
    let success = "";
    let submitting = false;

    $: filteredPriorApprovals = priorApprovals.filter(pa => 
        pa.status === 'approved' && 
        pa.grant_id == selectedGrant && 
        pa.category === category
    );
    let isPriorApprovalModalOpen = false;

    // FX rate (MWK to USD)
    const FX_RATE = 1705;

    $: usdAmount = amount ? (parseFloat(amount) / FX_RATE).toFixed(2) : "0.00";
    $: selectedCategoryData = budgetCategories.find(
        (c) => c.id === parseInt(selectedCategory),
    );
    $: remainingBalance = selectedCategoryData
        ? selectedCategoryData.remaining
        : 0;
    
    $: selectedGrantData = grants.find(g => g.id == selectedGrant);
    $: availableDisbursedFunds = selectedGrantData ? selectedGrantData.available_disbursed_funds : 0;

    onMount(async () => {
        await loadGrants();
        await loadExpenses();
        await loadPriorApprovals();
    });

    async function loadGrants() {
        try {
            const response = await axios.get(
                "http://localhost:5000/api/grants",
            );
            grants = response.data.grants || [];
            if (grants.length > 0) {
                selectedGrant = grants[0].id;
                await loadBudgetCategories();
            }
        } catch (err) {
            console.error("Error loading grants:", err);
            error = "Failed to load grants";
        }
    }

    async function loadBudgetCategories() {
        if (!selectedGrant) return;

        try {
            const response = await axios.get(
                `http://localhost:5000/api/grants/${selectedGrant}/budget-categories`,
            );
            budgetCategories = response.data.categories || [];
            if (budgetCategories.length > 0) {
                selectedCategory = budgetCategories[0].id;
            }
        } catch (err) {
            console.error("Error loading budget categories:", err);
            error = "Failed to load budget categories";
        }
    }

    async function loadExpenses() {
        loading = true;
        try {
            const response = await axios.get(
                "http://localhost:5000/api/expenses",
            );
            expenses = response.data.expenses || [];
        } catch (err) {
            console.error("Error loading expenses:", err);
            error = "Failed to load expenses";
        } finally {
            loading = false;
        }
    }

    async function loadPriorApprovals() {
        if (!selectedGrant) return;
        try {
            const response = await axios.get(
                `http://localhost:5000/api/prior-approvals/grant/${selectedGrant}`,
            );
            priorApprovals = response.data || [];
        } catch (err) {
            console.error("Error loading prior approvals:", err);
        }
    }

    async function handleGrantChange() {
        await loadBudgetCategories();
        await loadPriorApprovals();
    }

    function handleFileChange(event) {
        receiptFile = event.target.files[0];
    }

    async function submitExpense() {
        error = "";
        success = "";

        // Validation
        if (!selectedGrant || !selectedCategory || !amount || !expenseDate) {
            error = "Please fill in all required fields";
            return;
        }

        if (!receiptFile) {
            error = "Receipt file is required";
            return;
        }

        const amountNum = parseFloat(amount);
        
        // 1. Check Budget Category Balance
        if (amountNum > remainingBalance) {
            error = `Insufficient budget in category. Remaining in ${selectedCategoryData.name}: MWK ${remainingBalance.toLocaleString()}`;
            return;
        }

        // 2. Check Grant Disbursed Funds (Gating)
        if (amountNum > availableDisbursedFunds) {
            error = `Insufficient disbursed funds. Available across grant: MWK ${availableDisbursedFunds.toLocaleString()}. Please wait for next tranche.`;
            return;
        }

        submitting = true;

        try {
            const formData = new FormData();
            formData.append("grant_id", selectedGrant);
            formData.append("category", selectedCategoryData.name);
            formData.append("amount", amountNum);
            formData.append("expense_date", expenseDate);
            formData.append("description", description);
            if (selectedPriorApprovalId) {
                formData.append("prior_approval_id", selectedPriorApprovalId);
            }
            formData.append("receipt", receiptFile);

            const res = await axios.post("http://localhost:5000/api/expenses", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });

            success = res.data.message || "Expense submitted successfully!";

            // Reset form
            amount = "";
            expenseDate = "";
            description = "";
            receiptFile = null;
            selectedPriorApprovalId = "";
            document.getElementById("receipt-input").value = "";

            // Reload data
            await loadBudgetCategories();
            await loadExpenses();
            await loadPriorApprovals();
        } catch (err) {
            console.error("Error submitting expense:", err);
            error = err.response?.data?.error || "Failed to submit expense";
        } finally {
            submitting = false;
        }
    }

    async function deleteExpense(expenseId) {
        if (!await confirm("Are you sure you want to delete this expense?")) {
            return;
        }

        try {
            await axios.delete(
                `http://localhost:5000/api/expenses/${expenseId}`,
            );
            success = "Expense deleted successfully";
            await loadExpenses();
            await loadBudgetCategories();
        } catch (err) {
            console.error("Error deleting expense:", err);
            error = err.response?.data?.error || "Failed to delete expense";
        }
    }

    function viewReceipt(filename) {
        if (filename) {
            window.open(
                `http://localhost:5000/api/uploads/${filename}`,
                "_blank",
            );
        }
    }

    function formatDate(dateString) {
        if (!dateString) return "N/A";
        const date = new Date(dateString);
        return date.toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    }

    function getStatusBadge(status) {
        const s = status?.toLowerCase();
        if (s === "approved" || s === "completed") return "bg-green-100 text-green-700 border-green-200";
        if (s === "rejected" || s === "overdue" || s === "at_risk") return "bg-red-100 text-red-700 border-red-200";
        if (s === "pending" || s === "awaiting_approval" || s === "awaiting_prior_approval") return "bg-amber-100 text-amber-700 border-amber-200";
        return "bg-blue-100 text-blue-700 border-blue-200";
    }

    function getStatusIcon(status) {
        const icons = {
            pending: "⏳",
            awaiting_prior_approval: "🛡️",
            approved: "✅",
            rejected: "❌",
        };
        return icons[status] || "📄";
    }
</script>

<Layout>
    <div class="max-w-7xl mx-auto space-y-6 py-4">
        <!-- Header -->
        <div
            class="bg-white/60 backdrop-blur-xl border border-white/60 rounded-3xl p-8 shadow-lg"
        >
            <div>
                <p
                    class="text-xs uppercase tracking-[0.3em] text-blue-600 font-semibold"
                >
                    PI · Expenses
                </p>
                <h1 class="text-3xl font-bold text-gray-900">
                    Expense Management
                </h1>
                <p class="text-sm text-gray-600">
                    Submit and track expenses for your grants
                </p>
            </div>
            <button 
                on:click={() => isPriorApprovalModalOpen = true}
                class="px-4 py-2 bg-purple-600 text-white rounded-xl text-sm font-semibold shadow-lg shadow-purple-100 hover:bg-purple-700 transition-all flex items-center gap-2"
            >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                Request Prior Approval
            </button>
        </div>

        {#if error}
            <div class="bg-red-50 border border-red-200 rounded-xl p-4">
                <p class="text-red-700 text-sm">{error}</p>
            </div>
        {/if}

        {#if success}
            <div class="bg-green-50 border border-green-200 rounded-xl p-4">
                <p class="text-green-700 text-sm">{success}</p>
            </div>
        {/if}

        <!-- Expense Submission Form -->
        <div
            class="bg-white/70 backdrop-blur-xl border border-white/40 rounded-2xl shadow-md p-6"
        >
            <h2 class="text-xl font-bold text-gray-900 mb-6">
                Submit New Expense
            </h2>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Grant Selection -->
                <div>
                    <label
                        for="grant"
                        class="block text-sm font-medium text-gray-700 mb-2"
                        >Grant *</label
                    >
                    <select
                        id="grant"
                        bind:value={selectedGrant}
                        on:change={handleGrantChange}
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                        {#each grants as grant}
                            <option value={grant.id}>{grant.title}</option>
                        {/each}
                    </select>
                </div>

                <!-- Grant Info & Disbursement Status -->
                {#if selectedGrantData}
                <div class="md:col-span-2 p-4 bg-blue-50 border border-blue-100 rounded-xl">
                    <h4 class="text-xs font-bold text-blue-800 uppercase tracking-tight mb-2">Disbursement Status</h4>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <p class="text-[10px] text-blue-600 uppercase font-semibold">Total Disbursed</p>
                            <p class="text-lg font-bold text-blue-900">MWK {(selectedGrantData.disbursed_funds || 0).toLocaleString()}</p>
                        </div>
                        <div>
                            <p class="text-[10px] text-blue-600 uppercase font-semibold">Available to Spend</p>
                            <p class="text-lg font-bold text-blue-900">MWK {(selectedGrantData.available_disbursed_funds || 0).toLocaleString()}</p>
                        </div>
                    </div>
                    <p class="text-[10px] text-blue-500 mt-2 italic">
                        Spending is gated by the amount actually disbursed to the university (Tranches).
                    </p>
                </div>
                {/if}

                <!-- Budget Category -->
                <div>
                    <label
                        for="category"
                        class="block text-sm font-medium text-gray-700 mb-2"
                        >Budget Category *</label
                    >
                    <select
                        id="category"
                        bind:value={selectedCategory}
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                        {#each budgetCategories as category}
                            <option value={category.id}
                                >{category.name} (Remaining: MWK {category.remaining.toLocaleString()})</option
                            >
                        {/each}
                    </select>
                    {#if selectedCategoryData}
                        <p class="text-xs text-gray-500 mt-1">
                            Remaining in {selectedCategoryData.name}:
                            <span class="font-semibold text-blue-600"
                                >MWK {remainingBalance.toLocaleString()}</span
                            >
                        </p>
                    {/if}
                </div>

                <!-- Amount -->
                <div>
                    <label
                        for="amount"
                        class="block text-sm font-medium text-gray-700 mb-2"
                        >Amount (MWK) *</label
                    >
                    <input
                        id="amount"
                        type="number"
                        bind:value={amount}
                        placeholder="Enter amount in MWK"
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <p class="text-xs text-gray-500 mt-1">
                        = USD {usdAmount} @ rate {FX_RATE}
                    </p>
                </div>

                <!-- Expense Date -->
                <div>
                    <label
                        for="expense-date"
                        class="block text-sm font-medium text-gray-700 mb-2"
                        >Expense Date *</label
                    >
                    <input
                        id="expense-date"
                        type="date"
                        bind:value={expenseDate}
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                </div>

                <!-- Description -->
                <div class="md:col-span-2">
                    <label
                        for="description"
                        class="block text-sm font-medium text-gray-700 mb-2"
                        >Description</label
                    >
                    <textarea
                        id="description"
                        bind:value={description}
                        placeholder="Flight to Lilongwe for workshop"
                        rows="3"
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    ></textarea>
                </div>

                <!-- Receipt Upload -->
                <div class="md:col-span-2">
                    <label
                        for="receipt-input"
                        class="block text-sm font-medium text-gray-700 mb-2"
                        >Receipt (PDF/JPG/PNG) *</label
                    >
                    <input
                        id="receipt-input"
                        type="file"
                        accept=".pdf,.jpg,.jpeg,.png"
                        on:change={handleFileChange}
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    {#if receiptFile}
                        <p class="text-xs text-green-600 mt-1">
                            ✓ {receiptFile.name}
                        </p>
                    {/if}
                </div>

                <!-- Prior Approval Linking -->
                {#if filteredPriorApprovals.length > 0}
                    <div class="md:col-span-2 p-4 bg-emerald-50 border border-emerald-100 rounded-xl animate-in fade-in slide-in-from-top-2 duration-300">
                        <label for="pa-link" class="block text-xs font-bold text-emerald-800 mb-2 uppercase tracking-tight">
                            Pre-Approved Authorization Found
                        </label>
                        <select 
                            id="pa-link"
                            bind:value={selectedPriorApprovalId}
                            class="w-full px-4 py-2 bg-white border border-emerald-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                        >
                            <option value="">-- Apply an approved authorization (Optional) --</option>
                            {#each filteredPriorApprovals as pa}
                                <option value={pa.id}>
                                    Approved on {formatDate(pa.created_at)} - ${pa.amount.toLocaleString()} ({pa.justification.substring(0, 30)}...)
                                </option>
                            {/each}
                        </select>
                        <p class="text-[10px] text-emerald-600 mt-2 italic">
                            Linking a pre-approved request bypassing automatic compliance holds.
                        </p>
                    </div>
                {/if}
            </div>

            <!-- Submit Button -->
            <div class="mt-6">
                <button
                    on:click={submitExpense}
                    disabled={submitting}
                    class="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                    {submitting ? "Submitting..." : "Submit for Review"}
                </button>
            </div>
        </div>

        <!-- Expense List -->
        <div
            class="bg-white/70 backdrop-blur-xl border border-white/40 rounded-2xl shadow-md p-6"
        >
            <h2 class="text-xl font-bold text-gray-900 mb-6">My Expenses</h2>

            {#if loading}
                <div class="text-center py-8">
                    <p class="text-gray-500">Loading expenses...</p>
                </div>
            {:else if expenses.length === 0}
                <div class="text-center py-8">
                    <p class="text-gray-500">No expenses submitted yet</p>
                </div>
            {:else}
                <div class="overflow-x-auto">
                    <table class="w-full">
                        <thead class="bg-gray-50 border-b border-gray-200">
                            <tr>
                                <th
                                    class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase"
                                    >Date</th
                                >
                                <th
                                    class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase"
                                    >Grant</th
                                >
                                <th
                                    class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase"
                                    >Category</th
                                >
                                <th
                                    class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase"
                                    >Description</th
                                >
                                <th
                                    class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase"
                                    >Amount</th
                                >
                                <th
                                    class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase"
                                    >Status</th
                                >
                                <th
                                    class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase"
                                    >Receipt</th
                                >
                                <th
                                    class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase"
                                    >Actions</th
                                >
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-200">
                            {#each expenses as expense}
                                <tr
                                    class="hover:bg-blue-50/50 transition-colors"
                                >
                                    <td class="px-4 py-3 text-sm text-gray-700"
                                        >{formatDate(expense.expense_date)}</td
                                    >
                                    <td class="px-4 py-3 text-sm text-gray-700"
                                        >{expense.grant_title}</td
                                    >
                                    <td class="px-4 py-3 text-sm text-gray-700"
                                        >{expense.category}</td
                                    >
                                    <td
                                        class="px-4 py-3 text-sm text-gray-700 max-w-xs truncate"
                                        >{expense.description || "-"}</td
                                    >
                                    <td
                                        class="px-4 py-3 text-sm font-semibold text-gray-900"
                                        >MWK {expense.amount.toLocaleString()}</td
                                    >
                                    <td class="px-4 py-3">
                                        <span
                                            class="px-2 py-1 text-xs font-semibold rounded border {getStatusBadge(
                                                expense.status,
                                            )}"
                                        >
                                            {getStatusIcon(expense.status)}
                                            {expense.status
                                                .charAt(0)
                                                .toUpperCase() +
                                                expense.status.slice(1)}
                                        </span>
                                    </td>
                                    <td class="px-4 py-3">
                                        {#if expense.receipt_filename}
                                            <button
                                                on:click={() =>
                                                    viewReceipt(
                                                        expense.receipt_filename,
                                                    )}
                                                class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                                            >
                                                View
                                            </button>
                                        {:else}
                                            <span class="text-gray-400 text-sm"
                                                >-</span
                                            >
                                        {/if}
                                    </td>
                                    <td class="px-4 py-3">
                                        {#if expense.status === "pending"}
                                            <button
                                                on:click={() =>
                                                    deleteExpense(expense.id)}
                                                class="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-xl transition-all"
                                                title="Delete Expense"
                                            >
                                                <Icon name="delete" size={16} />
                                            </button>
                                        {:else}
                                            <span class="text-gray-400 text-sm"
                                                >-</span
                                            >
                                        {/if}
                                    </td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            {/if}
        </div>

        <!-- Prior Authorization Requests (PRE-SPEND) -->
        <div class="bg-white/70 backdrop-blur-xl border border-white/40 rounded-2xl shadow-md p-6">
            <h2 class="text-xl font-bold text-gray-900 mb-6">Pre-Spend Authorizations</h2>
            
            {#if priorApprovals.length === 0}
                <div class="text-center py-8">
                    <p class="text-gray-500 text-sm italic">No active pre-spend authorization requests found for this grant.</p>
                </div>
            {:else}
                <div class="overflow-x-auto">
                    <table class="w-full">
                        <thead class="bg-gray-50/50 border-b border-gray-200">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Type</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Amount</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Justification</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Date</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100">
                            {#each priorApprovals as req}
                                <tr class="hover:bg-purple-50/30 transition-colors">
                                    <td class="px-4 py-3 text-sm font-bold text-gray-700">{req.request_type}</td>
                                    <td class="px-4 py-3 text-sm font-semibold text-purple-700">${req.amount?.toLocaleString() || '0'}</td>
                                    <td class="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">{req.justification}</td>
                                    <td class="px-4 py-3">
                                        <span class="px-2 py-1 text-[10px] font-bold rounded-full border 
                                            {req.status === 'approved' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 
                                             req.status === 'rejected' ? 'bg-red-50 text-red-700 border-red-200' : 
                                             'bg-amber-50 text-amber-700 border-amber-200'}">
                                            {req.status.toUpperCase()}
                                        </span>
                                    </td>
                                    <td class="px-4 py-3 text-xs text-gray-400">{formatDate(req.created_at)}</td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            {/if}
        </div>
    </div>

    <PriorApprovalModal 
        grants={grants} 
        bind:isOpen={isPriorApprovalModalOpen}
        on:success={() => {
            success = "Prior approval request submitted successfully!";
            // Optionally reload a requests list if we had one
        }}
    />
</Layout>
