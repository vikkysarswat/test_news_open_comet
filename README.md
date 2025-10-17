# 🗞️ News Portal FastMCP Server

[![FastMCP](https://img.shields.io/badge/FastMCP-Powered-blue)](https://github.com/jlowin/fastmcp)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-green)](https://fastapi.tiangolo.com)
[![ChatGPT](https://img.shields.io/badge/ChatGPT-Integration-orange)](https://openai.com)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow)](https://python.org)

A complete Python FastAPI server powered by FastMCP for seamless news portal integration with ChatGPT. This production-ready application provides news aggregation, search, and display capabilities through an MCP (Model Context Protocol) interface.

## ✨ Features

- 🚀 **FastMCP-Powered**: Built on FastMCP for seamless ChatGPT integration
- 📰 **News Management**: Get, search, and categorize news articles
- 🎨 **Rich UI Components**: Pre-built carousel, cards, and list views
- 🔍 **Advanced Search**: Full-text search across articles
- 📱 **Responsive Design**: Mobile-friendly components
- 🔄 **Real-time Updates**: Auto-refreshing news carousel
- 🎯 **Category Filtering**: Browse by Technology, Business, Sports, and more
- 🌐 **RESTful API**: Standard REST endpoints alongside MCP tools

## 📁 Project Structure

```
test_news_open_comet/
├── main.py                          # FastMCP server with news tools
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── .gitignore                       # Python gitignore
└── assets/                          # Frontend assets
    └── components/
        ├── news_card.html           # Individual news card component
        ├── news_carousel.html       # Featured news carousel
        └── news_list.html           # (To be added) News list view
```

## 🔧 Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager
- (Optional) Virtual environment tool

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/vikkysarswat/test_news_open_comet.git
   cd test_news_open_comet
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server**
   ```bash
   python main.py
   ```

   The server will start on `http://0.0.0.0:8000`

5. **Verify installation**
   - Open browser to `http://localhost:8000/health`
   - Check MCP info at `http://localhost:8000/mcp/info`
   - View API docs at `http://localhost:8000/docs`

## 🛠️ Available MCP Tools

The server exposes the following tools for ChatGPT integration:

### 1. `get_news`
**Description**: Retrieve news articles with optional filtering

**Parameters**:
- `category` (optional): Filter by category (technology, business, sports)
- `limit` (default: 10): Maximum number of articles
- `page` (default: 1): Page number for pagination

**Example**:
```python
result = await get_news(category="technology", limit=5, page=1)
```

### 2. `get_article`
**Description**: Retrieve a specific news article by ID

**Parameters**:
- `article_id`: Unique identifier of the article

**Example**:
```python
article = await get_article("tech-1")
```

### 3. `list_categories`
**Description**: List all available news categories

**Example**:
```python
categories = await list_categories()
```

### 4. `search_news`
**Description**: Search for news articles by query

**Parameters**:
- `query`: Search query string
- `category` (optional): Limit search to specific category
- `limit` (default: 10): Maximum results

**Example**:
```python
results = await search_news("AI breakthrough", category="technology", limit=5)
```

## 🌐 REST API Endpoints

In addition to MCP tools, the server provides standard REST endpoints:

- `GET /api/news?category={category}&limit={limit}&page={page}` - Get news articles
- `GET /api/article/{article_id}` - Get specific article
- `GET /api/categories` - List all categories
- `GET /api/search?q={query}&category={category}&limit={limit}` - Search news
- `GET /health` - Health check
- `GET /mcp/info` - MCP server information
- `GET /docs` - Interactive API documentation

## 🔌 ChatGPT Integration

### Configuring as ChatGPT Connector App

1. **Start the server** locally or deploy to a public endpoint

2. **Configure ChatGPT Custom GPT** or **Apps Integration**:
   - Set the server URL (e.g., `http://your-server:8000`)
   - The MCP router is automatically included at `/mcp/*`
   - Use the `/mcp/info` endpoint to verify connectivity

3. **Test the integration**:
   - Ask ChatGPT: "Show me the latest technology news"
   - Ask: "Search for articles about AI"
   - Ask: "What news categories are available?"

### Example ChatGPT Prompts

```
"Get the latest 5 technology news articles"
"Search for business news about markets"
"Show me article with ID tech-1"
"List all available news categories"
"Find recent sports news"
```

## 🎨 UI Components

### News Card (`assets/components/news_card.html`)
Displays individual news articles with:
- Responsive card layout
- Category badges
- Author and date metadata
- Tag system
- Share functionality
- Read more button

### News Carousel (`assets/components/news_carousel.html`)
Featured news carousel with:
- Auto-rotating slides (5-second intervals)
- Manual navigation controls
- Keyboard navigation (Arrow keys)
- Responsive design
- Hover-to-pause functionality
- Indicator dots

## 📊 Data Model

### NewsArticle

```python
{
  "id": "tech-1",
  "title": "Article Title",
  "summary": "Brief summary of the article",
  "content": "Full article content",
  "author": "Author Name",
  "published_at": "2025-01-15T10:30:00Z",
  "category": "technology",
  "tags": ["AI", "NLP", "Machine Learning"],
  "image_url": "https://example.com/image.jpg",
  "source": "Tech Today",
  "url": "https://example.com/article"
}
```

## 🔄 Extending with Real News APIs

The current implementation uses mock data for demonstration. To integrate real news sources:

### Option 1: NewsAPI.org

```python
from newsapi import NewsApiClient

newsapi = NewsApiClient(api_key='YOUR_API_KEY')

@mcp.tool()
async def get_live_news(category: str = 'general'):
    top_headlines = newsapi.get_top_headlines(
        category=category,
        language='en',
        country='us'
    )
    return top_headlines
```

### Option 2: RSS Feeds

```python
import feedparser

@mcp.tool()
async def get_rss_news(feed_url: str):
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries:
        articles.append({
            'title': entry.title,
            'summary': entry.summary,
            'url': entry.link,
            'published_at': entry.published
        })
    return articles
```

### Option 3: Database Integration

Replace `MOCK_NEWS_DATA` with SQLAlchemy database queries for production use.

## 🚀 Deployment

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t news-portal-mcp .
docker run -p 8000:8000 news-portal-mcp
```

### Cloud Deployment

#### Heroku
```bash
heroku create your-app-name
git push heroku main
```

#### Railway/Render
- Connect your GitHub repository
- Set build command: `pip install -r requirements.txt`
- Set start command: `python main.py`

## 🧪 Testing

### Manual Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Get news
curl http://localhost:8000/api/news?category=technology&limit=3

# Search news
curl "http://localhost:8000/api/search?q=AI&limit=5"

# Get specific article
curl http://localhost:8000/api/article/tech-1
```

### Automated Testing (Future)

Add pytest tests:
```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_news():
    response = client.get("/api/news")
    assert response.status_code == 200
    assert "articles" in response.json()
```

## 📝 Configuration

Create a `.env` file for environment-specific settings:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# News API Keys (if using external APIs)
NEWS_API_KEY=your_newsapi_key

# Database (for production)
DATABASE_URL=postgresql://user:password@localhost/newsdb

# Redis Cache (optional)
REDIS_URL=redis://localhost:6379
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.

## 🔗 References

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [OpenAI Apps SDK Examples](https://github.com/openai/openai-apps-sdk-examples)
- [Model Context Protocol](https://modelcontextprotocol.io)

## 💡 Future Enhancements

- [ ] User authentication and personalization
- [ ] Bookmark/favorite articles
- [ ] Email notifications for breaking news
- [ ] Multi-language support
- [ ] Advanced filtering (by date, source, author)
- [ ] Article recommendations
- [ ] Social media integration
- [ ] Comments and discussions
- [ ] Analytics dashboard
- [ ] GraphQL API option

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact: [Your Email]

---

**Built with ❤️ using FastMCP, FastAPI, and modern web technologies**
