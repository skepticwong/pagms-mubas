<script>
  import { createEventDispatcher } from "svelte";
  import axios from "axios";
  import { confirm } from "../stores/modals.js";
  import Icon from "./Icon.svelte";

  axios.defaults.withCredentials = true;

  export let tasks = [];

  const dispatch = createEventDispatcher();

  function formatDate(dateString) {
    if (!dateString) return "N/A";
    const options = { month: "short", day: "numeric", year: "numeric" };
    return new Date(dateString).toLocaleDateString(undefined, options);
  }

  function getStatusConfig(status) {
    switch (status) {
      case "assigned":
        return {
          label: "Assigned",
          class: "bg-blue-50 text-blue-700 border-blue-100",
          icon: "M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z",
        };
      case "in_progress":
        return {
          label: "In Progress",
          class: "bg-indigo-50 text-indigo-700 border-indigo-100",
          icon: "M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99",
        };
      case "submitted":
        return {
          label: "Reviewing",
          class: "bg-amber-50 text-amber-700 border-amber-100",
          icon: "M10.125 2.25h-4.5c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125v-9M10.125 2.25l7.875 7.875M10.125 2.25v7.875h7.875",
        };
      case "completed":
        return {
          label: "Completed",
          class: "bg-emerald-50 text-emerald-700 border-emerald-100",
          icon: "M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
        };
      case "overdue":
        return {
          label: "Overdue",
          class: "bg-rose-50 text-rose-700 border-rose-100",
          icon: "M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z",
        };
      default:
        return {
          label: status,
          class: "bg-gray-50 text-gray-700 border-gray-100",
          icon: "M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z",
        };
    }
  }

  function validTaskId(id) {
    const n = Number(id);
    return Number.isInteger(n) && n > 0;
  }

  function editTask(task) {
    if (!validTaskId(task?.id)) {
      console.warn("TaskList: edit skipped — invalid task id", task);
      return;
    }
    dispatch("editTask", task);
  }

  async function handleDelete(taskId) {
    if (!validTaskId(taskId)) {
      console.warn("TaskList: delete skipped — invalid task id", taskId);
      return;
    }
    if (await confirm("Confirm task deletion? This action cannot be undone.")) {
      try {
        await axios.delete(`http://localhost:5000/api/tasks/${Number(taskId)}`);
        dispatch("taskDeleted");
      } catch (error) {
        console.error("Error deleting task:", error);
      }
    }
  }
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h3 class="text-xl font-bold text-gray-900 tracking-tight">
      Active Team Assignments
    </h3>
    <div
      class="px-3 py-1 bg-gray-100 rounded-full text-xs font-bold text-gray-500 uppercase tracking-widest"
    >
      {tasks.length} Total
    </div>
  </div>

  {#if tasks.length === 0}
    <div
      class="flex flex-col items-center justify-center py-20 bg-gray-50/50 rounded-3xl border-2 border-dashed border-gray-200"
    >
      <div
        class="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center text-gray-400 mb-4"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          class="w-8 h-8"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>
      <p class="text-gray-500 font-medium">No tasks have been assigned yet.</p>
      <button
        on:click={() => dispatch("assignNew")}
        class="mt-4 text-blue-600 font-bold hover:underline"
        >Assign the first task →</button
      >
    </div>
  {:else}
    <div
      class="overflow-hidden bg-white/50 backdrop-blur-md rounded-3xl border border-gray-100 shadow-sm"
    >
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-100">
          <thead>
            <tr class="bg-gray-50/50">
              <th
                class="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest"
                >Task Details</th
              >
              <th
                class="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest"
                >Project</th
              >
              <th
                class="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest"
                >Assigned To</th
              >
              <th
                class="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest"
                >Timeline</th
              >
              <th
                class="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest"
                >Status</th
              >
              <th
                class="px-6 py-4 text-right text-xs font-bold text-gray-400 uppercase tracking-widest"
                >Actions</th
              >
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            {#each tasks as task (task.id)}
              {@const status = getStatusConfig(task.status)}
              <tr class="hover:bg-blue-50/30 transition-colors group">
                <td class="px-6 py-5 whitespace-nowrap">
                  <div class="flex flex-col">
                    <span
                      class="text-sm font-bold text-gray-900 group-hover:text-blue-700 transition-colors"
                      >{task.title}</span
                    >
                    <span class="text-xs text-gray-500 mt-0.5"
                      >{task.task_type}</span
                    >
                    {#if task.milestone_title}
                      <span class="inline-flex items-center gap-1 mt-1 px-2 py-0.5 bg-cyan-50 text-cyan-700 text-[10px] font-bold rounded-full border border-cyan-100 uppercase tracking-tighter">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-2.5 h-2.5">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.96 5.96m0 0L2.25 21l.75-6.75 6.63-6.63m0 0l.001-.001" />
                        </svg>
                        {task.milestone_title}
                      </span>
                    {/if}
                  </div>
                </td>
                <td class="px-6 py-5 whitespace-nowrap">
                  <div class="flex flex-col">
                    <span class="text-sm font-medium text-gray-700"
                      >{task.grant_code}</span
                    >
                    <span class="text-xs text-gray-400 truncate max-w-[150px]"
                      >{task.grant_title}</span
                    >
                  </div>
                </td>
                <td class="px-6 py-5 whitespace-nowrap">
                  <div class="flex items-center gap-3">
                    <div
                      class="w-8 h-8 rounded-full bg-indigo-50 flex items-center justify-center text-xs font-bold text-indigo-600 border border-indigo-100 capitalize"
                    >
                      {task.assigned_to_name
                        ? task.assigned_to_name.charAt(0)
                        : "U"}
                    </div>
                    <div class="flex flex-col">
                      <span class="text-sm font-semibold text-gray-700"
                        >{task.assigned_to_name}</span
                      >
                      <span class="text-[10px] text-gray-400"
                        >{task.assigned_to_email}</span
                      >
                    </div>
                  </div>
                </td>
                <td class="px-6 py-5 whitespace-nowrap">
                  <div class="flex flex-col">
                    <span class="text-sm font-bold text-gray-700"
                      >{formatDate(task.deadline)}</span
                    >
                    <span
                      class="text-[10px] font-medium text-gray-400 uppercase tracking-tight"
                      >Deadline</span
                    >
                  </div>
                </td>
                <td class="px-6 py-5 whitespace-nowrap">
                  <div
                    class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border w-fit {status.class}"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke-width="2.5"
                      stroke="currentColor"
                      class="w-3.5 h-3.5 italic"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d={status.icon}
                      />
                    </svg>
                    <span
                      class="text-[10px] font-extrabold uppercase tracking-wider"
                      >{status.label}</span
                    >
                  </div>
                </td>
                <td class="px-6 py-5 whitespace-nowrap text-right text-sm">
                  <div class="flex items-center justify-end gap-2">
                    <button
                      on:click={() => editTask(task)}
                      class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all"
                      title="Edit Assignment"
                    >
                      <Icon name="edit" size={20} />
                    </button>
                    <button
                      on:click={() => handleDelete(task.id)}
                      class="p-2 text-gray-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-all"
                      title="Delete Task"
                    >
                      <Icon name="delete" size={20} />
                    </button>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {/if}
</div>
