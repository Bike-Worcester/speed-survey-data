function initMap() {
  const map = L.map("map").setView([52.193, -2.23], 14);


  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap"
  }).addTo(map);

  return map;
}

function addLocations(map, locations, charts) {
  // Add markers

  const markers = []
  locations.forEach(loc => {
    console.log("Adding location marker", loc.name);
    console.log("Location data", loc.lat, loc.lon);
    const marker = L.circleMarker([loc.lat, loc.lon], {
      radius: 4
    }).addTo(map);

    marker.on("click", () => showDetails(charts, loc));
    markers.push({ marker, location: loc })
  });
  return markers
}

