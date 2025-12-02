<script>
    import { onMount } from "svelte";
    import axios from "axios";
    import { user } from "../stores/auth.js";
    import { router } from "../stores/router.js";

    // Enable credentials for Flask sessions
    axios.defaults.withCredentials = true;

    let loading = true;
    let myGrants = [];
    let myTasks = [];
    let myEvidence = [];
    let myExpenses = [];

    // Derived Stats
    $: activeGrantsCount = myGrants.length;
    $: pendingTasks = myTasks.filter(
        (t) =>
            t.status === "assigned" ||
            t.status === "in_progress" ||
            t.status === "revision_requested",
    );
    $: completedTasks = myTasks.filter((t) => t.status === "completed");
    $: totalHours = myEvidence.reduce(
        (sum, e) => sum + (e.hours_worked || 0),
        0,
    );
    $: estimatedEarnings = totalHours * ($user?.pay_rate || 0);

    async function fetchDashboardData() {
        loading = true;
        try {
            const [grantsRes, tasksRes, evidenceRes, expensesRes] =
                await Promise.all([
                    axios.get("http://localhost:5000/api/grants"),
                    axios.get("http://localhost:5000/api/tasks"),
                    axios.get("http://localhost:5000/api/evidence"),
                    axios.get("http://localhost:5000/api/expenses"),
                ]);

            myGrants = grantsRes.data || [];
            myTasks = tasksRes.data.tasks || [];
            myEvidence = evidenceRes.data.submissions || [];
            myExpenses = expensesRes.data.expenses || [];
        } catch (err) {
            console.error("Failed to fetch Team dashboard data:", err);
        } finally {
            loading = false;
        }
    }

    onMount(() => {
        fetchDashboardData();
    });

    function statusBadge(status) {
        const s = status?.toLowerCase();
        if (s === "completed" || s === "approved")
            return "bg-green-100 text-green-800";
        if (s === "assigned" || s === "pending")
            return "bg-blue-100 text-blue-800";
        if (s === "revision_requested") return "bg-red-100 text-red-800";
        if (s === "submitted") return "bg-amber-100 text-amber-800";
        return "bg-gray-100 text-gray-700";
    }

    function formatDate(dateStr) {
        if (!dateStr) return "N/A";
        return new Date(dateStr).toLocaleDateString();
    }
</script>

