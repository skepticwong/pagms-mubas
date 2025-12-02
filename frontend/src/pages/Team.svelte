<script>
  import { onMount } from "svelte";
  import axios from "axios";
  import Layout from "../components/Layout.svelte";
  import { router } from "../stores/router.js";
  import { user } from "../stores/auth.js";

  $: showPage = $user?.role === "PI";

  // Team management state
  let selectedGrant = null;
  let grants = [];
  let teamMembers = [];
  let availableUsers = [];
  let isLoading = false;
  let isSubmitting = false;
  let error = "";
  let success = "";

  // Modal state
  let showAddMemberModal = false;
  let showRemoveModal = false;
  let selectedUserIdToAdd = "";
  let selectedRole = "";
  let memberToRemove = null;

  const ROLES = [
    {
      value: "Co-Investigator",
      label: "Co-Investigator",
      color: "blue",
      icon: "M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z",
    },
    {
      value: "Research Assistant",
      label: "Research Assistant",
      color: "emerald",
      icon: "M4.26 10.174L15.44 2.184a.75.75 0 011.15.511l.757 5.834a7.5 7.5 0 001.24 3.935l3.11 4.665a.75.75 0 01-.624 1.165h-5.419a.75.75 0 01-.645-.37l-1.428-2.381a1.5 1.5 0 00-2.582 0l-1.428 2.381a.75.75 0 01-.645.37H5.97a.75.75 0 01-.624-1.165l3.11-4.665a7.5 7.5 0 001.24-3.935l.757-5.834a.75.75 0 011.15-.511L22.74 10.174a.75.75 0 010 1.252L11.56 19.416a.75.75 0 01-1.15-.511l-.757-5.834a7.5 7.5 0 00-1.24-3.935l-3.11-4.665a7.5 7.5 0 01.624-1.165h5.419a.75.75 0 01.645.37l1.428 2.381a1.5 1.5 0 002.582 0l1.428-2.381a.75.75 0 01-.645.37h5.419a.75.75 0 01.624 1.165l-3.11 4.665a7.5 7.5 0 00-1.24 3.935l-.757-5.834a.75.75 0 01-1.15-.511L1.26 11.426a.75.75 0 010-1.252z",
    },
    {
      value: "Finance Contact",
      label: "Finance Contact",
      color: "purple",
      icon: "M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
    },
    {
      value: "Field Assistant",
      label: "Field Assistant",
      color: "amber",
      icon: "M15 10.5a3 3 0 11-6 0 3 3 0 016 0z",
    },
  ];

  const ROLE_PERMISSIONS = {
    "Co-Investigator": {
      name: "Co-Investigator",
      permissions: [
        "Full grant visibility",
        "Financial management",
        "Evidence approval",
        "Notes management",
      ],
      color: "blue",
    },
    "Research Assistant": {
      name: "Research Assistant",
      permissions: [
        "Task tracking",
        "Evidence submission",
        "Activity logging",
        "Limited budget view",
      ],
      color: "emerald",
    },
    "Finance Contact": {
      name: "Finance Contact",
      permissions: [
        "Budget oversight",
        "Expense auditing",
        "Financial reporting",
        "Payment tracking",
      ],
      color: "purple",
    },
    "Field Assistant": {
      name: "Field Assistant",
      permissions: [
        "Field data collection",
        "Location tracking",
        "Field expense reports",
        "Task updates",
      ],
      color: "amber",
    },
  };

  $: selectedRolePermissions = selectedRole
    ? ROLE_PERMISSIONS[selectedRole]
    : null;

  onMount(async () => {
    if (!$user) return router.goToLogin();
    if (showPage) await loadGrants();
  });

  async function loadGrants() {
    isLoading = true;
    try {
      const response = await axios.get("http://localhost:5000/api/grants");
      grants = response.data;
      if (grants.length > 0 && !selectedGrant) {
        selectedGrant = grants[0];
        await loadTeamMembers(selectedGrant.id);
      }
    } catch (err) {
      error = "Failed to load grants";
    } finally {
      isLoading = false;
    }
  }

  async function loadTeamMembers(grantId) {
    isLoading = true;
    try {
      const response = await axios.get(
        `http://localhost:5000/api/grants/${grantId}/team`,
      );
      let fetched = response.data;
      const piMember = {
        user_id: selectedGrant.pi_id,
        name: selectedGrant.pi.name,
        email: selectedGrant.pi.email,
        role: "PI",
        date_added: selectedGrant.created_at,
      };
      const piExists = fetched.some((m) => m.user_id === piMember.user_id);
      teamMembers = piExists ? fetched : [piMember, ...fetched];
    } catch (err) {
      error = "Failed to load team members";
    } finally {
      isLoading = false;
    }
  }

  async function loadAvailableUsers() {
    try {
      const response = await axios.get(
        "http://localhost:5000/api/users/available",
      );
      availableUsers = response.data;
    } catch (err) {
      console.error("Failed to load available users", err);
    }
  }

  async function handleGrantChange(event) {
    const grantId = parseInt(event.target.value);
    selectedGrant = grants.find((g) => g.id === grantId);
    if (selectedGrant) await loadTeamMembers(selectedGrant.id);
  }

  function openAddMemberModal() {
    loadAvailableUsers();
    showAddMemberModal = true;
    selectedUserIdToAdd = "";
    selectedRole = "";
    error = "";
    success = "";
  }

  async function addTeamMember() {
    if (!selectedUserIdToAdd || !selectedRole) return;
    isSubmitting = true;
    try {
      await axios.post(
        `http://localhost:5000/api/grants/${selectedGrant.id}/team`,
        {
          user_id: selectedUserIdToAdd,
          role: selectedRole,
        },
      );
      success = "Team member added successfully!";
      showAddMemberModal = false;
      await loadTeamMembers(selectedGrant.id);
      setTimeout(() => (success = ""), 4000);
    } catch (err) {
      error = err.response?.data?.error || "Failed to add member";
    } finally {
      isSubmitting = false;
    }
  }

  async function confirmRemoveMember() {
    if (!memberToRemove || !selectedGrant) return;
    isSubmitting = true;
    try {
      await axios.delete(
        `http://localhost:5000/api/grants/${selectedGrant.id}/team/${memberToRemove.user_id}`,
      );
      success = "Member removed successfully!";
      showRemoveModal = false;
      await loadTeamMembers(selectedGrant.id);
      setTimeout(() => (success = ""), 4000);
    } catch (err) {
      error = "Failed to remove member";
    } finally {
      isSubmitting = false;
    }
  }

  function getInitials(name) {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  }

  function formatDate(d) {
    return new Date(d).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  function canRemoveMember(member) {
    return (
      member.role !== "PI" &&
      member.role !== "RSU" &&
      member.user_id !== $user?.id
    );
  }
</script>

{#if showPage}
  <Layout>
    <div
      class="max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700"
    >
      <!-- Top Title Bar -->
      <div
        class="flex flex-col md:flex-row md:items-end justify-between gap-6 bg-white/40 backdrop-blur-xl border border-white/40 rounded-[2.5rem] p-10 shadow-2xl overflow-hidden relative group"
      >
        <div
          class="absolute top-0 right-0 w-64 h-64 bg-blue-400/10 rounded-full blur-3xl -mr-20 -mt-20 group-hover:bg-blue-400/20 transition-all duration-1000"
        ></div>
        <div class="z-10 relative">
          <div
            class="inline-flex items-center gap-2 px-4 py-1.5 bg-blue-500/10 border border-blue-200/20 rounded-full text-blue-600 font-bold text-[10px] uppercase tracking-widest mb-4"
          >
            <span class="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"
            ></span>
            Resource Management
          </div>
          <h1
            class="text-4xl md:text-5xl font-black text-gray-900 tracking-tight leading-none"
          >
            Team <span
              class="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600"
              >Command</span
            >
          </h1>
          <p class="text-gray-500 text-lg mt-3 font-medium max-w-xl">
            Streamline project collaboration by managing researchers, analysts,
            and fieldwork staff.
          </p>
        </div>

        {#if grants.length > 0}
          <div class="z-10 relative space-y-2 min-w-[320px]">
            <label
              for="grant-pick"
              class="block text-xs font-bold text-gray-400 uppercase tracking-widest ml-1"
              >Focus Project</label
            >
            <div class="relative group">
              <select
                id="grant-pick"
                class="w-full pl-6 pr-12 py-4 bg-white/80 border border-gray-100 rounded-2xl appearance-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all font-bold text-gray-800 shadow-sm cursor-pointer group-hover:bg-white"
                on:change={handleGrantChange}
              >
                {#each grants as grant}
                  <option
                    value={grant.id}
                    selected={selectedGrant?.id === grant.id}
                  >
                    {grant.grant_code} • {grant.title}
                  </option>
                {/each}
              </select>
              <div
                class="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke-width="2.5"
                  stroke="currentColor"
                  class="w-4 h-4"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M19.5 8.25l-7.5 7.5-7.5-7.5"
                  />
                </svg>
              </div>
            </div>
          </div>
        {/if}
      </div>

      {#if error || success}
        <div class="flex gap-4">
          {#if error}
            <div
              class="flex-1 bg-rose-50 border border-rose-100 p-4 rounded-2xl flex items-center gap-3 text-rose-700 animate-in bounce-in duration-500"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="2"
                stroke="currentColor"
                class="w-5 h-5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
                />
              </svg>
              <span class="text-sm font-bold">{error}</span>
            </div>
          {/if}
          {#if success}
            <div
              class="flex-1 bg-emerald-50 border border-emerald-100 p-4 rounded-2xl flex items-center gap-3 text-emerald-700 animate-in bounce-in duration-500"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="2"
                stroke="currentColor"
                class="w-5 h-5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span class="text-sm font-bold">{success}</span>
            </div>
          {/if}
        </div>
      {/if}

      <!-- Stats Grid -->
      {#if selectedGrant && teamMembers.length > 0}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div
            class="bg-white/60 backdrop-blur-md border border-white/40 rounded-[2rem] p-8 shadow-sm group hover:scale-[1.02] transition-all duration-500"
          >
            <div class="flex items-center gap-4">
              <div
                class="w-14 h-14 bg-blue-500/10 rounded-2xl flex items-center justify-center text-blue-600"
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
                    d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z"
                  />
                </svg>
              </div>
              <div>
                <p
                  class="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]"
                >
                  Team Capacity
                </p>
                <p class="text-3xl font-black text-gray-900 leading-tight">
                  {teamMembers.length}
                </p>
              </div>
            </div>
            <div class="mt-6 flex items-center gap-2">
              <span
                class="px-2 py-1 bg-blue-50 text-blue-600 text-[10px] font-bold rounded-lg uppercase tracking-wider"
                >Active Workspace</span
              >
            </div>
          </div>

          <div
            class="bg-white/60 backdrop-blur-md border border-white/40 rounded-[2rem] p-8 shadow-sm group hover:scale-[1.02] transition-all duration-500"
          >
            <div class="flex items-center gap-4">
              <div
                class="w-14 h-14 bg-emerald-500/10 rounded-2xl flex items-center justify-center text-emerald-600"
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
                    d="M11.42 15.17L17.25 21A2.652 2.652 0 0021 17.25l-5.83-5.83m0 0a8.959 8.959 0 01-5.83 1.35m5.83-1.35a8.959 8.959 0 01-1.35-5.83m0 0L3 3m0 0l.88 2.34A9.06 9.06 0 008.15 8.15L3 3z"
                  />
                </svg>
              </div>
              <div>
                <p
                  class="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]"
                >
                  Internal Specializations
                </p>
                <p class="text-3xl font-black text-gray-900 leading-tight">
                  {new Set(teamMembers.map((m) => m.role)).size}
                </p>
              </div>
            </div>
            <div class="mt-6 flex items-center gap-2">
              <span
                class="px-2 py-1 bg-emerald-50 text-emerald-600 text-[10px] font-bold rounded-lg uppercase tracking-wider"
                >Diversified Skills</span
              >
            </div>
          </div>

          <div
            class="bg-white/60 backdrop-blur-md border border-white/40 rounded-[2rem] p-8 shadow-sm group hover:scale-[1.02] transition-all duration-500"
          >
            <div class="flex items-center gap-4">
              <div
                class="w-14 h-14 bg-indigo-500/10 rounded-2xl flex items-center justify-center text-indigo-600"
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
                    d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418"
                  />
                </svg>
              </div>
              <div>
                <p
                  class="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]"
                >
                  Project Tenure
                </p>
                <div class="flex items-end gap-1">
                  <p class="text-3xl font-black text-gray-900 leading-tight">
                    {Math.floor(
                      (new Date() - new Date(selectedGrant.created_at)) /
                        (1000 * 60 * 60 * 24),
                    )}
                  </p>
                  <span class="text-xs font-bold text-gray-400 mb-1">DAYS</span>
                </div>
              </div>
            </div>
            <div class="mt-6 flex items-center gap-2">
              <span
                class="px-2 py-1 bg-indigo-50 text-indigo-600 text-[10px] font-bold rounded-lg uppercase tracking-wider"
                >Launch Maturity</span
              >
            </div>
          </div>
        </div>
      {/if}

      <!-- Main Team Table -->
      <div
        class="bg-white/50 backdrop-blur-xl border border-white/40 rounded-[2.5rem] shadow-2xl overflow-hidden min-h-[400px]"
      >
        <div
          class="p-8 md:p-10 border-b border-gray-100/50 flex flex-col sm:flex-row sm:items-center justify-between gap-6"
        >
          <div>
            <h2 class="text-2xl font-black text-gray-900 tracking-tight">
              Personnel Directory
            </h2>
            <p class="text-gray-500 text-sm font-medium mt-1">
              Operational view of all accounts assigned to <span
                class="text-blue-600 font-bold"
                >{selectedGrant?.grant_code}</span
              >
            </p>
          </div>
          <button
            class="px-8 py-4 bg-gradient-to-br from-gray-900 to-gray-800 text-white rounded-2xl font-black text-xs uppercase tracking-widest shadow-xl shadow-gray-200 hover:shadow-gray-300 hover:-translate-y-1 active:translate-y-0 transition-all flex items-center gap-3 disabled:opacity-50"
            on:click={openAddMemberModal}
            disabled={!selectedGrant}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="3"
              stroke="currentColor"
              class="w-4 h-4 text-blue-400"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 4.5v15m7.5-7.5h-15"
              />
            </svg>
            Add Member
          </button>
        </div>

        {#if isLoading}
          <div class="p-32 flex flex-col items-center justify-center gap-4">
            <div
              class="w-12 h-12 border-4 border-gray-100 border-t-blue-600 rounded-full animate-spin"
            ></div>
            <span
              class="text-xs font-black text-gray-400 uppercase tracking-widest"
              >Synchronizing Team...</span
            >
          </div>
        {:else if !selectedGrant}
          <div class="p-32 text-center">
            <div
              class="w-20 h-20 bg-gray-50 rounded-3xl flex items-center justify-center mx-auto text-gray-300 mb-6"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="2"
                stroke="currentColor"
                class="w-10 h-10"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
                />
              </svg>
            </div>
            <h3 class="text-xl font-bold text-gray-900">No Project Focused</h3>
            <p class="text-gray-500 max-w-xs mx-auto mt-2">
              Select a grant from the header to manage team personnel.
            </p>
          </div>
        {:else if teamMembers.length === 0}
          <div class="p-32 text-center">
            <div
              class="w-20 h-20 bg-gray-50 rounded-3xl flex items-center justify-center mx-auto text-gray-300 mb-6"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="2"
                stroke="currentColor"
                class="w-10 h-10"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"
                />
              </svg>
            </div>
            <h3 class="text-xl font-bold text-gray-900">Empty Team</h3>
            <p class="text-gray-500 max-w-xs mx-auto mt-2">
              Add researchers or assistants to start collaborating on this
              grant.
            </p>
          </div>
        {:else}
          <div class="overflow-x-auto">
            <table class="w-full border-collapse">
              <thead>
                <tr class="bg-gray-50/50">
                  <th
                    class="text-left px-10 py-5 text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-100"
                    >Member Details</th
                  >
                  <th
                    class="text-left px-10 py-5 text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-100"
                    >Functional Role</th
                  >
                  <th
                    class="text-left px-10 py-5 text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-100"
                    >Integrated On</th
                  >
                  <th
                    class="text-right px-10 py-5 text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-100"
                    >Management</th
                  >
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                {#each teamMembers as member}
                  {@const roleInfo =
                    member.role === "PI"
                      ? { color: "indigo" }
                      : ROLES.find((r) => r.value === member.role) || {
                          color: "gray",
                        }}
                  <tr
                    class="group hover:bg-blue-50/30 transition-all duration-300"
                  >
                    <td class="px-10 py-6">
                      <div class="flex items-center gap-5">
                        <div
                          class="w-12 h-12 rounded-2xl bg-gradient-to-br from-white to-gray-200 border border-gray-100 flex items-center justify-center text-gray-600 font-black text-sm shadow-sm group-hover:scale-110 group-hover:shadow-blue-200/50 transition-all"
                        >
                          {getInitials(member.name)}
                        </div>
                        <div>
                          <p
                            class="font-black text-gray-900 leading-none mb-1 group-hover:text-blue-700 transition-colors"
                          >
                            {member.name}
                          </p>
                          <p class="text-[10px] font-bold text-gray-400 italic">
                            {member.email}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td class="px-10 py-6">
                      <div
                        class="flex items-center gap-2 px-3 py-1.5 rounded-xl border w-fit
                        {roleInfo.color === 'indigo'
                          ? 'bg-indigo-50 border-indigo-100 text-indigo-700'
                          : ''}
                        {roleInfo.color === 'blue'
                          ? 'bg-blue-50 border-blue-100 text-blue-700'
                          : ''}
                        {roleInfo.color === 'emerald'
                          ? 'bg-emerald-50 border-emerald-100 text-emerald-700'
                          : ''}
                        {roleInfo.color === 'purple'
                          ? 'bg-purple-50 border-purple-100 text-purple-700'
                          : ''}
                        {roleInfo.color === 'amber'
                          ? 'bg-amber-50 border-amber-100 text-amber-700'
                          : ''}
                      "
                      >
                        {#if member.role === "PI"}
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
                              d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z"
                            />
                          </svg>
                        {:else if member.role === "Co-Investigator"}
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
                              d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
                            />
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                          </svg>
                        {:else}
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
                              d="M6.115 5.19l.319 1.913A6 6 0 008.11 10.36L9.75 12l-.387.775c-.217.433-.132.956.21 1.298l1.348 1.348c.21.21.329.497.329.795v1.089c0 .426.24.815.622 1.006l.663.332c.396.198.65.6.65 1.044v.242c0 .351.109.694.313.98l.583.816M11.96 3c-1.314 0-2.585.311-3.717.863L11.5 5.5l1.693 1.693c.211.21.329.496.329.795v1.444M11.96 3a9 9 0 00-1.24 17.915m1.24-17.915c1.455 0 2.836.345 4.06 1.04L15.5 5.5l-1.082 1.082a1.5 1.5 0 00-.44 1.06v.24c0 .359.136.702.38 1.008l1.584 1.981c.219.274.524.453.865.508l2.915.47c.451.073.882.316 1.2.684l.646.745M12.42 20.915A9 9 0 0021.1 12.04"
                            />
                          </svg>
                        {/if}
                        <span
                          class="text-[10px] font-black uppercase tracking-widest leading-none mt-0.5"
                          >{member.role === "PI"
                            ? "Principal Investigator"
                            : member.role}</span
                        >
                      </div>
                    </td>
                    <td class="px-10 py-6">
                      <div class="flex flex-col">
                        <span class="text-sm font-bold text-gray-700"
                          >{formatDate(member.date_added)}</span
                        >
                        <span
                          class="text-[10px] font-bold text-gray-400 uppercase"
                          >Archive Date</span
                        >
                      </div>
                    </td>
                    <td class="px-10 py-6 text-right">
                      {#if canRemoveMember(member)}
                        <button
                          class="p-3 text-gray-400 hover:text-rose-600 hover:bg-rose-50 rounded-2xl transition-all"
                          on:click={() => {
                            memberToRemove = member;
                            showRemoveModal = true;
                          }}
                          title="Revoke Access"
                          aria-label="Revoke Access"
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
                              d="M22 10.5h-6m-2.25-1.5a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0zM12 10.5h.008v.008H12V10.5z"
                            />
                          </svg>
                        </button>
                      {:else}
                        <div
                          class="flex items-center justify-end gap-1.5 text-gray-400"
                          title="Protected Account"
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke-width="2.5"
                            stroke="currentColor"
                            class="w-3.5 h-3.5"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"
                            />
                          </svg>
                          <span
                            class="text-[10px] font-black uppercase tracking-widest"
                            >Master</span
                          >
                        </div>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>
    </div>

    <!-- Add Member Modal -->
    {#if showAddMemberModal}
      <div
        class="fixed inset-0 z-50 flex items-center justify-center p-6 bg-gray-900/60 backdrop-blur-md animate-in fade-in duration-300"
        on:click={() => (showAddMemberModal = false)}
        on:keydown={(e) => e.key === "Escape" && (showAddMemberModal = false)}
        role="button"
        tabindex="-1"
      >
        <div
          class="bg-white/95 border border-white rounded-[3rem] shadow-2xl w-full max-w-xl overflow-hidden animate-in zoom-in-95 duration-300"
          on:click|stopPropagation
          on:keydown|stopPropagation
          role="presentation"
        >
          <div class="p-10 space-y-8">
            <div class="flex items-center justify-between">
              <div>
                <h3
                  class="text-3xl font-black text-gray-900 tracking-tight leading-none"
                >
                  Assemble <span class="text-blue-600">Personnel</span>
                </h3>
                <p class="text-gray-500 text-sm font-medium mt-2 italic">
                  Linking database users to {selectedGrant?.grant_code}
                </p>
              </div>
              <button
                on:click={() => (showAddMemberModal = false)}
                class="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center text-gray-400 hover:bg-rose-50 hover:text-rose-500 transition-all"
                aria-label="Close modal"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke-width="3"
                  stroke="currentColor"
                  class="w-5 h-5"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <div class="space-y-6">
              <div class="space-y-2">
                <label
                  for="user-target"
                  class="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1"
                  >Identity Selection</label
                >
                <div class="relative">
                  <select
                    id="user-target"
                    bind:value={selectedUserIdToAdd}
                    class="w-full pl-12 pr-6 py-5 bg-gray-50/50 border border-gray-100 rounded-3xl outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all font-bold text-gray-800"
                  >
                    <option value="">Search system users...</option>
                    {#each availableUsers as user}
                      <option value={user.id}>{user.name} ({user.email})</option
                      >
                    {/each}
                  </select>
                  <div
                    class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke-width="2"
                      stroke="currentColor"
                      class="w-5 h-5"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                      />
                    </svg>
                  </div>
                </div>
              </div>

              <div class="space-y-2">
                <label
                  for="role-target"
                  class="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1"
                  >Functional Designation</label
                >
                <div class="grid grid-cols-2 gap-3">
                  {#each ROLES as role}
                    <button
                      class="flex flex-col items-center gap-3 p-5 rounded-3xl border-2 transition-all text-center
                        {selectedRole === role.value
                        ? 'bg-blue-50/50 border-blue-500 ring-4 ring-blue-500/5'
                        : 'bg-gray-50/30 border-gray-100 hover:border-gray-200'}"
                      on:click={() => (selectedRole = role.value)}
                    >
                      <div
                        class="w-10 h-10 rounded-2xl {selectedRole ===
                        role.value
                          ? 'bg-blue-600 text-white'
                          : 'bg-white text-gray-400'} shadow-sm flex items-center justify-center transition-all"
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
                            d={role.icon}
                          />
                        </svg>
                      </div>
                      <span
                        class="text-xs font-black {selectedRole === role.value
                          ? 'text-blue-700'
                          : 'text-gray-500'} tracking-tight">{role.label}</span
                      >
                    </button>
                  {/each}
                </div>
              </div>

              {#if selectedRolePermissions}
                <div
                  class="p-6 bg-gradient-to-br from-gray-50 to-white border border-gray-100/50 rounded-3xl space-y-3"
                >
                  <span
                    class="text-[9px] font-black text-gray-400 uppercase tracking-widest"
                    >Project Permissions Scope</span
                  >
                  <div class="grid grid-cols-1 gap-2">
                    {#each selectedRolePermissions.permissions as perm}
                      <div class="flex items-center gap-3">
                        <div
                          class="w-5 h-5 bg-emerald-100 text-emerald-600 rounded-lg flex items-center justify-center"
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke-width="3"
                            stroke="currentColor"
                            class="w-3 h-3"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              d="M4.5 12.75l6 6 9-13.5"
                            />
                          </svg>
                        </div>
                        <span class="text-xs font-bold text-gray-600"
                          >{perm}</span
                        >
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>

            <button
              on:click={addTeamMember}
              disabled={!selectedUserIdToAdd || !selectedRole || isSubmitting}
              class="w-full py-6 bg-gray-900 border-2 border-gray-800 text-white rounded-[2rem] font-black uppercase text-xs tracking-widest shadow-2xl shadow-gray-300 hover:shadow-blue-200 hover:border-blue-500 hover:bg-blue-600 transition-all disabled:opacity-50 disabled:grayscale flex items-center justify-center gap-3 group"
            >
              {#if isSubmitting}
                <div
                  class="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"
                ></div>
                Initializing...
              {:else}
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke-width="3"
                  stroke="currentColor"
                  class="w-4 h-4 group-hover:scale-125 transition-transform"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.841m1.861-4.413a1.498 1.498 0 00-2.082 2.082V3.75"
                  />
                </svg>
                Confirm Deployment
              {/if}
            </button>
          </div>
        </div>
      </div>
    {/if}

    <!-- Remove Member Modal -->
    {#if showRemoveModal && memberToRemove}
      <div
        class="fixed inset-0 z-50 flex items-center justify-center p-6 bg-rose-950/20 backdrop-blur-md animate-in fade-in duration-300"
        on:click={() => (showRemoveModal = false)}
        on:keydown={(e) => e.key === "Escape" && (showRemoveModal = false)}
        role="button"
        tabindex="-1"
      >
        <div
          class="bg-white rounded-[3rem] shadow-2xl w-full max-md w-full overflow-hidden animate-in zoom-in-95 duration-300 border border-white"
          on:click|stopPropagation
          on:keydown|stopPropagation
          role="presentation"
        >
          <div class="p-10 text-center space-y-10">
            <div
              class="w-24 h-24 bg-rose-50 rounded-full flex items-center justify-center mx-auto text-rose-500 shadow-inner"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="2"
                stroke="currentColor"
                class="w-10 h-10"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M22 10.5h-6m-2.25-1.5a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0zM12 10.5h.008v.008H12V10.5z"
                />
              </svg>
            </div>

            <div class="space-y-2">
              <h3 class="text-3xl font-black text-gray-900 tracking-tight">
                Revoke Access
              </h3>
              <p class="text-gray-500 font-medium italic">
                Terminating project clearance for
              </p>
              <div class="inline-block px-4 py-2 bg-rose-50 rounded-xl mt-2">
                <p class="font-black text-rose-700 leading-none">
                  {memberToRemove.name}
                </p>
                <p
                  class="text-[9px] font-bold text-rose-400 tracking-widest mt-1 uppercase"
                >
                  {memberToRemove.role}
                </p>
              </div>
            </div>

            <div
              class="p-6 bg-amber-50 rounded-3xl border border-amber-100 text-left space-y-3"
            >
              <div class="flex items-center gap-2">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke-width="3"
                  stroke="currentColor"
                  class="w-4 h-4 text-amber-600"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                  />
                </svg>
                <span
                  class="text-[10px] font-black text-amber-800 uppercase tracking-widest"
                  >Security Protocol Note</span
                >
              </div>
              <p
                class="text-[11px] font-bold text-amber-700 leading-relaxed italic"
              >
                Revoking access will immediately disconnect this user from all
                data streams, notifications, and budget views associated with
                this grant. This can be reversed by a new assignment.
              </p>
            </div>

            <div class="flex flex-col gap-3">
              <button
                class="w-full py-5 bg-rose-600 text-white rounded-[2rem] font-black uppercase text-xs tracking-widest shadow-xl shadow-rose-200 hover:bg-rose-700 active:scale-95 transition-all"
                on:click={confirmRemoveMember}
                disabled={isSubmitting}
              >
                {isSubmitting ? "Processing..." : "Execute Revocation"}
              </button>
              <button
                class="w-full py-5 bg-gray-50 text-gray-400 rounded-[2rem] font-black uppercase text-[10px] tracking-[0.3em] hover:bg-gray-100 hover:text-gray-600 transition-all"
                on:click={() => (showRemoveModal = false)}
              >
                Hold Position
              </button>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </Layout>
{:else}
  <Layout>
    <div
      class="max-w-4xl mx-auto py-32 text-center space-y-8 animate-in zoom-in duration-500"
    >
      <div
        class="w-32 h-32 bg-gray-50 border border-gray-100 rounded-[3rem] flex items-center justify-center mx-auto text-gray-300"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2"
          stroke="currentColor"
          class="w-14 h-14"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"
          />
        </svg>
      </div>
      <div class="space-y-2">
        <h1 class="text-4xl font-black text-gray-900 tracking-tight">
          Access Restricted
        </h1>
        <p class="text-xl font-medium text-gray-500 italic max-w-sm mx-auto">
          Only Principal Investigators are authorized to access the Team Command
          interface.
        </p>
      </div>
      <button
        class="px-10 py-5 bg-gray-900 text-white rounded-[2rem] font-black uppercase text-xs tracking-widest shadow-2xl shadow-gray-200 hover:bg-blue-600 hover:shadow-blue-200 transition-all"
        on:click={() =>
          router.goToRoleHome?.($user?.role) ?? router.goToLogin()}
      >
        Return to My Workspace
      </button>
    </div>
  </Layout>
{/if}

<style>
  :global(.animate-in) {
    animation-fill-mode: forwards;
  }

  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes slide-in-from-bottom-4 {
    from {
      transform: translateY(1rem);
    }
    to {
      transform: translateY(0);
    }
  }

  @keyframes bounce-in {
    0% {
      transform: scale(0.95);
      opacity: 0;
    }
    50% {
      transform: scale(1.02);
    }
    100% {
      transform: scale(1);
      opacity: 1;
    }
  }

  @keyframes zoom-in {
    from {
      transform: scale(0.9);
      opacity: 0;
    }
    to {
      transform: scale(1);
      opacity: 1;
    }
  }

  .animate-in.fade-in {
    animation: fade-in 0.3s ease-out;
  }
  .animate-in.slide-in-from-bottom-4 {
    animation:
      slide-in-from-bottom-4 0.5s ease-out,
      fade-in 0.5s ease-out;
  }
  .animate-in.bounce-in {
    animation: bounce-in 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
  .animate-in.zoom-in {
    animation: zoom-in 0.4s ease-out;
  }
</style>
