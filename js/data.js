async function loadData() {
  const response = await fetch('data/locations.json')
  const data = await response.json();
  console.log("Loaded locations:", data);
  return data
}


