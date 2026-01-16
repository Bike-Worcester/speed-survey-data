const MARKER_SIZE_METRICS = {
  fixed: {
    label: 'Standard',
    accessor: () => 6,
    fixed: true
  },

  vehicles_7_7_per_min: {
    label: 'Traffic volume (per min)',
    format: v => v.toFixed(1)
  },

  vehicles_speeding_7_7_per_min: {
    label: 'Speeding vehicles (per min)',
    format: v => v.toFixed(2)
  },

  percent_speeding_7_7: {
    label: '% speeding',
    format: v => `${v.toFixed(1)}%`
  }
};

function buildSelectItems(metricConfig) {
  return Object.entries(metricConfig).map(([key, cfg]) => ({
    value: key,
    label: cfg.label
  }));
}

function computeMetricStats(locations) {
  const stats = {};

  Object.keys(MARKER_SIZE_METRICS).forEach(key => {
    if (MARKER_SIZE_METRICS[key].fixed) return;

    const values = locations
      .map(l => l[key])
      .filter(v => typeof v === 'number' && !isNaN(v));

    stats[key] = {
      min: Math.min(...values),
      max: Math.max(...values)
    };
  });

  return stats;
}


function scale(value, min, max, outMin = 4, outMax = 16) {
  if (min === max) return outMin;
  return outMin + ((value - min) * (outMax - outMin)) / (max - min);
}

function getMarkerRadius(location, metricKey, stats) {
  const metric = MARKER_SIZE_METRICS[metricKey];

  if (metric.fixed) return 6;

  const value = location[metricKey];
  if (typeof value !== 'number') return 1;

  return scale(value, stats[metricKey].min, stats[metricKey].max);
}

function updateMarkerSizes(markers, mode, stats) {
  markers.forEach(({ marker, location }) => {
    const radius = getMarkerRadius(location, mode, stats);
    marker.setRadius(radius);
  });
}

const MarkerSizeControl = L.Control.extend({
  options: {
    position: 'topleft',
    markers: [],
    stats: null
  }
  ,

  onAdd: function() {
    const { markers, stats } = this.options;

    const container = L.DomUtil.create(
      'div',
      'leaflet-bar leaflet-control leaflet-control-custom'
    );

    const select = L.DomUtil.create('select', '', container);

    Object.entries(MARKER_SIZE_METRICS).forEach(([key, cfg]) => {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = cfg.label;
      select.appendChild(opt);
    });

    select.value = 'fixed';

    L.DomEvent.disableClickPropagation(container);
    L.DomEvent.on(select, 'change', e => {
      updateMarkerSizes(markers, e.target.value, stats);
    });

    return container;
  }
});

