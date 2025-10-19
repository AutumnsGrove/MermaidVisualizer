/**
 * MermaidVisualizer - Main Application
 *
 * A comprehensive PWA for rendering Mermaid diagrams from markdown.
 * Supports multiple input methods, export formats, and mobile-optimized interactions.
 *
 * @author Claude (Sonnet 4.5)
 * @version 1.0.0
 */

// ============================================================================
// APPLICATION CLASS
// ============================================================================

class MermaidVisualizerApp {
    constructor() {
        // Configuration
        this.config = {
            autosaveDelay: 500, // milliseconds
            maxFileSize: 10 * 1024 * 1024, // 10MB
            supportedExtensions: ['.md', '.txt', '.mermaid'],
            storageKeys: {
                content: 'mermaid_content',
                darkMode: 'mermaid_darkMode',
                autoRender: 'mermaid_autoRender',
                recentDocs: 'mermaid_recentDocs'
            },
            viewer: {
                minZoom: 0.25,
                maxZoom: 4.0,
                zoomStep: 0.25,
                doubleTapZoom: 2.0
            }
        };

        // State
        this.state = {
            diagrams: [],
            currentDiagram: null,
            isRendering: false,
            darkMode: false,
            autoRender: false
        };

        // Auto-save debounce timer
        this.autosaveTimer = null;

        // Diagram viewer instance
        this.diagramViewer = null;

        // Initialize app
        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        console.log('Initializing MermaidVisualizer...');

        try {
            // Initialize Mermaid.js
            await this.initMermaid();

            // Cache DOM elements
            this.cacheDOMElements();

            // Load settings from localStorage
            this.loadSettings();

            // Register event listeners
            this.registerEventListeners();

            // Load saved content
            this.loadSavedContent();

            // Register service worker
            this.registerServiceWorker();

            // Initialize diagram viewer
            this.diagramViewer = new DiagramViewer(this);

            console.log('MermaidVisualizer initialized successfully');
            this.showToast('App ready!', 'success');
        } catch (error) {
            console.error('Initialization error:', error);
            this.showToast('Failed to initialize app', 'error');
        }
    }

    /**
     * Initialize Mermaid.js with mobile-optimized configuration
     */
    async initMermaid() {
        if (!window.mermaid) {
            throw new Error('Mermaid.js not loaded');
        }

        window.mermaid.initialize({
            startOnLoad: false,
            theme: 'default',
            securityLevel: 'loose',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            },
            sequence: {
                useMaxWidth: true,
                diagramMarginX: 10,
                diagramMarginY: 10
            }
        });

