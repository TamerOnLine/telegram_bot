// -----------------------------
// Basic Pi integration hooks
// -----------------------------
function onPiLogin() {
  const statusEl = document.getElementById("pi-status");
  statusEl.textContent = "Pi: Connected (mock)";
}

function onPiPayment() {
  alert("Pi payment placeholder");
}

function grantPiReward(amount = 1) {
  console.log(`Reward granted: ${amount}`);
}

// -----------------------------
const GAME_STATE = {
  MENU: "MENU",
  PLAYING: "PLAYING",
  PAUSED: "PAUSED",
  GAME_OVER: "GAME_OVER",
};

const game = {
  state: GAME_STATE.MENU,
  score: 0,
  level: 1,
  lastTime: 0,
  spawnTimer: 0,
  spawnInterval: 1.0,
  player: { x: 100, y: 200, width: 40, height: 40, speed: 260, color: "#22c55e" },
  enemies: [],
  keys: {},
};

// -----------------------------
const canvas = document.getElementById("game-canvas");
const ctx = canvas.getContext("2d");

const uiState = document.getElementById("ui-state");
const uiScore = document.getElementById("ui-score");
const uiLevel = document.getElementById("ui-level");

// Keyboard control
window.addEventListener("keydown", (e) => {
  game.keys[e.key.toLowerCase()] = true;

  if (e.key === " ") handleStartPause();
  if (e.key.toLowerCase() === "r" && game.state === GAME_STATE.GAME_OVER) startGame();
});

window.addEventListener("keyup", (e) => {
  game.keys[e.key.toLowerCase()] = false;
});

// -----------------------------
function handleStartPause() {
  if (game.state === GAME_STATE.MENU || game.state === GAME_STATE.GAME_OVER) startGame();
  else if (game.state === GAME_STATE.PLAYING) pauseGame();
  else if (game.state === GAME_STATE.PAUSED) resumeGame();
}

// -----------------------------
function startGame() {
  game.state = GAME_STATE.PLAYING;
  game.score = 0;
  game.level = 1;
  game.enemies = [];
  uiState.textContent = game.state;
}

function pauseGame() {
  game.state = GAME_STATE.PAUSED;
  uiState.textContent = game.state;
}

function resumeGame() {
  game.state = GAME_STATE.PLAYING;
  uiState.textContent = game.state;
}

function gameOver() {
  game.state = GAME_STATE.GAME_OVER;
  uiState.textContent = game.state;
}

// -----------------------------
function spawnEnemy() {
  const size = 30 + Math.random() * 20;
  const y = Math.random() * (canvas.height - size);
  const speed = 200 + Math.random() * 100;

  game.enemies.push({ x: canvas.width + size, y, width: size, height: size, speed, color: "#ef4444" });
}

// -----------------------------
function update(dt) {
  if (game.state !== GAME_STATE.PLAYING) return;

  const p = game.player;

  // Move
  if (game.keys["arrowleft"]) p.x -= p.speed * dt;
  if (game.keys["arrowright"]) p.x += p.speed * dt;
  if (game.keys["arrowup"]) p.y -= p.speed * dt;
  if (game.keys["arrowdown"]) p.y += p.speed * dt;

  // Clamp
  if (p.x < 0) p.x = 0;
  if (p.y < 0) p.y = 0;
  if (p.x + p.width > canvas.width) p.x = canvas.width - p.width;
  if (p.y + p.height > canvas.height) p.y = canvas.height - p.height;

  game.score += dt * 15;
  uiScore.textContent = Math.floor(game.score);

  // Harder levels
  if (game.score > game.level * 60) {
    game.level++;
    uiLevel.textContent = game.level;
    game.spawnInterval = Math.max(0.4, game.spawnInterval - 0.05);
  }

  game.spawnTimer += dt;
  if (game.spawnTimer >= game.spawnInterval) {
    game.spawnTimer = 0;
    spawnEnemy();
  }

  const remaining = [];
  for (const e of game.enemies) {
    e.x -= e.speed * dt;

    if (rectsCollide(p, e)) return gameOver();
    if (e.x + e.width > 0) remaining.push(e);
  }
  game.enemies = remaining;
}

// -----------------------------
function rectsCollide(a, b) {
  return !(
    a.x + a.width < b.x ||
    a.x > b.x + b.width ||
    a.y + a.height < b.y ||
    a.y > b.y + b.height
  );
}

// -----------------------------
function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Player
  ctx.fillStyle = game.player.color;
  ctx.fillRect(game.player.x, game.player.y, game.player.width, game.player.height);

  // Enemies
  for (const e of game.enemies) {
    ctx.fillStyle = e.color;
    ctx.fillRect(e.x, e.y, e.width, e.height);
  }
}

// -----------------------------
function loop(ts) {
  const dt = (ts - game.lastTime) / 1000;
  game.lastTime = ts;
  update(dt);
  render();
  requestAnimationFrame(loop);
}

// -----------------------------
// Mobile Controls
// -----------------------------
document.querySelectorAll(".mc-btn").forEach((btn) => {
  const dir = btn.dataset.dir;

  const start = () => {
    if (dir === "up") game.keys["arrowup"] = true;
    if (dir === "down") game.keys["arrowdown"] = true;
    if (dir === "left") game.keys["arrowleft"] = true;
    if (dir === "right") game.keys["arrowright"] = true;
    if (game.state !== GAME_STATE.PLAYING) startGame();
  };

  const stop = () => {
    game.keys["arrowup"] = false;
    game.keys["arrowdown"] = false;
    game.keys["arrowleft"] = false;
    game.keys["arrowright"] = false;
  };

  btn.addEventListener("touchstart", (e) => { e.preventDefault(); start(); });
  btn.addEventListener("touchend", (e) => { e.preventDefault(); stop(); });
  btn.addEventListener("mousedown", start);
  btn.addEventListener("mouseup", stop);
});

// Start game on tap
canvas.addEventListener("touchstart", (e)=>{ e.preventDefault(); handleStartPause(); });

// Init
uiState.textContent = game.state;
requestAnimationFrame(loop);
