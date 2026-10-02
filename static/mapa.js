(() => {
  const element = document.getElementById('map');
  if (!element) return;
  const status = document.getElementById('map-status');
  const printButton = document.getElementById('print-map');
  const map = L.map(element, { preferCanvas: true }).setView([-1.03, -79.46], 13);
  const tiles = L.tileLayer(element.dataset.tileUrl, {
    maxZoom: 20,
    attribution: element.dataset.tileAttribution,
  }).addTo(map);
  tiles.on('tileerror', () => {
    document.getElementById('basemap-warning').hidden = false;
  });
  const bounds = JSON.parse(document.getElementById('map-bbox').textContent);
  if (bounds) map.fitBounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]], { padding: [70, 70] });
  let layer, controller;
  const colors = {
    LISTO_PARA_NOTIFICAR: '#2563eb', ASIGNADO_NOTIFICACION: '#d97706',
    NOTIFICADO: '#15803d', NO_NOTIFICADO: '#dc2626', INCIDENCIA: '#dc2626',
  };
  async function load() {
    if (controller) controller.abort();
    controller = new AbortController();
    if (printButton) printButton.disabled = true;
    const b = map.getBounds();
    const query = new URLSearchParams({
      orden: element.dataset.orden,
      bbox: [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].join(','),
    });
    if (element.dataset.lote) query.set('lote', element.dataset.lote);
    try {
      const response = await fetch(element.dataset.endpoint + '?' + query, { signal: controller.signal });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'No se pudo cargar el mapa');
      if (layer) map.removeLayer(layer);
      layer = L.geoJSON(data, {
        style: feature => ({ color: colors[feature.properties.estado] || '#64748b', weight: 2, fillOpacity: .24 }),
        onEachFeature: (feature, polygon) => {
          const properties = feature.properties;
          const popup = document.createElement('div');
          for (const value of ['Expediente ' + properties.expediente, properties.estado, properties.direccion]) {
            const line = document.createElement('p');
            line.textContent = value;
            popup.appendChild(line);
          }
          polygon.bindPopup(popup);
          const label = document.createElement('span');
          label.textContent = properties.etiqueta_mapa;
          polygon.bindTooltip(label, { permanent: true, direction: 'center' });
        },
      }).addTo(map);
      status.textContent = data.features.length + ' predios visibles. Las etiquetas usan el número oficial o el ID interno abreviado; haga clic para ver el expediente completo.';
      if (printButton) printButton.disabled = false;
    } catch (error) {
      if (error.name !== 'AbortError') status.textContent = error.message;
    }
  }
  let timer;
  map.on('moveend', () => { clearTimeout(timer); timer = setTimeout(load, 250); });
  load();
  window.addEventListener('beforeprint', () => map.invalidateSize());
  window.addEventListener('afterprint', () => map.invalidateSize());
})();
