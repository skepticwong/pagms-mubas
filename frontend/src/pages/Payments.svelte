<script>
  import Layout from '../components/Layout.svelte';
</script>

<Layout>
  <div class="max-w-5xl mx-auto space-y-6">
    <div class="space-y-1">
      <h1 class="text-2xl font-bold text-gray-900">My Payments</h1>
      <p class="text-sm text-gray-600">View certified effort and payment status for your work.</p>
    </div>

    <div class="bg-white/70 backdrop-blur-xl border border-white/40 rounded-2xl shadow-md p-6">
      <p class="text-sm text-gray-700">
        This is a placeholder screen. Here you’ll be able to:
      </p>
      <ul class="mt-2 list-disc list-inside text-sm text-gray-700 space-y-1">
        <li>See which months/periods have certified effort.</li>
        <li>Track payment status (pending, processing, paid).</li>
        <li>View payment details and related effort reports.</li>
      </ul>
    </div>
  </div>
</Layout>

