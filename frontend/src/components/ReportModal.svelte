<script>
    import { createEventDispatcher, onMount } from "svelte";
    import axios from "axios";

    export let grant = null;

    const dispatch = createEventDispatcher();

    let options = [];
    let selectedOption = "";
    let isLoadingOptions = true;
    let isGenerating = false;
    let result = null;
    let error = "";

    onMount(async () => {
        if (grant) {
            await fetchOptions();
        }
    });

    async function fetchOptions() {
        isLoadingOptions = true;
        try {
            const response = await axios.get(
                `http://localhost:5000/api/grants/${grant.id}/reporting-options`,
                { withCredentials: true },
            );
            options = response.data;
            if (options.length > 0) {
                selectedOption = options[0].id;
            }
        } catch (err) {
            error = "Failed to load reporting options.";
        } finally {
            isLoadingOptions = false;
        }
    }

    async function handleGenerate() {
        if (!selectedOption) return;

        isGenerating = true;
        error = "";
        result = null;

        const option = options.find((o) => o.id === selectedOption);

        try {
            const response = await axios.post(
                `http://localhost:5000/api/grants/${grant.id}/generate-report`,
                {
                    type: option.type,
                    value: option.value,
                },
                { withCredentials: true },
            );
            result = response.data;
        } catch (err) {
            error = err.response?.data?.error || "Failed to generate report.";
        } finally {
            isGenerating = false;
        }
    }

    function handleClose() {
        dispatch("close");
    }

    function getOptionLabel(id) {
        return options.find((o) => o.id === id)?.label || "";
    }
</script>

