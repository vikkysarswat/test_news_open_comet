#!/usr/bin/env python3
"""
News Portal MCP Server (Widget-based)
------------------------------------
An MCP server modeled after the official "Pizzaz" demo.
It exposes widget-backed tools that render a news carousel in ChatGPT.
"""

from __future__ import annotations
import logging
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, ValidationError

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
            "summary": "Researchers achieve new milestone in AI language understanding with transformer models.",
            "author": "Dr. Sarah Chen",
            "published_at": "2025-01-15T10:30:00Z",
            "category": "technology",
            "image_url": "https://via.placeholder.com/400x200/0066cc/white?text=AI+News",
            "url": "https://example.com/tech-1",
        },
        {
            "id": "tech-2",
            "title": "New Quantum Computing Milestone Reached",
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
            "summary": "Stock markets worldwide see significant gains amid positive economic indicators.",
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
            "title": "Championship Finals Set for This Weekend",
            "summary": "Two powerhouse teams prepare for the ultimate showdown in the championship finals.",
            "author": "David Kim",
            "published_at": "2025-01-15T16:20:00Z",
            "category": "sports",
            "image_url": "https://via.placeholder.com/400x200/cc0066/white?text=Championship",
            "url": "https://example.com/sports-1",
        }
    ],
}

# --------------------------------------------------------------------
# Widget Definition
# --------------------------------------------------------------------
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
MIME_TYPE = "text/html+skybridge"

@dataclass(frozen=True)
class NewsWidget:
    identifier: str
    title: str
    template_uri: str
    html: str
    response_text: str
    invoking: str
    invoked: str


def _load_widget_html(component_name: str) -> str:
    html_path = ASSETS_DIR / f"{component_name}.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf8")
    raise FileNotFoundError(f"Missing widget HTML at {html_path}")


widgets: List[NewsWidget] = [
    NewsWidget(
        identifier="news-carousel",
        title="Show Latest News Carousel",
        template_uri="ui://widget/news-carousel.html",
        html=_load_widget_html("news-carousel"),
        response_text="Rendered the latest news carousel.",
        invoking="Fetching latest news articles",
        invoked="Displayed news carousel",
    )
]

WIDGETS_BY_ID = {w.identifier: w for w in widgets}
WIDGETS_BY_URI = {w.template_uri: w for w in widgets}

# --------------------------------------------------------------------
# Input Schema
# --------------------------------------------------------------------
class NewsInput(BaseModel):
    """Schema for selecting a category."""
    category: Optional[str] = Field(None, description="News category to display (e.g. technology, business, sports).")
    model_config = ConfigDict(extra="forbid")

TOOL_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "description": "News category to display (e.g. technology, business, sports)."
        }
    },
    "required": [],
    "additionalProperties": False,
}

# --------------------------------------------------------------------
# MCP Setup
# --------------------------------------------------------------------
mcp = FastMCP(name="news-portal-mcp", stateless_http=True)

def _tool_meta(widget: NewsWidget) -> Dict[str, Any]:
    return {
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
    }

def _embedded_widget_resource(widget: NewsWidget) -> types.EmbeddedResource:
    return types.EmbeddedResource(
        type="resource",
        resource=types.TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=widget.html,
            title=widget.title,
        ),
    )

# --------------------------------------------------------------------
# MCP Handlers
# --------------------------------------------------------------------
@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    """Expose tools (widgets) to ChatGPT."""
    return [
        types.Tool(
            name=w.identifier,
            title=w.title,
            description="Displays the latest news in a carousel format.",
            inputSchema=deepcopy(TOOL_INPUT_SCHEMA),
            _meta=_tool_meta(w),
            annotations={
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        )
        for w in widgets
    ]


@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    """Expose HTML templates as MCP resources."""
    return [
        types.Resource(
            name=w.title,
            title=w.title,
            uri=w.template_uri,
            description="News carousel widget HTML template",
            mimeType=MIME_TYPE,
            _meta=_tool_meta(w),
        )
        for w in widgets
    ]


@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> List[types.ResourceTemplate]:
    """Expose widget templates."""
    return [
        types.ResourceTemplate(
            name=w.title,
            title=w.title,
            uriTemplate=w.template_uri,
            description="Template for rendering news carousel widget",
            mimeType=MIME_TYPE,
            _meta=_tool_meta(w),
        )
        for w in widgets
    ]


async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    widget = WIDGETS_BY_URI.get(str(req.params.uri))
    if not widget:
        return types.ServerResult(types.ReadResourceResult(contents=[]))
    return types.ServerResult(
        types.ReadResourceResult(
            contents=[
                types.TextResourceContents(
                    uri=widget.template_uri,
                    mimeType=MIME_TYPE,
                    text=widget.html,
                    title=widget.title,
                    _meta=_tool_meta(widget),
                )
            ]
        )
    )


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    """Handle the main news retrieval and widget rendering."""
    widget = WIDGETS_BY_ID.get(req.params.name)
    if not widget:
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text="Unknown tool")],
                isError=True,
            )
        )

    # Parse category input
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

    # Aggregate news
    all_articles = []
    if category and category.lower() in MOCK_NEWS_DATA:
        all_articles = MOCK_NEWS_DATA[category.lower()]
    else:
        for v in MOCK_NEWS_DATA.values():
            all_articles.extend(v)
    all_articles.sort(key=lambda a: a["published_at"], reverse=True)

    # Build structured carousel content
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
            for a in all_articles
        ],
    }

    widget_resource = _embedded_widget_resource(widget)
    meta = {
        "openai.com/widget": widget_resource.model_dump(mode="json"),
        **_tool_meta(widget),
    }

    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text=widget.response_text)],
            structuredContent=structured,
            _meta=meta,
        )
    )

# Register handlers
mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource

# --------------------------------------------------------------------
# FastMCP Application
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
