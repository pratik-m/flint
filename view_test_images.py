#!/usr/bin/env python3
"""View the test mermaid images in the terminal."""

from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import VerticalScroll
from textual_image.widget import Image as ImageWidget

class ImageViewerApp(App):
    """Simple app to view test images."""

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            # Find all test images
            test_images = sorted(Path(".").glob("test_mermaid_*.png"))

            if not test_images:
                yield Static("[red]No test images found! Run test_mermaid.py first.[/red]")
            else:
                for img_path in test_images:
                    # Get image dimensions
                    from PIL import Image
                    with Image.open(img_path) as pil_img:
                        width, height = pil_img.size

                    # Display info
                    info_text = f"\n[bold cyan]{img_path.name}[/bold cyan]\n"
                    info_text += f"[dim]Dimensions: {width}x{height}px[/dim]\n"
                    yield Static(info_text)

                    # Display image with max height
                    img = ImageWidget(str(img_path))
                    img.styles.width = "auto"
                    img.styles.height = "auto"
                    img.styles.max_height = 30  # Limit height
                    img.styles.margin = (0, 0, 2, 0)
                    yield img

                    # Separator
                    yield Static("[dim]" + "─" * 60 + "[/dim]")

        yield Footer()

if __name__ == "__main__":
    app = ImageViewerApp()
    app.run()
