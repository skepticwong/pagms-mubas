<script>
  import { onMount } from "svelte";
  import axios from "axios";
  import { user } from "../stores/auth.js";
  import Layout from "../components/Layout.svelte";
  import Icon from "../components/Icon.svelte";

  let events = [];
  let loading = true;
  let currentDate = new Date();
  let view = "month"; // month, week, agenda
  let showCreateModal = false;
  let selectedDate = null;

  // New Event Form
  let newEvent = {
    title: "",
    description: "",
    event_date: "",
    event_type: "PERSONAL",
    grant_id: null,
    target_role: null
  };

  let grants = [];

  onMount(async () => {
    await fetchEvents();
    if ($user.role === "PI" || $user.role === "RSU") {
      await fetchGrants();
    }
  });

  async function fetchEvents() {
    loading = true;
    try {
      const res = await axios.get("/api/events", { withCredentials: true });
      events = res.data;
    } catch (err) {
      console.error("Failed to fetch events", err);
    } finally {
      loading = false;
    }
  }

  async function fetchGrants() {
    try {
      const res = await axios.get("/api/grants", { withCredentials: true });
      grants = res.data;
    } catch (err) {
      console.error("Failed to fetch grants", err);
    }
  }

  async function saveEvent() {
    try {
      if (!newEvent.event_date) {
          newEvent.event_date = selectedDate.toISOString();
      }
      await axios.post("/api/events", newEvent, { withCredentials: true });
      showCreateModal = false;
      resetForm();
      await fetchEvents();
    } catch (err) {
      alert("Failed to save event: " + (err.response?.data?.error || err.message));
    }
  }

  function resetForm() {
    newEvent = {
      title: "",
      description: "",
      event_date: "",
      event_type: "PERSONAL",
      grant_id: null,
      target_role: null
    };
  }

  // Calendar Helpers
  $: year = currentDate.getFullYear();
  $: month = currentDate.getMonth();

  function getDaysInMonth(y, m) {
    return new Date(y, m + 1, 0).getDate();
  }

  function firstDayOfMonth(y, m) {
    return new Date(y, m, 1).getDay();
  }

  $: days = Array.from({ length: getDaysInMonth(year, month) }, (_, i) => i + 1);
  $: blanks = Array.from({ length: firstDayOfMonth(year, month) }, (_, i) => i);

  function prevMonth() {
    currentDate = new Date(year, month - 1, 1);
  }

  function nextMonth() {
    currentDate = new Date(year, month + 1, 1);
  }

  function getEventsForDay(day) {
    const d = new Date(year, month, day);
    return events.filter(e => {
      const ed = new Date(e.event_date);
      return ed.getDate() === day && ed.getMonth() === month && ed.getFullYear() === year;
    });
  }

  function openCreateModal(day = null) {
      if (day) {
          selectedDate = new Date(year, month, day);
          newEvent.event_date = selectedDate.toISOString().split('T')[0] + "T09:00";
      }
      showCreateModal = true;
  }

  const typeColors = {
      BROADCAST: "bg-red-100 text-red-700 border-red-200",
      GRANT: "bg-blue-100 text-blue-700 border-blue-200",
      SYSTEM: "bg-green-100 text-green-700 border-green-200",
      PERSONAL: "bg-gray-100 text-gray-700 border-gray-200"
  };

  const monthNames = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
</script>

