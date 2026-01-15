<script lang="ts">
</script>

<header>
    <div class="container flex items-center justify-between">
        <div class="logo">
            <span class="logo-icon"
                ><i class="fa-solid fa-shield-halved"></i></span
            >
            <span class="logo-text">Reentrancy Lab</span>
        </div>
        <nav>
            <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                class="nav-link"
            >
                <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                >
                    <path
                        d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"
                    />
                </svg>
            </a>
        </nav>
    </div>
</header>

<style>
    header {
        background: rgba(11, 18, 31, 0.95);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border-color);
        position: sticky;
        top: 0;
        z-index: 100;
        padding: 1rem 0;
    }

    .logo {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .logo-icon {
        font-size: 1.5rem;
    }

    .logo-text {
        font-size: 1.25rem;
        font-weight: 700;
        background: linear-gradient(135deg, #9fef00 0%, #00b8d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
    }

    nav {
        display: flex;
        gap: 1rem;
    }

    .nav-link {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: 8px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        color: var(--text-secondary);
        transition: all var(--transition-normal);
    }

    .nav-link:hover {
        border-color: var(--accent-primary);
        color: var(--accent-primary);
        box-shadow: 0 0 15px rgba(159, 239, 0, 0.2);
    }
</style>
