import unittest
from fastapi.testclient import TestClient
from server import app, game, DEFAULT_PLAYERS, MISSION_TEAM_SIZES, MODERATOR_PIN

class TestOfficeHeistGame(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.client.post("/api/reset-game", json={"pin": MODERATOR_PIN})

    def test_moderator_pin_protection(self):
        # Public request succeeds
        res_pub = self.client.get("/api/state?role=public")
        self.assertEqual(res_pub.status_code, 200)
        self.assertNotIn("saboteurs", res_pub.json())
        
        # Moderator request without PIN fails with 403
        res_no_pin = self.client.get("/api/state?role=moderator")
        self.assertEqual(res_no_pin.status_code, 403)
        
        # Moderator request with wrong PIN fails with 403
        res_bad_pin = self.client.get("/api/state?role=moderator&pin=wrong")
        self.assertEqual(res_bad_pin.status_code, 403)
        
        # Moderator request with correct PIN succeeds
        res_ok = self.client.get(f"/api/state?role=moderator&pin={MODERATOR_PIN}")
        self.assertEqual(res_ok.status_code, 200)
        self.assertIn("saboteurs", res_ok.json())

    def test_initial_setup_and_roles(self):
        setup_res = self.client.post("/api/setup", json={"players": DEFAULT_PLAYERS, "pin": MODERATOR_PIN})
        self.assertEqual(setup_res.status_code, 200)
        
        mod_state = self.client.get(f"/api/state?role=moderator&pin={MODERATOR_PIN}").json()
        self.assertEqual(mod_state["phase"], "LEADER_PROPOSAL")
        self.assertEqual(len(mod_state["saboteurs"]), 5)
        self.assertEqual(len(mod_state["resistance_members"]), len(DEFAULT_PLAYERS) - 5)
        
        # Whispers protected by PIN
        whispers = self.client.get(f"/api/whispers?pin={MODERATOR_PIN}").json()
        self.assertEqual(len(whispers["messages"]), 5)
        for w in whispers["messages"]:
            self.assertIn("SABOTEUR", w["message"])
            self.assertIn(w["player"], mod_state["saboteurs"])

    def test_team_size_validation(self):
        self.client.post("/api/setup", json={"players": DEFAULT_PLAYERS, "pin": MODERATOR_PIN})
        
        # Mission 1 requires exactly 5 players
        self.assertEqual(MISSION_TEAM_SIZES[0], 5)
        
        res4 = self.client.post("/api/propose-team", json={"team": DEFAULT_PLAYERS[:4]})
        self.assertEqual(res4.status_code, 400)
        
        res5 = self.client.post("/api/propose-team", json={"team": DEFAULT_PLAYERS[:5]})
        self.assertEqual(res5.status_code, 200)

    def test_proposal_rejection_and_rotation(self):
        self.client.post("/api/setup", json={"players": DEFAULT_PLAYERS, "pin": MODERATOR_PIN})
        leader1 = self.client.get("/api/state").json()["current_leader"]
        
        self.client.post("/api/propose-team", json={"team": DEFAULT_PLAYERS[:5]})
        
        vote_res = self.client.post("/api/resolve-proposal-vote", json={"yes_count": 8, "no_count": 14})
        self.assertEqual(vote_res.status_code, 200)
        self.assertFalse(vote_res.json()["approved"])
        
        state = self.client.get("/api/state").json()
        self.assertEqual(state["proposal_attempt"], 2)
        leader2 = state["current_leader"]
        self.assertNotEqual(leader1, leader2)

    def test_mission_success_and_failure(self):
        self.client.post("/api/setup", json={"players": DEFAULT_PLAYERS, "pin": MODERATOR_PIN})
        mod_state = self.client.get(f"/api/state?role=moderator&pin={MODERATOR_PIN}").json()
        saboteurs = set(mod_state["saboteurs"])
        resistance = [p for p in DEFAULT_PLAYERS if p not in saboteurs]
        
        # Mission 1 (pure resistance)
        team1 = resistance[:5]
        self.client.post("/api/propose-team", json={"team": team1})
        self.client.post("/api/resolve-proposal-vote", json={"yes_count": 15, "no_count": 7})
        
        for p in team1:
            self.client.post("/api/mission-action", json={"player_name": p, "action": "SUCCESS"})
            
        m1_res = self.client.post("/api/resolve-mission")
        self.assertEqual(m1_res.json()["outcome"], "SUCCESS")
        
        # Mission 2 (with 1 saboteur)
        self.client.post("/api/next-mission")
        sab1 = list(saboteurs)[0]
        team2 = resistance[:5] + [sab1]
        self.client.post("/api/propose-team", json={"team": team2})
        self.client.post("/api/resolve-proposal-vote", json={"yes_count": 14, "no_count": 8})
        
        for p in resistance[:5]:
            self.client.post("/api/mission-action", json={"player_name": p, "action": "SUCCESS"})
        self.client.post("/api/mission-action", json={"player_name": sab1, "action": "SABOTAGE"})
        
        m2_res = self.client.post("/api/resolve-mission")
        self.assertEqual(m2_res.json()["outcome"], "FAILED")

    def test_spin_leader_and_timer(self):
        self.client.post("/api/setup", json={"players": DEFAULT_PLAYERS, "pin": MODERATOR_PIN})
        
        # Test spin leader
        spin_res = self.client.post("/api/spin-leader")
        self.assertEqual(spin_res.status_code, 200)
        new_leader = spin_res.json()["current_leader"]
        self.assertIn(new_leader, DEFAULT_PLAYERS)
        
        # Test timer start
        t_start = self.client.post("/api/timer-action", json={"action": "START", "seconds": 60})
        self.assertEqual(t_start.status_code, 200)
        self.assertTrue(t_start.json()["timer_running"])
        
        # Test timer pause
        t_pause = self.client.post("/api/timer-action", json={"action": "PAUSE"})
        self.assertEqual(t_pause.status_code, 200)
        self.assertFalse(t_pause.json()["timer_running"])
        
        # Test timer reset
        t_reset = self.client.post("/api/timer-action", json={"action": "RESET", "seconds": 90})
        self.assertEqual(t_reset.status_code, 200)
        self.assertEqual(t_reset.json()["timer_seconds"], 90)

if __name__ == "__main__":
    unittest.main()