<Layout>
  <div class="space-y-6">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-gray-900">Compliance Calendar</h1>
        <p class="text-gray-600">Track deadlines, REC meetings, and ethics expiries</p>
      </div>
      <div class="flex items-center gap-3">
        <button 
            on:click={() => openCreateModal()}
            class="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-xl hover:bg-blue-700 transition-colors shadow-lg shadow-blue-200">
          <Icon name="plus" size={18} />
          Create Event
        </button>
      </div>
    </div>

    <!-- Calendar Controls -->
    <div class="bg-white/60 backdrop-blur-md rounded-2xl border border-white/40 p-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button on:click={prevMonth} class="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <Icon name="chevronLeft" size={20} />
        </button>
        <h2 class="text-xl font-bold min-w-[150px] text-center">{monthNames[month]} {year}</h2>
        <button on:click={nextMonth} class="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <Icon name="chevronRight" size={20} />
        </button>
      </div>
      
      <div class="hidden md:flex items-center gap-2 bg-gray-100 p-1 rounded-xl">
          <button 
            on:click={() => view = "month"}
            class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all {view === 'month' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-600 hover:text-gray-900'}">
              Month
          </button>
          <button 
            on:click={() => view = "week"}
            class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all {view === 'week' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-600 hover:text-gray-900'}">
              Week
          </button>
          <button 
            on:click={() => view = "agenda"}
            class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all {view === 'agenda' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-600 hover:text-gray-900'}">
              Agenda
          </button>
      </div>
    </div>

    <!-- Legend -->
    <div class="flex flex-wrap gap-4 text-xs font-semibold uppercase tracking-wider text-gray-500">
        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-red-400"></span> Broadcast</div>
        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-blue-400"></span> Grant Event</div>
        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-green-400"></span> System Alert</div>
        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-gray-400"></span> Personal</div>
    </div>

    <!-- Calendar Grid -->
    {#if loading}
      <div class="flex justify-center py-20">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    {:else if view === 'month'}
    <div class="bg-white/40 backdrop-blur-xl rounded-3xl border border-white/40 overflow-hidden shadow-xl">
      <div class="grid grid-cols-7 border-b border-gray-200 bg-gray-50/50">
        {#each ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as day}
          <div class="py-3 text-center text-xs font-bold text-gray-500 uppercase tracking-widest">{day}</div>
        {/each}
      </div>
      <div class="grid grid-cols-7">
        {#each blanks as _}
          <div class="h-32 md:h-40 border-r border-b border-gray-100 bg-gray-50/30"></div>
        {/each}
        {#each days as day}
          <div 
            role="button"
            tabindex="0"
            class="h-32 md:h-40 border-r border-b border-gray-100 p-2 hover:bg-blue-50/30 transition-colors cursor-pointer group text-left items-start flex flex-col w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset"
            on:click={() => openCreateModal(day)}
            on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && openCreateModal(day)}>
            <div class="flex justify-between items-start mb-2 w-full">
              <span class="text-sm font-semibold {day === new Date().getDate() && month === new Date().getMonth() && year === new Date().getFullYear() ? 'bg-blue-600 text-white w-7 h-7 flex items-center justify-center rounded-full shadow-md' : 'text-gray-700'}">
                {day}
              </span>
              <div class="opacity-0 group-hover:opacity-100 p-1 hover:bg-blue-100 rounded text-blue-600 transition-all">
                  <Icon name="plus" size={14} />
              </div>
            </div>
            <div class="space-y-1 overflow-y-auto max-h-[80px] md:max-h-[110px] scrollbar-hide">
              {#each getEventsForDay(day) as event}
                <div class="px-2 py-1 rounded-md text-[10px] md:text-xs border truncate {typeColors[event.event_type] || typeColors.PERSONAL}">
                  {event.title}
                </div>
              {/each}
            </div>
          </div>
        {/each}
      </div>
    </div>
    {:else}
    <div class="bg-white/40 backdrop-blur-xl rounded-3xl border border-white/40 p-8 text-center text-gray-500 italic shadow-xl">
        Week and Agenda views are coming soon. Month view is fully functional.
    </div>
    {/if}
  </div>

  <!-- Create Event Modal -->
  {#if showCreateModal}
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/40 backdrop-blur-sm">
      <div class="bg-white rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden border border-white/20 animate-in fade-in zoom-in duration-200">
        <div class="px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white flex justify-between items-center">
          <h3 class="text-xl font-bold">Create New Event</h3>
          <button on:click={() => showCreateModal = false} class="hover:bg-white/20 p-1 rounded-full transition-colors">
            <Icon name="close" size={24} color="white" />
          </button>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <label for="event-title" class="block text-sm font-semibold text-gray-700 mb-1">Title</label>
            <input 
              id="event-title"
              type="text" 
              bind:value={newEvent.title}
              class="w-full px-4 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
              placeholder="Event title..."
            />
          </div>
          
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="event-date" class="block text-sm font-semibold text-gray-700 mb-1">Date & Time</label>
              <input 
                id="event-date"
                type="datetime-local" 
                bind:value={newEvent.event_date}
                class="w-full px-4 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
              />
            </div>
            <div>
              <label for="event-type" class="block text-sm font-semibold text-gray-700 mb-1">Event Type</label>
              <select 
                id="event-type"
                bind:value={newEvent.event_type}
                class="w-full px-4 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
              >
                <option value="PERSONAL">Personal</option>
                {#if $user.role === "PI" || $user.role === "RSU"}
                  <option value="GRANT">Grant Event</option>
                {/if}
                {#if $user.role === "RSU"}
                  <option value="BROADCAST">Broadcast</option>
                {/if}
              </select>
            </div>
          </div>

          {#if newEvent.event_type === 'GRANT'}
          <div>
            <label for="grant-selector" class="block text-sm font-semibold text-gray-700 mb-1">Associate with Grant</label>
            <select 
              id="grant-selector"
              bind:value={newEvent.grant_id}
              class="w-full px-4 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
            >
              <option value={null}>Select a grant...</option>
              {#each grants as g}
                <option value={g.id}>{g.grant_code} - {g.title}</option>
              {/each}
            </select>
          </div>
          {/if}

          {#if newEvent.event_type === 'BROADCAST'}
          <div>
            <label for="role-selector" class="block text-sm font-semibold text-gray-700 mb-1">Target Role (Optional)</label>
            <select 
              id="role-selector"
              bind:value={newEvent.target_role}
              class="w-full px-4 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
            >
              <option value={null}>All Roles</option>
              <option value="PI">PIs Only</option>
              <option value="Team">Team Only</option>
              <option value="Finance">Finance Only</option>
            </select>
          </div>
          {/if}

          <div>
            <label for="event-desc" class="block text-sm font-semibold text-gray-700 mb-1">Description</label>
            <textarea 
              id="event-desc"
              bind:value={newEvent.description}
              rows="3"
              class="w-full px-4 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
              placeholder="Details about the event..."
            ></textarea>
          </div>
        </div>
        <div class="px-6 py-4 bg-gray-50 flex justify-end gap-3 border-t border-gray-100">
          <button 
            on:click={() => showCreateModal = false}
            class="px-5 py-2 rounded-xl font-semibold text-gray-600 hover:bg-gray-200 transition-colors">
            Cancel
          </button>
          <button 
            on:click={saveEvent}
            disabled={!newEvent.title || !newEvent.event_date}
            class="px-6 py-2 rounded-xl font-semibold bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-200 transition-all">
            Save Event
          </button>
        </div>
      </div>
    </div>
  {/if}
</Layout>

<style>
  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }
  .scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
</style>
