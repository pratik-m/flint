"""Test the fast markdown viewer."""

import sys
from pathlib import Path
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from fast_viewer import FastMarkdownViewer


class FastMarkdownApp(App):
    """Fast markdown viewer app."""

    CSS = """
    FastMarkdownViewer {
        width: 1fr;
        height: 1fr;
    }
    """

    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path

    def compose(self) -> ComposeResult:
        yield Header()
        yield FastMarkdownViewer()
        yield Footer()

    def on_mount(self) -> None:
        """Load content asynchronously."""
        self.load_content()

    @work(exclusive=True)
    async def load_content(self) -> None:
        """Load the markdown file."""
        viewer = self.query_one(FastMarkdownViewer)
        await viewer.load(self.file_path)
        viewer.focus()


if __name__ == "__main__":
    file_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if not file_arg:
        print("Usage: python test_fast.py <markdown-file>")
        sys.exit(1)

    path = Path(file_arg)
    app = FastMarkdownApp(path)
    app.run()
