# ChatGPT Widget Integration Guide

## 🔍 Problem Identified

Your MCP server returns **only JSON responses** instead of **rendering widgets/carousels** in ChatGPT because it's missing the critical OpenAI Apps SDK integration metadata.

## 🎯 Root Cause

The key difference between a server that returns JSON vs. one that renders widgets is the **`_meta.openai/outputTemplate`** metadata. This tells ChatGPT to:
1. Fetch and render the widget HTML
2. Display it as a visual component (carousel, card, etc.)
3. Show it inline in the conversation instead of just text

## 📋 Missing Components in Your Repository

### 1. **Widget Metadata** ❌
Your tools don't include `_meta` with OpenAI-specific fields:
```python
_meta={
    "openai/outputTemplate": "ui://widget/news-carousel.html",
    "openai/widgetAccessible": True,
    "openai/resultCanProduceWidget": True,
}
```

### 2. **Embedded Widget Resources** ❌
Tool responses must return `EmbeddedResource` with:
- Widget HTML content
- MIME type: `text/html+skybridge`
- Template URI matching the outputTemplate

### 3. **Proper MCP Resource Registration** ❌
Widgets must be registered as MCP resources with:
- `list_resources()` handler
- `read_resource()` handler  
- Correct MIME type and metadata

## 🚀 Complete Solution

### Updated File Structure
```
test_news_open_comet/
├── main.py                      # ✅ Updated with widget metadata
├── requirements.txt             # ✅ Updated dependencies
├── README.md                    # ✅ Updated documentation
├── WIDGET_INTEGRATION_GUIDE.md  # ✅ This file
├── assets/
│   └── components/
│       ├── news-carousel.html   # ✅ Standalone carousel widget
│       ├── news-cards.html      # ✅ Grid card widget
│       └── news-list.html       # ✅ List view widget
└── .env.example                 # ✅ Environment variables template
```

## 🔑 Critical Code Changes

### 1. Widget Definition with Metadata

```python
from dataclasses import dataclass

@dataclass
class NewsWidget:
    identifier: str          # Tool name (e.g., "news-carousel")
    title: str              # Human-readable title
    template_uri: str       # Widget URI (ui://widget/...)
    invoking: str           # Loading message
    invoked: str            # Success message
    html: str               # Widget HTML content
    response_text: str      # Response message

# Define widgets
widgets = [
    NewsWidget(
        identifier="news-carousel",
        title="Show News Carousel",
        template_uri="ui://widget/news-carousel.html",
        invoking="Loading news carousel",
        invoked="Displayed news carousel",
        html=load_widget_html("news-carousel"),
        response_text="Here's a carousel of the latest news!"
    ),
    # ... more widgets
]
```

### 2. Tool Metadata Function

```python
def _tool_meta(widget: NewsWidget) -> Dict[str, Any]:
    """THE CRITICAL PIECE - tells ChatGPT to render widgets!"""
    return {
        # 🔥 This is the most important field!
        "openai/outputTemplate": widget.template_uri,
        
        # Status messages during tool invocation
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        
        # Widget capabilities
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
    }
```

### 3. MCP Tool Registration

```python
@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name=widget.identifier,
            title=widget.title,
            description=widget.title,
            inputSchema=TOOL_INPUT_SCHEMA,
            _meta=_tool_meta(widget),  # 🔥 Widget metadata!
            annotations={
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        )
        for widget in widgets
    ]
```

### 4. MCP Resource Registration

```python
@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    return [
        types.Resource(
            name=widget.title,
            title=widget.title,
            uri=widget.template_uri,
            description=f"{widget.title} widget markup",
            mimeType="text/html+skybridge",  # 🔥 Critical MIME type!
            _meta={
                "openai/widgetDescription": f"Interactive {widget.title}"
            },
        )
        for widget in widgets
    ]
```

### 5. Resource Reading Handler

```python
@mcp._mcp_server.read_resource()
async def _read_resource(uri: str) -> List[types.TextResourceContents]:
    for widget in widgets:
        if widget.template_uri == uri:
            return [
                types.TextResourceContents(
                    uri=widget.template_uri,
                    mimeType="text/html+skybridge",
                    text=widget.html,
                    title=widget.title,
                )
            ]
    raise ValueError(f"Resource not found: {uri}")
```

### 6. Tool Call Handler with Widget Response

```python
@mcp._mcp_server.call_tool()
async def _call_tool(name: str, arguments: Dict[str, Any]) -> List:
    widget = next((w for w in widgets if w.identifier == name), None)
    if not widget:
        raise ValueError(f"Unknown tool: {name}")
    
    # Get and filter news data
    filtered_news = get_filtered_news(arguments)
    
    # 🔥 Return BOTH text content AND embedded widget resource
    return [
        # Text response
        types.TextContent(
            type="text",
            text=f"{widget.response_text}\n\nShowing {len(filtered_news)} articles.",
        ),
        # Widget data injection
        types.TextContent(
            type="text",
            text=f"<script>window.articles = {json.dumps(filtered_news)};</script>",
            annotations={"mime_type": "text/html"}
        ),
        # 🔥🔥🔥 EMBEDDED WIDGET RESOURCE - THIS MAKES IT RENDER!
        types.EmbeddedResource(
            type="resource",
            resource=types.TextResourceContents(
                uri=widget.template_uri,
                mimeType="text/html+skybridge",
                text=widget.html,
                title=widget.title,
            ),
        )
    ]
```

