# Flint: The Markdown Viewer in your terminal!

Flint is a terminal-based Markdown viewer built with [Textual](https://textual.textualize.io/). Inspired by [Frogmouth](https://github.com/Textualize/frogmouth), it adds support for Mermaid rendering, image rendering and tables displayed as native Textual data tables for an improved viewing experience.


## 📸 Screenshots

![Screenshot 1](screenshots/screenshot1.png)
_Flint with default Obsidian style_

![Screenshot 2](screenshots/screenshot2.png)
_Retro style theme showcase_

![Screenshot 3](screenshots/screenshot3.png)
_Cyberpunk style theme showcase_

![Screenshot 4](screenshots/screenshot4.png)
_Interactive tables rendered as native Textual DataTable widgets_

![Screenshot 5](screenshots/screenshot5.png)
_High-resolution image rendering with Terminal Graphics Protocol_

![Screenshot 6](screenshots/screenshot6.png)
_Mermaid diagram rendered natively in the terminal_

![Screenshot 7](screenshots/screenshot7.png)
_Obsidian-style callouts with automatic icons_

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
# One-time run
uvx --from flint-markdown-viewer flint your-file.md

# Or install globally
uv tool install flint-markdown-viewer
```

## 📖 Usage

Simply run `flint` followed by the path to your Markdown file:

```bash
flint your-file.md
```

### Key Bindings

| Key                 | Action                                      |
| ------------------- | ------------------------------------------- |
| `q`                 | Quit                                        |
| `j` / `k`           | Scroll Down / Up                            |
| `g` / `G`           | Scroll to Top / Bottom                      |
| `Ctrl+U` / `Ctrl+D` | Scroll Half Page Up / Down                  |
| `Ctrl+P`            | Open Command Palette (Switch Styles/Themes) |


### Styles vs Themes

Flint has a two-layer visual customization system:

**Themes** (Color Schemes): Control the color palette of the app. Examples: `gruvbox`, `nord`, `dracula`, `catppuccin`. These are built into Textual and affect the overall color scheme across the entire interface.

**Styles** (Layout & Formatting): Control the visual layout, spacing, borders, typography, and overall aesthetic. Examples: `Obsidian`, `Minimal`, `Blueprint`, `Retro`, `Cyberpunk`. These are custom TCSS files in `flint/styles/` that define how Markdown elements are displayed.

You can mix and match any theme with any style. Access both via the Command Palette (`Ctrl+P`).

## ⚠️ Known Issues

- **Initial Render**: On app launch, you may need to trigger a mouse move or key press for the content to render properly. This issue is being looked into.
- **Style Switching**: Switching between styles may occasionally require reloading the document to fully apply changes.

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

