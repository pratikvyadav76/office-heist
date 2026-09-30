// Main Application Logic for The Resistance: Office Heist

const RAW_DEFAULT_PLAYERS = [
  "Riya Patil (riya.patil)",
  "Tanmay Indore (tanmay.indore)",
  "Sushil Kanojiya (sushil.kanojiya)",
  "Pratik Buge (pratik.buge)",
  "Karthik Iyer (karthik.iyer)",
  "Puja Godse (puja.godse)",
  "Niki Panchal (niki.panchal)",
  "Bhishma Mahajan (bhishma.mahajan)",
  "Sonakshi Julka (sonakshi.julka)",
  "Siddhesh Kadu (siddhesh.kadu)",
  "Smeet Shethia (smeet.shethia)",
  "Purva Hirve (purva.hirve)",
  "Shrukti Tamakuwala (shrukti.tamakuwala)",
  "Sanchay Mota (sanchay.mota)",
  "Akshay Thakare (akshay.thakare)",
  "Vidisha Shetty (vidisha.shetty)",
  "Saket Shinde (saket.shinde)",
  "Rohan Hile (rohan.hile)",
  "Siddharth Sharma (siddharth.sharma)",
  "Evelin Puthoor (evelin.puthoor)",
  "Mohammad Arbaz (mohammad.arbaz)",
  "Aishwarya Hate (aishwarya.hate)",
  "Pratik Morale (pratik.morale)",
  "Md Javed Akhter (javed.akhter)",
  "Amit Anilkumar (amit.anilkumar)"
];

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
        if (gameState) {
          gameState.proposal_votes_count = data.total_votes;
          if (data.voted_players) {
            gameState.proposal_voted_players = data.voted_players;
          } else if (data.player) {
            if (!gameState.proposal_voted_players) gameState.proposal_voted_players = [];
            if (!gameState.proposal_voted_players.includes(data.player)) {
              gameState.proposal_voted_players.push(data.player);
            }
          }
          updateDebateBallotStatus();
        } else {
          const countEl = document.getElementById('liveVotesCount');
          if (countEl) countEl.innerText = data.total_votes;
        }
        window.soundFx.playClick();
      } else if (data.type === 'MISSION_ACTION_SUBMITTED') {
        if (gameState) {
          gameState.mission_submissions_count = data.submissions_count;
          if (data.submitted_players) {
            gameState.mission_submitted_players = data.submitted_players;
          }
        }
        const counterEl = document.getElementById('submissionCounter');
        if (counterEl) counterEl.innerText = data.submissions_count;
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

// Setup Roster State
let setupActivePlayers = [];
let setupAbsentPlayers = [];
let setupSaboteurCount = 5;
let setupMissionSizes = [5, 6, 6, 7, 7];
let isSetupInitialized = false;

function initSetupState() {
  if (!gameState || !gameState.players) return;
  if (!isSetupInitialized || setupActivePlayers.length === 0) {
    setupActivePlayers = [...gameState.players];
    setupAbsentPlayers = [];
    setupSaboteurCount = gameState.saboteur_count || calculateRecommendedSaboteurs(setupActivePlayers.length);
    setupMissionSizes = gameState.mission_team_sizes ? [...gameState.mission_team_sizes] : calculateRecommendedTeamSizes(setupActivePlayers.length);
    isSetupInitialized = true;
  }
}

function calculateRecommendedSaboteurs(n) {
  if (n <= 6) return 2;
  if (n <= 9) return 3;
  if (n <= 14) return 4;
  return 5;
}

function calculateRecommendedTeamSizes(n) {
  if (n === 5) return [2, 3, 2, 3, 3];
  if (n === 6) return [2, 3, 4, 3, 4];
  if (n === 7) return [2, 3, 3, 4, 4];
  if (n >= 8 && n <= 10) return [3, 4, 4, 5, 5];
  if (n <= 14) return [4, 5, 5, 6, 6];
  return [5, 6, 6, 7, 7];
}

function removeSetupPlayer(name) {
  window.soundFx.playClick();
  setupActivePlayers = setupActivePlayers.filter(p => p !== name);
  if (!setupAbsentPlayers.includes(name)) {
    setupAbsentPlayers.push(name);
  }
  setupSaboteurCount = calculateRecommendedSaboteurs(setupActivePlayers.length);
  setupMissionSizes = calculateRecommendedTeamSizes(setupActivePlayers.length);
  renderSetupPhase();
}

function restoreSetupPlayer(name) {
  window.soundFx.playClick();
  setupAbsentPlayers = setupAbsentPlayers.filter(p => p !== name);
  if (!setupActivePlayers.includes(name)) {
    setupActivePlayers.push(name);
  }
  setupSaboteurCount = calculateRecommendedSaboteurs(setupActivePlayers.length);
  setupMissionSizes = calculateRecommendedTeamSizes(setupActivePlayers.length);
  renderSetupPhase();
}

// Render 5 Missions Bar
function renderMissionsTrack() {
  if (!gameState) return;
  const container = document.getElementById('missionsRow');
  container.innerHTML = '';
  
  const missions = gameState.missions || [
    { title: "Op Blackout", team_size: 5 },
    { title: "Minting Presses", team_size: 6 },
    { title: "Governor's Vault", team_size: 6 },
    { title: "Melt 90T Gold", team_size: 7 },
    { title: "Rooftop Escape", team_size: 7 }
  ];
  const results = gameState.mission_results || [null, null, null, null, null];
  const curIdx = gameState.current_mission - 1;
  
  missions.forEach((m, idx) => {
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
      <div class="node-title" title="${m.story || ''}">M${idx + 1}: ${m.title || `Mission ${idx+1}`}</div>
      <div class="node-size">${m.team_size} 👥</div>
      <div class="node-status ${statusClass}">${statusText}</div>
    `;
    container.appendChild(node);
  });
}

// Render the active phase
function renderPhase() {
  if (!gameState) return;
  
  const phases = ['phaseSetup', 'phaseProposal', 'phaseDebate', 'phaseProposalResult', 'phaseMissionAction', 'phaseGameOver'];
  phases.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });
  
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
  if (!p) return;
  p.style.display = 'block';
  
  initSetupState();

  const activeEl = document.getElementById('setupPlayerCount');
  if (activeEl) activeEl.innerText = setupActivePlayers.length;
  
  const absentEl = document.getElementById('setupAbsentCount');
  if (absentEl) absentEl.innerText = setupAbsentPlayers.length;

  const sabEl = document.getElementById('setupSaboteurCount');
  if (sabEl) sabEl.innerText = setupSaboteurCount;

  const sizesSummary = document.getElementById('setupMissionSizesSummary');
  if (sizesSummary) sizesSummary.innerText = setupMissionSizes.join(' • ');

  const grid = document.getElementById('setupRosterGrid');
  grid.innerHTML = '';
  
  setupActivePlayers.forEach(name => {
    const chip = document.createElement('div');
    chip.className = 'player-chip';
    chip.innerHTML = `
      <div class="chip-name">${name}</div>
      <div class="chip-role-badge">Operative</div>
      <button class="chip-remove-btn" title="Remove absent colleague">✕</button>
    `;
    const btnDel = chip.querySelector('.chip-remove-btn');
    btnDel.onclick = (e) => {
      e.stopPropagation();
      removeSetupPlayer(name);
    };
    grid.appendChild(chip);
  });

  // Render absent tray
  const absentSection = document.getElementById('setupAbsentSection');
  const absentGrid = document.getElementById('setupAbsentGrid');
  if (absentSection && absentGrid) {
    if (setupAbsentPlayers.length > 0) {
      absentSection.style.display = 'block';
      absentGrid.innerHTML = '';
      setupAbsentPlayers.forEach(name => {
        const item = document.createElement('div');
        item.className = 'absent-chip';
        item.innerHTML = `
          <span>${name}</span>
          <button class="absent-chip-restore">+ Restore</button>
        `;
        item.querySelector('.absent-chip-restore').onclick = () => restoreSetupPlayer(name);
        absentGrid.appendChild(item);
      });
    } else {
      absentSection.style.display = 'none';
    }
  }
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
  
  const curMission = (gameState.missions && gameState.missions[gameState.current_mission - 1]) || null;
  const missionTitle = curMission ? `${curMission.title} (${curMission.story})` : `Mission ${gameState.current_mission}`;
  
  const mNumEl = document.getElementById('debateMissionNum');
  if (mNumEl) mNumEl.innerText = gameState.current_mission;
  const mDescEl = document.getElementById('debateMissionStoryDesc');
  if (mDescEl) mDescEl.innerText = `Leader proposed the strike team below for ${missionTitle}. Debate their loyalty and cast secret ballots on your phones!`;

  document.getElementById('spotlightCount').innerText = gameState.proposed_team.length;
  const container = document.getElementById('proposedTeamChips');
  container.innerHTML = '';
  
  gameState.proposed_team.forEach(name => {
    const badge = document.createElement('div');
    badge.className = 'agent-badge';
    badge.innerHTML = `🕵️‍♂️ ${name}`;
    container.appendChild(badge);
  });
  
  updateDebateBallotStatus();
  resetTimer(90);
}

function updateDebateBallotStatus() {
  if (!gameState) return;
  const votedCount = gameState.proposal_votes_count || 0;
  const totalCount = gameState.players ? gameState.players.length : 22;
  const pct = Math.min(100, Math.round((votedCount / (totalCount || 1)) * 100));

  const countEl = document.getElementById('liveVotesCount');
  if (countEl) countEl.innerText = votedCount;
  const totalEl = document.getElementById('liveVotesTotal');
  if (totalEl) totalEl.innerText = totalCount;

  const barEl = document.getElementById('ballotProgressBar');
  if (barEl) barEl.style.width = `${pct}%`;

  const votersGrid = document.getElementById('ballotVotersGrid');
  if (votersGrid && gameState.players) {
    votersGrid.innerHTML = '';
    const votedList = gameState.proposal_voted_players || [];
    gameState.players.forEach(pName => {
      const hasVoted = votedList.includes(pName);
      const chip = document.createElement('div');
      chip.className = `voter-chip ${hasVoted ? 'voted' : 'waiting'}`;
      chip.innerHTML = hasVoted ? `✓ ${pName}` : `⏳ ${pName}`;
      votersGrid.appendChild(chip);
    });
  }
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
  
  try {
    const res = await fetch(`/api/state?role=moderator&pin=${encodeURIComponent(pin)}`);
    if (!res.ok) return;
    const data = await res.json();
    
    // Render Saboteurs list
    const sabList = document.getElementById('modSaboteursList');
    const sabCount = document.getElementById('modSaboteurCount');
    if (sabList && data.saboteurs) {
      if (sabCount) sabCount.innerText = data.saboteurs.length;
      sabList.innerHTML = '';
      data.saboteurs.forEach(name => {
        const item = document.createElement('div');
        item.style.background = 'rgba(255, 51, 102, 0.15)';
        item.style.border = '1px solid var(--saboteur-red)';
        item.style.borderRadius = '8px';
        item.style.padding = '8px 12px';
        item.style.fontSize = '13px';
        item.style.fontWeight = '800';
        item.style.color = '#fff';
        item.innerHTML = `😈 ${name}`;
        sabList.appendChild(item);
      });
    }

    // Render Loyal Resistance list
    const resList = document.getElementById('modResistanceList');
    const resCount = document.getElementById('modResistanceCount');
    if (resList && data.resistance_members) {
      if (resCount) resCount.innerText = data.resistance_members.length;
      resList.innerHTML = '';
      data.resistance_members.forEach(name => {
        const item = document.createElement('div');
        item.style.background = 'rgba(0, 242, 254, 0.1)';
        item.style.border = '1px solid var(--resistance-blue)';
        item.style.borderRadius = '6px';
        item.style.padding = '4px 8px';
        item.style.fontSize = '11px';
        item.style.color = '#fff';
        item.innerHTML = `🏢 ${name}`;
        resList.appendChild(item);
      });
    }

    // Render 5 Heist Missions summary
    const misList = document.getElementById('modMissionsList');
    if (misList && data.missions) {
      misList.innerHTML = '';
      data.missions.forEach((m, idx) => {
        const row = document.createElement('div');
        row.style.background = 'rgba(255, 255, 255, 0.03)';
        row.style.border = '1px solid var(--border-subtle)';
        row.style.borderRadius = '6px';
        row.style.padding = '6px 10px';
        row.style.display = 'flex';
        row.style.justifyContent = 'space-between';
        row.style.alignItems = 'center';
        row.innerHTML = `
          <div>
            <strong style="color: var(--heist-gold);">M${idx+1}: ${m.title}</strong>
            <div style="font-size: 10px; color: var(--text-muted);">${m.story}</div>
          </div>
          <div style="font-size: 11px; font-weight: 800; color: #fff;">
            ${m.team_size} 👥 • ${m.fails_required || 1} Fail
          </div>
        `;
        misList.appendChild(row);
      });
    }

    // Event Log
    const logContainer = document.getElementById('modEventLog');
    if (logContainer && data.history_log) {
      logContainer.innerHTML = '';
      data.history_log.forEach(item => {
        const el = document.createElement('div');
        el.style.marginBottom = '6px';
        el.innerHTML = `<span style="color: var(--gold-accent);">[M${item.mission}]</span> ${item.details}`;
        logContainer.appendChild(el);
      });
    }
  } catch (e) {
    console.error('Error fetching moderator state:', e);
  }
}

// Mission Customizer Modal Functions
function openMissionEditor() {
  if (!gameState || !gameState.missions) return;
  const modal = document.getElementById('missionEditorModal');
  const container = document.getElementById('missionEditorRows');
  container.innerHTML = '';
  
  gameState.missions.forEach((m, idx) => {
    const row = document.createElement('div');
    row.className = 'mission-editor-row';
    row.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <strong style="color: var(--gold-accent);">Mission ${idx + 1}</strong>
        <div style="display: flex; gap: 8px; align-items: center;">
          <label style="font-size: 11px; color: var(--text-muted);">Crew Size:</label>
          <input type="number" class="med-size-input" data-index="${idx+1}" value="${m.team_size}" min="2" max="15" style="width: 50px; padding: 4px; border-radius: 4px; background: rgba(0,0,0,0.4); border: 1px solid var(--border-subtle); color: #fff; text-align: center;">
          <label style="font-size: 11px; color: var(--text-muted);">Fails Needed:</label>
          <input type="number" class="med-fails-input" data-index="${idx+1}" value="${m.fails_required || 1}" min="1" max="5" style="width: 50px; padding: 4px; border-radius: 4px; background: rgba(0,0,0,0.4); border: 1px solid var(--border-subtle); color: #fff; text-align: center;">
        </div>
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">
        <input type="text" class="med-title-input" data-index="${idx+1}" value="${m.title}" placeholder="Mission Title" style="padding: 6px; border-radius: 6px; background: rgba(0,0,0,0.4); border: 1px solid var(--border-subtle); color: #fff; font-size: 12px;">
        <input type="text" class="med-story-input" data-index="${idx+1}" value="${m.story}" placeholder="Storyline objective" style="padding: 6px; border-radius: 6px; background: rgba(0,0,0,0.4); border: 1px solid var(--border-subtle); color: #fff; font-size: 12px;">
      </div>
    `;
    container.appendChild(row);
  });
  
  modal.classList.add('open');
}

async function saveCustomMissions() {
  const pin = sessionStorage.getItem('heist_mod_pin') || '2026';
  const sizeInputs = document.querySelectorAll('.med-size-input');
  const failsInputs = document.querySelectorAll('.med-fails-input');
  const titleInputs = document.querySelectorAll('.med-title-input');
  const storyInputs = document.querySelectorAll('.med-story-input');
  
  const missions = [];
  for (let i = 0; i < 5; i++) {
    missions.push({
      index: i + 1,
      title: titleInputs[i].value.trim() || `Mission ${i+1}`,
      story: storyInputs[i].value.trim() || `Objective ${i+1}`,
      team_size: parseInt(sizeInputs[i].value) || 5,
      fails_required: parseInt(failsInputs[i].value) || 1
    });
  }
  
  await fetch('/api/customize-missions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ missions, pin })
  });
  
  document.getElementById('missionEditorModal').classList.remove('open');
  fetchState();
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
  function openModDrawer() {
    const d = document.getElementById('modDrawer');
    if (d) d.classList.add('open');
    const b = document.getElementById('modDrawerBackdrop');
    if (b) b.classList.add('open');
    renderModeratorDrawer();
  }

  function closeModDrawer() {
    const d = document.getElementById('modDrawer');
    if (d) d.classList.remove('open');
    const b = document.getElementById('modDrawerBackdrop');
    if (b) b.classList.remove('open');
  }

  document.getElementById('btnModToggle').onclick = () => {
    const savedPin = sessionStorage.getItem('heist_mod_pin');
    if (savedPin) {
      openModDrawer();
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
        openModDrawer();
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

  const btnCloseMod = document.getElementById('btnCloseMod');
  if (btnCloseMod) btnCloseMod.onclick = closeModDrawer;

  const modBackdrop = document.getElementById('modDrawerBackdrop');
  if (modBackdrop) modBackdrop.onclick = closeModDrawer;

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModDrawer();
      const pinModal = document.getElementById('modPinModal');
      if (pinModal) pinModal.classList.remove('open');
      const qrModal = document.getElementById('qrModal');
      if (qrModal) qrModal.classList.remove('open');
      const kioskModal = document.getElementById('kioskModal');
      if (kioskModal) kioskModal.classList.remove('open');
      const rouletteModal = document.getElementById('rouletteModal');
      if (rouletteModal) rouletteModal.classList.remove('open');
      const medModal = document.getElementById('missionEditorModal');
      if (medModal) medModal.classList.remove('open');
    }
  });

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

  const btnQr = document.getElementById('btnQr');
  if (btnQr) {
    btnQr.onclick = () => {
      let playUrl = `${window.location.origin}/play`;
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        const ip = gameState ? gameState.local_ip : window.location.hostname;
        const port = window.location.port ? `:${window.location.port}` : '';
        playUrl = `http://${ip}${port}/play`;
      }
      renderQr(playUrl);
      const copyMsg = document.getElementById('copySuccessMsg');
      if (copyMsg) copyMsg.style.display = 'none';
      document.getElementById('qrModal').classList.add('open');
    };
  }

  const btnCopyMob = document.getElementById('btnCopyMobileLink');
  if (btnCopyMob) {
    btnCopyMob.onclick = async () => {
      const url = document.getElementById('qrUrlDisplay').innerText.trim();
      try {
        await navigator.clipboard.writeText(url);
        const msg = document.getElementById('copySuccessMsg');
        if (msg) msg.style.display = 'block';
        setTimeout(() => { if (msg) msg.style.display = 'none'; }, 3000);
      } catch (e) {
        prompt('Copy this link for your colleagues:', url);
      }
    };
  }

  const btnCloseQr = document.getElementById('btnCloseQr');
  if (btnCloseQr) {
    btnCloseQr.onclick = () => {
      document.getElementById('qrModal').classList.remove('open');
    };
  }

  // Setup Actions
  document.getElementById('btnStartGame').onclick = async () => {
    window.soundFx.playClick();
    const pin = sessionStorage.getItem('heist_mod_pin') || '2026';
    const playersToStart = setupActivePlayers.length > 0 ? setupActivePlayers : gameState.players;
    await fetch('/api/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        players: playersToStart,
        saboteur_count: setupSaboteurCount,
        mission_team_sizes: setupMissionSizes,
        pin: pin
      })
    });
    fetchState();
  };

  const btnReset = document.getElementById('btnResetRoster');
  if (btnReset) {
    btnReset.onclick = () => {
      window.soundFx.playClick();
      setupActivePlayers = RAW_DEFAULT_PLAYERS ? [...RAW_DEFAULT_PLAYERS] : (gameState ? [...gameState.players] : []);
      setupAbsentPlayers = [];
      setupSaboteurCount = calculateRecommendedSaboteurs(setupActivePlayers.length);
      setupMissionSizes = calculateRecommendedTeamSizes(setupActivePlayers.length);
      renderSetupPhase();
    };
  }

  const inputNewPlayer = document.getElementById('newPlayerName');
  const btnAdd = document.getElementById('btnAddPlayer');
  
  function addNewPlayerFromInput() {
    const val = inputNewPlayer.value.trim();
    if (!val) return;
    window.soundFx.playClick();
    if (!setupActivePlayers.includes(val)) {
      setupActivePlayers.push(val);
    }
    inputNewPlayer.value = '';
    setupSaboteurCount = calculateRecommendedSaboteurs(setupActivePlayers.length);
    setupMissionSizes = calculateRecommendedTeamSizes(setupActivePlayers.length);
    renderSetupPhase();
  }

  if (btnAdd) btnAdd.onclick = addNewPlayerFromInput;
  if (inputNewPlayer) {
    inputNewPlayer.onkeydown = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        addNewPlayerFromInput();
      }
    };
  }

  const btnDecSab = document.getElementById('btnDecSaboteur');
  if (btnDecSab) {
    btnDecSab.onclick = () => {
      window.soundFx.playClick();
      setupSaboteurCount = Math.max(1, setupSaboteurCount - 1);
      renderSetupPhase();
    };
  }
  const btnIncSab = document.getElementById('btnIncSaboteur');
  if (btnIncSab) {
    btnIncSab.onclick = () => {
      window.soundFx.playClick();
      setupSaboteurCount = Math.min(Math.floor(setupActivePlayers.length / 2), setupSaboteurCount + 1);
      renderSetupPhase();
    };
  }

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

  // Emergency Tally buttons (inside accordion)
  const tallyYes = document.getElementById('tallyYes');
  const tallyNo = document.getElementById('tallyNo');
  const btnIncY = document.getElementById('btnIncYes');
  if (btnIncY) btnIncY.onclick = () => { tallyYes.innerText = parseInt(tallyYes.innerText || '0') + 1; };
  const btnDecY = document.getElementById('btnDecYes');
  if (btnDecY) btnDecY.onclick = () => { tallyYes.innerText = Math.max(0, parseInt(tallyYes.innerText || '0') - 1); };
  const btnIncN = document.getElementById('btnIncNo');
  if (btnIncN) btnIncN.onclick = () => { tallyNo.innerText = parseInt(tallyNo.innerText || '0') + 1; };
  const btnDecN = document.getElementById('btnDecNo');
  if (btnDecN) btnDecN.onclick = () => { tallyNo.innerText = Math.max(0, parseInt(tallyNo.innerText || '0') - 1); };

  // Resolve Team Proposal Vote (Pure mobile vote calculation!)
  document.getElementById('btnResolveProposalVote').onclick = async () => {
    pauseTimer();
    const res = await fetch('/api/resolve-proposal-vote', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    const result = await res.json();
    handleProposalVoteResult(result);
  };

  const btnManualVote = document.getElementById('btnManualOverrideVote');
  if (btnManualVote) {
    btnManualVote.onclick = async () => {
      pauseTimer();
      const yesCount = parseInt(document.getElementById('tallyYes').innerText || '0');
      const noCount = parseInt(document.getElementById('tallyNo').innerText || '0');
      const res = await fetch('/api/resolve-proposal-vote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ yes_count: yesCount, no_count: noCount })
      });
      const result = await res.json();
      handleProposalVoteResult(result);
    };
  }

  function handleProposalVoteResult(result) {
    if (result.approved) {
      window.soundFx.playApproved();
    } else {
      window.soundFx.playRejected();
    }

    const banner = document.getElementById('proposalResultBanner');
    const icon = document.getElementById('proposalResultIcon');
    const title = document.getElementById('proposalResultTitle');
    const details = document.getElementById('proposalResultDetails');
    const proceedBtn = document.getElementById('btnProceedToMission');

    const yesCount = result.yes_votes;
    const noCount = result.no_votes;

    if (result.approved) {
      banner.style.background = 'rgba(16, 185, 129, 0.15)';
      banner.style.border = '2px solid var(--success-green)';
      icon.innerText = '✅';
      title.innerText = 'TEAM PROPOSAL APPROVED!';
      title.style.color = 'var(--success-green)';
      details.innerText = `${yesCount} Approved vs ${noCount} Rejected by mobile ballot. The heist team enters the vault!`;
      proceedBtn.style.display = 'inline-block';
    } else {
      banner.style.background = 'rgba(255, 51, 102, 0.15)';
      banner.style.border = '2px solid var(--saboteur-red)';
      icon.innerText = '❌';
      title.innerText = 'TEAM PROPOSAL REJECTED!';
      title.style.color = 'var(--saboteur-red)';
      details.innerText = `${noCount} Rejected vs ${yesCount} Approved by mobile ballot. Leader token passes clockwise!`;
      proceedBtn.style.display = 'none';
      setTimeout(() => fetchState(), 2500);
    }

    document.getElementById('phaseDebate').style.display = 'none';
    document.getElementById('phaseProposalResult').style.display = 'block';
  }

  // Mission Editor Modal Wiring
  const btnOpenMed = document.getElementById('btnOpenMissionEditor');
  if (btnOpenMed) btnOpenMed.onclick = openMissionEditor;

  const btnCloseMed = document.getElementById('btnCloseMissionEditor');
  if (btnCloseMed) btnCloseMed.onclick = () => document.getElementById('missionEditorModal').classList.remove('open');

  const btnCancelMed = document.getElementById('btnCancelMissions');
  if (btnCancelMed) btnCancelMed.onclick = () => document.getElementById('missionEditorModal').classList.remove('open');

  const btnSaveMed = document.getElementById('btnSaveMissions');
  if (btnSaveMed) btnSaveMed.onclick = saveCustomMissions;
  
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
