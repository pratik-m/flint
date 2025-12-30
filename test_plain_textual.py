"""Test plain Textual Markdown (Frogmouth approach) - no customization."""

import sys
from pathlib import Path
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Markdown
from textual.containers import VerticalScroll


class PlainTextualMarkdownApp(App):
    """Plain Textual Markdown - exactly like Frogmouth, no customization."""

    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path

    def compose(self) -> ComposeResult:
        yield Header()
        # Plain Markdown widget with placeholder - exactly like Frogmouth
        yield Markdown("# Loading...\n\nPlease wait.")
        yield Footer()

    def on_mount(self) -> None:
        """Load content asynchronously."""
        self.load_content()

    @work(exclusive=True)
    async def load_content(self) -> None:
        """Load markdown using Textual's built-in async load."""
        try:
            markdown = self.query_one(Markdown)
            # Use Textual's async load - like Frogmouth
            await markdown.load(self.file_path)
            markdown.scroll_home(animate=False)
            markdown.focus()
            self.log("Content loaded successfully")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")


if __name__ == "__main__":
    file_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if not file_arg:
        print("Usage: python test_plain_textual.py <markdown-file>")
        sys.exit(1)

    path = Path(file_arg)
    app = PlainTextualMarkdownApp(path)
    app.run()
