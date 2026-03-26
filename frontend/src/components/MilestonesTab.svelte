<script>
    import { onMount } from "svelte";
    import axios from "axios";
    import Icon from "./Icon.svelte";

    export let grantId;
    export let grantTitle;

    let milestones = [];
    let isLoading = true;
    let error = "";
    
    // Modal state
    let showModal = false;
    let editingMilestone = null;
    let isSaving = false;
    
    // Form state
    let milestoneForm = {
        title: "",
        description: "",
        due_date: "",
        reporting_period: "",
        triggers_tranche: null
    };

    onMount(fetchMilestones);

    async function fetchMilestones() {
        isLoading = true;
        try {
            const res = await axios.get(`http://localhost:5000/api/grants/${grantId}/milestones`, {
                withCredentials: true
            });
            milestones = res.data;
        } catch (err) {
            console.error(err);
            error = "Failed to load milestones.";
        } finally {
            isLoading = false;
        }
    }

    function openAddModal() {
        editingMilestone = null;
        milestoneForm = {
            title: "",
            description: "",
            due_date: "",
            reporting_period: "",
            triggers_tranche: null
        };
        showModal = true;
    }

    function openEditModal(milestone) {
        editingMilestone = milestone;
        milestoneForm = {
            title: milestone.title,
            description: milestone.description || "",
            due_date: milestone.due_date,
            reporting_period: milestone.reporting_period || "",
            triggers_tranche: milestone.triggers_tranche
        };
        showModal = true;
    }

    async function handleSave() {
        if (!milestoneForm.title || !milestoneForm.due_date) {
            alert("Title and Due Date are required.");
            return;
        }

        isSaving = true;
        try {
            if (editingMilestone) {
                await axios.put(`http://localhost:5000/api/milestones/${editingMilestone.id}`, {
                    ...milestoneForm,
                    grant_id: grantId
                }, { withCredentials: true });
            } else {
                await axios.post(`http://localhost:5000/api/milestones`, {
                    ...milestoneForm,
                    grant_id: grantId
                }, { withCredentials: true });
            }
            showModal = false;
            fetchMilestones();
        } catch (err) {
            console.error(err);
            alert(err.response?.data?.error || "Failed to save milestone.");
        } finally {
            isSaving = false;
        }
    }

    async function handleDelete(milestoneId) {
        if (!confirm("Are you sure you want to delete this milestone? This cannot be undone.")) {
            return;
        }

        try {
            await axios.delete(`http://localhost:5000/api/milestones/${milestoneId}`, {
                withCredentials: true
            });
            fetchMilestones();
        } catch (err) {
            console.error(err);
            alert(err.response?.data?.error || "Failed to delete milestone.");
        }
    }

    async function moveMilestone(index, direction) {
        const newMilestones = [...milestones];
        const newIndex = index + direction;
        
        if (newIndex < 0 || newIndex >= newMilestones.length) return;
        
        const temp = newMilestones[index];
        newMilestones[index] = newMilestones[newIndex];
        newMilestones[newIndex] = temp;
        
        milestones = newMilestones;
        
        // Persist to backend
        try {
            await axios.post(`http://localhost:5000/api/grants/${grantId}/milestones/reorder`, {
                ordered_ids: milestones.map(m => m.id)
            }, { withCredentials: true });
        } catch (err) {
            console.error(err);
            error = "Failed to save new order.";
        }
    }

    function getStatusBadge(status) {
        switch (status) {
            case "completed": return "bg-emerald-100 text-emerald-800";
            case "in_progress": return "bg-blue-100 text-blue-800";
            default: return "bg-gray-100 text-gray-700";
        }
    }

    function formatDate(dateStr) {
        if (!dateStr) return "N/A";
        return new Date(dateStr).toLocaleDateString("en-GB", {
            day: "2-digit",
            month: "short",
            year: "numeric"
        });
    }
</script>

