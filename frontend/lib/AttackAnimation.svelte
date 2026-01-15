<script lang="ts">
    import { onMount, onDestroy, createEventDispatcher } from "svelte";

    export let attackFlow: string[] = [];
    export let exampleId: string = "";

    const dispatch = createEventDispatcher<{ stepChange: number }>();

    let currentStep = 0;
    let lastAppliedStep = -1;
    let isPlaying = false;
    let animationInterval: ReturnType<typeof setInterval> | null = null;
    let speed = 2000; // ms per step

    // Derive attack flow index from last applied step
    $: {
        const steps =
            simulationSteps[exampleId] || simulationSteps["single-function"];
        if (lastAppliedStep >= 0 && lastAppliedStep < steps.length) {
            const flowIndex =
                steps[lastAppliedStep].attackFlowIndex ?? lastAppliedStep;
            dispatch("stepChange", flowIndex);
        } else {
            dispatch("stepChange", -1);
        }
    }

    // Simulation data for each example type
    interface SimulationState {
        attackerBalance: number;
        contractBalance: number;
        attackerDeposit: number;
        callStack: string[];
        logs: string[];
        // LP token tracking (for read-only example)
        attackerLP?: number;
        lpTotalSupply?: number;
        pricePerLP?: number;
        // Cross-function specific
        attacker2Balance?: number; // Attacker2's balance IN the vault
        attacker2ETH?: number; // Attacker2's actual ETH balance
        activeArrow?: string; // "attacker-vault" | "vault-attacker" | "attacker-attacker2" | "attacker2-attacker"
    }

    const initialStates: Record<string, SimulationState> = {
        "single-function": {
            attackerBalance: 1,
            contractBalance: 10,
            attackerDeposit: 1,
            callStack: [],
            logs: [],
        },
        "cross-function": {
            attackerBalance: 1, // Attacker's initial ETH to deposit
            contractBalance: 10, // Vault has 10 ETH from other users
            attackerDeposit: 0, // Attacker's balance IN the vault
            callStack: [],
            logs: [],
            attacker2Balance: 0, // Attacker2's balance IN the vault
            attacker2ETH: 0, // Attacker2's actual ETH
            activeArrow: "",
        },
        "cross-contract": {
            attackerBalance: 2,
            contractBalance: 10,
            attackerDeposit: 2,
            callStack: [],
            logs: [],
        },
        "read-only": {
            attackerBalance: 10,
            contractBalance: 0,
            attackerDeposit: 0,
            callStack: [],
            logs: [],
            attackerLP: 0,
            lpTotalSupply: 0,
            pricePerLP: 1.0,
        },
        "cross-chain": {
            attackerBalance: 0, // Token ID on Chain A (0 = none, 1 = owns #0)
            contractBalance: 0, // Token ID on Chain B (0 = none, 1 = owns #0)
            attackerDeposit: 0, // tokenIds counter value
            callStack: [],
            logs: [],
        },
    };

    // Simulation steps for each example
    // attackFlowIndex maps simulation step to corresponding attack_flow index in backend
    const simulationSteps: Record<
        string,
        Array<
            Partial<SimulationState> & {
                highlight?: string;
                attackFlowIndex?: number;
            }
        >
    > = {
        "single-function": [
            // Backend has 9 attack_flow steps
            {
                attackerBalance: 0,
                contractBalance: 11,
                attackerDeposit: 1,
                callStack: ["deposit()"],
                logs: ["Attacker → Bank: deposit(1 ETH)"],
                highlight: "deposit",
                attackFlowIndex: 0, // "Attacker deposits 1 ETH into VulnerableBank"
            },
            {
                callStack: ["withdraw()"],
                logs: ["Attacker → Bank: withdraw()"],
                highlight: "withdraw",
                attackFlowIndex: 1, // "Attacker calls withdraw()"
            },
            {
                logs: ["Bank: require(balance > 0) [PASS]"],
                highlight: "check",
                attackFlowIndex: 2, // "Bank checks balance (1 ETH) [PASS]"
            },
            {
                attackerBalance: 1,
                contractBalance: 10,
                callStack: ["withdraw()", "receive()"],
                logs: [
                    "Bank → Attacker: send(1 ETH)",
                    "Attacker.receive() triggered!",
                ],
                highlight: "callback",
                attackFlowIndex: 3, // "Bank sends 1 ETH to Attacker → triggers receive()"
            },
            {
                callStack: ["withdraw()", "receive()", "withdraw()"],
                logs: ["[REENTER] withdraw()"],
                highlight: "reenter",
                attackFlowIndex: 4, // "receive() calls withdraw() again (REENTER)"
            },
            {
                logs: ["Bank: require(balance > 0) [PASS] (still 1!)"],
                highlight: "check",
                attackFlowIndex: 5, // "Bank checks balance (still 1 ETH!) [PASS]"
            },
            {
                attackerBalance: 2,
                contractBalance: 9,
                logs: ["Bank → Attacker: send(1 ETH)"],
                highlight: "drain",
                attackFlowIndex: 6, // "Bank sends another 1 ETH..."
            },
            {
                attackerBalance: 3,
                contractBalance: 8,
                logs: ["... repeating ..."],
                highlight: "drain",
                attackFlowIndex: 7, // "Loop continues until bank is drained"
            },
            {
                attackerBalance: 10,
                contractBalance: 1,
                logs: ["Bank: balance[attacker] = 0 (too late!)"],
                highlight: "late",
                attackFlowIndex: 8, // "Finally, balances[attacker] = 0 (too late!)"
            },
            {
                attackerBalance: 11,
                contractBalance: 0,
                callStack: [],
                logs: ["[SUCCESS] Attack complete! Drained 10 ETH"],
                highlight: "complete",
                attackFlowIndex: 8, // Keep same as last step
            },
        ],
        "cross-function": [
            // Backend has 10 attack_flow steps
            {
                attackerBalance: 1,
                contractBalance: 10,
                attackerDeposit: 0,
                attacker2Balance: 0,
                attacker2ETH: 0,
                callStack: [],
                logs: ["Attacker has 1 ETH, Vault has 10 ETH from users"],
                highlight: "setup",
                activeArrow: "",
                attackFlowIndex: 0, // "Vault has 10 ETH from users, Attacker deposits 1 ETH"
            },
            {
                attackerBalance: 0,
                contractBalance: 11,
                attackerDeposit: 1,
                attacker2Balance: 0,
                callStack: ["deposit()"],
                logs: ["Attacker deposits 1 ETH → Vault balance = 1"],
                highlight: "deposit",
                activeArrow: "attacker-vault",
                attackFlowIndex: 0, // Same step
            },
            {
                callStack: ["withdraw()"],
                logs: ["Attacker calls withdraw() - has nonReentrant [PASS]"],
                highlight: "withdraw",
                activeArrow: "attacker-vault",
                attackFlowIndex: 1, // "Attacker calls withdraw() - has nonReentrant [PASS]"
            },
            {
                attackerBalance: 1,
                contractBalance: 10,
                attackerDeposit: 1,
                callStack: ["withdraw()", "receive()"],
                logs: ["withdraw() sends 1 ETH → Attacker.receive()"],
                highlight: "callback",
                activeArrow: "vault-attacker",
                attackFlowIndex: 2, // "withdraw() sends 1 ETH → triggers Attacker.receive()"
            },
            {
                callStack: ["withdraw()", "receive()", "transfer()"],
                logs: [
                    "[REENTER] Inside receive(): call transfer(attacker2, 1 ETH)",
                ],
                highlight: "reenter",
                activeArrow: "attacker-vault",
                attackFlowIndex: 3, // "Inside receive(): call transfer(attacker2, 1 ETH)"
            },
            {
                logs: ["transfer() has NO nonReentrant — bypasses guard!"],
                highlight: "exploit",
                activeArrow: "",
                attackFlowIndex: 4, // "transfer() has NO nonReentrant — bypasses guard!"
            },
            {
                attackerBalance: 1,
                attackerDeposit: 0,
                attacker2Balance: 1,
                logs: [
                    "Vault.transfer(): balance[attacker] → balance[attacker2]",
                ],
                highlight: "exploit",
                activeArrow: "attacker-attacker2",
                attackFlowIndex: 5, // "transfer() checks balance: still 1 ETH (not zeroed yet!)"
            },
            {
                attackerDeposit: 0,
                callStack: ["withdraw()"],
                logs: [
                    "withdraw() finishes, sets balance = 0 (already empty!)",
                ],
                highlight: "late",
                activeArrow: "",
                attackFlowIndex: 7, // "withdraw() finishes, sets balance to 0 (already empty!)"
            },
            {
                attackerBalance: 1,
                attackerDeposit: 1,
                attacker2Balance: 0,
                logs: ["Attacker2.sendBack() → Attacker vault balance = 1"],
                highlight: "state",
                activeArrow: "attacker2-attacker",
                attackFlowIndex: 6, // "Balance moved to Attacker2, then sent back to Attacker"
            },
            {
                attackerBalance: 1,
                attackerDeposit: 1,
                contractBalance: 10,
                callStack: ["withdraw()"],
                logs: ["Loop: deposit not needed! withdraw() again..."],
                highlight: "drain",
                activeArrow: "attacker-vault",
                attackFlowIndex: 8, // "Loop repeats: withdraw → transfer → repeat"
            },
            {
                attackerBalance: 2,
                attackerDeposit: 1,
                contractBalance: 9,
                attacker2Balance: 0,
                logs: ["withdraw() sends 1 ETH → Attacker.receive()"],
                highlight: "drain",
                activeArrow: "vault-attacker",
                attackFlowIndex: 8,
            },
            {
                attackerBalance: 2,
                attackerDeposit: 0,
                attacker2Balance: 1,
                logs: ["transfer() to Attacker2 during callback"],
                highlight: "drain",
                activeArrow: "attacker-attacker2",
                attackFlowIndex: 8,
            },
            {
                attackerBalance: 2,
                attackerDeposit: 1,
                attacker2Balance: 0,
                logs: ["Attacker2 sends vault balance back"],
                highlight: "drain",
                activeArrow: "attacker2-attacker",
                attackFlowIndex: 8,
            },
            {
                attackerBalance: 6,
                contractBalance: 5,
                logs: ["... loop continues draining ..."],
                highlight: "drain",
                activeArrow: "",
                attackFlowIndex: 8,
            },
            {
                attackerBalance: 11,
                contractBalance: 0,
                attackerDeposit: 0,
                attacker2Balance: 0,
                callStack: [],
                logs: ["[SUCCESS] Vault DRAINED: 10 ETH -> 0 ETH!"],
                highlight: "complete",
                activeArrow: "",
                attackFlowIndex: 9, // "Result: Vault drained from 10 ETH to 0 ETH!"
            },
            {
                logs: ["[CRITICAL] Partial protection = NO protection!"],
                highlight: "complete",
                activeArrow: "",
                attackFlowIndex: 9,
            },
        ],
        "cross-contract": [
            // Backend has 9 attack_flow steps - matches exactly!
            {
                attackerBalance: 0,
                contractBalance: 12,
                attackerDeposit: 2,
                callStack: ["vault.deposit()"],
                logs: ["Attacker deposits 2 ETH to Vault"],
                highlight: "deposit",
                attackFlowIndex: 0, // "Attacker deposits 2 ETH into Vault"
            },
            {
                logs: ["Ledger: balances[attacker] = 2 ETH"],
                highlight: "state",
                attackFlowIndex: 1, // "Ledger records: balances[attacker] = 2 ETH"
            },
            {
                callStack: ["vault.withdraw()"],
                logs: ["Attacker calls vault.withdraw()"],
                highlight: "withdraw",
                attackFlowIndex: 2, // "Attacker calls vault.withdraw()"
            },
            {
                attackerBalance: 2,
                contractBalance: 10,
                callStack: ["vault.withdraw()", "receive()"],
                logs: ["Vault sends 2 ETH → receive()"],
                highlight: "callback",
                attackFlowIndex: 3, // "Vault sends 2 ETH → triggers receive()"
            },
            {
                callStack: [
                    "vault.withdraw()",
                    "receive()",
                    "lending.borrow()",
                ],
                logs: ["[REENTER] Inside receive: lending.borrow(1 ETH)"],
                highlight: "reenter",
                attackFlowIndex: 4, // "Inside receive(), call lending.borrow(1 ETH)"
            },
            {
                logs: ["Lending checks Ledger: 2 ETH collateral [PASS]"],
                highlight: "exploit",
                attackFlowIndex: 5, // "Lending checks ledger: collateral = 2 ETH [PASS]"
            },
            {
                attackerBalance: 3,
                contractBalance: 9,
                logs: ["Lending sends 1 ETH loan"],
                highlight: "drain",
                attackFlowIndex: 6, // "Lending sends 1 ETH loan"
            },
            {
                callStack: ["vault.withdraw()"],
                logs: ["vault.withdraw() zeros ledger"],
                highlight: "late",
                attackFlowIndex: 7, // "vault.withdraw() continues, zeros balance"
            },
            {
                callStack: [],
                logs: ["[SUCCESS] Got: 2 ETH + 1 ETH loan = 3 ETH"],
                highlight: "complete",
                attackFlowIndex: 8, // "Attacker received: 2 ETH + 1 ETH loan = 3 ETH!"
            },
        ],
        "read-only": [
            // Backend has 9 attack_flow steps, simulation has 17
            {
                attackerBalance: 0,
                contractBalance: 10,
                attackerDeposit: 0,
                attackerLP: 10,
                lpTotalSupply: 10,
                pricePerLP: 1.0,
                callStack: ["addLiquidity(10 ETH)"],
                logs: ["Attacker deposits 10 ETH → gets 10 LP tokens"],
                highlight: "deposit",
                attackFlowIndex: 0, // "Attacker adds liquidity → gets LP tokens"
            },
            {
                callStack: [],
                logs: ["Pool state: 10 ETH, totalSupply = 10 LP"],
                highlight: "state",
                attackFlowIndex: 0,
            },
            {
                attackerLP: 9,
                logs: ["Attacker puts 1 LP as collateral in Lending"],
                highlight: "deposit",
                attackFlowIndex: 1, // "Attacker deposits some LP as collateral in Lending"
            },
            {
                logs: ["Attacker now holds: 0 ETH + 9 LP (1 LP locked)"],
                highlight: "state",
                attackFlowIndex: 1,
            },
            {
                logs: ["Normal price: 10 ETH / 10 LP = 1.0 per LP"],
                highlight: "check",
                attackFlowIndex: 1,
            },
            {
                callStack: ["removeLiquidity(9 LP)"],
                logs: ["Attacker calls removeLiquidity(9 LP)"],
                highlight: "withdraw",
                attackFlowIndex: 2, // "Attacker calls removeLiquidity()"
            },
            {
                attackerLP: 0,
                lpTotalSupply: 1,
                logs: ["Pool BURNS 9 LP → totalSupply: 10 → 1"],
                highlight: "state",
                attackFlowIndex: 3, // "Pool BURNS LP tokens (totalSupply reduced)"
            },
            {
                attackerBalance: 9,
                contractBalance: 1,
                callStack: ["removeLiquidity()", "receive()"],
                logs: ["Pool sends 9 ETH → triggers receive()"],
                highlight: "callback",
                attackFlowIndex: 4, // "Pool sends ETH → triggers receive() callback"
            },
            {
                pricePerLP: 10.0,
                logs: ["[WARN] Pool.ethBalance still 10! (not updated yet)"],
                highlight: "exploit",
                attackFlowIndex: 5, // "ethBalance NOT YET reduced!"
            },
            {
                logs: ["get_virtual_price() = 10 ETH / 1 LP = 10.0 !!!"],
                highlight: "exploit",
                attackFlowIndex: 6, // "get_virtual_price() = D/totalSupply = HIGH/LOW = INFLATED!"
            },
            {
                logs: ["Attacker's 1 LP collateral now valued at 10 ETH!"],
                highlight: "exploit",
                attackFlowIndex: 6,
            },
            {
                logs: ["Lending requires 2x collateral → can borrow 5 ETH"],
                highlight: "exploit",
                attackFlowIndex: 6,
            },
            {
                callStack: [
                    "removeLiquidity()",
                    "receive()",
                    "lending.borrow(5)",
                ],
                logs: [
                    "↪ In callback: borrow 5 ETH (max with 10 ETH collateral)",
                ],
                highlight: "reenter",
                attackFlowIndex: 7, // "Attacker borrows using inflated collateral value"
            },
            {
                attackerBalance: 14,
                contractBalance: 1,
                logs: ["Lending sends 5 ETH based on inflated value!"],
                highlight: "drain",
                attackFlowIndex: 7,
            },
            {
                callStack: [],
                pricePerLP: 1.0,
                logs: ["removeLiquidity() finishes, ethBalance updated"],
                highlight: "late",
                attackFlowIndex: 8, // "removeLiquidity() finishes, price returns to normal (too late)"
            },
            {
                logs: ["Price returns to normal: 1 ETH / 1 LP = 1.0"],
                highlight: "state",
                attackFlowIndex: 8,
            },
            {
                logs: [
                    "[SUCCESS] PROFIT: Started 10 ETH -> Ended 14 ETH (+4 ETH!)",
                ],
                highlight: "complete",
                attackFlowIndex: 8,
            },
        ],
        "cross-chain": [
            // Backend has 10 attack_flow steps (indices 0-9)
            {
                attackerBalance: 0,
                contractBalance: 0,
                attackerDeposit: 0,
                callStack: [],
                logs: ["CrossChainWarriors NFT deployed on Chain A & B"],
                highlight: "setup",
                attackFlowIndex: 0, // "Attacker contract calls mint() on Chain A"
            },
            {
                callStack: ["attack()"],
                logs: ["Attacker contract calls attack()"],
                highlight: "setup",
                attackFlowIndex: 0,
            },
            {
                callStack: ["attack()", "nft.mint()"],
                logs: ["attack() calls nft.mint(attackerContract)"],
                highlight: "withdraw",
                attackFlowIndex: 0,
            },
            {
                attackerDeposit: 0,
                logs: ["mint(): tokenIds = 0, will mint token #0"],
                highlight: "state",
                attackFlowIndex: 1, // "_safeMint() mints token ID #0 to attacker"
            },
            {
                callStack: ["attack()", "nft.mint()", "_safeMint()"],
                logs: ["_safeMint() mints token #0 to attacker contract"],
                highlight: "callback",
                attackFlowIndex: 1,
            },
            {
                callStack: [
                    "attack()",
                    "nft.mint()",
                    "_safeMint()",
                    "onERC721Received()",
                ],
                logs: ["_safeMint() calls onERC721Received() on attacker!"],
                highlight: "callback",
                attackFlowIndex: 2, // "_safeMint() calls onERC721Received() on attacker contract"
            },
            {
                logs: ["[WARN] tokenIds++ has NOT executed yet! Still = 0"],
                highlight: "exploit",
                attackFlowIndex: 3, // "tokenIds is STILL 0 (not incremented yet!)"
            },
            {
                callStack: [
                    "nft.mint()",
                    "_safeMint()",
                    "onERC721Received()",
                    "crossChainTransfer()",
                ],
                logs: [
                    "[REENTER] Attacker calls crossChainTransfer(0, accomplice, chainB)",
                ],
                highlight: "reenter",
                attackFlowIndex: 4, // "Inside callback: call crossChainTransfer(0, accomplice, chainB)"
            },
            {
                contractBalance: 1,
                logs: ["Token #0 BURNED on Chain A, event emitted for Chain B"],
                highlight: "drain",
                attackFlowIndex: 5, // "Token #0 is BURNED, event emitted for bridge validators"
            },
            {
                logs: [
                    "[BRIDGE] Token #0 will be minted to accomplice on Chain B",
                ],
                highlight: "state",
                attackFlowIndex: 5,
            },
            {
                callStack: [
                    "nft.mint()",
                    "_safeMint()",
                    "onERC721Received()",
                    "nft.mint()",
                ],
                logs: ["[REENTER] Attacker calls mint() AGAIN inside callback"],
                highlight: "reenter",
                attackFlowIndex: 6, // "Still inside callback: call mint() again"
            },
            {
                logs: [
                    "Second mint(): tokenIds STILL = 0! Minting another #0!",
                ],
                highlight: "exploit",
                attackFlowIndex: 7, // "mint() creates ANOTHER token #0 (tokenIds still = 0)"
            },
            {
                attackerBalance: 1,
                logs: ["Token #0 minted AGAIN to attacker's owner on Chain A"],
                highlight: "drain",
                attackFlowIndex: 7,
            },
            {
                callStack: ["nft.mint()"],
                attackerDeposit: 1,
                logs: ["Original mint() finally: tokenIds++ → now 1"],
                highlight: "late",
                attackFlowIndex: 8, // "Original mint() finally increments tokenIds to 1"
            },
            {
                callStack: [],
                attackerDeposit: 2,
                logs: ["Second mint() also: tokenIds++ → now 2"],
                highlight: "late",
                attackFlowIndex: 8,
            },
            {
                logs: ["[SUCCESS] EXPLOIT COMPLETE:"],
                highlight: "complete",
                attackFlowIndex: 9, // "Result: Token #0 on Chain A + Token #0 on Chain B = DUPLICATE!"
            },
            {
                logs: ["   Token #0 on Chain A: [OK] Attacker owns it"],
                highlight: "complete",
                attackFlowIndex: 9,
            },
            {
                logs: ["   Token #0 on Chain B: [OK] Accomplice owns it"],
                highlight: "complete",
                attackFlowIndex: 9,
            },
            {
                logs: [
                    "[CRITICAL] SAME NFT EXISTS ON BOTH CHAINS = DUPLICATED!",
                ],
                highlight: "complete",
                attackFlowIndex: 9,
            },
        ],
    };

    let state: SimulationState = {
        ...(initialStates[exampleId] || initialStates["single-function"]),
    };

    function resetSimulation() {
        currentStep = 0;
        lastAppliedStep = -1;
        state = {
            ...(initialStates[exampleId] || initialStates["single-function"]),
        };
        state.callStack = [];
        state.logs = [];
    }

    function applyStep(stepIndex: number) {
        const steps =
            simulationSteps[exampleId] || simulationSteps["single-function"];
        if (stepIndex >= steps.length) return;

        const step = steps[stepIndex];
        if (step.attackerBalance !== undefined)
            state.attackerBalance = step.attackerBalance;
        if (step.contractBalance !== undefined)
            state.contractBalance = step.contractBalance;
        if (step.attackerDeposit !== undefined)
            state.attackerDeposit = step.attackerDeposit;
        if (step.attackerLP !== undefined) state.attackerLP = step.attackerLP;
        if (step.lpTotalSupply !== undefined)
            state.lpTotalSupply = step.lpTotalSupply;
        if (step.pricePerLP !== undefined) state.pricePerLP = step.pricePerLP;
        if (step.attacker2Balance !== undefined)
            state.attacker2Balance = step.attacker2Balance;
        if (step.attacker2ETH !== undefined)
            state.attacker2ETH = step.attacker2ETH;
        if (step.activeArrow !== undefined)
            state.activeArrow = step.activeArrow;
        if (step.callStack) state.callStack = [...step.callStack];
        if (step.logs) state.logs = [...state.logs, ...step.logs].slice(-6);
        lastAppliedStep = stepIndex;
    }

    function nextStep() {
        const steps =
            simulationSteps[exampleId] || simulationSteps["single-function"];
        if (currentStep < steps.length) {
            applyStep(currentStep);
            currentStep++;
        } else {
            stopAnimation();
        }
    }

    function prevStep() {
        if (currentStep > 0) {
            currentStep--;
            // Rebuild state from beginning
            state = {
                ...(initialStates[exampleId] ||
                    initialStates["single-function"]),
            };
            state.callStack = [];
            state.logs = [];
            for (let i = 0; i < currentStep; i++) {
                applyStep(i);
            }
            lastAppliedStep = currentStep - 1;
        }
    }

    function startAnimation() {
        if (isPlaying) return;
        isPlaying = true;

        // Execute first step immediately if we are at the start or paused
        if (currentStep === 0) {
            nextStep();
        }

        animationInterval = setInterval(() => {
            nextStep();
        }, speed);
    }

    function stopAnimation() {
        isPlaying = false;
        if (animationInterval) {
            clearInterval(animationInterval);
            animationInterval = null;
        }
    }

    function togglePlay() {
        if (isPlaying) {
            stopAnimation();
        } else {
            const steps =
                simulationSteps[exampleId] ||
                simulationSteps["single-function"];
            if (currentStep >= steps.length) {
                resetSimulation();
            }
            startAnimation();
        }
    }

    $: totalSteps = (
        simulationSteps[exampleId] || simulationSteps["single-function"]
    ).length;
    $: currentHighlight =
        currentStep > 0
            ? (simulationSteps[exampleId] ||
                  simulationSteps["single-function"])[currentStep - 1]
                  ?.highlight
            : "";

    onDestroy(() => {
        stopAnimation();
    });
