import os
import json
import random
import socket
import asyncio
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

MISSION_TEAM_SIZES = [5, 6, 6, 7, 7]  # Missions 1 to 5

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
        self.saboteur_count: int = 5
        self.saboteurs: List[str] = []
        self.current_mission_index: int = 0
        self.mission_results: List[Optional[str]] = [None, None, None, None, None]
        self.mission_secret_sabotages: List[int] = [0, 0, 0, 0, 0]
        self.resistance_score: int = 0
        self.saboteur_score: int = 0
        self.game_over: bool = False
        self.winner: Optional[str] = None
        
        self.phase: str = "SETUP"
        self.leader_index: int = 0
        self.proposed_team: List[str] = []
        self.proposal_attempt: int = 1
        self.max_proposal_attempts: int = 5
        
        self.proposal_votes: Dict[str, str] = {}
        self.mission_submissions: Dict[str, str] = {}
        self.timer_seconds: int = 90
        self.timer_running: bool = False
        self.history_log: List[Dict[str, Any]] = []

    def assign_roles(self, custom_saboteurs: Optional[List[str]] = None):
        if custom_saboteurs and len(custom_saboteurs) == self.saboteur_count:
            self.saboteurs = list(custom_saboteurs)
        else:
            if len(self.players) < self.saboteur_count:
                raise ValueError("Not enough players for saboteur count")
            self.saboteurs = random.sample(self.players, self.saboteur_count)
        self.phase = "LEADER_PROPOSAL"
        self.log_event("GAME_STARTED", f"Game started with {len(self.players)} players. 5 Saboteurs assigned in secret.")
        self.save()

    def get_public_state(self) -> dict:
        required_team_size = MISSION_TEAM_SIZES[self.current_mission_index] if self.current_mission_index < 5 else 0
        return {
            "phase": self.phase,
            "players": self.players,
            "player_count": len(self.players),
            "saboteur_count": self.saboteur_count,
            "resistance_count": len(self.players) - self.saboteur_count,
            "current_mission": self.current_mission_index + 1,
            "mission_team_sizes": MISSION_TEAM_SIZES,
            "required_team_size": required_team_size,
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
            "proposal_votes_cast": self.proposal_votes if self.phase in ["PROPOSAL_RESULT", "MISSION_ACTION", "MISSION_RESULT", "GAME_OVER"] else {},
            "mission_submissions_count": len(self.mission_submissions),
            "timer_seconds": self.timer_seconds,
            "timer_running": self.timer_running,
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
                    self.saboteur_count = data.get("saboteur_count", 5)
                    self.saboteurs = data.get("saboteurs", [])
                    self.current_mission_index = data.get("current_mission_index", 0)
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
    saboteurs: Optional[List[str]] = None
    pin: Optional[str] = None

class ProposeTeamRequest(BaseModel):
    team: List[str]

class ProposalVoteRequest(BaseModel):
    player_name: str
    vote: str

class ManualProposalVoteRequest(BaseModel):
    yes_count: int
    no_count: int

class MissionActionRequest(BaseModel):
    player_name: str
    action: str

class ManualMissionTallyRequest(BaseModel):
    success_count: int
    sabotage_count: int

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
    verify_moderator_pin(req.pin)
    game.players = [p.strip() for p in req.players if p.strip()]
    if len(game.players) < 5:
        raise HTTPException(status_code=400, detail="At least 5 players required")
    game.assign_roles(req.saboteurs)
    await manager.broadcast({"type": "STATE_UPDATE", "state": game.get_public_state()})
    return {"status": "ok", "state": game.get_moderator_state()}

@app.post("/api/propose-team")
async def propose_team(req: ProposeTeamRequest):
    req_size = MISSION_TEAM_SIZES[game.current_mission_index]
    if len(req.team) != req_size:
        raise HTTPException(status_code=400, detail=f"Mission {game.current_mission_index+1} requires exactly {req_size} players")
    game.proposed_team = req.team
    game.phase = "DEBATE_AND_VOTE"
    game.proposal_votes = {}
    game.timer_seconds = 90
    game.timer_running = False
    leader_name = game.players[game.leader_index]
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
        "total_players": len(game.players)
    })
    return {"status": "ok", "voted": len(game.proposal_votes)}

@app.post("/api/resolve-proposal-vote")
async def resolve_proposal_vote(manual: Optional[ManualProposalVoteRequest] = None):
    if manual:
        yes_votes = manual.yes_count
        no_votes = manual.no_count
        total_votes = yes_votes + no_votes
    else:
        yes_votes = sum(1 for v in game.proposal_votes.values() if v == "YES")
        no_votes = sum(1 for v in game.proposal_votes.values() if v == "NO")
        total_votes = len(game.proposal_votes)
        
    approved = yes_votes > (total_votes / 2.0)
    game.phase = "PROPOSAL_RESULT"
    
    leader_name = game.players[game.leader_index]
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
        "required_count": len(game.proposed_team)
    })
    return {"status": "ok", "submitted": len(game.mission_submissions), "total_needed": len(game.proposed_team)}

@app.post("/api/resolve-mission")
async def resolve_mission(manual: Optional[ManualMissionTallyRequest] = None):
    if manual:
        sabotage_count = manual.sabotage_count
        success_count = manual.success_count
    else:
        sabotage_count = sum(1 for act in game.mission_submissions.values() if act == "SABOTAGE")
        success_count = sum(1 for act in game.mission_submissions.values() if act == "SUCCESS")
        
    mission_idx = game.current_mission_index
    game.mission_secret_sabotages[mission_idx] = sabotage_count
    
    is_success = (sabotage_count == 0)
    
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
