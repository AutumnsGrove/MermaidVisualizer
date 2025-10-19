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