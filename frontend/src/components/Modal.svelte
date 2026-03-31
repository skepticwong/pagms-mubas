<script>
  import { modal } from "../stores/modals.js";
  import { onMount } from "svelte";
  import Icon from "./Icon.svelte";

  let inputValue = "";
  let inputElement;

  $: if ($modal && $modal.type === 'prompt') {
    inputValue = $modal.defaultValue || "";
    // Wait for DOM to update then focus
    setTimeout(() => {
      if (inputElement) inputElement.focus();
    }, 50);
  }

  function handleConfirm() {
    if ($modal.type === 'prompt') {
      $modal.resolve(inputValue);
    } else {
      $modal.resolve(true);
    }
  }

  function handleCancel() {
    if ($modal.type === 'prompt') {
      $modal.resolve(null);
    } else {
      $modal.resolve(false);
    }
  }

  function handleKeydown(e) {
    if (e.key === "Escape") handleCancel();
    if (e.key === "Enter" && $modal.type === 'prompt') handleConfirm();
  }
</script>

{#if $modal}
  <div 
    class="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200"
    on:keydown={handleKeydown}
    role="none"
  >
    <div 
      class="bg-white/95 backdrop-blur-2xl border border-white/60 rounded-3xl shadow-2xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200"
      role="dialog"
      aria-modal="true"
    >
      <div class="p-6 pt-8 text-center">
        <div class="mb-4 w-14 h-14 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto">
          <Icon name={$modal.type === 'prompt' ? 'edit' : 'info'} size={28} />
        </div>
        
        <h2 class="text-xl font-bold text-gray-900 mb-2">
          {$modal.type === 'prompt' ? 'Action Required' : 'Confirm Action'}
        </h2>
        
        <p class="text-gray-600 text-sm leading-relaxed mb-6 px-4">
          {$modal.message}
        </p>

        {#if $modal.type === 'prompt'}
          <div class="mb-6 px-4">
            <input
              bind:this={inputElement}
              type="text"
              bind:value={inputValue}
              placeholder="Type here..."
              class="w-full px-5 py-3 bg-gray-50 border border-gray-200 rounded-2xl focus:bg-white focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 outline-none transition-all font-medium text-gray-900"
            />
          </div>
        {/if}

        <div class="flex gap-3 px-4 pb-2">
          <button 
            on:click={handleCancel}
            class="flex-1 py-3 px-6 rounded-2xl border border-gray-200 text-sm font-bold text-gray-600 hover:bg-gray-50 transition-all"
          >
            Cancel
          </button>
          <button 
            on:click={handleConfirm}
            class="flex-1 py-3 px-6 rounded-2xl bg-blue-600 text-white text-sm font-bold shadow-lg shadow-blue-200 hover:bg-blue-700 hover:-translate-y-0.5 transition-all"
          >
            {$modal.type === 'prompt' ? 'Submit' : 'Confirm'}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
