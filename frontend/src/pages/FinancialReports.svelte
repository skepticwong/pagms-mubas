<script>
  import Layout from '../components/Layout.svelte';
</script>

<Layout>
  <div class="max-w-6xl mx-auto space-y-6">
    <div class="space-y-1">
      <h1 class="text-2xl font-bold text-gray-900">Financial Reports</h1>
      <p class="text-sm text-gray-600">Export funder-ready financial statements for selected grants and periods.</p>
    </div>

    <div class="bg-white/70 backdrop-blur-xl border border-white/40 rounded-2xl shadow-md p-6">
      <p class="text-sm text-gray-700">
        This is a placeholder screen. Here you’ll be able to:
      </p>
      <ul class="mt-2 list-disc list-inside text-sm text-gray-700 space-y-1">
        <li>Select grants and reporting periods.</li>
        <li>Generate funder-specific report formats automatically.</li>
        <li>Download reports as Excel/PDF for submission.</li>
      </ul>
    </div>
  </div>
</Layout>

