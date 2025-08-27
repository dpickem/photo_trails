const map = L.map('map').setView([0, 0], 2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

fetch('/photos')
  .then(resp => resp.json())
  .then(data => {
    data.forEach(p => {
      if (p.latitude !== null && p.longitude !== null) {
        const marker = L.circleMarker([p.latitude, p.longitude], { radius: 5 }).addTo(map);
        marker.bindTooltip(`<img src="${p.url}" alt="photo" />`);
      }
    });
  });
