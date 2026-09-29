import * as maplibregl from 'https://unpkg.com/maplibre-gl@^6.11.2/dist/maplibre-gl.mjs';

document.addEventListener("DOMContentLoaded", () => {
  const map = new maplibregl.Map({
    container: 'map',
    // style: 'https://demotiles.maplibre.org/style.json',
    style: 'https://api.maptiler.com/maps/dataviz/style.json?key=V4XRenuxfw0NUYH5jX3e',
    center: [-74.006, 40.7128],
    zoom: 15,
  });
});
