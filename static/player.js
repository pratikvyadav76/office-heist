// Mobile Player Client Logic for The Resistance: Office Heist

let playerName = localStorage.getItem('heist_player_name') || '';
let playerState = null;
let ws = null;
let selectedMobileTeam = new Set();

async function init() {
  const urlParams = new URLSearchParams(window.location.search);
  const paramPlayer = urlParams.get('player') || urlParams.get('name') || urlParams.get('user');

  await populatePlayerList(paramPlayer);
  connectWebSocket();
  setupEventListeners();
  
  if (playerName) {
    switchToActivePlayer();
  }
}

async function populatePlayerList(preferredParam = '') {
  try {
    const res = await fetch('/api/state?role=public');
    const data = await res.json();
    const select = document.getElementById('playerSelect');
    select.innerHTML = '<option value="">-- Choose your name --</option>';
    
    let matchedName = null;

    const HOST_USERNAMES = ['pratik.yadav', 'om.naik', 'vighnesh.jadhav'];

    data.players.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p;
      opt.innerText = p;

      // If preferredParam passed via URL e.g. ?user=tanmay.indore or ?user=Tanmay
      if (preferredParam) {
        const cleanParam = preferredParam.trim().toLowerCase();
        if (p.toLowerCase().includes(cleanParam)) {
          matchedName = p;
        }
      }

      if (p === playerName) opt.selected = true;
      select.appendChild(opt);
    });

    if (preferredParam && !matchedName) {
      const cleanParam = preferredParam.trim().toLowerCase();
      if (HOST_USERNAMES.some(u => cleanParam.includes(u))) {
        matchedName = preferredParam;
        sessionStorage.setItem('heist_mod_pin', '2026');
      }
    }

    if (matchedName) {
      playerName = matchedName;
      localStorage.setItem('heist_player_name', matchedName);
      select.value = matchedName;
    }
  } catch (e) {
    console.error('Error fetching player roster:', e);
  }
}

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;
  
  ws = new WebSocket(wsUrl);
  
  ws.onopen = () => {
    document.getElementById('connBadge').innerText = '● LIVE';
    document.getElementById('connBadge').style.color = 'var(--success-green)';
    if (playerName) refreshPlayerState();
  };
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'STATE_UPDATE' || data.type === 'PROPOSAL_RESULT_ANNOUNCED' || data.type === 'MISSION_REVEAL') {
        if (playerName) refreshPlayerState();
      } else if (data.type === 'LEADER_SPUN') {
        showMobileLeaderToast(`👑 THE PROFESSOR CHOSE: ${data.leader}`);
        if (playerName) refreshPlayerState();
      } else if (data.type === 'TIMER_UPDATE') {
        syncMobileTimer(data.timer_seconds, data.timer_running, data.timer_end_timestamp);
      }
    } catch (e) {
      console.error(e);
    }
  };
  
  ws.onclose = () => {
    document.getElementById('connBadge').innerText = '○ OFFLINE';
    document.getElementById('connBadge').style.color = 'var(--saboteur-red)';
    setTimeout(connectWebSocket, 2000);
  };
}

