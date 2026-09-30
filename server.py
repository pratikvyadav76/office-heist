import os
import json
import random
import socket
import asyncio
import time
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel

app = FastAPI(title="The Resistance: Office Heist")

STATE_FILE = os.path.join(os.path.dirname(__file__), "game_state.json")

# Default Moderator PIN to protect Moderator Desk from players
MODERATOR_PIN = os.environ.get("MOD_PIN", "2026")

# Designated 3 Moderators
MODERATORS = [
    {"name": "Pratik Yadav", "username": "pratik.yadav", "role": "Lead Host"},
    {"name": "Om Naik", "username": "om.naik", "role": "Secret Whisperer"},
    {"name": "Vighnesh Jadhav", "username": "vighnesh.jadhav", "role": "Pacer & Collector"}
]

# Official Player Roster with unique firstname.lastname
RAW_PLAYER_DATA = [
    ("Riya Patil", "riya.patil"),
    ("Tanmay Indore", "tanmay.indore"),
    ("Sushil Kanojiya", "sushil.kanojiya"),
    ("Pratik Buge", "pratik.buge"),
    ("Karthik Iyer", "karthik.iyer"),
    ("Puja Godse", "puja.godse"),
    ("Niki Panchal", "niki.panchal"),
    ("Bhishma Mahajan", "bhishma.mahajan"),
    ("Sonakshi Julka", "sonakshi.julka"),
    ("Siddhesh Kadu", "siddhesh.kadu"),
    ("Smeet Shethia", "smeet.shethia"),
    ("Purva Hirve", "purva.hirve"),
    ("Shrukti Tamakuwala", "shrukti.tamakuwala"),
    ("Sanchay Mota", "sanchay.mota"),
    ("Akshay Thakare", "akshay.thakare"),
    ("Vidisha Shetty", "vidisha.shetty"),
    ("Saket Shinde", "saket.shinde"),
    ("Rohan Hile", "rohan.hile"),
    ("Siddharth Sharma", "siddharth.sharma"),
    ("Evelin Puthoor", "evelin.puthoor"),
    ("Mohammad Arbaz", "mohammad.arbaz"),
    ("Aishwarya Hate", "aishwarya.hate"),
    ("Pratik Morale", "pratik.morale"),
    ("Md Javed Akhter", "javed.akhter"),
    ("Amit Anilkumar", "amit.anilkumar")
]

DEFAULT_PLAYERS = [f"{name} ({uname})" for name, uname in RAW_PLAYER_DATA]

DEFAULT_MISSIONS = [
    {
        "index": 1,
        "title": "Operation Blackout",
        "story": "Hack Telecoms & Jam Police Radars",
        "description": "Rio taps into the microwave relay and redirects emergency dispatch lines.",
        "team_size": 5,
        "fails_required": 1
    },
    {
        "index": 2,
        "title": "Subterranean Minting",
        "story": "Start Presses & Print €2.4B Untraceable Cash",
        "description": "Nairobi commands the presses churning out crisp uncirculated 50-euro bills.",
        "team_size": 6,
        "fails_required": 1
    },
    {
        "index": 3,
        "title": "The Governor's Vault",
        "story": "Breach Underwater Chamber of Secrets",
        "description": "Berlin & Bogotá dive the flooded vault to extract the state's secret red dossiers.",
        "team_size": 6,
        "fails_required": 1
    },
    {
        "index": 4,
        "title": "Melt 90 Tons of Gold",
        "story": "Melt Reserves into Micro-Pellets",
        "description": "Helsinki and Palermo melt gold bars into micro-grains for hydraulic extraction.",
        "team_size": 7,
        "fails_required": 1
    },
    {
        "index": 5,
        "title": "Plan Chernobyl (Rooftop Extraction)",
        "story": "Deploy Red Smoke Canisters & Helo Extraction",
        "description": "The Professor triggers military decoys and rooftop flares for the final clean getaway.",
        "team_size": 7,
        "fails_required": 1
    }
]

def calculate_default_saboteurs(player_count: int) -> int:
    if player_count <= 6:
        return 2
    elif player_count <= 9:
        return 3
    elif player_count <= 14:
        return 4
    elif player_count <= 28:
        return 5
    else:
        return 6

