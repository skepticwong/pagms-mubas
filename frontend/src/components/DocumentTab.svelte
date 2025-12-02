<script>
    import axios from "axios";
    import { onMount } from "svelte";
    import { user } from "../stores/auth.js";

    export let grantId;
    export let grantTitle;

    let documents = [];
    let loading = true;
    let uploading = false;
    let error = "";
    let success = "";

    // Upload form state
    let fileInput;
    let selectedFile = null;
    let docType = "Award Letter";

    const docTypes = [
        "Award Letter",
        "Agreement",
        "Budget Breakdown",
        "Expense Receipt",
        "Evidence",
        "Final Report",
        "Milestone Evidence",
        "Ethical Approval",
        "Other",
    ];

    async function fetchDocuments() {
        loading = true;
        try {
            const url = grantId
                ? `http://localhost:5000/api/documents?grant_id=${grantId}`
                : `http://localhost:5000/api/documents`;
            const res = await axios.get(url, {
                withCredentials: true,
            });
            documents = res.data || [];
        } catch (err) {
            console.error("Failed to fetch documents:", err);
            // error = "Failed to load documents.";
        } finally {
            loading = false;
        }
    }

    onMount(fetchDocuments);

    async function handleUpload() {
        if (!selectedFile) {
            error = "Please select a file first.";
            return;
        }

        uploading = true;
        error = "";
        success = "";

        const formData = new FormData();
        formData.append("file", selectedFile);
        formData.append("grant_id", grantId);
        formData.append("doc_type", docType);

        try {
            await axios.post(
                "http://localhost:5000/api/documents/upload",
                formData,
                {
                    headers: { "Content-Type": "multipart/form-data" },
                    withCredentials: true,
                },
            );
            success = "Document uploaded successfully!";
            selectedFile = null;
            if (fileInput) fileInput.value = "";
            await fetchDocuments();
        } catch (err) {
            console.error("Upload error:", err);
            error = err.response?.data?.error || "Failed to upload document.";
        } finally {
            uploading = false;
        }
    }

    function handleFileChange(e) {
        selectedFile = e.target.files[0];
    }

    function formatDate(dateStr) {
        if (!dateStr) return "N/A";
        return new Date(dateStr).toLocaleString("en-GB", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    function getVersionColor(version) {
        if (version === 1) return "text-gray-500";
        return "text-blue-600 font-bold";
    }
</script>

<div class="space-y-6">
    <div
        class="flex flex-col sm:flex-row sm:items-center justify-between gap-3"
    >
        <div>
            <h3 class="text-lg font-bold text-gray-900">Document Repository</h3>
            <p class="text-sm text-gray-600">{grantTitle}</p>
        </div>
        <p
            class="text-xs font-mono bg-gray-100 px-2 py-1 rounded text-gray-600"
        >
            Total: {documents.length} files
        </p>
    </div>

    <!-- Upload Section -->
    {#if grantId && ($user.role === "PI" || $user.role === "Team")}
        <div
            class="p-5 bg-blue-50/40 rounded-3xl border border-blue-100/50 space-y-4 shadow-sm"
        >
            <div class="flex items-center gap-2">
                <div
                    class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold"
                >
                    ↑
                </div>
                <h4 class="text-sm font-bold text-blue-900">
                    Upload / Version File
                </h4>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                <div class="space-y-1">
                    <label
                        for="doc-type-select"
                        class="block text-[10px] uppercase tracking-wider font-bold text-blue-800 ml-1"
                        >Document Purpose</label
                    >
                    <select
                        id="doc-type-select"
                        bind:value={docType}
                        class="w-full rounded-2xl border-blue-100 bg-white text-sm focus:ring-blue-500 focus:border-blue-500 transition-all shadow-sm"
                    >
                        {#each docTypes as type}
                            <option value={type}>{type}</option>
                        {/each}
                    </select>
                </div>
                <div class="space-y-1">
                    <label
                        for="file-upload-input"
                        class="block text-[10px] uppercase tracking-wider font-bold text-blue-800 ml-1"
                        >Select File</label
                    >
                    <input
                        id="file-upload-input"
                        type="file"
                        bind:this={fileInput}
                        on:change={handleFileChange}
                        class="w-full text-xs text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer shadow-sm"
                    />
                </div>
                <div>
                    <button
                        on:click={handleUpload}
                        disabled={uploading || !selectedFile}
                        class="w-full py-2.5 px-4 bg-white border border-blue-200 text-blue-700 rounded-2xl text-xs font-black shadow-sm hover:bg-blue-50 disabled:opacity-50 transition-all active:scale-95 flex items-center justify-center gap-2"
                    >
                        {#if uploading}
                            <div
                                class="w-3 h-3 border-2 border-blue-600 border-t-transparent animate-spin rounded-full"
                            ></div>
                            UPLOADING...
                        {:else}
                            + PROCESS UPLOAD
                        {/if}
                    </button>
                </div>
            </div>

            {#if error}
                <div
                    class="flex items-center gap-2 text-[11px] text-red-600 bg-red-50 p-2 rounded-xl border border-red-100"
                >
                    <span class="font-bold">Error:</span>
                    {error}
                </div>
            {/if}
            {#if success}
                <div
                    class="flex items-center gap-2 text-[11px] text-green-700 bg-green-50 p-2 rounded-xl border border-green-100"
                >
                    <span class="font-bold">Success:</span>
                    {success}
                </div>
            {/if}
        </div>
    {/if}

    <!-- Documents Table -->
    <div
        class="bg-white/80 backdrop-blur-md border border-gray-100 rounded-3xl shadow-sm overflow-hidden"
    >
        {#if loading}
            <div
                class="p-16 flex flex-col items-center justify-center space-y-4"
            >
                <div class="relative w-12 h-12">
                    <div
                        class="absolute inset-0 border-4 border-blue-100 rounded-full"
                    ></div>
                    <div
                        class="absolute inset-0 border-4 border-blue-600 rounded-full border-t-transparent animate-spin"
                    ></div>
                </div>
                <p
                    class="text-xs font-bold text-gray-400 uppercase tracking-widest"
                >
                    Synchronizing Vault
                </p>
            </div>
        {:else if documents.length === 0}
            <div class="p-16 text-center">
                <div
                    class="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4 border border-gray-100"
                >
                    <span class="text-4xl grayscale opacity-30">📂</span>
                </div>
                <h4 class="text-gray-900 font-bold mb-1">Vault is Empty</h4>
                <p class="text-xs text-gray-500 max-w-[200px] mx-auto">
                    No digital assets have been archived for this grant module
                    yet.
                </p>
            </div>
        {:else}
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-100">
                    <thead class="bg-gray-50/50">
                        <tr>
                            <th
                                class="px-6 py-4 text-left text-[10px] font-black text-gray-400 uppercase tracking-widest"
                                >Document Registry</th
                            >
                            <th
                                class="px-6 py-4 text-left text-[10px] font-black text-gray-400 uppercase tracking-widest"
                                >Category</th
                            >
                            <th
                                class="px-6 py-4 text-left text-[10px] font-black text-gray-400 uppercase tracking-widest"
                                >Authentication</th
                            >
                            <th
                                class="px-6 py-4 text-left text-[10px] font-black text-gray-400 uppercase tracking-widest"
                                >Timestamp</th
                            >
                            <th
                                class="px-6 py-4 text-left text-[10px] font-black text-gray-400 uppercase tracking-widest text-center"
                                >v#</th
                            >
                            <th
                                class="px-6 py-4 text-right text-[10px] font-black text-gray-400 uppercase tracking-widest"
                                >Access</th
                            >
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-50">
                        {#each documents as doc}
                            <tr
                                class={doc.is_superseded
                                    ? "bg-gray-50 opacity-60"
                                    : "hover:bg-blue-50/20 transition-colors group"}
                            >
                                <td class="px-6 py-5 whitespace-nowrap">
                                    <div class="flex items-center gap-3">
                                        <div
                                            class="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center text-xl shadow-sm border border-white group-hover:bg-blue-100 group-hover:text-blue-600 transition-colors"
                                        >
                                            {doc.file_name.endsWith(".pdf")
                                                ? "📕"
                                                : doc.file_name.endsWith(
                                                        ".jpg",
                                                    ) ||
                                                    doc.file_name.endsWith(
                                                        ".png",
                                                    )
                                                  ? "🎨"
                                                  : "📄"}
                                        </div>
                                        <div class="flex flex-col">
                                            <span
                                                class="text-sm font-bold {doc.is_superseded
                                                    ? 'text-gray-400'
                                                    : 'text-gray-900'} truncate max-w-[180px]"
                                            >
                                                {doc.file_name}
                                            </span>
                                            {#if doc.is_superseded}
                                                <span
                                                    class="text-[9px] font-black bg-amber-100 text-amber-700 w-fit px-1.5 rounded-sm uppercase mt-1"
                                                    >SUPERSEDED</span
                                                >
                                            {:else}
                                                <span
                                                    class="text-[9px] font-bold text-blue-500 uppercase mt-0.5"
                                                    >Active Asset</span
                                                >
                                            {/if}
                                        </div>
                                    </div>
                                </td>
                                <td class="px-6 py-5 whitespace-nowrap">
                                    <span
                                        class="px-2.5 py-1 text-[10px] font-black rounded-lg border {doc.is_superseded
                                            ? 'border-gray-200 bg-gray-50 text-gray-400'
                                            : 'border-emerald-100 bg-emerald-50 text-emerald-700 shadow-sm'}"
                                    >
                                        {doc.doc_type.toUpperCase()}
                                    </span>
                                </td>
                                <td class="px-6 py-5 whitespace-nowrap">
                                    <div class="flex flex-col">
                                        <div
                                            class="text-[11px] font-bold {doc.is_superseded
                                                ? 'text-gray-400'
                                                : 'text-gray-700'}"
                                        >
                                            {doc.uploader_name}
                                        </div>
                                        <div
                                            class="text-[9px] font-black text-gray-400 uppercase tracking-tighter"
                                        >
                                            {doc.uploader_role}
                                        </div>
                                    </div>
                                </td>
                                <td
                                    class="px-6 py-5 whitespace-nowrap text-[11px] font-medium text-gray-500"
                                >
                                    {formatDate(doc.created_at)}
                                </td>
                                <td
                                    class="px-6 py-5 whitespace-nowrap text-center"
                                >
                                    <span
                                        class="text-xs {getVersionColor(
                                            doc.version,
                                        )} bg-gray-100 px-2 py-0.5 rounded-lg border border-white shadow-sm"
                                    >
                                        {doc.version}
                                    </span>
                                </td>
                                <td
                                    class="px-6 py-5 whitespace-nowrap text-right"
                                >
                                    <a
                                        href={`http://localhost:5000/api/documents/download/${doc.id}`}
                                        target="_blank"
                                        class="inline-flex items-center gap-1.5 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-[10px] font-black rounded-xl shadow-md transition-all active:scale-95"
                                    >
                                        VIEW FILE
                                    </a>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        {/if}
    </div>
</div>
