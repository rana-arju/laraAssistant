# Lara Assistant AI Backend

A production-ready FastAPI backend with MongoDB and Qdrant integration for AI chat, voice processing, and scheduling features.

## Features

- **Text Chat**: AI-powered text conversations with memory storage
- **Voice Chat**: Audio upload, transcription, and AI responses  
- **Scheduling**: Social media posts and email scheduling
- **Vector Memory**: Semantic search and conversation context using Qdrant
- **Authentication**: JWT verification with Node.js backend integration
- **Background Jobs**: Redis-based task queue for scheduled operations

## Tech Stack

- **FastAPI**: Modern Python web framework
- **MongoDB**: Document database via Beanie ODM
- **Qdrant**: Vector database for embeddings and semantic search
- **Redis**: Background job queue and caching
- **Docker**: Containerized deployment

## Quick Start

### 1. Environment Setup

Copy the environment template:
```bash
cp .env.example .env
```

Configure your `.env` file:
```bash
# Database URLs
MONGO_URI=mongodb://localhost:27017/lara_assistant
QDRANT_HOST=localhost
QDRANT_PORT=6333
REDIS_URL=redis://localhost:6379

# External Services  
NODE_AUTH_URL=http://localhost:3000  # Your Node.js auth backend
OPENAI_API_KEY=your-openai-api-key   # For AI completions and embeddings

# Optional
DEBUG=true
USE_OPENAI_WHISPER=true  # true = OpenAI API, false = local Whisper
```

### 2. Using Docker (Recommended)

Start all services:
```bash
docker-compose up -d
```

Start with admin UIs:
```bash
docker-compose --profile ui up -d
```

The API will be available at `http://localhost:8000`

Admin interfaces:
- MongoDB Express: `http://localhost:8081`
- Redis Commander: `http://localhost:8082` 
- Qdrant Dashboard: `http://localhost:6333/dashboard`

### 3. Local Development

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Start individual services:
```bash
# MongoDB
docker run -d -p 27017:27017 mongo:7-jammy

# Qdrant
docker run -d -p 6333:6333 qdrant/qdrant:v1.7.4

# Redis  
docker run -d -p 6379:6379 redis:7-alpine

# Start FastAPI app
uvicorn app.main:app --reload --port 8000
```

## API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
All endpoints require `Authorization: Bearer <jwt-token>` header.

### AI Chat
- `POST /api/v1/ai/chat/text` - Text chat with AI
- `POST /api/v1/ai/chat/voice/upload` - Voice chat (upload audio)
- `GET /api/v1/ai/chat/conversations` - Get user conversations

### Scheduling  
- `POST /api/v1/schedule/post` - Schedule social media post
- `POST /api/v1/schedule/email` - Schedule email

### Health
- `GET /` - API status
- `GET /health` - Health check

## Response Format

All responses follow the Express.js sendResponse pattern:

```json
{
  "statusCode": 200,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

Error responses:
```json
{
  "statusCode": 400,
  "message": "Error description", 
  "data": { "error": "details" }
}
```

## Configuration

### Required Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017/lara_assistant` |
| `QDRANT_HOST` | Qdrant server host | `localhost` |
| `QDRANT_PORT` | Qdrant server port | `6333` |
| `NODE_AUTH_URL` | Node.js auth service URL | `http://localhost:3000` |
| `OPENAI_API_KEY` | OpenAI API key for AI features | Required for AI |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `DEBUG` | Enable debug mode | `false` |
| `USE_OPENAI_WHISPER` | Use OpenAI Whisper API vs local | `true` |

## Node.js Backend Integration

This FastAPI backend integrates with your existing Node.js authentication service.

### Required Node.js Endpoints

Your Node backend should expose:

1. **POST /auth/verify** - Verify JWT token
   ```javascript
   // Expected response format
   {
     statusCode: 200,
     message: "Token verified",
     data: {
       userId: "user123",
       email: "user@example.com",
       // ... other user fields
     }
   }
   ```

2. **POST /subscriptions/verify** - Check user subscription
   ```javascript
   // Request body
   {
     userId: "user123", 
     feature: "ai_chat"  // or "voice_chat", "scheduling"
   }
   
   // Expected response
   {
     statusCode: 200,
     message: "Subscription valid",
     data: {
       planType: "premium",
       expiresAt: "2024-12-31T23:59:59Z",
       // ... subscription details
     }
   }
   ```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

```bash
black app/
isort app/
flake8 app/
```

### Database Migrations

The app uses Beanie ODM which handles schema migrations automatically. Models are defined in `app/models/`.

## Production Deployment

### Docker Production

1. Update `docker-compose.yml` for production settings
2. Set secure passwords and API keys
3. Use proper MongoDB authentication
4. Enable SSL/TLS certificates
5. Set up proper logging and monitoring

### Scaling Considerations

- Use MongoDB replica sets for high availability
- Scale Qdrant with clustering for large datasets  
- Use Redis Sentinel for Redis high availability
- Deploy multiple FastAPI instances behind a load balancer

## Troubleshooting

### Common Issues

1. **Connection refused errors**: Ensure all services are running
2. **Authentication failures**: Verify `NODE_AUTH_URL` is correct
3. **Embedding errors**: Check `OPENAI_API_KEY` is set
4. **Transcription issues**: Ensure audio files are valid format

### Logs

View logs:
```bash
docker-compose logs -f app
docker-compose logs -f worker
```

## License

MIT License - see LICENSE file for details.