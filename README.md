# Reentrancy Simulator

An educational web application demonstrating 5 types of smart contract reentrancy vulnerabilities with interactive attack flow visualizations.

## Reentrancy Types Covered

1. **Single-Function Reentrancy** - The DAO Hack ($60M)
2. **Cross-Function Reentrancy** - Partial ReentrancyGuard bypass
3. **Cross-Contract Reentrancy** - Shared state across contracts
4. **Read-Only Reentrancy** - View function manipulation (Curve-like)
5. **Cross-Chain Reentrancy** - NFT duplication via _safeMint

Each example includes vulnerable code, attack code, fixed code, and step-by-step attack flow.

## Tech Stack

- **Frontend**: Svelte 5 + TypeScript + Vite
- **Backend**: Python Flask
- **Deployment**: Docker + Nginx

## Running with Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:80
- Backend API: http://localhost:5000

## Running Locally

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

- `GET /api/examples` - List all reentrancy examples
- `GET /api/examples/<id>` - Get specific example details
- `GET /api/health` - Health check

## License

MIT
