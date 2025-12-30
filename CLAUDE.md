# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A terminal-based Markdown viewer built with Textual that supports advanced features like Mermaid diagrams, collapsible sections, Vim-like navigation, and multiple visual themes/styles.

## Running the Application

```bash
# Run with a specific markdown file
python app.py sample.md

# Run the app (alternative entry point)
python app.py
```

## Dependencies

Managed via `uv` package manager. Install dependencies:

```bash
uv sync
```

Key dependencies:
- `textual`: TUI framework
- `textual-image`: Image rendering in terminal
- `mermaid-py`: Mermaid diagram support
- `pillow`, `term-image`: Image processing
- `platformdirs`: XDG directory support

## Architecture

### CRITICAL: Rendering Architecture Decision

**Performance Investigation:**
Initial implementation used `CustomMarkdown` class that extended Textual's `Markdown` widget with:
- Custom BLOCKS (SmartMarkdownFence for Mermaid)
- Header processing in `on_mount` (adding collapse icons to all headers)
- Custom styling and collapsible sections

This caused **3-5 second load times** for a 301-line document.

**Root Cause:**
The customizations themselves were the bottleneck, NOT Textual's Markdown widget. Testing plain Textual `Markdown` (like Frogmouth uses) showed **split-second loading**.

**Solution: Plain Textual Markdown (Frogmouth Approach)**
Use Textual's `MarkdownViewer` widget as-is, without heavy customizations:
- ✅ **Fast loading** - Split second vs 3-5 seconds
- ✅ **All features work** - Built-in TOC, vim navigation, search, themes
- ✅ **Clean formatting** - Default Textual Markdown styling
- ✅ **Simple and maintainable** - Don't fight the framework

**What We Removed (The Slow Stuff):**
- ❌ `CustomMarkdown` class with custom BLOCKS
- ❌ `SmartMarkdownFence` (Mermaid support - will add back optimized later)
- ❌ Header icon processing in `on_mount`
- ❌ Collapsible sections
- ❌ Custom style files (obsidian.tcss, minimal.tcss, etc.)

**Key Lesson:**
**Don't fight Textual's Markdown widget - use it as-is.** Extending it with custom blocks and on_mount processing creates performance bottlenecks. Follow Frogmouth's example: plain `Markdown` widget + async loading.

**Implementation:**
- `CustomMarkdownViewer`: Thin wrapper around `MarkdownViewer`
- Uses Textual's built-in async `load()` method
- Async loading with `@work(exclusive=True)` pattern (from Frogmouth)
- No custom blocks, no mount processing, no custom styles

### Core Components

**app.py** - Main application entry point
- `TextualMarkdownApp`: Main Textual app class that orchestrates the viewer
- Command palette providers: `ThemeProvider`, `StyleProvider`, `MainCommandProvider`
- Implements vim-like keybindings, search functionality, and navigation history
- Uses async loading pattern with `@work` decorator for fast startup

**custom_markdown.py** - Markdown rendering (simplified)
- `CustomMarkdownViewer`: Thin wrapper around Textual's `MarkdownViewer`
- Provides `document` property and `load()` method for compatibility
- No custom blocks, no customizations - keeps it fast and simple
- Legacy code (CustomMarkdown, SmartMarkdownFence) remains but is unused

**config.py** - Configuration and directory management
- Uses `platformdirs` for XDG-compliant config/cache directories
- Config dir: `~/.config/textual-md-viewer/`
- Cache dir: `~/.cache/textual-md-viewer/` (defined but may not be used correctly)
- Themes dir: `~/.config/textual-md-viewer/themes/`
- Settings stored in JSON format

### Visual System

The app has a two-layer visual system:

1. **Themes** (Textual built-in): Color schemes like "gruvbox", "nord", "dracula"
2. **Styles** (Custom TCSS): Layout and formatting variants in `styles/` directory
   - `obsidian.tcss`: Obsidian-like appearance (primary style)
   - `minimal.tcss`: Clean, minimal design
   - `academic.tcss`: Academic paper style
   - `ascii.tcss`: ASCII art headers (LOWEST PRIORITY - experimental)

Styles are applied via reactive classes (`.style-obsidian`, etc.) and can be switched at runtime via command palette.

### Key Features Implementation

**Collapsible Sections**: Headers can be clicked to collapse/expand content. Tracking via `_collapsed_headers` set using object IDs. Icons (▼/▶) indicate state.

