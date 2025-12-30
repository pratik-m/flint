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
    MarkdownTable,
    MarkdownBlockQuote,
    slug_for_tcss_id
)
from textual.content import Content
from markdown_it.token import Token

# IMPORTANT: Import textual_image BEFORE app starts (per textual-image docs)
from textual_image.widget import TGPImage

# Pre-compiled regex for header cleanup
_HEADER_CLEANUP_RE = re.compile(r"^[▼▶]\s*|\s*[#=\-]+$|^\n+")

# Pre-compiled regex for image and callout preprocessing
_IMG_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^\)]+)\)')
_CALLOUT_PATTERN = re.compile(r'^>\s*\[!([^\]]+)\](.*)$', re.MULTILINE)
_BOLD_CALLOUT_PATTERN = re.compile(r'^>\s*\*\*([^*]+)\*\*(.*)$', re.MULTILINE)

class SmartImageFence(MarkdownFence):
    """A Markdown fence that renders images asynchronously."""

    def compose(self) -> ComposeResult:
        # For ~~~image blocks
        with Vertical(classes="code-block-container", id="image-block"):
            yield Label("image", classes="code-language")
            yield LoadingIndicator(id="loading-image")
        try:
            self.render_image()
        except Exception:
            pass

    @work(thread=True)
    def render_image(self) -> None:
        """Render images from local files or remote URLs."""
        try:
            from config import CACHE_DIR
            from PIL import Image as PILImage
            from pathlib import Path
            import io

            CACHE_DIR.mkdir(parents=True, exist_ok=True)

            # Parse: first line is URL/path, rest is alt text
            lines = self.code.strip().split('\n')
            url_or_path = lines[0].strip()

            # Check if it's a local file path
            is_local = not url_or_path.startswith(('http://', 'https://'))

            if is_local:
                # Handle local file
                local_path = Path(url_or_path)

                # Make path absolute if relative (relative to markdown file location)
                if not local_path.is_absolute() and hasattr(self.app, 'file_path'):
                    local_path = self.app.file_path.parent / local_path

                if local_path.exists():
                    self.app.log(f"→ Local image: {local_path.name}")

                    # Check if local image needs resizing
                    img = PILImage.open(local_path)
                    MAX_WIDTH = 1200

                    if img.width > MAX_WIDTH:
                        # Create cached resized version
                        cache_key = hashlib.md5(str(local_path).encode()).hexdigest()
                        cache_path = CACHE_DIR / f"local_{cache_key}.png"

                        if not cache_path.exists():
                            ratio = MAX_WIDTH / img.width
                            new_height = int(img.height * ratio)
                            resized = img.resize((MAX_WIDTH, new_height), PILImage.Resampling.LANCZOS)
                            resized.save(cache_path, "PNG", optimize=True)
                            self.app.log(f"  Resized local image to {MAX_WIDTH}x{new_height}")

                        self.app.call_from_thread(self.display_image, str(cache_path))
                    else:
                        # Use original if small enough
                        self.app.call_from_thread(self.display_image, str(local_path))
                else:
                    self.app.log(f"✗ Local image not found: {local_path}")
                    self.app.call_from_thread(self.show_image_error, f"File not found: {local_path.name}")
            else:
                # Handle remote URL
                import requests

                # Generate cache key for remote images
                cache_key = hashlib.md5(url_or_path.encode()).hexdigest()
                cache_path = CACHE_DIR / f"image_{cache_key}.png"

                # Check cache
                if cache_path.exists():
                    self.app.log(f"→ Image cache HIT: {url_or_path[:50]}")
                    self.app.call_from_thread(self.display_image, str(cache_path))
                    return

                self.app.log(f"→ Image cache MISS, downloading: {url_or_path[:50]}")

                # Download image
                if not self.app.is_running:
                    return
                response = requests.get(url_or_path, timeout=15)
                if not self.app.is_running:
                    return

                if response.status_code == 200:
                    # Load image and resize for terminal display
                    img = PILImage.open(io.BytesIO(response.content))

                    # Resize to terminal-optimal width (match Mermaid diagrams)
                    MAX_WIDTH = 800
                    if img.width > MAX_WIDTH:
                        ratio = MAX_WIDTH / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((MAX_WIDTH, new_height), PILImage.Resampling.LANCZOS)
                        self.app.log(f"  Resized to {MAX_WIDTH}x{new_height} for terminal")

                    # Save resized image to cache
                    img.save(cache_path, "PNG", optimize=True)
                    self.app.log(f"  Cached to: {cache_path.name}")
                    self.app.call_from_thread(self.display_image, str(cache_path))
                else:
                    self.app.call_from_thread(self.show_image_error, f"HTTP {response.status_code}")

        except Exception as e:
            if self.app.is_running:
                self.app.log(f"✗ Image error: {e}")
                self.app.call_from_thread(self.show_image_error, str(e))

    def display_image(self, image_path: str) -> None:
        try:
            # Remove loading indicator
            try:
                self.query_one("#loading-image").remove()
            except:
                pass

            # Create image widget using TGP rendering with unique ID
            import os
            img_id = f"img-{os.path.basename(image_path)[:16]}"
            img = TGPImage(str(image_path), id=img_id)
            img.styles.width = "auto"
            img.styles.height = "auto"
            img.styles.margin = (0, 0, 2, 0)

            # Mount into container
            container = self.query_one("#image-block", Vertical)
            container.mount(img)

            # Force refresh for instant display
            container.refresh(layout=True)
            self.refresh(layout=True)

            self.app.log(f"✓ Image displayed (TGP)")

        except Exception as e:
            self.app.log(f"✗ Error displaying image: {e}")
            self.show_image_error(str(e))

    def show_image_error(self, error_msg: str) -> None:
        try:
            try:
                self.query_one("#loading-image").remove()
            except:
                pass
            self.mount(Static(f"[red]Image load failed: {error_msg}[/red]", classes="error"))
        except:
            pass


