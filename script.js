// Configuration
const ACCESS_TOKEN = "secretBirdSound123";

// Get URL parameters
const params = new URLSearchParams(window.location.search);
const token = params.get("token");
const soundFile = params.get("sound");

// Security check
if (token !== ACCESS_TOKEN) {
  document.body.innerHTML = "<h2>Access Denied</h2><p>Invalid or missing token.</p>";
  throw new Error("Access denied");
}

// If token is valid, show sound player
if (soundFile) {
  const audio = document.createElement("audio");
  audio.controls = true;
  audio.src = `sounds/${soundFile}`;
  document.body.innerHTML = `<h1>Now Playing: ${soundFile}</h1>`;
  document.body.appendChild(audio);
} else {
  document.body.innerHTML = "<p>No sound specified.</p>";
}



/*const ACCESS_TOKEN = "secretBirdSound123";
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
  });*/