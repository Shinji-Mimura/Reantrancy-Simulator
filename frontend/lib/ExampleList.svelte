<script lang="ts">
    import { onMount, createEventDispatcher } from "svelte";
    import ExampleCard from "./ExampleCard.svelte";

    interface ExampleSummary {
        id: string;
        title: string;
        subtitle: string;
        description: string;
    }

    const dispatch = createEventDispatcher<{ select: string }>();

    let examples: ExampleSummary[] = [];
    let loading = true;
    let error = "";

    const API_BASE = "http://localhost:5000/api";

    onMount(async () => {
        try {
            const res = await fetch(`${API_BASE}/examples`);
            if (!res.ok) throw new Error("Failed to fetch examples");
            examples = await res.json();
            loading = false;
        } catch (e) {
            error =
                "Failed to load examples. Make sure the Flask backend is running.";
            loading = false;
        }
    });

    function handleSelect(id: string) {
        dispatch("select", id);
    }
</script>

<section class="examples-section">
    <h2 class="section-title">Types of Reentrancy</h2>

    {#if loading}
        <div class="loading-grid">
            {#each [1, 2, 3, 4, 5] as _}
                <div class="skeleton-card"></div>
            {/each}
        </div>
    {:else if error}
        <div class="error-message">
            <span class="error-icon"
                ><i class="fa-solid fa-triangle-exclamation"></i></span
            >
            <p>{error}</p>
            <button
                class="btn btn-secondary"
                on:click={() => location.reload()}
            >
                Retry
            </button>
        </div>
    {:else}
        <div class="examples-grid">
            {#each examples as example, i}
                <div
                    class="animate-fade-in"
                    style="animation-delay: {i * 100}ms"
                >
                    <ExampleCard
                        {example}
                        on:click={() => handleSelect(example.id)}
                    />
                </div>
            {/each}
        </div>
    {/if}
</section>

<style>
    .examples-section {
        margin-top: 2rem;
    }

    .section-title {
        margin-bottom: 2rem;
        text-align: center;
    }

    .examples-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 2rem;
    }

    .loading-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 2rem;
    }

    .skeleton-card {
        height: 200px;
        background: linear-gradient(
            90deg,
            var(--bg-card) 25%,
            var(--bg-secondary) 50%,
            var(--bg-card) 75%
        );
        background-size: 200% 100%;
        border-radius: var(--border-radius-lg);
        animation: shimmer 1.5s infinite;
    }

    .error-message {
        text-align: center;
        padding: 3rem;
        background: var(--bg-card);
        border-radius: var(--border-radius-lg);
        border: 1px solid var(--accent-red);
    }

    .error-icon {
        font-size: 2rem;
        display: block;
        margin-bottom: 1rem;
    }

    .error-message p {
        margin-bottom: 1rem;
        color: var(--text-secondary);
    }
</style>
