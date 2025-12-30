import os
import tempfile
import re
import hashlib
import base64
import json
from pathlib import Path
from typing import Iterable, Callable

# Import cache directory from config
from config import CACHE_DIR

from textual import work, events
from textual.app import ComposeResult
from textual.widgets import Markdown, Static, Label, LoadingIndicator, MarkdownViewer
from textual.containers import Vertical
from textual.widgets._markdown import (
    MarkdownBlock, 
    MarkdownFence, 
    MarkdownHeader, 
    MarkdownTableOfContents, 
    slug_for_tcss_id
)
from textual.content import Content
from markdown_it.token import Token

# Pre-compiled regex for header cleanup
_HEADER_CLEANUP_RE = re.compile(r"^[▼▶]\s*|\s*[#=\-]+$|^\n+")

class SmartMarkdownFence(MarkdownFence):
    """A Markdown fence that can render Mermaid diagrams asynchronously."""

    def compose(self) -> ComposeResult:
        lexer = self.lexer.strip().lower() if self.lexer else ""
        
        # Optimization: Avoid extra container if not mermaid
        if lexer == "mermaid":
            with Vertical(classes="code-block-container"):
                yield Label(lexer, classes="code-language")
                yield LoadingIndicator(id="loading-mermaid")
                yield Label(self._highlighted_code, id="code-content", classes="hidden")
            try:
                self.render_mermaid()
            except Exception:
                pass 
        elif lexer:
            # For normal code with lexer, we need the label
            with Vertical(classes="code-block-container"):
                yield Label(lexer, classes="code-language")
                yield Label(self._highlighted_code, id="code-content")
        else:
            # For plain code blocks, just yield the content (fastest)
            yield Label(self._highlighted_code, id="code-content")

    @work(thread=True)
    def render_mermaid(self) -> None:
        try:
            script = self.code.strip()
            cache_key = hashlib.md5(script.encode()).hexdigest()
            cache_path = CACHE_DIR / f"mermaid_{cache_key}.png"
            
            if cache_path.exists():
                self.app.call_from_thread(self.update_mermaid, str(cache_path))
                return

            # Safe theme detection
            is_dark = getattr(self.app, "dark", True)
            if hasattr(self.app, "theme") and self.app.theme:
                is_dark = "light" not in self.app.theme.lower()
            
            # Method 1: Direct encoding
            encoded_direct = base64.urlsafe_b64encode(script.encode('utf-8')).decode('ascii')
            url_direct = f"https://mermaid.ink/img/{encoded_direct}?bgColor=transparent"
            
            import requests
            if not self.app.is_running: return
            response = requests.get(url_direct, timeout=5)
            if not self.app.is_running: return
            
            if response.status_code == 200:
                with open(cache_path, "wb") as f:
                    f.write(response.content)
                self.app.call_from_thread(self.update_mermaid, str(cache_path))
        except Exception as e:
            if self.app.is_running:
                self.app.call_from_thread(self.show_error, str(e))

    def update_mermaid(self, image_path: str) -> None:
        try:
            from textual_image.widget import Image as ImageWidget
            self.query_one("#loading-mermaid").remove()
            img = ImageWidget(image_path)
            img.styles.width = "auto"
            img.styles.height = "auto"
            img.styles.max_height = 100
            img.styles.margin = (1, 0)
            if hasattr(img, "upscale"):
                img.upscale = True
            self.mount(img)
        except Exception:
            pass

    def show_error(self, error_msg: str) -> None:
        try:
            self.query_one("#loading-mermaid").remove()
            self.query_one("#code-content").remove_class("hidden")
            self.mount(Static(f"Error: {error_msg}", classes="error"))
        except Exception:
            pass

