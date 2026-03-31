<script>
    import { onMount } from "svelte";
    import axios from "axios";
    import { user } from "../stores/auth.js";
    import { router } from "../stores/router.js";
    import { notifications } from "../stores/notifications.js";
    import Icon from "../components/Icon.svelte";

    // Enable credentials for Flask sessions
    axios.defaults.withCredentials = true;

    let loading = $state(true);
    let myGrants = $state([]);
    let myTasks = $state([]);
    let myDeliverables = $state([]);
    let myExpenses = $state([]);

    let currentPage = $state(1);
    const pageSize = 5;

    let sortedTasks = $derived([...myTasks].sort((a, b) => {
        const dateA = new Date(a.created_at || a.id);
        const dateB = new Date(b.created_at || b.id);
        return dateB - dateA;
    }));

    let pendingTasks = $derived(sortedTasks.filter(
        (t) =>
            t.status === "assigned" ||
            t.status === "in_progress" ||
            t.status === "overdue" ||
            t.status === "revision_requested",
    ));

    let totalPages = $derived(Math.ceil(pendingTasks.length / pageSize));
    let paginatedPendingTasks = $derived(pendingTasks.slice((currentPage - 1) * pageSize, currentPage * pageSize));

    let activeGrantsCount = $derived(myGrants.length);
    let completedTasks = $derived(myTasks.filter((t) => t.status === "completed" || t.status === "approved"));
    let totalHours = $derived(myDeliverables.reduce(
        (sum, e) => sum + (e.hours_worked || 0),
        0,
    ));
    let estimatedEarnings = $derived(totalHours * ($user?.pay_rate || 0));
    let unreadCount = $derived($notifications.length);

    async function fetchDashboardData() {
        loading = true;
        try {
            const [grantsRes, tasksRes, deliverablesRes, expensesRes] =
                await Promise.all([
                    axios.get("/api/grants"),
                    axios.get("/api/tasks"),
                    axios.get("/api/deliverables"),
                    axios.get("/api/expenses"),
                ]);

            myGrants = grantsRes.data.grants || [];
            myTasks = (tasksRes.data.tasks || []).filter(t => Number(t.assigned_to) === Number($user?.id));
            myDeliverables = deliverablesRes.data.submissions || [];
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
            return "bg-green-500/10 text-green-600 border-green-500/20";
        if (s === "assigned" || s === "pending")
            return "bg-blue-500/10 text-blue-600 border-blue-500/20";
        if (s === "overdue" || s === "revision_requested") 
            return "bg-red-500/10 text-red-600 border-red-500/20";
        if (s === "submitted") return "bg-amber-500/10 text-amber-600 border-amber-500/20";
        return "bg-gray-500/10 text-gray-700 border-gray-500/20";
    }

    function formatDate(dateStr) {
        if (!dateStr) return "N/A";
        return new Date(dateStr).toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
            year: "numeric"
        });
    }

    function getInitials(name) {
        return name?.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2) || "U";
    }

    // --- Quick Progress Note ---
    let noteModalOpen = $state(false);
    let selectedTaskId = $state(null);
    let selectedTaskTitle = $state('');
    let noteText = $state('');
    let noteSubmitting = $state(false);
    let noteSuccess = $state(null);

    function openNoteModal(task) {
        selectedTaskId = task.id;
        selectedTaskTitle = task.title;
        noteText = '';
        noteSuccess = null;
        noteModalOpen = true;
    }

    function closeNoteModal() {
        noteModalOpen = false;
    }

    async function submitProgressNote() {
        if (!noteText.trim() || !selectedTaskId) return;
        noteSubmitting = true;
        try {
            await axios.post(`/api/tasks/${selectedTaskId}/progress-note`, { note: noteText });
            noteSuccess = 'Note sent to PI ✅';
            setTimeout(() => closeNoteModal(), 1800);
        } catch (e) {
            alert('Failed to send note. Please try again.');
        } finally {
            noteSubmitting = false;
        }
    }
</script>

