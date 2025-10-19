# TODOs

## ✅ Completed

### File Naming Convention Improvements
- [x] Use the markdown header content from source files as the primary file name when available
- [x] For files containing only Mermaid code:
  - Use abbreviated prefixes to indicate diagram type:
    - seq_ for sequence diagrams
    - graph_ for flowcharts/graphs
    - class_ for class diagrams
    - etc.
  - Follow with a descriptive name based on content
  - Example: "seq_user_authentication.md" instead of "diagrams_0_sequence"

### Implementation Tasks
- [x] Extract markdown headers from source files during parsing
- [x] Implement new naming convention in file generation
- [x] Add fallback naming strategy for files without headers
- [x] Update file name generation logic to handle special characters
- [x] Add name conflict resolution for duplicate headers

### HTML Gallery Viewer
- [x] Implement beautiful, responsive gallery design
- [x] Add GLightbox integration for lightbox/modal viewing
- [x] Enable zoom in/out functionality
- [x] Add mobile-friendly touch gestures and responsive layout
- [x] Include keyboard navigation support

## 🚧 In Progress

### Progressive Web App (PWA) - Mobile Support

#### Phase 1: Foundation & PWA Structure (~40 min)
- [ ] Create `/web-app/` project structure with subdirectories
- [ ] Build mobile-first HTML shell with iOS safe area support
- [ ] Create PWA manifest.json with app metadata
- [ ] Implement service worker for offline support
- [ ] Generate app icons (192x192, 512x512, apple-touch-icon)
- [ ] Test: Install to iPhone home screen

#### Phase 2: Client-Side Mermaid Rendering (~60 min)
- [ ] Integrate Mermaid.js v10+ library via CDN
- [ ] Implement markdown parser to extract mermaid code blocks
- [ ] Build diagram rendering engine with error handling
- [ ] Create gallery UI with card-based layout
- [ ] Add pinch-to-zoom and swipe navigation
- [ ] Support dark mode based on iOS settings

#### Phase 3: Input Methods (~40 min)
- [ ] Implement textarea input with auto-save to LocalStorage
- [ ] Add file upload support (.md, .txt, .mermaid files)
- [ ] Integrate GitHub Gist URL fetching
- [ ] Add public URL markdown fetching capability

#### Phase 4: Export & Share (~50 min)
- [ ] Implement SVG export from Mermaid.js
- [ ] Add PNG export (SVG → Canvas → PNG conversion)
- [ ] Integrate iOS Web Share API for native sharing
- [ ] Add batch ZIP download for all diagrams
- [ ] Implement clipboard copy functionality

#### Phase 5: Backend API Design (~20 min)
- [ ] Design REST API endpoint structure
- [ ] Document backend rendering options (Netlify/Vercel/AWS)
- [ ] Create renderer abstraction layer for client/server toggle
- [ ] Plan future integration path

#### Phase 6: Polish & Advanced Features (~40 min)
- [ ] Build settings panel (theme, render mode, export quality)
- [ ] Implement LocalStorage for saved diagrams and recents
- [ ] Add keyboard shortcuts for desktop use
- [ ] Ensure accessibility (screen readers, focus indicators)
- [ ] Optimize performance (lazy loading, image optimization)

#### Deployment
- [ ] Deploy to GitHub Pages or Netlify
- [ ] Test on multiple iPhone models
- [ ] Verify offline functionality
- [ ] Document usage in README