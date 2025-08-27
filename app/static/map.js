const map = L.map('map').setView([0, 0], 2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

fetch('/photos')
  .then(resp => resp.json())
  .then(data => {
    const markers = L.markerClusterGroup();
    data.forEach(p => {
      if (p.latitude !== null && p.longitude !== null) {
        const marker = L.marker([p.latitude, p.longitude]);
        marker.bindTooltip(`<img src="${p.url}" alt="photo" />`);
        markers.addLayer(marker);
      }
    });
    map.addLayer(markers);
  });
