<!-- frontend/src/pages/Tasks.svelte -->
<script>
  import { onMount } from 'svelte';
  import { router } from '../stores/router.js';
  import Layout from '../components/Layout.svelte';
  import { user } from '../stores/auth.js';
  import CheckSquare from '../components/icons/CheckSquare.svelte';
  import FileText from '../components/icons/FileText.svelte';

  let tasks = [];
  let isLoading = true;
  let error = '';
  let showEvidenceModal = false;
  let selectedTask = null;
  let evidenceFiles = [];
  let evidenceNotes = '';
  let submittingEvidence = false;
  let evidenceError = '';
  let evidenceSuccess = '';

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
      const response = await fetch('http://localhost:5000/api/tasks', {
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
    if (statusLower === 'assigned') return 'bg-blue-100 text-blue-800';
    if (statusLower === 'submitted') return 'bg-amber-100 text-amber-800';
    if (statusLower === 'approved') return 'bg-green-100 text-green-800';
    if (statusLower === 'overdue') return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  }

  function getStatusLabel(status) {
    const statusLower = (status || 'assigned').toLowerCase();
    if (statusLower === 'assigned') return 'Not Started';
    if (statusLower === 'submitted') return 'Submitted';
    if (statusLower === 'approved') return 'Approved';
    if (statusLower === 'overdue') return 'Overdue';
    return status;
  }

  function openEvidenceModal(task) {
    selectedTask = task;
    evidenceFiles = [];
    evidenceNotes = '';
    evidenceError = '';
    evidenceSuccess = '';
    showEvidenceModal = true;
  }

  function closeEvidenceModal() {
    showEvidenceModal = false;
    selectedTask = null;
    evidenceFiles = [];
    evidenceNotes = '';
  }

  function handleFileChange(e) {
    evidenceFiles = Array.from(e.target.files);
  }

  async function submitEvidence() {
    if (!selectedTask) return;

    submittingEvidence = true;
    evidenceError = '';
    evidenceSuccess = '';

    try {
      const formData = new FormData();
      evidenceFiles.forEach(file => {
        formData.append('files', file);
      });
      formData.append('notes', evidenceNotes);

      const response = await fetch(`http://localhost:5000/api/tasks/${selectedTask.id}/evidence`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to submit evidence');
      }

      evidenceSuccess = 'Evidence submitted successfully!';
      
      // Refresh tasks list
      await fetchTasks();
      
      // Close modal after 2 seconds
      setTimeout(() => {
        closeEvidenceModal();
      }, 2000);
    } catch (err) {
      evidenceError = err.message || 'Failed to submit evidence';
    } finally {
      submittingEvidence = false;
    }
  }

  function canSubmitEvidence(task) {
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
            View and submit evidence for your assigned tasks
          {/if}
        </p>
      </div>
      {#if $user?.role === 'PI'}
        <button
          on:click={() => router.goToCreateTask()}
          class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-150 shadow-sm"
        >
          <CheckSquare size={18} />
          <span>Create New Task</span>
        </button>
      {/if}
    </div>

    <!-- Error Message -->
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
            on:click={() => router.goToCreateTask()}
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
                <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Task Type</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Deadline</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Hours</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Status</th>
                {#if $user?.role === 'Team'}
                  <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Action</th>
                {/if}
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              {#each tasks as task}
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
                  {#if $user?.role === 'Team'}
                    <td class="px-6 py-4 whitespace-nowrap">
                      {#if canSubmitEvidence(task)}
                        <button
                          on:click={() => openEvidenceModal(task)}
                          class="text-blue-600 hover:text-blue-800 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1"
                        >
                          Submit Evidence
                        </button>
                      {:else}
                        <span class="text-sm text-gray-500">-</span>
                      {/if}
                    </td>
                  {/if}
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    {/if}
  </div>

  <!-- Evidence Submission Modal -->
  {#if showEvidenceModal && selectedTask}
    <div class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" on:click={closeEvidenceModal}>
      <div class="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" on:click|stopPropagation>
        <div class="p-6 border-b border-gray-200">
          <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900">Submit Evidence</h2>
            <button
              on:click={closeEvidenceModal}
              class="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>
          <p class="text-sm text-gray-600 mt-1">Task: {selectedTask.title}</p>
        </div>

        <div class="p-6 space-y-6">
          <!-- Required Evidence Instructions -->
          {#if selectedTask.evidence_rules && selectedTask.evidence_rules.length > 0}
            <div class="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p class="text-sm font-semibold text-blue-900 mb-2">Required Evidence:</p>
              <ul class="text-sm text-blue-800 list-disc list-inside space-y-1">
                {#each selectedTask.evidence_rules as rule}
                  <li>{rule}</li>
                {/each}
              </ul>
            </div>
          {/if}

          <!-- Error/Success Messages -->
          {#if evidenceError}
            <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p class="text-red-700">{evidenceError}</p>
            </div>
          {/if}

          {#if evidenceSuccess}
            <div class="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p class="text-green-700">{evidenceSuccess}</p>
            </div>
          {/if}

          <!-- File Upload -->
          <div>
            <label for="evidence_files" class="block text-sm font-medium text-gray-700 mb-1">
              Upload Files *
            </label>
            <input
              id="evidence_files"
              type="file"
              multiple
              accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.csv"
              on:change={handleFileChange}
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {#if evidenceFiles.length > 0}
              <div class="mt-2 space-y-1">
                {#each evidenceFiles as file}
                  <p class="text-sm text-green-600">✓ {file.name}</p>
                {/each}
              </div>
            {/if}
            <p class="mt-1 text-xs text-gray-500">Accepted: Images, PDF, Word, Excel, CSV</p>
          </div>

          <!-- Notes -->
          <div>
            <label for="evidence_notes" class="block text-sm font-medium text-gray-700 mb-1">
              Activity Notes (Optional)
            </label>
            <textarea
              id="evidence_notes"
              rows="4"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              bind:value={evidenceNotes}
              placeholder="Describe the work completed, methodology used, or any relevant details..."
            ></textarea>
          </div>

          <!-- Submit Button -->
          <div class="flex gap-4 pt-4">
            <button
              on:click={submitEvidence}
              disabled={submittingEvidence || evidenceFiles.length === 0}
              class="flex-1 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150"
            >
              {submittingEvidence ? 'Submitting...' : 'Submit Evidence'}
            </button>
            <button
              on:click={closeEvidenceModal}
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