<div class="fixed inset-0 z-[100] flex items-center justify-center p-4">
    <!-- Backdrop -->
    <div
        class="absolute inset-0 bg-gray-900/40 backdrop-blur-sm transition-opacity"
        on:click={handleClose}
        on:keydown={(e) => e.key === "Escape" && handleClose()}
        role="button"
        tabindex="-1"
        aria-label="Close modal backdrop"
    ></div>

    <!-- Modal content -->
    <div
        class="relative bg-white rounded-[2rem] shadow-2xl w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-200"
    >
        <div class="p-8 space-y-6">
            <!-- Header -->
            <div class="flex items-center justify-between">
                <div class="space-y-1">
                    <h2
                        class="text-2xl font-black text-gray-900 tracking-tight"
                    >
                        Generate Report
                    </h2>
                    <p class="text-sm text-gray-500 font-medium">
                        {grant?.grant_code} • {grant?.title}
                    </p>
                </div>
                <button
                    on:click={handleClose}
                    class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-all"
                    aria-label="Close modal"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke-width="2.5"
                        stroke="currentColor"
                        class="w-5 h-5"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M6 18L18 6M6 6l12 12"
                        />
                    </svg>
                </button>
            </div>

            {#if error}
                <div
                    class="p-4 bg-rose-50 border border-rose-100 rounded-2xl flex items-center gap-3 text-rose-700 animate-in shake duration-500"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke-width="2"
                        stroke="currentColor"
                        class="w-5 h-5"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
                        />
                    </svg>
                    <span class="text-xs font-bold">{error}</span>
                </div>
            {/if}

            {#if !result}
                <div class="space-y-6">
                    <div class="space-y-2">
                        <h3
                            class="block text-xs font-black text-gray-400 uppercase tracking-widest ml-1"
                        >
                            Select Report Type
                        </h3>
                        {#if isLoadingOptions}
                            <div
                                class="h-14 bg-gray-50 rounded-2xl animate-pulse flex items-center px-6"
                            >
                                <span class="text-xs text-gray-400 font-bold"
                                    >Scanning project timeline...</span
                                >
                            </div>
                        {:else if options.length === 0}
                            <div
                                class="p-6 bg-gray-50 rounded-2xl text-center border border-dashed border-gray-200"
                            >
                                <p class="text-sm text-gray-500 font-medium">
                                    No valid reporting periods available yet.
                                </p>
                            </div>
                        {:else}
                            <div class="relative">
                                <select
                                    bind:value={selectedOption}
                                    class="w-full p-4 rounded-2xl border-2 border-gray-100 bg-white hover:border-gray-200 text-gray-700 font-bold text-sm appearance-none focus:outline-none focus:border-blue-600 transition-all cursor-pointer"
                                >
                                    {#each options as option}
                                        <option value={option.id}
                                            >{option.label}</option
                                        >
                                    {/each}
                                </select>
                                <div
                                    class="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400"
                                >
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke-width="2.5"
                                        stroke="currentColor"
                                        class="w-4 h-4"
                                    >
                                        <path
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                            d="M19.5 8.25l-7.5 7.5-7.5-7.5"
                                        />
                                    </svg>
                                </div>
                            </div>
                        {/if}
                    </div>

                    <button
                        class="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl font-black text-xs uppercase tracking-widest shadow-xl shadow-blue-200 hover:shadow-blue-300 transition-all flex items-center justify-center gap-3 disabled:opacity-50"
                        disabled={!selectedOption ||
                            isGenerating ||
                            isLoadingOptions}
                        on:click={handleGenerate}
                    >
                        {#if isGenerating}
                            <div
                                class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"
                            ></div>
                            <span
                                >Compiling verified data from milestones,
                                expenses, and effort records...</span
                            >
                        {:else}
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke-width="2.5"
                                stroke="currentColor"
                                class="w-4 h-4"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m.75 12l3 3m0 0l3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
                                />
                            </svg>
                            <span>Generate PDF</span>
                        {/if}
                    </button>
                </div>
            {:else}
                <!-- Success/Result View -->
                <div
                    class="space-y-8 py-4 animate-in fade-in slide-in-from-bottom-4 duration-500"
                >
                    <div
                        class="flex flex-col items-center text-center space-y-4"
                    >
                        <div
                            class="w-20 h-20 bg-emerald-50 rounded-[2rem] flex items-center justify-center text-emerald-600 shadow-inner"
                        >
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke-width="2.5"
                                stroke="currentColor"
                                class="w-10 h-10"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                            </svg>
                        </div>
                        <div>
                            <h3
                                class="text-xl font-black text-gray-900 tracking-tight"
                            >
                                Report Ready
                            </h3>
                            <p class="text-sm text-gray-500 font-medium mt-1">
                                {getOptionLabel(selectedOption)} has been successfully
                                compiled.
                            </p>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <a
                            href={result.preview_url}
                            target="_blank"
                            class="flex flex-col items-center justify-center p-6 rounded-3xl bg-gray-50 border border-gray-100 hover:bg-gray-100 transition-all group"
                        >
                            <div
                                class="w-10 h-10 rounded-xl bg-white border border-gray-100 flex items-center justify-center text-gray-400 group-hover:text-blue-600 transition-colors mb-3"
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke-width="2"
                                    stroke="currentColor"
                                    class="w-5 h-5"
                                >
                                    <path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
                                    />
                                    <path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                                    />
                                </svg>
                            </div>
                            <span
                                class="text-xs font-black text-gray-600 uppercase tracking-widest"
                                >Preview</span
                            >
                        </a>
                        <a
                            href={result.download_url}
                            class="flex flex-col items-center justify-center p-6 rounded-3xl bg-blue-600 text-white shadow-xl shadow-blue-200 hover:bg-blue-700 transition-all"
                        >
                            <div
                                class="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center mb-3"
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke-width="2.5"
                                    stroke="currentColor"
                                    class="w-5 h-5"
                                >
                                    <path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                                    />
                                </svg>
                            </div>
                            <span
                                class="text-xs font-black uppercase tracking-widest"
                                >Download</span
                            >
                        </a>
                    </div>

                    <div
                        class="p-4 bg-amber-50 rounded-2xl border border-amber-100/50"
                    >
                        <div class="flex gap-3">
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke-width="2"
                                stroke="currentColor"
                                class="w-5 h-5 text-amber-600 flex-shrink-0"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
                                />
                            </svg>
                            <p
                                class="text-[11px] font-bold text-amber-800 leading-relaxed italic"
                            >
                                “This report contains only system-verified data.
                                No manual edits were made.”
                            </p>
                        </div>
                    </div>
                </div>
            {/if}
        </div>
    </div>
</div>

<style>
    @keyframes shake {
        0%,
        100% {
            transform: translateX(0);
        }
        25% {
            transform: translateX(-4px);
        }
        75% {
            transform: translateX(4px);
        }
    }
    .animate-in {
        animation-fill-mode: both;
    }
</style>
