# TODOs

## File Naming Convention Improvements
- Use the markdown header content from source files as the primary file name when available
- For files containing only Mermaid code:
  - Use abbreviated prefixes to indicate diagram type: 
    - seq_ for sequence diagrams
    - graph_ for flowcharts/graphs
    - class_ for class diagrams
    - etc.
  - Follow with a descriptive name based on content
  - Example: "seq_user_authentication.md" instead of "diagrams_0_sequence"

## Implementation Tasks
- Extract markdown headers from source files during parsing
- Implement new naming convention in file generation
- Add fallback naming strategy for files without headers
- Update file name generation logic to handle special characters
- Add name conflict resolution for duplicate headers