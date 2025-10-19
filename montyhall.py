import streamlit as st
import random
import pandas as pd
from datetime import datetime, timedelta
import time
from github import Github

st.set_page_config(page_title="Card Game Experiment", page_icon="🏆", layout="wide")

# --- Parameters ---
max_rounds_per_block = 20
time_per_block_seconds = 10 * 60  # 10 minutes per timed block

# --- Initialize session state ---
if "player_name" not in st.session_state:
    st.session_state.player_name = None
if "trial_mode" not in st.session_state:
    st.session_state.trial_mode = None
if "experiment_rounds" not in st.session_state:
    st.session_state.experiment_rounds = 0
if "cards" not in st.session_state:
    st.session_state.cards = ["🂠"]*3
if "trophy_pos" not in st.session_state:
    st.session_state.trophy_pos = random.randint(0,2)
if "first_choice" not in st.session_state:
    st.session_state.first_choice = None
if "flipped_card" not in st.session_state:
    st.session_state.flipped_card = None
if "second_choice" not in st.session_state:
    st.session_state.second_choice = None
if "phase" not in st.session_state:
    st.session_state.phase = "first_pick"
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame(columns=["block_number","round_number","first_choice","flipped_card","second_choice","result","points","phase_type"])
if "experiment_finished" not in st.session_state:
    st.session_state.experiment_finished = False
if "logged_this_round" not in st.session_state:
    st.session_state.logged_this_round = False
if "ready_page" not in st.session_state:
    st.session_state.ready_page = False
if "current_points" not in st.session_state:
    st.session_state.current_points = 0
if "contact_info" not in st.session_state:
    st.session_state.contact_info = ""
if "blocks" not in st.session_state:
    time_block_first = random.choice([True, False])
    st.session_state.blocks = [
        {"block_number": 1, "time_pressure": time_block_first, "rounds_completed": 0},
        {"block_number": 2, "time_pressure": not time_block_first, "rounds_completed": 0}
    ]
if "current_block_index" not in st.session_state:
    st.session_state.current_block_index = 0
if "block_timer_start" not in st.session_state:
    st.session_state.block_timer_start = None

# --- Reset game ---
def reset_game():
    st.session_state.cards = ["🂠"]*3
    st.session_state.trophy_pos = random.randint(0,2)
    st.session_state.first_choice = None
    st.session_state.flipped_card = None
    st.session_state.second_choice = None
    st.session_state.phase = "first_pick"
    st.session_state.game_over = False
    st.session_state.logged_this_round = False

# --- Instructions, name, points explanation, contact info ---
if st.session_state.trial_mode is None and not st.session_state.ready_page:
    st.title("🏆 Card Game Experiment")
    st.write("""
Instructions:
You will be shown three cards and your goal is to find the trophy 🏆 behind one of them.

1️⃣ Choose a card.  
2️⃣ One of the NOT chosen cards will be revealed.  
3️⃣ Choose to stick with your first choice or switch to the other remaining card.  
The winning trophy card is then revealed!
""")

    st.subheader("🏆 Win a prize based on your points!")
    st.write("""
You have the chance to win a prize as one of the top three scorers at the end of the experiment!  

**Points system:**
- You **start with 50 points** at the beginning of the first round.  
- Every time you pick the **trophy card correctly**, you earn **100 points**.  
- If you pick the **wrong card**, you get **0 points**.
- If you **switch your card** after the reveal, **20 points are deducted**.  
- If you **stay** with your first choice, **no points are deducted**.  

💡 Points are **cumulative across rounds**. At the end, top three scorers receive:  
- 1st place: 50 CHF  
- 2nd place: 30 CHF  
- 3rd place: 20 CHF
""")

    st.subheader("📧 Contact info (optional)")
    st.write("If you want to partake in the prize drawing, please provide your email or phone number:")

    name_input = st.text_input("Enter your first and last name:", key="name_input", value=st.session_state.player_name or "")
    contact_input = st.text_input("Email or phone number:", key="contact_input", value=st.session_state.contact_info)

    col1, col2 = st.columns(2)
    if col1.button("✅ Confirm Name & Start Trial"):
        if name_input.strip() != "":
            st.session_state.player_name = name_input.strip()
            st.session_state.contact_info = contact_input.strip()
            st.session_state.trial_mode = True
            reset_game()
            st.rerun()
        else:
            st.warning("Please enter a valid name.")
    if col2.button("✅ Skip Trial & Start Experiment"):
        if name_input.strip() != "":
            st.session_state.player_name = name_input.strip()
            st.session_state.contact_info = contact_input.strip()
            st.session_state.trial_mode = False
            st.session_state.ready_page = True
            st.rerun()
        else:
            st.warning("Please enter a valid name.")
    st.stop()

