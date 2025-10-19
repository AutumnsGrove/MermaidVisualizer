# MermaidVisualizer - Progressive Web App

A mobile-first Progressive Web App (PWA) for rendering and visualizing Mermaid diagrams on-the-go, built to complement the Python CLI tool with zero-installation browser-based rendering.

## Overview

### What is MermaidVisualizer PWA?

MermaidVisualizer PWA is a standalone web application that allows you to create, visualize, and export Mermaid diagrams directly from your mobile device or desktop browser. No installation required - just visit the URL and start creating diagrams immediately. Install it to your home screen for a native app-like experience.

### Key Features

- **Zero Installation**: Works instantly in any modern browser
- **Offline Capable**: Full functionality without internet connection (after first load)
- **Mobile-First Design**: Optimized touch interface for iPhone and Android
- **Multiple Input Methods**: Paste, upload files, or load from GitHub Gists
- **Export Options**: Download as PNG or SVG, share diagrams
- **PWA Benefits**: Install to home screen, works like a native app
- **Gallery View**: Render and manage multiple diagrams simultaneously
- **Dark Mode Support**: Automatic theme switching based on system preferences

### How It Complements the Python CLI

| Feature | Python CLI | PWA |
|---------|-----------|-----|
| **Use Case** | Batch processing, automation, CI/CD | Quick edits, mobile work, demos |
| **Installation** | Requires Python, Node.js, dependencies | Zero installation, just open URL |
| **Offline** | Requires local setup | Works offline after first load |
| **Input** | Directory scanning, file processing | Paste, upload, URL loading |
| **Output** | Organized folders, batch generation | Individual exports, share links |
| **Platform** | Command-line, scripts | Web browser, any device |
| **Best For** | Documentation projects, large repos | On-the-go editing, quick diagrams |

**Use Together**: Generate diagrams with CLI for your docs repo, then use PWA for quick edits and mobile reviews!

## Architecture

### Hybrid Rendering Approach

The PWA uses **client-side rendering** with Mermaid.js, providing instant feedback without server dependencies:

```
┌─────────────────────────────────────────────────────────────┐
│                    User Browser (Client)                     │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   HTML/CSS   │───▶│  Mermaid.js  │───▶│  Rendered    │  │
│  │   Markdown   │    │   Parser     │    │   Diagram    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Service Worker (Offline Cache + Asset Management)    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Future Backend Option**: Can be extended with server-side rendering using mermaid-cli for complex diagrams or batch operations.

### Technology Stack

- **Frontend Framework**: Vanilla JavaScript (ES6+)
- **Diagram Rendering**: Mermaid.js 10.6.1 (via CDN)
- **Styling**: Custom CSS with CSS Grid and Flexbox
- **PWA Features**: Service Worker for offline caching
- **Icons**: Custom SVG icons with safe-area support
- **Storage**: localStorage for settings and auto-save

### File Structure

```
web-app/
├── index.html              # Main application HTML
├── manifest.json           # PWA manifest (app metadata)
├── sw.js                   # Service Worker (offline caching)
├── README.md              # This file
│
├── css/
│   └── styles.css         # Application styles (mobile-first)
│
├── js/
│   └── app.js             # Main application logic
│
└── icons/
    ├── generate-icons.html # Icon generator utility
    ├── icon-192.png       # PWA icon (192x192)
    ├── icon-512.png       # PWA icon (512x512)
    ├── icon-152.png       # iOS icon (152x152)
    ├── apple-touch-icon.png # iOS icon (180x180)
    └── favicon-*.png      # Browser favicons
