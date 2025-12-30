#!/usr/bin/env python3
"""Test script to debug mermaid.ink rendering."""

import base64
import requests
from pathlib import Path

# Simple test mermaid diagram
MERMAID_CODE = """
graph TD
    A[Start] --> B[Process]
    B --> C[End]
"""

def test_mermaid_url(params_str, description):
    """Test a mermaid.ink URL with given parameters."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Params: {params_str}")
    print(f"{'='*60}")

    # Encode mermaid code
    encoded = base64.urlsafe_b64encode(MERMAID_CODE.strip().encode('utf-8')).decode('ascii')

    # Build URL
    url = f"https://mermaid.ink/img/{encoded}"
    if params_str:
        url += f"?{params_str}"

    print(f"URL: {url[:100]}...")

    try:
        # Make request
        response = requests.get(url, timeout=10)

        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")

        if response.status_code == 200:
            size_kb = len(response.content) / 1024
            print(f"Size: {size_kb:.1f} KB")

            # Save to file
            output_file = Path(f"test_mermaid_{description.replace(' ', '_')}.png")
            with open(output_file, "wb") as f:
                f.write(response.content)
            print(f"✓ Saved to: {output_file}")

            # Try to get image dimensions
            try:
                from PIL import Image
                with Image.open(output_file) as img:
                    print(f"Dimensions: {img.width}x{img.height} pixels")
            except Exception as e:
                print(f"Could not read dimensions: {e}")
        else:
            print(f"✗ FAILED")
            error_body = response.text[:500]
            print(f"Error: {error_body}")

    except Exception as e:
        print(f"✗ Exception: {e}")

def main():
    print("Mermaid.ink API Testing")
    print("="*60)
    print("Test diagram:")
    print(MERMAID_CODE)

    # Test different parameter combinations
    tests = [
        ("", "no parameters (default)"),
        ("bgColor=transparent", "transparent background only"),
        ("width=800", "width 800"),
        ("width=1200", "width 1200"),
        ("width=1600", "width 1600"),
        ("scale=2", "scale 2 only (might fail)"),
        ("width=1200&scale=2", "width 1200 with scale 2"),
        ("bgColor=transparent&width=1200", "transparent + width 1200"),
        ("bgColor=transparent&width=1200&scale=2", "all params"),
    ]

    for params, desc in tests:
        test_mermaid_url(params, desc)

    print("\n" + "="*60)
    print("Testing complete! Check the generated PNG files.")
    print("="*60)

if __name__ == "__main__":
    main()
