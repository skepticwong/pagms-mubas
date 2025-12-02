<script>
  import Layout from '../components/Layout.svelte';
</script>

<Layout>
  <div class="max-w-4xl mx-auto space-y-6">
    <div class="space-y-1">
      <h1 class="text-2xl font-bold text-gray-900">Notifications</h1>
      <p class="text-sm text-gray-600">See alerts about deadlines, budgets, tasks, and RSU messages.</p>
    </div>

    <div class="bg-white/70 backdrop-blur-xl border border-white/40 rounded-2xl shadow-md p-6">
      <p class="text-sm text-gray-700">
        This is a placeholder screen. Here you’ll be able to:
      </p>
      <ul class="mt-2 list-disc list-inside text-sm text-gray-700 space-y-1">
        <li>View alerts for overdue tasks and upcoming deadlines.</li>
        <li>Receive budget warnings and compliance reminders.</li>
        <li>Read messages and announcements from RSU.</li>
      </ul>
    </div>
  </div>
</Layout>

