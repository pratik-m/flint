"""Fast markdown viewer using Rich rendering instead of Textual's widget-heavy approach."""

from pathlib import Path
from rich.markdown import Markdown as RichMarkdown
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static


class FastMarkdownViewer(VerticalScroll):
    """A fast markdown viewer using Rich rendering (single widget)."""

    def __init__(self, content: str = "", **kwargs):
        super().__init__(**kwargs)
        self._content = content

    def compose(self) -> ComposeResult:
        """Compose with a single Static widget."""
        if self._content:
            yield Static(RichMarkdown(self._content))
        else:
            yield Static("# Loading...\n\nPlease wait.")

    async def load(self, path: Path) -> None:
        """Load markdown from a file."""
        content = path.read_text(encoding="utf-8")
        # Update the static widget with rendered markdown
        static = self.query_one(Static)
        static.update(RichMarkdown(content))
        self.scroll_home(animate=False)
