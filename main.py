#!/usr/bin/env python3
"""
News Portal FastMCP Server
A complete FastAPI server powered by FastMCP for news portal integration with ChatGPT.
Combines clean structure from Code 2 and rich documentation and robustness from Code 1.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Mock News Data (for demo) ---
MOCK_NEWS_DATA = {
    "technology": [
        {
            "id": "tech-1",
            "title": "AI Breakthrough in Natural Language Processing",
            "summary": "Researchers achieve new milestone in AI language understanding with transformer models.",
            "content": "Scientists at leading AI research labs have announced a significant breakthrough in natural language processing...",
            "author": "Dr. Sarah Chen",
            "published_at": "2025-01-15T10:30:00Z",
            "category": "technology",
            "tags": ["AI", "NLP", "Machine Learning"],
            "image_url": "https://via.placeholder.com/400x200/0066cc/white?text=AI+News",
            "source": "Tech Today",
            "url": "https://example.com/tech-1"
        },
        {
            "id": "tech-2",
            "title": "New Quantum Computing Milestone Reached",
            "summary": "IBM announces breakthrough in quantum error correction.",
            "content": "IBM researchers have achieved a new milestone in quantum computing by demonstrating improved error correction...",
            "author": "Michael Rodriguez",
            "published_at": "2025-01-14T14:45:00Z",
            "category": "technology",
            "tags": ["Quantum Computing", "IBM", "Technology"],
            "image_url": "https://via.placeholder.com/400x200/6600cc/white?text=Quantum+Computing",
            "source": "Science Weekly",
            "url": "https://example.com/tech-2"
        }
    ],
    "business": [
        {
            "id": "biz-1",
            "title": "Global Markets Rally on Economic Optimism",
            "summary": "Stock markets worldwide see significant gains amid positive economic indicators.",
            "content": "Global financial markets experienced a significant rally today as investors responded positively to new economic data...",
            "author": "Jennifer Walsh",
            "published_at": "2025-01-15T08:15:00Z",
            "category": "business",
            "tags": ["Markets", "Economy", "Stocks"],
            "image_url": "https://via.placeholder.com/400x200/cc6600/white?text=Market+Rally",
            "source": "Financial Times",
            "url": "https://example.com/biz-1"
        }
    ],
    "sports": [
        {
            "id": "sports-1",
            "title": "Championship Finals Set for This Weekend",
            "summary": "Two powerhouse teams prepare for the ultimate showdown in the championship finals.",
            "content": "The stage is set for an epic championship final as two of the league's most dominant teams prepare to face off...",
            "author": "David Kim",
            "published_at": "2025-01-15T16:20:00Z",
            "category": "sports",
            "tags": ["Championship", "Finals", "Sports"],
            "image_url": "https://via.placeholder.com/400x200/cc0066/white?text=Championship",
            "source": "Sports Central",
            "url": "https://example.com/sports-1"
        }
    ]
}

# --- Data Models ---
class NewsArticle(BaseModel):
    id: str
    title: str
    summary: str
    content: str
    author: str
    published_at: str
    category: str
    tags: List[str]
    image_url: str
    source: str
    url: str

class NewsListResponse(BaseModel):
    articles: List[NewsArticle]
    total: int
    page: int
    per_page: int

class CategoryResponse(BaseModel):
    categories: List[str]
    total: int

# --- Initialize FastAPI and FastMCP ---
app = FastAPI(
    title="News Portal MCP Server",
    description="FastMCP server for news portal with ChatGPT integration",
    version="1.0.0"
)

# Mount static files for assets
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Initialize FastMCP instance from FastAPI
mcp = FastMCP.from_fastapi(app=app)

# --- MCP Tools ---
@mcp.tool()
async def get_news(
    category: Optional[str] = None,
    limit: int = 10,
    page: int = 1
) -> Dict[str, Any]:
    """
    Retrieve news articles with optional category filtering and pagination.
    """
    try:
        all_articles = []
        if category:
            cat = category.lower()
            if cat in MOCK_NEWS_DATA:
                all_articles = MOCK_NEWS_DATA[cat]
            else:
                raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
        else:
            for articles in MOCK_NEWS_DATA.values():
                all_articles.extend(articles)

        # Sort by date (newest first)
        all_articles.sort(key=lambda x: x['published_at'], reverse=True)

        start = (page - 1) * limit
        end = start + limit
        paginated = all_articles[start:end]

        return {
            "articles": paginated,
            "total": len(all_articles),
            "page": page,
            "per_page": limit,
            "total_pages": (len(all_articles) + limit - 1) // limit
        }
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch news")

@mcp.tool()
async def get_article(article_id: str) -> Dict[str, Any]:
    """
    Retrieve a specific news article by ID.
    """
    try:
        for category, articles in MOCK_NEWS_DATA.items():
            for article in articles:
                if article["id"] == article_id:
                    return article
        raise HTTPException(status_code=404, detail=f"Article with ID '{article_id}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching article {article_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch article")

@mcp.tool()
async def list_categories() -> Dict[str, Any]:
    """
    List all available news categories.
    """
    try:
        categories = list(MOCK_NEWS_DATA.keys())
        return {"categories": categories, "total": len(categories)}
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to list categories")

@mcp.tool()
async def search_news(
    query: str,
    category: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search for news articles based on a query string.
    """
    try:
        all_articles = []
        if category:
            cat = category.lower()
            if cat in MOCK_NEWS_DATA:
                all_articles = MOCK_NEWS_DATA[cat]
            else:
                return {"articles": [], "total": 0, "query": query}
        else:
            for group in MOCK_NEWS_DATA.values():
                all_articles.extend(group)

        query_lower = query.lower()
        matched = [
            a for a in all_articles
            if (query_lower in a["title"].lower() or
                query_lower in a["summary"].lower() or
                query_lower in a["content"].lower() or
                any(query_lower in tag.lower() for tag in a["tags"]))
        ]

        matched.sort(key=lambda x: x["published_at"], reverse=True)
        limited = matched[:limit]

        return {
            "articles": limited,
            "total": len(matched),
            "query": query,
            "category": category
        }
    except Exception as e:
        logger.error(f"Error searching news: {e}")
        raise HTTPException(status_code=500, detail="Failed to search news")

# --- REST API Endpoints ---
@app.get("/api/news")
async def api_get_news(category: Optional[str] = None, limit: int = 10, page: int = 1):
    result = await get_news(category, limit, page)
    return JSONResponse(content=result)

@app.get("/api/article/{article_id}")
async def api_get_article(article_id: str):
    result = await get_article(article_id)
    return JSONResponse(content=result)

@app.get("/api/categories")
async def api_list_categories():
    result = await list_categories()
    return JSONResponse(content=result)

@app.get("/api/search")
async def api_search_news(q: str, category: Optional[str] = None, limit: int = 10):
    result = await search_news(q, category, limit)
    return JSONResponse(content=result)

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/mcp/info")
async def mcp_info():
    """Get MCP server information."""
    return {
        "name": "News Portal MCP Server",
        "version": "1.0.0",
        "description": "FastMCP server for news portal with ChatGPT integration",
        "tools": [
            {"name": "get_news", "description": "Retrieve news articles with optional category filtering"},
            {"name": "get_article", "description": "Retrieve a specific news article by its ID"},
            {"name": "list_categories", "description": "List all available news categories"},
            {"name": "search_news", "description": "Search for news articles based on a query string"}
        ],
        "assets_url": "/assets"
    }

# --- Entry Point ---
if __name__ == "__main__":
    # Run combined FastAPI + MCP server
    mcp.run(transport="http", host="0.0.0.0", port=8000)