<div class="space-y-6">
    <!-- Profile & Welcome -->
    <div
        class="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col md:flex-row md:items-center justify-between gap-4"
    >
        <div class="flex items-center gap-4">
            <div
                class="h-16 w-16 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-2xl"
            >
                {$user?.name?.charAt(0) || "U"}
            </div>
            <div>
                <h2 class="text-2xl font-bold text-gray-900">
                    Welcome, {$user?.name || "Team Member"}
                </h2>
                <p class="text-sm text-gray-600">
                    {$user?.email} •
                    <span class="font-medium text-blue-700">{$user?.role}</span>
                </p>
            </div>
        </div>
        <div class="flex flex-col items-end">
            <p
                class="text-xs text-gray-500 uppercase tracking-wider font-semibold"
            >
                Base Pay Rate
            </p>
            <p class="text-xl font-bold text-gray-900">
                MWK {$user?.pay_rate?.toLocaleString() || 0} / hr
            </p>
        </div>
    </div>

    <!-- Quick Stats -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
            <h3 class="font-medium text-gray-900">Assigned Grants</h3>
            <p class="text-3xl mt-2 font-bold text-blue-700">
                {activeGrantsCount}
            </p>
            <p class="text-xs text-gray-500 mt-1">Active projects</p>
        </div>
        <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
            <h3 class="font-medium text-gray-900">Pending Tasks</h3>
            <p class="text-3xl mt-2 font-bold text-amber-600">
                {pendingTasks.length}
            </p>
            <p class="text-xs text-gray-500 mt-1">Requires action</p>
        </div>
        <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
            <h3 class="font-medium text-gray-900">Total Hours</h3>
            <p class="text-3xl mt-2 font-bold text-green-600">{totalHours}</p>
            <p class="text-xs text-gray-500 mt-1">Submitted evidence</p>
        </div>
        <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
            <h3 class="font-medium text-gray-900">Estimated Earnings</h3>
            <p class="text-3xl mt-2 font-bold text-indigo-700">
                MWK {estimatedEarnings.toLocaleString()}
            </p>
            <p class="text-xs text-gray-500 mt-1">Based on approved/pending</p>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Tasks Column -->
        <div class="lg:col-span-2 space-y-6">
            <div
                class="bg-white p-6 rounded-xl shadow-sm border border-gray-100"
            >
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-bold text-lg text-gray-900">
                        My Task Queue
                    </h3>
                    <span
                        class="text-xs font-medium px-2 py-1 bg-gray-100 rounded text-gray-600"
                        >{pendingTasks.length} Pending</span
                    >
                </div>

                <div class="space-y-3">
                    {#each pendingTasks as task}
                        <div
                            class="p-4 rounded-lg bg-gray-50 border border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                        >
                            <div>
                                <p class="font-semibold text-gray-900">
                                    {task.title}
                                </p>
                                <p class="text-xs text-gray-600">
                                    {task.grant_title} • Due: {formatDate(
                                        task.deadline,
                                    )}
                                </p>
                                {#if task.status === "revision_requested"}
                                    <p
                                        class="text-xs text-red-600 mt-1 font-medium italic"
                                    >
                                        Revision Requested by PI
                                    </p>
                                {/if}
                            </div>
                            <div class="flex items-center gap-3">
                                <span
                                    class="px-2 py-1 text-xs font-semibold rounded-full {statusBadge(
                                        task.status,
                                    )}">{task.status}</span
                                >
                                <button
                                    on:click={() =>
                                        router.goToSubmitEvidence(task.id)}
                                    class="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700"
                                >
                                    Submit Evidence
                                </button>
                            </div>
                        </div>
                    {:else}
                        <div class="text-center py-8">
                            <p class="text-gray-500 text-sm">
                                No pending tasks at the moment.
                            </p>
                        </div>
                    {/each}
                </div>
            </div>

            <!-- Recent Evidence -->
            <div
                class="bg-white p-6 rounded-xl shadow-sm border border-gray-100"
            >
                <h3 class="font-bold text-lg text-gray-900 mb-4">
                    Recent Submissions
                </h3>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead>
                            <tr>
                                <th
                                    class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                                    >Task</th
                                >
                                <th
                                    class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                                    >Hours</th
                                >
                                <th
                                    class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                                    >Submitted</th
                                >
                                <th
                                    class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                                    >Status</th
                                >
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100">
                            {#each myEvidence.slice(0, 5) as item}
                                <tr>
                                    <td class="px-3 py-3 text-sm text-gray-900"
                                        >{item.task_title}</td
                                    >
                                    <td class="px-3 py-3 text-sm text-gray-600"
                                        >{item.hours_worked}</td
                                    >
                                    <td class="px-3 py-3 text-sm text-gray-600"
                                        >{formatDate(item.submitted_at)}</td
                                    >
                                    <td class="px-3 py-3 text-sm">
                                        <span
                                            class="px-2 py-0.5 text-xs font-medium rounded-full {statusBadge(
                                                item.status,
                                            )}">{item.status}</span
                                        >
                                    </td>
                                </tr>
                            {:else}
                                <tr>
                                    <td
                                        colspan="4"
                                        class="px-3 py-6 text-center text-gray-500 text-sm"
                                        >No submissions yet.</td
                                    >
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Sidebar Info -->
        <div class="space-y-6">
            <!-- Active Grants -->
            <div
                class="bg-white p-6 rounded-xl shadow-sm border border-gray-100"
            >
                <h3 class="font-bold text-lg text-gray-900 mb-4">My Grants</h3>
                <div class="space-y-4">
                    {#each myGrants as grant}
                        <div
                            class="border-b border-gray-100 pb-3 last:border-0 last:pb-0"
                        >
                            <p class="font-semibold text-gray-900 text-sm">
                                {grant.title}
                            </p>
                            <p class="text-xs text-gray-600">
                                {grant.funder} • {grant.grant_code}
                            </p>
                            <div class="mt-2 flex items-center justify-between">
                                <span
                                    class="text-xs text-blue-700 bg-blue-50 px-2 py-0.5 rounded font-medium"
                                    >{grant.status}</span
                                >
                                <span class="text-xs text-gray-500"
                                    >Till: {formatDate(grant.end_date)}</span
                                >
                            </div>
                        </div>
                    {:else}
                        <p class="text-sm text-gray-500">
                            Not assigned to any grants yet.
                        </p>
                    {/each}
                </div>
            </div>

            <!-- Quick Actions -->
            <div
                class="bg-white p-6 rounded-xl shadow-sm border border-gray-200 bg-gradient-to-br from-blue-50 to-white"
            >
                <h3 class="font-bold text-lg text-gray-900 mb-3">
                    Quick Actions
                </h3>
                <div class="grid grid-cols-1 gap-2">
                    <button
                        on:click={() => router.goToSubmitExpense()}
                        class="flex items-center gap-3 p-3 bg-white border border-blue-100 rounded-lg text-sm text-blue-700 font-medium hover:border-blue-300 transition-colors shadow-sm"
                    >
                        <span class="text-xl">💸</span> Submit Expense Claim
                    </button>
                    <button
                        class="flex items-center gap-3 p-3 bg-white border border-blue-100 rounded-lg text-sm text-gray-700 font-medium hover:border-blue-300 transition-colors shadow-sm"
                    >
                        <span class="text-xl">📅</span> Activity Report
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>
