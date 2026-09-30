import os
import time
import requests
from playwright.sync_api import sync_playwright

scratch_dir = r"C:\Users\pyadav6\.gemini\antigravity\brain\35030f63-e75e-4ef0-8c06-9260a641cf1f\scratch"
os.makedirs(scratch_dir, exist_ok=True)

# 1. Reset Game to clean setup
requests.post("http://localhost:8088/api/reset-game")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    
    print("Navigating to Big Screen http://localhost:8088/ ...")
    page.goto("http://localhost:8088/")
    page.wait_for_load_state("domcontentloaded")
    time.sleep(2)
    
    # 1. Screenshot Setup Phase
    setup_shot = os.path.join(scratch_dir, "ui_1_setup.png")
    page.screenshot(path=setup_shot)
    print("Setup screenshot saved to:", setup_shot)
    
    # Click Draw Secret Roles & Start Game
    print("Clicking Draw Roles...")
    page.click("#btnStartGame")
    time.sleep(2)
    
    # 2. Screenshot Leader Proposal Phase
    proposal_shot = os.path.join(scratch_dir, "ui_2_proposal.png")
    page.screenshot(path=proposal_shot)
    print("Proposal screenshot saved to:", proposal_shot)
    
    # Select 5 operatives
    print("Selecting 5 operatives...")
    chips = page.locator("#proposalRosterGrid .player-chip")
    for i in range(5):
        chips.nth(i).click()
        time.sleep(0.15)
        
    time.sleep(1)
    # Click Confirm Proposed Team
    page.click("#btnConfirmProposal")
    time.sleep(2)
    
    # 3. Screenshot Debate & Vote Phase
    debate_shot = os.path.join(scratch_dir, "ui_3_debate.png")
    page.screenshot(path=debate_shot)
    print("Debate screenshot saved to:", debate_shot)
    
    # Finalize Vote (Approve)
    print("Finalizing Vote...")
    page.click("#btnResolveProposalVote")
    time.sleep(2)
    
    # 4. Screenshot Proposal Result
    result_shot = os.path.join(scratch_dir, "ui_4_vote_approved.png")
    page.screenshot(path=result_shot)
    print("Vote result screenshot saved to:", result_shot)
    
    # Proceed to mission execution
    page.click("#btnProceedToMission")
    time.sleep(2)
    
    # 5. Screenshot Mission Action Phase
    action_shot = os.path.join(scratch_dir, "ui_5_mission_action.png")
    page.screenshot(path=action_shot)
    print("Mission action screenshot saved to:", action_shot)
    
    # Enter 5 Successes in manual tally
    for _ in range(5):
        page.click("#btnIncManualSuccess")
        time.sleep(0.1)
        
    # Click Resolve Mission
    print("Resolving Mission (Revealing outcome)...")
    page.click("#btnResolveMission")
    time.sleep(4)
    
    # 6. Screenshot Dramatic Reveal Modal
    reveal_shot = os.path.join(scratch_dir, "ui_6_dramatic_reveal.png")
    page.screenshot(path=reveal_shot)
    print("Reveal screenshot saved to:", reveal_shot)
    
    # Close reveal modal and test next mission
    page.wait_for_selector("#btnNextMission", state="visible", timeout=10000)
    page.click("#btnNextMission")
    time.sleep(2)
    
    # Open Moderator Drawer
    print("Opening Moderator Desk...")
    page.click("#btnModToggle")
    time.sleep(1)
    
    mod_shot = os.path.join(scratch_dir, "ui_7_mod_drawer.png")
    page.screenshot(path=mod_shot)
    print("Moderator drawer screenshot saved to:", mod_shot)
    
    # Now test Mobile View
    mobile_page = browser.new_page(viewport={"width": 420, "height": 840})
    print("Navigating to Mobile View http://localhost:8088/play ...")
    mobile_page.goto("http://localhost:8088/play")
    mobile_page.wait_for_load_state("domcontentloaded")
    time.sleep(1)
    
    # Pick a player
    mobile_page.select_option("#playerSelect", index=1)
    mobile_page.click("#btnConfirmPlayer")
    time.sleep(1)
    
    mobile_shot = os.path.join(scratch_dir, "ui_8_mobile_pad.png")
    mobile_page.screenshot(path=mobile_shot)
    print("Mobile player screenshot saved to:", mobile_shot)
    
    browser.close()
    print("All browser UI tests completed successfully!")