        console.log('Mermaid.js initialized');
    }

    /**
     * Cache frequently accessed DOM elements
     */
    cacheDOMElements() {
        // Input elements
        this.elements = {
            markdownInput: document.getElementById('markdownInput'),
            urlInput: document.getElementById('urlInput'),
            fileInput: document.getElementById('fileInput'),

            // Buttons
            renderBtn: document.getElementById('renderBtn'),
            loadFileBtn: document.getElementById('loadFileBtn'),
            loadUrlBtn: document.getElementById('loadUrlBtn'),
            clearBtn: document.getElementById('clearBtn'),
            downloadBtn: document.getElementById('downloadBtn'),
            shareBtn: document.getElementById('shareBtn'),
            menuBtn: document.getElementById('menuBtn'),

            // Containers
            diagramContainer: document.getElementById('diagramContainer'),
            diagramGallery: document.getElementById('diagramGallery'),
            toastContainer: document.getElementById('toastContainer'),
            loadingOverlay: document.getElementById('loadingOverlay'),

            // Modal
            settingsModal: document.getElementById('settingsModal'),
            closeModalBtn: document.getElementById('closeModalBtn'),
            themeToggle: document.getElementById('themeToggle'),
            autoRenderToggle: document.getElementById('autoRender')
        };
    }

    /**
     * Register all event listeners
     */
    registerEventListeners() {
        // Render button
        this.elements.renderBtn.addEventListener('click', () => this.renderDiagrams());

        // File operations
        this.elements.loadFileBtn.addEventListener('click', () => this.elements.fileInput.click());
        this.elements.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        this.elements.clearBtn.addEventListener('click', () => this.clearInput());

        // URL loading
        this.elements.loadUrlBtn.addEventListener('click', () => this.loadFromUrl());
        this.elements.urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.loadFromUrl();
        });

        // Export/Share
        this.elements.downloadBtn.addEventListener('click', () => this.exportDiagrams());
        this.elements.shareBtn.addEventListener('click', () => this.shareDiagrams());

        // Settings
        this.elements.menuBtn.addEventListener('click', () => this.openSettingsModal());
        this.elements.closeModalBtn.addEventListener('click', () => this.closeSettingsModal());
        this.elements.themeToggle.addEventListener('change', (e) => this.toggleDarkMode(e.target.checked));
        this.elements.autoRenderToggle.addEventListener('change', (e) => this.toggleAutoRender(e.target.checked));

        // Auto-save on input
        this.elements.markdownInput.addEventListener('input', () => this.handleInputChange());

        // Keyboard shortcuts
        this.elements.markdownInput.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));

        // Modal close on outside click
        this.elements.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.elements.settingsModal) {
                this.closeSettingsModal();
            }
        });

        // Prevent zoom on double-tap for buttons
        document.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('touchend', (e) => {
                e.preventDefault();
                btn.click();
            }, { passive: false });
        });
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(e) {
        // Cmd/Ctrl + Enter to render
        if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
            e.preventDefault();
            this.renderDiagrams();
        }
    }

    /**
     * Handle input changes with debounced auto-save
     */
    handleInputChange() {
        // Clear existing timer
        if (this.autosaveTimer) {
            clearTimeout(this.autosaveTimer);
        }

        // Set new timer
        this.autosaveTimer = setTimeout(() => {
            this.saveContent();

            // Auto-render if enabled
            if (this.state.autoRender) {
                this.renderDiagrams();
            }
        }, this.config.autosaveDelay);
    }

    /**
     * Parse markdown and extract Mermaid code blocks
     */
    parseMarkdown(markdown) {
        const diagrams = [];

        // Regex to match mermaid code blocks
        const mermaidRegex = /```mermaid\s*\n([\s\S]*?)```/g;
        let match;
        let index = 0;

        while ((match = mermaidRegex.exec(markdown)) !== null) {
            const code = match[1].trim();

            if (code) {
                // Detect diagram type
                const type = this.detectDiagramType(code);

                diagrams.push({
                    id: `diagram-${Date.now()}-${index}`,
                    code: code,
                    type: type,
                    index: index
                });

                index++;
            }
        }

        return diagrams;
    }

    /**
     * Detect the type of Mermaid diagram
     */
    detectDiagramType(code) {
        const firstLine = code.trim().split('\n')[0].toLowerCase();

        if (firstLine.startsWith('graph')) return 'flowchart';
        if (firstLine.startsWith('sequencediagram')) return 'sequence';
        if (firstLine.startsWith('classdiagram')) return 'class';
        if (firstLine.startsWith('statediagram')) return 'state';
        if (firstLine.startsWith('erdiagram')) return 'er';
        if (firstLine.startsWith('journey')) return 'journey';
        if (firstLine.startsWith('gantt')) return 'gantt';
        if (firstLine.startsWith('pie')) return 'pie';
        if (firstLine.startsWith('gitgraph')) return 'gitgraph';
        if (firstLine.startsWith('mindmap')) return 'mindmap';

        return 'unknown';
    }

    /**
     * Render all diagrams from markdown input
     */
    async renderDiagrams() {
        const markdown = this.elements.markdownInput.value.trim();

        if (!markdown) {
            this.showToast('Please enter some markdown content', 'warning');
            return;
        }

        // Show loading
        this.showLoading(true);
        this.state.isRendering = true;

        try {
            // Parse markdown
            const diagrams = this.parseMarkdown(markdown);

            if (diagrams.length === 0) {
                this.showToast('No Mermaid diagrams found in markdown', 'warning');
                this.showLoading(false);
                return;
            }

            // Clear existing diagrams
            this.state.diagrams = [];
            this.elements.diagramContainer.innerHTML = '';
            this.elements.diagramGallery.innerHTML = '';

            // Render each diagram
            for (const diagram of diagrams) {
                await this.renderSingleDiagram(diagram);
            }

            // Update UI based on diagram count
            if (diagrams.length === 1) {
                // Single diagram - show in main container
                this.elements.diagramGallery.style.display = 'none';
            } else {
                // Multiple diagrams - show gallery
                this.elements.diagramGallery.style.display = 'grid';
                this.populateGallery();
            }

            // Enable export buttons
            this.elements.downloadBtn.disabled = false;
            this.elements.shareBtn.disabled = false;

            this.showToast(`Rendered ${diagrams.length} diagram(s)`, 'success');
        } catch (error) {
            console.error('Rendering error:', error);
            this.showToast(`Rendering failed: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
            this.state.isRendering = false;
        }
    }

    /**
     * Render a single Mermaid diagram
     */
    async renderSingleDiagram(diagram) {
        try {
            // Create container for this diagram
            const container = document.createElement('div');
            container.className = 'diagram-item';
            container.id = diagram.id;

            // Render diagram using Mermaid
            const { svg } = await window.mermaid.render(diagram.id + '-svg', diagram.code);

            // Create wrapper with metadata
            const wrapper = document.createElement('div');
            wrapper.className = 'diagram-wrapper';
            wrapper.innerHTML = `
                <div class="diagram-header">
                    <span class="diagram-type">${diagram.type}</span>
                    <span class="diagram-index">#${diagram.index + 1}</span>
                </div>
                <div class="diagram-content">
                    ${svg}
                </div>
            `;

            container.appendChild(wrapper);
            this.elements.diagramContainer.appendChild(container);

            // Store diagram data
            diagram.svg = svg;
            this.state.diagrams.push(diagram);

        } catch (error) {
            console.error(`Failed to render diagram ${diagram.index}:`, error);
            throw new Error(`Diagram ${diagram.index + 1} rendering failed: ${error.message}`);
        }
    }

    /**
     * Populate gallery with diagram thumbnails
     */
    populateGallery() {
        this.elements.diagramGallery.innerHTML = '';

        this.state.diagrams.forEach((diagram, index) => {
            const card = document.createElement('div');
            card.className = 'gallery-card';
            card.innerHTML = `
                <div class="gallery-thumbnail">
                    ${diagram.svg}
                </div>
                <div class="gallery-info">
                    <span class="gallery-type">${diagram.type}</span>
                    <span class="gallery-index">#${index + 1}</span>
                </div>
            `;

            // Click to open diagram in modal viewer
            card.addEventListener('click', () => {
                if (this.diagramViewer) {
                    this.diagramViewer.open(index);
                }
            });

            this.elements.diagramGallery.appendChild(card);
        });
    }

    /**
     * View a specific diagram by ID (legacy method, now opens in modal)
     */
    viewDiagram(diagramId) {
        const index = this.state.diagrams.findIndex(d => d.id === diagramId);
        if (index !== -1 && this.diagramViewer) {
            this.diagramViewer.open(index);
        }
    }

    /**
     * Handle file upload
     */
    async handleFileUpload(event) {
        const file = event.target.files[0];

        if (!file) return;

        // Validate file size
        if (file.size > this.config.maxFileSize) {
            this.showToast('File too large (max 10MB)', 'error');
            return;
        }

        // Validate file extension
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        if (!this.config.supportedExtensions.includes(extension)) {
            this.showToast('Unsupported file type', 'error');
            return;
        }

        try {
            const content = await this.readFileAsText(file);
            this.elements.markdownInput.value = content;
            this.saveContent();
            this.showToast(`Loaded ${file.name}`, 'success');

            // Auto-render if enabled
            if (this.state.autoRender) {
                this.renderDiagrams();
            }
        } catch (error) {
            console.error('File read error:', error);
            this.showToast('Failed to read file', 'error');
        }

        // Clear file input
        event.target.value = '';
    }

    /**
     * Read file as text
     */
    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e);
            reader.readAsText(file);
        });
    }

    /**
     * Load content from URL (GitHub Gist or raw markdown)
     */
    async loadFromUrl() {
        const url = this.elements.urlInput.value.trim();

        if (!url) {
            this.showToast('Please enter a URL', 'warning');
            return;
        }

        this.showLoading(true);

        try {
            // Check if it's a GitHub Gist URL
            let fetchUrl = url;

            if (url.includes('gist.github.com')) {
                // Convert Gist URL to raw URL
                fetchUrl = this.convertGistToRawUrl(url);
            }

            // Fetch content
            const response = await fetch(fetchUrl);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const content = await response.text();
            this.elements.markdownInput.value = content;
            this.saveContent();
            this.showToast('Content loaded successfully', 'success');

            // Auto-render if enabled
            if (this.state.autoRender) {
                this.renderDiagrams();
            }
        } catch (error) {
            console.error('URL load error:', error);
            this.showToast(`Failed to load URL: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Convert GitHub Gist URL to raw URL
     */
    convertGistToRawUrl(gistUrl) {
        // Example: https://gist.github.com/user/abc123
        // Converts to: https://gist.githubusercontent.com/user/abc123/raw

        const gistMatch = gistUrl.match(/gist\.github\.com\/([^\/]+)\/([^\/\?#]+)/);

        if (gistMatch) {
            const [, user, gistId] = gistMatch;
            return `https://gist.githubusercontent.com/${user}/${gistId}/raw`;
        }

        return gistUrl;
    }

    /**
     * Export diagrams (SVG or PNG)
     */
    async exportDiagrams() {
        if (this.state.diagrams.length === 0) {
            this.showToast('No diagrams to export', 'warning');
            return;
        }

        // Show export options
        const format = await this.showExportDialog();

        if (!format) return;

        try {
            if (format === 'svg') {
                await this.exportAsSVG();
            } else if (format === 'png') {
                await this.exportAsPNG();
            }
        } catch (error) {
            console.error('Export error:', error);
            this.showToast(`Export failed: ${error.message}`, 'error');
        }
    }

    /**
     * Show export format dialog
     */
    showExportDialog() {
        return new Promise((resolve) => {
            const dialog = document.createElement('div');
            dialog.className = 'export-dialog';
            dialog.innerHTML = `
                <div class="export-dialog-content">
                    <h3>Export Format</h3>
                    <button class="btn-primary export-option" data-format="svg">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                        </svg>
                        SVG (Vector)
                    </button>
                    <button class="btn-secondary export-option" data-format="png">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                            <circle cx="8.5" cy="8.5" r="1.5"></circle>
                            <polyline points="21 15 16 10 5 21"></polyline>
                        </svg>
                        PNG (Raster)
                    </button>
                    <button class="btn-text export-option" data-format="cancel">Cancel</button>
                </div>
            `;

            document.body.appendChild(dialog);

            dialog.addEventListener('click', (e) => {
                const option = e.target.closest('.export-option');
                if (option) {
                    const format = option.dataset.format;
                    document.body.removeChild(dialog);
                    resolve(format === 'cancel' ? null : format);
                }
            });
        });
    }

    /**
     * Export diagrams as SVG
     */
    async exportAsSVG() {
        for (const diagram of this.state.diagrams) {
            const filename = `${diagram.type}_diagram_${diagram.index + 1}.svg`;
            this.downloadFile(diagram.svg, filename, 'image/svg+xml');
        }

        this.showToast(`Exported ${this.state.diagrams.length} SVG file(s)`, 'success');
    }

    /**
     * Export diagrams as PNG
     */
    async exportAsPNG() {
        for (const diagram of this.state.diagrams) {
            const blob = await this.svgToPng(diagram.svg);
            const filename = `${diagram.type}_diagram_${diagram.index + 1}.png`;
            this.downloadBlob(blob, filename);
        }

        this.showToast(`Exported ${this.state.diagrams.length} PNG file(s)`, 'success');
    }

    /**
     * Convert SVG to PNG using Canvas
     */
    svgToPng(svgString) {
        return new Promise((resolve, reject) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();

            img.onload = () => {
                canvas.width = img.width * 2; // 2x for better quality
                canvas.height = img.height * 2;
                ctx.scale(2, 2);
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);

                canvas.toBlob((blob) => {
                    if (blob) {
                        resolve(blob);
                    } else {
                        reject(new Error('Canvas to Blob conversion failed'));
                    }
                }, 'image/png');
            };

            img.onerror = () => reject(new Error('Image load failed'));

            // Convert SVG to data URL
            const blob = new Blob([svgString], { type: 'image/svg+xml' });
            img.src = URL.createObjectURL(blob);
        });
    }

    /**
     * Download file helper
     */
    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        this.downloadBlob(blob, filename);
    }

    /**
     * Download blob helper
     */
    downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Share diagrams using Web Share API
     */
    async shareDiagrams() {
        if (!navigator.share) {
            this.showToast('Sharing not supported on this device', 'warning');
            return;
        }

        if (this.state.diagrams.length === 0) {
            this.showToast('No diagrams to share', 'warning');
            return;
        }

        try {
            // Convert first diagram to PNG for sharing
            const diagram = this.state.diagrams[0];
            const blob = await this.svgToPng(diagram.svg);
            const file = new File([blob], `${diagram.type}_diagram.png`, { type: 'image/png' });

            await navigator.share({
                title: 'Mermaid Diagram',
                text: `Check out this ${diagram.type} diagram!`,
                files: [file]
            });

            this.showToast('Shared successfully', 'success');
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Share error:', error);
                this.showToast('Sharing failed', 'error');
            }
        }
    }

    /**
     * Clear input
     */
    clearInput() {
        if (confirm('Clear all input? This cannot be undone.')) {
            this.elements.markdownInput.value = '';
            this.elements.urlInput.value = '';
            this.state.diagrams = [];
            this.elements.diagramContainer.innerHTML = '<div class="empty-state"><svg class="empty-icon" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="9" x2="15" y2="9"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg><p class="empty-text">Your diagrams will appear here</p><p class="empty-subtext">Paste markdown above and tap Render</p></div>';
            this.elements.diagramGallery.style.display = 'none';
            this.elements.downloadBtn.disabled = true;
            this.elements.shareBtn.disabled = true;
            this.saveContent();
            this.showToast('Input cleared', 'info');
        }
    }

    /**
     * Save content to localStorage
     */
    saveContent() {
        try {
            localStorage.setItem(
                this.config.storageKeys.content,
                this.elements.markdownInput.value
            );
        } catch (error) {
            console.error('Failed to save content:', error);
        }
    }

    /**
     * Load saved content from localStorage
     */
    loadSavedContent() {
        try {
            const saved = localStorage.getItem(this.config.storageKeys.content);
            if (saved) {
                this.elements.markdownInput.value = saved;
            }
        } catch (error) {
            console.error('Failed to load saved content:', error);
        }
    }

    /**
     * Load settings from localStorage
     */
    loadSettings() {
        try {
            // Dark mode
            const darkMode = localStorage.getItem(this.config.storageKeys.darkMode) === 'true';
            this.state.darkMode = darkMode;
            this.elements.themeToggle.checked = darkMode;
            if (darkMode) {
                document.body.classList.add('dark-mode');
            }

            // Auto-render
            const autoRender = localStorage.getItem(this.config.storageKeys.autoRender) === 'true';
            this.state.autoRender = autoRender;
            this.elements.autoRenderToggle.checked = autoRender;
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }

    /**
     * Toggle dark mode
     */
    toggleDarkMode(enabled) {
        this.state.darkMode = enabled;

        if (enabled) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }

        localStorage.setItem(this.config.storageKeys.darkMode, enabled);
        this.showToast(`Dark mode ${enabled ? 'enabled' : 'disabled'}`, 'info');
    }

    /**
     * Toggle auto-render
     */
    toggleAutoRender(enabled) {
        this.state.autoRender = enabled;
        localStorage.setItem(this.config.storageKeys.autoRender, enabled);
        this.showToast(`Auto-render ${enabled ? 'enabled' : 'disabled'}`, 'info');
    }

    /**
     * Open settings modal
     */
    openSettingsModal() {
        this.elements.settingsModal.style.display = 'flex';
    }

    /**
     * Close settings modal
     */
    closeSettingsModal() {
        this.elements.settingsModal.style.display = 'none';
    }

    /**
     * Show loading overlay
     */
    showLoading(show) {
        this.elements.loadingOverlay.style.display = show ? 'flex' : 'none';
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        this.elements.toastContainer.appendChild(toast);

        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);

        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    this.elements.toastContainer.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }

    /**
     * Register service worker
     */
    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('Service Worker registered:', registration.scope);
                })
                .catch(error => {
                    console.error('Service Worker registration failed:', error);
                });
        }
    }
}

