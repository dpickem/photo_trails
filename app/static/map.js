const map = L.map('map').setView([0, 0], 2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

let markerLayer = null;

async function loadMarkers() {
  try {
    // Fetch in larger pages to avoid huge JSON payloads.
    const pageSize = 500;
    let offset = 0;
    let points = [];
    const markers = L.markerClusterGroup();
    while (true) {
      const resp = await fetch(`/photos?with_gps=1&offset=${offset}&limit=${pageSize}`);
      const body = await resp.json();
      const items = Array.isArray(body) ? body : body.items || [];
      items.forEach(p => {
        if (p.latitude !== null && p.longitude !== null) {
          const latlng = [p.latitude, p.longitude];
          const marker = L.marker(latlng);
          marker.bindTooltip(`<img src="${p.url}" alt="photo" />`);
          markers.addLayer(marker);
          points.push(latlng);
        }
      });
      if (Array.isArray(body)) break;
      if (!body.has_more) break;
      offset += body.limit;
    }
    if (markerLayer) {
      map.removeLayer(markerLayer);
    }
    markerLayer = markers;
    map.addLayer(markerLayer);
    if (points.length > 0) {
      map.fitBounds(L.latLngBounds(points), { padding: [20, 20] });
    }
  } catch (e) {
    // ignore
  }
}

loadMarkers();

window.addEventListener('photos-updated', () => {
  loadMarkers();
});
