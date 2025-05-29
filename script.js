const ACCESS_TOKEN = "secretBirdSound123";
const urlToken = new URLSearchParams(window.location.search).get("token");

if (urlToken !== ACCESS_TOKEN) {
  document.body.innerHTML = "<h2>Access Denied</h2><p>Invalid or missing token.</p>";
  throw new Error("Access denied");
}

fetch('data/sounds.json')
  .then(response => response.json())
  .then(sounds => {
    const container = document.getElementById('sound-list');
    sounds.forEach((sound, index) => {
      const div = document.createElement('div');
      div.className = "sound-item";
      div.innerHTML = `
        <p>${sound.name}</p>
        <audio id="audio${index}" src="sounds/${sound.file}"></audio>
        <button onclick="document.getElementById('audio${index}').play()">Play</button>
      `;
      container.appendChild(div);
    });
  });