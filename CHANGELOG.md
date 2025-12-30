# Changelog

All notable changes to Flint will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-12-30

### Changed
- Updated README with correct `uvx` command: `uvx --from flint-markdown-viewer flint`
- Added GitHub repository URLs to package metadata

## [0.1.0] - 2025-12-30

### Added
- Initial release of Flint Markdown Viewer
- **Interactive Tables**: Markdown tables rendered as interactive DataTable widgets with row selection and hover effects
- **High-Resolution Images**: Crystal clear image rendering using Terminal Graphics Protocol (TGP)
- **Mermaid Diagrams**: Full support for Mermaid diagrams (flowcharts, sequence diagrams, etc.)
- **Obsidian-Style Callouts**: Support for `> [!INFO]` and `> **Type**` callouts with automatic icons
- **Multiple Visual Styles & Themes**: Obsidian, Cyberpunk, Retro, Blueprint, Minimal styles with Textual color themes (Gruvbox, Nord, Dracula, etc.)
- **Vim-like Navigation**: Navigate with j/k, gg/G, Ctrl+U/D for smooth scrolling
- **Command Palette**: Quick access to themes and styles via Ctrl+P
- **XDG Compliance**: Config and cache follow XDG Base Directory specification
- **Image Caching**: Persistent caching of images and Mermaid diagrams for faster subsequent loads

### Performance
- Async image and Mermaid rendering to prevent UI blocking
- Lazy import of heavy dependencies for faster startup
- Pre-compiled regex patterns for efficient text processing
- Background workers for search and rendering operations

### Developer Features
- Clean package structure for easy installation via pip/pipx/uvx
- Comprehensive documentation in CLAUDE.md
- MIT License
