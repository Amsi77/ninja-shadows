// Ninja Shadows: network first, so a new upload reaches every phone on its next launch;
// the last good copy stays cached so the game still opens offline.
const CACHE = 'ninja-shadows-v4-haifa';
const FILES = ["./", "./index.html", "./vendor/three.min.js", "./assets/city1.jpg", "./assets/paris2.jpg", "./assets/city4.jpg", "./assets/city1-hd.png", "./assets/city3.jpg", "./assets/chain.png", "./assets/drummer.png", "./assets/breaker.png", "./assets/pulse.png", "./assets/paris4.jpg", "./assets/city3-hd.png", "./assets/blue.png", "./assets/grunt.png", "./assets/city4-hd.png", "./assets/kit.png", "./assets/logo.webp", "./assets/city5.jpg", "./assets/city2.jpg", "./assets/boss.png", "./assets/redpk.png", "./assets/striker.png", "./assets/paris1.jpg", "./assets/citymap.jpg", "./assets/ember.png", "./assets/echo.png", "./assets/warden.png", "./assets/sguard.png", "./assets/frost.png", "./assets/raven.png", "./assets/archer.png", "./assets/shadow.png", "./assets/red.png", "./assets/city6.jpg", "./assets/thrower.png", "./assets/bluepk.png", "./assets/paris3.jpg", "./assets/viper.png", "./assets/emperor.png", "./music/old-city.mp3", "./assets/haifa1.jpg", "./assets/haifa2.jpg", "./assets/haifa3.jpg", "./assets/haifa4.jpg", "./assets/haifa5.jpg", "./assets/haifa6.jpg"];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('ninja-shadows-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
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
      return hit || (e.request.mode === 'navigate' ? await caches.match('./index.html') : Response.error());
    }
  })());
});
