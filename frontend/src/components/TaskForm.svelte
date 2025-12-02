<script>
  import { createEventDispatcher } from "svelte";
  import axios from "axios";

  export let grants = [];
  export let teamMembers = [];
  export let editingTask = null;

  const dispatch = createEventDispatcher();

  let form = {
    grant_id: editingTask?.grant_id || "",
    assigned_to: editingTask?.assigned_to || "",
    title: editingTask?.title || "",
    task_type: editingTask?.task_type || "Fieldwork",
    deadline: editingTask?.deadline
      ? new Date(editingTask.deadline).toISOString().substring(0, 10)
      : "",
    estimated_hours: editingTask?.estimated_hours || "",
  };

  let errorMessage = "";
  let successMessage = "";
  let isSubmitting = false;

  const taskTypes = ["Fieldwork", "Data Analysis", "Remote Work", "Reporting"];

  $: if (editingTask) {
    form = {
      grant_id: editingTask.grant_id || "",
      assigned_to: editingTask.assigned_to || "",
      title: editingTask.title || "",
      task_type: editingTask.task_type || "Fieldwork",
      deadline: editingTask.deadline
        ? new Date(editingTask.deadline).toISOString().substring(0, 10)
        : "",
      estimated_hours: editingTask.estimated_hours || "",
    };
  }

  async function handleSubmit() {
    errorMessage = "";
    successMessage = "";
    isSubmitting = true;

    try {
      const payload = {
        ...form,
        estimated_hours: parseFloat(form.estimated_hours),
      };

      let response;
      if (editingTask) {
        response = await axios.put(
          `http://localhost:5000/api/tasks/${editingTask.id}`,
          payload,
        );
        successMessage = "Task updated successfully!";
      } else {
        response = await axios.post("http://localhost:5000/api/tasks", payload);
        successMessage = "Task created successfully!";
      }

      dispatch("taskCreated", response.data);
      if (!editingTask) {
        form = {
          grant_id: "",
          assigned_to: "",
          title: "",
          task_type: "Fieldwork",
          deadline: "",
          estimated_hours: "",
        };
      }
    } catch (error) {
      console.error("Task form submission error:", error);
      errorMessage =
        error.response?.data?.error || "An unexpected error occurred.";
    } finally {
      isSubmitting = false;
    }
  }

  function handleCancel() {
    dispatch("cancel");
    errorMessage = "";
    successMessage = "";
  }
</script>

<div
  class="bg-white/80 backdrop-blur-xl border border-white/40 rounded-3xl shadow-2xl overflow-hidden max-w-4xl mx-auto"
