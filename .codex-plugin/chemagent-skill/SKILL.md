# ChemAgent Skill

Use this skill when the user asks about chemical formulas, materials, or any chemistry R&D knowledge stored in their ChemAgent system. This skill routes queries to the local ChemAgent API.

## When to Use
- User asks "search formulas containing epoxy"
- User asks "analyze formula F-001"
- User asks "find materials similar to titanium dioxide"
- User asks "predict performance of formula X"
- Any chemical recipe / formulation question

## How to Use
1. The ChemAgent API runs at `http://localhost:8000` (default).
2. Check API health first: `GET /health`
3. Use the following endpoints:

### Available API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check service status |
| `/api/formulas/search?keyword=...` | GET | Search formulas |
| `/api/formulas/{code}` | GET | Get formula detail |
| `/api/formulas/{code}/similar` | GET | Find similar formulas |
| `/api/materials/search?keyword=...` | GET | Search materials |
| `/api/materials/{name}/usage` | GET | Material usage stats |
| `/api/chat` | POST | AI chat with agent |
| `/api/knowledge/search?query=...` | GET | Search knowledge base |
| `/api/predict` | POST | Predict performance |
| `/api/formula-versions/{code}` | GET | Version history |
| `/api/formula-versions/{code}/diff?v1=...&v2=...` | GET | Version diff |

### API Base
Use `API_BASE` environment variable or default `http://localhost:8000`.

### Workflow
1. Check health: if API is down, tell user to run `./deploy.sh docker` or `.\install.ps1`
2. Query the appropriate endpoint based on user's question
3. Format results in a user-friendly way
4. For complex analysis, use the `/api/chat` endpoint with ReAct agent mode

### Graph Stats
Use `/api/formulas/stats` to get an overview of available data before searching.