class SmartMarkdownFence(MarkdownFence):
    """A Markdown fence that can render Mermaid diagrams and images asynchronously."""

    def compose(self) -> ComposeResult:
        lexer = self.lexer.strip().lower() if self.lexer else ""

        if lexer == "image":
            # Handle images
            with Vertical(classes="code-block-container", id="image-block"):
                yield Label("image", classes="code-language")
                yield LoadingIndicator(id="loading-image")
            try:
                self.render_image()
            except Exception:
                pass
        elif lexer == "mermaid":
            # Handle mermaid diagrams
            with Vertical(classes="code-block-container", id="mermaid-block"):
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
    def render_image(self) -> None:
        """Render images from local files or remote URLs."""
        try:
            from config import CACHE_DIR
            from PIL import Image as PILImage
            from pathlib import Path
            import io

            CACHE_DIR.mkdir(parents=True, exist_ok=True)

            # Parse: first line is URL/path, rest is alt text
            lines = self.code.strip().split('\n')
            url_or_path = lines[0].strip()

            # Check if it's a local file path
            is_local = not url_or_path.startswith(('http://', 'https://'))

            if is_local:
                # Handle local file
                local_path = Path(url_or_path)

                # Make path absolute if relative (relative to markdown file location)
                if not local_path.is_absolute() and hasattr(self.app, 'file_path'):
                    local_path = self.app.file_path.parent / local_path

                if local_path.exists():
                    self.app.log(f"→ Local image: {local_path.name}")

                    # Check if local image needs resizing
                    img = PILImage.open(local_path)
                    MAX_WIDTH = 1200

                    if img.width > MAX_WIDTH:
                        # Create cached resized version
                        cache_key = hashlib.md5(str(local_path).encode()).hexdigest()
                        cache_path = CACHE_DIR / f"local_{cache_key}.png"

                        if not cache_path.exists():
                            ratio = MAX_WIDTH / img.width
                            new_height = int(img.height * ratio)
                            resized = img.resize((MAX_WIDTH, new_height), PILImage.Resampling.LANCZOS)
                            resized.save(cache_path, "PNG", optimize=True)
                            self.app.log(f"  Resized local image to {MAX_WIDTH}x{new_height}")

                        self.app.call_from_thread(self.display_image, str(cache_path))
                    else:
                        # Use original if small enough
                        self.app.call_from_thread(self.display_image, str(local_path))
                else:
                    self.app.log(f"✗ Local image not found: {local_path}")
                    self.app.call_from_thread(self.show_image_error, f"File not found: {local_path.name}")
            else:
                # Handle remote URL
                import requests

                # Generate cache key for remote images
                cache_key = hashlib.md5(url_or_path.encode()).hexdigest()
                cache_path = CACHE_DIR / f"image_{cache_key}.png"

                # Check cache
                if cache_path.exists():
                    self.app.log(f"→ Image cache HIT: {url_or_path[:50]}")
                    self.app.call_from_thread(self.display_image, str(cache_path))
                    return

                self.app.log(f"→ Image cache MISS, downloading: {url_or_path[:50]}")

                # Download image
                if not self.app.is_running:
                    return
                response = requests.get(url_or_path, timeout=15)
                if not self.app.is_running:
                    return

                if response.status_code == 200:
                    # Load image and resize for terminal display
                    img = PILImage.open(io.BytesIO(response.content))

                    # Resize to terminal-optimal width (match Mermaid diagrams)
                    MAX_WIDTH = 800
                    if img.width > MAX_WIDTH:
                        ratio = MAX_WIDTH / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((MAX_WIDTH, new_height), PILImage.Resampling.LANCZOS)
                        self.app.log(f"  Resized to {MAX_WIDTH}x{new_height} for terminal")

                    # Save resized image to cache
                    img.save(cache_path, "PNG", optimize=True)
                    self.app.log(f"  Cached to: {cache_path.name}")
                    self.app.call_from_thread(self.display_image, str(cache_path))
                else:
                    self.app.call_from_thread(self.show_image_error, f"HTTP {response.status_code}")

        except Exception as e:
            if self.app.is_running:
                self.app.log(f"✗ Image error: {e}")
                self.app.call_from_thread(self.show_image_error, str(e))

    def display_image(self, image_path: str) -> None:
        """Display loaded image."""
        try:
            # Remove loading indicator
            try:
                self.query_one("#loading-image").remove()
            except:
                pass

            # Create image widget using TGP rendering with unique ID
            import os
            img_id = f"img-{os.path.basename(image_path)[:16]}"
            img = TGPImage(str(image_path), id=img_id)
            img.styles.width = "auto"
            img.styles.height = "auto"
            img.styles.margin = (0, 0, 2, 0)

            # Mount into container
            container = self.query_one("#image-block", Vertical)
            container.mount(img)

            # Force refresh for instant display
            container.refresh(layout=True)
            self.refresh(layout=True)

            self.app.log(f"✓ Image displayed (TGP)")

        except Exception as e:
            self.app.log(f"✗ Error displaying image: {e}")
            self.show_image_error(str(e))

    def show_image_error(self, error_msg: str) -> None:
        """Show image load error."""
        try:
            try:
                self.query_one("#loading-image").remove()
            except:
                pass
            self.mount(Static(f"[red]Image load failed: {error_msg}[/red]", classes="error"))
        except:
            pass

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

            # Use smaller width for better terminal rendering quality
            # width=800 is smaller but may render better at terminal resolution
            encoded_direct = base64.urlsafe_b64encode(script.encode('utf-8')).decode('ascii')
            url_direct = f"https://mermaid.ink/img/{encoded_direct}?bgColor=transparent&width=800"

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
            from PIL import Image as PILImage

            # Get actual image dimensions
            with PILImage.open(image_path) as pil_img:
                img_width, img_height = pil_img.size

            # Get terminal dimensions
            terminal_height = self.app.size.height if hasattr(self.app, 'size') else 60

            self.app.log(f"  Image: {img_width}x{img_height}px")

            # Create image widget using TGP rendering with unique ID
            import os
            img_id = f"img-{os.path.basename(image_path)[:16]}"
            img = TGPImage(str(image_path), id=img_id)
            img.styles.width = "auto"
            img.styles.height = "auto"
            img.styles.margin = (0, 0, 2, 0)

            # Remove loading indicator and code-content
            try:
                self.query_one("#loading-mermaid").remove()
            except:
                pass
            try:
                self.query_one("#code-content").remove()
            except:
                pass

            # Mount into container
            container = self.query_one("#mermaid-block", Vertical)
            container.mount(img)

            # Force refresh for instant display
            container.refresh(layout=True)
            self.refresh(layout=True)

            self.app.log(f"✓ Mermaid displayed {img_width}x{img_height}px")

        except Exception as e:
            self.app.log(f"✗ Error: {e}")
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

