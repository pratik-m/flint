import sys
from pathlib import Path
from typing import Iterable

from textual import work
from textual.app import App, ComposeResult, Widget
from textual.binding import Binding
from textual.widgets import Footer, Header, Input
from textual.widgets._markdown import MarkdownTableOfContents
from textual.containers import Vertical
from textual.reactive import reactive
from textual.command import Command, Hit, Provider, CommandPalette, DiscoveryHit
# from custom_markdown import CustomMarkdownViewer, CustomMarkdown  # Lazy loaded
# from config import THEMES_DIR, CACHE_DIR, load_settings, save_settings  # DISABLED

from functools import partial

# Get the package directory for loading resources
_PACKAGE_DIR = Path(__file__).parent


class ThemeProvider(Provider):
    """A provider for themes."""

    @property
    def commands(self) -> list[tuple[str, callable]]:
        themes = self.app.available_themes

        def set_app_theme(name: str) -> None:
            self.app.theme = name

        # User themes disabled for now
        user_themes = []

        commands = [
            (theme.name, partial(set_app_theme, theme.name))
            for theme in themes.values()
            if theme.name != "textual-ansi"
        ]
        commands.extend(user_themes)
        return commands

    async def discover(self) -> Iterable[DiscoveryHit]:
        for name, callback in self.commands:
            yield DiscoveryHit(
                name,
                callback,
                help=f"Switch to the {name} theme",
            )

    async def search(self, query: str) -> Iterable[Hit]:
        matcher = self.matcher(query)
        for name, callback in self.commands:
            if (match := matcher.match(name)) > 0:
                yield Hit(
                    match,
                    matcher.highlight(name),
                    callback,
                    help=f"Switch to the {name} theme",
                )


class StyleProvider(Provider):
    """A provider for visual styles."""

    @property
    def commands(self) -> list[tuple[str, callable]]:
        styles = {
            "Obsidian": "obsidian",
            "Minimal": "minimal",
            "Academic": "academic",
            "Cyberpunk": "cyberpunk",
            "Blueprint": "blueprint",
            "Retro": "retro",
            "ASCII": "ascii",
        }
        return [
            (name, partial(self.app.action_switch_style, style_id))
            for name, style_id in styles.items()
        ]

    async def discover(self) -> Iterable[DiscoveryHit]:
        for name, callback in self.commands:
            yield DiscoveryHit(
                name,
                callback,
                help=f"Switch to the {name} visual style",
            )

    async def search(self, query: str) -> Iterable[Hit]:
        matcher = self.matcher(query)
        for name, callback in self.commands:
            if (match := matcher.match(name)) > 0:
                yield Hit(
                    match,
                    matcher.highlight(name),
                    callback,
                    help=f"Switch to the {name} visual style",
                )


class MainCommandProvider(Provider):
    """The main command provider that offers submenus."""

    async def discover(self) -> Iterable[DiscoveryHit]:
        """Yield commands to be displayed when the palette is opened."""
        yield DiscoveryHit(
            "Switch Style...",
            self.app.action_search_styles,
            help="Open the style selection menu",
        )
        yield DiscoveryHit(
            "Switch Theme...",
            self.app.action_search_themes,
            help="Open the theme selection menu",
        )
        yield DiscoveryHit(
            "Clear Cache",
            self.app.action_clear_cache,
            help="Remove all cached images and diagrams",
        )

    async def search(self, query: str) -> Iterable[Hit]:
        matcher = self.matcher(query)

        # Switch Style...
        name = "Switch Style..."
        if (match := matcher.match(name)) > 0:
            yield Hit(
                match,
                matcher.highlight(name),
                self.app.action_search_styles,
                help="Open the style selection menu",
            )

        # Switch Theme...
        name = "Switch Theme..."
        if (match := matcher.match(name)) > 0:
            yield Hit(
                match,
                matcher.highlight(name),
                self.app.action_search_themes,
                help="Open the theme selection menu",
            )

        # Clear Cache
        name = "Clear Cache"
        if (match := matcher.match(name)) > 0:
            yield Hit(
                match,
                matcher.highlight(name),
                self.app.action_clear_cache,
                help="Remove all cached images and diagrams",
            )


