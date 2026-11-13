/* Static shell only: never cache private /api responses. */
const CACHE='sportcoach-static-v2';
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['/assets/styles.css','/assets/app.js','/assets/icon.svg']))));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))));
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);if(u.origin!==self.location.origin||u.pathname.startsWith('/api/')||e.request.method!=='GET')return;if(u.pathname.startsWith('/assets/'))e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)))});
