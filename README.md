# NailAI - AI-Powered Nail Design Assistant 💅

An intelligent nail design assistant powered by RAG (Retrieval-Augmented Generation), GPT-4o vision, and Weaviate vector database. Get personalized nail style recommendations, analyze nail images, and discover your perfect nail designs with advanced multilingual support.

## ✨ Features

- 🎨 **AI Nail Stylist Chat** - Conversational interface for nail design advice with markdown-formatted responses
- 📸 **Image Analysis** - Upload nail photos for shape and style analysis using GPT-4o vision
- 🔍 **RAG-Powered Search** - Hybrid search (vector + BM25) across 4 specialized knowledge collections
- 💬 **Chat History** - Persistent conversation management with pin, rename, delete functionality
- 🌐 **Advanced Multilingual Support** - Seamless Finnish, Swedish, and English language support with automatic detection
- ⚡ **Real-time Responses** - WebSocket streaming for interactive conversations
- 🧠 **Smart Memory** - Short-term (10 messages) conversation context
- 🚀 **Optimizations** - Query expansion, category routing, response caching, and reranking
- 👍 **Message Feedback** - Like/dislike/copy actions for AI responses

## 🏗️ Architecture

```
nail-RAG/
├── backend/                    # FastAPI + Weaviate RAG service
│   ├── app/
│   │   ├── main.py            # FastAPI application
│   │   ├── config.py          # Configuration settings
│   │   ├── constants.py       # Application constants
│   │   ├── logger.py          # Logging setup
│   │   ├── models/            # Database models
│   │   ├── services/          # Business logic services
│   │   │   ├── rag_service.py           # Core RAG logic
│   │   │   ├── chat_service.py          # Chat processing
│   │   │   ├── image_service.py         # Image analysis
│   │   │   ├── multilingual_service.py  # Language support
│   │   │   ├── weaviate_service.py      # Vector DB ops
│   │   │   └── ...
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
│   ├── app/                   # React components & pages
│   │   ├── page.tsx           # Main chat page
│   │   ├── layout.tsx         # App layout
│   │   └── globals.css        # Global styles
│   ├── components/            # Reusable components
│   │   ├── MarkdownRenderer.tsx    # Formats AI responses
│   │   └── MessageActions.tsx      # Like/copy actions
│   ├── package.json           # Node dependencies
│   └── tailwind.config.js     # Styling config
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ and npm
- OpenAI API Key with GPT-4o access

### 1. Backend Setup

```bash
cd backend

# Copy environment template and add your OpenAI API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=your-key-here

# Start backend services (Weaviate + FastAPI)
docker-compose up -d

# Wait for services to be healthy (check with docker-compose ps)
# Then import dataset (first time only)
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

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/chat/conversation` | POST | Create new conversation |
| `/api/chat/conversation/{id}` | DELETE | Delete conversation |
| `/api/chat/message` | POST | Send text message |
| `/api/chat/image` | POST | Upload and analyze image |

### Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔧 Configuration

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | **Required** |
| `OPENAI_MODEL` | GPT model to use | `gpt-4o` |
| `EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:3000` |
| `WEAVIATE_HOST` | Weaviate hostname | `weaviate` (Docker) |
| `WEAVIATE_PORT` | Weaviate port | `8080` |
| `MAX_CONTEXTS_PER_QUERY` | RAG context limit | `8` |
| `SIMILARITY_SCORE_THRESHOLD` | Search threshold | `0.75` |
| `MAX_TOKENS_RESPONSE` | Response token limit | `1000` |
| `TEMPERATURE_RAG` | Response temperature | `0.7` |
| `SHORT_TERM_MEMORY_LIMIT` | Conversation memory | `10` messages |
| `CACHING_ENABLED` | Enable response caching | `true` |
| `QUERY_EXPANSION_ENABLED` | Enable query expansion | `true` |
| `CATEGORY_ROUTING_ENABLED` | Enable smart routing | `true` |

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_CHAT_API_URL` | Backend API URL | `http://localhost:8000` |

## 🗄️ Knowledge Collections

The service uses 4 specialized Weaviate collections:

1. **NailColorTheory** - Color theory, outfit matching, and color psychology
2. **NailSkinTone** - Skin tone-based nail color recommendations
3. **NailSeasonal** - Seasonal trends, occasion-based suggestions
4. **NailShape** - Hand/finger shape analysis and design guidance

Each collection uses hybrid search (vector + BM25) for optimal retrieval.

## 🌐 Multilingual Support

The system provides advanced multilingual capabilities:

### Supported Languages
- 🇬🇧 **English** - Default language
- 🇫🇮 **Finnish (Suomi)** - Full support with automatic detection
- 🇸🇪 **Swedish (Svenska)** - Full support with automatic detection

### How It Works
1. **Automatic Language Detection** - Identifies user's language from input
2. **Query Translation** - Translates non-English queries to English for RAG search
3. **Response Translation** - Translates English RAG results back to user's language
4. **Natural Conversation Flow** - Maintains language consistency throughout conversation

