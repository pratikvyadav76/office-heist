// Main Application Logic for The Resistance: Office Heist

let gameState = null;
let ws = null;
let timerInterval = null;
let timerSeconds = 90;
let isTimerRunning = false;
let selectedOperatives = new Set();
let currentKioskPlayer = null;

// Connect to WebSocket for instant live state sync
function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;
  
  ws = new WebSocket(wsUrl);
  
  ws.onopen = () => {
    console.log('Connected to Office Heist WebSocket');
  };
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'STATE_UPDATE' || data.type === 'PROPOSAL_RESULT_ANNOUNCED') {
        updateState(data.state);
      } else if (data.type === 'LEADER_SPUN') {
        runRouletteAnimation(data.leader, () => {
          if (data.state) updateState(data.state);
        });
      } else if (data.type === 'TIMER_UPDATE') {
        syncTimer(data.timer_seconds, data.timer_running, data.timer_end_timestamp);
      } else if (data.type === 'MISSION_REVEAL') {
        handleMissionReveal(data);
      } else if (data.type === 'VOTE_CAST') {
        document.getElementById('liveVotesCount').innerText = data.total_votes;
        window.soundFx.playClick();
      } else if (data.type === 'MISSION_ACTION_SUBMITTED') {
        document.getElementById('submissionCounter').innerText = data.submissions_count;
        window.soundFx.playClick();
      }
    } catch (e) {
      console.error('Error handling WS message:', e);
    }
  };
  
  ws.onclose = () => {
    console.log('WS disconnected. Reconnecting in 2s...');
    setTimeout(connectWebSocket, 2000);
  };
}

// Fetch initial state via REST
async function fetchState() {
  try {
    const pin = sessionStorage.getItem('heist_mod_pin') || '';
    const url = pin ? `/api/state?role=moderator&pin=${encodeURIComponent(pin)}` : '/api/state?role=public';
    const res = await fetch(url);
    const data = await res.json();
    updateState(data);
  } catch (e) {
    console.error('Error fetching initial state:', e);
  }
}

// Update UI based on Game State
function updateState(state) {
  gameState = state;
  renderUniversalLeader();
  if (state && state.timer_seconds !== undefined) {
    syncTimer(state.timer_seconds, state.timer_running, state.timer_end_timestamp);
  }
  renderScoreboard();
  renderMissionsTrack();
  renderPhase();
  renderModeratorDrawer();
}

function renderUniversalLeader() {
  if (!gameState) return;
  const cur = gameState.current_leader || 'Awaiting Role Assignment...';
  const el = document.getElementById('univLeaderName');
  if (el) {
    if (el.innerText !== cur && el.innerText !== 'Awaiting Role Assignment...' && el.innerText !== 'Waiting for Game Start...') {
      showLeaderToast(`👑 THE PROFESSOR CHOSE: ${cur}`);
    }
    el.innerText = cur;
  }
}

// Render Scoreboard & Proposal Attempts
function renderScoreboard() {
  if (!gameState) return;
  
  document.getElementById('resScore').innerText = gameState.resistance_score;
  document.getElementById('sabScore').innerText = gameState.saboteur_score;
  
  // Attempts dots
  const dotsContainer = document.getElementById('attemptsDots');
  dotsContainer.innerHTML = '';
  const maxAttempts = gameState.max_proposal_attempts || 5;
  const currentAttempt = gameState.proposal_attempt || 1;
  
  for (let i = 1; i <= maxAttempts; i++) {
    const dot = document.createElement('div');
    dot.className = 'attempt-dot';
    if (i < currentAttempt) {
      dot.classList.add('active');
    } else if (i === currentAttempt) {
      dot.classList.add('active');
      if (currentAttempt >= 4) dot.classList.add('danger');
    }
    dotsContainer.appendChild(dot);
  }
  
  const warn = document.getElementById('attemptWarning');
  if (currentAttempt === 5) {
    warn.innerText = '⚠️ FINAL ATTEMPT! If rejected, Saboteurs win!';
  } else if (currentAttempt === 4) {
    warn.innerText = '⚠️ Warning: 4th attempt!';
  } else {
    warn.innerText = '';
  }
}

