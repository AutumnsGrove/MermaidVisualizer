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

            // Click to view full diagram
            card.addEventListener('click', () => this.viewDiagram(diagram.id));

            this.elements.diagramGallery.appendChild(card);
        });
    }

    /**
     * View a specific diagram (scroll to it)
     */
    viewDiagram(diagramId) {
        const element = document.getElementById(diagramId);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            element.classList.add('highlight');
            setTimeout(() => element.classList.remove('highlight'), 2000);
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
