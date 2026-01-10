async function loadData() {
  const response = await fetch('data/locations.json')
  return await response.json();
}


