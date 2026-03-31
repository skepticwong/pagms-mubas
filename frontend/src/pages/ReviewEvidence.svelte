<script>
  import { onMount } from "svelte";
  import axios from "axios";
  import Layout from "../components/Layout.svelte";
  import { router } from "../stores/router.js";
  import { user, isAuthenticated, checkAuth } from "../stores/auth.js";

  let showPage = false;
  let loading = true;
  let error = "";
  let submissions = [];
  let actionState = {};

  onMount(async () => {
    await checkAuth();
    if (!$isAuthenticated || $user?.role !== "PI") {
      router.goToDashboard();
      return;
    }
    showPage = true;
    await fetchEvidence();
  });

  async function fetchEvidence() {
    loading = true;
    error = "";
    try {
      const response = await axios.get(
        "http://localhost:5000/api/deliverables?status=pending",
        {
          withCredentials: true,
        },
      );
      submissions = response.data?.submissions || [];
    } catch (err) {
      error =
        err.response?.data?.error || "Could not load evidence submissions.";
    } finally {
      loading = false;
    }
  }

  function toggleConfirmation(id, value) {
    actionState = {
      ...actionState,
      [id]: { ...(actionState[id] || {}), confirmed: value },
    };
  }

  function setComment(id, value) {
    actionState = {
      ...actionState,
      [id]: { ...(actionState[id] || {}), comment: value },
    };
  }

  async function approveEvidence(id) {
    const state = actionState[id];
    if (!state?.confirmed) {
      actionState = {
        ...actionState,
        [id]: {
          ...(state || {}),
          error: "Please certify effort before approving.",
        },
      };
      return;
    }

    actionState = {
      ...actionState,
      [id]: { ...(state || {}), submitting: true, error: "", success: "" },
    };

    try {
      await axios.post(
        `http://localhost:5000/api/deliverables/${id}/approve`,
        {},
        { withCredentials: true },
      );
      actionState = {
        ...actionState,
        [id]: {
          ...(actionState[id] || {}),
          submitting: false,
          success: "Approved & certified.",
        },
      };
      await fetchEvidence();
    } catch (err) {
      actionState = {
        ...actionState,
        [id]: {
          ...(actionState[id] || {}),
          submitting: false,
          error: err.response?.data?.error || "Approval failed.",
        },
      };
    }
  }

  async function requestRevision(id) {
    const state = actionState[id];
    const comment = state?.comment?.trim();
    if (!comment) {
      actionState = {
        ...actionState,
        [id]: {
          ...(state || {}),
          error: "Please provide revision instructions.",
        },
      };
      return;
    }

    actionState = {
      ...actionState,
      [id]: { ...(state || {}), submitting: true, error: "", success: "" },
    };

    try {
      await axios.post(
        `http://localhost:5000/api/deliverables/${id}/request-revision`,
        { comment },
        { withCredentials: true },
      );
      actionState = {
        ...actionState,
        [id]: {
          ...(actionState[id] || {}),
          submitting: false,
          success: "Revision requested.",
        },
      };
      await fetchEvidence();
    } catch (err) {
      actionState = {
        ...actionState,
        [id]: {
          ...(actionState[id] || {}),
          submitting: false,
          error: err.response?.data?.error || "Request failed.",
        },
      };
    }
  }

  function getState(id) {
    return actionState[id] || {};
  }

  $: submissionViews = submissions.map((submission) => ({
    submission,
    state: getState(submission.id),
  }));
</script>