### Key Features
- Context-aware translations preserve technical terms
- Handles code-switching (multiple languages in one message)
- Maintains original meaning and tone across languages
- No manual language selection required

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Weaviate 4.x** - Vector database with hybrid search
- **OpenAI GPT-4o** - Language model & vision
- **text-embedding-3-small** - Text embeddings
- **Docker & Docker Compose** - Containerization

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Lucide React** - Icon library
- **Markdown Rendering** - Rich text formatting

## ⚡ Performance Optimizations

- **Query Expansion** - Generates query variants for better retrieval (20% improvement)
- **Category Routing** - Routes queries to 1-2 most relevant collections (40% faster)
- **Response Caching** - LRU cache (100 entries, 5 min TTL) for frequent queries
- **Context Reranking** - Enhanced scoring with similarity + keyword matching
- **Parallel Processing** - Concurrent searches across collections
- **Answer Quality Validation** - Scores answers for completeness and relevance
- **Efficient Translation Pipeline** - Batch processing and caching for multilingual queries

## 🎨 UI Features

### Chat Interface
- Clean, modern design with nail-themed color scheme (#D98B99)
- Responsive layout (mobile + desktop)
- Persistent chat history with localStorage
- Pin, rename, and delete conversations
- Search through chat history
- Image preview and upload

### Message Display
- **Markdown Rendering** - Bold text, numbered lists, bullet points, headers
- **Message Actions** (AI responses):
  - 👍 Like - Provide positive feedback
  - 👎 Dislike - Provide negative feedback (mutually exclusive with like)
  - 📋 Copy - Copy message to clipboard
- **User Messages** - Copy-only action
- Typing indicators
- Error handling with user-friendly messages

## 🔍 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rag_evaluation.py -v -s

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Manual Testing

```bash
# Test API health
curl http://localhost:8000/health

# Test Weaviate connection
curl http://localhost:8080/v1/.well-known/ready
```

## 🐳 Docker Deployment

### Development (Recommended)

```bash
cd backend
docker-compose up -d
```

### Production

```bash
cd backend

# Build with production settings
docker-compose -f docker-compose.yml build

# Run with restart policy
docker-compose up -d --restart always
```

### Docker Services

- **weaviate** - Vector database (ports: 8080, 50051)
- **nail-rag-api** - FastAPI application (port: 8000)

### Docker Commands

```bash
# View logs
docker-compose logs -f nail-rag-api
docker-compose logs -f weaviate

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v
```

## 🔍 Troubleshooting

### Weaviate Connection Issues
```bash
# Check if Weaviate is running
curl http://localhost:8080/v1/.well-known/ready

# Check Weaviate logs
docker-compose logs weaviate

# Restart Weaviate
docker-compose restart weaviate
```

### Backend API Issues
```bash
# Check API health
curl http://localhost:8000/health

# Check API logs
docker-compose logs nail-rag-api

# Restart API
docker-compose restart nail-rag-api
```

### Dataset Import Issues
```bash
# Check if collections exist
curl http://localhost:8080/v1/schema

# Re-import dataset
docker-compose exec nail-rag-api python -m app.scripts.bulk_import

# Check import logs
docker-compose logs nail-rag-api | grep "import"
```

### Frontend Issues
```bash
# Check if backend is reachable
curl http://localhost:8000/health

# Clear Next.js cache
cd frontend
rm -rf .next
npm run dev

# Check environment variables
cat .env.local
```

### Common Issues

1. **"Conversation not found" errors**
   - Restart backend: `docker-compose restart nail-rag-api`
   - Clear browser cache and localStorage

2. **Images not analyzing**
   - Check OpenAI API key has GPT-4o vision access
   - Verify image size < 5MB and format is JPEG/PNG/WebP

3. **Slow responses**
   - Enable caching: `CACHING_ENABLED=true` in `.env`
   - Reduce `MAX_CONTEXTS_PER_QUERY` to 5-6
   - Check Weaviate memory usage

4. **CORS errors in frontend**
   - Verify `ALLOWED_ORIGINS` includes `http://localhost:3000`
   - Check `NEXT_PUBLIC_CHAT_API_URL` is correct

## 📚 Project Structure Details

### Key Backend Files

- `app/main.py` - FastAPI app initialization, CORS, routes
- `app/config.py` - Environment variables and settings
- `app/services/rag_service.py` - Core RAG logic with multilingual support
- `app/services/chat_service.py` - Message processing and streaming
- `app/services/image_service.py` - GPT-4o vision integration
- `app/services/multilingual_service.py` - Language detection and translation
- `app/services/weaviate_service.py` - Vector DB operations
- `app/routes/chat_routes.py` - REST API endpoints

### Key Frontend Files

- `app/page.tsx` - Main chat interface component
- `components/MarkdownRenderer.tsx` - Formats AI responses
- `components/MessageActions.tsx` - Like/dislike/copy functionality

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- OpenAI for GPT-4o and embedding models
- Weaviate for vector database
- Next.js team for the amazing framework
- FastAPI community

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

**Built with ❤️ for nail enthusiasts and beauty professionals**

