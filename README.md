# 🔥 Flint: The Premium Markdown Viewer

Flint is a premium, terminal-based Markdown viewer built with [Textual](https://textual.textualize.io/). Designed for speed, aesthetics, and a seamless Obsidian-like experience in your terminal.

## ✨ Features

- **📊 Interactive Tables**: Markdown tables are rendered as interactive `DataTable` widgets with row selection, hover effects, and smooth scrolling.
- **🖼️ High-Res Images**: Crystal clear image rendering using the Terminal Graphics Protocol (TGP).
- **🧜 Mermaid Diagrams**: Full support for Mermaid diagrams (flowcharts, sequence diagrams, etc.) rendered directly in the terminal.
- **📝 Obsidian-Style Callouts**: Support for `> [!INFO]` and `> **Type**` callouts with automatic icons and distinct styling.
- **🎨 Visual Styles & Themes**: Multiple built-in styles (**Obsidian**, **Cyberpunk**, **Retro**, **Blueprint**, **Minimal**) and color themes (**Gruvbox**, **Nord**, **Dracula**, etc.).
- **⌨️ Vim-like Navigation**: Navigate with `j/k`, `gg/G`, `Ctrl+U/D` for smooth scrolling.

## 🚀 Installation

### Using `pip`
```bash
pip install flint-markdown-viewer
```

### Using `pipx` (Recommended for CLI tools)
```bash
pipx install flint-markdown-viewer
```

### Using `uv` (Fastest)
```bash
uv tool install flint-markdown-viewer
```

## 📖 Usage

Simply run `flint` followed by the path to your Markdown file:

```bash
flint your-file.md
```

### Key Bindings

| Key | Action |
| --- | --- |
| `q` | Quit |
| `j` / `k` | Scroll Down / Up |
| `g` / `G` | Scroll to Top / Bottom |
| `Ctrl+U` / `Ctrl+D` | Scroll Half Page Up / Down |
| `Ctrl+P` | Open Command Palette (Switch Styles/Themes) |

## 🛠️ Configuration

The app follows XDG standards:
- **Config Directory**: `~/.config/textual-md-viewer/`
- **Cache Directory**: `~/.cache/textual-md-viewer/` (images and Mermaid diagrams)

### Styles vs Themes

Flint has a two-layer visual customization system:

**Themes** (Color Schemes): Control the color palette of the app. Examples: `gruvbox`, `nord`, `dracula`, `catppuccin`. These are built into Textual and affect the overall color scheme across the entire interface.

**Styles** (Layout & Formatting): Control the visual layout, spacing, borders, typography, and overall aesthetic. Examples: `Obsidian`, `Minimal`, `Blueprint`, `Retro`, `Cyberpunk`. These are custom TCSS files in `flint/styles/` that define how Markdown elements are displayed.

You can mix and match any theme with any style. Access both via the Command Palette (`Ctrl+P`).

## ⚠️ Known Issues

- **Initial Render**: On first launch, you may need to trigger a mouse move or key press for the content to render properly. This is a known Textual framework issue with async rendering.
- **Style Switching**: Switching between styles may occasionally require reloading the document to fully apply changes.

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.