>
  <div class="p-8 space-y-8">
    <div
      class="flex items-center justify-between border-b border-gray-100 pb-6"
    >
      <h2
        class="text-2xl font-bold text-gray-900 flex items-center gap-3"
        id="form-title"
      >
        <span
          class="w-10 h-10 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center shadow-inner"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="2"
            stroke="currentColor"
            class="w-6 h-6"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"
            />
          </svg>
        </span>
        {editingTask ? "Update Task Assignment" : "Assign New Task"}
      </h2>
      <button
        on:click={handleCancel}
        class="text-gray-400 hover:text-gray-600 transition-colors"
        aria-label="Close form"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2"
          stroke="currentColor"
          class="w-6 h-6"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>

    {#if errorMessage}
      <div
        class="flex items-center gap-3 p-4 bg-red-50 border border-red-200 text-red-800 rounded-2xl animate-shake"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          class="w-5 h-5 flex-shrink-0"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
          />
        </svg>
        <span class="text-sm font-medium">{errorMessage}</span>
      </div>
    {/if}

    <form
      on:submit|preventDefault={handleSubmit}
      class="space-y-6"
      aria-labelledby="form-title"
    >
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Grant Selection -->
        <div class="space-y-2">
          <label
            for="grant-id"
            class="text-sm font-bold text-gray-700 ml-1 flex items-center gap-2"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="2"
              stroke="currentColor"
              class="w-4 h-4 text-blue-500"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.25c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18c-2.305 0-4.408.867-6 2.292m0-14.25v14.25"
              />
            </svg>
            Grant Project
          </label>
          <select
            id="grant-id"
            bind:value={form.grant_id}
            required
            class="w-full px-4 py-3.5 rounded-2xl border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none bg-gray-50/50 hover:bg-white"
          >
            <option value="" disabled>-- Select Project --</option>
            {#each grants as grant}
              <option value={grant.id}
                >{grant.grant_code} - {grant.title}</option
              >
            {/each}
          </select>
        </div>

        <!-- Assignee Selection -->
        <div class="space-y-2">
          <label
            for="assignee-id"
            class="text-sm font-bold text-gray-700 ml-1 flex items-center gap-2"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="2"
              stroke="currentColor"
              class="w-4 h-4 text-indigo-500"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
              />
            </svg>
            Assign Team Member
          </label>
          <select
            id="assignee-id"
            bind:value={form.assigned_to}
            required
            class="w-full px-4 py-3.5 rounded-2xl border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none bg-gray-50/50 hover:bg-white"
          >
            <option value="" disabled>-- Select Member --</option>
            {#each teamMembers as member}
              <option value={member.id}>{member.name} ({member.role})</option>
            {/each}
          </select>
        </div>
      </div>

      <!-- Task Title -->
      <div class="space-y-2">
        <label
          for="task-title"
          class="text-sm font-bold text-gray-700 ml-1 flex items-center gap-2"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="2"
            stroke="currentColor"
            class="w-4 h-4 text-amber-500"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M9 12h3.75M9 15h3.375m1.875-8.125L12 4.5M4.5 3h15.75a1.125 1.125 0 011.125 1.125v15.75a1.125 1.125 0 01-1.125 1.125H4.5a1.125 1.125 0 01-1.125-1.125V4.125A1.125 1.125 0 014.5 3z"
            />
          </svg>
          Task Description / Title
        </label>
        <input
          id="task-title"
          type="text"
          bind:value={form.title}
          required
          placeholder="e.g. Conduct soil sampling in Zomba district"
          class="w-full px-4 py-3.5 rounded-2xl border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none bg-gray-50/50 hover:bg-white"
        />
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Task Type -->
        <div class="space-y-2">
          <label
            for="task-type"
            class="text-sm font-bold text-gray-700 ml-1 flex items-center gap-2"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="2"
              stroke="currentColor"
              class="w-4 h-4 text-emerald-500"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581a2.25 2.25 0 003.182 0l4.318-4.318a2.25 2.25 0 000-3.182L11.159 3.659a2.25 2.25 0 00-1.591-.659z"
              />
            </svg>
            Task Category
          </label>
          <select
            id="task-type"
            bind:value={form.task_type}
            required
            class="w-full px-4 py-3.5 rounded-2xl border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none bg-gray-50/50 hover:bg-white"
          >
            {#each taskTypes as type}
              <option value={type}>{type}</option>
            {/each}
          </select>
        </div>

        <!-- Deadline -->
        <div class="space-y-2">
          <label
            for="deadline"
            class="text-sm font-bold text-gray-700 ml-1 flex items-center gap-2"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="2"
              stroke="currentColor"
              class="w-4 h-4 text-rose-500"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5"
              />
            </svg>
            Deadline
          </label>
          <input
            id="deadline"
            type="date"
            bind:value={form.deadline}
            required
            class="w-full px-4 py-3.5 rounded-2xl border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none bg-gray-50/50 hover:bg-white"
          />
        </div>

        <!-- Estimated Hours -->
        <div class="space-y-2">
          <label
            for="estimated-hours"
            class="text-sm font-bold text-gray-700 ml-1 flex items-center gap-2"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="2"
              stroke="currentColor"
              class="w-4 h-4 text-purple-500"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Est. Hours
          </label>
          <input
            id="estimated-hours"
            type="number"
            bind:value={form.estimated_hours}
            required
            min="0.5"
            step="0.5"
            placeholder="0.0"
            class="w-full px-4 py-3.5 rounded-2xl border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none bg-gray-50/50 hover:bg-white"
          />
        </div>
      </div>

      <div class="flex flex-col sm:flex-row gap-4 pt-6">
        <button
          type="button"
          on:click={handleCancel}
          class="flex-1 px-6 py-4 border border-gray-200 text-gray-600 rounded-2xl font-bold hover:bg-gray-50 transition-all text-center"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          class="flex-[2] py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl font-bold shadow-xl shadow-blue-200 hover:shadow-blue-300 hover:scale-[1.01] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {#if isSubmitting}
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
          {editingTask ? "Update Task Assignment" : "Confirm Task Assignment"}
        </button>
      </div>
    </form>
  </div>
</div>

<style>
  @keyframes shake {
    0%,
    100% {
      transform: translateX(0);
    }
    25% {
      transform: translateX(-4px);
    }
    75% {
      transform: translateX(4px);
    }
  }
  .animate-shake {
    animation: shake 0.4s ease-in-out;
  }
</style>
