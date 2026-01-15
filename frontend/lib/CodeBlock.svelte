<script lang="ts">
    export let code: string;
    export let language: string = "solidity";

    // Simple syntax highlighting for Solidity
    function highlightSolidity(code: string): string {
        // Escape HTML first
        let html = code
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Comments
        html = html.replace(/(\/\/.*$)/gm, '<span class="comment">$1</span>');
        html = html.replace(
            /(\/\*[\s\S]*?\*\/)/g,
            '<span class="comment">$1</span>',
        );

        // Strings
        html = html.replace(/(".*?")/g, '<span class="string">$1</span>');

        // Keywords
        const keywords = [
            "pragma",
            "solidity",
            "contract",
            "interface",
            "library",
            "abstract",
            "function",
            "modifier",
            "event",
            "struct",
            "enum",
            "mapping",
            "public",
            "private",
            "internal",
            "external",
            "view",
            "pure",
            "payable",
            "memory",
            "storage",
            "calldata",
            "returns",
            "return",
            "if",
            "else",
            "for",
            "while",
            "do",
            "break",
            "continue",
            "import",
            "is",
            "new",
            "delete",
            "try",
            "catch",
            "revert",
            "require",
            "assert",
            "emit",
            "constructor",
            "receive",
            "fallback",
            "virtual",
            "override",
            "constant",
            "immutable",
            "indexed",
        ];

        keywords.forEach((keyword) => {
            const regex = new RegExp(`\\b(${keyword})\\b`, "g");
            html = html.replace(regex, '<span class="keyword">$1</span>');
        });

        // Types
        const types = [
            "address",
            "bool",
            "string",
            "bytes",
            "bytes32",
            "bytes4",
            "uint",
            "uint8",
            "uint16",
            "uint32",
            "uint64",
            "uint128",
            "uint256",
            "int",
            "int8",
            "int16",
            "int32",
            "int64",
            "int128",
            "int256",
        ];

        types.forEach((type) => {
            const regex = new RegExp(`\\b(${type})\\b`, "g");
            html = html.replace(regex, '<span class="type">$1</span>');
        });

        // Built-in globals
        const builtins = ["msg", "block", "tx", "abi", "this"];
        builtins.forEach((builtin) => {
            const regex = new RegExp(`\\b(${builtin})\\b`, "g");
            html = html.replace(regex, '<span class="builtin">$1</span>');
        });

        // Numbers
        html = html.replace(
            /\b(\d+(\.\d+)?)\b/g,
            '<span class="number">$1</span>',
        );
        html = html.replace(
            /\b(0x[a-fA-F0-9]+)\b/g,
            '<span class="number">$1</span>',
        );

        // Special values
        html = html.replace(
            /\b(true|false)\b/g,
            '<span class="boolean">$1</span>',
        );
        html = html.replace(
            /\b(ether|wei|gwei|seconds|minutes|hours|days|weeks)\b/g,
            '<span class="unit">$1</span>',
        );

        return html;
    }

    $: highlightedCode = highlightSolidity(code);
    $: lines = code.split("\n");
</script>

<div class="code-block">
    <div class="code-header">
        <span class="language-badge">{language}</span>
        <button
            class="copy-btn"
            on:click={() => navigator.clipboard.writeText(code)}
        >
            <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
            >
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path
                    d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
                ></path>
            </svg>
            Copy
        </button>
    </div>

    <div class="code-content">
        <div class="line-numbers">
            {#each lines as _, i}
                <span class="line-number">{i + 1}</span>
            {/each}
        </div>
        <pre><code class="language-{language}">{@html highlightedCode}</code
            ></pre>
    </div>
</div>

<style>
    .code-block {
        font-family: var(--font-mono);
        font-size: 0.875rem;
        background: var(--bg-code);
    }

    .code-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1rem;
        background: rgba(0, 0, 0, 0.3);
        border-bottom: 1px solid var(--border-color);
    }

    .language-badge {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--accent-cyan);
        font-weight: 600;
        padding: 0.25rem 0.5rem;
        background: rgba(6, 182, 212, 0.1);
        border-radius: 4px;
    }

    .copy-btn {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0.75rem;
        background: transparent;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        color: var(--text-muted);
        cursor: pointer;
        font-size: 0.75rem;
        font-family: var(--font-sans);
        transition: all var(--transition-fast);
    }

    .copy-btn:hover {
        background: var(--bg-card);
        color: var(--text-primary);
        border-color: var(--accent-purple);
    }

    .code-content {
        display: flex;
        overflow-x: auto;
        max-height: 600px;
        overflow-y: auto;
    }

    .line-numbers {
        display: flex;
        flex-direction: column;
        padding: 1rem 0;
        background: rgba(0, 0, 0, 0.2);
        border-right: 1px solid var(--border-color);
        user-select: none;
        position: sticky;
        left: 0;
        z-index: 1;
    }

    .line-number {
        padding: 0 1rem;
        text-align: right;
        color: var(--text-muted);
        font-size: 0.8rem;
        line-height: 1.5rem;
        min-width: 3rem;
    }

    pre {
        margin: 0;
        padding: 1rem;
        flex: 1;
        overflow-x: visible;
    }

    code {
        display: block;
        line-height: 1.5rem;
        white-space: pre;
    }

    /* Syntax highlighting colors */
    :global(.comment) {
        color: #6a737d;
        font-style: italic;
    }

    :global(.keyword) {
        color: #ff7b72;
    }

    :global(.type) {
        color: #79c0ff;
    }

    :global(.string) {
        color: #a5d6ff;
    }

    :global(.number) {
        color: #ffa657;
    }

    :global(.boolean) {
        color: #ff7b72;
    }

    :global(.builtin) {
        color: #d2a8ff;
    }

    :global(.unit) {
        color: #7ee787;
    }
</style>