// Render 5 Missions Bar
function renderMissionsTrack() {
  if (!gameState) return;
  const container = document.getElementById('missionsRow');
  container.innerHTML = '';
  
  const teamSizes = gameState.mission_team_sizes || [5, 6, 6, 7, 7];
  const results = gameState.mission_results || [null, null, null, null, null];
  const curIdx = gameState.current_mission - 1;
  
  teamSizes.forEach((size, idx) => {
    const node = document.createElement('div');
    node.className = 'mission-node';
    
    const res = results[idx];
    if (res === 'SUCCESS') {
      node.classList.add('success');
    } else if (res === 'FAILED') {
      node.classList.add('failed');
    } else if (idx === curIdx && !gameState.game_over) {
      node.classList.add('active');
    }
    
    let statusText = 'Pending';
    let statusClass = 'status-pending';
    if (res === 'SUCCESS') {
      statusText = 'Passed ✅';
      statusClass = 'status-success';
    } else if (res === 'FAILED') {
      statusText = 'Failed ❌';
      statusClass = 'status-failed';
    } else if (idx === curIdx && !gameState.game_over) {
      statusText = 'Current';
      statusClass = 'status-active';
    }
    
    node.innerHTML = `
      <div class="node-title">Mission ${idx + 1}</div>
      <div class="node-size">${size} 👥</div>
      <div class="node-status ${statusClass}">${statusText}</div>
    `;
    container.appendChild(node);
  });
}

// Render the active phase
function renderPhase() {
  if (!gameState) return;
  
  const phases = ['phaseSetup', 'phaseProposal', 'phaseDebate', 'phaseProposalResult', 'phaseMissionAction', 'phaseGameOver'];
  phases.forEach(id => document.getElementById(id).style.display = 'none');
  
  if (gameState.phase === 'SETUP') {
    renderSetupPhase();
  } else if (gameState.phase === 'LEADER_PROPOSAL') {
    renderProposalPhase();
  } else if (gameState.phase === 'DEBATE_AND_VOTE') {
    renderDebatePhase();
  } else if (gameState.phase === 'PROPOSAL_RESULT') {
    renderProposalResultPhase();
  } else if (gameState.phase === 'MISSION_ACTION') {
    renderMissionActionPhase();
  } else if (gameState.phase === 'GAME_OVER') {
    renderGameOverPhase();
  }
}

// PHASE: SETUP
function renderSetupPhase() {
  const p = document.getElementById('phaseSetup');
  p.style.display = 'block';
  
  document.getElementById('setupPlayerCount').innerText = gameState.players.length;
  const grid = document.getElementById('setupRosterGrid');
  grid.innerHTML = '';
  
  gameState.players.forEach(name => {
    const chip = document.createElement('div');
    chip.className = 'player-chip';
    chip.innerHTML = `
      <div class="chip-name">${name}</div>
      <div class="chip-role-badge">Operative</div>
    `;
    grid.appendChild(chip);
  });
}

// PHASE: LEADER PROPOSAL
function renderProposalPhase() {
  const p = document.getElementById('phaseProposal');
  p.style.display = 'block';
  
  document.getElementById('leaderNameDisplay').innerText = gameState.current_leader || 'None';
  document.getElementById('currentMissionNum').innerText = gameState.current_mission;
  document.getElementById('requiredTeamSize').innerText = gameState.required_team_size;
  
  selectedOperatives.clear();
  updateProposalCounter();
  
  const grid = document.getElementById('proposalRosterGrid');
  grid.innerHTML = '';
  
  gameState.players.forEach(name => {
    const chip = document.createElement('div');
    chip.className = 'player-chip';
    if (name === gameState.current_leader) chip.classList.add('is-leader');
    
    chip.innerHTML = `
      <div class="chip-name">${name}</div>
      <div class="chip-role-badge">${name === gameState.current_leader ? '👑 Leader' : 'Available'}</div>
    `;
    
    chip.onclick = () => {
      window.soundFx.playClick();
      if (selectedOperatives.has(name)) {
        selectedOperatives.delete(name);
        chip.classList.remove('selected');
      } else {
        if (selectedOperatives.size < gameState.required_team_size) {
          selectedOperatives.add(name);
          chip.classList.add('selected');
        }
      }
      updateProposalCounter();
    };
    
    grid.appendChild(chip);
  });
}

