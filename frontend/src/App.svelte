<script lang="ts">
  import Header from './lib/Header.svelte';
  import ExampleList from './lib/ExampleList.svelte';
  import ExampleDetail from './lib/ExampleDetail.svelte';
  
  let selectedExampleId: string | null = null;
  
  function selectExample(event: CustomEvent<string>) {
    selectedExampleId = event.detail;
  }
  
  function goBack() {
    selectedExampleId = null;
  }
</script>

<Header />

<main class="container">
  {#if selectedExampleId}
    <ExampleDetail exampleId={selectedExampleId} on:back={goBack} />
  {:else}
    <section class="hero">
      <h1>Reentrancy Attack Examples</h1>
      <p class="subtitle">
        Explore the different types of reentrancy vulnerabilities in smart contracts
        with interactive code examples and attack flows.
      </p>
    </section>
    
    <ExampleList on:select={selectExample} />
  {/if}
</main>

<footer>
  <div class="container">
    <p class="text-muted text-sm">
      Educational resource for smart contract security • Built with Flask + Svelte
    </p>
  </div>
</footer>

<style>
  main {
    flex: 1;
    padding: 2rem 0;
  }
  
  .hero {
    text-align: center;
    padding: 3rem 0;
    margin-bottom: 2rem;
  }
  
  .hero h1 {
    margin-bottom: 1rem;
  }
  
  .subtitle {
    font-size: 1.125rem;
    max-width: 600px;
    margin: 0 auto;
    color: var(--text-secondary);
  }
  
  footer {
    padding: 2rem 0;
    border-top: 1px solid var(--border-color);
    text-align: center;
  }
</style>