let mobileTimerInterval = null;
function syncMobileTimer(seconds, isRunning, endTimestamp) {
  if (mobileTimerInterval) {
    clearInterval(mobileTimerInterval);
    mobileTimerInterval = null;
  }

  function renderMobileDigits(sec) {
    const mins = Math.floor(sec / 60);
    const s = sec % 60;
    const str = `${String(mins).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    const el = document.getElementById('mobileTimerDigits');
    const pill = document.getElementById('mobileTimerPill');
    if (el) el.innerText = str;
    if (pill) {
      if (sec <= 15 && isRunning) {
        pill.classList.add('danger');
      } else {
        pill.classList.remove('danger');
      }
    }
  }

  renderMobileDigits(seconds);

  if (isRunning && endTimestamp > 0) {
    mobileTimerInterval = setInterval(() => {
      const nowSec = Date.now() / 1000;
      const remaining = Math.max(0, Math.ceil(endTimestamp - nowSec));
      renderMobileDigits(remaining);
      if (remaining <= 0) {
        clearInterval(mobileTimerInterval);
        mobileTimerInterval = null;
        renderMobileDigits(0);
      }
    }, 500);
  }
}

function showMobileLeaderToast(text) {
  const toast = document.getElementById('mobileLeaderToast');
  if (!toast) return;
  toast.innerText = text;
  toast.classList.add('show');
  if (navigator.vibrate) {
    try { navigator.vibrate([100, 50, 100]); } catch (e) {}
  }
  setTimeout(() => toast.classList.remove('show'), 3500);
}

async function refreshPlayerState() {
  if (!playerName) return;
  try {
    const res = await fetch(`/api/state?player=${encodeURIComponent(playerName)}`);
    playerState = await res.json();
    if (playerState.timer_seconds !== undefined) {
      syncMobileTimer(playerState.timer_seconds, playerState.timer_running, playerState.timer_end_timestamp);
    }
    renderPlayerUI();
  } catch (e) {
    console.error('Error fetching player state:', e);
  }
}

function switchToActivePlayer() {
  document.getElementById('selectPlayerCard').style.display = 'none';
  document.getElementById('activePlayerUI').style.display = 'block';
  document.getElementById('agentNameDisplay').innerText = playerName;
  refreshPlayerState();
}

function renderPlayerUI() {
  if (!playerState) return;

  // Universal Current Leader Banner update
  const curLeader = playerState.current_leader || 'Awaiting Selection';
  const leaderNameEl = document.getElementById('mobileLeaderName');
  const banner = document.getElementById('mobileLeaderBanner');
  if (leaderNameEl) {
    if (leaderNameEl.innerText !== curLeader && leaderNameEl.innerText !== 'Awaiting Assignment...' && leaderNameEl.innerText !== 'Loading Leader...') {
      showMobileLeaderToast(`👑 NEW HEIST LEADER: ${curLeader}`);
    }
    leaderNameEl.innerText = curLeader;
  }
  const attemptEl = document.getElementById('mobileProposalAttempt');
  if (attemptEl) {
    attemptEl.innerText = `Attempt ${playerState.proposal_attempt || 1}/${playerState.max_proposal_attempts || 5}`;
  }

  // Highlight banner if this player is the leader!
  if (banner) {
    if (playerState.is_leader) {
      banner.style.background = 'linear-gradient(90deg, #b45309 0%, #f59e0b 50%, #b45309 100%)';
      banner.style.boxShadow = '0 0 15px rgba(245, 158, 11, 0.6)';
    } else {
      banner.style.background = 'linear-gradient(90deg, rgba(229, 9, 20, 0.25) 0%, rgba(245, 158, 11, 0.25) 50%, rgba(229, 9, 20, 0.25) 100%)';
      banner.style.boxShadow = '0 4px 20px rgba(229, 9, 20, 0.2)';
    }
  }
  
  // Render Secret Role Content (Money Heist theme)
  const icon = document.getElementById('roleSecretIcon');
  const title = document.getElementById('roleSecretTitle');
  const desc = document.getElementById('roleSecretDesc');
  const fellowBox = document.getElementById('fellowSaboteursBox');
  const fellowList = document.getElementById('fellowSaboteursList');
  
  if (playerState.is_saboteur) {
    icon.innerText = '🎭';
    title.innerText = 'SECRET SABOTEUR';
    title.style.color = 'var(--heist-red)';
    desc.innerText = 'You are an undercover Saboteur wearing the Dalí mask! Blend in with the Professor\'s crew and secretly fail 3 missions!';
    
    fellowBox.style.display = 'block';
    const others = (playerState.fellow_saboteurs || []).filter(n => n !== playerName);
    fellowList.innerText = others.length ? others.join(', ') : 'None (Only you)';
  } else {
    icon.innerText = '🏛️';
    title.innerText = 'ROYAL MINT OPERATIVE';
    title.style.color = 'var(--resistance-blue)';
    desc.innerText = 'You are a loyal member of the Professor\'s heist crew. Complete 3 heist missions without sabotage to take the vault!';
    fellowBox.style.display = 'none';
  }
  
  // Render Phases
  const leaderSec = document.getElementById('mobileLeaderSection');
  const voteSec = document.getElementById('mobileVoteSection');
  const actionSec = document.getElementById('mobileActionSection');
  const waitCard = document.getElementById('mobileWaitingCard');
  const waitText = document.getElementById('mobileWaitingText');
  
  leaderSec.style.display = 'none';
  voteSec.style.display = 'none';
  actionSec.style.display = 'none';
  waitCard.style.display = 'block';
  
  const phase = playerState.phase;
  
  if (phase === 'LEADER_PROPOSAL') {
    if (playerState.is_leader) {
      leaderSec.style.display = 'block';
      waitCard.style.display = 'none';
      renderMobileLeaderRoster();
    } else {
      waitText.innerText = `Leader ${playerState.current_leader} is selecting the crew for Mission ${playerState.current_mission}...`;
    }
  } else if (phase === 'DEBATE_AND_VOTE') {
    voteSec.style.display = 'block';
    waitCard.style.display = 'none';
    
    // Show proposed chips
    const chipsCont = document.getElementById('mobileProposedChips');
    chipsCont.innerHTML = '';
    (playerState.proposed_team || []).forEach(n => {
      const c = document.createElement('div');
      c.className = 'agent-badge';
      c.style.fontSize = '12px';
      c.style.padding = '4px 10px';
      c.innerText = `🕵️‍♂️ ${n}`;
      chipsCont.appendChild(c);
    });
    
    if (playerState.has_voted_proposal) {
      document.getElementById('mobileVoteButtons').style.display = 'none';
      document.getElementById('mobileVoteConfirmation').style.display = 'block';
    } else {
      document.getElementById('mobileVoteButtons').style.display = 'flex';
      document.getElementById('mobileVoteConfirmation').style.display = 'none';
    }
  } else if (phase === 'MISSION_ACTION') {
    if (playerState.is_on_proposed_team) {
      actionSec.style.display = 'block';
      waitCard.style.display = 'none';
      
      const sabBtn = document.getElementById('btnMobileSabotage');
      if (playerState.is_saboteur) {
        sabBtn.disabled = false;
        sabBtn.style.opacity = '1';
      } else {
        // Resistance rule: cannot sabotage!
        sabBtn.disabled = true;
        sabBtn.style.opacity = '0.2';
      }
      
      if (playerState.has_submitted_mission) {
        document.getElementById('mobileActionButtons').style.display = 'none';
        document.getElementById('mobileActionConfirmation').style.display = 'block';
      } else {
        document.getElementById('mobileActionButtons').style.display = 'flex';
        document.getElementById('mobileActionConfirmation').style.display = 'none';
      }
    } else {
      waitText.innerText = `The chosen crew is executing Mission ${playerState.current_mission}. Awaiting results...`;
    }
  } else if (phase === 'MISSION_RESULT') {
    waitText.innerText = `Mission outcome revealed on the big screen!`;
  } else if (phase === 'GAME_OVER') {
    waitText.innerText = `Game Over! Check Big Screen for victory announcement!`;
  } else {
    waitText.innerText = `Waiting for game to begin...`;
  }
}

function renderMobileLeaderRoster() {
  document.getElementById('mobileMissionNum').innerText = playerState.current_mission;
  document.getElementById('mobileReqSize').innerText = playerState.required_team_size;
  
  const grid = document.getElementById('mobileRosterGrid');
  grid.innerHTML = '';
  selectedMobileTeam.clear();
  updateMobileProposalButton();
  
  playerState.players.forEach(name => {
    const btn = document.createElement('button');
    btn.className = 'btn-icon';
    btn.style.width = '100%';
    btn.style.padding = '10px 8px';
    btn.style.fontSize = '13px';
    btn.innerText = name;
    
    btn.onclick = () => {
      if (selectedMobileTeam.has(name)) {
        selectedMobileTeam.delete(name);
        btn.style.background = 'rgba(255,255,255,0.05)';
        btn.style.borderColor = 'var(--border-subtle)';
      } else {
        if (selectedMobileTeam.size < playerState.required_team_size) {
          selectedMobileTeam.add(name);
          btn.style.background = 'rgba(0, 242, 254, 0.2)';
          btn.style.borderColor = 'var(--resistance-blue)';
        }
      }
      updateMobileProposalButton();
    };
    grid.appendChild(btn);
  });
}

function updateMobileProposalButton() {
  const btn = document.getElementById('btnMobilePropose');
  const size = selectedMobileTeam.size;
  const req = playerState ? playerState.required_team_size : 5;
  btn.disabled = (size !== req);
  btn.innerText = `Confirm Proposed Team (${size}/${req})`;
}

function setupEventListeners() {
  // Select Player
  document.getElementById('btnConfirmPlayer').onclick = () => {
    const val = document.getElementById('playerSelect').value;
    if (val) {
      playerName = val;
      localStorage.setItem('heist_player_name', val);
      switchToActivePlayer();
    }
  };
  
  // Switch Player
  document.getElementById('btnSwitchPlayer').onclick = () => {
    localStorage.removeItem('heist_player_name');
    playerName = '';
    document.getElementById('selectPlayerCard').style.display = 'block';
    document.getElementById('activePlayerUI').style.display = 'none';
  };
  
  // Press and Hold Role Card Reveal
  const holdBtn = document.getElementById('btnHoldReveal');
  const cover = document.getElementById('roleCover');
  const content = document.getElementById('roleSecretContent');
  
  const showRole = (e) => {
    e.preventDefault();
    cover.style.display = 'none';
    content.classList.add('revealed');
  };
  
  const hideRole = (e) => {
    e.preventDefault();
    cover.style.display = 'block';
    content.classList.remove('revealed');
  };
  
  holdBtn.addEventListener('mousedown', showRole);
  holdBtn.addEventListener('mouseup', hideRole);
  holdBtn.addEventListener('mouseleave', hideRole);
  holdBtn.addEventListener('touchstart', showRole);
  holdBtn.addEventListener('touchend', hideRole);
  holdBtn.addEventListener('touchcancel', hideRole);
  
  // Propose Team
  document.getElementById('btnMobilePropose').onclick = async () => {
    const team = Array.from(selectedMobileTeam);
    await fetch('/api/propose-team', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team })
    });
    refreshPlayerState();
  };
  
  // Cast Proposal Vote
  document.getElementById('btnMobileApprove').onclick = async () => {
    await castVote('YES');
  };
  document.getElementById('btnMobileReject').onclick = async () => {
    await castVote('NO');
  };
  
  // Submit Mission Action
  document.getElementById('btnMobileSuccess').onclick = async () => {
    await submitAction('SUCCESS');
  };
  document.getElementById('btnMobileSabotage').onclick = async () => {
    await submitAction('SABOTAGE');
  };

  // Mobile Host Deck Toggle & PIN Auth
  const hostToggleBtn = document.getElementById('btnMobileHostToggle');
  const hostDeck = document.getElementById('mobileHostDeck');
  const closeHostBtn = document.getElementById('btnCloseMobileHost');
  const HOST_USERNAMES = ['pratik.yadav', 'om.naik', 'vighnesh.jadhav'];

  hostToggleBtn.onclick = () => {
    let savedPin = sessionStorage.getItem('heist_mod_pin') || '';
    const isNamedHost = HOST_USERNAMES.some(u => (playerName || '').toLowerCase().includes(u));
    
    if (savedPin === '2026' || isNamedHost) {
      if (!savedPin) sessionStorage.setItem('heist_mod_pin', '2026');
      hostDeck.style.display = (hostDeck.style.display === 'none') ? 'block' : 'none';
      if (hostDeck.style.display === 'block') {
        hostDeck.scrollIntoView({ behavior: 'smooth' });
      }
    } else {
      document.getElementById('inputMobPin').value = '';
      document.getElementById('mobPinError').style.display = 'none';
      document.getElementById('mobPinModal').classList.add('open');
      setTimeout(() => document.getElementById('inputMobPin').focus(), 100);
    }
  };

  document.getElementById('btnSubmitMobPin').onclick = () => {
    const enteredPin = document.getElementById('inputMobPin').value.trim();
    if (enteredPin === '2026') {
      sessionStorage.setItem('heist_mod_pin', '2026');
      document.getElementById('mobPinModal').classList.remove('open');
      hostDeck.style.display = 'block';
      hostDeck.scrollIntoView({ behavior: 'smooth' });
    } else {
      document.getElementById('mobPinError').style.display = 'block';
    }
  };

  document.getElementById('btnCancelMobPin').onclick = () => {
    document.getElementById('mobPinModal').classList.remove('open');
  };

  closeHostBtn.onclick = () => {
    hostDeck.style.display = 'none';
  };

  // Mobile Host Deck Actions
  document.getElementById('btnMobSpinLeader').onclick = async () => {
    const pin = sessionStorage.getItem('heist_mod_pin') || '2026';
    const res = await fetch('/api/spin-leader', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pin })
    });
    const d = await res.json();
    if (d.current_leader) {
      showMobileLeaderToast(`👑 THE PROFESSOR CHOSE: ${d.current_leader}`);
      refreshPlayerState();
    }
  };

  document.getElementById('btnMobRotateLeader').onclick = async () => {
    await fetch('/api/rotate-leader-manually', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}'
    });
    refreshPlayerState();
  };

  document.getElementById('btnMobTimerStart').onclick = async () => {
    await fetch('/api/timer-action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'START' })
    });
  };

  document.getElementById('btnMobTimerPause').onclick = async () => {
    await fetch('/api/timer-action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'PAUSE' })
    });
  };

  document.getElementById('btnMobApproveVote').onclick = async () => {
    if (confirm('Force Approve the proposed team?')) {
      await fetch('/api/resolve-proposal-vote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ yes_count: 22, no_count: 0 })
      });
      refreshPlayerState();
    }
  };

  document.getElementById('btnMobRejectVote').onclick = async () => {
    if (confirm('Force Reject the proposed team?')) {
      await fetch('/api/resolve-proposal-vote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ yes_count: 0, no_count: 22 })
      });
      refreshPlayerState();
    }
  };

  document.getElementById('btnMobNextMission').onclick = async () => {
    if (confirm('Proceed to next heist mission?')) {
      await fetch('/api/next-mission', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}'
      });
      refreshPlayerState();
    }
  };

  document.getElementById('btnMobShowWhispers').onclick = async () => {
    const area = document.getElementById('mobWhispersArea');
    const list = document.getElementById('mobSaboteursList');
    if (area.style.display === 'block') {
      area.style.display = 'none';
      return;
    }
    const pin = sessionStorage.getItem('heist_mod_pin') || '2026';
    try {
      const res = await fetch(`/api/whispers?pin=${pin}`);
      if (res.ok) {
        const data = await res.json();
        list.innerHTML = '';
        data.saboteurs.forEach((s, idx) => {
          const div = document.createElement('div');
          div.style.padding = '4px 0';
          div.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
          div.innerHTML = `<strong>${idx + 1}. 😈 ${s}</strong>`;
          list.appendChild(div);
        });
        area.style.display = 'block';
      } else {
        alert('Could not load Saboteurs. Check PIN.');
      }
    } catch (e) {
      alert('Error fetching secret Saboteurs.');
    }
  };
}

async function castVote(v) {
  await fetch('/api/proposal-vote', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_name: playerName, vote: v })
  });
  refreshPlayerState();
}

async function submitAction(act) {
  await fetch('/api/mission-action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_name: playerName, action: act })
  });
  refreshPlayerState();
}

document.addEventListener('DOMContentLoaded', init);