function updateProposalCounter() {
  const counter = document.getElementById('selectionCounter');
  const btn = document.getElementById('btnConfirmProposal');
  const size = selectedOperatives.size;
  const req = gameState.required_team_size;
  
  counter.innerText = `${size} / ${req} Selected`;
  if (size === req) {
    btn.disabled = false;
    counter.style.color = 'var(--success-green)';
  } else {
    btn.disabled = true;
    counter.style.color = 'var(--resistance-blue)';
  }
}

// PHASE: DEBATE AND VOTE
function renderDebatePhase() {
  const p = document.getElementById('phaseDebate');
  p.style.display = 'block';
  
  document.getElementById('spotlightCount').innerText = gameState.proposed_team.length;
  const container = document.getElementById('proposedTeamChips');
  container.innerHTML = '';
  
  gameState.proposed_team.forEach(name => {
    const badge = document.createElement('div');
    badge.className = 'agent-badge';
    badge.innerHTML = `🕵️‍♂️ ${name}`;
    container.appendChild(badge);
  });
  
  // Set default tally
  const half = Math.ceil(gameState.players.length / 2);
  document.getElementById('tallyYes').innerText = half + 1;
  document.getElementById('tallyNo').innerText = gameState.players.length - (half + 1);
  document.getElementById('liveVotesCount').innerText = gameState.proposal_votes_count || 0;
  
  resetTimer(90);
}

// PHASE: PROPOSAL RESULT
function renderProposalResultPhase() {
  const p = document.getElementById('phaseProposalResult');
  p.style.display = 'block';
}

// PHASE: MISSION ACTION
function renderMissionActionPhase() {
  const p = document.getElementById('phaseMissionAction');
  p.style.display = 'block';
  
  document.getElementById('missionActionNum').innerText = gameState.current_mission;
  document.getElementById('missionActionCount').innerText = gameState.proposed_team.length;
  document.getElementById('submissionCounter').innerText = gameState.mission_submissions_count || 0;
  document.getElementById('submissionTotal').innerText = gameState.proposed_team.length;
  
  // Reset manual counters
  document.getElementById('manualSuccessCount').innerText = '0';
  document.getElementById('manualSabotageCount').innerText = '0';
  
  // Kiosk buttons for each operative on team
  const kioskList = document.getElementById('kioskOperativesList');
  kioskList.innerHTML = '';
  
  gameState.proposed_team.forEach(name => {
    const btn = document.createElement('button');
    btn.className = 'btn-icon';
    btn.style.padding = '10px 14px';
    btn.innerText = `👤 ${name}`;
    btn.onclick = () => openKioskModal(name);
    kioskList.appendChild(btn);
  });
}

// PHASE: GAME OVER
function renderGameOverPhase() {
  const p = document.getElementById('phaseGameOver');
  p.style.display = 'block';
  
  const isRes = gameState.winner === 'Resistance';
  document.getElementById('gameOverIcon').innerText = isRes ? '🏆' : '😈';
  document.getElementById('gameOverTitle').innerText = isRes ? 'RESISTANCE VICTORY!' : 'SABOTEURS VICTORY!';
  document.getElementById('gameOverTitle').style.color = isRes ? 'var(--resistance-blue)' : 'var(--saboteur-red)';
  document.getElementById('gameOverDesc').innerText = isRes 
    ? 'The loyal office team successfully completed 3 missions and cracked the vault without getting sabotaged!'
    : 'The secret saboteurs successfully infiltrated and compromised 3 missions!';
    
  // Render saboteurs list
  const sabList = document.getElementById('gameOverSaboteursList');
  sabList.innerHTML = '';
  if (gameState.saboteurs) {
    gameState.saboteurs.forEach(name => {
      const chip = document.createElement('div');
      chip.className = 'agent-badge';
      chip.style.borderColor = 'var(--saboteur-red)';
      chip.style.background = 'rgba(255, 51, 102, 0.2)';
      chip.innerHTML = `😈 <strong>${name}</strong>`;
      sabList.appendChild(chip);
    });
  }
}

