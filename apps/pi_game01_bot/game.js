// -----------------------------
// Basic Pi integration hooks
// -----------------------------
// لاحقًا تستبدل هذه بدوال Pi / CiDi الحقيقية

function onPiLogin() {
  console.log("Pi login clicked (placeholder).");
  const statusEl = document.getElementById("pi-status");
  statusEl.textContent = "Pi: Connected (mock user)";
}

function onPiPayment() {
  console.log("Pi payment clicked (placeholder).");
  alert("Pi payment placeholder – integrate real Pi API here.");
}

function grantPiReward(amount = 1) {
  console.log(`Granting Pi reward: ${amount} (placeholder).`);
}

// -----------------------------
// Game constants and state
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
  spawnInterval: 1.0, // ثانية بين كل عدو وآخر (تقل مع الوقت)
  player: {
    x: 100,
    y: 200,
    width: 40,
    height: 40,
    speed: 260,
    color: "#22c55e",
  },
  enemies: [],
  keys: {},
};

// -----------------------------
// DOM setup
// -----------------------------
const canvas = document.getElementById("game-canvas");
const ctx = canvas.getContext("2d");

const uiState = document.getElementById("ui-state");
const uiScore = document.getElementById("ui-score");
const uiLevel = document.getElementById("ui-level");

document.getElementById("btn-pi-login").addEventListener("click", onPiLogin);
document.getElementById("btn-pi-payment").addEventListener("click", onPiPayment);

// Keyboard events
window.addEventListener("keydown", (e) => {
  game.keys[e.key.toLowerCase()] = true;

  if (e.key === " ") {
    e.preventDefault();
    if (game.state === GAME_STATE.MENU || game.state === GAME_STATE.GAME_OVER) {
      startGame();
    } else if (game.state === GAME_STATE.PLAYING) {
      pauseGame();
    } else if (game.state === GAME_STATE.PAUSED) {
      resumeGame();
    }
  }

  if (e.key.toLowerCase() === "r") {
    if (game.state === GAME_STATE.GAME_OVER) {
      startGame();
    }
  }
});

window.addEventListener("keyup", (e) => {
  game.keys[e.key.toLowerCase()] = false;
});

// -----------------------------
// Helpers
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
// Game control
// -----------------------------
function startGame() {
  game.state = GAME_STATE.PLAYING;
  game.score = 0;
  game.level = 1;
  game.spawnTimer = 0;
  game.spawnInterval = 1.0;
  game.enemies = [];

  game.player.x = canvas.width / 4;
  game.player.y = canvas.height / 2 - game.player.height / 2;
  game.player.speed = 260;

  uiState.textContent = game.state;
  uiScore.textContent = game.score.toFixed(0);
  uiLevel.textContent = game.level;
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

  // مكافأة Pi تجريبية لو وصلت سكور معيّن
  if (game.score >= 80) {
    grantPiReward(1); // placeholder
  }
}

// -----------------------------
// Enemy logic
// -----------------------------
function spawnEnemy() {
  const size = 30 + Math.random() * 20;
  const y = Math.random() * (canvas.height - size);
  const baseSpeed = 180 + game.level * 25;
  const speed = baseSpeed + Math.random() * 80;

  game.enemies.push({
    x: canvas.width + size,
    y,
    width: size,
    height: size,
    speed,
    color: "#ef4444",
  });
}

