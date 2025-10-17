#!/usr/bin/env python3
"""
News Portal FastMCP Server
A complete FastAPI server powered by FastMCP for news portal integration with ChatGPT
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock news data for demonstration
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

# Data models
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

# Initialize FastAPI app
app = FastAPI(
    title="News Portal MCP Server",
    description="FastMCP server for news portal with ChatGPT integration",
    version="1.0.0"
)

# Mount static files for assets
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Initialize FastMCP
mcp = FastMCP("News Portal Server")

@mcp.tool()
async def get_news(
    category: Optional[str] = None,
    limit: int = 10,
    page: int = 1
) -> Dict[str, Any]:
    """
    Retrieve news articles with optional category filtering.
    
    Args:
        category: News category to filter by (technology, business, sports)
        limit: Maximum number of articles to return (default: 10)
        page: Page number for pagination (default: 1)
    
    Returns:
        Dictionary containing articles, pagination info, and metadata
    """
    try:
        all_articles = []
        
        if category:
            if category.lower() in MOCK_NEWS_DATA:
                all_articles = MOCK_NEWS_DATA[category.lower()]
            else:
                raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
        else:
            # Get all articles from all categories
            for cat_articles in MOCK_NEWS_DATA.values():
                all_articles.extend(cat_articles)
        
        # Sort by published date (newest first)
        all_articles.sort(key=lambda x: x['published_at'], reverse=True)
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_articles = all_articles[start_idx:end_idx]
        
        return {
            "articles": paginated_articles,
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
    Retrieve a specific news article by its ID.
    
    Args:
        article_id: Unique identifier of the article
    
    Returns:
        Dictionary containing the full article details
    """
    try:
        # Search for article across all categories
        for category, articles in MOCK_NEWS_DATA.items():
            for article in articles:
                if article['id'] == article_id:
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
    
    Returns:
        Dictionary containing list of categories and count
    """
    try:
        categories = list(MOCK_NEWS_DATA.keys())
        return {
            "categories": categories,
            "total": len(categories)
        }
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
    
    Args:
        query: Search query string
        category: Optional category to limit search to
        limit: Maximum number of results to return
    
    Returns:
        Dictionary containing matching articles and metadata
    """
    try:
        all_articles = []
        
        if category:
            if category.lower() in MOCK_NEWS_DATA:
                all_articles = MOCK_NEWS_DATA[category.lower()]
            else:
                return {"articles": [], "total": 0, "query": query}
        else:
            for cat_articles in MOCK_NEWS_DATA.values():
                all_articles.extend(cat_articles)
        
        # Simple search implementation (case-insensitive)
        query_lower = query.lower()
        matching_articles = []
        
        for article in all_articles:
            if (query_lower in article['title'].lower() or 
                query_lower in article['summary'].lower() or 
                query_lower in article['content'].lower() or
                any(query_lower in tag.lower() for tag in article['tags'])):
                matching_articles.append(article)
        
        # Sort by published date and limit results
        matching_articles.sort(key=lambda x: x['published_at'], reverse=True)
        limited_results = matching_articles[:limit]
        
        return {
            "articles": limited_results,
            "total": len(matching_articles),
            "query": query,
            "category": category
        }
    except Exception as e:
        logger.error(f"Error searching news: {e}")
        raise HTTPException(status_code=500, detail="Failed to search news")

# FastAPI endpoints for direct API access
@app.get("/api/news")
async def api_get_news(
    category: Optional[str] = None,
    limit: int = 10,
    page: int = 1
):
    """REST API endpoint for getting news"""
    result = await get_news(category, limit, page)
    return JSONResponse(content=result)

@app.get("/api/article/{article_id}")
async def api_get_article(article_id: str):
    """REST API endpoint for getting a specific article"""
    result = await get_article(article_id)
    return JSONResponse(content=result)

@app.get("/api/categories")
async def api_list_categories():
    """REST API endpoint for listing categories"""
    result = await list_categories()
    return JSONResponse(content=result)

@app.get("/api/search")
async def api_search_news(
    q: str,
    category: Optional[str] = None,
    limit: int = 10
):
    """REST API endpoint for searching news"""
    result = await search_news(q, category, limit)
    return JSONResponse(content=result)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# MCP server info endpoint
@app.get("/mcp/info")
async def mcp_info():
    """Get MCP server information"""
    return {
        "name": "News Portal MCP Server",
        "version": "1.0.0",
        "description": "FastMCP server for news portal with ChatGPT integration",
        "tools": [
            {
                "name": "get_news",
                "description": "Retrieve news articles with optional category filtering"
            },
            {
                "name": "get_article", 
                "description": "Retrieve a specific news article by its ID"
            },
            {
                "name": "list_categories",
                "description": "List all available news categories"
            },
            {
                "name": "search_news",
                "description": "Search for news articles based on a query string"
            }
        ],
        "assets_url": "/assets"
    }

# Include the FastMCP router
app.include_router(mcp.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