// ============================================================================
// DIAGRAM VIEWER CLASS (Modal with Zoom, Pan, Navigation)
// ============================================================================

class DiagramViewer {
    constructor(app) {
        this.app = app;
        this.currentIndex = 0;
        this.zoom = 1.0;
        this.panX = 0;
        this.panY = 0;
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;
        this.lastTap = 0;
        this.touchDistance = 0;

        // Create modal DOM structure
        this.createModal();
        this.registerEventListeners();
    }

    /**
     * Create modal HTML structure
     */
    createModal() {
        const modal = document.createElement('div');
        modal.id = 'diagramViewerModal';
        modal.className = 'diagram-viewer-modal';
        modal.innerHTML = `
            <div class="diagram-viewer-backdrop"></div>

            <!-- Close Button -->
            <button class="viewer-close-btn" aria-label="Close">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>

            <!-- Navigation Arrows -->
            <button class="viewer-nav-btn viewer-prev-btn" aria-label="Previous">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
            </button>
            <button class="viewer-nav-btn viewer-next-btn" aria-label="Next">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </button>

            <!-- Diagram Container -->
            <div class="viewer-diagram-container">
                <div class="viewer-diagram-content"></div>
            </div>

            <!-- Controls Bar -->
            <div class="viewer-controls">
                <!-- Diagram Info -->
                <div class="viewer-info">
                    <span class="viewer-type-badge"></span>
                    <span class="viewer-position"></span>
                </div>

                <!-- Zoom Controls -->
                <div class="viewer-zoom-controls">
                    <button class="viewer-zoom-btn" data-action="zoom-out" aria-label="Zoom Out">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="8" y1="11" x2="14" y2="11"></line>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                    </button>
                    <span class="viewer-zoom-level">100%</span>
                    <button class="viewer-zoom-btn" data-action="zoom-in" aria-label="Zoom In">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="11" y1="8" x2="11" y2="14"></line>
                            <line x1="8" y1="11" x2="14" y2="11"></line>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                    </button>
                    <button class="viewer-zoom-btn" data-action="zoom-reset" aria-label="Reset Zoom">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 4v6h6"></path>
                            <path d="M23 20v-6h-6"></path>
                            <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
                        </svg>
                    </button>
                    <button class="viewer-zoom-btn" data-action="zoom-fit" aria-label="Fit to Screen">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
                        </svg>
                    </button>
                </div>

                <!-- Keyboard Shortcuts Hint -->
                <div class="viewer-shortcuts-hint">
                    <span>💡 ESC to close • Arrows to navigate • +/- to zoom</span>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.modal = modal;

        // Cache modal elements
        this.elements = {
            modal: modal,
            backdrop: modal.querySelector('.diagram-viewer-backdrop'),
            closeBtn: modal.querySelector('.viewer-close-btn'),
            prevBtn: modal.querySelector('.viewer-prev-btn'),
            nextBtn: modal.querySelector('.viewer-next-btn'),
            container: modal.querySelector('.viewer-diagram-container'),
            content: modal.querySelector('.viewer-diagram-content'),
            typeBadge: modal.querySelector('.viewer-type-badge'),
            position: modal.querySelector('.viewer-position'),
            zoomLevel: modal.querySelector('.viewer-zoom-level'),
            zoomControls: modal.querySelectorAll('.viewer-zoom-btn')
        };
    }

    /**
     * Register event listeners for modal interactions
     */
    registerEventListeners() {
        // Close button
        this.elements.closeBtn.addEventListener('click', () => this.close());

        // Backdrop click
        this.elements.backdrop.addEventListener('click', () => this.close());

        // Navigation buttons
        this.elements.prevBtn.addEventListener('click', () => this.previous());
        this.elements.nextBtn.addEventListener('click', () => this.next());

        // Zoom controls
        this.elements.zoomControls.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleZoomControl(e));
        });

        // Mouse drag events
        this.elements.content.addEventListener('mousedown', (e) => this.handleDragStart(e));
        window.addEventListener('mousemove', (e) => this.handleDragMove(e));
        window.addEventListener('mouseup', () => this.handleDragEnd());

        // Touch events
        this.elements.content.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: false });
        this.elements.content.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
        this.elements.content.addEventListener('touchend', (e) => this.handleTouchEnd(e));

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));

        // Prevent context menu on long press
        this.elements.content.addEventListener('contextmenu', (e) => e.preventDefault());
    }

    /**
     * Open modal and display diagram at index
     */
    open(index = 0) {
        if (!this.app.state.diagrams || this.app.state.diagrams.length === 0) {
            return;
        }

        this.currentIndex = Math.max(0, Math.min(index, this.app.state.diagrams.length - 1));
        this.resetView();
        this.loadDiagram();
        this.updateUI();
        this.elements.modal.classList.add('active');
        document.body.style.overflow = 'hidden'; // Prevent background scroll
    }

    /**
     * Close modal
     */
    close() {
        this.elements.modal.classList.remove('active');
        document.body.style.overflow = ''; // Restore scroll
    }

    /**
     * Load current diagram into viewer
     */
    loadDiagram() {
        const diagram = this.app.state.diagrams[this.currentIndex];
        if (!diagram) return;

        this.elements.content.innerHTML = diagram.svg;
        this.elements.typeBadge.textContent = diagram.type;
        this.updatePosition();
    }

    /**
     * Navigate to previous diagram
     */
    previous() {
        this.currentIndex--;
        if (this.currentIndex < 0) {
            this.currentIndex = this.app.state.diagrams.length - 1; // Wrap around
        }
        this.resetView();
        this.loadDiagram();
        this.updateUI();
    }

    /**
     * Navigate to next diagram
     */
    next() {
        this.currentIndex++;
        if (this.currentIndex >= this.app.state.diagrams.length) {
            this.currentIndex = 0; // Wrap around
        }
        this.resetView();
        this.loadDiagram();
        this.updateUI();
    }

    /**
     * Handle zoom control buttons
     */
    handleZoomControl(event) {
        const action = event.currentTarget.dataset.action;

        switch (action) {
            case 'zoom-in':
                this.zoomIn();
                break;
            case 'zoom-out':
                this.zoomOut();
                break;
            case 'zoom-reset':
                this.resetZoom();
                break;
            case 'zoom-fit':
                this.fitToScreen();
                break;
        }
    }

    /**
     * Zoom in
     */
    zoomIn() {
        this.setZoom(this.zoom + this.app.config.viewer.zoomStep);
    }

    /**
     * Zoom out
     */
    zoomOut() {
        this.setZoom(this.zoom - this.app.config.viewer.zoomStep);
    }

    /**
     * Reset zoom to 100%
     */
    resetZoom() {
        this.setZoom(1.0);
        this.panX = 0;
        this.panY = 0;
        this.updateTransform();
    }

    /**
     * Fit diagram to screen
     */
    fitToScreen() {
        const containerRect = this.elements.container.getBoundingClientRect();
        const contentRect = this.elements.content.firstElementChild?.getBoundingClientRect();

        if (!contentRect) return;

        const scaleX = containerRect.width / contentRect.width;
        const scaleY = containerRect.height / contentRect.height;
        const scale = Math.min(scaleX, scaleY, 1.0) * 0.9; // 90% to add padding

        this.setZoom(scale);
        this.panX = 0;
        this.panY = 0;
        this.updateTransform();
    }

    /**
     * Set zoom level with constraints
     */
    setZoom(newZoom) {
        this.zoom = Math.max(
            this.app.config.viewer.minZoom,
            Math.min(newZoom, this.app.config.viewer.maxZoom)
        );
        this.updateTransform();
        this.updateZoomDisplay();
    }

    /**
     * Update zoom level display
     */
    updateZoomDisplay() {
        this.elements.zoomLevel.textContent = `${Math.round(this.zoom * 100)}%`;
    }

    /**
     * Update diagram position display
     */
    updatePosition() {
        this.elements.position.textContent = `${this.currentIndex + 1} / ${this.app.state.diagrams.length}`;
    }

    /**
     * Update UI elements
     */
    updateUI() {
        this.updateZoomDisplay();
        this.updatePosition();

        // Update navigation button visibility
        const hasMult = this.app.state.diagrams.length > 1;
        this.elements.prevBtn.style.display = hasMult ? 'flex' : 'none';
        this.elements.nextBtn.style.display = hasMult ? 'flex' : 'none';

        // Update cursor based on zoom
        this.elements.content.style.cursor = this.zoom > 1.0 ? 'grab' : 'default';
    }

    /**
     * Reset view (zoom and pan)
     */
    resetView() {
        this.zoom = 1.0;
        this.panX = 0;
        this.panY = 0;
        this.updateTransform();
    }

    /**
     * Update transform (apply zoom and pan)
     */
    updateTransform() {
        this.elements.content.style.transform = `translate(${this.panX}px, ${this.panY}px) scale(${this.zoom})`;
        this.elements.content.style.cursor = this.isDragging ? 'grabbing' : (this.zoom > 1.0 ? 'grab' : 'default');
    }

    /**
     * Handle drag start (mouse)
     */
    handleDragStart(event) {
        if (this.zoom <= 1.0) return; // Only drag when zoomed in

        this.isDragging = true;
        this.dragStartX = event.clientX - this.panX;
        this.dragStartY = event.clientY - this.panY;
        this.updateTransform();
        event.preventDefault();
    }

    /**
     * Handle drag move (mouse)
     */
    handleDragMove(event) {
        if (!this.isDragging) return;

        this.panX = event.clientX - this.dragStartX;
        this.panY = event.clientY - this.dragStartY;
        this.updateTransform();
    }

    /**
     * Handle drag end (mouse)
     */
    handleDragEnd() {
        this.isDragging = false;
        this.updateTransform();
    }

    /**
     * Handle touch start
     */
    handleTouchStart(event) {
        const now = Date.now();
        const timeDiff = now - this.lastTap;

        // Double-tap detection
        if (timeDiff < 300 && timeDiff > 0) {
            this.handleDoubleTap(event);
            this.lastTap = 0;
            return;
        }
        this.lastTap = now;

        if (event.touches.length === 2) {
            // Pinch zoom start
            this.touchDistance = this.getTouchDistance(event.touches);
            event.preventDefault();
        } else if (event.touches.length === 1 && this.zoom > 1.0) {
            // Single finger drag (when zoomed)
            const touch = event.touches[0];
            this.isDragging = true;
            this.dragStartX = touch.clientX - this.panX;
            this.dragStartY = touch.clientY - this.panY;
            event.preventDefault();
        }
    }

    /**
     * Handle touch move
     */
    handleTouchMove(event) {
        if (event.touches.length === 2) {
            // Pinch zoom
            const newDistance = this.getTouchDistance(event.touches);
            const scale = newDistance / this.touchDistance;
            this.setZoom(this.zoom * scale);
            this.touchDistance = newDistance;
            event.preventDefault();
        } else if (event.touches.length === 1 && this.isDragging) {
            // Single finger drag
            const touch = event.touches[0];
            this.panX = touch.clientX - this.dragStartX;
            this.panY = touch.clientY - this.dragStartY;
            this.updateTransform();
            event.preventDefault();
        }
    }

    /**
     * Handle touch end
     */
    handleTouchEnd(event) {
        if (event.touches.length === 0) {
            this.isDragging = false;
            this.updateTransform();
        }
    }

    /**
     * Handle double-tap to zoom
     */
    handleDoubleTap(event) {
        if (this.zoom > 1.0) {
            this.resetZoom();
        } else {
            this.setZoom(this.app.config.viewer.doubleTapZoom);
        }
        event.preventDefault();
    }

    /**
     * Get distance between two touch points
     */
    getTouchDistance(touches) {
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboard(event) {
        // Only handle if modal is open
        if (!this.elements.modal.classList.contains('active')) return;

        switch (event.key) {
            case 'Escape':
                this.close();
                event.preventDefault();
                break;
            case 'ArrowLeft':
                this.previous();
                event.preventDefault();
                break;
            case 'ArrowRight':
                this.next();
                event.preventDefault();
                break;
            case '+':
            case '=':
                this.zoomIn();
                event.preventDefault();
                break;
            case '-':
            case '_':
                this.zoomOut();
                event.preventDefault();
                break;
            case '0':
                this.resetZoom();
                event.preventDefault();
                break;
            case 'f':
            case 'F':
                this.fitToScreen();
                event.preventDefault();
                break;
        }
    }
}

// ============================================================================
// INITIALIZE APP
// ============================================================================

// Wait for DOM and Mermaid to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

function initApp() {
    // Wait for Mermaid to be available
    const checkMermaid = setInterval(() => {
        if (window.mermaid) {
            clearInterval(checkMermaid);
            window.app = new MermaidVisualizerApp();
        }
    }, 100);

    // Timeout after 5 seconds
    setTimeout(() => {
        clearInterval(checkMermaid);
        if (!window.mermaid) {
            console.error('Mermaid.js failed to load');
            alert('Failed to load Mermaid.js. Please refresh the page.');
        }
    }, 5000);
}