def calculate_default_team_sizes(player_count: int) -> List[int]:
    if player_count == 5:
        return [2, 3, 2, 3, 3]
    elif player_count == 6:
        return [2, 3, 4, 3, 4]
    elif player_count == 7:
        return [2, 3, 3, 4, 4]
    elif player_count in (8, 9, 10):
        return [3, 4, 4, 5, 5]
    elif player_count <= 14:
        return [4, 5, 5, 6, 6]
    else:
        return [5, 6, 6, 7, 7]

MISSION_TEAM_SIZES = [5, 6, 6, 7, 7]  # Backward compatibility fallback

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                dead.append(conn)
        for d in dead:
            self.disconnect(d)

manager = ConnectionManager()

class GameState:
    def __init__(self):
        self.reset_defaults()

    def reset_defaults(self):
        self.players: List[str] = list(DEFAULT_PLAYERS)
        self.saboteur_count: int = calculate_default_saboteurs(len(self.players))
        self.saboteurs: List[str] = []
        self.current_mission_index: int = 0
        self.mission_results: List[Optional[str]] = [None, None, None, None, None]
        self.mission_secret_sabotages: List[int] = [0, 0, 0, 0, 0]
        self.resistance_score: int = 0
        self.saboteur_score: int = 0
        self.game_over: bool = False
        self.winner: Optional[str] = None
        
        # Missions with Money Heist lore
        self.missions = [dict(m) for m in DEFAULT_MISSIONS]
        default_sizes = calculate_default_team_sizes(len(self.players))
        for idx, sz in enumerate(default_sizes):
            if idx < len(self.missions):
                self.missions[idx]["team_size"] = sz
        self.mission_team_sizes = [m["team_size"] for m in self.missions]
        
        self.phase: str = "SETUP"
        self.leader_index: int = 0
        self.proposed_team: List[str] = []
        self.proposal_attempt: int = 1
        self.max_proposal_attempts: int = 5
        
        self.proposal_votes: Dict[str, str] = {}
        self.mission_submissions: Dict[str, str] = {}
        self.timer_seconds: int = 90
        self.timer_running: bool = False
        self.timer_end_timestamp: float = 0.0
        self.history_log: List[Dict[str, Any]] = []

    def assign_roles(self, custom_saboteurs: Optional[List[str]] = None):
        if custom_saboteurs and len(custom_saboteurs) == self.saboteur_count:
            self.saboteurs = list(custom_saboteurs)
        else:
            if len(self.players) < self.saboteur_count:
                raise ValueError("Not enough players for saboteur count")
            self.saboteurs = random.sample(self.players, self.saboteur_count)
        self.phase = "LEADER_PROPOSAL"
        self.log_event("GAME_STARTED", f"Game started with {len(self.players)} players. {self.saboteur_count} Saboteurs assigned in secret.")
        self.save()

    def spin_random_leader(self) -> str:
        if not self.players:
            return ""
        available = [i for i in range(len(self.players)) if i != self.leader_index]
        self.leader_index = random.choice(available) if available else 0
        new_leader = self.players[self.leader_index]
        self.log_event("LEADER_SPUN", f"The Professor's Roulette appointed {new_leader} as the new Heist Leader!")
        self.save()
        return new_leader

    def get_public_state(self) -> dict:
        cur_mission = self.missions[self.current_mission_index] if self.current_mission_index < len(self.missions) else None
        required_team_size = cur_mission["team_size"] if cur_mission else 0
        fails_required = cur_mission.get("fails_required", 1) if cur_mission else 1

        rem_sec = self.timer_seconds
        if self.timer_running and self.timer_end_timestamp > 0:
            rem_sec = max(0, int(self.timer_end_timestamp - time.time()))
            if rem_sec == 0:
                self.timer_running = False
                self.timer_seconds = 0

        return {
            "phase": self.phase,
            "players": self.players,
            "player_count": len(self.players),
            "saboteur_count": self.saboteur_count,
            "resistance_count": len(self.players) - self.saboteur_count,
            "current_mission": self.current_mission_index + 1,
            "missions": self.missions,
            "current_mission_info": cur_mission,
            "mission_team_sizes": [m["team_size"] for m in self.missions],
            "required_team_size": required_team_size,
            "fails_required": fails_required,
            "mission_results": self.mission_results,
            "resistance_score": self.resistance_score,
            "saboteur_score": self.saboteur_score,
            "game_over": self.game_over,
            "winner": self.winner,
            "current_leader": self.players[self.leader_index] if self.players else None,
            "leader_index": self.leader_index,
            "proposed_team": self.proposed_team,
            "proposal_attempt": self.proposal_attempt,
            "max_proposal_attempts": self.max_proposal_attempts,
            "proposal_votes_count": len(self.proposal_votes),
            "proposal_voted_players": list(self.proposal_votes.keys()),
            "proposal_votes_cast": self.proposal_votes if self.phase in ["PROPOSAL_RESULT", "MISSION_ACTION", "MISSION_RESULT", "GAME_OVER"] else {},
            "mission_submissions_count": len(self.mission_submissions),
            "mission_submitted_players": list(self.mission_submissions.keys()),
            "timer_seconds": rem_sec,
            "timer_running": self.timer_running,
            "timer_end_timestamp": self.timer_end_timestamp if self.timer_running else 0,
            "history_log": self.history_log,
            "local_ip": get_local_ip(),
            "moderators": MODERATORS
        }

    def get_moderator_state(self) -> dict:
        pub = self.get_public_state()
        pub["saboteurs"] = self.saboteurs
        pub["resistance_members"] = [p for p in self.players if p not in self.saboteurs]
        pub["mission_secret_sabotages"] = self.mission_secret_sabotages
        pub["mission_submissions_raw"] = self.mission_submissions
        return pub

    def get_player_state(self, player_key: str) -> dict:
        # Match player by full label or username
        matched_player = None
        for p in self.players:
            if player_key.lower() in p.lower():
                matched_player = p
                break
        if not matched_player:
            matched_player = player_key
            
        pub = self.get_public_state()
        is_saboteur = matched_player in self.saboteurs
        pub["player_name"] = matched_player
        pub["is_saboteur"] = is_saboteur
        pub["role"] = "SABOTEUR" if is_saboteur else "RESISTANCE"
        pub["fellow_saboteurs"] = self.saboteurs if is_saboteur else []
        pub["is_leader"] = (matched_player == self.players[self.leader_index]) if self.players else False
        pub["is_on_proposed_team"] = matched_player in self.proposed_team
        pub["has_voted_proposal"] = matched_player in self.proposal_votes
        pub["has_submitted_mission"] = matched_player in self.mission_submissions
        return pub

    def log_event(self, event_type: str, details: str):
        self.history_log.insert(0, {
            "type": event_type,
            "details": details,
            "mission": self.current_mission_index + 1,
            "attempt": self.proposal_attempt
        })

    def rotate_leader(self):
        if self.players:
            self.leader_index = (self.leader_index + 1) % len(self.players)

    def save(self):
        try:
            data = {
                "players": self.players,
                "saboteur_count": self.saboteur_count,
                "saboteurs": self.saboteurs,
                "current_mission_index": self.current_mission_index,
                "missions": self.missions,
                "mission_team_sizes": [m["team_size"] for m in self.missions],
                "mission_results": self.mission_results,
                "mission_secret_sabotages": self.mission_secret_sabotages,
                "resistance_score": self.resistance_score,
                "saboteur_score": self.saboteur_score,
                "game_over": self.game_over,
                "winner": self.winner,
                "phase": self.phase,
                "leader_index": self.leader_index,
                "proposed_team": self.proposed_team,
                "proposal_attempt": self.proposal_attempt,
                "proposal_votes": self.proposal_votes,
                "mission_submissions": self.mission_submissions,
                "history_log": self.history_log
            }
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")

    def load(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.players = data.get("players", list(DEFAULT_PLAYERS))
                    self.saboteur_count = data.get("saboteur_count", calculate_default_saboteurs(len(self.players)))
                    self.saboteurs = data.get("saboteurs", [])
                    self.current_mission_index = data.get("current_mission_index", 0)
                    
                    saved_missions = data.get("missions")
                    if saved_missions and len(saved_missions) == 5:
                        self.missions = saved_missions
                    else:
                        self.missions = [dict(m) for m in DEFAULT_MISSIONS]
                        def_sizes = calculate_default_team_sizes(len(self.players))
                        for i, sz in enumerate(def_sizes):
                            if i < len(self.missions):
                                self.missions[i]["team_size"] = sz
                    self.mission_team_sizes = [m["team_size"] for m in self.missions]

                    self.mission_results = data.get("mission_results", [None]*5)
                    self.mission_secret_sabotages = data.get("mission_secret_sabotages", [0]*5)
                    self.resistance_score = data.get("resistance_score", 0)
                    self.saboteur_score = data.get("saboteur_score", 0)
                    self.game_over = data.get("game_over", False)
                    self.winner = data.get("winner", None)
                    self.phase = data.get("phase", "SETUP")
                    self.leader_index = data.get("leader_index", 0)
                    self.proposed_team = data.get("proposed_team", [])
                    self.proposal_attempt = data.get("proposal_attempt", 1)
                    self.proposal_votes = data.get("proposal_votes", {})
                    self.mission_submissions = data.get("mission_submissions", {})
                    self.history_log = data.get("history_log", [])
            except Exception as e:
                print(f"Error loading state: {e}")

game = GameState()
game.load()

# Models
class SetupRequest(BaseModel):
    players: List[str]
    saboteur_count: Optional[int] = None
    saboteurs: Optional[List[str]] = None
    mission_team_sizes: Optional[List[int]] = None
    pin: Optional[str] = None

class ProposeTeamRequest(BaseModel):
    team: List[str]

class ProposalVoteRequest(BaseModel):
    player_name: str
    vote: str

class ManualProposalVoteRequest(BaseModel):
    yes_count: Optional[int] = None
    no_count: Optional[int] = None

class MissionConfigItem(BaseModel):
    index: int
    title: str
    story: str
    team_size: int
    fails_required: int = 1

class CustomizeMissionsRequest(BaseModel):
    missions: List[MissionConfigItem]
    pin: Optional[str] = None

class MissionActionRequest(BaseModel):
    player_name: str
    action: str

class ManualMissionTallyRequest(BaseModel):
    success_count: Optional[int] = None
    sabotage_count: Optional[int] = None

class TimerActionRequest(BaseModel):
    action: str
    seconds: Optional[int] = 90
    pin: Optional[str] = None

class SpinLeaderRequest(BaseModel):
    pin: Optional[str] = None

def verify_moderator_pin(pin: Optional[str]):
    if not pin or str(pin).strip() != MODERATOR_PIN:
        raise HTTPException(status_code=403, detail="Invalid Moderator PIN")

# API Endpoints
@app.get("/api/state")
async def get_state(role: str = "public", player: Optional[str] = None, pin: Optional[str] = None):
    if role == "moderator":
        verify_moderator_pin(pin)
        return game.get_moderator_state()
    elif player:
        return game.get_player_state(player)
    return game.get_public_state()

@app.post("/api/verify-mod-pin")
async def verify_pin(data: Dict[str, str]):
    pin = data.get("pin", "")
    if pin.strip() == MODERATOR_PIN:
        return {"status": "ok", "valid": True}
    raise HTTPException(status_code=403, detail="Incorrect Moderator PIN")

@app.post("/api/setup")
async def setup_game(req: SetupRequest):
    if req.pin:
        verify_moderator_pin(req.pin)
    cleaned = [p.strip() for p in req.players if p.strip()]
    if len(cleaned) < 5:
        raise HTTPException(status_code=400, detail="At least 5 players required")
    game.players = cleaned
    
    if req.saboteur_count and 1 <= req.saboteur_count < len(cleaned):
        game.saboteur_count = req.saboteur_count
    else:
        game.saboteur_count = calculate_default_saboteurs(len(cleaned))
        
    if req.mission_team_sizes and len(req.mission_team_sizes) == 5:
        for idx, sz in enumerate(req.mission_team_sizes):
            if idx < len(game.missions):
                game.missions[idx]["team_size"] = sz
    else:
        recommended = calculate_default_team_sizes(len(cleaned))
        for idx, sz in enumerate(recommended):
            if idx < len(game.missions):
                game.missions[idx]["team_size"] = sz
                
    game.mission_team_sizes = [m["team_size"] for m in game.missions]
    game.assign_roles(req.saboteurs)
    await manager.broadcast({"type": "STATE_UPDATE", "state": game.get_public_state()})
    return {"status": "ok", "state": game.get_moderator_state()}

@app.post("/api/customize-missions")
async def customize_missions(req: CustomizeMissionsRequest):
    if req.pin:
        verify_moderator_pin(req.pin)
    for m in req.missions:
        if 1 <= m.index <= 5:
            idx = m.index - 1
            if idx < len(game.missions):
                game.missions[idx]["title"] = m.title
                game.missions[idx]["story"] = m.story
                game.missions[idx]["team_size"] = m.team_size
                game.missions[idx]["fails_required"] = m.fails_required
    game.mission_team_sizes = [m["team_size"] for m in game.missions]
    game.save()
    await manager.broadcast({"type": "STATE_UPDATE", "state": game.get_public_state()})
    return {"status": "ok", "missions": game.missions}

@app.post("/api/propose-team")
async def propose_team(req: ProposeTeamRequest):
    req_size = game.mission_team_sizes[game.current_mission_index] if game.current_mission_index < len(game.mission_team_sizes) else 5
    if len(req.team) != req_size:
        raise HTTPException(status_code=400, detail=f"Mission {game.current_mission_index+1} requires exactly {req_size} players")
    game.proposed_team = req.team
    game.phase = "DEBATE_AND_VOTE"
    game.proposal_votes = {}
    game.timer_seconds = 90
    game.timer_running = False
    leader_name = game.players[game.leader_index] if game.players else "Leader"
    game.log_event("TEAM_PROPOSED", f"Leader {leader_name} proposed team: {', '.join(req.team)} (Attempt {game.proposal_attempt}/{game.max_proposal_attempts})")
    game.save()
    await manager.broadcast({"type": "STATE_UPDATE", "state": game.get_public_state()})
    return {"status": "ok"}

@app.post("/api/proposal-vote")
async def cast_proposal_vote(req: ProposalVoteRequest):
    if game.phase != "DEBATE_AND_VOTE":
        raise HTTPException(status_code=400, detail="Not in debate and voting phase")
    game.proposal_votes[req.player_name] = "YES" if req.vote.upper() == "YES" else "NO"
    game.save()
    await manager.broadcast({
        "type": "VOTE_CAST", 
        "player": req.player_name, 
        "total_votes": len(game.proposal_votes),
        "total_players": len(game.players),
        "voted_players": list(game.proposal_votes.keys())
    })
    return {"status": "ok", "voted": len(game.proposal_votes)}

@app.post("/api/resolve-proposal-vote")
async def resolve_proposal_vote(manual: Optional[ManualProposalVoteRequest] = None):
    if manual and ((manual.yes_count is not None and manual.yes_count > 0) or (manual.no_count is not None and manual.no_count > 0)):
        yes_votes = manual.yes_count or 0
        no_votes = manual.no_count or 0
        total_votes = yes_votes + no_votes
    else:
        yes_votes = sum(1 for v in game.proposal_votes.values() if v == "YES")
        no_votes = sum(1 for v in game.proposal_votes.values() if v == "NO")
        total_votes = len(game.proposal_votes)
        
    approved = (yes_votes > (total_votes / 2.0)) if total_votes > 0 else False
    game.phase = "PROPOSAL_RESULT"
    
    leader_name = game.players[game.leader_index] if game.players else "Leader"
    team_str = ", ".join(game.proposed_team)
    
    if approved:
        game.log_event("PROPOSAL_APPROVED", f"Team [{team_str}] was APPROVED ({yes_votes} Yes vs {no_votes} No). Proceeding to heist!")
        game.phase = "MISSION_ACTION"
        game.mission_submissions = {}
    else:
        game.log_event("PROPOSAL_REJECTED", f"Team [{team_str}] was REJECTED ({yes_votes} Yes vs {no_votes} No). Leader passes.")
        game.proposal_attempt += 1
        if game.proposal_attempt > game.max_proposal_attempts:
            game.game_over = True
            game.winner = "Saboteurs"
            game.phase = "GAME_OVER"
            game.log_event("GAME_OVER", "5 consecutive team proposals were rejected! Saboteurs win by infiltration chaos!")
        else:
            game.rotate_leader()
            game.phase = "LEADER_PROPOSAL"
            game.proposed_team = []
            
    game.save()
    await manager.broadcast({"type": "PROPOSAL_RESULT_ANNOUNCED", "approved": approved, "yes_votes": yes_votes, "no_votes": no_votes, "state": game.get_public_state()})
    return {"approved": approved, "yes_votes": yes_votes, "no_votes": no_votes}

@app.post("/api/mission-action")
async def submit_mission_action(req: MissionActionRequest):
    if game.phase != "MISSION_ACTION":
        raise HTTPException(status_code=400, detail="Not in mission action phase")
    if req.player_name not in game.proposed_team:
        raise HTTPException(status_code=400, detail="Player is not on the mission team")
        
    is_saboteur = req.player_name in game.saboteurs
    action = req.action.upper()
    if action not in ["SUCCESS", "SABOTAGE"]:
        raise HTTPException(status_code=400, detail="Action must be SUCCESS or SABOTAGE")
        
    if not is_saboteur and action == "SABOTAGE":
        raise HTTPException(status_code=400, detail="Resistance members cannot sabotage the heist!")
        
    game.mission_submissions[req.player_name] = action
    game.save()
    
    await manager.broadcast({
        "type": "MISSION_ACTION_SUBMITTED",
        "submissions_count": len(game.mission_submissions),
        "required_count": len(game.proposed_team),
        "submitted_players": list(game.mission_submissions.keys())
    })
    return {"status": "ok", "submitted": len(game.mission_submissions), "total_needed": len(game.proposed_team)}

@app.post("/api/resolve-mission")
async def resolve_mission(manual: Optional[ManualMissionTallyRequest] = None):
    if manual and ((manual.success_count is not None and manual.success_count > 0) or (manual.sabotage_count is not None and manual.sabotage_count > 0)):
        sabotage_count = manual.sabotage_count or 0
        success_count = manual.success_count or 0
    else:
        sabotage_count = sum(1 for act in game.mission_submissions.values() if act == "SABOTAGE")
        success_count = sum(1 for act in game.mission_submissions.values() if act == "SUCCESS")
        
    mission_idx = game.current_mission_index
    game.mission_secret_sabotages[mission_idx] = sabotage_count
    
    fails_needed = 1
    if mission_idx < len(game.missions):
        fails_needed = game.missions[mission_idx].get("fails_required", 1)
        
    is_success = (sabotage_count < fails_needed)
    
    if is_success:
        game.mission_results[mission_idx] = "SUCCESS"
        game.resistance_score += 1
        game.log_event("MISSION_SUCCESS", f"Mission {mission_idx+1} SUCCEEDED! The vault security was cracked clean!")
    else:
        game.mission_results[mission_idx] = "FAILED"
        game.saboteur_score += 1
        # Crucial rule: Do not tell players how many Saboteurs were on the mission; say only 'Mission failed.'
        game.log_event("MISSION_FAILED", f"Mission {mission_idx+1} FAILED! Sabotage detected in the operation!")
        
    if game.resistance_score >= 3:
        game.game_over = True
        game.winner = "Resistance"
        game.phase = "GAME_OVER"
        game.log_event("GAME_OVER", "RESISTANCE WINS! The office heist was a complete success!")
    elif game.saboteur_score >= 3:
        game.game_over = True
        game.winner = "Saboteurs"
        game.phase = "GAME_OVER"
        game.log_event("GAME_OVER", "SABOTEURS WIN! The heist was completely compromised!")
    else:
        game.phase = "MISSION_RESULT"
        
    game.save()
    
    await manager.broadcast({
        "type": "MISSION_REVEAL",
        "mission_index": mission_idx,
        "is_success": is_success,
        "outcome": "SUCCESS" if is_success else "FAILED",
        "state": game.get_public_state()
    })
    return {"outcome": "SUCCESS" if is_success else "FAILED", "state": game.get_public_state()}

@app.post("/api/next-mission")
async def next_mission():
    if game.game_over:
        raise HTTPException(status_code=400, detail="Game is already over")
    game.current_mission_index += 1
    game.proposal_attempt = 1
    game.rotate_leader()
    game.proposed_team = []
    game.proposal_votes = {}
    game.mission_submissions = {}
    game.phase = "LEADER_PROPOSAL"
    game.save()
    await manager.broadcast({"type": "STATE_UPDATE", "state": game.get_public_state()})
    return {"status": "ok", "state": game.get_public_state()}

@app.post("/api/rotate-leader-manually")
async def rotate_leader_manually(req: Dict[str, Any] = {}):
    index = req.get("index")
    if index is not None and 0 <= index < len(game.players):
        game.leader_index = index
    else:
        game.rotate_leader()
    game.save()
    await manager.broadcast({"type": "STATE_UPDATE", "state": game.get_public_state()})
    return {"current_leader": game.players[game.leader_index]}

@app.post("/api/spin-leader")
async def spin_leader(req: SpinLeaderRequest = SpinLeaderRequest()):
    if not game.players:
        raise HTTPException(status_code=400, detail="No players available in the heist crew")
    new_leader = game.spin_random_leader()
    await manager.broadcast({
        "type": "LEADER_SPUN",
        "leader": new_leader,
        "leader_index": game.leader_index,
        "state": game.get_public_state()
    })
    return {"status": "ok", "current_leader": new_leader, "leader_index": game.leader_index}

@app.post("/api/timer-action")
async def handle_timer_action(req: TimerActionRequest):
    act = req.action.upper()
    if act == "START":
        game.timer_running = True
        if req.seconds is not None and req.seconds > 0:
            game.timer_seconds = req.seconds
        game.timer_end_timestamp = time.time() + game.timer_seconds
    elif act == "PAUSE":
        if game.timer_running and game.timer_end_timestamp > 0:
            game.timer_seconds = max(0, int(game.timer_end_timestamp - time.time()))
        game.timer_running = False
        game.timer_end_timestamp = 0.0
    elif act == "RESET":
        game.timer_running = False
        game.timer_seconds = req.seconds if req.seconds is not None else 90
        game.timer_end_timestamp = 0.0
    game.save()
    
    await manager.broadcast({
        "type": "TIMER_UPDATE",
        "timer_seconds": game.timer_seconds,
        "timer_running": game.timer_running,
        "timer_end_timestamp": game.timer_end_timestamp,
        "state": game.get_public_state()
    })
    return {
        "status": "ok",
        "timer_seconds": game.timer_seconds,
        "timer_running": game.timer_running,
        "timer_end_timestamp": game.timer_end_timestamp
    }

@app.post("/api/reset-game")
async def reset_game(data: Dict[str, Any] = {}):
    pin = data.get("pin")
    verify_moderator_pin(pin)
    game.reset_defaults()
    game.save()
    await manager.broadcast({"type": "STATE_UPDATE", "state": game.get_public_state()})
    return {"status": "ok"}

@app.get("/api/whispers")
async def get_whatsapp_whispers(pin: Optional[str] = None):
    verify_moderator_pin(pin)
    messages = []
    for s_name in game.saboteurs:
        other_saboteurs = [x for x in game.saboteurs if x != s_name]
        msg = (
            f"🤫 *OFFICE HEIST: TOP SECRET ROLE ASSIGNMENT*\n\n"
            f"Hello {s_name}!\n"
            f"You are a secret 😈 *SABOTEUR*!\n\n"
            f"👥 Your fellow Saboteurs are: *{', '.join(other_saboteurs)}*\n\n"
            f"🎯 *Your Goal*: Make 3 missions FAIL without blowing your cover!\n"
            f"• When on a mission team, you can secretly submit *Success* (to blend in) or *Sabotage* (to fail the mission).\n"
            f"• Just 1 Sabotage is enough to fail the mission!\n"
            f"• Act completely innocent and blend in with the Resistance.\n\n"
            f"Keep this whisper strictly secret! 🤫"
        )
        messages.append({
            "player": s_name,
            "role": "SABOTEUR",
            "message": msg
        })
    return {"saboteurs": game.saboteurs, "messages": messages}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    await websocket.send_json({"type": "STATE_UPDATE", "state": game.get_public_state()})
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "PING":
                await websocket.send_json({"type": "PONG"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def get_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/play")
async def get_player_view():
    return FileResponse(os.path.join(static_dir, "player.html"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8088))
    print(f"Starting Office Heist Game Server on port {port}")
    print(f"Local URL: http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
