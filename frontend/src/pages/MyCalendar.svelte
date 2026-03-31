<script>
  import { onMount } from "svelte";
  import axios from "axios";
  import { showToast } from "../stores/toast.js";
  import { user } from "../stores/auth.js";
  import { router } from "../stores/router.js";
  import Layout from "../components/Layout.svelte";
  import Icon from "../components/Icon.svelte";

  let events = [];
  let loading = true;
  let currentDate = new Date();
  let showCreateModal = false;
  let selectedDate = null;
  let grants = [];

  // New Event Form
  let newEvent = {
    title: "",
    description: "",
    event_date: "",
    event_type: "PERSONAL",
    grant_id: null,
    target_role: null
  };

  onMount(async () => {
    await fetchEvents();
    if (["PI", "RSU", "Finance"].includes($user.role)) {
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
      showToast("Could not load calendar events", "error");
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
      await axios.post("/api/events", newEvent, { withCredentials: true });
      showCreateModal = false;
      resetForm();
      await fetchEvents();
      showToast("Event saved successfully", "success");
    } catch (err) {
      showToast("Failed to save event: " + (err.response?.data?.error || err.message), "error");
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
    return events.filter(e => {
      const ed = new Date(e.event_date);
      return ed.getDate() === day && ed.getMonth() === month && ed.getFullYear() === year;
    });
  }

  function openCreateModal(day = null) {
    if (day) {
      selectedDate = new Date(year, month, day);
      // Format for datetime-local input
      const localDate = new Date(selectedDate.getTime() - (selectedDate.getTimezoneOffset() * 60000));
      localDate.setHours(9, 0, 0, 0); // Default to 9 AM
      newEvent.event_date = localDate.toISOString().slice(0, 16);
    }
    showCreateModal = true;
  }

  const typeColors = {
    BROADCAST: "bg-red-100 text-red-700 border-red-200",
    GRANT: "bg-blue-100 text-blue-700 border-blue-200",
    SYSTEM: "bg-emerald-100 text-emerald-700 border-emerald-200",
    PERSONAL: "bg-indigo-100 text-indigo-700 border-indigo-200",
    FINANCE: "bg-amber-100 text-amber-700 border-amber-200"
  };

  $: sortedEvents = [...events]
    .sort((a,b) => new Date(a.event_date) - new Date(b.event_date))
    .filter(e => new Date(e.event_date) >= new Date().setHours(0,0,0,0));

  const monthNames = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
</script>

<Layout>
  <div class="space-y-6 pt-2 pb-10">
    <!-- Premium Header -->
    <section class="bg-gradient-to-r from-indigo-600 via-purple-600 to-blue-600 rounded-3xl p-8 shadow-2xl relative overflow-hidden text-white">
      <div class="absolute top-0 right-0 p-8 opacity-10">
        <Icon name="calendar" size={120} />
      </div>
      <div class="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 class="text-4xl font-black mb-2">My Calendar</h1>
          <p class="text-indigo-100 max-w-xl">
            Stay ahead of deadlines, milestones, and system updates. Personalize your schedule with custom events.
          </p>
        </div>
        <button 
          on:click={() => openCreateModal()}
          class="flex items-center gap-2 bg-white text-indigo-600 px-6 py-3 rounded-2xl font-bold hover:bg-indigo-50 transition-all shadow-xl active:scale-95">
          <Icon name="plus" size={20} />
          Create Event
        </button>
      </div>
    </section>

    <!-- Calendar Controls -->
    <div class="bg-white/70 backdrop-blur-xl rounded-3xl border border-white/60 p-4 shadow-lg flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button on:click={prevMonth} class="p-2 hover:bg-gray-100 rounded-xl transition-colors text-gray-600">
          <Icon name="chevron-left" size={24} />
        </button>
        <div class="text-center min-w-[180px]">
          <h2 class="text-2xl font-black text-gray-900 leading-none">{monthNames[month]}</h2>
          <span class="text-xs font-bold text-gray-500 uppercase tracking-widest">{year}</span>
        </div>
        <button on:click={nextMonth} class="p-2 hover:bg-gray-100 rounded-xl transition-colors text-gray-600">
          <Icon name="chevron-right" size={24} />
        </button>
      </div>
      
      <!-- Legend (Desktop) -->
      <div class="hidden lg:flex items-center gap-4 text-[10px] font-bold uppercase tracking-tighter">
        <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-red-400"></span> Broadcast</div>
        <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-blue-400"></span> Grant</div>
        <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span> System</div>
        <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-indigo-400"></span> Personal</div>
        <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-amber-400"></span> Finance</div>
      </div>
    </div>

    <!-- Calendar Main Content (Two Columns) -->
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
      
      <!-- Left Column: Calendar Grid (3/4 width) -->
      <div class="lg:col-span-3 space-y-6">
        <div class="bg-white/40 backdrop-blur-2xl rounded-[2.5rem] border border-white/40 overflow-hidden shadow-2xl relative">
          {#if loading}
            <div class="absolute inset-0 z-10 flex items-center justify-center bg-white/20 backdrop-blur-sm">
              <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
          {/if}

          <div class="grid grid-cols-7 border-b border-gray-200/50 bg-gray-50/30">
            {#each ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as day}
              <div class="py-4 text-center text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">{day}</div>
            {/each}
          </div>

          <div class="grid grid-cols-7 min-h-[500px]">
            {#each blanks as _}
              <div class="border-r border-b border-gray-100/50 bg-gray-50/20"></div>
            {/each}
            {#each days as day}
              {@const isToday = day === new Date().getDate() && month === new Date().getMonth() && year === new Date().getFullYear()}
              {@const dayEvents = getEventsForDay(day)}
              <div 
                class="group relative border-r border-b border-gray-100/50 p-2 hover:bg-indigo-50/50 transition-all cursor-pointer flex flex-col items-start min-h-[110px]"
                role="button"
                tabindex="0"
                on:click={() => openCreateModal(day)}
                on:keydown={(e) => e.key === 'Enter' && openCreateModal(day)}>
                
                <div class="flex justify-between items-center w-full mb-1">
                  <span class="text-xs font-bold {isToday ? 'bg-indigo-600 text-white w-6 h-6 flex items-center justify-center rounded-full shadow-lg shadow-indigo-200' : 'text-gray-700'}">
                    {day}
                  </span>
                </div>

                <div class="space-y-1 w-full overflow-y-auto pr-1 scrollbar-hide flex-1">
                  {#each dayEvents as event}
                    <div class="px-2 py-1 rounded-lg text-[9px] font-bold border truncate transition-all hover:brightness-95 shadow-sm {typeColors[event.event_type] || typeColors.PERSONAL}">
                      {event.title}
                    </div>
                  {/each}
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>

      <!-- Right Column: Upcoming List Sidebar (1/4 width) -->
      <aside class="space-y-6">
        <div class="bg-white/70 backdrop-blur-xl rounded-[2.5rem] border border-white/60 p-6 shadow-xl h-full flex flex-col">
          <h3 class="text-xl font-black text-gray-900 mb-4 flex items-center gap-2">
            <Icon name="clock" size={20} className="text-indigo-600" />
            Agenda
          </h3>
          
          <div class="space-y-4 overflow-y-auto pr-2 flex-1 max-h-[600px] scrollbar-hide">
            {#each sortedEvents.slice(0, 10) as event}
              <div class="p-4 rounded-2xl border border-gray-100 bg-gray-50/50 hover:bg-white hover:shadow-md transition-all group">
                <div class="flex items-center gap-2 mb-1">
                  <div class="w-1.5 h-1.5 rounded-full {event.event_type === 'BROADCAST' ? 'bg-red-500' : event.event_type === 'GRANT' ? 'bg-blue-500' : 'bg-indigo-500'}"></div>
                  <span class="text-[10px] font-black text-gray-400 uppercase tracking-widest">{event.event_type}</span>
                </div>
                <p class="font-bold text-gray-900 line-clamp-2 leading-tight group-hover:text-indigo-600 transition-colors">{event.title}</p>
                <div class="flex items-center gap-1.5 mt-2 text-[11px] font-bold text-gray-500">
                  <Icon name="calendar" size={12} />
                  {new Date(event.event_date).toLocaleDateString('en-GB', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            {:else}
              <div class="text-center py-10">
                <p class="text-gray-400 font-medium text-sm">No upcoming events.</p>
              </div>
            {/each}
          </div>

          <div class="mt-6 pt-6 border-t border-gray-100">
            <button 
              on:click={() => openCreateModal()}
              class="w-full py-3 bg-indigo-600 text-white rounded-2xl font-bold text-sm shadow-xl shadow-indigo-100 hover:bg-indigo-700 active:scale-95 transition-all">
              + New Agenda Item
            </button>
          </div>
        </div>
      </aside>
    </div>
  </div>

  <!-- Create Event Modal -->
  {#if showCreateModal}
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-indigo-900/40 backdrop-blur-md">
      <div class="bg-white rounded-[2rem] shadow-2xl w-full max-w-xl overflow-hidden border border-white/20 animate-in fade-in zoom-in duration-300">
        <div class="px-8 py-6 bg-gradient-to-br from-indigo-600 to-purple-700 text-white flex justify-between items-center">
          <div>
            <h3 class="text-2xl font-black">Design New Event</h3>
            <p class="text-indigo-100 text-xs font-bold uppercase tracking-widest mt-1">Calendar Integration</p>
          </div>
          <button on:click={() => showCreateModal = false} class="bg-white/20 hover:bg-white/30 p-2 rounded-2xl transition-all">
            <Icon name="x" size={24} />
          </button>
        </div>
        
        <div class="p-8 space-y-5">
          <div class="space-y-1">
            <label for="event-title" class="block text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Event Title</label>
            <input 
              id="event-title"
              type="text" 
              bind:value={newEvent.title}
              class="w-full px-5 py-3 rounded-2xl border-2 border-gray-100 focus:border-indigo-500 outline-none transition-all font-bold text-gray-800 placeholder:text-gray-300"
              placeholder="What are we doing?..."
            />
          </div>
          
          <div class="grid grid-cols-2 gap-5">
            <div class="space-y-1">
              <label for="event-date" class="block text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Date & Time</label>
              <input 
                id="event-date"
                type="datetime-local" 
                bind:value={newEvent.event_date}
                class="w-full px-5 py-3 rounded-2xl border-2 border-gray-100 focus:border-indigo-500 outline-none transition-all font-bold text-gray-800"
              />
            </div>
            <div class="space-y-1">
              <label for="event-type" class="block text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Context</label>
              <select 
                id="event-type"
                bind:value={newEvent.event_type}
                class="w-full px-5 py-3 rounded-2xl border-2 border-gray-100 focus:border-indigo-500 outline-none transition-all font-bold text-gray-800 appearance-none bg-no-repeat bg-[right_1.25rem_center]"
              >
                <option value="PERSONAL">Personal Item</option>
                {#if ["PI", "RSU"].includes($user.role)}
                  <option value="GRANT">Grant Activity</option>
                {/if}
                {#if $user.role === "RSU"}
                  <option value="BROADCAST">System Broadcast</option>
                {/if}
                {#if $user.role === "Finance"}
                  <option value="FINANCE">Finance Update (for PI)</option>
                {/if}
              </select>
            </div>
          </div>

          {#if newEvent.event_type === 'GRANT'}
          <div class="space-y-1 animate-in slide-in-from-top-2 duration-300">
            <label for="target-grant" class="block text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Target Grant</label>
            <select 
              id="target-grant"
              bind:value={newEvent.grant_id}
              class="w-full px-5 py-3 rounded-2xl border-2 border-gray-100 focus:border-indigo-500 outline-none transition-all font-bold text-gray-800"
            >
              <option value={null}>Select the applicable project...</option>
              {#each grants as g}
                <option value={g.id}>{g.grant_code} — {g.title}</option>
              {/each}
            </select>
          </div>
          {/if}

          {#if newEvent.event_type === 'BROADCAST'}
          <div class="space-y-1 animate-in slide-in-from-top-2 duration-300">
            <label for="target-role" class="block text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Audience Filter</label>
            <select 
              id="target-role"
              bind:value={newEvent.target_role}
              class="w-full px-5 py-3 rounded-2xl border-2 border-gray-100 focus:border-indigo-500 outline-none transition-all font-bold text-gray-800"
            >
              <option value={null}>Notify Everyone</option>
              <option value="PI">Principal Investigators Only</option>
              <option value="Team">Field Team Member Only</option>
              <option value="Finance">Finance Department Only</option>
            </select>
          </div>
          {/if}

          <div class="space-y-1">
            <label for="event-desc" class="block text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Brief Description</label>
            <textarea 
              id="event-desc"
              bind:value={newEvent.description}
              rows="3"
              class="w-full px-5 py-3 rounded-2xl border-2 border-gray-100 focus:border-indigo-500 outline-none transition-all font-bold text-gray-800 placeholder:text-gray-300 resize-none"
              placeholder="Add some context for your future self..."
            ></textarea>
          </div>
        </div>

        <div class="px-8 py-6 bg-gray-50 flex justify-end gap-3 border-t border-gray-100">
          <button 
            on:click={() => showCreateModal = false}
            class="px-6 py-3 rounded-2xl font-bold text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all">
            Discard
          </button>
          <button 
            on:click={saveEvent}
            disabled={!newEvent.title || !newEvent.event_date}
            class="px-8 py-3 rounded-2xl font-bold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-30 disabled:cursor-not-allowed shadow-xl shadow-indigo-200 transition-all active:scale-95">
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
