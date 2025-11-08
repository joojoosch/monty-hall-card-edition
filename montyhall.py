import streamlit as st
import random
import pandas as pd
from datetime import datetime
from github import Github

st.set_page_config(page_title="Card Game Experiment", page_icon="🏆", layout="wide")

trial_runs_required = 10
max_experiment_rounds = 6  # 2 rounds × 3 trials each

# --- Initialize session state ---
if "player_name" not in st.session_state:
    st.session_state.player_name = None
if "page" not in st.session_state:
    st.session_state.page = "instructions"
if "trial_runs_done" not in st.session_state:
    st.session_state.trial_runs_done = 0
if "trial_log" not in st.session_state:
    st.session_state.trial_log = pd.DataFrame(columns=["trial_number","first_choice","flipped_card","second_choice","trophy_card","result","switch_win","stay_win"])
if "experiment_round" not in st.session_state:
    st.session_state.experiment_round = 0
if "current_round_set" not in st.session_state:
    st.session_state.current_round_set = 1
if "experiment_log" not in st.session_state:
    st.session_state.experiment_log = pd.DataFrame(columns=["round_number","first_choice","flipped_card","second_choice","trophy_card","result","phase_type","points_after_round","switch_win","stay_win"])
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
if "points" not in st.session_state:
    st.session_state.points = 50  # start points
if "logged_this_round" not in st.session_state:
    st.session_state.logged_this_round = False

# --- Reset game function ---
def reset_game():
    st.session_state.cards = ["🂠"]*3
    st.session_state.trophy_pos = random.randint(0,2)
    st.session_state.first_choice = None
    st.session_state.flipped_card = None
    st.session_state.second_choice = None
    st.session_state.phase = "first_pick"
    st.session_state.game_over = False
    st.session_state.logged_this_round = False

# --- Helper to get card emojis ---
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

# --- Helper to count switch/stay wins ---
def compute_switch_stay(first, second, trophy):
    if second == trophy:
        if first == second:
            return 0,1  # stay_win
        else:
            return 1,0  # switch_win
    else:
        return 0,0

# ---------------- PAGE: Instructions + Name ----------------
if st.session_state.page == "instructions":
    st.title("🏆 Card Game Experiment")
    st.write("""
You will be shown three cards and your goal is to find the trophy 🏆 behind one of them.

1️⃣ Choose a card.  
2️⃣ One of the NOT chosen cards will be revealed.  
3️⃣ Choose to stick with your first choice or switch to the other remaining card.  
The winning trophy card is then revealed!
""")
    if st.session_state.player_name is None:
        name_input = st.text_input("Enter your first and last name:", key="name_input")
        if st.button("✅ Confirm Name"):
            if name_input.strip() != "":
                st.session_state.player_name = name_input.strip()
                st.session_state.page = "trial"
                reset_game()
                st.rerun()
            else:
                st.warning("Please enter a valid name.")
        st.stop()

# ---------------- PAGE: Trial Runs ----------------
if st.session_state.page == "trial":
    st.title("🔁 Trial Runs (Practice)")
    if st.session_state.phase=="first_pick":
        st.subheader("Pick your first card")
    elif st.session_state.phase=="second_pick":
        st.subheader("Pick Again (same or switch)")
    st.write(f"Trial runs completed: **{st.session_state.trial_runs_done}/{trial_runs_required}**")
    if st.session_state.game_over and st.button("Next"):
        reset_game()
        st.rerun()

# ---------------- TRIAL / EXPERIMENT CARD LOGIC ----------------
if st.session_state.page in ["trial","round1","round2"]:
    cols = st.columns(3)
    emojis = get_card_emojis()
    for i,col in enumerate(cols):
        col.markdown(f"<h1 style='font-size:10rem; text-align:center'>{emojis[i]}</h1>", unsafe_allow_html=True)
        if not st.session_state.game_over and col.button("Pick", key=f"card_{i}", use_container_width=True):
            if st.session_state.phase == "first_pick":
                st.session_state.first_choice = i
                losing_cards = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
                st.session_state.flipped_card = random.choice(losing_cards)
                st.session_state.phase = "second_pick"
                st.rerun()
            elif st.session_state.phase == "second_pick" and i != st.session_state.flipped_card:
                staying = i == st.session_state.first_choice
                cost = 0
                if st.session_state.page != "trial":
                    if st.session_state.current_round_set == 1 and not staying:
                        cost = 10
                    elif st.session_state.current_round_set == 2 and staying:
                        cost = 10
                    if st.session_state.points < cost:
                        st.warning("⚠️ You don’t have enough points for this action!")
                        st.stop()
                    st.session_state.points -= cost
                st.session_state.second_choice = i
                st.session_state.phase = "reveal_all"
                st.session_state.game_over = True
                st.rerun()

# ---------------- DISPLAY RESULTS ----------------
if st.session_state.game_over:
    first = st.session_state.first_choice
    second = st.session_state.second_choice
    trophy = st.session_state.trophy_pos
    won = second == trophy
    stayed = first == second
    switch_win, stay_win = compute_switch_stay(first, second, trophy)

    if st.session_state.page == "trial":
        if won:
            st.success("🎉 You found the correct card!")
        else:
            st.error("❌ You picked the wrong card.")
            if first == trophy and second != trophy:
                st.info("💡 You should have stayed to win.")
            elif first != trophy and second != trophy:
                st.info("💡 You should have switched to win.")
        if not st.session_state.logged_this_round:
            trial_number = st.session_state.trial_runs_done + 1
            new_row = pd.DataFrame([{
                "trial_number": trial_number,
                "first_choice": first,
                "flipped_card": st.session_state.flipped_card,
                "second_choice": second,
                "trophy_card": trophy,
                "result": won,
                "switch_win": switch_win,
                "stay_win": stay_win
            }])
            st.session_state.trial_log = pd.concat([st.session_state.trial_log,new_row],ignore_index=True)
            st.session_state.trial_runs_done +=1
            st.session_state.logged_this_round = True
            if st.session_state.trial_runs_done >= trial_runs_required:
                st.info("✅ You completed 10 trial runs.")
                if st.button("📄 See Results"):
                    st.session_state.page = "trial_summary"
                    st.rerun()

# ---------------- PAGE: Trial Summary ----------------
if st.session_state.page=="trial_summary":
    st.title("📄 Trial Summary")
    st.write(f"Total trials completed: {st.session_state.trial_runs_done}")
    total_switch_wins = st.session_state.trial_log['switch_win'].sum()
    total_stay_wins = st.session_state.trial_log['stay_win'].sum()
    st.write(f"Wins by switching: {total_switch_wins}")
    st.write(f"Wins by staying: {total_stay_wins}")
    col1,col2 = st.columns(2)
    with col1:
        if st.button("🔄 Another 10 Trial Rounds"):
            st.session_state.trial_runs_done = 0
            st.session_state.trial_log = pd.DataFrame(columns=st.session_state.trial_log.columns)
            st.session_state.page="trial"
            reset_game()
            st.rerun()
    with col2:
        if st.button("🚀 Go to Real Experiment"):
            st.session_state.page="round1_instr"
            st.rerun()



