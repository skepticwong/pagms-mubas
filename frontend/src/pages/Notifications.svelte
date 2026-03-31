<script>
  import Layout from '../components/Layout.svelte';
  import { notifications, markAsRead, removeNotification, clearAll } from '../stores/notifications.js';
  import Icon from '../components/Icon.svelte';

  function formatDate(date) {
    if (!date) return '';
    return new Date(date).toLocaleString();
  }

  function getTypeStyles(type) {
    switch (type) {
      case 'budget':
        return {
          bg: 'bg-red-50',
          border: 'border-red-100',
          text: 'text-red-700',
          icon: 'warning',
          iconColor: 'text-red-600'
        };
      case 'task':
        return {
          bg: 'bg-amber-50',
          border: 'border-amber-100',
          text: 'text-amber-700',
          icon: 'tasks',
          iconColor: 'text-amber-600'
        };
      case 'milestone':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-100',
          text: 'text-blue-700',
          icon: 'mission',
          iconColor: 'text-blue-600'
        };
      default:
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-100',
          text: 'text-gray-700',
          icon: 'info',
          iconColor: 'text-gray-600'
        };
    }
  }
</script>

<Layout>
  <div class="max-w-4xl mx-auto space-y-6 py-4">
    <!-- Header -->
    <div class="flex items-center justify-between bg-white/60 backdrop-blur-xl border border-white/60 rounded-3xl p-8 shadow-lg">
      <div>
        <h1 class="text-3xl font-bold text-gray-900">Notifications</h1>
        <p class="text-sm text-gray-600 mt-1">Stay updated on grant deadlines, budget limits, and team tasks.</p>
      </div>
      {#if $notifications.length > 0}
        <button 
          on:click={clearAll}
          class="px-4 py-2 bg-gray-900 text-white text-xs font-bold rounded-xl hover:bg-gray-800 transition-all shadow-lg"
        >
          Clear All
        </button>
      {/if}
    </div>

    {#if $notifications.length === 0}
      <div class="bg-white/70 backdrop-blur-xl border border-white/40 rounded-3xl p-16 shadow-md text-center">
        <div class="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-6">
          <Icon name="check" size={40} className="text-gray-300" />
        </div>
        <h3 class="text-xl font-bold text-gray-900">All caught up!</h3>
        <p class="text-gray-500 mt-2">You don't have any new notifications at the moment.</p>
      </div>
    {:else}
      <div class="space-y-3">
        {#each $notifications as n (n.id)}
          {@const styles = getTypeStyles(n.type)}
          <div 
            class="group relative flex items-start gap-4 p-5 rounded-2xl border transition-all {styles.bg} {styles.border} {n.read ? 'opacity-60 grayscale-[0.5]' : 'shadow-sm'}"
          >
            <!-- Type Icon -->
            <div class="w-10 h-10 rounded-xl bg-white flex items-center justify-center shrink-0 border {styles.border} shadow-sm">
               <Icon name={styles.icon} size={20} className={styles.iconColor} />
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-[10px] font-black uppercase tracking-widest {styles.text}">{n.type}</span>
                {#if n.grant_code}
                  <span class="h-1 w-1 bg-gray-300 rounded-full"></span>
                  <span class="text-[10px] font-bold text-gray-400">{n.grant_code}</span>
                {/if}
                <span class="ml-auto text-[10px] font-medium text-gray-400">{formatDate(n.timestamp)}</span>
              </div>
              <p class="text-sm font-semibold text-gray-900 leading-relaxed">{n.message}</p>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-2">
              {#if !n.read}
                <button 
                  on:click={() => markAsRead(n.id)}
                  class="p-2 hover:bg-white rounded-xl transition-all text-gray-400 hover:text-blue-600"
                  title="Mark as read"
                >
                  <Icon name="check" size={18} />
                </button>
              {/if}
              <button 
                on:click={() => removeNotification(n.id)}
                class="p-2 hover:bg-white rounded-xl transition-all text-gray-400 hover:text-red-600 opacity-0 group-hover:opacity-100"
                title="Dismiss"
              >
                <Icon name="close" size={18} />
              </button>
            </div>

            {#if !n.read}
              <div class="absolute -top-1 -left-1 w-3 h-3 bg-blue-500 rounded-full border-2 border-white"></div>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </div>
</Layout>