class TextualMarkdownApp(App):
    """A Textual app to view Markdown files with Vim-like motions and theme support."""

    # Load base styles and default style
    CSS_PATH = [
        str(_PACKAGE_DIR / "styles.tcss"),
        str(_PACKAGE_DIR / "styles" / "obsidian.tcss"),
    ]
    ENABLE_COMMAND_PALETTE = True
    COMMANDS = {MainCommandProvider}

    current_style = reactive("obsidian")

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("t", "toggle_sidebar", "Toggle Sidebar", show=True),
        Binding("/", "search", "Search", show=False),
        Binding("n", "find_next", "Find Next", show=False),
        Binding("N", "find_prev", "Find Prev", show=False),
        Binding("j", "scroll_down", "Scroll Down", show=False),
        Binding("k", "scroll_up", "Scroll Up", show=False),
        Binding("h", "scroll_left", "Scroll Left", show=False),
        Binding("l", "scroll_right", "Scroll Right", show=False),
        Binding("g", "scroll_top", "Scroll to Top", show=False),
        Binding("G", "scroll_bottom", "Scroll to Bottom", show=False),
        Binding("ctrl+p", "command_palette", "Command Palette", show=True),
        Binding("escape", "hide_search", "Hide Search", show=False),
        Binding("ctrl+o", "back", "Back", show=False),
        Binding("ctrl+i", "forward", "Forward", show=False),
        Binding("ctrl+u", "scroll_half_up", "Half Page Up", show=False),
        Binding("ctrl+d", "scroll_half_down", "Half Page Down", show=False),
    ]

    def __init__(self, file_path: Path | None = None):
        super().__init__()
        self.file_path = file_path
        # Set dynamic title with filename
        if file_path:
            self.title = f"Flint - {file_path.name}"
        else:
            self.title = "Flint"
        self.markdown_content: str = ""  # Store for search
        self.search_results: list[Widget] = []
        self.current_search_index: int = -1
        self.search_query: str = ""
        self.history: list[Path] = []
        self.forward_stack: list[Path] = []
        self._loaded_styles: set[str] = {"obsidian"}  # Track loaded styles
        self._highlighted_blocks: set[Widget] = (
            set()
        )  # Track blocks with search highlights

    def compose(self) -> ComposeResult:
        from .custom_markdown import CustomMarkdownViewer

        yield Header()
        # Create empty viewer - content will be loaded asynchronously
        # Sidebar hidden by default, toggle with 't' key
        yield CustomMarkdownViewer("", show_table_of_contents=False)
        yield Input(
            placeholder="Search document...", id="search-input", classes="hidden"
        )
        yield Footer()

    def watch_current_style(self, old_style: str, new_style: str) -> None:
        """Update the app's class when the style changes."""
        self.remove_class(f"style-{old_style}")
        self.add_class(f"style-{new_style}")

    def on_mount(self) -> None:
        """Load content asynchronously and apply style."""
        self.add_class(f"style-{self.current_style}")
        # Load content asynchronously if we have a file path
        if self.file_path:
            self.load_document()

    @work(exclusive=True)
    async def load_document(self) -> None:
        """Load the markdown document asynchronously (Frogmouth pattern)."""
        from .custom_markdown import CustomMarkdownViewer

        try:
            viewer = self.query_one(CustomMarkdownViewer)

            # Load content asynchronously
            await viewer.load(self.file_path)

            # Store content for search
            if self.file_path and self.file_path.exists():
                import asyncio

                self.markdown_content = await asyncio.to_thread(
                    self.file_path.read_text, encoding="utf-8"
                )

            # Focus the viewer
            viewer.focus()

        except Exception as e:
            self.notify(f"Error loading document: {e}", severity="error")

    def action_switch_style(self, style_id: str) -> None:
        """Switch to a new visual style, lazy loading CSS if needed."""
        # Lazy load the style CSS if not already loaded
        if style_id not in self._loaded_styles:
            style_path = _PACKAGE_DIR / "styles" / f"{style_id}.tcss"
            try:
                self.stylesheet.read(str(style_path))
                self._loaded_styles.add(style_id)
            except Exception as e:
                self.notify(f"Failed to load style: {e}", severity="error")
                return

        self.current_style = style_id
        self.notify(f"Switched to {style_id.capitalize()} style")

    def action_search_styles(self) -> None:
        """Show a command palette for visual styles."""
        self.push_screen(
            CommandPalette(
                providers=[StyleProvider],
                placeholder="Search for styles...",
            )
        )

    def action_search_themes(self) -> None:
        """Show a command palette for themes."""
        self.push_screen(
            CommandPalette(
                providers=[ThemeProvider],
                placeholder="Search for themes...",
            )
        )

    def action_toggle_sidebar(self) -> None:
        from .custom_markdown import CustomMarkdownViewer

        viewer = self.query_one(CustomMarkdownViewer)
        viewer.show_table_of_contents = not viewer.show_table_of_contents

    def action_switch_user_theme(self, tcss_path: str) -> None:
        """Switch to a user-defined theme from a TCSS file."""
        self.stylesheet.read(tcss_path)
        self.notify(f"Loaded user theme: {Path(tcss_path).stem}")

    def action_clear_cache(self) -> None:
        """Remove all cached images and diagrams."""
        from .config import CACHE_DIR
        import shutil

        try:
            if CACHE_DIR.exists():
                # Remove all files in cache directory
                for item in CACHE_DIR.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                self.notify("Cache cleared successfully")
            else:
                self.notify("Cache directory is empty")
        except Exception as e:
            self.notify(f"Failed to clear cache: {e}", severity="error")

    def action_search(self) -> None:
        search_input = self.query_one("#search-input", Input)
        search_input.remove_class("hidden")
        search_input.focus()

    def action_hide_search(self) -> None:
        search_input = self.query_one("#search-input", Input)
        if not search_input.has_class("hidden"):
            search_input.add_class("hidden")
            from .custom_markdown import CustomMarkdownViewer

            self.query_one(CustomMarkdownViewer).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            query = event.value.lower()
            if query:
                self.perform_search(query)
            else:
                self.clear_highlights()
                self.search_results = []
                self.current_search_index = -1

            self.action_hide_search()

    @work(exclusive=True)
    async def perform_search(self, query: str) -> None:
        """Perform search in a background worker."""
        self.search_query = query
        self.search_results = []
        self.current_search_index = -1

        # Clear previous highlights
        self.clear_highlights()

        if not self.search_query:
            return

        from .custom_markdown import CustomMarkdownViewer, CustomMarkdown
        from textual.widgets._markdown import MarkdownBlock

        try:
            viewer = self.query_one(CustomMarkdownViewer)
            markdown = viewer.query_one(CustomMarkdown)
        except Exception:
            return

        # Find all matching blocks in a single pass
        lines = self.markdown_content.splitlines()
        matching_line_indices = {
            i for i, line in enumerate(lines) if self.search_query in line.lower()
        }

        blocks = list(markdown.walk_children(MarkdownBlock))

        for block in blocks:
            found = False
            # Check source range
            if block.source_range:
                start, end = block.source_range
                for line_idx in range(start, end):
                    if line_idx in matching_line_indices:
                        found = True
                        break

            # Fallback: search rendered text
            if not found and hasattr(block, "_content"):
                if self.search_query in block._content.plain.lower():
                    found = True

            if found:
                self.search_results.append(block)

        if self.search_results:
            self.apply_highlights()
            self.current_search_index = 0
            self.jump_to_match()
        else:
            self.notify(
                f"No matches found for '{self.search_query}'", severity="warning"
            )

    def clear_highlights(self) -> None:
        """Clear all search highlights efficiently."""
        while self._highlighted_blocks:
            block = self._highlighted_blocks.pop()
            try:
                if hasattr(block, "_content"):
                    # Reset content to remove styles
                    block._content.stylize_before(0, len(block._content), "")
                    block.update(block._content)
            except Exception:
                pass

    def apply_highlights(self) -> None:
        if not self.search_query:
            return

        for block in self.search_results:
            if hasattr(block, "_content"):
                plain = block._content.plain.lower()
                start = 0
                highlighted = False
                while True:
                    idx = plain.find(self.search_query, start)
                    if idx == -1:
                        break
                    # Apply highlight style
                    block._content.stylize_before(
                        idx, idx + len(self.search_query), "reverse"
                    )
                    start = idx + len(self.search_query)
                    highlighted = True

                if highlighted:
                    block.update(block._content)
                    self._highlighted_blocks.add(block)

    def jump_to_match(self) -> None:
        if 0 <= self.current_search_index < len(self.search_results):
            from .custom_markdown import CustomMarkdownViewer, CustomMarkdown

            viewer = self.query_one(CustomMarkdownViewer)
            block = self.search_results[self.current_search_index]

            # Ensure the block is visible if it's in a collapsed section
            markdown = viewer.query_one(CustomMarkdown)
            markdown.ensure_visible(block)

            viewer.scroll_to_widget(block)

            # Highlight current match distinctly
            # We re-apply all highlights first to clear previous "current" highlight
            self.apply_highlights()
            if hasattr(block, "_content"):
                plain = block._content.plain.lower()
                idx = plain.find(self.search_query)
                if idx != -1:
                    block._content.stylize_before(
                        idx, idx + len(self.search_query), "bold reverse underline"
                    )
                    block.update(block._content)

            self.notify(
                f"Match {self.current_search_index + 1} of {len(self.search_results)}"
            )

    def action_find_next(self) -> None:
        if self.search_results:
            self.current_search_index = (self.current_search_index + 1) % len(
                self.search_results
            )
            self.jump_to_match()

    def action_find_prev(self) -> None:
        if self.search_results:
            self.current_search_index = (self.current_search_index - 1) % len(
                self.search_results
            )
            self.jump_to_match()

    def action_scroll_down(self) -> None:
        from .custom_markdown import CustomMarkdownViewer

        viewer = self.query_one(CustomMarkdownViewer)
        viewer.scroll_down()

    def action_scroll_up(self) -> None:
        from .custom_markdown import CustomMarkdownViewer

        viewer = self.query_one(CustomMarkdownViewer)
        viewer.scroll_up()

    def action_scroll_left(self) -> None:
        from .custom_markdown import CustomMarkdownViewer

        viewer = self.query_one(CustomMarkdownViewer)
        viewer.scroll_left()

    def action_scroll_right(self) -> None:
        from .custom_markdown import CustomMarkdownViewer

        viewer = self.query_one(CustomMarkdownViewer)
        viewer.scroll_right()

    def action_scroll_top(self) -> None:
        from .custom_markdown import CustomMarkdownViewer

        viewer = self.query_one(CustomMarkdownViewer)
        viewer.scroll_home()

    def action_scroll_bottom(self) -> None:
        from .custom_markdown import CustomMarkdownViewer

        viewer = self.query_one(CustomMarkdownViewer)
        viewer.scroll_end()

    def action_scroll_half_up(self) -> None:
        from .custom_markdown import CustomMarkdownViewer

        viewer = self.query_one(CustomMarkdownViewer)
        viewer.scroll_page_up(duration=0.1)

    def action_scroll_half_down(self) -> None:
        from .custom_markdown import CustomMarkdownViewer

        viewer = self.query_one(CustomMarkdownViewer)
        viewer.scroll_page_down(duration=0.1)

    async def action_back(self) -> None:
        if self.history:
            current = self.file_path
            if current:
                self.forward_stack.append(current)
            prev = self.history.pop()
            self.file_path = prev
            await self.reload_content()

    async def action_forward(self) -> None:
        if self.forward_stack:
            current = self.file_path
            if current:
                self.history.append(current)
            next_path = self.forward_stack.pop()
            self.file_path = next_path
            await self.reload_content()

    def action_quit(self) -> None:
        """Quit the application immediately."""
        # Cancel all background workers to prevent hanging
        self.workers.cancel_all()
        # Force exit
        self.exit()

    async def reload_content(self) -> None:
        """Reload content using async pattern."""
        if self.file_path and self.file_path.exists():
            from .custom_markdown import CustomMarkdownViewer

            viewer = self.query_one(CustomMarkdownViewer)
            # Use async load pattern
            await viewer.document.load(self.file_path)
            # Store content for search
            import asyncio

            self.markdown_content = await asyncio.to_thread(
                self.file_path.read_text, encoding="utf-8"
            )
            viewer.scroll_home(animate=False)


def main():
    """Main entry point for the application."""
    file_arg = sys.argv[1] if len(sys.argv) > 1 else None
    path = Path(file_arg) if file_arg else None
    app = TextualMarkdownApp(path)
    app.run()


if __name__ == "__main__":
    main()
