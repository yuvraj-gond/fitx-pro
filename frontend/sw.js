const CACHE_NAME = 'fitx-pro-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/manifest.json',
  '/pages/login.html',
  '/pages/dashboard.html',
  '/pages/workout.html',
  '/pages/nutrition.html',
  '/pages/insights.html',
  '/pages/body.html',
  '/pages/profile.html',
  '/assets/css/main.css',
  '/assets/js/api.js',
  '/assets/js/shell.js',
  '/assets/icons/icon-192.png',
  '/assets/icons/icon-512.png'
];

// Install event
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(name => name !== CACHE_NAME)
          .map(name => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - Cache First, Network Fallback
self.addEventListener('fetch', event => {
  // We only handle GET requests and exclude API routes from cache-first processing
  if (event.request.method !== 'GET' || event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        // Return cached response if found
        if (cachedResponse) {
          return cachedResponse;
        }

        // Otherwise fetch from network
        return fetch(event.request).then(response => {
          // Check if we received a valid response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clone the response because it's a stream and can only be consumed once
          const responseToCache = response.clone();

          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(event.request, responseToCache);
            });

          return response;
        }).catch(() => {
          // Offline fallback
          if (event.request.mode === 'navigate') {
            return caches.match('/pages/dashboard.html');
          }
        });
      })
  );
});