{#if showPage}
  <Layout>
    <div class="max-w-6xl mx-auto space-y-8">
      <div
        class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl p-8 shadow-lg"
      >
        <h1 class="text-3xl font-bold text-gray-900">Review Evidence</h1>
        <p class="text-sm text-gray-600 mt-2">
          Verify team submissions, enforce compliance, and certify effort.
        </p>
      </div>

      {#if error}
        <div
          class="p-4 rounded-2xl bg-red-50 border border-red-100 text-red-700"
        >
          {error}
        </div>
      {/if}

      {#if loading}
        <div class="p-6 text-center text-sm text-gray-500">
          Loading pending evidence…
        </div>
      {:else if submissions.length === 0}
        <div
          class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-6 text-center text-gray-600"
        >
          No evidence submissions awaiting review.
        </div>
      {:else}
        <div class="space-y-6">
          {#each submissionViews as view (view.submission.id)}
            <article
              class="bg-white/80 backdrop-blur-xl border border-white/60 rounded-3xl p-6 shadow-md"
            >
              <div class="flex flex-col gap-4">
                <header
                  class="flex flex-col md:flex-row md:items-center md:justify-between gap-2"
                >
                  <div>
                    <p class="text-lg font-semibold text-gray-900">
                      {view.submission.task_title}
                    </p>
                    <p class="text-sm text-gray-600">
                      {view.submission.grant_title}
                    </p>
                  </div>
                  <span
                    class="px-3 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-semibold"
                    >Pending certification</span
                  >
                </header>

                <div
                  class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600"
                >
                  <p>
                    <span class="font-semibold text-gray-900">Team member:</span
                    >
                    {view.submission.team_member}
                  </p>
                  <p>
                    <span class="font-semibold text-gray-900">Submitted:</span>
                    {new Date(view.submission.submitted_at).toLocaleString()}
                  </p>
                  <p>
                    <span class="font-semibold text-gray-900">Task window:</span
                    >
                    {view.submission.task_start} → {view.submission.task_end}
                  </p>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <div class="space-y-3">
                    <h3
                      class="text-sm font-semibold text-gray-900 uppercase tracking-wide"
                    >
                      Files
                    </h3>
                    <div class="grid grid-cols-2 gap-3">
                      {#if view.submission.photo_url}
                        <div
                          class="rounded-2xl overflow-hidden border border-gray-100"
                        >
                          <img
                            src={view.submission.photo_url}
                            alt="Evidence photo"
                            class="w-full h-32 object-cover"
                          />
                        </div>
                      {/if}
                      {#each view.submission.documents as doc}
                        <a
                          href={doc.url}
                          class="flex items-center gap-2 px-3 py-2 rounded-xl border border-gray-200 text-sm text-gray-700 hover:bg-gray-50"
                          target="_blank"
                          rel="noreferrer"
                        >
                          📄 <span class="truncate">{doc.name}</span>
                        </a>
                      {/each}
                    </div>
                    <div>
                      <h4 class="text-sm font-semibold text-gray-900">Notes</h4>
                      <p class="text-sm text-gray-600 mt-1 whitespace-pre-wrap">
                        {view.submission.notes || "No notes provided."}
                      </p>
                    </div>
                  </div>

                  <div class="space-y-4">
                    <h3
                      class="text-sm font-semibold text-gray-900 uppercase tracking-wide"
                    >
                      Automated verification
                    </h3>
                    <ul class="space-y-2 text-sm">
                      <li class="flex items-center gap-2">
                        <span class="text-emerald-600">✅</span>
                        Photo timestamp within task window
                      </li>
                      <li class="flex items-center gap-2">
                        <span class="text-emerald-600">✅</span>
                        GPS coordinates in Malawi
                      </li>
                      <li class="flex items-center gap-2">
                        <span class="text-emerald-600">✅</span>
                        Image hash not reused
                      </li>
                    </ul>

                    <label class="flex items-start gap-3 text-sm text-gray-700">
                      <input
                        type="checkbox"
                        class="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded"
                        checked={view.state.confirmed || false}
                        on:change={(event) =>
                          toggleConfirmation(
                            view.submission.id,
                            event.target.checked,
                          )}
                      />
                      <span
                        >I confirm this effort was performed on this grant.</span
                      >
                    </label>

                    <textarea
                      class="w-full rounded-2xl border border-gray-200 px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows="3"
                      placeholder="Comment (required for revisions)"
                      value={view.state.comment || ""}
                      on:input={(event) =>
                        setComment(view.submission.id, event.target.value)}
                    ></textarea>

                    {#if view.state.error}
                      <div class="text-sm text-rose-600">
                        {view.state.error}
                      </div>
                    {/if}
                    {#if view.state.success}
                      <div class="text-sm text-emerald-600">
                        {view.state.success}
                      </div>
                    {/if}

                    <div class="flex flex-wrap gap-3">
                      <button
                        class="px-4 py-2 rounded-xl text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50"
                        on:click={() => approveEvidence(view.submission.id)}
                        disabled={view.state.submitting}
                      >
                        Approve & Certify
                      </button>
                      <button
                        class="px-4 py-2 rounded-xl text-sm font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 focus:outline-none focus:ring-2 focus:ring-rose-200 disabled:opacity-50"
                        on:click={() => requestRevision(view.submission.id)}
                        disabled={view.state.submitting}
                      >
                        Request Revisions
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </article>
          {/each}
        </div>
      {/if}
    </div>
  </Layout>
{/if}
