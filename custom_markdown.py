import os
import tempfile
import re
import hashlib
import base64
import json
from pathlib import Path
from typing import Iterable, Callable

from rich.markdown import Markdown as RichMarkdown
from textual import work, events
from textual.app import ComposeResult
from textual.widgets import Markdown, Static, Label, LoadingIndicator, MarkdownViewer
from textual.containers import Vertical, VerticalScroll
from textual.reactive import reactive
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
            from config import CACHE_DIR
            import requests
            import time

            start_time = time.time()

            # Ensure cache directory exists
            CACHE_DIR.mkdir(parents=True, exist_ok=True)

            script = self.code.strip()
            cache_key = hashlib.md5(script.encode()).hexdigest()
            cache_path = CACHE_DIR / f"mermaid_{cache_key}.png"

            # Check cache first
            if cache_path.exists():
                cache_size = cache_path.stat().st_size / 1024  # KB
                self.app.log(f"→ Mermaid cache HIT: {cache_key[:8]} ({cache_size:.1f}KB)")
                self.app.call_from_thread(self.update_mermaid, str(cache_path), from_cache=True)
                elapsed = time.time() - start_time
                self.app.log(f"  Cache load time: {elapsed:.3f}s")
                return

            self.app.log(f"→ Mermaid cache MISS: {cache_key[:8]}, fetching...")

            # Use moderate quality settings
            # scale=2 for good quality without massive file sizes
            encoded_direct = base64.urlsafe_b64encode(script.encode('utf-8')).decode('ascii')
            url_direct = f"https://mermaid.ink/img/{encoded_direct}?bgColor=transparent&scale=2"

            if not self.app.is_running: return

            fetch_start = time.time()
            response = requests.get(url_direct, timeout=15)
            fetch_time = time.time() - fetch_start

            if not self.app.is_running: return

            if response.status_code == 200:
                size_kb = len(response.content) / 1024
                self.app.log(f"  Fetched in {fetch_time:.2f}s ({size_kb:.1f}KB)")

                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                with open(cache_path, "wb") as f:
                    f.write(response.content)

                self.app.log(f"  Cached to: {cache_path.name}")
                self.app.call_from_thread(self.update_mermaid, str(cache_path), from_cache=False)

                elapsed = time.time() - start_time
                self.app.log(f"  Total time: {elapsed:.2f}s")
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_body = response.text[:200]  # First 200 chars of error
                    if error_body:
                        error_msg += f": {error_body}"
                except:
                    pass

                self.app.log(f"✗ Mermaid fetch failed: {error_msg}")
                self.app.log(f"  URL: {url_direct[:100]}...")
                self.app.log(f"  Mermaid code ({len(script)} chars):\n{script[:300]}")

                self.app.call_from_thread(self.show_error, error_msg)
        except Exception as e:
            if self.app.is_running:
                self.app.log(f"✗ Mermaid error: {e}")
                self.app.call_from_thread(self.show_error, str(e))

    def update_mermaid(self, image_path: str, from_cache: bool = False) -> None:
        try:
            from textual_image.widget import Image as ImageWidget
            from PIL import Image as PILImage

            # Remove loading indicator
            try:
                self.query_one("#loading-mermaid").remove()
            except Exception:
                pass

            # Get actual image dimensions
            with PILImage.open(image_path) as pil_img:
                img_width, img_height = pil_img.size

            # Get terminal dimensions
            terminal_height = self.app.size.height if hasattr(self.app, 'size') else 60
            terminal_width = self.app.size.width if hasattr(self.app, 'size') else 120

            # Calculate max height
            max_diagram_height = max(30, int(terminal_height * 0.6))

            self.app.log(f"  Image: {img_width}x{img_height}px")
            self.app.log(f"  Terminal: {terminal_width}x{terminal_height} cells")
            self.app.log(f"  Max height: {max_diagram_height} cells")

            # Create and mount image widget
            img = ImageWidget(image_path)

            # Set reasonable constraints based on terminal size
            img.styles.width = "auto"
            img.styles.height = "auto"
            img.styles.max_height = max_diagram_height
            img.styles.margin = (1, 0)

            self.mount(img)

            status = "from cache (instant)" if from_cache else "newly fetched"
            self.app.log(f"✓ Mermaid displayed {status}")

        except Exception as e:
            self.app.log(f"✗ Error mounting mermaid image: {e}")
            import traceback
            self.app.log(traceback.format_exc())
            self.show_error(str(e))

    def show_error(self, error_msg: str) -> None:
        try:
            # Remove loading indicator
            try:
                self.query_one("#loading-mermaid").remove()
            except:
                pass

            # Show the original code
            try:
                self.query_one("#code-content").remove_class("hidden")
            except:
                pass

            # Show detailed error message
            error_text = f"[bold red]Mermaid Rendering Failed[/bold red]\n"
            error_text += f"Error: {error_msg}\n\n"
            error_text += "[dim]The original Mermaid code is shown above.[/dim]"

            self.mount(Static(error_text, classes="error"))
        except Exception as e:
            # Last resort fallback
            try:
                self.mount(Static(f"Error: {error_msg}", classes="error"))
            except:
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
        # Skip header processing for faster load
        # TODO: Make this optional or lazy-load
        pass

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

class FastMarkdownContent(VerticalScroll, can_focus=True):
    """Fast markdown content using Rich rendering (single widget)."""

    def compose(self) -> ComposeResult:
        """Compose with a single Static widget for fast rendering."""
        yield Static("# Loading...\n\nPlease wait.", id="md-content")

    async def load(self, path: Path) -> None:
        """Load markdown from a file."""
        content = path.read_text(encoding="utf-8")
        static = self.query_one("#md-content", Static)
        static.update(RichMarkdown(content))


class CustomMarkdownViewer(VerticalScroll, can_focus=True):
    """Markdown viewer with Mermaid support and table of contents."""

    show_table_of_contents = reactive(True)

    def __init__(self, markdown: str = "", show_table_of_contents: bool = True, **kwargs):
        super().__init__(**kwargs)
        self._markdown_content = markdown
        self.show_table_of_contents = show_table_of_contents

    def compose(self) -> ComposeResult:
        """Compose the viewer with TOC and CustomMarkdown."""
        if self.show_table_of_contents:
            yield MarkdownTableOfContents()
        yield CustomMarkdown(self._markdown_content)

    def watch_show_table_of_contents(self, show: bool) -> None:
        """Toggle table of contents visibility."""
        try:
            toc = self.query_one(MarkdownTableOfContents)
            toc.display = show
        except Exception:
            pass

    @property
    def document(self) -> CustomMarkdown:
        """Get the CustomMarkdown widget."""
        return self.query_one(CustomMarkdown)

    async def load(self, path: Path) -> None:
        """Load markdown from a file asynchronously."""
        try:
            markdown_widget = self.document
            await markdown_widget.load(path)
            self.scroll_home(animate=False)
        except Exception as e:
            self.app.log(f"Error loading markdown: {e}")

    async def go(self, location: str | Path) -> None:
        """Navigate to a location (file or URL)."""
        href = str(location)
        parsed = urlparse(href)

        if parsed.scheme in ("http", "https", "mailto"):
            try:
                import webbrowser
                webbrowser.open(href)
            except Exception:
                pass
        else:
            # Handle file navigation
            if hasattr(self.app, "history"):
                current = getattr(self.app, "file_path", None)
                if current and current != Path(location):
                    self.app.history.append(current)
                    self.app.forward_stack.clear()

            if hasattr(self.app, "file_path"):
                self.app.file_path = Path(location)

            # Load the new file
            await self.load(Path(location))