// Handle Dramatic Mission Reveal
function handleMissionReveal(data) {
  const modal = document.getElementById('revealModal');
  const card = document.getElementById('revealCard');
  const icon = document.getElementById('revealAnimIcon');
  const title = document.getElementById('revealTitle');
  const subtitle = document.getElementById('revealSubtitle');
  const btnContainer = document.getElementById('revealButtonContainer');
  
  modal.classList.add('open');
  card.className = 'reveal-card';
  btnContainer.style.display = 'none';
  
  icon.innerText = '🔐';
  title.innerText = 'SHUFFLING SECRET REPORTS...';
  subtitle.innerText = 'Mixing encrypted submissions in the office vault...';
  
  window.soundFx.playSuspenseDrum();
  
  // Dramatic suspense timing
  setTimeout(() => {
    window.soundFx.playSuspenseDrum();
    icon.innerText = '⚡';
    title.innerText = 'ANALYZING VAULT INTEGRITY...';
  }, 1600);
  
  setTimeout(() => {
    const isSuccess = data.is_success;
    if (isSuccess) {
      window.soundFx.playSuccessFanfare();
      card.classList.add('revealed-success');
      icon.innerText = '🎉';
      title.innerText = 'MISSION ACCOMPLISHED!';
      title.style.color = 'var(--success-green)';
      subtitle.innerText = 'The vault security was bypassed cleanly! Resistance earns +1 Point!';
    } else {
      window.soundFx.playFailureAlarm();
      card.classList.add('revealed-failed');
      icon.innerText = '🚨';
      // IMPORTANT USER RULE: Never tell players how many Saboteurs are on a failed mission; say only “Mission failed.”
      title.innerText = 'MISSION FAILED!';
      title.style.color = 'var(--saboteur-red)';
      subtitle.innerText = 'Sabotage detected in the heist operation! Saboteurs earn +1 Point!';
    }
    btnContainer.style.display = 'block';
  }, 3200);
}

// Render Moderator Drawer Content
async function renderModeratorDrawer() {
  if (!gameState) return;
  const pin = sessionStorage.getItem('heist_mod_pin');
  if (!pin) return;
  
  // Whispers
  try {
    const res = await fetch(`/api/whispers?pin=${encodeURIComponent(pin)}`);
    if (!res.ok) return;
    const data = await res.json();
    const list = document.getElementById('modWhispersList');
    list.innerHTML = '';
    
    data.messages.forEach(item => {
      const card = document.createElement('div');
      card.className = 'whisper-card';
      card.innerHTML = `
        <div class="whisper-card-header">
          <strong style="color: var(--saboteur-red);">😈 ${item.player}</strong>
          <button class="btn-icon" style="font-size: 11px; padding: 4px 8px;" onclick="copyWhisper('${encodeURIComponent(item.message)}')">
            📋 Copy Whisper
          </button>
        </div>
        <div class="whisper-text">${item.message}</div>
      `;
      list.appendChild(card);
    });
  } catch (e) {
    console.error('Error fetching whispers:', e);
  }
  
  // Event Log
  const logContainer = document.getElementById('modEventLog');
  logContainer.innerHTML = '';
  if (gameState.history_log) {
    gameState.history_log.forEach(item => {
      const el = document.createElement('div');
      el.style.marginBottom = '6px';
      el.innerHTML = `<span style="color: var(--gold-accent);">[M${item.mission}]</span> ${item.details}`;
      logContainer.appendChild(el);
    });
  }
}

function copyWhisper(encodedMsg) {
  const msg = decodeURIComponent(encodedMsg);
  navigator.clipboard.writeText(msg).then(() => {
    alert('Copied WhatsApp whisper text to clipboard!');
  });
}

