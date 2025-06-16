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
audio.loop = true;
audio.src = `sounds/${decodeURIComponent(sound)}.mp3`;

audio.addEventListener("play", () => {
  setTimeout(() => {
    audio.pause();
    audio.currentTime = 0;
  }, 60000);
});

const sourceButton = document.createElement("button");
sourceButton.textContent = "Show Source";

const sourceLink = document.createElement("a");
sourceLink.href = window.soundMap[sound];
sourceLink.textContent = `Source: ${window.soundMap[sound]}`;
sourceLink.target = "_blank";
sourceLink.style.display = "none";

sourceButton.addEventListener("click", () => {
  if (sourceLink.style.display === "none" || sourceLink.style.display === "") {
    sourceLink.style.display = "inline-block";
    sourceButton.textContent = "Hide Source";
  } else {
    sourceLink.style.display = "none";
    sourceButton.textContent = "Show Source";
  }
});

//sourceButton.addEventListener("click", () => {
//  sourceLink.style.display = "inline-block";
//  sourceButton.disabled = true;
//  sourceButton.textContent = "Source Shown";
//});

container.appendChild(title);
container.appendChild(audio);

if (window.soundMap[sound]) {
  container.appendChild(sourceButton);
  container.appendChild(document.createElement("br"));
  container.appendChild(sourceLink);
}