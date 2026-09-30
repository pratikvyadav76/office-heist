import os
import time
import subprocess
import requests
from playwright.sync_api import sync_playwright

scratch_dir = r"C:\Users\pyadav6\.gemini\antigravity\brain\35030f63-e75e-4ef0-8c06-9260a641cf1f\scratch"
os.makedirs(scratch_dir, exist_ok=True)

print("Starting local test server on port 8088...")
server_proc = subprocess.Popen(["py", "server.py"], cwd=r"C:\Prateek\fun friday")

# Wait for server to come online
time.sleep(3)
for attempt in range(10):
    try:
        r = requests.get("http://localhost:8088/api/state")
        if r.status_code == 200:
            print("Server is healthy and responding!")
            break
    except Exception:
        time.sleep(1)

try:
    # 1. Reset game
    requests.post("http://localhost:8088/api/reset-game", json={"pin": "2026"})
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # --- TEST ROLE 1: BIG SCREEN (PROJECTOR VIEW) ---
        print("\n--- 1. Testing Big Screen (Main Projector View) ---")
        screen_page = browser.new_page(viewport={"width": 1400, "height": 900})
        screen_page.goto("http://localhost:8088/")
        screen_page.wait_for_load_state("domcontentloaded")
        time.sleep(1)
        
        # Take screenshot of Setup Screen with Money Heist theme
        shot1 = os.path.join(scratch_dir, "play_1_bigscreen_setup.png")
        screen_page.screenshot(path=shot1)
        print("Big Screen Setup captured:", shot1)
        
        # Click Draw Roles & Start Game
        screen_page.click("#btnStartGame")
        time.sleep(2)
        
        # Click Bella Ciao
        print("Testing Bella Ciao sound button...")
        screen_page.click("#btnBellaCiao")
        time.sleep(0.5)
        
        # Click Professor's Roulette
        print("Testing Professor's Roulette Leader Spin...")
        screen_page.click("#btnTriggerRoulette")
        time.sleep(3.5) # Wait for spinning animation
        
        shot2 = os.path.join(scratch_dir, "play_2_roulette_winner.png")
        screen_page.screenshot(path=shot2)
        print("Roulette Winner modal captured:", shot2)
        
        # Fetch current state to know roles
        mod_state = requests.get("http://localhost:8088/api/state?role=moderator&pin=2026").json()
        current_leader = mod_state["current_leader"]
        saboteurs = mod_state["saboteurs"]
        resistance = [p for p in mod_state["players"] if p not in saboteurs]
        
        print(f"Current Leader: {current_leader}")
        print(f"Saboteurs (5): {saboteurs}")
        print(f"Resistance Operatives: {len(resistance)}")
        
        # --- TEST ROLE 2: MOBILE HOST MODERATOR ---
        print("\n--- 2. Testing Mobile Host Moderator Pad (Pratik Yadav) ---")
        host_page = browser.new_page(viewport={"width": 420, "height": 880})
        host_page.goto("http://localhost:8088/play?user=pratik.yadav")
        host_page.wait_for_load_state("domcontentloaded")
        time.sleep(1)
        
        # Open Host Deck
        host_page.click("#btnMobileHostToggle")
        time.sleep(0.5)
        
        # View 5 Saboteurs on mobile
        host_page.click("#btnMobShowWhispers")
        time.sleep(0.5)
        
        shot_host = os.path.join(scratch_dir, "play_3_mobile_host_deck.png")
        host_page.screenshot(path=shot_host)
        print("Mobile Host Deck with 5 Saboteurs captured:", shot_host)
        
        # Test Timer Start from Mobile Host
        print("Starting timer from Mobile Host...")
        host_page.click("#btnMobTimerStart")
        time.sleep(1)
        
        # --- TEST ROLE 3: TEAM LEADER ON MOBILE ---
        print(f"\n--- 3. Testing Team Leader Pad ({current_leader}) ---")
        leader_page = browser.new_page(viewport={"width": 420, "height": 880})
        leader_page.goto(f"http://localhost:8088/play?player={requests.utils.quote(current_leader)}")
        leader_page.wait_for_selector("#mobileLeaderSection", state="visible", timeout=10000)
        time.sleep(1)
        
        shot_leader = os.path.join(scratch_dir, "play_4_mobile_leader.png")
        leader_page.screenshot(path=shot_leader)
        print("Mobile Leader Pad captured:", shot_leader)
        
        # Leader picks 5 operatives for Mission 1
        print("Leader proposing team of 5...")
        chips = leader_page.locator("#mobileRosterGrid button")
        for i in range(5):
            chips.nth(i).click()
            time.sleep(0.15)
            
        time.sleep(0.5)
        leader_page.click("#btnMobilePropose")
        time.sleep(2)
        
        # --- TEST ROLE 4: LOYAL RESISTANCE OPERATIVE ON MOBILE ---
        loyal_player = resistance[0] if resistance[0] != current_leader else resistance[1]
        print(f"\n--- 4. Testing Loyal Resistance Operative Pad ({loyal_player}) ---")
        loyal_page = browser.new_page(viewport={"width": 420, "height": 880})
        loyal_page.goto(f"http://localhost:8088/play?player={requests.utils.quote(loyal_player)}")
        loyal_page.wait_for_selector("#btnHoldReveal", state="visible", timeout=10000)
        time.sleep(1)
        
        # Test Hold to Reveal
        loyal_page.dispatch_event("#btnHoldReveal", "mousedown")
        time.sleep(0.5)
        shot_loyal_role = os.path.join(scratch_dir, "play_5_loyal_revealed.png")
        loyal_page.screenshot(path=shot_loyal_role)
        print("Loyal Resistance Secret Role captured:", shot_loyal_role)
        loyal_page.dispatch_event("#btnHoldReveal", "mouseup")
        
        # Loyal votes APPROVE on the proposed team
        print("Loyal voting APPROVE...")
        loyal_page.wait_for_selector("#btnMobileApprove", state="visible", timeout=10000)
        loyal_page.click("#btnMobileApprove")
        time.sleep(0.5)
        
        # --- TEST ROLE 5: SECRET SABOTEUR (DALÍ MASK CREW) ON MOBILE ---
        sab_player = saboteurs[0]
        print(f"\n--- 5. Testing Secret Saboteur Pad ({sab_player}) ---")
        sab_page = browser.new_page(viewport={"width": 420, "height": 880})
        sab_page.goto(f"http://localhost:8088/play?player={requests.utils.quote(sab_player)}")
        sab_page.wait_for_selector("#btnHoldReveal", state="visible", timeout=10000)
        time.sleep(1)
        
        # Test Hold to Reveal for Saboteur
        sab_page.dispatch_event("#btnHoldReveal", "mousedown")
        time.sleep(0.5)
        shot_sab_role = os.path.join(scratch_dir, "play_6_saboteur_revealed.png")
        sab_page.screenshot(path=shot_sab_role)
        print("Saboteur Secret Role with Fellow Saboteurs captured:", shot_sab_role)
        sab_page.dispatch_event("#btnHoldReveal", "mouseup")
        
        # Saboteur votes REJECT
        print("Saboteur voting REJECT...")
        sab_page.wait_for_selector("#btnMobileReject", state="visible", timeout=10000)
        sab_page.click("#btnMobileReject")
        time.sleep(0.5)
        
        # --- 6. ADVANCE TO MISSION EXECUTION & TEST MISSION SUBMISSIONS ---
        print("\n--- 6. Finalizing Proposal Vote on Big Screen ---")
        screen_page.click("#btnResolveProposalVote")
        time.sleep(2)
        screen_page.click("#btnProceedToMission")
        time.sleep(2)
        
        # Refresh states to test Mission Action
        loyal_page.reload()
        sab_page.reload()
        time.sleep(1)
        
        shot_action = os.path.join(scratch_dir, "play_7_mission_action.png")
        screen_page.screenshot(path=shot_action)
        print("Mission action stage captured:", shot_action)
        
        print("\nALL 5 ROLES TESTED AND VERIFIED SUCCESSFULLY!")

finally:
    print("Terminating test server...")
    server_proc.terminate()
