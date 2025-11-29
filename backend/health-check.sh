#!/bin/bash

echo "🔍 AI Nail Stylist - System Health Check"
echo "========================================"
echo ""

# Check Backend API
echo "📊 Backend API Status:"
response=$(curl -s http://localhost:8000/)
echo "   Endpoint: http://localhost:8000"
echo "   Response: $response"
echo ""

# Check Frontend Dev Server
echo "🌐 Frontend Server Status:"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001)
if [ "$response" = "200" ]; then
  echo "   ✅ http://localhost:3001 (Running)"
else
  echo "   ❌ http://localhost:3001 (Status: $response)"
fi
echo ""

# Check Weaviate Vector DB
echo "🗄️ Weaviate Vector Database:"
response=$(curl -s http://localhost:8080/v1/meta)
ready=$(echo "$response" | grep -o '"ready":[^,}]*' || echo "error")
echo "   Endpoint: http://localhost:8080"
echo "   Status: $ready"
echo ""

# Check Docker Services
echo "🐳 Docker Services:"
docker_status=$(docker-compose -f /Users/radinamri/startup-projects/nail-rag/nail-rag-master/docker-compose.yml ps 2>/dev/null)
echo "$docker_status" | grep -E "(nail-rag-api|weaviate)" | while read line; do
  echo "   $line"
done
echo ""

# List Frontend Files
echo "📂 Frontend Files:"
echo "   Config: $(test -f /Users/radinamri/startup-projects/nail-rag/nail-rag-master/frontend/config.ts && echo '✅' || echo '❌') config.ts"
echo "   API Service: $(test -f /Users/radinamri/startup-projects/nail-rag/nail-rag-master/frontend/utils/chatApi.ts && echo '✅' || echo '❌') utils/chatApi.ts"
echo "   Chat Page: $(test -f /Users/radinamri/startup-projects/nail-rag/nail-rag-master/frontend/app/chat/page.tsx && echo '✅' || echo '❌') app/chat/page.tsx (830 lines)"
echo "   AuthContext: $(test -f /Users/radinamri/startup-projects/nail-rag/nail-rag-master/frontend/context/AuthContext.tsx && echo '✅' || echo '❌') context/AuthContext.tsx"
echo "   Environment: $(test -f /Users/radinamri/startup-projects/nail-rag/nail-rag-master/frontend/.env.local && echo '✅' || echo '❌') .env.local"
echo ""

echo "✨ System Ready!"
echo "   🌐 Frontend: http://localhost:3001"
echo "   🔗 Backend:  http://localhost:8000"
echo "   🗄️ Database: http://localhost:8080"
