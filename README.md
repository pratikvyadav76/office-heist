# 💼 The Resistance: Office Heist — Fun Friday Edition

A real-time, cyberpunk-themed corporate web application built for **22 Players + 3 Moderators** playing *The Resistance: Office Heist*.

---

## 🚀 How to Run the Game

### Option 1: One-Click Launcher (Recommended)
Double-click:
```
C:\Prateek\fun friday\run_game.bat
```
This automatically launches the server on port `8088` and opens the Big Screen in your browser.

### Option 2: Command Line
```powershell
cd "C:\Prateek\fun friday"
py server.py
```
Then open:
- **Projector / Big Screen**: [http://localhost:8088](http://localhost:8088)
- **Mobile Agent Pad (Phones on Wi-Fi)**: `http://<Your-IP>:8088/play` (or click **📱 Join on Mobile** on screen to scan the QR code).

---

## 🎮 Game Specifications & Setup

- **Players**: 22 Players (Pre-populated with 22 default office names, editable)
- **Teams**: 5 Secret Saboteurs, 17 Loyal Resistance
- **Win Condition**: First team to win **3 Missions**
- **5 Missions**:
  - **Mission 1**: 5 Operatives
  - **Mission 2**: 6 Operatives
  - **Mission 3**: 6 Operatives
  - **Mission 4**: 7 Operatives
  - **Mission 5**: 7 Operatives

---

## 📋 The 3 Moderator Roles

1. **Moderator 1: The Game Director (Host)**
   - Displays the Big Screen on the room TV / projector.
   - Rotates the Team Leader, calls for debate, and facilitates arguments.
2. **Moderator 2: The Secret Whisperer**
   - Clicks **🛡️ Moderator Desk** on top right.
   - Clicks **Copy Whisper** for each of the 5 Saboteurs to privately WhatsApp/Teams message them their secret identity and fellow teammates.
3. **Moderator 3: The Timekeeper & Vote Collector**
   - Controls the 90s/120s debate timer.
   - If using WhatsApp/Teams: collects private S or F messages from the mission team and enters them secretly into the manual tally.

---

## 🔄 Round Flow

1. **Leader Proposal**:
   - The rotating Team Leader selects the exact required number of operatives (e.g. 5 for Mission 1).
2. **Debate & Proposal Vote**:
   - 90-second debate countdown with warning sounds.
   - Entire room votes **Approve (Yes)** or **Reject (No)** (via show-of-hands tally or live mobile buttons).
   - If rejected: Leader token passes clockwise, proposal attempt increments (5 consecutive rejections = Saboteur victory!).
   - If approved (> 50% Yes): The heist team enters the vault!
3. **Secret Mission Action**:
   - Chosen operatives secretly choose **Success** or **Sabotage**.
   - *Loyal Resistance* must submit **Success**.
   - *Saboteurs* may submit **Success** (to blend in) or **Sabotage** (to fail the heist).
   - Can be submitted via:
     - Mobile phone client
     - Pass-the-Screen Kiosk mode (with privacy shields)
     - Moderator WhatsApp tally (one moderator receives S/F messages)
4. **Dramatic Reveal**:
   - Dramatic vault decryption sound and suspense animation.
   - **Crucial Rule**: The screen announces **ONLY** whether the mission was a **SUCCESS** or **FAILED**. It **never reveals the number of sabotages**, keeping the mystery and suspicion alive!
   - 1 or more Sabotages = Mission Fails. 0 Sabotages = Mission Succeeds.
5. **Game Over**:
   - First side to win 3 missions is crowned champion!
   - Full post-game reveal of all 5 Saboteurs and complete debate audit log.

---

## 🧪 Testing

The application includes automated unit and browser test suites:
```powershell
# Run unit test suite
py test_game.py

# Run browser UI end-to-end automation
py test_browser_ui.py
```
