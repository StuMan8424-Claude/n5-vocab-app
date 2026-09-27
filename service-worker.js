// Network-first with cache fallback: when online, always fetch the latest
// version (so updates show up next time you have signal); when offline
// (airplane mode), serve the last cached copy so the app still opens.
//
// { cache: 'no-store' } on the network fetch is load-bearing: without it,
// the browser's own HTTP cache can silently hand back a stale response
// (per GitHub Pages' Cache-Control headers) without ever re-checking the
// server — "network-first" logic alone doesn't help if the "network" call
// itself is quietly served from a local cache underneath it.
const CACHE_NAME = 'n5vocab-cache-v2';
const CORE_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  './icon-512-maskable.png',
  './apple-touch-icon.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => Promise.all(
        CORE_ASSETS.map((url) =>
          fetch(url, { cache: 'no-store' }).then((res) => cache.put(url, res)).catch(() => {})
        )
      ))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    fetch(event.request, { cache: 'no-store' })
      .then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        return response;
      })
      .catch(() =>
        caches.match(event.request).then((cached) => cached || caches.match('./index.html'))
      )
  );
});
