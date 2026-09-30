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

    def test_absentee_player_removal_and_dynamic_scaling(self):
        # Suppose 4 players are absent, so only 21 players
        reduced_players = DEFAULT_PLAYERS[:18]
        setup_res = self.client.post("/api/setup", json={"players": reduced_players, "pin": MODERATOR_PIN})
        self.assertEqual(setup_res.status_code, 200)
        
        state = self.client.get("/api/state").json()
        self.assertEqual(state["player_count"], 18)
        self.assertEqual(state["saboteur_count"], 5)
        self.assertEqual(len(state["missions"]), 5)

    def test_pure_mobile_proposal_voting_resolution(self):
        self.client.post("/api/setup", json={"players": DEFAULT_PLAYERS, "pin": MODERATOR_PIN})
        self.client.post("/api/propose-team", json={"team": DEFAULT_PLAYERS[:5]})
        
        # 12 players vote YES on mobile, 4 vote NO
        for p in DEFAULT_PLAYERS[:12]:
            self.client.post("/api/proposal-vote", json={"player_name": p, "vote": "YES"})
        for p in DEFAULT_PLAYERS[12:16]:
            self.client.post("/api/proposal-vote", json={"player_name": p, "vote": "NO"})
            
        state = self.client.get("/api/state").json()
        self.assertEqual(state["proposal_votes_count"], 16)
        self.assertIn(DEFAULT_PLAYERS[0], state["proposal_voted_players"])
        
        # Resolve without manual override
        res = self.client.post("/api/resolve-proposal-vote")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["approved"])
        self.assertEqual(res.json()["yes_votes"], 12)
        self.assertEqual(res.json()["no_votes"], 4)

    def test_custom_missions_configuration(self):
        self.client.post("/api/setup", json={"players": DEFAULT_PLAYERS, "pin": MODERATOR_PIN})
        
        custom_missions = [
            {"index": 1, "title": "Custom M1", "story": "Story 1", "team_size": 4, "fails_required": 1},
            {"index": 2, "title": "Custom M2", "story": "Story 2", "team_size": 5, "fails_required": 1},
            {"index": 3, "title": "Custom M3", "story": "Story 3", "team_size": 5, "fails_required": 1},
            {"index": 4, "title": "Custom M4", "story": "Story 4", "team_size": 6, "fails_required": 2},
            {"index": 5, "title": "Custom M5", "story": "Story 5", "team_size": 6, "fails_required": 1},
        ]
        
        c_res = self.client.post("/api/customize-missions", json={"missions": custom_missions, "pin": MODERATOR_PIN})
        self.assertEqual(c_res.status_code, 200)
        
        state = self.client.get("/api/state").json()
        self.assertEqual(state["missions"][0]["title"], "Custom M1")
        self.assertEqual(state["mission_team_sizes"], [4, 5, 5, 6, 6])
        self.assertEqual(state["required_team_size"], 4)

    def test_excluded_saboteurs_protection(self):
        excluded_names = [
            "bhishma", "puja", "niki", "pratik buge", "saket", 
            "sonakshi", "tanmay", "pratik morale", "smeet"
        ]
        
        # Run 50 random assignments to statistically guarantee exclusion
        for _ in range(50):
            self.client.post("/api/setup", json={"players": DEFAULT_PLAYERS, "pin": MODERATOR_PIN})
            mod_state = self.client.get(f"/api/state?role=moderator&pin={MODERATOR_PIN}").json()
            saboteurs = mod_state["saboteurs"]
            
            # Ensure exactly 5 saboteurs are selected
            self.assertEqual(len(saboteurs), 5)
            
            # Check that NONE of the excluded names are in saboteurs
            for s in saboteurs:
                s_lower = s.lower()
                for exc in excluded_names:
                    self.assertNotIn(exc, s_lower, f"Violated rule: {s} matched excluded name '{exc}'!")
                    
            # Ensure all excluded names are in resistance members
            resistance = " ".join(mod_state["resistance_members"]).lower()
            for exc in excluded_names:
                self.assertIn(exc, resistance, f"Excluded player '{exc}' was missing from Resistance!")

    def test_reset_game_endpoint(self):
        # Start game
        self.client.post("/api/setup", json={"players": DEFAULT_PLAYERS, "pin": MODERATOR_PIN})
        state = self.client.get("/api/state").json()
        self.assertEqual(state["phase"], "LEADER_PROPOSAL")
        
        # Reset without pin (smooth UI reset)
        res_no_pin = self.client.post("/api/reset-game")
        self.assertEqual(res_no_pin.status_code, 200)
        state_after = self.client.get("/api/state").json()
        self.assertEqual(state_after["phase"], "SETUP")
        self.assertEqual(len(state_after["players"]), len(DEFAULT_PLAYERS))
        
        # Reset with wrong pin should fail with 403
        res_bad = self.client.post("/api/reset-game", json={"pin": "wrong"})
        self.assertEqual(res_bad.status_code, 403)
        
        # Reset with correct pin succeeds
        res_ok = self.client.post("/api/reset-game", json={"pin": MODERATOR_PIN})
        self.assertEqual(res_ok.status_code, 200)
        self.assertEqual(res_ok.json()["state"]["phase"], "SETUP")

    def test_single_device_login_and_claim(self):
        player = DEFAULT_PLAYERS[0]
        dev_a = "device_phone_A_123"
        dev_b = "device_phone_B_456"

        # Device A claims player
        res_a = self.client.post("/api/claim-player", json={"player_name": player, "device_id": dev_a})
        self.assertEqual(res_a.status_code, 200)

        # Device A re-claiming (refreshing) succeeds
        res_a_refresh = self.client.post("/api/claim-player", json={"player_name": player, "device_id": dev_a})
        self.assertEqual(res_a_refresh.status_code, 200)

        # Device B trying to claim same player is REJECTED with 409 Conflict
        res_b = self.client.post("/api/claim-player", json={"player_name": player, "device_id": dev_b})
        self.assertEqual(res_b.status_code, 409)
        self.assertIn("already logged in on another device", res_b.json()["detail"])

        # State reports claimed player
        state = self.client.get("/api/state").json()
        self.assertIn(player, state["claimed_players"])

        # Release from Device A
        res_rel = self.client.post("/api/release-player", json={"player_name": player, "device_id": dev_a})
        self.assertEqual(res_rel.status_code, 200)

        # Now Device B can claim
        res_b_now = self.client.post("/api/claim-player", json={"player_name": player, "device_id": dev_b})
        self.assertEqual(res_b_now.status_code, 200)

        # Release all devices
        res_rel_all = self.client.post("/api/release-all-devices")
        self.assertEqual(res_rel_all.status_code, 200)
        self.assertEqual(len(self.client.get("/api/state").json()["claimed_players"]), 0)

if __name__ == "__main__":
    unittest.main()
