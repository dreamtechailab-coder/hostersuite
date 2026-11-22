/* Web Push handlers, imported into the Workbox-generated service worker. */

// The app lives under the SW scope (e.g. /hostelsuite/). The backend sends
// app-relative paths like "/tenant/X", so resolve them against the scope.
const appUrl = (url) => new URL(String(url || '').replace(/^\/+/, ''), self.registration.scope).href

self.addEventListener('push', (event) => {
  let data = {}
  try {
    data = event.data ? event.data.json() : {}
  } catch (e) {
    data = { title: event.data && event.data.text() }
  }
  const title = data.title || 'PG Manager'
  event.waitUntil(
    self.registration.showNotification(title, {
      body: data.body || '',
      icon: appUrl('icons/pwa-192x192.png'),
      badge: appUrl('icons/pwa-64x64.png'),
      data: { url: appUrl(data.url) },
    }),
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const url = (event.notification.data && event.notification.data.url) || self.registration.scope
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if ('focus' in client) {
          client.navigate(url)
          return client.focus()
        }
      }
      return self.clients.openWindow(url)
    }),
  )
})
