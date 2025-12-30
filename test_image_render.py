#!/usr/bin/env python3
"""Test script to debug image rendering with TGPImage."""

from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import VerticalScroll
from textual_image.widget import TGPImage
from PIL import Image as PILImage
import hashlib
import requests
import io

# Test with one of the Unsplash images from test.md
TEST_URL = "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee"

class ImageTestApp(App):
    """Simple app to test image rendering."""

    CSS = """
    Screen {
        background: $surface;
    }

    #info {
        margin: 1;
        padding: 1;
        background: $panel;
    }

    #test-image {
        margin: 1 0;
        width: auto;
        height: auto;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            yield Static(
                f"[bold cyan]Testing Image Rendering[/bold cyan]\n"
                f"URL: {TEST_URL[:60]}...\n"
                f"Downloading and resizing to 800px width...",
                id="info"
            )
            yield Static("Loading...", id="status")
        yield Footer()

    def on_mount(self) -> None:
        """Download and display image on mount."""
        self.load_and_display_image()

    def load_and_display_image(self) -> None:
        """Download, resize, and display the test image."""
        try:
            status = self.query_one("#status", Static)

            # Download image
            status.update("[yellow]Downloading image...[/yellow]")
            self.log(f"Downloading: {TEST_URL}")
            response = requests.get(TEST_URL, timeout=15)

            if response.status_code != 200:
                status.update(f"[red]Download failed: HTTP {response.status_code}[/red]")
                return

            # Load and get original size
            img = PILImage.open(io.BytesIO(response.content))
            original_size = f"{img.width}x{img.height}"
            self.log(f"Original size: {original_size}")

            # Resize to 800px width
            MAX_WIDTH = 800
            if img.width > MAX_WIDTH:
                status.update("[yellow]Resizing to 800px width...[/yellow]")
                ratio = MAX_WIDTH / img.width
                new_height = int(img.height * ratio)
                img = img.resize((MAX_WIDTH, new_height), PILImage.Resampling.LANCZOS)
                resized_size = f"{img.width}x{img.height}"
                self.log(f"Resized to: {resized_size}")

            # Save to temp file
            cache_dir = Path.home() / ".cache" / "textual-md-viewer"
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_key = hashlib.md5(TEST_URL.encode()).hexdigest()
            cache_path = cache_dir / f"test_{cache_key}.png"

            status.update("[yellow]Saving to cache...[/yellow]")
            img.save(cache_path, "PNG", optimize=True)
            size_kb = cache_path.stat().st_size / 1024
            self.log(f"Saved to: {cache_path} ({size_kb:.1f}KB)")

            # Display using TGPImage
            status.update("[yellow]Rendering with TGPImage...[/yellow]")
            self.log("Creating TGPImage widget")

            # Update status with info
            status.update(
                f"[green]✓ Image loaded successfully[/green]\n\n"
                f"Original: {original_size}\n"
                f"Resized: {img.width}x{img.height}px\n"
                f"Cache: {size_kb:.1f}KB\n"
                f"Path: {cache_path.name}"
            )

            # Mount the image
            scroll = self.query_one(VerticalScroll)
            test_img = TGPImage(str(cache_path), id="test-image")
            scroll.mount(test_img)

            self.log("✓ Image displayed")

        except Exception as e:
            self.log(f"✗ Error: {e}")
            import traceback
            self.log(traceback.format_exc())
            status.update(f"[red]✗ Error: {e}[/red]")


if __name__ == "__main__":
    app = ImageTestApp()
    app.run()