// Universal Timer Synchronization & Backend Actions
function syncTimer(seconds, isRunning, endTimestamp) {
  timerSeconds = seconds;
  isTimerRunning = isRunning;
  
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }

  function renderDigits(sec) {
    const mins = Math.floor(sec / 60);
    const s = sec % 60;
    const str = `${String(mins).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    const topDigits = document.getElementById('topTimerDigits');
    const stageDigits = document.getElementById('timerDisplay');
    const topBadge = document.getElementById('topNavTimer');
    
    if (topDigits) topDigits.innerText = str;
    if (stageDigits) stageDigits.innerText = str;

    if (sec <= 15 && isRunning) {
      if (topBadge) topBadge.classList.add('danger');
      if (stageDigits) stageDigits.classList.add('warning');
      if (sec <= 10 && sec > 0) window.soundFx.playWarning();
    } else {
      if (topBadge) topBadge.classList.remove('danger');
      if (stageDigits) stageDigits.classList.remove('warning');
    }
  }

  renderDigits(timerSeconds);

  if (isRunning && endTimestamp > 0) {
    timerInterval = setInterval(() => {
      const nowSec = Date.now() / 1000;
      const remaining = Math.max(0, Math.ceil(endTimestamp - nowSec));
      renderDigits(remaining);
      if (remaining <= 0) {
        clearInterval(timerInterval);
        timerInterval = null;
        isTimerRunning = false;
        renderDigits(0);
        window.soundFx.playRejected();
      }
    }, 500);
  }
}

async function startTimer() {
  window.soundFx.init();
  await fetch('/api/timer-action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'START', seconds: timerSeconds })
  });
}

async function pauseTimer() {
  await fetch('/api/timer-action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'PAUSE' })
  });
}

async function resetTimer(secs = 90) {
  await fetch('/api/timer-action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'RESET', seconds: secs })
  });
}

// Toast Alert
function showLeaderToast(text) {
  const toast = document.getElementById('leaderToast');
  if (!toast) return;
  toast.innerText = text;
  toast.classList.add('show');
  window.soundFx.playLeaderAppointed();
  setTimeout(() => toast.classList.remove('show'), 3500);
}

// Professor's Roulette Animation
let isRouletteRunning = false;
function runRouletteAnimation(winnerName, onComplete) {
  if (isRouletteRunning) return;
  isRouletteRunning = true;

  const modal = document.getElementById('rouletteModal');
  const reelText = document.getElementById('rouletteNameText');
  const banner = document.getElementById('rouletteResultBanner');
  const winnerText = document.getElementById('rouletteWinnerName');
  const closeBtn = document.getElementById('btnCloseRoulette');

  modal.classList.add('open');
  banner.style.display = 'none';
  closeBtn.style.display = 'none';
  reelText.classList.remove('winner');

  const roster = (gameState && gameState.players && gameState.players.length > 0)
    ? gameState.players
    : ['Operative A', 'Operative B', 'Operative C'];

  let ticks = 0;
  const maxTicks = 26;
  let delay = 60;

  function nextTick() {
    ticks++;
    const randomPlayer = roster[Math.floor(Math.random() * roster.length)];
    reelText.innerText = randomPlayer;
    window.soundFx.playRouletteTick(700 + (ticks * 15));

    if (ticks < 14) delay = 60;
    else if (ticks < 20) delay = 120;
    else if (ticks < 24) delay = 220;
    else delay = 380;

    if (ticks >= maxTicks) {
      reelText.innerText = winnerName;
      reelText.classList.add('winner');
      winnerText.innerText = winnerName;
      banner.style.display = 'block';
      closeBtn.style.display = 'block';
      window.soundFx.playLeaderAppointed();
      isRouletteRunning = false;

      closeBtn.onclick = () => {
        modal.classList.remove('open');
        if (onComplete) onComplete();
      };
      setTimeout(() => {
        modal.classList.remove('open');
        if (onComplete) onComplete();
      }, 3500);
    } else {
      setTimeout(nextTick, delay);
    }
  }

  nextTick();
}

// Kiosk Pass-the-Screen Handlers
function openKioskModal(playerName) {
  currentKioskPlayer = playerName;
  document.getElementById('kioskPlayerName').innerText = playerName;
  document.getElementById('kioskShield').style.display = 'block';
  document.getElementById('kioskActionArea').style.display = 'none';
  document.getElementById('kioskModal').classList.add('open');
}

// Wire Up Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  connectWebSocket();
  fetchState();

  // Bella Ciao Theme
  const bellaBtn = document.getElementById('btnBellaCiao');
  if (bellaBtn) {
    bellaBtn.onclick = () => {
      window.soundFx.playBellaCiaoRiff();
    };
  }

  // Professor's Roulette Spin
  const rouletteBtn = document.getElementById('btnTriggerRoulette');
  if (rouletteBtn) {
    rouletteBtn.onclick = async () => {
      window.soundFx.playClick();
      const res = await fetch('/api/spin-leader', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}'
      });
      const data = await res.json();
      if (data.current_leader) {
        runRouletteAnimation(data.current_leader, () => fetchState());
      }
    };
  }

  // Pass Leader Clockwise
  const nextLeaderBtn = document.getElementById('btnRotateNextLeader');
  if (nextLeaderBtn) {
    nextLeaderBtn.onclick = async () => {
      window.soundFx.playClick();
      await fetch('/api/rotate-leader-manually', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}'
      });
      fetchState();
    };
  }
  
  // Sound Toggle
  document.getElementById('btnSound').onclick = () => {
    const isMuted = window.soundFx.toggleMute();
    document.getElementById('btnSound').innerHTML = isMuted ? '🔇 <span class="nav-btn-text">Sound OFF</span>' : '🔊 <span class="nav-btn-text">Sound ON</span>';
  };
  
  // Fullscreen Toggle
  document.getElementById('btnFullscreen').onclick = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };
  
  // Moderator Drawer Toggle with PIN Authentication
  document.getElementById('btnModToggle').onclick = () => {
    const savedPin = sessionStorage.getItem('heist_mod_pin');
    if (savedPin) {
      document.getElementById('modDrawer').classList.add('open');
      renderModeratorDrawer();
    } else {
      document.getElementById('inputModPin').value = '';
      document.getElementById('pinErrorMsg').style.display = 'none';
      document.getElementById('modPinModal').classList.add('open');
      setTimeout(() => document.getElementById('inputModPin').focus(), 100);
    }
  };

  document.getElementById('btnSubmitPin').onclick = async () => {
    const pin = document.getElementById('inputModPin').value.trim();
    try {
      const res = await fetch('/api/verify-mod-pin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pin })
      });
      if (res.ok) {
        sessionStorage.setItem('heist_mod_pin', pin);
        document.getElementById('modPinModal').classList.remove('open');
        document.getElementById('modDrawer').classList.add('open');
        fetchState();
      } else {
        document.getElementById('pinErrorMsg').style.display = 'block';
      }
    } catch (e) {
      document.getElementById('pinErrorMsg').style.display = 'block';
    }
  };

  document.getElementById('btnCancelPin').onclick = () => {
    document.getElementById('modPinModal').classList.remove('open');
  };

  document.getElementById('btnCloseMod').onclick = () => {
    document.getElementById('modDrawer').classList.remove('open');
  };
  
  // QR Modal Logic
  function renderQr(targetUrl) {
    document.getElementById('qrUrlDisplay').innerText = targetUrl;
    if (window.qrcode) {
      const qr = qrcode(0, 'M');
      qr.addData(targetUrl);
      qr.make();
      document.getElementById('qrCodeTarget').innerHTML = qr.createSvgTag(6, 0);
    }
  }

  document.getElementById('btnQr').onclick = () => {
    // Generate mobile join link based on the current website URL
    let playUrl = `${window.location.origin}/play`;
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      const ip = gameState ? gameState.local_ip : window.location.hostname;
      const port = window.location.port ? `:${window.location.port}` : '';
      playUrl = `http://${ip}${port}/play`;
    }
    renderQr(playUrl);
    document.getElementById('copySuccessMsg').style.display = 'none';
    document.getElementById('qrModal').classList.add('open');
  };

  document.getElementById('btnCopyMobileLink').onclick = async () => {
    const url = document.getElementById('qrUrlDisplay').innerText.trim();
    try {
      await navigator.clipboard.writeText(url);
      const msg = document.getElementById('copySuccessMsg');
      msg.style.display = 'block';
      setTimeout(() => { msg.style.display = 'none'; }, 3000);
    } catch (e) {
      prompt('Copy this link for your colleagues:', url);
    }
  };

  document.getElementById('btnCloseQr').onclick = () => {
    document.getElementById('qrModal').classList.remove('open');
  };
  
  // Setup Actions
  document.getElementById('btnStartGame').onclick = async () => {
    window.soundFx.playClick();
    const pin = sessionStorage.getItem('heist_mod_pin') || '2026';
    await fetch('/api/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ players: gameState.players, pin: pin })
    });
    fetchState();
  };
  
  // Rotate Leader
  document.getElementById('btnRotateLeader').onclick = async () => {
    window.soundFx.playClick();
    await fetch('/api/rotate-leader-manually', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
    fetchState();
  };
  
  // Confirm Proposed Team
  document.getElementById('btnConfirmProposal').onclick = async () => {
    window.soundFx.playClick();
    const team = Array.from(selectedOperatives);
    await fetch('/api/propose-team', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team })
    });
    fetchState();
  };
  
  // Timer buttons
  document.getElementById('btnTimerStart').onclick = () => startTimer();
  document.getElementById('btnTimerPause').onclick = () => pauseTimer();
  document.getElementById('btnTimerReset').onclick = () => resetTimer(90);
  
  // Tally Yes/No buttons
  const tallyYes = document.getElementById('tallyYes');
  const tallyNo = document.getElementById('tallyNo');
  document.getElementById('btnIncYes').onclick = () => { tallyYes.innerText = parseInt(tallyYes.innerText) + 1; };
  document.getElementById('btnDecYes').onclick = () => { tallyYes.innerText = Math.max(0, parseInt(tallyYes.innerText) - 1); };
  document.getElementById('btnIncNo').onclick = () => { tallyNo.innerText = parseInt(tallyNo.innerText) + 1; };
  document.getElementById('btnDecNo').onclick = () => { tallyNo.innerText = Math.max(0, parseInt(tallyNo.innerText) - 1); };
  
  // Resolve Team Proposal Vote
  document.getElementById('btnResolveProposalVote').onclick = async () => {
    pauseTimer();
    const yesCount = parseInt(tallyYes.innerText);
    const noCount = parseInt(tallyNo.innerText);
    
    const res = await fetch('/api/resolve-proposal-vote', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ yes_count: yesCount, no_count: noCount })
    });
    const result = await res.json();
    
    // Play sound
    if (result.approved) {
      window.soundFx.playApproved();
    } else {
      window.soundFx.playRejected();
    }
    
    // Update banner
    const banner = document.getElementById('proposalResultBanner');
    const icon = document.getElementById('proposalResultIcon');
    const title = document.getElementById('proposalResultTitle');
    const details = document.getElementById('proposalResultDetails');
    const proceedBtn = document.getElementById('btnProceedToMission');
    
    if (result.approved) {
      banner.style.background = 'rgba(16, 185, 129, 0.15)';
      banner.style.border = '2px solid var(--success-green)';
      icon.innerText = '✅';
      title.innerText = 'TEAM PROPOSAL APPROVED!';
      title.style.color = 'var(--success-green)';
      details.innerText = `${yesCount} Approved vs ${noCount} Rejected. The heist team enters the vault!`;
      proceedBtn.style.display = 'inline-block';
    } else {
      banner.style.background = 'rgba(255, 51, 102, 0.15)';
      banner.style.border = '2px solid var(--saboteur-red)';
      icon.innerText = '❌';
      title.innerText = 'TEAM PROPOSAL REJECTED!';
      title.style.color = 'var(--saboteur-red)';
      details.innerText = `${noCount} Rejected vs ${yesCount} Approved. Leader token passes clockwise!`;
      proceedBtn.style.display = 'none';
      setTimeout(() => fetchState(), 2500);
    }
    
    document.getElementById('phaseDebate').style.display = 'none';
    document.getElementById('phaseProposalResult').style.display = 'block';
  };
  
  document.getElementById('btnProceedToMission').onclick = () => {
    fetchState();
  };
  
  // Manual Mission Tally S/F counters
  const manSucc = document.getElementById('manualSuccessCount');
  const manSabo = document.getElementById('manualSabotageCount');
  document.getElementById('btnIncManualSuccess').onclick = () => { manSucc.innerText = parseInt(manSucc.innerText) + 1; };
  document.getElementById('btnDecManualSuccess').onclick = () => { manSucc.innerText = Math.max(0, parseInt(manSucc.innerText) - 1); };
  document.getElementById('btnIncManualSabotage').onclick = () => { manSabo.innerText = parseInt(manSabo.innerText) + 1; };
  document.getElementById('btnDecManualSabotage').onclick = () => { manSabo.innerText = Math.max(0, parseInt(manSabo.innerText) - 1); };
  
  // Resolve Mission Outcome
  document.getElementById('btnResolveMission').onclick = async () => {
    window.soundFx.init();
    const succ = parseInt(manSucc.innerText);
    const sabo = parseInt(manSabo.innerText);
    
    let body = null;
    if (succ + sabo > 0) {
      body = JSON.stringify({ success_count: succ, sabotage_count: sabo });
    }
    
    const res = await fetch('/api/resolve-mission', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body
    });
    const resData = await res.json();
    handleMissionReveal({
      is_success: resData.outcome === 'SUCCESS',
      outcome: resData.outcome,
      state: resData.state
    });
  };
  
  // Next Mission
  document.getElementById('btnNextMission').onclick = async () => {
    document.getElementById('revealModal').classList.remove('open');
    await fetch('/api/next-mission', { method: 'POST' });
    fetchState();
  };
  
  // Restart Game
  document.getElementById('btnRestartGame').onclick = async () => {
    await fetch('/api/reset-game', { method: 'POST' });
    fetchState();
  };
  
  // Moderator manual overrides
  document.getElementById('btnModForceLeader').onclick = async () => {
    await fetch('/api/rotate-leader-manually', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
    fetchState();
  };
  
  document.getElementById('btnModResetGame').onclick = async () => {
    if (confirm('Are you sure you want to reset the game back to setup?')) {
      await fetch('/api/reset-game', { method: 'POST' });
      document.getElementById('modDrawer').classList.remove('open');
      fetchState();
    }
  };
  
  // Kiosk Modal Ready
  document.getElementById('btnKioskReady').onclick = async () => {
    document.getElementById('kioskShield').style.display = 'none';
    document.getElementById('kioskActionArea').style.display = 'block';
    
    // Check if player is saboteur
    const res = await fetch(`/api/state?player=${encodeURIComponent(currentKioskPlayer)}`);
    const pState = await res.json();
    
    const banner = document.getElementById('kioskRoleBanner');
    const sabBtn = document.getElementById('btnKioskSabotage');
    
    if (pState.is_saboteur) {
      banner.style.background = 'rgba(255, 51, 102, 0.2)';
      banner.style.color = 'var(--saboteur-red)';
      banner.innerText = '😈 You are a SABOTEUR! You may choose Success or Sabotage.';
      sabBtn.disabled = false;
      sabBtn.style.opacity = '1';
    } else {
      banner.style.background = 'rgba(0, 242, 254, 0.2)';
      banner.style.color = 'var(--resistance-blue)';
      banner.innerText = '🏢 You are LOYAL RESISTANCE! (You must submit Success).';
      sabBtn.disabled = true;
      sabBtn.style.opacity = '0.3';
    }
  };
  
  document.getElementById('btnKioskSuccess').onclick = async () => {
    await submitKioskAction('SUCCESS');
  };
  document.getElementById('btnKioskSabotage').onclick = async () => {
    await submitKioskAction('SABOTAGE');
  };
});

async function submitKioskAction(act) {
  window.soundFx.playClick();
  await fetch('/api/mission-action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_name: currentKioskPlayer, action: act })
  });
  document.getElementById('kioskModal').classList.remove('open');
}
