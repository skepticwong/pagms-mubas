<script>
    import Layout from "../components/Layout.svelte";
    import DocumentTab from "../components/DocumentTab.svelte";
</script>

<Layout>
    <div class="max-w-7xl mx-auto space-y-6">
        <div
            class="flex flex-col md:flex-row md:items-center md:justify-between gap-3"
        >
            <div>
                <h1 class="text-2xl md:text-3xl font-bold text-gray-900">
                    Document Repository
                </h1>
                <p class="text-sm text-gray-600">
                    Centralized access to all grant-related digital assets and
                    version history.
                </p>
            </div>
        </div>

        <div
            class="bg-white/80 backdrop-blur-xl border border-white/60 rounded-3xl shadow-sm p-6"
        >
            <DocumentTab grantId={null} grantTitle="Global Archive" />
        </div>
    </div>
</Layout>
