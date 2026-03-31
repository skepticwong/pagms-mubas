<script>
  import { toast, dismissToast } from "../stores/toast.js";
  import Icon from "./Icon.svelte";

  function dismiss() {
    dismissToast();
  }
</script>

{#if $toast}
  <div
    class="fixed bottom-6 right-6 z-[100] max-w-md w-[calc(100%-2rem)] toast-pop"
    role="status"
    aria-live="polite"
  >
    <div
      class="rounded-2xl shadow-2xl border backdrop-blur-md px-4 py-3 flex items-start gap-3
        {$toast.type === 'success'
        ? 'bg-emerald-50/95 border-emerald-200 text-emerald-900'
        : $toast.type === 'error'
          ? 'bg-rose-50/95 border-rose-200 text-rose-900'
          : 'bg-slate-900/90 border-slate-700 text-white'}"
    >
      <div
        class="mt-0.5 flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center
          {$toast.type === 'success'
          ? 'bg-emerald-500 text-white'
          : $toast.type === 'error'
            ? 'bg-rose-500 text-white'
            : 'bg-slate-600 text-white'}"
      >
        {#if $toast.type === "success"}
          <Icon name="check" size={18} />
        {:else if $toast.type === "error"}
          <Icon name="close" size={18} />
        {:else}
          <Icon name="info" size={18} />
        {/if}
      </div>
      <p class="text-sm font-medium leading-snug flex-1 pt-0.5">{$toast.message}</p>
      <button
        type="button"
        class="flex-shrink-0 p-1 rounded-lg opacity-70 hover:opacity-100 hover:bg-black/5 transition"
        on:click={dismiss}
        aria-label="Dismiss"
      >
        <Icon name="close" size={16} />
      </button>
    </div>
  </div>
{/if}

<style>
  .toast-pop {
    animation: toastPop 0.28s ease-out;
  }
  @keyframes toastPop {
    from {
      opacity: 0;
      transform: translateY(12px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>
