
class ChartView {
  constructor() {
    this.distributionChart = null;
    this.timeChart = null;
  }

  render(location) {
    this._renderDistribution(location);
    this._renderTime(location);
  }

  _renderDistribution(location) {
    const ctx = document.getElementById('distributionChart');

    // If data is missing or empty
    if (!Array.isArray(location.distribution) || location.distribution.length === 0) {
      if (this.distributionChart) {
        this.distributionChart.destroy();
        this.distributionChart = null;
      }
      this._drawNoData(ctx);
      return;
    }

    if (!this.distributionChart) {
      this.distributionChart = createDistributionChart(ctx, location)
    } else {
      this.distributionChart.data.datasets[0].data = location.distribution;
      this.distributionChart.update();
    }
  }

  _renderTime(location) {
    const ctx = document.getElementById('timeChart');

    if (!Array.isArray(location.time) || location.time.length === 0) {
      if (this.timeChart) {
        this.timeChart.destroy();
        this.timeChart = null;
      }
      this._drawNoData(ctx);
      return;
    }

    if (!this.timeChart) {
      this.timeChart = createTimeChart(ctx, location)
    } else {
      this.timeChart.data.datasets[0].data = location.time;
      this.timeChart.update();
    }
  }

  destroy() {
    this.distributionChart?.destroy();
    this.timeChart?.destroy();
    this.distributionChart = null;
    this.timeChart = null;
  }

  _drawNoData(ctx) {
    const canvas = ctx.getContext('2d');
    canvas.clearRect(0, 0, ctx.width, ctx.height);
    canvas.font = '16px sans-serif';
    canvas.fillStyle = '#666';
    canvas.textAlign = 'center';
    canvas.textBaseline = 'middle';
    canvas.fillText('No data available', ctx.width / 2, ctx.height / 2);
  }
}

function initOverlay() {
  // Back to map
  document.getElementById("back-to-map").onclick = () => {
    document.getElementById("location-detail").style.display = "none";
    if (window.innerWidth < 900) {
      document.getElementById("map").scrollIntoView({ behavior: "smooth" });
    };
  }

}

function createTimeChart(ctx, location) {
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['00', '01', '02', '03', '04', '05',
        '06', '07', '08', '09', '10', '11',
        '12', '13', '14', '15', '16', '17',
        '18', '19', '20', '21', '22', '23'],
      datasets: [{ data: location.time, tension: 0.3 }]
    },
    options: { plugins: { legend: { display: false } } }
  });
}

function createDistributionChart(ctx, location) {
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['<5', '5-10', '10-15', '15-20', '20-25', '25-30', '30-35', '35-40', '40-45', '45-50', '50 - 55', '55 - 60', '60 + '],
      datasets: [{ data: location.distribution }]
    },
    options: { plugins: { legend: { display: false } } }
  });
}

function showDetails(charts, location) {
  const name = location.name ?? 'Unknown location';
  const limit = location.limit ?? 'N/A';
  const pctSpeeding =
    location.vehicles_speeding_7_7_per_min === 0
      ? "0.00"
      : location.vehicles_speeding_7_7_per_min ?? "N/A";

  const avgSpeed = location.percent_speeding_7_7 ?? "N/A";
  const distribution = Array.isArray(location.distribution)
    ? location.distribution
    : [];
  const time = Array.isArray(location.time)
    ? location.time
    : [];

  // Update DOM safely
  document.getElementById('location-name').textContent = name;
  document.getElementById('location-meta').textContent =
    limit !== 'N/A' ? `Speed limit: ${limit} mph` : 'Speed limit: N/A';
  document.getElementById('pct-speeding').textContent = pctSpeeding;
  document.getElementById('avg-speed').textContent = avgSpeed + "%";

  const detailEl = document.getElementById('location-detail');
  detailEl.style.display = 'block';

  if (window.innerWidth < 900) {
    detailEl.scrollIntoView({ behavior: 'smooth' });
  }

  // Pass a safe object to charts
  charts.render({
    ...location,
    distribution,
    time
  });
}

