const ACCESS_TOKEN = "secretBirdSound123";

const params = new URLSearchParams(window.location.search);
const token = params.get("token");
const sound = params.get("sound");

if (token !== ACCESS_TOKEN) {
  document.body.innerHTML = "<h2>Access Denied</h2><p>Invalid or missing token.</p>";
  throw new Error("Access denied");
}

if (!sound) {
  document.body.innerHTML = "<h2>No Sound Specified</h2><p>Please add a 'sound' parameter in the URL.</p>";
  throw new Error("No sound provided");
}

const container = document.getElementById("player-container");

const title = document.createElement("h1");
title.textContent = `Now Playing: ${decodeURIComponent(sound)}`;

const audio = document.createElement("audio");
audio.controls = true;
console.log(`sounds/${decodeURIComponent(sound)}.mp3`);
audio.src = `sounds/${decodeURIComponent(sound)}.mp3`;


container.appendChild(title);
container.appendChild(audio);