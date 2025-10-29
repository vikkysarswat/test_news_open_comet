#!/usr/bin/env python3
"""
News MCP Server
---------------
A fully working MCP server exposing a `get_news` tool that returns
rich structured content (carousel format) compatible with ChatGPT widgets.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from copy import deepcopy
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict, ValidationError

import mcp.types as types
from mcp.server.fastmcp import FastMCP

# --------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("news-mcp")

# --------------------------------------------------------------------
# Mock Data
# --------------------------------------------------------------------
MOCK_NEWS_DATA = {
    "technology": [
        {
            "id": "tech-1",
            "title": "AI Breakthrough in Natural Language Processing",
            "summary": "Researchers achieve new milestone in AI understanding with transformers.",
            "author": "Dr. Sarah Chen",
            "published_at": "2025-01-15T10:30:00Z",
            "category": "technology",
            "image_url": "https://via.placeholder.com/400x200/0066cc/white?text=AI+News",
            "url": "https://example.com/tech-1",
        },
        {
            "id": "tech-2",
            "title": "Quantum Computing Reaches New Milestone",
            "summary": "IBM announces breakthrough in quantum error correction.",
            "author": "Michael Rodriguez",
            "published_at": "2025-01-14T14:45:00Z",
            "category": "technology",
            "image_url": "https://via.placeholder.com/400x200/6600cc/white?text=Quantum+Computing",
            "url": "https://example.com/tech-2",
        },
    ],
    "business": [
        {
            "id": "biz-1",
            "title": "Global Markets Rally on Economic Optimism",
            "summary": "Stocks worldwide rise amid positive indicators.",
            "author": "Jennifer Walsh",
            "published_at": "2025-01-15T08:15:00Z",
            "category": "business",
            "image_url": "https://via.placeholder.com/400x200/cc6600/white?text=Market+Rally",
            "url": "https://example.com/biz-1",
        }
    ],
    "sports": [
        {
            "id": "sports-1",
            "title": "Championship Finals This Weekend",
            "summary": "Two powerhouse teams prepare for the ultimate showdown.",
            "author": "David Kim",
            "published_at": "2025-01-15T16:20:00Z",
            "category": "sports",
            "image_url": "https://via.placeholder.com/400x200/cc0066/white?text=Championship",
            "url": "https://example.com/sports-1",
        }
    ],
}

# --------------------------------------------------------------------
# MCP Setup
# --------------------------------------------------------------------
mcp = FastMCP(name="open_ai_app", stateless_http=True)
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
MIME_TYPE = "text/html+skybridge"

# --------------------------------------------------------------------
# Input Schema
# --------------------------------------------------------------------
class NewsInput(BaseModel):
    """Schema for selecting a news category."""
    category: Optional[str] = Field(
        None, description="News category (technology, business, or sports)."
    )
    model_config = ConfigDict(extra="forbid")

TOOL_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "description": "News category (technology, business, or sports)."
        }
    },
    "required": [],
    "additionalProperties": False,
}

# --------------------------------------------------------------------
# Tool Definition
# --------------------------------------------------------------------
TOOL_NAME = "get_news"
TOOL_TITLE = "Get Latest News"
TOOL_DESCRIPTION = "Returns a carousel of the latest news articles."

HTML_TEMPLATE = """
<div class="news-carousel">
  <h2>Latest News 🗞️</h2>
  <div class="carousel">
    {{#each items}}
      <div class="card">
        <img src="{{image_url}}" alt="{{title}}">
        <h3>{{title}}</h3>
        <p>{{subtitle}}</p>
        <p>{{description}}</p>
        <a href="{{link.url}}" target="_blank">{{link.label}}</a>
      </div>
    {{/each}}
  </div>
</div>
"""

TEMPLATE_URI = "ui://widget/get_news.html"

def _meta() -> Dict[str, Any]:
    return {
        "openai/outputTemplate": TEMPLATE_URI,
        "openai/toolInvocation/invoking": "Fetching latest news",
        "openai/toolInvocation/invoked": "Displayed news carousel",
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
    }

def _embedded_widget() -> types.EmbeddedResource:
    return types.EmbeddedResource(
        type="resource",
        resource=types.TextResourceContents(
            uri=TEMPLATE_URI,
            mimeType=MIME_TYPE,
            text=HTML_TEMPLATE,
            title=TOOL_TITLE,
        ),
    )

# --------------------------------------------------------------------
# Tool Listing
# --------------------------------------------------------------------
@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name=TOOL_NAME,
            title=TOOL_TITLE,
            description=TOOL_DESCRIPTION,
            inputSchema=deepcopy(TOOL_INPUT_SCHEMA),
            _meta=_meta(),
        )
    ]

@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    return [
        types.Resource(
            name=TOOL_TITLE,
            title=TOOL_TITLE,
            uri=TEMPLATE_URI,
            description="HTML template for rendering the news carousel",
            mimeType=MIME_TYPE,
            _meta=_meta(),
        )
    ]

# --------------------------------------------------------------------
# Main Tool Handler
# --------------------------------------------------------------------
async def _call_tool(req: types.CallToolRequest) -> types.ServerResult:
    if req.params.name != TOOL_NAME:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text="Unknown tool")],
                isError=True,
            )
        )

    try:
        payload = NewsInput.model_validate(req.params.arguments or {})
        category = payload.category
    except ValidationError as e:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Validation error: {e.errors()}")],
                isError=True,
            )
        )

    # Get news
    if category and category.lower() in MOCK_NEWS_DATA:
        articles = MOCK_NEWS_DATA[category.lower()]
    else:
        articles = [a for v in MOCK_NEWS_DATA.values() for a in v]

    articles.sort(key=lambda a: a["published_at"], reverse=True)

    structured = {
        "title": "Latest News 🗞️",
        "items": [
            {
                "title": a["title"],
                "subtitle": f"{a['category'].title()} — {a['author']}",
                "description": a["summary"],
                "image_url": a["image_url"],
                "link": {"url": a["url"], "label": "Read full article →"},
            }
            for a in articles
        ],
    }

    widget = _embedded_widget()
    # Note: ensure widget.model_dump returns the correct dict
    meta = {
        "openai/widget": widget.model_dump(mode="json"),
        "openai/resultCanProduceWidget": True,
        "openai/widgetAccessible": True,
        "openai/outputTemplate": TEMPLATE_URI,
    }

    return types.ServerResult(
        types.CallToolResult(
            content=[
                types.TextResourceContents(
                    uri=TEMPLATE_URI,
                    mimeType=MIME_TYPE,
                    text=HTML_TEMPLATE,
                    title=TOOL_TITLE,
                )
            ],
            structuredContent=structured,
            _meta=meta,
        )
    )


# Register the handler
mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool

# --------------------------------------------------------------------
# FastMCP App
# --------------------------------------------------------------------
app = mcp.streamable_http_app()

try:
    from starlette.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
except Exception:
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
