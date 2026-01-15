<script lang="ts">
    import { onMount, createEventDispatcher } from "svelte";
    import CodeBlock from "./CodeBlock.svelte";
    import AttackAnimation from "./AttackAnimation.svelte";

    export let exampleId: string;

    interface Example {
        id: string;
        title: string;
        subtitle: string;
        description: string;
        vulnerable_code: string;
        attack_code: string;
        fixed_code: string;
        attack_flow: string[];
    }

    const dispatch = createEventDispatcher();

    let example: Example | null = null;
    let loading = true;
    let error = "";
    let activeTab: "vulnerable" | "attack" | "fixed" | "animation" =
        "vulnerable";
    let activeSimulationStep = -1;

    function handleStepChange(event: CustomEvent<number>) {
        activeSimulationStep = event.detail;
    }

    // Reset when leaving simulation tab
    $: if (activeTab !== "animation") {
        activeSimulationStep = -1;
    }

    const API_BASE = "http://localhost:5000/api";

    onMount(async () => {
        try {
            const res = await fetch(`${API_BASE}/examples/${exampleId}`);
            if (!res.ok) throw new Error("Failed to fetch example");
            example = await res.json();
            loading = false;
        } catch (e) {
            error = "Failed to load example details.";
            loading = false;
        }
    });

    function goBack() {
        dispatch("back");
    }

    $: currentCode = example
        ? {
              vulnerable: example.vulnerable_code,
              attack: example.attack_code,
              fixed: example.fixed_code,
          }[activeTab]
        : "";
</script>

