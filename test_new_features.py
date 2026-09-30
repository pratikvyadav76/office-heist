import os
import time
import subprocess
import requests
from playwright.sync_api import sync_playwright

print("Starting test server...")
server_proc = subprocess.Popen(["py", "server.py"], cwd=r"C:\Prateek\fun friday")

time.sleep(3)
for attempt in range(10):
    try:
        r = requests.get("http://localhost:8088/api/state")
        if r.status_code == 200:
            print("Server is online!")
            break
    except Exception:
        time.sleep(1)

try:
    requests.post("http://localhost:8088/api/reset-game", json={"pin": "2026"})
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto("http://localhost:8088/")
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1)
        
        print("1. Testing Setup Screen and Absentee Removal...")
        # Check initial count
        initial_count = page.locator("#setupPlayerCount").inner_text()
        print(f"Initial setup count: {initial_count}")
        assert initial_count == "28", f"Expected 28, got {initial_count}"
        
        # Click remove on the first chip
        first_chip = page.locator(".player-chip").first
        first_chip_name = first_chip.locator(".chip-name").inner_text()
        print(f"Removing absent player: {first_chip_name}")
        first_chip.locator(".chip-remove-btn").click()
        time.sleep(0.5)
        
        # Verify count decreased
        new_count = page.locator("#setupPlayerCount").inner_text()
        absent_count = page.locator("#setupAbsentCount").inner_text()
        print(f"New count: {new_count}, Absent count: {absent_count}")
        assert new_count == "27", f"Expected 27, got {new_count}"
        assert absent_count == "1", f"Expected 1, got {absent_count}"
        
        # Verify absent tray has the player and restore works
        assert page.locator("#setupAbsentSection").is_visible(), "Absent tray should be visible"
        print("Restoring absent player...")
        page.locator(".absent-chip-restore").first.click()
        time.sleep(0.5)
        restored_count = page.locator("#setupPlayerCount").inner_text()
        assert restored_count == "28", f"Expected restored count 28, got {restored_count}"
        print("Absentee removal and restore passed!")
        
        print("\n2. Testing Moderator Control Room Open & Close...")
        # Click Moderator Desk button
        page.click("#btnModToggle")
        time.sleep(0.5)
        
        # Enter PIN
        page.fill("#inputModPin", "2026")
        page.click("#btnSubmitPin")
        time.sleep(0.5)
        
        # Verify drawer is open
        drawer = page.locator("#modDrawer")
        assert "open" in drawer.get_attribute("class"), "modDrawer should have class 'open'"
        print("Moderator Control Room successfully opened!")
        
        # Verify whispers list is gone and secret dossier is present
        assert page.locator("#modSaboteursList").count() > 0, "modSaboteursList should be present"
        assert page.locator("#modWhispersList").count() == 0, "modWhispersList should be completely removed"
        print("Whisper clutter removed and confidential dossier verified!")
        
        # Click close button (✕)
        print("Clicking close button (#btnCloseMod)...")
        page.click("#btnCloseMod")
        time.sleep(0.5)
        assert "open" not in drawer.get_attribute("class"), "modDrawer should be closed after clicking close button"
        print("Moderator Control Room close button [X] works perfectly!")
        
        # Re-open and test backdrop click to close
        page.click("#btnModToggle")
        time.sleep(0.5)
        assert "open" in drawer.get_attribute("class"), "modDrawer should re-open"
        page.click("#modDrawerBackdrop", position={"x": 50, "y": 50})
        time.sleep(0.5)
        assert "open" not in drawer.get_attribute("class"), "modDrawer should close on backdrop click"
        print("Backdrop click to close works perfectly!")
        
        print("\n3. Testing Game Start & Pure Mobile Voting UI...")
        page.click("#btnStartGame")
        time.sleep(1.5)
        
        # Now in LEADER_PROPOSAL
        # Select 5 players from proposal grid
        chips = page.locator("#proposalRosterGrid .player-chip")
        for i in range(5):
            chips.nth(i).click()
            time.sleep(0.1)
            
        page.click("#btnConfirmProposal")
        time.sleep(1.5)
        
        # Now in DEBATE_AND_VOTE phase
        assert page.locator("#phaseDebate").is_visible(), "Debate phase should be visible"
        # Verify NO manual counter buttons are showing in main view
        assert page.locator(".tally-inputs").count() == 0, "Manual tally inputs should be completely removed"
        
        # Verify Live Mobile Room Ballot is present
        assert page.locator(".ballot-progress-track").is_visible(), "Ballot progress track should be visible"
        assert page.locator("#ballotVotersGrid").is_visible(), "Voters grid should be visible"
        
        # Check initial voter chips (all waiting)
        waiting_chips = page.locator(".voter-chip.waiting")
        print(f"Initial waiting voters count: {waiting_chips.count()}")
        assert waiting_chips.count() == 28, f"Expected 28 waiting voters, got {waiting_chips.count()}"
        
        # Simulate mobile votes via API
        state = requests.get("http://localhost:8088/api/state").json()
        players = state["players"]
        for p in players[:15]:
            requests.post("http://localhost:8088/api/proposal-vote", json={"player_name": p, "vote": "YES"})
        for p in players[15:20]:
            requests.post("http://localhost:8088/api/proposal-vote", json={"player_name": p, "vote": "NO"})
            
        time.sleep(1)
        
        # Verify voters grid updated live
        voted_chips = page.locator(".voter-chip.voted")
        print(f"Updated voted chips count: {voted_chips.count()}")
        assert voted_chips.count() == 20, f"Expected 20 voted chips, got {voted_chips.count()}"
        
        # Click Reveal Mobile Ballots & Announce Result
        print("Clicking Reveal Mobile Ballots...")
        page.click("#btnResolveProposalVote")
        time.sleep(1)
        
        # Verify proposal approved banner shows mobile ballot result
        assert page.locator("#phaseProposalResult").is_visible(), "Proposal result should be visible"
        details_text = page.locator("#proposalResultDetails").inner_text()
        print(f"Result details text: {details_text}")
        assert "15 Approved vs 5 Rejected by mobile ballot" in details_text, f"Unexpected details: {details_text}"
        print("Pure mobile proposal voting and announcement passed!")
        
        print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")
        browser.close()
finally:
    server_proc.terminate()
