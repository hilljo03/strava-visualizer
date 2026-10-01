import * as maplibregl from 'https://unpkg.com/maplibre-gl@^6.11.2/dist/maplibre-gl.mjs';

const DATA_URL = '/data/activities_with_polylines.json';


// Decodes Google's encoded-polyline format (precision 5) into [lng, lat] pairs,
// the coordinate order GeoJSON and MapLibre expect.
function decodePolyline(encoded) {
  const coordinates = [];
  let index = 0;
  let lat = 0;
  let lng = 0;

  while (index < encoded.length) {
    let shift = 0;
    let result = 0;
    let byte;

    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);
    lat += result & 1 ? ~(result >> 1) : result >> 1;

    shift = 0;
    result = 0;
    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);
    lng += result & 1 ? ~(result >> 1) : result >> 1;

    coordinates.push([lng / 1e5, lat / 1e5]);
  }

  return coordinates;
}

function toFeatureCollection(activities) {
  const features = activities
    .map((activity) => ({
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: decodePolyline(activity.map.summary_polyline),
      },
      properties: {
        name: activity.name,
        sport_type: activity.sport_type,
        distance: activity.distance,
      },
    }))
    .filter((feature) => feature.geometry.coordinates.length > 1);

  return { type: 'FeatureCollection', features };
}

async function addRoutes(map) {
  const response = await fetch(DATA_URL);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }

  const collection = toFeatureCollection(await response.json());

  map.addSource('routes', { type: 'geojson', data: collection });
  map.addLayer({
    id: 'routes',
    type: 'line',
    source: 'routes',
    layout: { 'line-join': 'round', 'line-cap': 'round' },
    paint: { 'line-color': '#fc5200', 'line-width': 2, 'line-opacity': 0.1 },
  });

  const bounds = new maplibregl.LngLatBounds();
  for (const feature of collection.features) {
    for (const coordinate of feature.geometry.coordinates) {
      bounds.extend(coordinate);
    }
  }
  if (!bounds.isEmpty()) {
    map.fitBounds(bounds, { padding: 40, duration: 0 });
  }

  return collection.features.length;
}

document.addEventListener("DOMContentLoaded", () => {
  // Optional readout: the page renders fine without a #status element.
  const report = (message) => {
    const status = document.getElementById("status");
    if (status) status.textContent = message;
    console.log(message);
  };

  const map = new maplibregl.Map({
    container: "map",
    style: "https://api.maptiler.com/maps/dataviz/style.json?key=V4XRenuxfw0NUYH5jX3e",
    center: [-74.006, 40.7128],
    zoom: 14,
  });

  map.on('load', async () => {
    try {
      const count = await addRoutes(map);
      report(`Rendered ${count} route${count === 1 ? '' : 's'}.`);
    } catch (error) {
      report(`Could not load routes: ${error.message}`);
      console.error(error);
    }
  });
});
