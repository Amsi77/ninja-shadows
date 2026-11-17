// Ninja Shadows: network first, so a new upload reaches every phone on its next launch;
// the last good copy stays cached so the game still opens offline.
const CACHE = 'ninja-shadows-v2';
const FILES = ['./', './index.html', './vendor/three.min.js'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET' || e.request.headers.has('range')) return;   // streamed music: let the browser handle partial requests
  e.respondWith((async () => {
    try {
      const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), 5000);
      const r = await fetch(e.request, { cache: 'no-store', signal: ctl.signal });
      clearTimeout(t);
      if (r.status === 200 && new URL(e.request.url).origin === location.origin) (await caches.open(CACHE)).put(e.request, r.clone());
      return r;
    } catch (err) {
      const hit = await caches.match(e.request, { ignoreSearch: true });
      return hit || caches.match('./index.html');
    }
  })());
});
