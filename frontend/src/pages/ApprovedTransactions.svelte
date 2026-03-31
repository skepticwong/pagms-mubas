<script>
  import { onMount } from 'svelte';
  import Layout from '../components/Layout.svelte';
  import { showToast } from '../stores/toast.js';

  let loading = true;
  let search = '';
  let dateRange = '30d';
  let exportBusy = false;
  let transactions = [];

  const mockTransactions = [
    {
      id: 'TRX-5412',
      grant: 'Climate Smart Agriculture',
      category: 'Field Travel',
      vendor: 'MUBAS Logistics',
      amount: 1450,
      currency: 'USD',
      approval: 'Finance Ops · 18 Jan',
      paymentRef: 'TT-99231',
      paidOn: '2026-01-20'
    },
    {
      id: 'TRX-5388',
      grant: 'Water Sanitation',
      category: 'Construction',
      vendor: 'BluePump Africa',
      amount: 7800,
      currency: 'USD',
      approval: 'Treasury · 16 Jan',
      paymentRef: 'TT-99102',
      paidOn: '2026-01-18'
    },
    {
      id: 'TRX-5360',
      grant: 'Inclusive STEM Labs',
      category: 'Equipment',
      vendor: 'TechLab Imports',
      amount: 4200,
      currency: 'USD',
      approval: 'Finance Ops · 12 Jan',
      paymentRef: 'TT-99011',
      paidOn: '2026-01-14'
    }
  ];

  onMount(() => {
    setTimeout(() => {
      transactions = mockTransactions;
      loading = false;
    }, 320);
  });

  function filteredTransactions() {
    return transactions.filter((trx) => `${trx.id} ${trx.grant} ${trx.vendor}`.toLowerCase().includes(search.toLowerCase()));
  }

  function exportCsv() {
    exportBusy = true;
    setTimeout(() => {
      exportBusy = false;
      showToast('Audit trail exported (mock).', 'success');
    }, 500);
  }

  function totalPaid() {
    return filteredTransactions().reduce((sum, trx) => sum + trx.amount, 0);
  }
</script>

<Layout>
  <div class="max-w-6xl mx-auto space-y-8 py-4">
    <section class="bg-white/60 backdrop-blur-xl border border-white/60 rounded-3xl p-8 shadow-lg">
      <div class="flex flex-col gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.3em] text-blue-600 font-semibold">Finance · Audit trail</p>
          <h1 class="text-3xl font-bold text-gray-900">Approved & paid transactions</h1>
          <p class="text-sm text-gray-600">Every release logged with approver, payment reference, and timestamp.</p>
        </div>
        <div class="flex flex-wrap gap-3 text-xs text-gray-600">
          <span class="px-3 py-1 rounded-full bg-blue-50 text-blue-700">Realtime mirror</span>
          <span class="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700">{filteredTransactions().length} payments</span>
          <button class="ml-auto px-4 py-2 text-xs font-semibold rounded-full border border-gray-200 text-gray-700" type="button" on:click={exportCsv} disabled={exportBusy}>
            {exportBusy ? 'Exporting…' : 'Export CSV'}
          </button>
        </div>
      </div>
    </section>

    <section class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="p-5 rounded-2xl bg-white/70 border border-white/60">
        <p class="text-xs text-gray-500">Total paid (filter)</p>
        <p class="text-3xl font-bold text-gray-900">${totalPaid().toLocaleString()}</p>
      </div>
      <div class="p-5 rounded-2xl bg-white/70 border border-white/60">
        <p class="text-xs text-gray-500">Average approval time</p>
        <p class="text-3xl font-bold text-emerald-600">2.1 days</p>
      </div>
      <div class="p-5 rounded-2xl bg-white/70 border border-white/60">
        <p class="text-xs text-gray-500">Payments flagged</p>
        <p class="text-3xl font-bold text-rose-600">0</p>
      </div>
    </section>

    <section class="bg-white/70 backdrop-blur-xl border border-white/40 rounded-2xl shadow-md p-6 space-y-6">
      <div class="flex flex-wrap items-center gap-3">
        <input
          class="flex-1 min-w-[220px] px-4 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          type="search"
          placeholder="Search grant, vendor, or transaction id"
          bind:value={search}
        />
        <select class="px-3 py-2 rounded-xl border border-gray-200 text-sm" bind:value={dateRange}>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
        </select>
      </div>

      <div class="border border-dashed border-gray-200 rounded-2xl">
        <div class="grid grid-cols-12 px-5 py-3 text-xs font-semibold text-gray-500 uppercase">
          <span class="col-span-2">Transaction</span>
          <span class="col-span-3">Grant</span>
          <span class="col-span-2">Vendor</span>
          <span class="col-span-2">Amount</span>
          <span class="col-span-2">Approval</span>
          <span class="col-span-1">Paid</span>
        </div>
        {#if loading}
          <div class="p-8 text-center text-sm text-gray-500">Loading transactions…</div>
        {:else if filteredTransactions().length === 0}
          <div class="p-8 text-center text-sm text-gray-500">No transactions found for this filter.</div>
        {:else}
          {#each filteredTransactions() as trx}
            <div class="grid grid-cols-12 px-5 py-4 border-t border-gray-100 text-sm text-gray-800">
              <div class="col-span-2">
                <p class="font-semibold text-gray-900">{trx.id}</p>
                <p class="text-xs text-gray-500">{trx.paymentRef}</p>
              </div>
              <div class="col-span-3">
                <p class="font-semibold text-gray-900">{trx.grant}</p>
                <p class="text-xs text-gray-500">{trx.category}</p>
              </div>
              <div class="col-span-2">
                <p>{trx.vendor}</p>
              </div>
              <div class="col-span-2">
                <p class="font-semibold text-emerald-600">{trx.currency} {trx.amount.toLocaleString()}</p>
              </div>
              <div class="col-span-2">
                <p>{trx.approval}</p>
              </div>
              <div class="col-span-1">
                <p class="text-xs text-gray-500">{new Date(trx.paidOn).toLocaleDateString()}</p>
              </div>
            </div>
          {/each}
        {/if}
      </div>
    </section>

    <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white/70 backdrop-blur-xl border border-white/40 rounded-2xl shadow-md p-6">
        <h2 class="text-lg font-semibold text-gray-900">Control reminders</h2>
        <ul class="mt-4 space-y-2 text-sm text-gray-700">
          <li>• Dual approval (Finance + RSU) enforced for > $5K equipment.</li>
          <li>• Treasury references sync nightly with bank portal.</li>
          <li>• Keep vendor KYC refreshed every 12 months.</li>
        </ul>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/40 rounded-2xl shadow-md p-6">
        <h2 class="text-lg font-semibold text-gray-900">Audit exports</h2>
        <p class="text-sm text-gray-600">Send full ledger to auditors.</p>
        <div class="mt-4 flex flex-wrap gap-2">
          <button class="px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-semibold" type="button" on:click={exportCsv} disabled={exportBusy}>
            {exportBusy ? 'Exporting…' : 'Export ledger CSV'}
          </button>
          <button class="px-4 py-2 rounded-xl border border-gray-200 text-sm font-semibold" type="button">
            Download approvals PDF
          </button>
        </div>
      </div>
    </section>
  </div>
</Layout>

