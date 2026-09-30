import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

output_dir = r"C:\Prateek\fun friday"

# Color Palette: Money Heist (La Casa de Papel)
COLOR_BG = RGBColor(12, 13, 17)        # Dark Slate Charcoal
COLOR_CARD = RGBColor(22, 24, 32)      # Card background
COLOR_RED = RGBColor(229, 9, 20)       # Signature Dalí Red
COLOR_CRIMSON = RGBColor(184, 29, 36)  # Dark Crimson
COLOR_GOLD = RGBColor(245, 158, 11)    # Bank Vault Gold
COLOR_CYAN = RGBColor(56, 189, 248)    # Operative Blue
COLOR_WHITE = RGBColor(248, 250, 252)  # Bright White
COLOR_MUTED = RGBColor(148, 163, 184)  # Muted Slate
COLOR_GREEN = RGBColor(16, 185, 129)   # Success Green

def set_slide_background(slide, color):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_header(slide, title_text, category_text="LA CASA DE PAPEL: OFFICE HEIST"):
    # Category tag
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.5), Inches(0.4))
    tf_cat = cat_box.text_frame
    tf_cat.word_wrap = True
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.size = Pt(11)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_GOLD
    
    # Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.5), Inches(0.9))
    tf = title_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

def add_card(slide, left, top, width, height, bg_color=COLOR_CARD, border_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(2)
    else:
        shape.line.fill.background()
    return shape

# ==========================================
# PPT 1: PLAYERS GUIDE (FOR EVERYONE)
# ==========================================
def build_players_ppt():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    
    # SLIDE 1: Title Slide
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, COLOR_BG)
    
    # Decorative Red Banner Box
    dec = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.4), Inches(7.5))
    dec.fill.solid()
    dec.fill.fore_color.rgb = COLOR_RED
    dec.line.fill.background()
    
    tb = s1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(11), Inches(3.8))
    tf = tb.text_frame
    
    p0 = tf.paragraphs[0]
    p0.text = "🎭 THE RESISTANCE: ROYAL MINT EDITION"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_GOLD
    p0.space_after = Pt(14)
    
    p1 = tf.add_paragraph()
    p1.text = "LA CASA DE PAPEL\nOFFICE HEIST"
    p1.font.size = Pt(44)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_WHITE
    p1.space_after = Pt(20)
    
    p2 = tf.add_paragraph()
    p2.text = "Corporate Fun Friday Game Guide • 28 Members (25 Operatives + 3 Host Moderators)\n\"Trust No One. Question Everyone. Secure The Vault.\""
    p2.font.size = Pt(16)
    p2.font.color.rgb = COLOR_MUTED
    
    # SLIDE 2: Two Factions
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, COLOR_BG)
    add_header(s2, "The Two Secret Factions: Who Can You Trust?")
    
    # Resistance Card (Left)
    add_card(s2, Inches(0.8), Inches(2.0), Inches(5.6), Inches(4.8), COLOR_CARD, COLOR_CYAN)
    tb_res = s2.shapes.add_textbox(Inches(1.1), Inches(2.2), Inches(5.0), Inches(4.4))
    tf_res = tb_res.text_frame
    tf_res.word_wrap = True
    
    p = tf_res.paragraphs[0]
    p.text = "🏛️ ROYAL MINT OPERATIVES"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p.space_after = Pt(12)
    
    bullets_res = [
        "Team Size: 17 Loyal Colleagues",
        "Mission: Successfully pass 3 heist missions without sabotage to crack the vault!",
        "Knowledge: You know ONLY your own identity. You have NO idea who the 5 Saboteurs are.",
        "Rule of Engagement: On missions, you MUST ALWAYS submit SUCCESS. Sabotaging is locked out.",
        "Winning Key: Observe voting patterns, track who was on failed missions, and vote down suspicious teams."
    ]
    for b in bullets_res:
        bp = tf_res.add_paragraph()
        bp.text = "• " + b
        bp.font.size = Pt(13)
        bp.font.color.rgb = COLOR_WHITE
        bp.space_after = Pt(8)
        
    # Saboteur Card (Right)
    add_card(s2, Inches(6.9), Inches(2.0), Inches(5.6), Inches(4.8), COLOR_CARD, COLOR_RED)
    tb_sab = s2.shapes.add_textbox(Inches(7.2), Inches(2.2), Inches(5.0), Inches(4.4))
    tf_sab = tb_sab.text_frame
    tf_sab.word_wrap = True
    
    p = tf_sab.paragraphs[0]
    p.text = "🎭 SECRET SABOTEURS (DALÍ CREW)"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = COLOR_RED
    p.space_after = Pt(12)
    
    bullets_sab = [
        "Team Size: Exactly 5 Secret Infiltrators",
        "Mission: Make 3 missions FAIL, OR cause 5 rejected team proposals in a row!",
        "Knowledge: You know ALL 5 fellow Saboteurs! Your phone secretly reveals their names.",
        "Rule of Engagement: On missions, you can choose SUCCESS (to blend in) or SABOTAGE (to fail it).",
        "Winning Key: Blend in, act outraged when missions fail, and frame innocent Resistance members!"
    ]
    for b in bullets_sab:
        bp = tf_sab.add_paragraph()
        bp.text = "• " + b
        bp.font.size = Pt(13)
        bp.font.color.rgb = COLOR_WHITE
        bp.space_after = Pt(8)

    # SLIDE 3: How to Connect via Phone
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, COLOR_BG)
    add_header(s3, "Your Handheld Agent Pad: Connect in 30 Seconds")
    
    steps = [
        ("Step 1: Scan QR or Open Link", "Scan the QR code projected on the main room display, or click the link shared in your Teams / WhatsApp chat (https://.../play).", COLOR_GOLD),
        ("Step 2: Pick Your Identity", "Select your name from the dropdown list. Everyone has a unique 'firstname.lastname' identity (e.g., Tanmay Indore, Riya Patil, Pratik Buge).", COLOR_CYAN),
        ("Step 3: Secret Identity Shield", "Press & hold the '👁️ HOLD TO REVEAL IDENTITY' button on your screen. Keep your phone tilted away from curious coworkers!", COLOR_RED),
        ("Step 4: Real-Time Handheld Actions", "Your phone automatically lights up when it's time to vote (Approve/Reject), debate (live timer), or submit secret heist reports!", COLOR_GREEN)
    ]
    
    for idx, (title, desc, accent) in enumerate(steps):
        top_pos = Inches(2.0 + idx * 1.25)
        add_card(s3, Inches(0.8), top_pos, Inches(11.7), Inches(1.1), COLOR_CARD, accent)
        tb_s = s3.shapes.add_textbox(Inches(1.1), top_pos + Inches(0.15), Inches(11.1), Inches(0.8))
        tf_s = tb_s.text_frame
        tf_s.word_wrap = True
        p_t = tf_s.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(16)
        p_t.font.bold = True
        p_t.font.color.rgb = accent
        p_d = tf_s.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = COLOR_WHITE

    # SLIDE 4: The 5 Missions Blueprint
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, COLOR_BG)
    add_header(s4, "The 5 Vault Missions: Crew Sizes & Stakes")
    
    mission_info = [
        ("Mission 1", "5 Operatives", "Initial Bank Infiltration", "Warm-up round. Saboteurs often lay low or strike early."),
        ("Mission 2", "6 Operatives", "Disabling Thermal Alarms", "Stakes increase. Arguments intensify."),
        ("Mission 3", "6 Operatives", "Drilling The Inner Vault", "Crucial turning point! First team to 2 points takes momentum."),
        ("Mission 4", "7 Operatives", "Cracking Gold Reserve", "Large crew. High probability of saboteur infiltration!"),
        ("Mission 5", "7 Operatives", "Helicopter Rooftop Escape", "Final showdown if tied 2-2. Winner takes all!")
    ]
    
    for idx, (m_name, m_size, m_task, m_note) in enumerate(mission_info):
        left_pos = Inches(0.8 + idx * 2.4)
        add_card(s4, left_pos, Inches(2.0), Inches(2.2), Inches(4.8), COLOR_CARD, COLOR_GOLD if idx==2 else COLOR_CRIMSON)
        tb_m = s4.shapes.add_textbox(left_pos + Inches(0.15), Inches(2.2), Inches(1.9), Inches(4.4))
        tf_m = tb_m.text_frame
        tf_m.word_wrap = True
        
        p = tf_m.paragraphs[0]
        p.text = m_name
        p.font.size = Pt(18)
        p.font.bold = True
        p.font.color.rgb = COLOR_GOLD
        p.space_after = Pt(8)
        
        p_sz = tf_m.add_paragraph()
        p_sz.text = f"👥 {m_size}"
        p_sz.font.size = Pt(20)
        p_sz.font.bold = True
        p_sz.font.color.rgb = COLOR_WHITE
        p_sz.space_after = Pt(12)
        
        p_tk = tf_m.add_paragraph()
        p_tk.text = m_task
        p_tk.font.size = Pt(13)
        p_tk.font.bold = True
        p_tk.font.color.rgb = COLOR_CYAN
        p_tk.space_after = Pt(10)
        
        p_nt = tf_m.add_paragraph()
        p_nt.text = m_note
        p_nt.font.size = Pt(11)
        p_nt.font.color.rgb = COLOR_MUTED

    # SLIDE 5: Round Flow (4 Key Steps)
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, COLOR_BG)
    add_header(s5, "Heist Mechanics: How Every Round Works")
    
    flow_steps = [
        ("1. The Professor's Roulette", "A rotating Leader is chosen. The main screen runs the Professor's Roulette wheel with ticking audio, appointing the new Team Leader!", COLOR_GOLD),
        ("2. Propose The Crew", "The Leader selects the required number of operatives on their mobile phone pad and hits 'Confirm Proposed Team'.", COLOR_CYAN),
        ("3. Debate & Interrogation", "A 90-second synchronized timer ticks on EVERY screen. The room debates: 'Why did you pick them? Can we trust this team?'", COLOR_RED),
        ("4. Vote: Approve or Reject", "All 25 operatives privately vote 👍 APPROVE or 👎 REJECT on their phones. More than 50% Yes is required to send the crew!", COLOR_GREEN)
    ]
    
    for idx, (title, desc, accent) in enumerate(flow_steps):
        top_pos = Inches(2.0 + idx * 1.25)
        add_card(s5, Inches(0.8), top_pos, Inches(11.7), Inches(1.1), COLOR_CARD, accent)
        tb_f = s5.shapes.add_textbox(Inches(1.1), top_pos + Inches(0.15), Inches(11.1), Inches(0.8))
        tf_f = tb_f.text_frame
        tf_f.word_wrap = True
        p_t = tf_f.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(16)
        p_t.font.bold = True
        p_t.font.color.rgb = accent
        p_d = tf_f.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = COLOR_WHITE

    # SLIDE 6: Rejection & The 5-Attempt Danger Track
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, COLOR_BG)
    add_header(s6, "Proposal Voting: The 5-Attempt Danger Track")
    
    add_card(s6, Inches(0.8), Inches(2.0), Inches(5.6), Inches(4.8), COLOR_CARD, COLOR_GREEN)
    tb_v1 = s6.shapes.add_textbox(Inches(1.1), Inches(2.2), Inches(5.0), Inches(4.4))
    tf_v1 = tb_v1.text_frame
    tf_v1.word_wrap = True
    p = tf_v1.paragraphs[0]
    p.text = "✅ IF TEAM IS APPROVED (> 50% YES)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_GREEN
    p.space_after = Pt(12)
    b_yes = [
        "The proposed heist crew steps into the bank vault.",
        "Proposal attempt counter resets to 1 for the next mission.",
        "Only those chosen operatives receive the secret submission prompts on their phones."
    ]
    for b in b_yes:
        bp = tf_v1.add_paragraph()
        bp.text = "• " + b
        bp.font.size = Pt(13)
        bp.font.color.rgb = COLOR_WHITE
        bp.space_after = Pt(10)
        
    add_card(s6, Inches(6.9), Inches(2.0), Inches(5.6), Inches(4.8), COLOR_CARD, COLOR_RED)
    tb_v2 = s6.shapes.add_textbox(Inches(7.2), Inches(2.2), Inches(5.0), Inches(4.4))
    tf_v2 = tb_v2.text_frame
    tf_v2.word_wrap = True
    p = tf_v2.paragraphs[0]
    p.text = "❌ IF TEAM IS REJECTED (>= 50% NO)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_RED
    p.space_after = Pt(12)
    b_no = [
        "The proposed team is turned away at the door.",
        "Leader token passes clockwise to the next player.",
        "Attempt counter increases: 1/5 ➔ 2/5 ➔ 3/5...",
        "⚠️ CRITICAL DANGER: If 5 consecutive proposals are rejected, the heist fails completely and SABOTEURS WIN AUTOMATICALLY!"
    ]
    for b in b_no:
        bp = tf_v2.add_paragraph()
        bp.text = "• " + b
        bp.font.size = Pt(13)
        bp.font.color.rgb = COLOR_WHITE
        bp.space_after = Pt(10)

    # SLIDE 7: Secret Mission Submission (1 Sabotage = Failure!)
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, COLOR_BG)
    add_header(s7, "Inside The Vault: The 1-Sabotage Golden Rule")
    
    add_card(s7, Inches(0.8), Inches(2.0), Inches(11.7), Inches(4.8), COLOR_CARD, COLOR_GOLD)
    tb_rule = s7.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(11.0), Inches(4.4))
    tf_rule = tb_rule.text_frame
    tf_rule.word_wrap = True
    
    p = tf_rule.paragraphs[0]
    p.text = "💥 THE GOLDEN RULE OF THE RESISTANCE"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = COLOR_GOLD
    p.space_after = Pt(14)
    
    gold_bullets = [
        "Just ONE Sabotage (💥) causes the entire mission to FAIL!",
        "Every operative on the mission secretly chooses their action on their phone:",
        "    - Loyal Resistance: MUST submit 'Success' (cannot sabotage).",
        "    - Saboteur: Can choose 'Success' (bluffing to gain trust) OR 'Sabotage' (striking from shadows).",
        "The Host Laptop shuffles all submissions and reveals ONLY the dramatic outcome:",
        "    - 'MISSION SUCCEEDED' or 'MISSION FAILED'.",
        "STRICT SECRECY: The system NEVER reveals who submitted which card, and never reveals how many sabotages occurred!"
    ]
    for b in gold_bullets:
        bp = tf_rule.add_paragraph()
        bp.text = b
        bp.font.size = Pt(14)
        bp.font.color.rgb = COLOR_WHITE
        bp.space_after = Pt(8)

    # SLIDE 8: Player Strategy Guide
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, COLOR_BG)
    add_header(s8, "Mastering The Heist: Tactical Bluffing Guide")
    
    add_card(s8, Inches(0.8), Inches(2.0), Inches(5.6), Inches(4.8), COLOR_CARD, COLOR_CYAN)
    tb_st1 = s8.shapes.add_textbox(Inches(1.1), Inches(2.2), Inches(5.0), Inches(4.4))
    tf_st1 = tb_st1.text_frame
    tf_st1.word_wrap = True
    p = tf_st1.paragraphs[0]
    p.text = "💡 FOR LOYAL RESISTANCE"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p.space_after = Pt(12)
    st_res = [
        "Trust the math: There are only 5 Saboteurs out of 25. Most people are honest.",
        "Track voting patterns: Who voted Yes to a team that later failed?",
        "Do not approve teams if you have doubt. You have up to 4 attempts before danger.",
        "Watch facial reactions when the vault reveal animation plays!"
    ]
    for s in st_res:
        bp = tf_st1.add_paragraph()
        bp.text = "• " + s
        bp.font.size = Pt(13)
        bp.font.color.rgb = COLOR_WHITE
        bp.space_after = Pt(10)
        
    add_card(s8, Inches(6.9), Inches(2.0), Inches(5.6), Inches(4.8), COLOR_CARD, COLOR_RED)
    tb_st2 = s8.shapes.add_textbox(Inches(7.2), Inches(2.2), Inches(5.0), Inches(4.4))
    tf_st2 = tb_st2.text_frame
    tf_st2.word_wrap = True
    p = tf_st2.paragraphs[0]
    p.text = "😈 FOR SECRET SABOTEURS"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_RED
    p.space_after = Pt(12)
    st_sab = [
        "Play the long game: Submitting 'Success' on Mission 1 earns you unshakeable trust for Missions 3 and 4.",
        "Coordinate subtly: If two Saboteurs are on a team, both sabotaging is redundant and exposes you.",
        "Act genuinely shocked: Point fingers at innocent teammates when a mission fails.",
        "Leverage the rejection track: If Resistance rejects 4 teams, force a 5th rejection to win!"
    ]
    for s in st_sab:
        bp = tf_st2.add_paragraph()
        bp.text = "• " + s
        bp.font.size = Pt(13)
        bp.font.color.rgb = COLOR_WHITE
        bp.space_after = Pt(10)

    # SLIDE 9: Corporate Ground Rules & Launch
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, COLOR_BG)
    add_header(s9, "Corporate Fun Friday Rules: Ready to Play!")
    
    add_card(s9, Inches(0.8), Inches(2.0), Inches(11.7), Inches(4.8), COLOR_CARD, COLOR_GOLD)
    tb_g = s9.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(11.0), Inches(4.4))
    tf_g = tb_g.text_frame
    tf_g.word_wrap = True
    p = tf_g.paragraphs[0]
    p.text = "🤝 FUN FRIDAY ETIQUETTE"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = COLOR_GOLD
    p.space_after = Pt(14)
    
    rules = [
        "Keep it fun and friendly: Accusations are 100% in-game roleplay!",
        "Strict phone privacy: Never peek at a neighbor's screen or snatch their phone.",
        "No elimination: Everyone plays all 5 missions until the very end!",
        "Respect the 90s timer: When time expires, debate halts and votes are counted.",
        "Grab your phone, scan the QR code on the big screen, and prepare for the heist!"
    ]
    for r in rules:
        bp = tf_g.add_paragraph()
        bp.text = "✓ " + r
        bp.font.size = Pt(15)
        bp.font.color.rgb = COLOR_WHITE
        bp.space_after = Pt(12)

    prs.save(os.path.join(output_dir, "Office_Heist_Players_Guide.pptx"))
    print("Players Guide PPTX generated successfully!")