**Search**: Full-text search with highlight via Input widget at bottom. Results tracked in `search_results` list, navigable with n/N keys.

**Vim Navigation**:
- j/k/h/l for scrolling
- gg/G for top/bottom
- Ctrl+U/D for half-page scroll
- Ctrl+O/I for back/forward navigation

**History**: File navigation tracked in `history` list with `forward_stack` for forward navigation.

**Mermaid Diagrams**: Rendered asynchronously using `@work(thread=True)` decorator. Images cached by MD5 hash of diagram source. Loading indicator shown during render.

**Image Caching**: Images (both inline and Mermaid diagrams) should be cached persistently to improve performance on subsequent loads.

## Performance Considerations

**CRITICAL**: Performance is a top priority for this application.

- **Lazy Loading**: Heavy imports are deferred to function level to speed up app startup
- **Caching**: All images and Mermaid diagrams MUST be cached persistently
- **Regex Optimization**: Use pre-compiled regex patterns (e.g., `_HEADER_CLEANUP_RE`)
- **Minimal Rendering**: Avoid unnecessary container nesting
- **Thread-Safe Updates**: Mermaid rendering uses `@work(thread=True)` and `app.call_from_thread()` to avoid blocking the UI
- **Startup Speed**: Application must load and close quickly - avoid expensive operations at import time

When making changes:
- Always profile performance impact
- Prefer async/background workers for I/O operations
- Minimize widget hierarchy depth
- Cache expensive computations
- Test startup time after changes

## Important Patterns

**Lazy Loading**: Heavy imports (CustomMarkdownViewer, CustomMarkdown) are imported at function level to speed up app startup.

**Thread-Safe Updates**: Mermaid rendering uses `app.call_from_thread()` to safely update UI from worker threads.

**Content Updates**: When modifying MarkdownBlock content, always call `block.update(block._content)` after changing `_content`.

**Header State**: Headers maintain `_original_text` attribute to preserve clean text when toggling collapse icons.

## File Structure

```
app.py                 # Main application
custom_markdown.py     # Custom Markdown widgets
config.py             # Config/cache management
styles.tcss           # Base styles
styles/               # Visual style variants
  obsidian.tcss       # Primary style
  minimal.tcss
  academic.tcss
  ascii.tcss          # LOWEST PRIORITY
test_*.py             # Development test files
```

## Command Palette

Access via Ctrl+P:
- "Switch Style..." - Opens style picker
- "Switch Theme..." - Opens theme picker
- "Clear Cache" - Remove cached diagrams (currently disabled)

## Development Workflow

**Git Commits**: Commit changes as you go. Make small, atomic commits for each feature or fix. Don't accumulate large changesets. Use clear, descriptive commit messages.

**Testing**: Test files (`test_*.py`) are used for development/debugging. Run the app with different markdown files to verify changes.

---

## CURRENT ISSUES AND PAIN POINTS

### Critical Performance Issues

1. **Slow Startup Time**
   - App takes a long time to open
   - Likely caused by:
     - CSS loading all 5 files (styles.tcss + 4 style variants) at startup
     - Heavy imports not properly lazy-loaded
     - Image/Mermaid processing happening at startup
     - On-mount operations in CustomMarkdown (adding icons to all headers)

2. **App Reopens When Pressing 'q' to Quit**
   - Severe bug: hitting 'q' to quit causes app to reopen instead of exiting
   - Needs investigation in quit action handling
   - May be related to app lifecycle or binding issues

3. **Cache Implementation Issues**
   - Cache directory hardcoded to `/tmp/textual-md-viewer-cache` in custom_markdown.py:11
   - config.py defines proper cache directory via platformdirs but it's not used
   - Inconsistent cache paths: config.py has one path, custom_markdown.py uses another
   - Cache might not be persisting correctly between sessions
   - Need to unify cache directory usage

### Minor Issues

4. **Disabled Cache Clear Functionality**
   - action_clear_cache() in app.py:245-248 just shows "Cache clear disabled"
   - Should implement proper cache clearing

5. **Heavy CSS Loading**
   - CSS_PATH loads 5 files at startup (app.py:149-155)
   - Only one style is used at a time, but all are loaded
   - Should lazy-load style CSS files

6. **On-Mount Header Icon Processing**
   - CustomMarkdown.on_mount() (custom_markdown.py:131-137) loops through all headers to add icons
   - Happens every time, no caching
   - Could be slow for large documents