# --- Phase type and current block ---
phase_type = 0 if st.session_state.trial_mode else 1
current_block = st.session_state.blocks[st.session_state.current_block_index]

# --- Ready page for timed/untimed block ---
if st.session_state.ready_page:
    st.title(f"🚀 Block {current_block['block_number']} Instructions")
    st.write(f"You will complete {max_rounds_per_block} rounds in this block.")
    if current_block["time_pressure"]:
        st.warning(f"This block has **time pressure**! You have {time_per_block_seconds//60} minutes to complete 20 rounds.")
    else:
        st.info("This block has **no time pressure**. Take your time!")

    if st.button("✅ Start Block"):
        st.session_state.ready_page = False
        if st.session_state.current_block_index == 0:
            st.session_state.current_points = 50
        if current_block["time_pressure"]:
            st.session_state.block_timer_start = datetime.now()
        reset_game()
        st.rerun()

# --- Timer display for timed block ---
if not st.session_state.trial_mode and current_block["time_pressure"] and st.session_state.block_timer_start:
    elapsed = (datetime.now() - st.session_state.block_timer_start).total_seconds()
    remaining = max(0, time_per_block_seconds - elapsed)
    minutes, seconds = divmod(int(remaining), 60)
    st.info(f"⏱ Time remaining: {minutes:02d}:{seconds:02d}")
    if remaining <= 0:
        st.error("⏰ Time's up for this block!")
        st.session_state.current_block_index += 1
        st.session_state.experiment_rounds = 0
        if st.session_state.current_block_index >= len(st.session_state.blocks):
            st.session_state.experiment_finished = True
        else:
            st.session_state.ready_page = True
        st.rerun()

# --- Determine emojis ---
def get_card_emojis():
    emojis = []
    for i in range(3):
        if st.session_state.phase == "reveal_all" or st.session_state.game_over:
            emojis.append("🏆" if i == st.session_state.trophy_pos else "❌")
        elif st.session_state.phase == "second_pick":
            emojis.append("❌" if i == st.session_state.flipped_card else "🂠")
        else:
            emojis.append("🂠")
    return emojis

# --- Display header ---
header_text = ""
if st.session_state.phase == "first_pick":
    header_text = "Pick your first card"
elif st.session_state.phase == "second_pick":
    header_text = "Pick Again (same or new card)"
elif st.session_state.phase == "reveal_all" and not st.session_state.trial_mode:
    header_text = "Reveal"

if not st.session_state.trial_mode:
    header_text = f"Block {current_block['block_number']} ({'Timed' if current_block['time_pressure'] else 'Untimed'}) - Round {st.session_state.experiment_rounds + 1}/{max_rounds_per_block}: {header_text}"

st.header(header_text)

# --- Display cards ---
cols = st.columns(3)
emojis = get_card_emojis()
for i, col in enumerate(cols):
    col.markdown(f"<h1 style='font-size:10rem; text-align:center'>{emojis[i]}</h1>", unsafe_allow_html=True)
    if not st.session_state.game_over and col.button("Pick", key=f"card_{i}", use_container_width=True):
        if st.session_state.phase == "first_pick":
            st.session_state.first_choice = i
            losing_cards = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
            st.session_state.flipped_card = random.choice(losing_cards)
            st.session_state.phase = "second_pick"
            st.rerun()
        elif st.session_state.phase == "second_pick" and i != st.session_state.flipped_card:
            st.session_state.second_choice = i
            st.session_state.phase = "reveal_all"
            st.session_state.game_over = True
            if not st.session_state.trial_mode:
                stayed = st.session_state.first_choice == st.session_state.second_choice
                won = st.session_state.second_choice == st.session_state.trophy_pos
                if not stayed:
                    st.session_state.current_points -= 20
                if won:
                    st.session_state.current_points += 100
            st.rerun()

# --- Log round ---
if st.session_state.game_over:
    won = st.session_state.second_choice == st.session_state.trophy_pos
    stayed = st.session_state.first_choice == st.session_state.second_choice

    if not st.session_state.logged_this_round:
        round_number = current_block["rounds_completed"] + 1
        points = st.session_state.current_points if not st.session_state.trial_mode else 0
        new_row = pd.DataFrame([{
            "block_number": current_block["block_number"],
            "round_number": round_number,
            "first_choice": st.session_state.first_choice,
            "flipped_card": st.session_state.flipped_card,
            "second_choice": st.session_state.second_choice,
            "result": won,
            "points": points,
            "phase_type": phase_type
        }])
        st.session_state.log_df = pd.concat([st.session_state.log_df, new_row], ignore_index=True)
        st.session_state.logged_this_round = True
        st.session_state.blocks[st.session_state.current_block_index]["rounds_completed"] += 1

# --- Show log ---
st.divider()
st.subheader("📊 Game Log")
st.dataframe(st.session_state.log_df, use_container_width=True)



