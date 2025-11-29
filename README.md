# NailAI - AI-Powered Nail Design Assistant

An intelligent nail design assistant powered by RAG (Retrieval-Augmented Generation), GPT-4o vision, and Weaviate vector database. Get personalized nail style recommendations, analyze nail images, and discover your perfect nail designs.

## ✨ Features

- 🎨 **AI Nail Stylist Chat** - Conversational interface for nail design advice
- 📸 **Image Analysis** - Upload nail photos for shape and style analysis using GPT-4o vision
- 🔍 **RAG-Powered Search** - Hybrid search (vector + BM25) across specialized knowledge collections
- 💬 **Chat History** - Persistent conversation management with pin, rename, delete
- 🌐 **Multilingual Support** - Finnish, Swedish, and English language support
- ⚡ **Real-time Responses** - WebSocket streaming for interactive conversations
- 🧠 **Smart Memory** - Short-term (10 messages) and long-term (Weaviate) conversation memory
- 🚀 **Optimizations** - Query expansion, category routing, response caching, and reranking

## 🏗️ Architecture

```
nailai/
├── backend/                    # FastAPI + Weaviate RAG service
│   ├── app/
│   │   ├── main.py            # FastAPI application
│   │   ├── config.py          # Configuration settings
│   │   ├── models/            # Database models
│   │   ├── services/          # Business logic services
│   │   ├── routes/            # API endpoints
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── utils/             # Utility functions
│   │   ├── prompts/           # Prompt templates
│   │   └── scripts/           # Utility scripts
│   ├── datasets/              # Nail design knowledge base
│   ├── docker-compose.yml     # Docker services config
│   ├── Dockerfile             # API container
│   └── requirements.txt       # Python dependencies
├── frontend/                   # Next.js 15 chat interface
│   ├── app/                   # React components
│   ├── package.json           # Node dependencies
│   └── tailwind.config.js     # Styling config
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ and npm
- OpenAI API Key

### 1. Backend Setup

```bash
cd backend

# Copy environment template and add your OpenAI API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=your-key-here

# Start backend services (Weaviate + FastAPI)
docker-compose up -d

# Import dataset (first time only, after services are healthy)
docker-compose exec nail-rag-api python -m app.scripts.bulk_import
```

The backend will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 📖 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/conversation` | POST | Create new conversation |
| `/conversation/{id}` | DELETE | Delete conversation |
| `/message` | POST | Send text message |
| `/image` | POST | Upload and analyze image |
| `/docs` | GET | Swagger UI documentation |
| `/redoc` | GET | ReDoc documentation |

## 🔧 Configuration

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | GPT model to use | `gpt-4o` |
| `EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` |
| `ALLOWED_ORIGINS` | CORS origins | `http://localhost:3000` |
| `MAX_CONTEXTS_PER_QUERY` | RAG context limit | `8` |
| `SIMILARITY_SCORE_THRESHOLD` | Search threshold | `0.75` |
| `MAX_TOKENS_RESPONSE` | Response token limit | `1000` |
| `TEMPERATURE_RAG` | Response temperature | `0.7` |

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_CHAT_API_URL` | Backend API URL | `http://localhost:8000` |

## 🗄️ Knowledge Collections

The service uses 4 specialized Weaviate collections:

1. **NailColorTheory** - Color theory & outfit matching advice
2. **NailSkinTone** - Skin tone-based nail color recommendations
3. **NailSeasonal** - Seasonal & occasion-based nail suggestions
4. **NailShape** - Hand/finger shape & nail design guidance

## 🛠️ Tech Stack

**Backend:**
- FastAPI (Python web framework)
- Weaviate (Vector database with hybrid search)
- OpenAI GPT-4o & text-embedding-3-small
- Docker & Docker Compose

**Frontend:**
- Next.js 15 (React framework)
- TypeScript
- Tailwind CSS
- Lucide React (Icons)

## ⚡ Performance Optimizations

- **Query Expansion** - Generates query variants for better retrieval
- **Category Routing** - Routes queries to 1-2 most relevant collections
- **Response Caching** - LRU cache (100 entries, 5 min TTL)
- **Context Reranking** - Enhanced scoring with similarity + keyword matching
- **Parallel Processing** - Concurrent searches across collections
- **Answer Quality Validation** - Scores answers for completeness

## 🔍 Troubleshooting

### Weaviate Connection Issues
```bash
# Check if Weaviate is running
curl http://localhost:8080/v1/.well-known/ready

# Check logs
docker-compose logs weaviate
```

### API Issues
```bash
# Check API health
curl http://localhost:8000/health

# Check logs
docker-compose logs nail-rag-api
```

## 📝 License

MIT License