</script>

<div class="animation-container">
    <div class="animation-header">
        <h3><i class="fa-solid fa-clapperboard"></i> Attack Simulation</h3>
        <p class="hint">Watch how the reentrancy attack unfolds step-by-step</p>
    </div>

    <div class="simulation-area">
        <!-- Entities -->
        <div class="entities">
            {#if exampleId === "cross-chain"}
                <!-- Cross-chain specific layout: Two chains side by side -->
                <div
                    class="entity chain"
                    class:active={currentHighlight === "callback" ||
                        currentHighlight === "reenter"}
                >
                    <div class="entity-icon">
                        <i class="fa-solid fa-link"></i>
                    </div>
                    <div class="entity-name">Chain A (Source)</div>
                    <div class="entity-info">
                        <div class="chain-stat">
                            <span class="label">Token #0:</span>
                            <span
                                class="value"
                                class:owned={state.attackerBalance === 1}
                            >
                                {#if state.attackerBalance === 1}
                                    <i class="fa-solid fa-check"></i> Attacker owns
                                {:else}
                                    <i class="fa-solid fa-xmark"></i> Not owned
                                {/if}
                            </span>
                        </div>
                        <div class="chain-stat">
                            <span class="label">tokenIds:</span>
                            <span class="value counter"
                                >{state.attackerDeposit}</span
                            >
                        </div>
                    </div>
                </div>

                <div class="arrow-container">
                    {#if state.callStack.length > 0}
                        <div
                            class="call-arrow"
                            class:reentrant={state.callStack.length > 1}
                        >
                            <div class="arrow-line"></div>
                            <div class="arrow-label">
                                {state.callStack[state.callStack.length - 1]}
                            </div>
                        </div>
                    {/if}
                </div>

                <div
                    class="entity chain chain-b"
                    class:vulnerable={currentHighlight === "exploit"}
                    class:success={state.contractBalance === 1}
                >
                    <div class="entity-icon">
                        <i class="fa-solid fa-bridge"></i>
                    </div>
                    <div class="entity-name">Chain B (Destination)</div>
                    <div class="entity-info">
                        <div class="chain-stat">
                            <span class="label">Token #0:</span>
                            <span
                                class="value"
                                class:owned={state.contractBalance === 1}
                            >
                                {#if state.contractBalance === 1}
                                    <i class="fa-solid fa-check"></i> Accomplice
                                    owns
                                {:else}
                                    <i class="fa-solid fa-hourglass-half"></i> Pending...
                                {/if}
                            </span>
                        </div>
                        <div class="chain-stat">
                            <span class="label">Bridge:</span>
                            <span class="value">
                                {#if state.contractBalance === 1}
                                    <i class="fa-solid fa-envelope"></i> Event received
                                {:else}
                                    Listening...
                                {/if}
                            </span>
                        </div>
                    </div>
                </div>
            {:else if exampleId === "cross-function"}
                <!-- Cross-function layout: Triangle with Vault at top, Attacker + Attacker2 at bottom -->
                <div class="triangle-layout">
                    <!-- Top: Vault -->
                    <div class="triangle-top">
                        <div
                            class="entity contract"
                            class:vulnerable={currentHighlight === "exploit"}
                        >
                            <div class="entity-icon">
                                <i class="fa-solid fa-landmark"></i>
                            </div>
                            <div class="entity-name">Vault</div>
                            <div class="entity-balance">
                                <span class="label">Balance:</span>
                                <span
                                    class="value"
                                    class:draining={currentHighlight ===
                                        "drain"}
                                >
                                    {state.contractBalance} ETH
                                </span>
                            </div>
                            <div class="guard-status">
                                <span class="guard withdraw"
                                    >withdraw: <i class="fa-solid fa-lock"
                                    ></i></span
                                >
                                <span class="guard transfer unprotected"
                                    >transfer: <i
                                        class="fa-solid fa-triangle-exclamation"
                                    ></i></span
                                >
                            </div>
                        </div>
                    </div>

                    <!-- Arrows between entities -->
                    <div class="triangle-arrows">
                        <!-- Arrow: Attacker ↔ Vault (Left side) -->
                        <div
                            class="arrow-path left-arrow"
                            class:active={state.activeArrow ===
                                "attacker-vault" ||
                                state.activeArrow === "vault-attacker"}
                        >
                            <div class="arrow-line-diagonal left"></div>
                            {#if state.activeArrow === "attacker-vault"}
                                <span class="arrow-direction up">↗</span>
                                <span class="arrow-label-small"
                                    >deposit() / withdraw()</span
                                >
                            {:else if state.activeArrow === "vault-attacker"}
                                <span class="arrow-direction down">↙</span>
                                <span class="arrow-label-small eth-flow"
                                    ><i class="fa-solid fa-coins"></i> 1 ETH</span
                                >
                            {/if}
                        </div>

                        <!-- Arrow: Vault ↔ Attacker2 (Right side - not used in this attack) -->
                        <div
                            class="arrow-path right-arrow"
                            class:active={state.activeArrow ===
                                "vault-attacker2" ||
                                state.activeArrow === "attacker2-vault"}
                        >
                            <div class="arrow-line-diagonal right"></div>
                        </div>

                        <!-- Arrow: Attacker ↔ Attacker2 (via Vault.transfer) - Bottom -->
                        <div
                            class="arrow-path bottom-arrow"
                            class:active={state.activeArrow ===
                                "attacker-attacker2" ||
                                state.activeArrow === "attacker2-attacker"}
                        >
                            {#if state.activeArrow === "attacker-attacker2"}
                                <span class="arrow-label-small exploit"
                                    ><i class="fa-solid fa-triangle-exclamation"
                                    ></i> vault.transfer()</span
                                >
                                <div
                                    class="arrow-line-animated right-flow"
                                ></div>
                                <span class="arrow-eth-indicator"
                                    >→ 1 ETH →</span
                                >
                            {:else if state.activeArrow === "attacker2-attacker"}
                                <span class="arrow-label-small">sendBack()</span
                                >
                                <div
                                    class="arrow-line-animated left-flow"
                                ></div>
                                <span class="arrow-eth-indicator"
                                    >← 1 ETH ←</span
                                >
                            {:else}
                                <div class="arrow-line-horizontal"></div>
                                <span class="arrow-label-dimmed"
                                    >vault.transfer()</span
                                >
                            {/if}
                        </div>
                    </div>

                    <!-- Bottom: Attacker and Attacker2 -->
                    <div class="triangle-bottom">
                        <div
                            class="entity attacker"
                            class:active={currentHighlight === "callback" ||
                                currentHighlight === "reenter"}
                        >
                            <div class="entity-icon">
                                <i class="fa-solid fa-user-ninja"></i>
                            </div>
                            <div class="entity-name">Attacker</div>
                            <div class="entity-balance">
                                <span class="label">ETH:</span>
                                <span
                                    class="value"
                                    class:changed={currentHighlight ===
                                        "drain" ||
                                        currentHighlight === "complete"}
                                >
                                    {state.attackerBalance} ETH
                                </span>
                            </div>
                            <div class="entity-balance">
                                <span class="label">Vault Balance:</span>
                                <span class="value secondary"
                                    >{state.attackerDeposit} ETH</span
                                >
                            </div>
                        </div>

                        <div
                            class="entity attacker2"
                            class:active={state.activeArrow ===
                                "attacker-attacker2" ||
                                state.activeArrow === "attacker2-attacker"}
                        >
                            <div class="entity-icon">
                                <i class="fa-solid fa-handshake"></i>
                            </div>
                            <div class="entity-name">Attacker2</div>
                            <div class="entity-balance">
                                <span class="label">ETH:</span>
                                <span
                                    class="value"
                                    class:changed={(state.attacker2ETH ?? 0) >
                                        0}
                                >
                                    {state.attacker2ETH ?? 0} ETH
                                </span>
                            </div>
                            <div class="entity-balance">
                                <span class="label">Vault Balance:</span>
                                <span
                                    class="value secondary"
                                    class:changed={(state.attacker2Balance ??
                                        0) > 0}
                                >
                                    {state.attacker2Balance ?? 0} ETH
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            {:else if exampleId === "read-only"}
                <!-- Read-Only Reentrancy: Triangle layout with LP Pool at top, Attacker and Lending at bottom -->
                <div class="triangle-layout">
                    <!-- Top: LP Pool (Curve-like) -->
                    <div class="triangle-top">
                        <div
                            class="entity lp-pool"
                            class:exploited={currentHighlight === "exploit"}
                        >
                            <div class="entity-icon">
                                <i class="fa-solid fa-water"></i>
                            </div>
                            <div class="entity-name">Curve LP Pool</div>
                            <div class="entity-info">
                                <div class="lp-stat">
                                    <span class="label">ETH Balance:</span>
                                    <span class="value"
                                        >{state.contractBalance} ETH</span
                                    >
                                </div>
                                <div class="lp-stat">
                                    <span class="label">Total Supply:</span>
                                    <span class="value"
                                        >{state.lpTotalSupply ?? 0} LP</span
                                    >
                                </div>
                                <div class="lp-stat">
                                    <span class="label"
                                        >get_virtual_price():</span
                                    >
                                    <span
                                        class="value"
                                        class:inflated={(state.pricePerLP ??
                                            1) > 1}
                                    >
                                        {(state.pricePerLP ?? 1).toFixed(1)} ETH/LP
                                        {#if (state.pricePerLP ?? 1) > 1}
                                            <span class="warning"
                                                ><i
                                                    class="fa-solid fa-triangle-exclamation"
                                                ></i> INFLATED!</span
                                            >
                                        {/if}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Arrows between entities -->
                    <div class="triangle-arrows readonly-arrows">
                        <!-- Arrow: Attacker ↔ LP Pool (Left side) -->
                        <div
                            class="arrow-path left-arrow"
                            class:active={currentHighlight === "deposit" ||
                                currentHighlight === "withdraw" ||
                                currentHighlight === "callback"}
                        >
                            <div class="arrow-line-diagonal left"></div>
                            {#if currentHighlight === "deposit"}
                                <span class="arrow-direction up">↗</span>
                                <span class="arrow-label-small"
                                    >addLiquidity()</span
                                >
                            {:else if currentHighlight === "withdraw" || currentHighlight === "callback"}
                                <span class="arrow-direction down">↙</span>
                                <span class="arrow-label-small eth-flow"
                                    >removeLiquidity()</span
                                >
                            {/if}
                        </div>

                        <!-- Arrow: LP Pool ↔ Lending (Right side) -->
                        <div
                            class="arrow-path right-arrow"
                            class:active={currentHighlight === "exploit" ||
                                currentHighlight === "reenter"}
                        >
                            <div class="arrow-line-diagonal right"></div>
                            {#if currentHighlight === "exploit" || currentHighlight === "reenter"}
                                <span class="arrow-direction">↘</span>
                                <span class="arrow-label-small exploit"
                                    >reads price!</span
                                >
                            {/if}
                        </div>

                        <!-- Arrow: Attacker → Lending (Bottom) -->
                        <div
                            class="arrow-path bottom-arrow"
                            class:active={currentHighlight === "reenter" ||
                                currentHighlight === "drain"}
                        >
                            {#if currentHighlight === "reenter" || currentHighlight === "drain"}
                                <span class="arrow-label-small exploit"
                                    ><i class="fa-solid fa-triangle-exclamation"
                                    ></i> borrow()</span
                                >
                                <div
                                    class="arrow-line-animated right-flow"
                                ></div>
                                <span class="arrow-eth-indicator"
                                    >→ borrows ETH →</span
                                >
                            {:else}
                                <div class="arrow-line-horizontal"></div>
                                <span class="arrow-label-dimmed">borrow()</span>
                            {/if}
                        </div>
                    </div>

                    <!-- Bottom: Attacker and Lending -->
                    <div class="triangle-bottom">
                        <div
                            class="entity attacker"
                            class:active={currentHighlight === "callback" ||
                                currentHighlight === "reenter"}
                        >
                            <div class="entity-icon">
                                <i class="fa-solid fa-user-ninja"></i>
                            </div>
                            <div class="entity-name">Attacker</div>
                            <div class="entity-balance">
                                <span class="label">ETH:</span>
                                <span
                                    class="value"
                                    class:changed={currentHighlight ===
                                        "drain" ||
                                        currentHighlight === "complete"}
                                >
                                    {state.attackerBalance} ETH
                                </span>
                            </div>
                            <div class="entity-balance">
                                <span class="label">LP Tokens:</span>
                                <span class="value secondary"
                                    >{state.attackerLP ?? 0} LP</span
                                >
                            </div>
                        </div>

                        <div
                            class="entity lending"
                            class:active={currentHighlight === "exploit" ||
                                currentHighlight === "reenter"}
                        >
                            <div class="entity-icon">
                                <i class="fa-solid fa-landmark"></i>
                            </div>
                            <div class="entity-name">Lending Protocol</div>
                            <div class="entity-info">
                                <div class="lp-stat">
                                    <span class="label">Collateral (1 LP):</span
                                    >
                                    <span
                                        class="value"
                                        class:inflated={(state.pricePerLP ??
                                            1) > 1}
                                    >
                                        {(state.pricePerLP ?? 1).toFixed(1)} ETH
                                        value
                                    </span>
                                </div>
                                <div class="lp-stat">
                                    <span class="label">Max Borrow (50%):</span>
                                    <span class="value">
                                        {((state.pricePerLP ?? 1) / 2).toFixed(
                                            1,
                                        )} ETH
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            {:else}
                <!-- Default layout for other examples -->
                <div
                    class="entity attacker"
                    class:active={currentHighlight === "callback" ||
                        currentHighlight === "reenter"}
                >
                    <div class="entity-icon">
                        <i class="fa-solid fa-user-ninja"></i>
                    </div>
                    <div class="entity-name">Attacker</div>
                    <div class="entity-balance">
                        <span class="label">Balance:</span>
                        <span
                            class="value"
                            class:changed={currentHighlight === "drain" ||
                                currentHighlight === "complete"}
                        >
                            {state.attackerBalance} ETH
                        </span>
                    </div>
                </div>

                <div class="arrow-container">
                    {#if state.callStack.length > 0}
                        <div
                            class="call-arrow"
                            class:reentrant={state.callStack.length > 1}
                        >
                            <div class="arrow-line"></div>
                            <div class="arrow-label">
                                {state.callStack[state.callStack.length - 1]}
                            </div>
                        </div>
                    {/if}
                </div>

                <div
                    class="entity contract"
                    class:vulnerable={currentHighlight === "exploit" ||
                        currentHighlight === "check"}
                >
                    <div class="entity-icon">
                        <i class="fa-solid fa-file-code"></i>
                    </div>
                    <div class="entity-name">Vulnerable Contract</div>
                    <div class="entity-balance">
                        <span class="label">Balance:</span>
                        <span
                            class="value"
                            class:draining={currentHighlight === "drain"}
                        >
                            {state.contractBalance} ETH
                        </span>
                    </div>
                </div>

                <!-- LP Pool Info Card (only for read-only example) -->
                {#if exampleId === "read-only"}
                    <div
                        class="entity lp-pool"
                        class:exploited={currentHighlight === "exploit"}
                    >
                        <div class="entity-icon">
                            <i class="fa-solid fa-water"></i>
                        </div>
                        <div class="entity-name">LP Pool</div>
                        <div class="entity-info">
                            <div class="lp-stat">
                                <span class="label">Total Supply:</span>
                                <span class="value"
                                    >{state.lpTotalSupply ?? 0} LP</span
                                >
                            </div>
                            <div class="lp-stat">
                                <span class="label">Your LP:</span>
                                <span class="value"
                                    >{state.attackerLP ?? 0} LP</span
                                >
                            </div>
                            <div class="lp-stat">
                                <span class="label">Price/LP:</span>
                                <span
                                    class="value"
                                    class:inflated={(state.pricePerLP ?? 1) > 1}
                                >
                                    {(state.pricePerLP ?? 1).toFixed(1)} ETH
                                    {#if (state.pricePerLP ?? 1) > 1}
                                        <span class="warning"
                                            ><i
                                                class="fa-solid fa-triangle-exclamation"
                                            ></i></span
                                        >
                                    {/if}
                                </span>
                            </div>
                        </div>
                    </div>
                {/if}
            {/if}
        </div>

        <!-- Call Stack Visualization -->
        {#if state.callStack.length > 0}
            <div class="call-stack">
                <div class="stack-label">
                    <i class="fa-solid fa-layer-group"></i> Call Stack:
                </div>
                <div class="stack-items">
                    {#each state.callStack as call, i}
                        <div
                            class="stack-item"
                            class:reentrant={i > 0}
                            style="--depth: {i}"
                        >
                            {call}
                        </div>
                    {/each}
                </div>
            </div>
        {/if}

        <!-- Event Log -->
        <div class="event-log">
            <div class="log-label">
                <i class="fa-solid fa-scroll"></i> Transaction Log:
            </div>
            <div class="log-entries">
                {#each state.logs as log, i}
                    <div
                        class="log-entry"
                        class:latest={i === state.logs.length - 1}
                        style="animation-delay: {i * 50}ms"
                    >
                        <span class="log-bullet">›</span>
                        {log}
                    </div>
                {/each}
            </div>
        </div>
    </div>

    <!-- Controls -->
    <div class="controls">
        <div class="progress-info">
            Step {currentStep} / {totalSteps}
        </div>

        <div class="progress-bar">
            <div
                class="progress-fill"
                style="width: {(currentStep / totalSteps) * 100}%"
            ></div>
        </div>

        <div class="control-buttons">
            <button
                class="control-btn"
                on:click={resetSimulation}
                title="Reset"
            >
                <i class="fa-solid fa-backward-fast"></i>
            </button>
            <button
                class="control-btn"
                on:click={prevStep}
                disabled={currentStep === 0}
                title="Previous"
            >
                <i class="fa-solid fa-backward-step"></i>
            </button>
            <button
                class="control-btn play-btn"
                on:click={togglePlay}
                title={isPlaying ? "Pause" : "Play"}
            >
                {#if isPlaying}
                    <i class="fa-solid fa-pause"></i>
                {:else}
                    <i class="fa-solid fa-play"></i>
                {/if}
            </button>
            <button
                class="control-btn"
                on:click={nextStep}
                disabled={currentStep >= totalSteps}
                title="Next"
            >
                <i class="fa-solid fa-forward-step"></i>
            </button>
        </div>

        <div class="speed-control">
            <label>Speed:</label>
            <input
                type="range"
                min="500"
                max="3000"
                step="250"
                bind:value={speed}
                on:change={() => {
                    if (isPlaying) {
                        stopAnimation();
                        startAnimation();
                    }
                }}
            />
            <span>{(speed / 1000).toFixed(1)}s</span>
        </div>
    </div>
</div>

<style>
    .animation-container {
        background: var(--bg-code);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius-lg);
        padding: 1.5rem;
        overflow: hidden;
    }

    .animation-header {
        margin-bottom: 1.5rem;
        text-align: center;
    }

    .animation-header h3 {
        margin-bottom: 0.5rem;
    }

    .hint {
        font-size: 0.875rem;
        color: var(--text-muted);
    }

    .simulation-area {
        background: var(--bg-secondary);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        min-height: 300px;
    }

    .entities {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
    }

    .entity {
        flex: 0 0 180px;
        padding: 1.25rem;
        background: var(--bg-card);
        border: 2px solid var(--border-color);
        border-radius: var(--border-radius);
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }

    .entity.active {
        border-color: var(--accent-orange);
        box-shadow: 0 0 20px rgba(249, 115, 22, 0.3);
    }

    .entity.vulnerable {
        border-color: var(--accent-red);
        box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
    }

    .entity-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }

    .entity-name {
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.75rem;
        color: var(--text-primary);
    }

    .entity-balance {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .entity-balance .label {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    .entity-balance .value {
        font-family: var(--font-mono);
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--accent-green);
        transition: all 0.3s ease;
    }

    .entity-balance .value.changed {
        color: var(--accent-cyan);
        transform: scale(1.1);
    }

    .entity-balance .value.draining {
        color: var(--accent-red);
        animation: pulse 0.5s ease;
    }

    /* LP Pool Card Styles */
    .entity.lp-pool {
        border-color: var(--accent-purple);
    }

    .entity.lp-pool.exploited {
        border-color: var(--accent-red);
        box-shadow: 0 0 20px rgba(239, 68, 68, 0.4);
        animation: pulse 0.5s ease;
    }

    .entity-info {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        width: 100%;
    }

    .lp-stat {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.85rem;
    }

    .lp-stat .label {
        color: var(--text-muted);
        font-size: 0.75rem;
    }

    .lp-stat .value {
        font-family: var(--font-mono);
        font-weight: 600;
        color: var(--accent-purple);
    }

    .lp-stat .value.inflated {
        color: var(--accent-red);
        font-size: 1.1rem;
        animation: pulse 0.5s ease infinite;
    }

    .lp-stat .warning {
        margin-left: 0.25rem;
    }

    /* Cross-chain Card Styles */
    .entity.chain {
        border-color: var(--accent-cyan);
        flex: 0 0 200px;
    }

    .entity.chain.chain-b {
        border-color: var(--accent-purple);
    }

    .entity.chain.success {
        border-color: var(--accent-green);
        box-shadow: 0 0 20px rgba(34, 197, 94, 0.4);
    }

    .chain-stat {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.85rem;
        padding: 0.25rem 0;
    }

    .chain-stat .label {
        color: var(--text-muted);
        font-size: 0.75rem;
    }

    .chain-stat .value {
        font-family: var(--font-mono);
        font-weight: 600;
        color: var(--text-secondary);
        font-size: 0.8rem;
    }

    .chain-stat .value.owned {
        color: var(--accent-green);
    }

    .chain-stat .value.counter {
        color: var(--accent-cyan);
        font-size: 1rem;
    }

    /* Triangle Layout for Cross-Function */
    .triangle-layout {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
        width: 100%;
    }

    .triangle-top {
        display: flex;
        justify-content: center;
    }

    .triangle-bottom {
        display: flex;
        justify-content: space-between;
        width: 100%;
        gap: 2rem;
    }

    .triangle-arrows {
        position: relative;
        width: 100%;
        height: 40px;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .arrow-path {
        position: absolute;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.25rem;
        opacity: 0.3;
        transition: all 0.3s ease;
    }

    .arrow-path.active {
        opacity: 1;
    }

    .arrow-path.left-arrow {
        left: 15%;
    }

    .arrow-path.right-arrow {
        right: 15%;
    }

    .arrow-path.bottom-arrow {
        bottom: -20px;
        left: 50%;
        transform: translateX(-50%);
        flex-direction: column;
        gap: 0.15rem;
    }

    .arrow-line-diagonal {
        width: 70px;
        height: 4px;
        background: var(--gradient-primary);
        border-radius: 2px;
        box-shadow: 0 0 6px rgba(159, 239, 0, 0.3);
    }

    .arrow-line-horizontal {
        width: 120px;
        height: 4px;
        background: linear-gradient(
            90deg,
            var(--accent-orange),
            var(--accent-purple)
        );
        border-radius: 2px;
        opacity: 0.5;
        box-shadow: 0 0 6px rgba(139, 92, 246, 0.3);
    }

    .arrow-line-animated {
        width: 100px;
        height: 4px;
        border-radius: 2px;
        position: relative;
        overflow: hidden;
    }

    .arrow-line-animated.right-flow {
        background: linear-gradient(
            90deg,
            var(--accent-red),
            var(--accent-orange)
        );
        animation: flowRight 0.6s ease-in-out infinite;
        box-shadow: 0 0 10px rgba(255, 62, 62, 0.5);
    }

    .arrow-line-animated.left-flow {
        background: linear-gradient(
            90deg,
            var(--accent-purple),
            var(--accent-cyan)
        );
        animation: flowLeft 0.6s ease-in-out infinite;
        box-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
    }

    @keyframes flowRight {
        0% {
            box-shadow: -30px 0 10px var(--accent-orange);
        }
        100% {
            box-shadow: 110px 0 10px var(--accent-red);
        }
    }

    @keyframes flowLeft {
        0% {
            box-shadow: 110px 0 10px var(--accent-cyan);
        }
        100% {
            box-shadow: -30px 0 10px var(--accent-purple);
        }
    }

    .arrow-direction {
        font-size: 1.5rem;
        color: var(--accent-cyan);
        animation: pulse 0.8s ease infinite;
    }

    .arrow-direction.up {
        color: var(--accent-green);
    }

    .arrow-direction.down {
        color: var(--accent-orange);
    }

    .arrow-label-small {
        font-size: 0.65rem;
        color: var(--accent-cyan);
        font-family: var(--font-mono);
        background: rgba(0, 0, 0, 0.5);
        padding: 0.15rem 0.3rem;
        border-radius: 3px;
    }

    .arrow-label-small.eth-flow {
        color: var(--accent-orange);
        font-weight: 600;
    }

    .arrow-label-small.exploit {
        color: var(--accent-red);
        animation: pulse 0.5s ease infinite;
    }

    .arrow-label-dimmed {
        font-size: 0.6rem;
        color: var(--text-muted);
        font-family: var(--font-mono);
        opacity: 0.5;
    }

    .arrow-eth-indicator {
        font-size: 0.75rem;
        font-family: var(--font-mono);
        font-weight: 700;
        color: var(--accent-green);
        animation: pulse 0.8s ease infinite;
    }

    .arrow-path.active .arrow-line-diagonal,
    .arrow-path.active .arrow-line-horizontal {
        background: var(--gradient-primary);
        box-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
    }

    /* Guard Status Display */
    .guard-status {
        display: flex;
        gap: 0.5rem;
        justify-content: center;
        margin-top: 0.5rem;
        flex-wrap: wrap;
    }

    .guard {
        font-size: 0.65rem;
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        font-family: var(--font-mono);
    }

    .guard.withdraw {
        background: rgba(34, 197, 94, 0.2);
        color: var(--accent-green);
    }

    .guard.transfer.unprotected {
        background: rgba(239, 68, 68, 0.2);
        color: var(--accent-red);
    }

    /* Attacker2 Entity */
    .entity.attacker2 {
        border-color: var(--accent-purple);
    }

    .entity.attacker2.active {
        border-color: var(--accent-orange);
        box-shadow: 0 0 20px rgba(249, 115, 22, 0.3);
    }

    /* Lending Entity for Read-Only */
    .entity.lending {
        border-color: var(--accent-orange);
    }

    .entity.lending.active {
        border-color: var(--accent-red);
        box-shadow: 0 0 20px rgba(239, 68, 68, 0.4);
    }

    .entity-balance .value.secondary {
        font-size: 0.9rem;
        color: var(--text-muted);
    }

    .arrow-container {
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center;
        position: relative;
        min-height: 60px;
    }

    .call-arrow {
        display: flex;
        flex-direction: column;
        align-items: center;
        animation: fadeIn 0.3s ease;
    }

    .call-arrow.reentrant .arrow-label {
        color: var(--accent-red);
    }

    .arrow-line {
        width: 120px;
        height: 4px;
        background: var(--gradient-primary);
        position: relative;
        border-radius: 2px;
        box-shadow: 0 0 8px rgba(159, 239, 0, 0.4);
    }

    .arrow-line::after {
        content: "";
        position: absolute;
        right: -12px;
        top: 50%;
        transform: translateY(-50%);
        width: 0;
        height: 0;
        border-left: 12px solid var(--accent-cyan);
        border-top: 8px solid transparent;
        border-bottom: 8px solid transparent;
        filter: drop-shadow(0 0 4px var(--accent-cyan));
    }

    .arrow-label {
        margin-top: 0.5rem;
        font-family: var(--font-mono);
        font-size: 0.8rem;
        color: var(--accent-purple);
        background: var(--bg-card);
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
    }

    .call-stack {
        background: var(--bg-card);
        border-radius: var(--border-radius);
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .stack-label {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-bottom: 0.5rem;
    }

    .stack-items {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .stack-item {
        font-family: var(--font-mono);
        font-size: 0.85rem;
        padding: 0.35rem 0.75rem;
        background: rgba(159, 239, 0, 0.2);
        border: 1px solid var(--accent-purple);
        border-radius: 4px;
        color: var(--text-primary);
    }

    .stack-item.reentrant {
        background: rgba(239, 68, 68, 0.2);
        border-color: var(--accent-red);
        animation: pulse 0.5s ease;
    }

    .event-log {
        background: var(--bg-code);
        border-radius: var(--border-radius);
        padding: 1rem;
        max-height: 150px;
        overflow-y: auto;
    }

    .log-label {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-bottom: 0.5rem;
    }

    .log-entries {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
    }

    .log-entry {
        font-family: var(--font-mono);
        font-size: 0.8rem;
        color: var(--text-secondary);
        display: flex;
        gap: 0.5rem;
        animation: slideIn 0.3s ease;
    }

    .log-entry.latest {
        color: var(--accent-cyan);
        font-weight: 500;
    }

    .log-bullet {
        color: var(--accent-purple);
    }

    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-10px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    .controls {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .progress-info {
        text-align: center;
        font-size: 0.9rem;
        color: var(--text-secondary);
    }

    .progress-bar {
        height: 6px;
        background: var(--bg-card);
        border-radius: 3px;
        overflow: hidden;
    }

    .progress-fill {
        height: 100%;
        background: var(--gradient-primary);
        transition: width 0.3s ease;
    }

    .control-buttons {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 0.75rem;
        background: var(--bg-card);
        padding: 0.75rem 1.5rem;
        border-radius: 50px;
        width: fit-content;
        margin: 0 auto;
    }

    .control-btn {
        width: 48px;
        height: 48px;
        border: 1px solid var(--border-color);
        border-radius: 50%;
        background: var(--bg-card);
        font-size: 1.25rem;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--text-primary);
    }

    .control-btn:hover:not(:disabled) {
        background: var(--bg-secondary);
        border-color: var(--accent-purple);
        transform: scale(1.05);
    }

    .control-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

    .control-btn.play-btn {
        width: 64px;
        height: 64px;
        font-size: 1.5rem;
        background: var(--gradient-primary);
        border: none;
        color: white;
    }

    .control-btn.play-btn:hover {
        transform: scale(1.1);
        box-shadow: var(--shadow-glow);
    }

    .speed-control {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin-top: 0.5rem;
    }

    .speed-control input[type="range"] {
        width: 120px;
        accent-color: var(--accent-purple);
    }
</style>
