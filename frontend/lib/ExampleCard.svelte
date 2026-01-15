<script lang="ts">
    import { createEventDispatcher } from "svelte";

    interface ExampleSummary {
        id: string;
        title: string;
        subtitle: string;
        description: string;
    }

    export let example: ExampleSummary;

    const dispatch = createEventDispatcher();

    const icons: Record<string, string> = {
        "single-function": "fa-solid fa-rotate",
        "cross-function": "fa-solid fa-shuffle",
        "cross-contract": "fa-solid fa-cubes",
        "read-only": "fa-solid fa-eye",
        "cross-chain": "fa-solid fa-link",
    };

    const colors: Record<string, string> = {
        "single-function": "var(--accent-red)",
        "cross-function": "var(--accent-orange)",
        "cross-contract": "var(--accent-purple)",
        "read-only": "var(--accent-cyan)",
        "cross-chain": "var(--accent-pink)",
    };
</script>

<button class="card example-card" on:click={() => dispatch("click")}>
    <div class="card-header">
        <span
            class="icon"
            style="--accent-color: {colors[example.id] ||
                'var(--accent-primary)'}"
        >
            <i class={icons[example.id] || "fa-solid fa-shield-halved"}></i>
        </span>
        <span class="subtitle">{example.subtitle}</span>
    </div>

    <h3 class="title">{example.title}</h3>
    <p class="description">{example.description}</p>

    <div class="card-footer">
        <span class="learn-more">
            Explore
            <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
            >
                <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
        </span>
    </div>
</button>

<style>
    .example-card {
        display: flex;
        flex-direction: column;
        text-align: left;
        cursor: pointer;
        min-height: 200px;
        height: 100%;
        width: 100%;
        position: relative;
        overflow: hidden;
    }

    /* HTB-style accent line on top */
    .example-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--accent-primary);
        transform: scaleX(0);
        transition: transform var(--transition-normal);
    }

    .example-card:hover::before {
        transform: scaleX(1);
    }

    .card-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }

    .icon {
        font-size: 1.5rem;
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(159, 239, 0, 0.05);
        border-radius: 8px;
        border: 1px solid var(--accent-color);
        color: var(--accent-color);
        transition: all var(--transition-normal);
    }

    .example-card:hover .icon {
        background: rgba(159, 239, 0, 0.1);
        box-shadow: 0 0 15px rgba(159, 239, 0, 0.15);
    }

    .subtitle {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-secondary);
        font-weight: 600;
    }

    .title {
        margin-bottom: 0.75rem;
        transition: color var(--transition-fast);
    }

    .example-card:hover .title {
        color: var(--accent-primary);
    }

    .description {
        font-size: 0.875rem;
        line-height: 1.6;
        flex: 1;
    }

    .card-footer {
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border-color);
    }

    .learn-more {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--accent-primary);
        transition: all var(--transition-fast);
    }

    .example-card:hover .learn-more {
        gap: 0.75rem;
    }
</style>
