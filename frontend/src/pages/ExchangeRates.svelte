<script>
  import { onMount } from 'svelte';
  import Layout from '../components/Layout.svelte';

  let loading = true;
  let editable = false;
  let rates = [];
  let selectedRate = null;

  const mockRates = [
    { currency: 'USD', buying: 1705, selling: 1722, spread: 1.0, lastUpdated: '2026-01-28 09:35' },
    { currency: 'EUR', buying: 1850, selling: 1870, spread: 1.1, lastUpdated: '2026-01-27 11:20' },
    { currency: 'GBP', buying: 2125, selling: 2150, spread: 1.2, lastUpdated: '2026-01-27 14:05' }
  ];

  onMount(() => {
    setTimeout(() => {
      rates = mockRates;
      selectedRate = mockRates[0];
      loading = false;
    }, 200);
  });

  function selectRate(rate) {
    selectedRate = { ...rate };
  }

  function updateField(field, value) {
    if (!selectedRate) return;
    selectedRate = { ...selectedRate, [field]: Number(value) };
  }

  function saveRate() {
    editable = false;
    rates = rates.map((rate) => (rate.currency === selectedRate.currency ? selectedRate : rate));
  }
</script>

<Layout>
  <div class="max-w-5xl mx-auto space-y-8 py-4">
    <section class="bg-white/60 backdrop-blur-xl border border-white/60 rounded-3xl p-8 shadow-lg">
      <div class="flex flex-col gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.3em] text-blue-600 font-semibold">Finance · FX controls</p>
          <h1 class="text-3xl font-bold text-gray-900">Exchange rate board</h1>
          <p class="text-sm text-gray-600">Reference rates used across all grant disbursements and conversions.</p>
        </div>
        <div class="flex flex-wrap gap-3 text-xs text-gray-600">
          <span class="px-3 py-1 rounded-full bg-blue-50 text-blue-700">RBM spot + buffer</span>
          <span class="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700">Updates synced daily</span>
          <button class="ml-auto px-4 py-2 rounded-full border border-gray-200 text-gray-700" type="button" on:click={() => (editable = !editable)}>
            {editable ? 'Cancel edit' : 'Toggle edit'}
          </button>
        </div>
      </div>
    </section>

    <section class="grid grid-cols-1 md:grid-cols-3 gap-4">
      {#if loading}
        <div class="col-span-3 p-6 text-center text-sm text-gray-500">Loading rates…</div>
      {:else}
        {#each rates as rate}
          <button
            class={`p-5 rounded-2xl border text-left ${selectedRate?.currency === rate.currency ? 'border-blue-500 bg-blue-50/60' : 'border-white/60 bg-white/70'}`}
            type="button"
            on:click={() => selectRate(rate)}
          >
            <p class="text-sm text-gray-500">{rate.currency}</p>
            <p class="text-2xl font-bold text-gray-900">Buying {rate.buying}</p>
            <p class="text-sm text-gray-500">Selling {rate.selling}</p>
            <p class="text-xs text-gray-400 mt-2">Updated {rate.lastUpdated}</p>
          </button>
        {/each}
      {/if}
    </section>

    {#if selectedRate}
      <section class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-md p-6 space-y-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">Editing</p>
            <h2 class="text-2xl font-semibold text-gray-900">{selectedRate.currency} reference rate</h2>
            <p class="text-xs text-gray-500">Last updated {selectedRate.lastUpdated}</p>
          </div>
          {#if editable}
            <button class="px-4 py-2 rounded-xl bg-emerald-600 text-white text-sm font-semibold" type="button" on:click={saveRate}>
              Save changes
            </button>
          {/if}
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-700">
          <div class="p-4 rounded-2xl border border-gray-100">
            <p class="text-xs text-gray-500">Buying rate</p>
            {#if editable}
              <input class="mt-2 w-full px-3 py-2 rounded-xl border border-gray-200" type="number" bind:value={selectedRate.buying} on:input={(e) => updateField('buying', e.target.value)} />
            {:else}
              <p class="text-2xl font-semibold text-gray-900">{selectedRate.buying}</p>
            {/if}
          </div>
          <div class="p-4 rounded-2xl border border-gray-100">
            <p class="text-xs text-gray-500">Selling rate</p>
            {#if editable}
              <input class="mt-2 w-full px-3 py-2 rounded-xl border border-gray-200" type="number" bind:value={selectedRate.selling} on:input={(e) => updateField('selling', e.target.value)} />
            {:else}
              <p class="text-2xl font-semibold text-gray-900">{selectedRate.selling}</p>
            {/if}
          </div>
          <div class="p-4 rounded-2xl border border-gray-100">
            <p class="text-xs text-gray-500">Buffer spread</p>
            <p class="text-2xl font-semibold text-amber-600">{selectedRate.spread}%</p>
          </div>
        </div>
        <div class="space-y-3 text-sm text-gray-700">
          <p class="text-xs uppercase tracking-wide text-gray-500">Grant usage</p>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="p-4 rounded-2xl border border-gray-100">
              <p class="text-xs text-gray-500">Grants referencing this rate</p>
              <p class="text-lg font-semibold text-gray-900">4</p>
            </div>
            <div class="p-4 rounded-2xl border border-gray-100">
              <p class="text-xs text-gray-500">Next refresh</p>
              <p class="text-lg font-semibold text-gray-900">Tomorrow 09:00</p>
            </div>
          </div>
        </div>
      </section>
    {/if}

    <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white/70 backdrop-blur-xl border border-white/40 rounded-2xl shadow-md p-6">
        <h2 class="text-lg font-semibold text-gray-900">Policy reminders</h2>
        <ul class="mt-4 space-y-2 text-sm text-gray-700">
          <li>• Rates track Reserve Bank of Malawi spot + 1% buffer.</li>
          <li>• Any manual override requires CFO approval (logged).</li>
          <li>• All conversions auto-log reference rate for audits.</li>
        </ul>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/40 rounded-2l shadow-md p-6">
        <h2 class="text-lg font-semibold text-gray-900">Integrations</h2>
        <p class="text-sm text-gray-600">Live feeds sync hourly with treasury API.</p>
        <div class="mt-4 space-y-2 text-sm text-gray-700">
          <p>• Source: RBM + OANDA composite.</p>
          <p>• Logs stored for 7 years.</p>
          <p>• Upcoming: auto-hedge suggestions (Q3 roadmap).</p>
        </div>
      </div>
    </section>
  </div>
</Layout>