## 🎨 Widget HTML Structure

### Carousel Widget Example

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        .carousel-container {
            max-width: 100%;
            overflow: hidden;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 12px;
        }
        .carousel-wrapper {
            display: flex;
            transition: transform 0.5s ease;
        }
        .carousel-item {
            min-width: 100%;
            padding: 0 10px;
        }
        /* More styles... */
    </style>
</head>
<body>
    <div class="carousel-container" id="newsCarousel">
        <div class="carousel-wrapper" id="carouselWrapper"></div>
        <div class="carousel-controls" id="carouselControls"></div>
    </div>
    
    <script>
        // Access data passed from MCP server
        const articles = window.articles || [];
        
        // Render carousel
        const wrapper = document.getElementById('carouselWrapper');
        articles.forEach((article, index) => {
            const item = document.createElement('div');
            item.className = 'carousel-item';
            item.innerHTML = `
                <div class="news-card">
                    <img src="${article.image_url}" alt="${article.title}">
                    <h2>${article.title}</h2>
                    <p>${article.summary}</p>
                </div>
            `;
            wrapper.appendChild(item);
        });
        
        // Auto-rotate logic
        let currentIndex = 0;
        setInterval(() => {
            currentIndex = (currentIndex + 1) % articles.length;
            wrapper.style.transform = `translateX(-${currentIndex * 100}%)`;
        }, 5000);
    </script>
</body>
</html>
```

## 🔄 Comparison: JSON vs Widget Response

### ❌ Current (JSON Only)
```json
{
  "articles": [...],
  "total": 10
}
```
**Result:** Plain text in ChatGPT

### ✅ With Widget Metadata
```python
[
    TextContent(text="Here's a carousel..."),
    EmbeddedResource(
        uri="ui://widget/news-carousel.html",
        mimeType="text/html+skybridge",
        text="<html>...</html>"
    )
]
```
**Result:** Interactive carousel rendered in ChatGPT! 🎉

## 📦 Updated Dependencies

```txt
fastapi==0.115.0
fastmcp==0.3.0
uvicorn[standard]==0.32.0
pydantic==2.9.0
```

## 🚀 Deployment Steps

### 1. Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python main.py

# Expose with ngrok
ngrok http 8000
```

### 2. Add to ChatGPT

1. Enable **Developer Mode** in ChatGPT settings
2. Go to **Settings > Connectors**
3. Add new connector:
   - **Name:** News Portal
   - **MCP URL:** `https://your-ngrok-url.ngrok.app/mcp`
4. Test by asking: "Show me a news carousel"

### 3. Deploy to Render/Production

```yaml
# render.yaml
services:
  - type: web
    name: news-mcp-server
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

## 🎯 Expected Behavior After Fix

### Before (JSON):
```
User: Show me tech news
Assistant: Here are some tech articles:
{
  "id": "tech-1",
  "title": "AI Breakthrough...",
  ...
}
```

### After (Widget):
```
User: Show me tech news
Assistant: Here's a carousel of the latest news!

[Interactive Carousel Widget Renders Here]
┌────────────────────────────────────┐
│  🖼️ [News Image]                   │
│  TECHNOLOGY                        │
│  AI Breakthrough: New Model...     │
│  Researchers announce major...     │
│  By Dr. Sarah Johnson             │
│  ← → [Carousel Controls]          │
└────────────────────────────────────┘
```

## 🐛 Troubleshooting

### Widget Not Rendering?

1. **Check MCP endpoint**: Must be `/mcp` not `/mcp/` or `/`
2. **Verify HTTPS**: ChatGPT requires HTTPS (use ngrok for local)
3. **Check metadata**: Ensure `_meta.openai/outputTemplate` is present
4. **MIME type**: Must be exactly `text/html+skybridge`
5. **Resource embedding**: Tool response must include `EmbeddedResource`

### Still Getting JSON?

Add debugging to see what ChatGPT receives:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

@mcp._mcp_server.call_tool()
async def _call_tool(name: str, arguments: Dict) -> List:
    result = [...]  # Your widget response
    logging.debug(f"Returning: {result}")
    return result
```

## 📚 References

- [OpenAI Apps SDK Examples](https://github.com/openai/openai-apps-sdk-examples)
- [Pizzaz Python Server](https://github.com/openai/openai-apps-sdk-examples/tree/main/pizzaz_server_python)
- [Apps SDK Documentation](https://developers.openai.com/apps-sdk/)
- [MCP Specification](https://modelcontextprotocol.io/)

## ✅ Checklist for Widget Rendering

- [ ] Widget metadata includes `openai/outputTemplate`
- [ ] Tool responses include `EmbeddedResource`
- [ ] Resources use MIME type `text/html+skybridge`
- [ ] HTML widgets are self-contained (CSS + JS inline)
- [ ] MCP server implements `list_resources()` and `read_resource()`
- [ ] HTTPS endpoint (ngrok or production deployment)
- [ ] Developer Mode enabled in ChatGPT
- [ ] Connector added with correct MCP URL

## 🎉 Success Indicators

You'll know it's working when:
1. ChatGPT shows loading message from `invoking` field
2. Interactive widget renders inline (not just text)
3. You can interact with carousel controls
4. Auto-rotation works (for carousel)
5. Hover effects work (for cards)

---

**Made with ❤️ for ChatGPT Apps SDK Integration**
