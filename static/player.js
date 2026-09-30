// Mobile Player Client Logic for The Resistance: Office Heist

let playerName = localStorage.getItem('heist_player_name') || '';
let playerState = null;
let ws = null;
let selectedMobileTeam = new Set();

function init() {
  populatePlayerList();
  connectWebSocket();
  setupEventListeners();
  
  if (playerName) {
    switchToActivePlayer();
  }
}

async function populatePlayerList() {
  try {
    const res = await fetch('/api/state?role=public');
    const data = await res.json();
    const select = document.getElementById('playerSelect');
    select.innerHTML = '<option value="">-- Choose your name --</option>';
    
    data.players.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p;
      opt.innerText = p;
      if (p === playerName) opt.selected = true;
      select.appendChild(opt);
    });
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

async function refreshPlayerState() {
  if (!playerName) return;
  try {
    const res = await fetch(`/api/state?player=${encodeURIComponent(playerName)}`);
    playerState = await res.json();
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
  
  // Render Secret Role Content
  const icon = document.getElementById('roleSecretIcon');
  const title = document.getElementById('roleSecretTitle');
  const desc = document.getElementById('roleSecretDesc');
  const fellowBox = document.getElementById('fellowSaboteursBox');
  const fellowList = document.getElementById('fellowSaboteursList');
  
  if (playerState.is_saboteur) {
    icon.innerText = '😈';
    title.innerText = 'SABOTEUR';
    title.style.color = 'var(--saboteur-red)';
    desc.innerText = 'You are a secret Saboteur! Infiltrate missions and cause 3 to fail!';
    
    fellowBox.style.display = 'block';
    const others = (playerState.fellow_saboteurs || []).filter(n => n !== playerName);
    fellowList.innerText = others.length ? others.join(', ') : 'None (Only you)';
  } else {
    icon.innerText = '🏢';
    title.innerText = 'LOYAL RESISTANCE';
    title.style.color = 'var(--resistance-blue)';
    desc.innerText = 'You are loyal to the Resistance. Pass 3 missions to win the heist!';
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
