<!-- frontend/src/pages/Tasks.svelte -->
<script>
  import { onMount } from 'svelte';
  import { router } from '../stores/router.js';
  import Layout from '../components/Layout.svelte';
  import { user } from '../stores/auth.js';
  import CheckSquare from '../components/icons/CheckSquare.svelte';
  import FileText from '../components/icons/FileText.svelte';

  let tasks = $state([]);
  let isLoading = $state(true);
  let error = $state('');
  let showDeliverablesModal = $state(false);
  let selectedTask = $state(null);
  let deliverableFiles = $state([]);
  let deliverableNotes = $state('');
  let deliverableHoursWorked = $state('');
  let submittingDeliverables = $state(false);
  let deliverableError = $state('');
  let deliverableSuccess = $state('');
  let savedHoursWorked = $state(null);
  let myTasksOnly = $state(false); // Filter: All Tasks vs My Tasks

  let currentPage = $state(1);
  const pageSize = 10;

  let filteredTasks = $derived([...(myTasksOnly
    ? tasks.filter(t => Number(t.assigned_to) === Number($user?.id))
    : tasks)]
    .sort((a, b) => {
      // Sort by created_at descending (latest first)
      const dateA = new Date(a.created_at || a.id);
      const dateB = new Date(b.created_at || b.id);
      return dateB - dateA;
    }));

  let totalPages = $derived(Math.ceil(filteredTasks.length / pageSize));
  let paginatedTasks = $derived(filteredTasks.slice((currentPage - 1) * pageSize, currentPage * pageSize));

  // Reset page when filter changes
  $effect(() => {
    if (myTasksOnly) currentPage = 1;
  });

  onMount(async () => {
    if (!$user) {
      router.goToLogin();
      return;
    }
    await fetchTasks();
  });

  async function fetchTasks() {
    isLoading = true;
    error = '';
    try {
      const response = await fetch('/api/tasks', {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to fetch tasks');
      }

      const data = await response.json();
      tasks = data.tasks || [];
    } catch (err) {
      console.error('Error fetching tasks:', err);
      error = 'Failed to load tasks. Please try again.';
    } finally {
      isLoading = false;
    }
  }

  function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  }

  function isOverdue(task) {
    if (!task.deadline) return false;
    const deadline = new Date(task.deadline);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return deadline < today && task.status === 'assigned';
  }

  function getStatusBadgeClass(status) {
    const statusLower = (status || 'assigned').toLowerCase();
    if (statusLower === 'assigned' || statusLower === 'not_started') return 'bg-blue-100 text-blue-800';
    if (statusLower === 'submitted') return 'bg-amber-100 text-amber-800';
    if (statusLower === 'approved' || statusLower === 'completed') return 'bg-green-100 text-green-800';
    if (statusLower === 'overdue' || statusLower === 'revision_requested') return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  }

  function getStatusLabel(status) {
    const statusLower = (status || 'assigned').toLowerCase();
    if (statusLower === 'assigned' || statusLower === 'not_started') return 'Not Started';
    if (statusLower === 'submitted') return 'Submitted';
    if (statusLower === 'approved' || statusLower === 'completed') return 'Approved / Completed';
    if (statusLower === 'overdue') return 'Overdue';
    if (statusLower === 'revision_requested') return 'Revision Requested';
    if (statusLower === 'cancelled') return 'Cancelled';
    return status;
  }

  function validTaskId(id) {
    const n = Number(id);
    return Number.isInteger(n) && n > 0;
  }

  function openDeliverablesModal(task) {
    if (!validTaskId(task?.id)) {
      console.warn('Tasks: open deliverables skipped — invalid task id', task);
      return;
    }
    selectedTask = task;
    deliverableFiles = [];
    deliverableNotes = '';
    deliverableHoursWorked = task?.estimated_hours ?? '';
    deliverableError = '';
    deliverableSuccess = '';
    savedHoursWorked = null;
    showDeliverablesModal = true;
  }

  function closeDeliverablesModal() {
    showDeliverablesModal = false;
    selectedTask = null;
    deliverableFiles = [];
    deliverableNotes = '';
    deliverableHoursWorked = '';
    savedHoursWorked = null;
  }

  function handleFileChange(e) {
    deliverableFiles = Array.from(e.target.files);
  }

  async function submitDeliverables() {
    if (!selectedTask || !validTaskId(selectedTask.id)) {
      deliverableError = 'Invalid task — refresh the page and try again.';
      return;
    }

    submittingDeliverables = true;
    deliverableError = '';
    deliverableSuccess = '';

    try {
      const formData = new FormData();
      deliverableFiles.forEach(file => {
        formData.append('files', file);
      });
      formData.append('notes', deliverableNotes);
      formData.append('hours_worked', deliverableHoursWorked);

      const response = await fetch(`http://localhost:5000/api/tasks/${Number(selectedTask.id)}/deliverables`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to submit deliverables');
      }

      deliverableSuccess = 'Deliverables submitted successfully!';
      savedHoursWorked = data.hours_worked ?? deliverableHoursWorked;
      
      // Refresh tasks list
      await fetchTasks();
      
      // Close modal after 2 seconds
      setTimeout(() => {
        closeDeliverablesModal();
      }, 2000);
    } catch (err) {
      deliverableError = err.message || 'Failed to submit deliverables';
    } finally {
      submittingDeliverables = false;
    }
  }

  function canSubmitDeliverables(task) {
    return task.status === 'assigned' || task.status === 'overdue';
  }