<div class="space-y-6">
    <div class="flex items-center justify-between">
        <div>
            <h2 class="text-lg font-bold text-gray-900">Project Milestones</h2>
            <p class="text-xs text-gray-600">Define and track execution phases for {grantTitle}.</p>
        </div>
        <button 
            on:click={openAddModal}
            class="px-4 py-2 bg-blue-600 text-white text-xs font-bold rounded-xl shadow-sm hover:bg-blue-700 transition-all flex items-center gap-2"
        >
            <Icon name="plus" size={14} />
            Add Milestone
        </button>
    </div>

    {#if isLoading}
        <div class="flex flex-col items-center justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
            <p class="text-xs text-gray-500 font-medium">Loading milestones...</p>
        </div>
    {:else if milestones.length === 0}
        <div class="text-center py-16 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200">
            <div class="text-3xl mb-3">📍</div>
            <h3 class="text-sm font-bold text-gray-900">No Milestones Set</h3>
            <p class="text-xs text-gray-500 mb-6">Break down your project into manageable phases.</p>
            <button 
                on:click={openAddModal}
                class="px-4 py-2 border border-blue-600 text-blue-600 text-xs font-bold rounded-xl hover:bg-blue-50 transition-all"
            >
                Create Your First Milestone
            </button>
        </div>
    {:else}
        <div class="space-y-3">
            {#each milestones as milestone, i}
                <div class="group bg-white border border-gray-100 rounded-2xl p-4 shadow-sm hover:shadow-md transition-all flex items-center gap-4">
                    <!-- Order controls -->
                    <div class="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button 
                            on:click={() => moveMilestone(i, -1)}
                            disabled={i === 0}
                            class="p-1 hover:bg-gray-100 rounded disabled:opacity-30"
                        >
                            <Icon name="chevron-up" size={14} />
                        </button>
                        <button 
                            on:click={() => moveMilestone(i, 1)}
                            disabled={i === milestones.length - 1}
                            class="p-1 hover:bg-gray-100 rounded disabled:opacity-30"
                        >
                            <Icon name="chevron-down" size={14} />
                        </button>
                    </div>

                    <div class="flex-1 space-y-1">
                        <div class="flex items-center gap-2">
                            <span class="w-6 h-6 rounded-lg bg-blue-50 text-blue-700 text-[10px] font-black flex items-center justify-center border border-blue-100">
                                {milestone.sequence}
                            </span>
                            <h4 class="text-sm font-bold text-gray-900">{milestone.title}</h4>
                            <span class={"px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider " + getStatusBadge(milestone.status)}>
                                {milestone.status.replace('_', ' ')}
                            </span>
                            {#if milestone.triggers_tranche}
                                <span class="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 text-[10px] font-bold">
                                    Triggers Tranche {milestone.triggers_tranche}
                                </span>
                            {/if}
                        </div>
                        <p class="text-xs text-gray-600 line-clamp-1">{milestone.description || 'No description'}</p>
                        <div class="flex items-center gap-4 text-[10px] text-gray-500 font-medium">
                            <span class="flex items-center gap-1">
                                <Icon name="calendar" size={12} />
                                Due: {formatDate(milestone.due_date)}
                            </span>
                            {#if milestone.reporting_period}
                                <span class="flex items-center gap-1">
                                    <Icon name="info" size={12} />
                                    Period: {milestone.reporting_period}
                                </span>
                            {/if}
                        </div>
                    </div>

                    <div class="flex items-center gap-1">
                        <button 
                            on:click={() => openEditModal(milestone)}
                            class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all"
                            title="Edit"
                        >
                            <Icon name="edit" size={16} />
                        </button>
                        <button 
                            on:click={() => handleDelete(milestone.id)}
                            class="p-2 text-gray-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-all"
                            title="Delete"
                        >
                            <Icon name="delete" size={16} />
                        </button>
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>

<!-- Modal -->
{#if showModal}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm">
    <div class="bg-white w-full max-w-md rounded-3xl shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-lg font-bold text-gray-900">
                {editingMilestone ? 'Edit Milestone' : 'Add New Milestone'}
            </h3>
            <button on:click={() => showModal = false} class="text-gray-400 hover:text-gray-600 transition-all">
                &times;
            </button>
        </div>
        
        <div class="p-6 space-y-4">
            <div class="space-y-1">
                <label for="m-title" class="text-[10px] font-black uppercase tracking-widest text-gray-500">Title</label>
                <input 
                    id="m-title"
                    bind:value={milestoneForm.title}
                    type="text" 
                    placeholder="Phase 1: Research Initiation"
                    class="w-full px-4 py-3 bg-gray-50 border-0 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500/20"
                />
            </div>

            <div class="space-y-1">
                <label for="m-desc" class="text-[10px] font-black uppercase tracking-widest text-gray-500">Description</label>
                <textarea 
                    id="m-desc"
                    bind:value={milestoneForm.description}
                    rows="3"
                    placeholder="Key deliverables and goals for this phase..."
                    class="w-full px-4 py-3 bg-gray-50 border-0 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500/20"
                ></textarea>
            </div>

            <div class="grid grid-cols-2 gap-4">
                <div class="space-y-1">
                    <label for="m-due" class="text-[10px] font-black uppercase tracking-widest text-gray-500">Due Date</label>
                    <input 
                        id="m-due"
                        bind:value={milestoneForm.due_date}
                        type="date"
                        class="w-full px-4 py-3 bg-gray-50 border-0 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500/20"
                    />
                </div>
                <div class="space-y-1">
                    <label for="m-period" class="text-[10px] font-black uppercase tracking-widest text-gray-500">Reporting Period</label>
                    <input 
                        id="m-period"
                        bind:value={milestoneForm.reporting_period}
                        type="text"
                        placeholder="e.g. Q1 Year 1"
                        class="w-full px-4 py-3 bg-gray-50 border-0 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500/20"
                    />
                </div>
            </div>

            <div class="space-y-1">
                <label for="m-tranche" class="text-[10px] font-black uppercase tracking-widest text-gray-500">Tranche release trigger</label>
                <select 
                    id="m-tranche"
                    bind:value={milestoneForm.triggers_tranche}
                    class="w-full px-4 py-3 bg-gray-50 border-0 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500/20"
                >
                    <option value={null}>None</option>
                    <option value={1}>Tranche 1</option>
                    <option value={2}>Tranche 2</option>
                    <option value={3}>Tranche 3</option>
                </select>
                <p class="text-[10px] text-gray-400 italic">Completing this milestone will be a requirement for this tranche release.</p>
            </div>
        </div>

        <div class="px-6 py-4 bg-gray-50/50 flex items-center justify-end gap-3">
            <button 
                on:click={() => showModal = false}
                class="px-5 py-2 text-xs font-bold text-gray-500 hover:text-gray-700 transition-all"
            >
                Cancel
            </button>
            <button 
                on:click={handleSave}
                disabled={isSaving}
                class="px-6 py-2 bg-blue-600 text-white text-xs font-bold rounded-xl shadow-lg hover:bg-blue-700 disabled:opacity-50 transition-all"
            >
                {isSaving ? 'Saving...' : editingMilestone ? 'Update Milestone' : 'Create Milestone'}
            </button>
        </div>
    </div>
</div>
{/if}

<style>
    /* Add any custom animations if needed */
    .line-clamp-1 {
        display: -webkit-box;
        -webkit-line-clamp: 1;
        line-clamp: 1;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>