class CustomMarkdown(Markdown):
    """Markdown widget with custom block support."""

    def __init__(
        self,
        markdown: str | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        parser_factory: Callable[[], any] | None = None,
        open_links: bool = True,
    ):
        super().__init__(markdown, name=name, id=id, classes=classes, parser_factory=parser_factory, open_links=open_links)
        self.BLOCKS = self.BLOCKS.copy()
        self.BLOCKS["fence"] = SmartMarkdownFence
        self._collapsed_headers: set[int] = set()
        self.current_style = "obsidian"

    def on_mount(self) -> None:
        """Add icons to headers on mount."""
        # Process headers asynchronously to avoid blocking UI
        self.add_header_icons()

    @work(exclusive=True)
    async def add_header_icons(self) -> None:
        """Add collapse icons to all headers asynchronously."""
        for header in self.query(MarkdownHeader):
            if hasattr(header, "_content"):
                header._original_text = header._content.plain
                header._content = Content("▼ " + header._content.plain)
                if header.is_mounted:
                    header.update(header._content)

    def on_click(self, event: events.Click) -> None:
        """Handle clicks on headers to toggle collapse."""
        widget = event.widget
        while widget and widget is not self:
            if isinstance(widget, MarkdownHeader):
                self.toggle_section(widget)
                event.stop()
                return
            widget = widget.parent

    def toggle_section(self, header: MarkdownHeader) -> None:
        header_id = id(header)
        is_collapsing = header_id not in self._collapsed_headers
        
        if is_collapsing:
            self._collapsed_headers.add(header_id)
        else:
            self._collapsed_headers.remove(header_id)

        # Update header icon
        self.update_header_icon(header, not is_collapsing)

        # Find blocks to toggle
        blocks = list(self.walk_children(MarkdownBlock))
        try:
            start_idx = blocks.index(header)
        except ValueError:
            return

        for block in blocks[start_idx + 1:]:
            if isinstance(block, MarkdownHeader) and block.LEVEL <= header.LEVEL:
                break
            
            if is_collapsing:
                block.add_class("collapsed")
            else:
                block.remove_class("collapsed")

    def update_header_icon(self, header: MarkdownHeader, expanded: bool) -> None:
        if not hasattr(header, "_content"):
            return
            
        icon = "▼ " if expanded else "▶ "
        
        if hasattr(header, "_original_text"):
            plain = header._original_text
        else:
            plain = _HEADER_CLEANUP_RE.sub("", header._content.plain)
            header._original_text = plain
        
        new_text = icon + plain
        header._content = Content(new_text)
        if header.is_mounted:
            header.update(header._content)

    def ensure_visible(self, block: MarkdownBlock) -> None:
        blocks = list(self.walk_children(MarkdownBlock))
        try:
            idx = blocks.index(block)
        except ValueError:
            return

        current_idx = idx
        required_levels = list(range(1, 7))
        
        while current_idx >= 0 and required_levels:
            item = blocks[current_idx]
            if isinstance(item, MarkdownHeader) and item.LEVEL in required_levels:
                if id(item) in self._collapsed_headers:
                    self.toggle_section(item)
                required_levels = [l for l in required_levels if l < item.LEVEL]
            current_idx -= 1

class CustomMarkdownViewer(MarkdownViewer):
    """A Markdown viewer that uses CustomMarkdown."""

    def compose(self) -> ComposeResult:
        markdown = CustomMarkdown(
            parser_factory=self._parser_factory, open_links=False
        )
        markdown.can_focus = True
        yield markdown
        yield MarkdownTableOfContents(markdown)

    async def go(self, location: str | Path) -> None:
        href = str(location)
        from urllib.parse import urlparse
        parsed = urlparse(href)
        
        if parsed.scheme in ("http", "https", "mailto"):
            try:
                import webbrowser
                webbrowser.open(href)
            except Exception:
                pass
        else:
            if hasattr(self.app, "history"):
                current = getattr(self.app, "file_path", None)
                if current and current != Path(location):
                    self.app.history.append(current)
                    self.app.forward_stack.clear()
            
            if hasattr(self.app, "file_path"):
                self.app.file_path = Path(location)
                
            await super().go(location)
