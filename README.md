# 🔥 Flint: The Premium Markdown Viewer

Flint is a premium, terminal-based Markdown viewer built with [Textual](https://textual.textualize.io/). Designed for speed, aesthetics, and a seamless Obsidian-like experience in your terminal.

## ✨ Features

- **📊 Interactive Tables**: Markdown tables are rendered as interactive `DataTable` widgets with row selection, hover effects, and smooth scrolling.
- **🖼️ High-Res Images**: Crystal clear image rendering using the Terminal Graphics Protocol (TGP).
- **🧜 Mermaid Diagrams**: Full support for Mermaid diagrams (flowcharts, sequence diagrams, etc.) rendered directly in the terminal.
- **📝 Obsidian-Style Callouts**: Support for `> [!INFO]` and `> **Type**` callouts with automatic icons and distinct styling.
- **📂 Collapsible Headers**: Click on any header to collapse or expand the section beneath it.
- **🔍 Fast Async Search**: Search through large documents with background processing and instant highlight clearing.
- **🎨 Visual Styles**: Multiple built-in themes including **Obsidian**, **Cyberpunk**, **Retro**, **Blueprint**, and **Minimal**.
- **⌨️ Vim-like Navigation**: Navigate with `j/k`, `gg/G`, `Ctrl+U/D`, and maintain history with `Ctrl+O/I`.

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
| `t` | Toggle Sidebar (Table of Contents) |
| `/` | Search |
| `n` / `N` | Next / Previous Search Match |
| `j` / `k` | Scroll Down / Up |
| `g` / `G` | Scroll to Top / Bottom |
| `Ctrl+P` | Open Command Palette (Switch Styles/Themes) |
| `Ctrl+O` / `Ctrl+I` | Back / Forward in History |

## 🛠️ Configuration

The app follows XDG standards:
- **Themes**: Place your custom `.tcss` files in `~/.config/textual-md-viewer/themes/`.
- **Cache**: Images and diagrams are cached in `~/.cache/textual-md-viewer/`.

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.