<div class="detail-page">
    <button class="back-button" on:click={goBack}>
        <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
        >
            <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        Back to examples
    </button>

    {#if loading}
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading example...</p>
        </div>
    {:else if error}
        <div class="error-message">
            <span class="error-icon"
                ><i class="fa-solid fa-triangle-exclamation"></i></span
            >
            <p>{error}</p>
        </div>
    {:else if example}
        <header class="detail-header">
            <span class="subtitle">{example.subtitle}</span>
            <h1>{example.title}</h1>
            <p class="description">{example.description}</p>
        </header>

        <div class="content-grid">
            <section class="code-section">
                <div class="tabs">
                    <button
                        class="tab"
                        class:active={activeTab === "vulnerable"}
                        class:danger={activeTab === "vulnerable"}
                        on:click={() => (activeTab = "vulnerable")}
                    >
                        <span class="tab-icon"
                            ><i class="fa-solid fa-triangle-exclamation"
                            ></i></span
                        >
                        Vulnerable Code
                    </button>
                    <button
                        class="tab"
                        class:active={activeTab === "attack"}
                        class:warning={activeTab === "attack"}
                        on:click={() => (activeTab = "attack")}
                    >
                        <span class="tab-icon"
                            ><i class="fa-solid fa-skull-crossbones"></i></span
                        >
                        Attack Contract
                    </button>
                    <button
                        class="tab"
                        class:active={activeTab === "fixed"}
                        class:success={activeTab === "fixed"}
                        on:click={() => (activeTab = "fixed")}
                    >
                        <span class="tab-icon"
                            ><i class="fa-solid fa-check"></i></span
                        >
                        Fixed Code
                    </button>
                    <button
                        class="tab"
                        class:active={activeTab === "animation"}
                        class:animation={activeTab === "animation"}
                        on:click={() => (activeTab = "animation")}
                    >
                        <span class="tab-icon"
                            ><i class="fa-solid fa-clapperboard"></i></span
                        >
                        Simulation
                    </button>
                </div>

                <div class="code-container">
                    {#if activeTab === "animation"}
                        <AttackAnimation
                            {exampleId}
                            attackFlow={example.attack_flow}
                            on:stepChange={handleStepChange}
                        />
                    {:else}
                        <CodeBlock code={currentCode} language="solidity" />
                    {/if}
                </div>
            </section>

            <aside class="attack-flow">
                <h3>
                    <span class="flow-icon"
                        ><i class="fa-solid fa-rotate"></i></span
                    >
                    Attack Flow
                </h3>
                <ol class="flow-list">
                    {#each example.attack_flow as step, i}
                        <li
                            class="flow-step"
                            class:active={activeSimulationStep === i}
                            class:completed={activeSimulationStep > i}
                            style="animation-delay: {i * 100}ms"
                        >
                            <span class="step-number">{i + 1}</span>
                            <span class="step-text">{step}</span>
                        </li>
                    {/each}
                </ol>
            </aside>
        </div>
    {/if}
</div>

<style>
    .detail-page {
        animation: fadeIn 0.4s ease;
    }

    .back-button {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.25rem;
        background: transparent;
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        color: var(--text-secondary);
        cursor: pointer;
        font-size: 0.875rem;
        font-weight: 500;
        transition: all var(--transition-normal);
        margin-bottom: 2rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .back-button:hover {
        border-color: var(--accent-primary);
        color: var(--accent-primary);
    }

    .detail-header {
        margin-bottom: 2rem;
    }

    .detail-header .subtitle {
        display: inline-block;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--accent-primary);
        font-weight: 700;
        margin-bottom: 0.75rem;
        padding: 0.25rem 0.75rem;
        background: rgba(159, 239, 0, 0.1);
        border: 1px solid rgba(159, 239, 0, 0.3);
        border-radius: 4px;
    }

    .detail-header h1 {
        margin-bottom: 1rem;
    }

    .description {
        font-size: 1.05rem;
        line-height: 1.8;
        max-width: 800px;
    }

    .content-grid {
        display: grid;
        grid-template-columns: 1fr 350px;
        gap: 2rem;
    }

    @media (max-width: 1024px) {
        .content-grid {
            grid-template-columns: 1fr;
        }
    }

    .tabs {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }

    .tab {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.875rem 1.5rem;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        color: var(--text-secondary);
        cursor: pointer;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        transition: all var(--transition-normal);
    }

    .tab:hover {
        border-color: var(--accent-primary);
        color: var(--text-primary);
    }

    .tab.active {
        color: #0b121f;
        border-color: transparent;
    }

    .tab.active.danger {
        background: var(--accent-primary);
    }

    .tab.active.warning {
        background: var(--accent-primary);
    }

    .tab.active.success {
        background: var(--accent-primary);
    }

    .tab.active.animation {
        background: var(--accent-primary);
    }

    .tab-icon {
        font-size: 1rem;
    }

    .code-container {
        background: var(--bg-code);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius-lg);
        overflow: hidden;
    }

    .attack-flow {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius-lg);
        padding: 1.5rem;
        height: fit-content;
        position: sticky;
        top: 100px;
    }

    .attack-flow h3 {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .flow-icon {
        font-size: 1.25rem;
    }

    .flow-list {
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .flow-step {
        display: flex;
        gap: 1rem;
        align-items: flex-start;
        animation: fadeIn 0.4s ease forwards;
        opacity: 0;
    }

    .step-number {
        flex-shrink: 0;
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--accent-primary);
        color: #0b121f;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
    }

    .step-text {
        font-size: 0.875rem;
        color: var(--text-secondary);
        line-height: 1.5;
        padding-top: 0.25rem;
        transition: color var(--transition-normal);
    }

    /* Active step highlighting */
    .flow-step.active {
        background: rgba(159, 239, 0, 0.1);
        border-radius: 6px;
        padding: 0.5rem;
        margin: -0.5rem;
        margin-bottom: 0.25rem;
        border-left: 3px solid var(--accent-primary);
    }

    .flow-step.active .step-number {
        background: var(--accent-primary);
        color: #0b121f;
        box-shadow: 0 0 15px rgba(159, 239, 0, 0.5);
        animation: pulse-glow 1s ease infinite;
    }

    .flow-step.active .step-text {
        color: var(--text-primary);
        font-weight: 500;
    }

    /* Completed step styling */
    .flow-step.completed .step-number {
        background: var(--accent-cyan);
        opacity: 0.7;
    }

    .flow-step.completed .step-text {
        opacity: 0.6;
    }

    @keyframes pulse-glow {
        0%,
        100% {
            box-shadow: 0 0 8px rgba(159, 239, 0, 0.4);
        }
        50% {
            box-shadow: 0 0 20px rgba(159, 239, 0, 0.7);
        }
    }

    .loading {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 4rem;
        gap: 1rem;
    }

    .spinner {
        width: 40px;
        height: 40px;
        border: 3px solid var(--border-color);
        border-top-color: var(--accent-primary);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
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
</style>