// -----------------------------
// Game loop
// -----------------------------
function update(dt) {
  if (game.state !== GAME_STATE.PLAYING) return;

  const p = game.player;

  // Movement
  if (game.keys["arrowleft"] || game.keys["a"]) p.x -= p.speed * dt;
  if (game.keys["arrowright"] || game.keys["d"]) p.x += p.speed * dt;
  if (game.keys["arrowup"] || game.keys["w"]) p.y -= p.speed * dt;
  if (game.keys["arrowdown"] || game.keys["s"]) p.y += p.speed * dt;

  // Bounds
  if (p.x < 0) p.x = 0;
  if (p.y < 0) p.y = 0;
  if (p.x + p.width > canvas.width) p.x = canvas.width - p.width;
  if (p.y + p.height > canvas.height) p.y = canvas.height - p.height;

  // Score over time
  game.score += dt * 15;
  uiScore.textContent = Math.floor(game.score);

  // Level up
  if (game.score > game.level * 60) {
    game.level += 1;
    uiLevel.textContent = game.level;
    // أصعب: أسرع سباون و أسرع أعداء
    game.player.speed += 10;
    game.spawnInterval = Math.max(0.4, game.spawnInterval - 0.05);
  }

  // Spawn enemies
  game.spawnTimer += dt;
  if (game.spawnTimer >= game.spawnInterval) {
    game.spawnTimer = 0;
    spawnEnemy();
  }

  // Move enemies + collision
  const remaining = [];
  for (const enemy of game.enemies) {
    enemy.x -= enemy.speed * dt;

    // Collision with player
    if (rectsCollide(p, enemy)) {
      gameOver();
      return;
    }

    // keep enemies inside list if still visible
    if (enemy.x + enemy.width > 0) {
      remaining.push(enemy);
    }
  }
  game.enemies = remaining;
}

function render() {
  // Background
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#020617";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Player
  const p = game.player;
  ctx.fillStyle = p.color;
  ctx.fillRect(p.x, p.y, p.width, p.height);

  // Enemies
  for (const enemy of game.enemies) {
    ctx.fillStyle = enemy.color;
    ctx.fillRect(enemy.x, enemy.y, enemy.width, enemy.height);
  }

  // HUD
  ctx.fillStyle = "#e5e7eb";
  ctx.font = "16px system-ui";
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.fillText(`State: ${game.state}`, 16, 16);
  ctx.fillText(`Score: ${Math.floor(game.score)}`, 16, 40);
  ctx.fillText(`Level: ${game.level}`, 16, 64);

  // Messages
  if (game.state === GAME_STATE.MENU) {
    drawCenterMessage("Press SPACE to Start");
  } else if (game.state === GAME_STATE.PAUSED) {
    drawCenterMessage("Paused - Press SPACE to Resume");
  } else if (game.state === GAME_STATE.GAME_OVER) {
    drawCenterMessage("Game Over - Press R to Restart");
  }
}

function drawCenterMessage(text) {
  const boxWidth = 360;
  const boxHeight = 80;
  const x = canvas.width / 2 - boxWidth / 2;
  const y = canvas.height / 2 - boxHeight / 2;

  ctx.fillStyle = "rgba(15,23,42,0.8)";
  ctx.fillRect(x, y, boxWidth, boxHeight);

  ctx.strokeStyle = "#f97316";
  ctx.lineWidth = 2;
  ctx.strokeRect(x + 4, y + 4, boxWidth - 8, boxHeight - 8);

  ctx.fillStyle = "#f9fafb";
  ctx.font = "18px system-ui";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, canvas.width / 2, canvas.height / 2);
}

// Main loop
function loop(timestamp) {
  const dt = (timestamp - game.lastTime) / 1000;
  game.lastTime = timestamp;

  update(dt);
  render();

  requestAnimationFrame(loop);
}

// =======================================
// Mobile Touch Controls
// =======================================
const mcButtons = document.querySelectorAll(".mc-btn");

mcButtons.forEach(btn => {
  const dir = btn.dataset.dir;

  const start = () => {
    if (dir === "up") game.keys["arrowup"] = true;
    if (dir === "down") game.keys["arrowdown"] = true;
    if (dir === "left") game.keys["arrowleft"] = true;
    if (dir === "right") game.keys["arrowright"] = true;
  };

  const stop = () => {
    game.keys["arrowup"] = false;
    game.keys["arrowdown"] = false;
    game.keys["arrowleft"] = false;
    game.keys["arrowright"] = false;
  };

  // Touch events
  btn.addEventListener("touchstart", (e) => {
    e.preventDefault();
    start();
  });

  btn.addEventListener("touchend", (e) => {
    e.preventDefault();
    stop();
  });

  // Mouse fallback (desktop)
  btn.addEventListener("mousedown", start);
  btn.addEventListener("mouseup", stop);
  btn.addEventListener("mouseleave", stop);
});

// init
uiState.textContent = game.state;
requestAnimationFrame(loop);