```

## Setup & Deployment

### Prerequisites

**None!** This is a static web app that runs entirely in the browser. No build step, no dependencies, no installation required.

### Generate Icons

Before deployment, generate PWA icons for your app:

1. Open `icons/generate-icons.html` in your browser
2. The page will generate all required icon sizes automatically
3. Icons are created using HTML5 Canvas with gradient design
4. Right-click each generated icon and save as:
   - `icon-192.png` (192x192)
   - `icon-512.png` (512x512)
   - `icon-152.png` (152x152)
   - `apple-touch-icon.png` (180x180)
   - `favicon-32x32.png` (32x32)
   - `favicon-16x16.png` (16x16)

**Alternative**: Provide your own custom icons matching these dimensions.

### Local Testing

Test the PWA locally using any simple HTTP server:

**Option 1: Python**
```bash
cd web-app
python3 -m http.server 8000
# Visit: http://localhost:8000
```

**Option 2: Node.js (npx)**
```bash
cd web-app
npx serve
# Visit: http://localhost:3000
```

**Option 3: VS Code Live Server**
1. Install "Live Server" extension
2. Right-click `index.html`
3. Select "Open with Live Server"

**Testing PWA Features**:
- Use Chrome DevTools → Application → Service Workers
- Use Chrome DevTools → Application → Manifest
- Test offline: DevTools → Network → Offline checkbox

### Deployment to GitHub Pages

Deploy the PWA as a free static site on GitHub Pages:

#### Step 1: Prepare Repository

```bash
# Ensure you're in the MermaidVisualizer root directory
cd /path/to/MermaidVisualizer

# Check git status
git status

# Add web-app files
git add web-app/
git commit -m "Add MermaidVisualizer PWA for mobile rendering"
git push origin main
```

#### Step 2: Configure GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under "Source", select:
   - **Branch**: `main`
   - **Folder**: `/web-app`
4. Click **Save**

#### Step 3: Update Configuration

After GitHub Pages builds, update these files with your actual URL:

**manifest.json**:
```json
{
  "start_url": "https://yourusername.github.io/MermaidVisualizer/",
  "scope": "https://yourusername.github.io/MermaidVisualizer/"
}
```

**sw.js** (if using absolute paths):
```javascript
const PRECACHE_URLS = [
  '/MermaidVisualizer/',
  '/MermaidVisualizer/index.html',
  '/MermaidVisualizer/css/styles.css',
  // ... etc
];
```

**Commit and push these changes**:
```bash
git add web-app/manifest.json web-app/sw.js
git commit -m "Update PWA URLs for GitHub Pages deployment"
git push origin main
```

#### Step 4: Access Your PWA

Visit: `https://yourusername.github.io/MermaidVisualizer/`

GitHub Pages typically deploys within 1-5 minutes.

### Deployment to Netlify

Alternative deployment option with automatic HTTPS and CDN:

#### Quick Deploy (Drag & Drop)

