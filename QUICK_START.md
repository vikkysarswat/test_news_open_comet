# Quick Start: Converting JSON to Widgets

## The One Thing You Need to Know

Your server returns JSON because it's missing **ONE critical metadata field**:

```python
_meta={
    "openai/outputTemplate": "ui://widget/your-widget.html"
}
```

## 3-Step Fix

### Step 1: Add Widget Metadata to Tools

```python
@mcp._mcp_server.list_tools()
async def _list_tools():
    return [
        types.Tool(
            name="news-carousel",
            title="Show News Carousel",
            # 🔥 ADD THIS:
            _meta={
                "openai/outputTemplate": "ui://widget/news-carousel.html",
                "openai/widgetAccessible": True,
                "openai/resultCanProduceWidget": True,
            }
        )
    ]
```

### Step 2: Register Widget as Resource

```python
@mcp._mcp_server.list_resources()
async def _list_resources():
    return [
        types.Resource(
            uri="ui://widget/news-carousel.html",
            name="News Carousel",
            mimeType="text/html+skybridge",  # 🔥 EXACT STRING!
            description="News carousel widget"
        )
    ]

@mcp._mcp_server.read_resource()
async def _read_resource(uri: str):
    if uri == "ui://widget/news-carousel.html":
        return [
            types.TextResourceContents(
                uri=uri,
                mimeType="text/html+skybridge",
                text=CAROUSEL_HTML,  # Your widget HTML
                title="News Carousel"
            )
        ]
```

### Step 3: Return EmbeddedResource in Tool Response

```python
@mcp._mcp_server.call_tool()
async def _call_tool(name: str, arguments: Dict) -> List:
    # Get your news data
    articles = get_news_articles(arguments)
    
    # 🔥 RETURN EMBEDDED RESOURCE (not just dict!):
    return [
        types.TextContent(
            type="text",
            text="Here's your news carousel!"
        ),
        types.EmbeddedResource(
            type="resource",
            resource=types.TextResourceContents(
                uri="ui://widget/news-carousel.html",
                mimeType="text/html+skybridge",
                text=CAROUSEL_HTML
            )
        )
    ]
```

## Widget HTML Template

```html
<!DOCTYPE html>
<html>
<head>
<style>
.carousel { padding: 20px; background: #f8f9fa; border-radius: 12px; }
.card { background: white; padding: 20px; border-radius: 8px; margin: 10px 0; }
h2 { font-size: 20px; margin-bottom: 10px; }
</style>
</head>
<body>
<div class="carousel" id="carousel"></div>
<script>
const articles = window.articles || [];
const carousel = document.getElementById('carousel');
articles.forEach(article => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
        <h2>${article.title}</h2>
        <p>${article.summary}</p>
    `;
    carousel.appendChild(card);
});
</script>
</body>
</html>
```

## Complete Minimal Example

```python
from fastapi import FastAPI
from fastmcp import FastMCP
from mcp import types
from typing import List, Dict, Any

app = FastAPI()
mcp = FastMCP("News", dependencies=["fastapi"])

CAROUSEL_HTML = """<!DOCTYPE html>..."""  # From above

@mcp._mcp_server.list_tools()
async def _list_tools():
    return [
        types.Tool(
            name="news-carousel",
            title="Show News Carousel",
            inputSchema={"type": "object", "properties": {}},
            _meta={
                "openai/outputTemplate": "ui://widget/news-carousel.html",
                "openai/widgetAccessible": True,
            }
        )
    ]

@mcp._mcp_server.list_resources()
async def _list_resources():
    return [
        types.Resource(
            uri="ui://widget/news-carousel.html",
            name="News Carousel",
            mimeType="text/html+skybridge"
        )
    ]

@mcp._mcp_server.read_resource()
async def _read_resource(uri: str):
    return [
        types.TextResourceContents(
            uri=uri,
            mimeType="text/html+skybridge",
            text=CAROUSEL_HTML
        )
    ]

@mcp._mcp_server.call_tool()
async def _call_tool(name: str, arguments: Dict) -> List:
    articles = [{"title": "Test", "summary": "Test article"}]
    
    return [
        types.TextContent(type="text", text="Here's your carousel!"),
        types.EmbeddedResource(
            type="resource",
            resource=types.TextResourceContents(
                uri="ui://widget/news-carousel.html",
                mimeType="text/html+skybridge",
                text=CAROUSEL_HTML
            )
        )
    ]

app.mount("/mcp", mcp.get_asgi_app())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Testing

```bash
# Run server
python main.py

# Expose
ngrok http 8000

# In ChatGPT:
# Settings > Connectors > Add Connector
# MCP URL: https://your-url.ngrok.app/mcp

# Test:
# "Show me a news carousel"
```

## Expected Result

❌ **Before:**
```
{"articles": [...]}
```

✅ **After:**
```
[Interactive Widget Renders Here]
```

## Debugging

If still seeing JSON:

1. **Check metadata:**
   ```python
   print(tool._meta)  # Should have "openai/outputTemplate"
   ```

2. **Check MIME type:**
   ```python
   # Must be EXACTLY: "text/html+skybridge"
   ```

3. **Check response:**
   ```python
   # Must include EmbeddedResource, not just dict
   ```

4. **Check ChatGPT:**
   - Developer Mode enabled?
   - Connector added correctly?
   - MCP URL ends with `/mcp`?

## Key Points

1. ✅ Add `_meta.openai/outputTemplate` to tools
2. ✅ Use MIME type `text/html+skybridge` (exact string!)
3. ✅ Return `EmbeddedResource` in tool responses
4. ✅ Register resources with `list_resources()`
5. ✅ Implement `read_resource()` handler

---

That's it! These 5 things turn your JSON server into a widget-rendering powerhouse. 🚀