<div class="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
    <!-- Profile & Hero Section -->
    <div
        class="bg-white/40 backdrop-blur-xl p-10 rounded-[2.5rem] border border-white/40 shadow-2xl relative overflow-hidden group"
    >
        <div class="absolute -right-20 -top-20 w-80 h-80 bg-blue-400/10 rounded-full blur-[80px] group-hover:bg-blue-400/20 transition-all duration-1000"></div>
        <div class="absolute -left-20 -bottom-20 w-80 h-80 bg-indigo-400/10 rounded-full blur-[80px] group-hover:bg-indigo-400/20 transition-all duration-1000"></div>

        <div class="flex flex-col md:flex-row md:items-center justify-between gap-8 relative z-10">
            <div class="flex items-center gap-6">
                <div
                    class="h-20 w-20 rounded-3xl bg-gradient-to-br from-blue-600 to-indigo-600 shadow-xl shadow-blue-200 flex items-center justify-center text-white font-black text-3xl"
                >
                    {getInitials($user?.name)}
                </div>
                <div>
                    <div class="inline-flex items-center gap-2 px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-600 text-[10px] font-black uppercase tracking-widest mb-2">
                        <span class="w-1.5 h-1.5 bg-blue-600 rounded-full animate-pulse"></span>
                        Active Session
                    </div>
                    <h2 class="text-4xl font-black text-gray-900 tracking-tight">
                        Hi, {$user?.name?.split(" ")[0] || "Team Member"}
                    </h2>
                    <p class="text-gray-500 font-medium">
                        {$user?.email} • <span class="text-indigo-600 font-bold">{$user?.role}</span>
                    </p>
                </div>
            </div>
            
            <div class="flex flex-col md:items-end">
                <p class="text-[10px] text-gray-400 uppercase tracking-[0.3em] font-black mb-1">Current Pay Rate</p>
                <div class="flex items-baseline gap-2">
                    <span class="text-4xl font-black text-gray-900">MWK {$user?.pay_rate?.toLocaleString() || 0}</span>
                    <span class="text-gray-400 font-bold text-sm">/ hr</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div class="bg-white/40 backdrop-blur-md p-6 rounded-[2rem] border border-white/40 shadow-lg hover:-translate-y-1 transition-all duration-300">
            <div class="w-12 h-12 bg-blue-500/10 rounded-2xl flex items-center justify-center text-blue-600 mb-4">
                <Icon name="folder" size={24} />
            </div>
            <p class="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1">Total Grants</p>
            <p class="text-3xl font-black text-gray-900 leading-tight">{activeGrantsCount}</p>
        </div>

        <div class="bg-white/40 backdrop-blur-md p-6 rounded-[2rem] border border-white/40 shadow-lg hover:-translate-y-1 transition-all duration-300">
            <div class="w-12 h-12 bg-amber-500/10 rounded-2xl flex items-center justify-center text-amber-600 mb-4">
                <Icon name="tasks" size={24} />
            </div>
            <p class="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1">Tasks Pending</p>
            <p class="text-3xl font-black text-amber-600 leading-tight">{pendingTasks.length}</p>
        </div>

        <div class="bg-white/40 backdrop-blur-md p-6 rounded-[2rem] border border-white/40 shadow-lg hover:-translate-y-1 transition-all duration-300">
            <div class="w-12 h-12 bg-emerald-500/10 rounded-2xl flex items-center justify-center text-emerald-600 mb-4">
                <Icon name="clock" size={24} />
            </div>
            <p class="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1">Total Hours</p>
            <p class="text-3xl font-black text-emerald-600 leading-tight">{totalHours}</p>
        </div>

        <div class="bg-white/40 backdrop-blur-md p-6 rounded-[2rem] border border-white/40 shadow-lg hover:-translate-y-1 transition-all duration-300">
            <div class="w-12 h-12 bg-indigo-500/10 rounded-2xl flex items-center justify-center text-indigo-600 mb-4">
                <Icon name="money" size={24} />
            </div>
            <p class="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1">Est. Earnings</p>
            <p class="text-3xl font-black text-indigo-600 leading-tight">{estimatedEarnings.toLocaleString()}</p>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 text-gray-900">
        <!-- Main Column -->
        <div class="lg:col-span-2 space-y-8">
            <div class="bg-white/40 backdrop-blur-xl p-8 rounded-[2.5rem] border border-white/40 shadow-2xl overflow-hidden relative">
                    <div>
                        <h3 class="text-2xl font-black tracking-tight">Priority Task Queue</h3>
                        <p class="text-sm text-gray-500 font-medium">Items requiring your immediate scientific attention</p>
                    </div>
                    {#if totalPages > 1}
                        <div class="flex items-center gap-2">
                             <button
                                onclick={() => currentPage = Math.max(1, currentPage - 1)}
                                disabled={currentPage === 1}
                                class="px-3 py-1.5 bg-white/60 border border-white/60 rounded-xl text-[10px] font-black uppercase tracking-widest disabled:opacity-30 disabled:cursor-not-allowed hover:bg-white transition-all shadow-sm"
                            >
                                Prev
                            </button>
                            <span class="text-[10px] font-black text-gray-400 uppercase tracking-widest px-2">Page {currentPage} / {totalPages}</span>
                            <button
                                onclick={() => currentPage = Math.min(totalPages, currentPage + 1)}
                                disabled={currentPage === totalPages}
                                class="px-3 py-1.5 bg-gradient-to-br from-gray-900 to-gray-800 text-white rounded-xl text-[10px] font-black uppercase tracking-widest disabled:opacity-30 disabled:cursor-not-allowed hover:shadow-lg transition-all shadow-md"
                            >
                                Next
                            </button>
                        </div>
                    {/if}

                <div class="space-y-4 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                    {#each paginatedPendingTasks as task}
                        <div class="p-6 rounded-3xl bg-white/60 border border-white/60 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6 hover:bg-white/80 transition-all duration-300">
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-2 mb-1">
                                    <p class="font-black text-lg text-gray-900 truncate">{task.title}</p>
                                    {#if task.status === 'overdue'}
                                        <span class="px-2 py-0.5 bg-red-100 text-red-600 text-[9px] font-black uppercase rounded">Overdue</span>
                                    {/if}
                                </div>
                                <div class="flex items-center gap-3 text-xs text-gray-500 font-bold">
                                    <span class="text-indigo-600">{task.grant_title}</span>
                                    <span>•</span>
                                    <span>Due: {formatDate(task.deadline)}</span>
                                </div>
                            </div>
                            <div class="flex items-center gap-3">
                                <span class="px-3 py-1 text-[10px] font-black uppercase tracking-wider rounded-xl border {statusBadge(task.status)}">
                                    {task.status}
                                </span>
                                <button
                                    onclick={() => openNoteModal(task)}
                                    title="Log a progress note"
                                    class="px-3 py-2.5 bg-white/60 border border-gray-200 text-gray-600 text-sm rounded-xl hover:bg-amber-50 hover:border-amber-300 hover:text-amber-700 transition-all"
                                >💬</button>
                                <button
                                    onclick={() => router.goToTasks()}
                                    class="px-6 py-2.5 bg-gradient-to-br from-gray-900 to-gray-800 text-white text-[10px] font-black uppercase tracking-widest rounded-xl shadow-xl shadow-gray-200 hover:shadow-gray-300 hover:-translate-y-0.5 transition-all"
                                >
                                    Work
                                </button>
                            </div>
                        </div>
                    {:else}
                        <div class="text-center py-20 bg-white/30 rounded-3xl border border-dashed border-gray-200">
                            <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-300">
                                <Icon name="check" size={32} />
                            </div>
                            <p class="text-gray-500 font-bold">Your queue is empty. Great work!</p>
                        </div>
                    {/each}
                </div>
            </div>

            <!-- Recent Activity Table -->
            <div class="bg-white/40 backdrop-blur-xl p-8 rounded-[2.5rem] border border-white/40 shadow-2xl overflow-hidden">
                <h3 class="text-2xl font-black tracking-tight mb-6">Recent Submissions</h3>
                <div class="overflow-x-auto">
                    <table class="w-full">
                        <thead>
                            <tr class="text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-100">
                                <th class="text-left py-4 px-4">Task</th>
                                <th class="text-left py-4 px-4">Logged Hours</th>
                                <th class="text-left py-4 px-4">Submitted On</th>
                                <th class="text-right py-4 px-4">Verification</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-50">
                            {#each myDeliverables.slice(0, 8) as item}
                                <tr class="hover:bg-blue-50/30 transition-all duration-150">
                                    <td class="py-5 px-4">
                                        <p class="font-black text-sm text-gray-900">{item.task_title}</p>
                                        <p class="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Deliverable</p>
                                    </td>
                                    <td class="py-5 px-4">
                                        <span class="font-black text-sm text-gray-900">{item.hours_worked}h</span>
                                    </td>
                                    <td class="py-5 px-4 font-bold text-sm text-gray-500">
                                        {formatDate(item.submitted_at)}
                                    </td>
                                    <td class="py-5 px-4 text-right">
                                        <span class="px-2 py-1 text-[9px] font-black uppercase tracking-widest rounded-lg border {statusBadge(item.status)}">
                                            {item.status}
                                        </span>
                                    </td>
                                </tr>
                            {:else}
                                <tr>
                                    <td colspan="4" class="py-12 text-center text-gray-400 font-bold italic">No submissions logged yet.</td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Sidebar Actions -->
        <div class="space-y-8">
            <!-- Active Grants -->
            <div class="bg-white/40 backdrop-blur-xl p-8 rounded-[2.5rem] border border-white/40 shadow-2xl">
                <h3 class="text-xl font-black tracking-tight mb-6">My Assignments</h3>
                <div class="space-y-6">
                    {#each myGrants as grant}
                        <div class="relative pl-6 border-l-2 border-blue-500/20 hover:border-blue-500 transition-colors">
                            <p class="font-black text-sm text-gray-900 mb-1">{grant.title}</p>
                            <p class="text-[10px] text-gray-400 font-black uppercase tracking-widest">{grant.grant_code} • {grant.funder}</p>
                            <div class="flex items-center gap-2 mt-2">
                                <span class="text-[9px] px-2 py-0.5 bg-blue-50 text-blue-600 font-black rounded uppercase">{grant.status}</span>
                                <span class="text-[9px] text-gray-400 font-bold">Till {formatDate(grant.end_date)}</span>
                            </div>
                        </div>
                    {:else}
                        <p class="text-sm text-gray-500 italic">No assigned grants found.</p>
                    {/each}
                </div>
            </div>

            <!-- Quick Utilities -->
            <div class="bg-gradient-to-br from-indigo-600 to-blue-700 p-8 rounded-[2.5rem] shadow-2xl text-white relative overflow-hidden">
                <div class="absolute -right-10 -bottom-10 w-40 h-40 bg-white/10 rounded-full blur-2xl"></div>
                <h3 class="text-xl font-black tracking-tight mb-4 relative z-10">Quick Utilities</h3>
                
                <div class="space-y-3 relative z-10">
                    <button
                        onclick={() => router.goToExpenses()}
                        class="w-full flex items-center justify-between p-4 bg-white/10 hover:bg-white/20 border border-white/10 rounded-2xl transition-all"
                    >
                        <span class="font-black text-xs uppercase tracking-widest">New Expense Claim</span>
                        <Icon name="plus" size={16} />
                    </button>
                    <button
                        onclick={() => router.goToEffort()}
                        class="w-full flex items-center justify-between p-4 bg-white/10 hover:bg-white/20 border border-white/10 rounded-2xl transition-all"
                    >
                        <span class="font-black text-xs uppercase tracking-widest">Log Effort</span>
                        <Icon name="clock" size={16} />
                    </button>
                    <button
                        onclick={() => router.goToNotifications()}
                        class="w-full flex items-center justify-between p-4 bg-white/10 hover:bg-white/20 border border-white/10 rounded-2xl transition-all"
                    >
                        <span class="font-black text-xs uppercase tracking-widest">My Alerts</span>
                        <div class="flex items-center gap-2">
                             {#if unreadCount > 0}
                                <span class="w-2 h-2 bg-rose-400 rounded-full"></span>
                             {/if}
                             <Icon name="bell" size={16} />
                        </div>
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- 💬 Quick Progress Note Modal -->
{#if noteModalOpen}
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
        <div class="bg-white rounded-3xl shadow-2xl max-w-md w-full p-8 animate-in zoom-in duration-200">
            <div class="flex items-center gap-3 mb-6">
                <div class="h-12 w-12 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-2xl shadow">
                    💬
                </div>
                <div>
                    <h2 class="text-xl font-black text-gray-900">Log Progress Note</h2>
                    <p class="text-sm text-gray-500 truncate max-w-[220px]">{selectedTaskTitle}</p>
                </div>
            </div>

            {#if noteSuccess}
                <div class="text-center py-6">
                    <p class="text-5xl mb-2">✅</p>
                    <p class="font-bold text-gray-700">{noteSuccess}</p>
                </div>
            {:else}
                <textarea
                    bind:value={noteText}
                    rows="4"
                    placeholder="e.g. Stuck waiting for lab results. Will upload deliverable by Friday..."
                    class="w-full border border-gray-200 rounded-2xl px-4 py-3 text-sm focus:ring-2 focus:ring-amber-300 focus:border-amber-400 outline-none resize-none mb-6"
                ></textarea>
                <p class="text-xs text-gray-400 mb-4">The PI will receive a silent notification with your update.</p>

                <div class="flex gap-3">
                    <button
                        onclick={closeNoteModal}
                        class="flex-1 py-3 rounded-2xl border border-gray-200 text-gray-600 text-sm font-semibold hover:bg-gray-50 transition-colors"
                    >Cancel</button>
                    <button
                        onclick={submitProgressNote}
                        disabled={noteSubmitting || !noteText.trim()}
                        class="flex-1 py-3 rounded-2xl bg-gradient-to-r from-amber-500 to-orange-500 text-white text-sm font-bold hover:opacity-90 disabled:opacity-40 transition-all shadow"
                    >{noteSubmitting ? 'Sending...' : '📨 Send to PI'}</button>
                </div>
            {/if}
        </div>
    </div>
{/if}

<style>
    .custom-scrollbar::-webkit-scrollbar {
        width: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
        background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background: rgba(0,0,0,0.05);
        border-radius: 10px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
        background: rgba(0,0,0,0.1);
    }
</style>
