import streamlit as st
import random
import time
import pandas as pd
from datetime import datetime
from github import Github

# --- Config ---
st.set_page_config(page_title="Card Game Experiment", page_icon="🏆", layout="wide")
MAX_ROUNDS = 20  # rounds per block
CARD_SIZE = "12rem"  # emoji size

# --- Initialize session state ---
for key, default in [
    ("player_name", None),
    ("participant_email", ""),
    ("trial_mode", None),
    ("experiment_rounds", 0),
    ("current_block", 0),
    ("cards", ["🂠"]*3),
    ("trophy_pos", random.randint(0,2)),
    ("first_choice", None),
    ("flipped_card", None),
    ("second_choice", None),
    ("phase", "first_pick"),
    ("game_over", False),
    ("log_df", pd.DataFrame(columns=[
        "block", "round_number","first_choice","flipped_card","second_choice",
        "result","stay_or_switch","heuristic","time_pressure","reward"
    ])),
    ("heuristic", None),
    ("time_pressure", False),
    ("show_summary", False)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- Reset round ---
def reset_round():
    st.session_state.cards = ["🂠"]*3
    st.session_state.trophy_pos = random.randint(0,2)
    st.session_state.first_choice = None
    st.session_state.flipped_card = None
    st.session_state.second_choice = None
    st.session_state.phase = "first_pick"
    st.session_state.game_over = False

# --- Get card emojis ---
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

# --- Participant name input (mandatory) ---
if st.session_state.player_name is None:
    st.title("🏆 Card Game Experiment")
    st.write("""
Instructions:
You will be shown three cards and your goal is to find the card with the trophy 🏆 behind it.

1️⃣ Choose a card.  
2️⃣ One of the NOT chosen cards will then be revealed.  
3️⃣ Pick again: you can stick with your first choice or switch to the other card.  
The winning trophy card is then revealed!

Points system:
- Winning card gives 100 points.  
- In some rounds, switching or staying may reduce points (hidden from you).  
- The overall best scorers can win 20, 30, or 50 CHF.  
- Email or phone number is optional for prize contact.
""")
    name_input = st.text_input("Enter your first and last name:", key="name_input")
    email_input = st.text_input("Email or phone (optional):", key="email_input")
    if st.button("✅ Confirm"):
        if name_input.strip() != "":
            st.session_state.player_name = name_input.strip()
            st.session_state.participant_email = email_input.strip()
            st.experimental_rerun()
        else:
            st.warning("Please enter a valid name.")
    st.stop()

player_name = st.session_state.player_name

# --- Trial / Experiment selection ---
if st.session_state.trial_mode is None:
    st.write("Do you want to do a few trial runs first?")
    col1, col2 = st.columns(2)
    if col1.button("Yes, trial runs"):
        st.session_state.trial_mode = True
        st.experimental_rerun()
    if col2.button("No, start real experiment"):
        st.session_state.trial_mode = False
        st.session_state.current_block = 1
        st.session_state.experiment_rounds = 0
        st.session_state.heuristic = random.choice(["familiarity","representativeness"])
        st.session_state.time_pressure = random.choice([True, False])
        reset_round()
        st.experimental_rerun()
    st.stop()

phase_type = 0 if st.session_state.trial_mode else 1  # 0=trial, 1=experiment

# --- Trial sidebar control (only in trials) ---
if st.session_state.trial_mode and st.session_state.phase == "first_pick":
    with st.sidebar:
        st.subheader("Trial Runs Control")
        if st.button("Start Real Experiment"):
            st.session_state.trial_mode = False
            st.session_state.current_block = 1
            st.session_state.experiment_rounds = 0
            st.session_state.heuristic = random.choice(["familiarity","representativeness"])
            st.session_state.time_pressure = random.choice([True, False])
            reset_round()
            st.experimental_rerun()

# --- Header ---
header_text = ""
if st.session_state.phase == "first_pick":
    header_text = "Pick your first card"
elif st.session_state.phase == "second_pick":
    header_text = "Pick again (same or new card)"
elif st.session_state.phase == "reveal_all":
    header_text = "Result"

if not st.session_state.trial_mode:
    if st.session_state.phase != "reveal_all":
        header_text = f"Round {st.session_state.experiment_rounds + 1}/{MAX_ROUNDS} : {header_text}"
    else:
        header_text = f"Round {st.session_state.experiment_rounds + 1}/{MAX_ROUNDS} : Result"

st.subheader(header_text)

# --- Display cards ---
cols = st.columns(3)
emojis = get_card_emojis()
for i, col in enumerate(cols):
    col.markdown(f"<h1 style='font-size:{CARD_SIZE}; text-align:center'>{emojis[i]}</h1>", unsafe_allow_html=True)
    if not st.session_state.game_over and col.button("Pick", key=f"card_{i}", use_container_width=True):
        if st.session_state.phase == "first_pick":
            st.session_state.first_choice = i
            losing_cards = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
            st.session_state.flipped_card = random.choice(losing_cards)
            st.session_state.phase = "second_pick"
            st.experimental_rerun()
        elif st.session_state.phase == "second_pick" and i != st.session_state.flipped_card:
            st.session_state.second_choice = i
            st.session_state.phase = "reveal_all"
            st.session_state.game_over = True
            st.experimental_rerun()

# --- Show result ---
if st.session_state.game_over:
    won = st.session_state.second_choice == st.session_state.trophy_pos
    stay_or_switch = "Stayed" if st.session_state.first_choice == st.session_state.second_choice else "Switched"
    reward = 100
    if st.session_state.heuristic == "familiarity" and stay_or_switch == "Switched":
        reward -= 10
    if st.session_state.heuristic == "representativeness" and stay_or_switch == "Stayed":
        reward -= 10

    st.subheader("Result")
    if won:
        st.success(f"🎉 You won the trophy! ({stay_or_switch})")
    else:
        st.error(f"❌ You picked the wrong card. ({stay_or_switch})")
        first = st.session_state.first_choice
        trophy = st.session_state.trophy_pos
        if first == trophy:
            st.info("💡 You should have stayed to win.")
        else:
            st.info("💡 You should have switched to win.")

    # Log the round
    round_number = st.session_state.experiment_rounds + 1
    new_row = pd.DataFrame([{
        "block": st.session_state.current_block,
        "round_number": round_number,
        "first_choice": st.session_state.first_choice,
        "flipped_card": st.session_state.flipped_card,
        "second_choice": st.session_state.second_choice,
        "result": won,
        "stay_or_switch": stay_or_switch,
        "heuristic": st.session_state.heuristic,
        "time_pressure": st.session_state.time_pressure,
        "reward": reward
    }])
    st.session_state.log_df = pd.concat([st.session_state.log_df, new_row], ignore_index=True)

    # --- Next / Summary button ---
    if st.session_state.trial_mode or st.session_state.experiment_rounds + 1 < MAX_ROUNDS:
        if st.button("Next Round"):
            st.session_state.experiment_rounds += 1
            reset_round()
            st.experimental_rerun()
    else:
        if st.button("Show Summary"):
            st.session_state.show_summary = True
            st.experimental_rerun()

# --- Summary ---
if st.session_state.show_summary:
    st.title("✅ Thank You for Participating!")
    total_points = st.session_state.log_df["reward"].sum()
    total_correct = st.session_state.log_df["result"].sum()
    st.write(f"Total points earned: {total_points}")
    st.write(f"Correct picks: {total_correct} / {len(st.session_state.log_df)}")

    # Save CSV to GitHub
    try:
        token = st.secrets["GITHUB_TOKEN"]
        g = Github(token)
        repo = g.get_repo("joojoosch/monty-hall-card-edition")
        csv_data = st.session_state.log_df.to_csv(index=False)
        path = f"player_logs/{st.session_state.participant_email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        repo.create_file(path, f"Add results for {st.session_state.participant_email}", csv_data)
        st.success(f"Results saved to GitHub as {path}")
    except Exception as e:
        st.error(f"⚠️ Couldn't save CSV to GitHub: {e}")


