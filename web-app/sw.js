/**
 * Service Worker for Mermaid Visualizer
 * Provides offline functionality and performance optimization through intelligent caching
 */

// Cache version - increment this to force cache refresh on all clients
const CACHE_NAME = 'mermaid-visualizer-v1';

// Files to pre-cache on service worker installation
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/css/styles.css',
  '/js/app.js',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png'
];

// CDN resources that should be cached for offline use
const CDN_CACHE_URLS = [
  'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs',
  'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js'
];

/**
 * INSTALL EVENT
 * Triggered when the service worker is first installed
 * Pre-caches essential files for offline functionality
 */
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing service worker...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Pre-caching essential files');

        // Pre-cache local files
        return cache.addAll(PRECACHE_URLS)
          .then(() => {
            // Pre-cache CDN resources separately with error handling
            return Promise.allSettled(
              CDN_CACHE_URLS.map(url =>
                cache.add(url).catch(err => {
                  console.warn(`[Service Worker] Failed to cache ${url}:`, err);
                })
              )
            );
          });
      })
      .then(() => {
        console.log('[Service Worker] Pre-caching completed');
        // Force the waiting service worker to become the active service worker
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[Service Worker] Pre-caching failed:', error);
      })
  );
});

/**
 * ACTIVATE EVENT
 * Triggered when the service worker becomes active
 * Cleans up old caches and takes control of all clients
 */
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating service worker...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        // Remove outdated caches
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              // Delete caches that don't match current version
              return cacheName !== CACHE_NAME;
            })
            .map((cacheName) => {
              console.log(`[Service Worker] Deleting old cache: ${cacheName}`);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        console.log('[Service Worker] Old caches cleaned up');
        // Take control of all clients immediately
        return self.clients.claim();
      })
      .catch((error) => {
        console.error('[Service Worker] Activation failed:', error);
      })
  );
});

/**
 * FETCH EVENT
 * Intercepts all network requests and applies caching strategies
 * Uses different strategies based on request type
 */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Determine caching strategy based on request type
  if (shouldUseNetworkFirst(url)) {
    // Network-first strategy for API calls and dynamic content
    event.respondWith(networkFirstStrategy(request));
  } else {
    // Cache-first strategy for static assets
    event.respondWith(cacheFirstStrategy(request));
  }
});

/**
 * Determines if a URL should use network-first strategy
 * @param {URL} url - The URL to check
 * @returns {boolean} - True if network-first should be used
 */
function shouldUseNetworkFirst(url) {
  // Use network-first for:
  // 1. API endpoints
  // 2. GitHub Gist URLs (dynamic content)
  // 3. External data sources

  const networkFirstPatterns = [
    '/api/',
    'api.github.com',
    'gist.github.com',
    'raw.githubusercontent.com'
  ];

  return networkFirstPatterns.some(pattern =>
    url.href.includes(pattern)
  );
}

/**
 * CACHE-FIRST STRATEGY
 * Best for: Static assets (HTML, CSS, JS, images, fonts)
 * Flow: Cache → Network → Fallback
 */
async function cacheFirstStrategy(request) {
  try {
    // Try to get from cache first
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
      console.log(`[Service Worker] Cache hit: ${request.url}`);
      return cachedResponse;
    }

    // If not in cache, fetch from network
    console.log(`[Service Worker] Cache miss, fetching: ${request.url}`);
    const networkResponse = await fetch(request);

    // Cache successful responses for future use
    if (networkResponse && networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);

      // Only cache same-origin requests and CDN resources
      const url = new URL(request.url);
      if (url.origin === location.origin || isCDNResource(url)) {
        cache.put(request, networkResponse.clone());
        console.log(`[Service Worker] Cached new resource: ${request.url}`);
      }
    }

    return networkResponse;

  } catch (error) {
    console.error(`[Service Worker] Fetch failed for ${request.url}:`, error);

    // Return offline fallback if available
    return getOfflineFallback(request);
  }
}

/**
 * NETWORK-FIRST STRATEGY
 * Best for: API calls, dynamic content, real-time data
 * Flow: Network → Cache → Fallback
 */
async function networkFirstStrategy(request) {
  try {
    // Try network first
    console.log(`[Service Worker] Network first: ${request.url}`);
    const networkResponse = await fetch(request);

    // Cache successful responses
    if (networkResponse && networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
      console.log(`[Service Worker] Updated cache: ${request.url}`);
    }

    return networkResponse;

  } catch (error) {
    console.warn(`[Service Worker] Network failed for ${request.url}, trying cache:`, error);

    // Fallback to cache if network fails
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
      console.log(`[Service Worker] Serving from cache: ${request.url}`);
      return cachedResponse;
    }

    // Return offline fallback if no cache available
    return getOfflineFallback(request);
  }
}

/**
 * Checks if a URL is a CDN resource that should be cached
 * @param {URL} url - The URL to check
 * @returns {boolean} - True if URL is a CDN resource
 */
function isCDNResource(url) {
  const cdnDomains = [
    'cdn.jsdelivr.net',
    'unpkg.com',
    'cdnjs.cloudflare.com'
  ];

  return cdnDomains.some(domain => url.hostname.includes(domain));
}

/**
 * Provides offline fallback responses
 * @param {Request} request - The failed request
 * @returns {Response} - Fallback response
 */
async function getOfflineFallback(request) {
  const url = new URL(request.url);

  // For HTML requests, try to serve cached index.html
  if (request.headers.get('accept')?.includes('text/html')) {
    const cachedIndex = await caches.match('/index.html');
    if (cachedIndex) {
      console.log('[Service Worker] Serving cached index.html as fallback');
      return cachedIndex;
    }
  }

  // For other requests, return a generic offline response
  return new Response(
    JSON.stringify({
      error: 'Offline',
      message: 'You are currently offline. Please check your internet connection.'
    }),
    {
      status: 503,
      statusText: 'Service Unavailable',
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    }
  );
}

/**
 * MESSAGE EVENT
 * Allows communication between the service worker and clients
 */
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('[Service Worker] Received SKIP_WAITING message');
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CACHE_URLS') {
    console.log('[Service Worker] Received request to cache URLs');
    const urls = event.data.urls || [];

    event.waitUntil(
      caches.open(CACHE_NAME)
        .then(cache => cache.addAll(urls))
        .then(() => {
          console.log('[Service Worker] Additional URLs cached successfully');
          event.ports[0]?.postMessage({ success: true });
        })
        .catch(error => {
          console.error('[Service Worker] Failed to cache additional URLs:', error);
          event.ports[0]?.postMessage({ success: false, error: error.message });
        })
    );
  }
});

/**
 * ERROR EVENT
 * Global error handler for uncaught errors in the service worker
 */
self.addEventListener('error', (event) => {
  console.error('[Service Worker] Uncaught error:', event.error);
});

/**
 * UNHANDLED REJECTION EVENT
 * Handler for unhandled promise rejections
 */
self.addEventListener('unhandledrejection', (event) => {
  console.error('[Service Worker] Unhandled promise rejection:', event.reason);
});

console.log('[Service Worker] Service worker script loaded');