7. **ASCII Theme Priority**
   - ASCII theme is lowest priority but still loaded and available
   - Should be de-emphasized or made opt-in

---

## IMPLEMENTATION PLAN TO FIX ISSUES

### Phase 1: Critical Bug Fixes (Highest Priority)

#### Task 1.1: Fix 'q' Quit Issue
- **Problem**: Pressing 'q' causes app to reopen instead of quitting
- **Investigation needed**:
  - Check app.py action_quit binding
  - Look for any code that re-launches the app
  - Check if __name__ == "__main__" block at app.py:458-462 is causing re-launch
  - Verify no circular imports or reload issues
- **Expected fix**: Ensure action_quit properly exits without re-launching

#### Task 1.2: Unify Cache Directory
- **Problem**: Cache hardcoded in custom_markdown.py, conflicts with config.py
- **Fix**:
  - Remove hardcoded `CACHE_DIR = Path("/tmp/textual-md-viewer-cache")` from custom_markdown.py:11
  - Import and use `CACHE_DIR` from config.py instead
  - Update all cache references in SmartMarkdownFence to use unified cache
  - Ensure cache directory is created on app startup
- **Files to modify**: custom_markdown.py, verify config.py

### Phase 2: Performance Optimizations (High Priority)

#### Task 2.1: Lazy Load CSS Styles
- **Problem**: All 5 CSS files loaded at startup, only 1 used
- **Fix**:
  - Start with only `styles.tcss` and `styles/obsidian.tcss` (default style)
  - Dynamically load other styles only when user switches to them
  - Use `app.stylesheet.read()` in action_switch_style() to load on-demand
- **Files to modify**: app.py
- **Expected impact**: Faster startup

#### Task 2.2: Optimize Header Icon Addition
- **Problem**: on_mount() processes all headers synchronously
- **Fix**:
  - Consider making header icon addition lazy (only when header becomes visible)
  - Or move to async worker if it must happen upfront
  - Profile to measure actual impact first
- **Files to modify**: custom_markdown.py
- **Expected impact**: Faster rendering for large documents

#### Task 2.3: Profile and Optimize Imports
- **Problem**: Slow startup suggests heavy imports
- **Investigation**:
  - Add timing instrumentation to measure import times
  - Identify slow imports (likely textual-image, Pillow, mermaid-py)
  - Verify lazy loading is working correctly
- **Fix**: Move more imports to function level if needed
- **Files to modify**: app.py, custom_markdown.py

### Phase 3: Feature Completion (Medium Priority)

#### Task 3.1: Implement Cache Clear
- **Problem**: action_clear_cache() disabled
- **Fix**:
  - Implement proper cache clearing in app.py
  - Clear all files in CACHE_DIR (from config.py)
  - Show confirmation notification
- **Files to modify**: app.py

#### Task 3.2: Verify Image Caching Works
- **Problem**: Unclear if image caching actually works
- **Test**:
  - Open file with images/Mermaid
  - Close and reopen
  - Verify images load from cache (should be instant)
- **Fix if needed**: Ensure cache keys are stable, cache hits are logged

### Phase 4: Polish (Low Priority)

#### Task 4.1: ASCII Theme Handling
- **Problem**: ASCII theme is lowest priority but still prominent
- **Options**:
  - Remove from default CSS_PATH loading
  - Load only on explicit user request
  - Or simply leave as-is since it's working

---

## Implementation Order

1. Fix 'q' quit bug (CRITICAL - blocks usability)
2. Unify cache directory (CRITICAL - correctness issue)
3. Lazy load CSS styles (HIGH - improves startup)
4. Profile imports (HIGH - diagnostic for startup performance)
5. Optimize header icons (MEDIUM - depends on profiling results)
6. Implement cache clear (MEDIUM - feature completion)
7. Verify image caching (MEDIUM - feature verification)
8. ASCII theme handling (LOW - polish)

## Development Notes

- Styles use reactive properties to dynamically swap CSS classes
- Search implementation uses source line ranges when available, falls back to rendered text
- Header cleanup uses pre-compiled regex `_HEADER_CLEANUP_RE` for performance
- Mermaid diagrams use mermaid.ink API with base64 encoding
- When fixing issues, **commit changes as you go** - don't wait until all fixes are done
- since this is a textual app, do not run it directly as it will overflwo the context window. ask the suer to run it.