# ==========================================
# PPT 2: HOST MASTER GUIDE (FOR 3 MODERATORS)
# ==========================================
def build_hosts_ppt():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    
    # SLIDE 1: Title Slide
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, COLOR_BG)
    
    dec = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.4), Inches(7.5))
    dec.fill.solid()
    dec.fill.fore_color.rgb = COLOR_GOLD
    dec.line.fill.background()
    
    tb = s1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(11), Inches(3.8))
    tf = tb.text_frame
    
    p0 = tf.paragraphs[0]
    p0.text = "🔒 STRICTLY CONFIDENTIAL • FOR MODERATORS ONLY"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_RED
    p0.space_after = Pt(14)
    
    p1 = tf.add_paragraph()
    p1.text = "THE PROFESSOR'S PLAYBOOK\nHOST MASTER GUIDE"
    p1.font.size = Pt(44)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_GOLD
    p1.space_after = Pt(20)
    
    p2 = tf.add_paragraph()
    p2.text = "Behind-The-Scenes Operational Manual for Pratik Yadav, Om Naik & Vighnesh Jadhav\nModerator Desk Access PIN: 2026"
    p2.font.size = Pt(16)
    p2.font.color.rgb = COLOR_MUTED

    # SLIDE 2: 3-Host Division of Labor
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, COLOR_BG)
    add_header(s2, "Moderator Roles: 3-Way Division of Labor", "CONFIDENTIAL HOST GUIDE")
    
    hosts = [
        ("1. Pratik Yadav", "Lead Host & Master of Ceremonies", [
            "Operates the main laptop / conference room TV.",
            "Triggers the Professor's Roulette wheel for leader selection.",
            "Plays the synthesized Bella Ciao theme and hypes up the room.",
            "Calls for votes and announces vault results with drama!"
        ], COLOR_GOLD),
        ("2. Om Naik", "Secret Whisperer & Secrecy Guard", [
            "Accesses the 5 Saboteurs list inside the Moderator Desk.",
            "Monitors the room to ensure no one peeks over phones.",
            "Sends private WhatsApp/Teams whispers if any player needs verification.",
            "Confirms all Saboteurs understand their role and teammates."
        ], COLOR_RED),
        ("3. Vighnesh Jadhav", "Pacer, Timekeeper & Backup Officer", [
            "Operates the synchronized debate timer (Start/Pause/Reset).",
            "Monitors live vote incoming count on phone.",
            "Enforces the 90s discussion limit ('Time is up, cast your votes!').",
            "Assists anyone whose phone disconnects using Kiosk mode."
        ], COLOR_CYAN)
    ]
    
    for idx, (name, role, tasks, accent) in enumerate(hosts):
        left_pos = Inches(0.8 + idx * 4.0)
        add_card(s2, left_pos, Inches(2.0), Inches(3.7), Inches(4.8), COLOR_CARD, accent)
        tb_h = s2.shapes.add_textbox(left_pos + Inches(0.15), Inches(2.2), Inches(3.4), Inches(4.4))
        tf_h = tb_h.text_frame
        tf_h.word_wrap = True
        
        p = tf_h.paragraphs[0]
        p.text = name
        p.font.size = Pt(18)
        p.font.bold = True
        p.font.color.rgb = accent
        
        p_r = tf_h.add_paragraph()
        p_r.text = role
        p_r.font.size = Pt(12)
        p_r.font.bold = True
        p_r.font.color.rgb = COLOR_WHITE
        p_r.space_after = Pt(12)
        
        for t in tasks:
            pt = tf_h.add_paragraph()
            pt.text = "• " + t
            pt.font.size = Pt(11)
            pt.font.color.rgb = COLOR_MUTED
            pt.space_after = Pt(6)

    # SLIDE 3: System Architecture & PIN Security
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, COLOR_BG)
    add_header(s3, "Architecture & Access Security: PIN 2026", "CONFIDENTIAL HOST GUIDE")
    
    add_card(s3, Inches(0.8), Inches(2.0), Inches(5.6), Inches(4.8), COLOR_CARD, COLOR_GOLD)
    tb_sec1 = s3.shapes.add_textbox(Inches(1.1), Inches(2.2), Inches(5.0), Inches(4.4))
    tf_sec1 = tb_sec1.text_frame
    tf_sec1.word_wrap = True
    p = tf_sec1.paragraphs[0]
    p.text = "💻 LAPTOP MODERATOR DESK"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_GOLD
    p.space_after = Pt(12)
    sec_laptop = [
        "Location: Top navigation bar on big screen ('🛡️ Moderator Desk').",
        "Protected by PIN: 2026.",
        "Reveals the 5 Secret Saboteurs with 1-click 'Copy Whisper' buttons.",
        "Displays full game history log with timestamped event records.",
        "Provides manual override buttons: Force Leader Rotate & Full Game Reset."
    ]
    for b in sec_laptop:
        bp = tf_sec1.add_paragraph()
        bp.text = "• " + b
        bp.font.size = Pt(13)
        bp.font.color.rgb = COLOR_WHITE
        bp.space_after = Pt(8)
        
    add_card(s3, Inches(6.9), Inches(2.0), Inches(5.6), Inches(4.8), COLOR_CARD, COLOR_RED)
    tb_sec2 = s3.shapes.add_textbox(Inches(7.2), Inches(2.2), Inches(5.0), Inches(4.4))
    tf_sec2 = tb_sec2.text_frame
    tf_sec2.word_wrap = True
    p = tf_sec2.paragraphs[0]
    p.text = "📱 MOBILE HOST CONTROL DECK"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_RED
    p.space_after = Pt(12)
    sec_mob = [
        "Location: Top right corner on your phone pad ('🛡️ Host').",
        "Direct Access: Auto-unlocked for pratik.yadav, om.naik, and vighnesh.jadhav (or via PIN 2026).",
        "One-Tap Actions from anywhere in the room:",
        "    - 🎲 Spin Leader (Triggers roulette on big screen)",
        "    - ▶ Start Timer / ⏸ Pause Timer",
        "    - ✓ Force Approve / ✕ Force Reject",
        "    - ⏩ Next Mission / 😈 5 Saboteurs list"
    ]
    for b in sec_mob:
        bp = tf_sec2.add_paragraph()
        bp.text = "• " + b
        bp.font.size = Pt(13)
        bp.font.color.rgb = COLOR_WHITE
        bp.space_after = Pt(6)

    # SLIDE 4: The Whisper Protocol
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, COLOR_BG)
    add_header(s4, "The Secret Whisper Protocol: Managing Saboteurs", "CONFIDENTIAL HOST GUIDE")
    
    add_card(s4, Inches(0.8), Inches(2.0), Inches(11.7), Inches(4.8), COLOR_CARD, COLOR_RED)
    tb_wh = s4.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(11.0), Inches(4.4))
    tf_wh = tb_wh.text_frame
    tf_wh.word_wrap = True
    p = tf_wh.paragraphs[0]
    p.text = "🤫 WHATSAPP / MS TEAMS BACKUP PROTOCOL"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = COLOR_RED
    p.space_after = Pt(12)
    
    wh_pts = [
        "While players see their role on their phone pad, Om Naik should verify the 5 Saboteurs immediately after clicking 'Draw Secret Roles'.",
        "Each saboteur card in the Moderator Desk has pre-formatted whisper text ready to copy:",
        "    '🤫 OFFICE HEIST: TOP SECRET ROLE ASSIGNMENT\n    Hello [Name]! You are a secret 😈 SABOTEUR!\n    Your fellow Saboteurs are: [Names]\n    Goal: Make 3 missions FAIL without blowing cover!'",
        "Why this matters: In a bustling room, having Om whisper them confirms they know their fellow teammates even if they accidentally glanced away from their phone.",
        "Zero Information Leaks: Never look at a specific player while whispering; send all 5 quietly from your phone/laptop."
    ]
    for w in wh_pts:
        bp = tf_wh.add_paragraph()
        bp.text = "• " + w
        bp.font.size = Pt(13)
        bp.font.color.rgb = COLOR_WHITE
        bp.space_after = Pt(8)

    # SLIDE 5: Facilitation Playbook: Stage by Stage
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, COLOR_BG)
    add_header(s5, "Facilitator Playbook: Step-by-Step Operations", "CONFIDENTIAL HOST GUIDE")
    
    playbook = [
        ("Launch (00:00)", "Pratik opens the big screen on the room projector. Clicks '📱 Join on Mobile' or uses '📋 Copy Link' to post in Teams. Tells everyone to connect.", COLOR_GOLD),
        ("Role Draw", "Click '🚀 Draw Secret Roles & Start Game'. Remind room: 'Hold your thumb to reveal your identity. Keep screens hidden!'", COLOR_CYAN),
        ("Leader Roulette", "Click '🎲 Professor's Roulette'. Build tension as the wheel spins through names and locks onto the Leader with a chime!", COLOR_RED),
        ("Debate Control", "Leader proposes 5 operatives. Vighnesh hits '▶ Start Timer' (90s). Pratik asks: 'Why is Tanmay on this team? Does anyone object?'", COLOR_GOLD),
        ("Vote & Vault", "When timer hits 0, call for votes. If approved, chosen crew secretly submits on phones. Click 'Reveal Mission Outcome'!", COLOR_GREEN)
    ]
    for idx, (title, desc, accent) in enumerate(playbook):
        top_pos = Inches(2.0 + idx * 1.05)
        add_card(s5, Inches(0.8), top_pos, Inches(11.7), Inches(0.95), COLOR_CARD, accent)
        tb_p = s5.shapes.add_textbox(Inches(1.1), top_pos + Inches(0.12), Inches(11.1), Inches(0.7))
        tf_p = tb_p.text_frame
        tf_p.word_wrap = True
        p_t = tf_p.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(15)
        p_t.font.bold = True
        p_t.font.color.rgb = accent
        p_d = tf_p.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(11)
        p_d.font.color.rgb = COLOR_WHITE

    # SLIDE 6: Fail-Safes & Edge Case Handling
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, COLOR_BG)
    add_header(s6, "Emergency Protocols: What If Scenarios", "CONFIDENTIAL HOST GUIDE")
    
    failsafes = [
        ("Phone Disconnects / Battery Dies", "Use the built-in 'Pass-the-Screen Kiosk' on the host laptop. The operative steps up to the laptop, selects their name, and votes privately behind the privacy shield.", COLOR_GOLD),
        ("Someone Misses the Vote", "You can manually adjust the Yes/No count using the '+ / -' tally buttons on the Big Screen or tap 'Force Approve / Force Reject' on your Mobile Host Deck.", COLOR_CYAN),
        ("Room Won't Stop Arguing", "Vighnesh calls time: 'Timer is at zero! 5 seconds to submit phone votes: 5, 4, 3, 2, 1—Locked!'", COLOR_RED),
        ("Game Accidental Tab Close", "State is auto-saved to disk (game_state.json). Simply reload the browser; the game restores instantly without losing scores or roles.", COLOR_GREEN)
    ]
    for idx, (title, desc, accent) in enumerate(failsafes):
        top_pos = Inches(2.0 + idx * 1.25)
        add_card(s6, Inches(0.8), top_pos, Inches(11.7), Inches(1.1), COLOR_CARD, accent)
        tb_fs = s6.shapes.add_textbox(Inches(1.1), top_pos + Inches(0.15), Inches(11.1), Inches(0.8))
        tf_fs = tb_fs.text_frame
        tf_fs.word_wrap = True
        p_t = tf_fs.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(16)
        p_t.font.bold = True
        p_t.font.color.rgb = accent
        p_d = tf_fs.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = COLOR_WHITE

    # SLIDE 7: Event Timeline & Pacing Masterplan
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, COLOR_BG)
    add_header(s7, "Master Timeline: 35-45 Minute Fun Friday Schedule", "CONFIDENTIAL HOST GUIDE")
    
    schedule = [
        ("00:00 - 05:00", "Arrival & QR Join", "Show PPT 1, ensure all 25 players connect on phones, test sound."),
        ("05:00 - 12:00", "Mission 1 (5 Players)", "Role assignment, leader roulette, quick debate, first vault reveal."),
        ("12:00 - 20:00", "Mission 2 (6 Players)", "Paranoia begins. Accusations start flying."),
        ("20:00 - 28:00", "Mission 3 (6 Players)", "High drama! Potential 2-1 or 2-0 point lead."),
        ("28:00 - 36:00", "Mission 4 (7 Players)", "Near climax. Rejection track tension peaks."),
        ("36:00 - 42:00", "Mission 5 / Endgame", "Match point! Play Bella Ciao upon victory announcement!"),
        ("42:00 - 45:00", "Debrief & MVP Awards", "Saboteurs reveal themselves, best bluffs celebrated.")
    ]
    for idx, (time_slot, phase_name, detail) in enumerate(schedule):
        top_pos = Inches(2.0 + idx * 0.72)
        add_card(s7, Inches(0.8), top_pos, Inches(11.7), Inches(0.65), COLOR_CARD, COLOR_GOLD if idx==5 else None)
        tb_sc = s7.shapes.add_textbox(Inches(1.1), top_pos + Inches(0.08), Inches(11.1), Inches(0.5))
        tf_sc = tb_sc.text_frame
        tf_sc.word_wrap = True
        p = tf_sc.paragraphs[0]
        p.text = f"{time_slot}  |  {phase_name.upper()}  —  {detail}"
        p.font.size = Pt(12)
        p.font.bold = (idx == 5)
        p.font.color.rgb = COLOR_GOLD if idx == 5 else COLOR_WHITE

    prs.save(os.path.join(output_dir, "Office_Heist_Host_Master_Guide.pptx"))
    print("Host Master Guide PPTX generated successfully!")

if __name__ == "__main__":
    build_players_ppt()
    build_hosts_ppt()