</script>

<Layout>
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">
          {#if $user?.role === 'PI'}
            All Tasks
          {:else}
            My Tasks
          {/if}
        </h1>
        <p class="text-gray-600">
          {#if $user?.role === 'PI'}
            Manage tasks across your grants
          {:else}
            View and submit deliverables for your assigned tasks
          {/if}
        </p>
      </div>
      {#if $user?.role === 'PI'}
        <button
          onclick={() => router.goToCreateTask()}
          class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-150 shadow-sm"
        >
          <CheckSquare size={18} />
          <span>Create New Task</span>
        </button>
      {/if}
    </div>

    <!-- My Tasks / All Tasks toggle (PI only, allows PI to filter to their own assigned tasks) -->
    {#if $user?.role === 'PI'}
      <div class="mb-4 flex items-center gap-1 bg-gray-100 p-1 rounded-xl w-fit">
        <button
          onclick={() => myTasksOnly = false}
          class="px-4 py-1.5 rounded-lg text-sm font-semibold transition-all {!myTasksOnly ? 'bg-white shadow text-blue-700' : 'text-gray-500 hover:text-gray-700'}"
        >All Tasks</button>
        <button
          onclick={() => myTasksOnly = true}
          class="px-4 py-1.5 rounded-lg text-sm font-semibold transition-all {myTasksOnly ? 'bg-white shadow text-blue-700' : 'text-gray-500 hover:text-gray-700'}"
        >My Tasks</button>
      </div>
    {/if}


    {#if error}
      <div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
        <p class="text-red-700">{error}</p>
      </div>
    {/if}

    <!-- Loading State -->
    {#if isLoading}
      <div class="flex flex-col items-center justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
        <p class="text-gray-600">Loading tasks...</p>
      </div>
    {:else if tasks.length === 0}
      <!-- Empty State -->
      <div class="bg-white/40 backdrop-blur-xl border border-white/30 rounded-2xl shadow-lg p-12 text-center">
        <CheckSquare size={64} class="mx-auto text-gray-400 mb-4" />
        <h3 class="text-xl font-semibold text-gray-900 mb-2">No Tasks Yet</h3>
        <p class="text-gray-600 mb-6">
          {#if $user?.role === 'PI'}
            You haven't created any tasks yet. Click 'Create New Task' to get started.
          {:else}
            No tasks assigned yet.
          {/if}
        </p>
        {#if $user?.role === 'PI'}
          <button
            onclick={() => router.goToCreateTask()}
            class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-150"
          >
            Create New Task
          </button>
        {/if}
      </div>
    {:else}
      <!-- Tasks Table -->
      <div class="bg-white/40 backdrop-blur-xl border border-white/30 rounded-2xl shadow-lg overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50/80 border-b border-gray-200">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Task Title</th>
                {#if $user?.role === 'PI'}
                  <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Assigned To</th>
                {/if}
                <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Grant</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Milestone</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Task Type</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Deadline</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Hours</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              {#each paginatedTasks as task}
                <tr class="hover:bg-blue-50/50 transition-colors duration-150">
                  <td class="px-6 py-4">
                    <div class="text-sm font-medium text-gray-900">{task.title}</div>
                    {#if task.description}
                      <div class="text-xs text-gray-500 mt-1">{task.description}</div>
                    {/if}
                  </td>
                  {#if $user?.role === 'PI'}
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="text-sm text-gray-700">{task.assigned_to_name}</div>
                      <div class="text-xs text-gray-500">{task.assigned_to_email}</div>
                    </td>
                  {/if}
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-700">{task.grant_title}</div>
                    {#if task.grant_code}
                      <div class="text-xs text-gray-500 font-mono">{task.grant_code}</div>
                    {/if}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-700">{task.milestone_title || 'General'}</div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-700">{task.task_type}</div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-700 {isOverdue(task) ? 'text-red-600 font-semibold' : ''}">
                      {formatDate(task.deadline)}
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-700">{task.estimated_hours}h</div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full {getStatusBadgeClass(task.status)}">
                      {getStatusLabel(task.status)}
                    </span>
                  </td>
                  <!-- Action column: show Submit button for anyone assigned to this task with pending status -->
                  <td class="px-6 py-4 whitespace-nowrap">
                    {#if canSubmitDeliverables(task) && Number(task.assigned_to) === Number($user?.id)}
                      <button
                        onclick={() => openDeliverablesModal(task)}
                        class="text-blue-600 hover:text-blue-800 text-sm font-bold focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-lg px-3 py-1.5 bg-blue-50 hover:bg-blue-100 transition-all"
                      >
                        📤 Submit Work
                      </button>
                    {:else}
                      <span class="text-sm text-gray-400">—</span>
                    {/if}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>

        {#if totalPages > 1}
          <div class="px-6 py-4 bg-gray-50/50 border-t border-gray-200 flex items-center justify-between">
            <div class="text-sm text-gray-600">
              Showing <span class="font-bold">{(currentPage - 1) * pageSize + 1}</span> to <span class="font-bold">{Math.min(currentPage * pageSize, filteredTasks.length)}</span> of <span class="font-bold">{filteredTasks.length}</span> tasks
            </div>
            <div class="flex items-center gap-2">
              <button
                onclick={() => currentPage = Math.max(1, currentPage - 1)}
                disabled={currentPage === 1}
                class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-bold text-gray-600 hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                Previous
              </button>
              <div class="flex items-center gap-1">
                {#each Array(totalPages) as _, i}
                   {#if totalPages <= 5 || (i + 1 >= currentPage - 1 && i + 1 <= currentPage + 1) || i === 0 || i === totalPages - 1}
                     <button
                       onclick={() => currentPage = i + 1}
                       class="w-8 h-8 rounded-lg text-xs font-bold transition-all {currentPage === i + 1 ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-500 hover:bg-gray-100'}"
                     >
                       {i + 1}
                     </button>
                   {:else if i === 1 || i === totalPages - 2}
                     <span class="text-gray-400">...</span>
                   {/if}
                {/each}
              </div>
              <button
                onclick={() => currentPage = Math.min(totalPages, currentPage + 1)}
                disabled={currentPage === totalPages}
                class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-bold text-gray-600 hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                Next
              </button>
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>

  <!-- Deliverables Submission Modal -->
  {#if showDeliverablesModal && selectedTask}
    <div class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" onclick={closeDeliverablesModal} role="button" tabindex="0" onkeydown={(e) => e.key === 'Escape' && closeDeliverablesModal()}>
      <div class="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onclick={(e) => e.stopPropagation()} role="presentation">
        <div class="p-6 border-b border-gray-200">
          <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900">Submit Deliverables</h2>
            <button
              onclick={closeDeliverablesModal}
              class="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>
          <p class="text-sm text-gray-600 mt-1">Task: {selectedTask.title}</p>
        </div>

        <div class="p-6 space-y-6">
          <!-- Required Deliverables Instructions -->
          {#if selectedTask.deliverable_rules && selectedTask.deliverable_rules.length > 0}
            <div class="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p class="text-sm font-semibold text-blue-900 mb-2">Required Deliverables:</p>
              <ul class="text-sm text-blue-800 list-disc list-inside space-y-1">
                {#each selectedTask.deliverable_rules as rule}
                  <li>{rule}</li>
                {/each}
              </ul>
            </div>
          {/if}

          <!-- Error/Success Messages -->
          {#if deliverableError}
            <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p class="text-red-700">{deliverableError}</p>
            </div>
          {/if}

          {#if deliverableSuccess}
            <div class="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p class="text-green-700">{deliverableSuccess}</p>
              {#if savedHoursWorked !== null}
                <p class="text-xs text-green-700 mt-1">
                  Recorded hours: <span class="font-semibold">{savedHoursWorked}h</span>
                </p>
              {/if}
            </div>
          {/if}

          <!-- File Upload -->
          <div>
            <label for="deliverable_files" class="block text-sm font-medium text-gray-700 mb-1">
              Upload Files *
            </label>
            <input
              id="deliverable_files"
              type="file"
              multiple
              accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.csv"
              onchange={handleFileChange}
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {#if deliverableFiles.length > 0}
              <div class="mt-2 space-y-1">
                {#each deliverableFiles as file}
                  <p class="text-sm text-green-600">✓ {file.name}</p>
                {/each}
              </div>
            {/if}
            <p class="mt-1 text-xs text-gray-500">Accepted: Images, PDF, Word, Excel, CSV</p>
          </div>

          <!-- Notes -->
          <div>
            <label for="deliverable_hours" class="block text-sm font-medium text-gray-700 mb-1">
              Actual Hours Worked
            </label>
            <input
              id="deliverable_hours"
              type="number"
              min="0"
              step="0.25"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              bind:value={deliverableHoursWorked}
              placeholder="e.g. 6.5"
            />
            <p class="mt-1 text-xs text-gray-500">
              Prefilled from estimated hours ({selectedTask.estimated_hours}h). Adjust to actual time spent.
            </p>
          </div>

          <!-- Notes -->
          <div>
            <label for="deliverable_notes" class="block text-sm font-medium text-gray-700 mb-1">
              Activity Notes (Optional)
            </label>
            <textarea
              id="deliverable_notes"
              rows="4"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              bind:value={deliverableNotes}
              placeholder="Describe the work completed, methodology used, or any relevant details..."
            ></textarea>
          </div>

          <!-- Submit Button -->
          <div class="flex gap-4 pt-4">
            <button
              onclick={submitDeliverables}
              disabled={submittingDeliverables || deliverableFiles.length === 0}
              class="flex-1 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150"
            >
              {submittingDeliverables ? 'Submitting...' : 'Submit Deliverables'}
            </button>
            <button
              onclick={closeDeliverablesModal}
              class="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-all duration-150"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  {/if}
</Layout>



