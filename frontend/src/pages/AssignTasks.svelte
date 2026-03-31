<script>
  import { onMount } from "svelte";
  import axios from "axios";
  import Layout from "../components/Layout.svelte";
  import { router } from "../stores/router.js";
  import TaskForm from "../components/TaskForm.svelte";
  import TaskList from "../components/TaskList.svelte";

  axios.defaults.withCredentials = true;

  let loading = true;
  let grants = [];
  let teamMembers = [];
  let tasks = [];

  let showTaskForm = false;
  let editingTask = null;

  async function fetchInitialData() {
    try {
      const cfg = { withCredentials: true };
      const [grantsRes, teamMembersRes, tasksRes] = await Promise.all([
        axios.get("http://localhost:5000/api/grants", cfg),
        axios.get("http://localhost:5000/api/team-members", cfg),
        axios.get("http://localhost:5000/api/tasks", cfg),
      ]);
      grants = grantsRes.data.grants || [];
      teamMembers = teamMembersRes.data.team_members || [];
      tasks = tasksRes.data.tasks || [];
    } catch (error) {
      console.error("Error fetching initial task management data:", error);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchInitialData();
  });

  function handleTaskCreated() {
    fetchInitialData();
    showTaskForm = false;
  }

  function handleEditTask(event) {
    const task = event?.detail;
    const id = Number(task?.id);
    if (!Number.isInteger(id) || id <= 0) {
      console.warn("AssignTasks: edit ignored — invalid task id", task);
      return;
    }
    editingTask = task;
    showTaskForm = true;
  }

  function handleTaskDeleted() {
    fetchInitialData();
  }

  $: if (editingTask && !showTaskForm) {
    editingTask = null;
  }
</script>

<Layout>
  <div class="max-w-6xl mx-auto space-y-8 py-6 px-4">
    <!-- Header Section -->
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
      <div class="space-y-2">
        <h1 class="text-4xl font-extrabold text-gray-900 tracking-tight">
          Task Management
        </h1>
        <p class="text-lg text-gray-600 max-w-2xl">
          Coordinate your team effectively by creating, assigning, and
          monitoring progress across all project grants.
        </p>
      </div>

      {#if !showTaskForm}
        <button
          on:click={() => (showTaskForm = true)}
          class="flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl font-bold shadow-xl shadow-blue-200 hover:shadow-blue-300 hover:scale-[1.02] transition-all active:scale-95"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="2.5"
            stroke="currentColor"
            class="w-5 h-5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 4.5v15m7.5-7.5h-15"
            />
          </svg>
          Assign New Task
        </button>
      {/if}
    </div>

    {#if loading}
      <div class="flex flex-col items-center justify-center py-20 space-y-4">
        <div
          class="w-12 h-12 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin"
        ></div>
        <p class="text-gray-500 font-medium animate-pulse">
          Synchronizing task data...
        </p>
      </div>
    {:else}
      <div class="relative">
        {#if showTaskForm}
          <div
            class="transition-all duration-300 ease-out transform scale-100 opacity-100"
          >
            <TaskForm
              {grants}
              {teamMembers}
              {editingTask}
              on:taskCreated={handleTaskCreated}
              on:cancel={() => (showTaskForm = false)}
            />
          </div>
        {:else}
          <div class="transition-all duration-300 ease-out">
            <TaskList
              {tasks}
              on:editTask={handleEditTask}
              on:taskDeleted={handleTaskDeleted}
            />
          </div>
        {/if}
      </div>
    {/if}
  </div>
</Layout>


<style>
  :global(body) {
    background-color: #f8fafc;
  }
</style>