class InteractiveTable(MarkdownTable):
    """A Markdown table that renders as an interactive DataTable."""

    def compose(self) -> ComposeResult:
        # Do not yield DataTable here as it might interfere with Markdown parser adding children
        return []

    def on_mount(self) -> None:
        """Schedule data extraction after children are mounted."""
        from textual.widgets import DataTable
        # Mount DataTable manually
        self.mount(DataTable())
        self.call_later(self._extract_table_data)

    def _extract_table_data(self) -> None:
        """Extract data from _blocks and populate DataTable."""
        from textual.widgets import DataTable

        try:
            table = self.query_one(DataTable)
            table.cursor_type = "row"
            table.zebra_stripes = True
            table.clear(columns=True)
            
            # Use inherited method to get data from self._blocks
            # This is populated by the Markdown parser before the widget is mounted
            headers, rows = self._get_headers_and_rows()
            
            # Convert Content objects to plain text
            plain_headers = [h.plain for h in headers]
            plain_rows = [[c.plain for c in row] for row in rows]
            
            if plain_headers:
                table.add_columns(*plain_headers)
            
            if plain_rows:
                table.add_rows(plain_rows)

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
        # Pre-process markdown to convert images to fence blocks and handle callouts
        if markdown:
            markdown = self._preprocess_markdown(markdown)

        super().__init__(markdown, name=name, id=id, classes=classes, parser_factory=parser_factory, open_links=open_links)
        self.BLOCKS = self.BLOCKS.copy()
        self.BLOCKS["fence"] = SmartMarkdownFence
        self.BLOCKS["table_open"] = InteractiveTable
        self._collapsed_headers: set[int] = set()
        self.current_style = "obsidian"

    @staticmethod
    def _preprocess_markdown(markdown: str) -> str:
        """Preprocess markdown for images and callouts."""
        # 1. Images: Convert ![alt](url) to ~~~image fence blocks
        def replace_image(match):
            alt = match.group(1)
            url = match.group(2)
            return f"~~~image\n{url}\n{alt}\n~~~"
        markdown = _IMG_PATTERN.sub(replace_image, markdown)

        # 2. Callouts: Convert > [!TYPE] Title or > **TYPE** to styled header
        def replace_callout(match):
            ctype = match.group(1).upper()
            title = match.group(2).strip()
            
            # Map types to icons
            icons = {
                "INFO": "ℹ️",
                "WARNING": "⚠️",
                "ERROR": "🚫",
                "TIP": "💡",
                "NOTE": "📝",
                "IMPORTANT": "❗",
                "CAUTION": "🔥",
                "SUCCESS": "✅",
                "QUESTION": "❓",
                "ABSTRACT": "📋",
                "TODO": "☑️",
                "FAILURE": "❌",
                "DANGER": "⚡",
                "BUG": "🐛",
                "EXAMPLE": "🧪",
                "QUOTE": "💬"
            }
            icon = icons.get(ctype, "📝")
            
            # Create a bold header with icon
            header = f"**{icon} {ctype}**"
            if title:
                header += f" {title}"
            
            # Return the header and an empty blockquote line to separate from content
            return f"> {header}\n> "
            
        markdown = _CALLOUT_PATTERN.sub(replace_callout, markdown)
        markdown = _BOLD_CALLOUT_PATTERN.sub(replace_callout, markdown)
        
        return markdown

    @staticmethod
    def _preprocess_images(markdown: str) -> str:
        """Legacy method, now uses _preprocess_markdown."""
        return CustomMarkdown._preprocess_markdown(markdown)

    async def load(self, path: Path) -> None:
        """Override load to preprocess markdown."""
        import asyncio
        # Read file in thread to avoid blocking
        content = await asyncio.to_thread(path.read_text, encoding="utf-8")
        # Preprocess markdown before passing to parent load
        content = self._preprocess_markdown(content)
        # Update document with preprocessed content
        await self.update(content)

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