1. Go to [Netlify Drop](https://app.netlify.com/drop)
2. Drag the `web-app` folder into the upload area
3. Netlify generates a URL: `https://random-name.netlify.app`
4. Update `manifest.json` and `sw.js` with your Netlify URL

#### Git-Based Continuous Deployment

1. Sign up at [Netlify](https://netlify.com)
2. Click "New site from Git"
3. Connect your GitHub repository
4. Configure build settings:
   - **Base directory**: `web-app`
   - **Build command**: (leave empty - static site)
   - **Publish directory**: `.` (current directory)
5. Click "Deploy site"

**Custom Domain** (optional):
1. Netlify → Domain Settings → Add custom domain
2. Follow DNS configuration instructions
3. Update `manifest.json` and `sw.js` with custom domain

## Usage

### Installing to iPhone Home Screen

Transform the PWA into a native-like app:

1. **Open in Safari**: Visit the PWA URL in Safari (Chrome won't work for iOS install)
2. **Tap Share Button**: Bottom center toolbar (square with arrow)
3. **Add to Home Screen**: Scroll down and tap "Add to Home Screen"
4. **Customize Name**: Edit app name if desired (default: "MermaidVisualizer")
5. **Tap Add**: Icon appears on home screen

**Benefits**:
- Opens in fullscreen (no browser UI)
- Appears in app switcher
- Works offline
- Faster launch times

### Installing on Android

1. **Open in Chrome**: Visit the PWA URL
2. **Install Prompt**: Chrome shows "Add to Home Screen" banner automatically
   - **Alternative**: Menu (⋮) → "Install app" or "Add to Home Screen"
3. **Confirm Installation**: Tap "Install"
4. **Launch**: Icon appears in app drawer and home screen

### Input Methods

#### 1. Paste Markdown

The simplest method:

```markdown
1. Tap the large text area
2. Paste your markdown with Mermaid diagrams:

   ```mermaid
   graph LR
       A[Start] --> B[Process]
       B --> C[End]
   ```

3. Tap "Render Diagram"
```

#### 2. Upload File

Load markdown files from your device:

1. Tap the **file icon** (📄) in the input section header
2. Select a `.md`, `.txt`, or `.mermaid` file
3. Content loads into text area automatically
4. Tap "Render Diagram"

**Supported files**: `.md`, `.txt`, `.mermaid` (max 10MB)

#### 3. Load from GitHub Gist

Load diagrams from GitHub Gists or raw URLs:

1. Get a Gist URL:
   - **Gist**: `https://gist.github.com/username/abc123`
   - **Raw**: `https://raw.githubusercontent.com/...`
2. Paste URL into the "URL input" field
3. Tap **Load** button
4. Markdown loads and renders automatically

**Example Gist workflow**:
```
1. Create Gist with Mermaid diagram
2. Copy Gist URL
3. Open PWA → Paste URL → Load
4. Diagram renders instantly
```

### Exporting Diagrams

#### Download as PNG

1. Render your diagram
2. Tap **download icon** (⬇️) in output section
3. Diagram downloads as `mermaid-diagram-YYYYMMDD-HHMMSS.png`
4. Access via Files app or Photos (depending on browser)

#### Download as SVG

1. Open Settings (⚙️ menu)
2. Enable "Export as SVG" (if implemented)
3. Tap download icon
4. Vector format - perfect for presentations and documents

#### Share Diagram

1. Tap **share icon** (🔗) in output section
2. Native share sheet appears
3. Share via:
   - Messages, Email, Slack
   - AirDrop (iOS)
   - Copy to clipboard
   - Save to Files

### Settings and Preferences

Access settings via the menu button (☰):

| Setting | Description |
|---------|-------------|
| **Dark Mode** | Toggle dark theme (or use auto system preference) |
| **Auto-render** | Render diagrams automatically as you type (debounced) |
| **Auto-save** | Save input to localStorage automatically |
| **Export Format** | Default format for downloads (PNG/SVG) |

**Settings persist** across sessions using localStorage.

### Keyboard Shortcuts

Desktop users can use keyboard shortcuts:

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl + Enter` | Render diagram |
| `Cmd/Ctrl + S` | Download diagram |
| `Cmd/Ctrl + K` | Clear input |
| `Cmd/Ctrl + O` | Open file picker |
| `Cmd/Ctrl + ,` | Open settings |
| `Esc` | Close modals |

## Features

### Implemented Features

#### PWA Capabilities
- ✅ **Install to Home Screen**: Full PWA support for iOS and Android
- ✅ **Offline Functionality**: Service Worker caches all assets
- ✅ **App Manifest**: Proper metadata for installation
- ✅ **Standalone Mode**: Fullscreen experience without browser UI

#### Mobile Optimizations
- ✅ **Touch-Friendly UI**: Large tap targets, swipe gestures
- ✅ **Safe Area Support**: Notch and home indicator handling (iPhone X+)
- ✅ **Responsive Layout**: Adapts to all screen sizes
- ✅ **Mobile Keyboard**: Optimized input fields with proper autocomplete

#### Input Features
- ✅ **Paste Markdown**: Direct markdown input with syntax highlighting
- ✅ **File Upload**: Load `.md`, `.txt`, `.mermaid` files
- ✅ **GitHub Gist Support**: Load diagrams from Gist URLs
- ✅ **URL Loading**: Fetch from any raw markdown URL
- ✅ **Auto-save**: Preserve work in localStorage

#### Rendering Features
- ✅ **Mermaid.js Integration**: Full Mermaid diagram support
- ✅ **Multiple Diagram Types**: Flowchart, sequence, gantt, pie, etc.
- ✅ **Live Preview**: Instant rendering on button tap
- ✅ **Error Handling**: Clear error messages for invalid syntax
- ✅ **Diagram Gallery**: Handle multiple diagrams in one document

#### Export Features
- ✅ **PNG Export**: Download high-quality raster images
- ✅ **SVG Export**: Vector graphics for scaling
- ✅ **Share Integration**: Native share sheet (iOS/Android)
- ✅ **Smart Naming**: Auto-generated filenames with timestamps

#### UX Features
- ✅ **Toast Notifications**: Non-intrusive status messages
- ✅ **Loading States**: Clear feedback during rendering
- ✅ **Empty States**: Helpful placeholder guidance
- ✅ **Settings Modal**: Customizable preferences
- ✅ **Theme Support**: Light and dark modes

### Export Options

Currently supported export formats:

1. **PNG** (Raster)
   - Default export format
   - High-resolution rendering
   - Best for: Documents, presentations, web use

2. **SVG** (Vector)
   - Scalable graphics
   - Smaller file sizes
   - Best for: Print, high-DPI displays, further editing

3. **Share**
   - Share diagram image via native share sheet
   - Copy to clipboard
   - Send via messaging apps

## Development

### File Structure Explained

```
web-app/
│
├── index.html                  # Single-page application
│   ├── <head>                  # Meta tags, PWA manifest, iOS config
│   ├── <header>                # App title and menu button
│   ├── <main>                  # Input and output sections
│   │   ├── Input section       # Markdown textarea + URL input
│   │   └── Output section      # Diagram container + gallery
│   ├── <footer>                # Render button action bar
│   └── <modals>                # Settings, loading overlay, toasts
│
├── css/styles.css              # Application styling
│   ├── CSS Variables           # Theme colors, spacing, typography
│   ├── Reset & Base            # Cross-browser normalization
│   ├── Layout                  # Grid, flexbox, safe-area
│   ├── Components              # Buttons, inputs, cards
│   ├── Sections                # Input, output, gallery
│   └── Responsive              # Mobile-first breakpoints
│
├── js/app.js                   # Main application logic
│   ├── MermaidVisualizerApp    # Main class
│   │   ├── init()              # Initialize app
│   │   ├── initMermaid()       # Configure Mermaid.js
│   │   ├── registerEventListeners() # UI interactions
│   │   ├── renderDiagrams()    # Parse and render Mermaid
│   │   ├── exportDiagram()     # Download functionality
│   │   ├── loadFromURL()       # Fetch from Gist/URL
│   │   └── showToast()         # Notifications
│   └── Event Handlers          # Button clicks, input changes
│
├── sw.js                       # Service Worker
│   ├── CACHE_NAME              # Version control for cache
│   ├── PRECACHE_URLS           # Files to cache on install
│   ├── install event           # Pre-cache essential files
│   ├── activate event          # Clean old caches
│   └── fetch event             # Serve from cache, fallback network
│
├── manifest.json               # PWA metadata
│   ├── name, short_name        # App titles
│   ├── icons[]                 # Icon sizes for all devices
│   ├── start_url, scope        # App boundaries
│   ├── display: standalone     # Fullscreen mode
│   └── theme_color             # UI theming
│
└── icons/
    ├── generate-icons.html     # Icon generator utility
    └── *.png                   # Generated icons
```

### How to Modify/Extend

#### Add New Diagram Type Support

Mermaid.js supports many diagram types out of the box:

```javascript
// In app.js → initMermaid()
window.mermaid.initialize({
  // ... existing config
  gantt: {
    useMaxWidth: true,
    titleTopMargin: 25
  },
  pie: {
    useMaxWidth: true
  }
  // Add more diagram types here
});
```

#### Customize Styling

```css
/* In css/styles.css */
:root {
  /* Update CSS variables for global changes */
  --primary-color: #667eea;      /* Change app accent color */
  --background: #ffffff;          /* Light mode background */
  --text-primary: #1a202c;        /* Primary text color */
  /* ... etc */
}
```

#### Add New Input Method

```javascript
// In app.js → registerEventListeners()
this.elements.newInputBtn.addEventListener('click', async () => {
  try {
    const data = await this.loadFromNewSource();
    this.elements.markdownInput.value = data;
    this.showToast('Loaded successfully', 'success');
  } catch (error) {
    this.showToast('Failed to load', 'error');
  }
});
```

#### Modify Export Behavior

```javascript
// In app.js → exportDiagram()
async exportDiagram(format = 'png') {
  const svgElement = document.querySelector('#diagramContainer svg');

  if (format === 'pdf') {
    // Add PDF export using jsPDF or similar
    const pdf = new jsPDF();
    pdf.addImage(svgElement, 'PNG', 0, 0);
    pdf.save('diagram.pdf');
  }
}
```

### Adding Backend Rendering (Future)

For complex diagrams or batch operations, add server-side rendering:

#### Architecture with Backend

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Browser    │─────▶│   API Server │─────▶│  mermaid-cli │
│   (PWA)      │◀─────│   (Node.js)  │◀─────│  (Puppeteer) │
└──────────────┘      └──────────────┘      └──────────────┘
```

#### Backend Implementation Steps

1. **Create API Server** (`server/index.js`):

```javascript
// server/index.js
const express = require('express');
const { run } = require('@mermaid-js/mermaid-cli');
const app = express();

app.post('/api/render', async (req, res) => {
  const { markdown, format } = req.body;

  // Save markdown to temp file
  const inputFile = '/tmp/diagram.mmd';
  const outputFile = `/tmp/diagram.${format}`;

  fs.writeFileSync(inputFile, markdown);

  // Render with mermaid-cli
  await run(inputFile, outputFile, { puppeteerConfig: {} });

  // Return rendered diagram
  res.sendFile(outputFile);
});

app.listen(3000);
```

2. **Update Frontend** (`js/app.js`):

```javascript
async renderWithBackend(markdown, format = 'png') {
  const response = await fetch('/api/render', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ markdown, format })
  });

  const blob = await response.blob();
  return URL.createObjectURL(blob);
}
```

3. **Fallback Strategy**:

```javascript
async renderDiagram(markdown) {
  try {
    // Try client-side first (fast)
    return await this.renderWithMermaidJS(markdown);
  } catch (error) {
    // Fallback to backend for complex diagrams
    console.warn('Client-side rendering failed, using backend');
    return await this.renderWithBackend(markdown);
  }
}
```

## Troubleshooting

### Common Issues

#### PWA Not Installing

**Symptoms**: "Add to Home Screen" doesn't appear

**Solutions**:
1. **Verify HTTPS**: PWAs require HTTPS (localhost is exempt)
   - GitHub Pages and Netlify provide HTTPS automatically
   - Use `npx serve --ssl` for local HTTPS testing
2. **Check Manifest**: Ensure `manifest.json` is valid
   - Open DevTools → Application → Manifest
   - Look for errors or warnings
3. **Service Worker**: Verify SW is registered
   - DevTools → Application → Service Workers
   - Should show "activated and running"
4. **Clear Cache**: Force reload and re-register
   ```javascript
   // In browser console
   navigator.serviceWorker.getRegistrations()
     .then(regs => regs.forEach(reg => reg.unregister()));
   ```

#### Diagrams Not Rendering

**Symptoms**: Empty output or error messages

**Solutions**:
1. **Check Mermaid Syntax**: Validate your diagram syntax
   - Visit [Mermaid Live Editor](https://mermaid.live)
   - Paste diagram code to validate
2. **Console Errors**: Open DevTools → Console for specific errors
3. **Mermaid.js Loading**: Check Network tab for CDN failures
   - Try different CDN URL or download Mermaid.js locally
4. **Diagram Type**: Ensure diagram type is supported
   ```mermaid
   graph TD  ← Valid
   badtype TD  ← Invalid
   ```

#### Offline Mode Not Working

**Symptoms**: App doesn't work without internet

**Solutions**:
1. **First Load**: Visit app online at least once to cache assets
2. **Service Worker**: Check registration status
   - DevTools → Application → Service Workers
3. **Cache Version**: Update `CACHE_NAME` in `sw.js` if assets changed
4. **Force Update**: Unregister SW and reload
   ```javascript
   navigator.serviceWorker.getRegistrations()
     .then(regs => regs.forEach(reg => reg.unregister()))
     .then(() => location.reload());
   ```

#### File Upload Fails

**Symptoms**: "Failed to load file" error

**Solutions**:
1. **File Size**: Ensure file is under 10MB
2. **File Type**: Use `.md`, `.txt`, or `.mermaid` extensions
3. **File Encoding**: Ensure UTF-8 encoding (not UTF-16 or binary)
4. **Browser Permissions**: Check file access permissions

### Service Worker Debugging

Enable verbose logging:

```javascript
// In sw.js
const DEBUG = true;

if (DEBUG) {
  console.log('[SW] Cache hit:', request.url);
  console.log('[SW] Network fetch:', request.url);
}
```

**Chrome DevTools**:
1. Open DevTools → Application → Service Workers
2. Check "Update on reload" (forces SW update on refresh)
3. Click "Unregister" to remove SW
4. Click "skipWaiting" to activate new SW immediately

**Firefox DevTools**:
1. Open DevTools → Application → Service Workers
2. Use "Unregister" and "Update" buttons
3. Check console for SW lifecycle events

### iOS Installation Issues

**Symptoms**: App doesn't install on iPhone

**Solutions**:
1. **Use Safari**: Chrome/Firefox don't support PWA install on iOS
2. **Valid Manifest**: Ensure `manifest.json` has required fields:
   ```json
   {
     "name": "MermaidVisualizer",
     "short_name": "Mermaid",
     "start_url": "/",
     "display": "standalone",
     "icons": [/* at least 192x192 */]
   }
   ```
3. **Apple Touch Icons**: Add to `<head>`:
   ```html
   <link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
   <meta name="apple-mobile-web-app-capable" content="yes">
   ```
4. **HTTPS Required**: Even localhost must use HTTPS on iOS (or use ngrok)

### Performance Issues

**Symptoms**: Slow rendering, laggy UI

**Solutions**:
1. **Large Diagrams**: Break into smaller diagrams
2. **Disable Auto-render**: Turn off auto-render in settings
3. **Clear localStorage**: Reset app state
   ```javascript
   localStorage.clear();
   location.reload();
   ```
4. **Reduce Animations**: Add to `styles.css`:
   ```css
   * {
     animation: none !important;
     transition: none !important;
   }
   ```

## Future Enhancements

### Planned Features

#### Backend Rendering with mermaid-cli
- Server-side diagram generation for complex visualizations
- Batch processing support
- Higher quality exports
- Support for all Mermaid features

#### Advanced Export Options
- **PDF Export**: Multi-page diagram exports
- **Batch Download**: Export all diagrams as ZIP
- **High-DPI**: Retina-quality PNG exports
- **Transparent Backgrounds**: For presentations

#### Collaboration Features
- **Cloud Sync**: Save diagrams to cloud storage
- **Real-time Collaboration**: Multiple users editing
- **Version History**: Track diagram changes
- **Comments**: Annotate diagrams

#### Editor Enhancements
- **Syntax Highlighting**: Code editor with Mermaid syntax
- **Auto-complete**: Intelligent Mermaid code suggestions
- **Templates**: Quick-start diagram templates
- **Snippets**: Reusable diagram components

#### Mobile Improvements
- **Touch Gestures**: Pinch-to-zoom, pan diagrams
- **Apple Pencil**: Annotate on iPad
- **Drag & Drop**: Reorder elements visually
- **Voice Input**: Dictate diagram descriptions

#### Integration Features
- **GitHub Integration**: Save directly to repos
- **Notion/Confluence**: Export to documentation platforms
- **Clipboard Monitoring**: Auto-detect Mermaid code
- **QR Code**: Share diagrams via QR codes

### Contributing Ideas

Want to contribute? Areas needing help:

1. **Accessibility**: Improve screen reader support, keyboard navigation
2. **Internationalization**: Translate UI to other languages
3. **Testing**: Add unit tests, E2E tests, PWA compliance tests
4. **Documentation**: Video tutorials, example gallery
5. **Themes**: Additional color themes, diagram themes

## Credits

- **Mermaid.js**: [mermaid.js.org](https://mermaid.js.org) - Diagram rendering library
- **Icons**: Custom SVG icons with gradient design
- **Development**: Built with Claude (Sonnet 4.5)

## License

This project is part of the MermaidVisualizer ecosystem. See main repository for license details.

---

**Version**: 1.0.0
**Last Updated**: 2025-10-19
**Maintained by**: MermaidVisualizer Team

For issues, feature requests, or questions, please visit the [main repository](https://github.com/yourusername/MermaidVisualizer).
