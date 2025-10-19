import streamlit as st
import random
import time
import pandas as pd
from datetime import datetime
from github import Github

# ----------------------------
# Configuration
# ----------------------------
st.set_page_config(page_title="Card Game Experiment", page_icon="🏆", layout="wide")
MAX_ROUNDS = 20  # rounds per block
EMOJI_SIZE = "10rem"  # slightly smaller

# ----------------------------
# Session State Initialization
# ----------------------------
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
    st.session_state.phase = "first_pick"  # first_pick, second_pick, reveal_all
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame(columns=[
        "round_number","block","time_pressure","heuristic",
        "first_choice","flipped_card","second_choice","switched","reward","result","email_or_phone"
    ])
if "assigned_heuristic" not in st.session_state:
    st.session_state.assigned_heuristic = random.choice(["familiarity","representativeness"])
if "current_block" not in st.session_state:
    st.session_state.current_block = 1
if "time_pressure" not in st.session_state:
    st.session_state.time_pressure = True
if "show_instructions_block2" not in st.session_state:
    st.session_state.show_instructions_block2 = False
if "participant_contact" not in st.session_state:
    st.session_state.participant_contact = ""

# ----------------------------
# Reset Game Function
# ----------------------------
def reset_game():
    st.session_state.cards = ["🂠"]*3
    st.session_state.trophy_pos = random.randint(0,2)
    st.session_state.first_choice = None
    st.session_state.flipped_card = None
    st.session_state.second_choice = None
    st.session_state.phase = "first_pick"
    st.session_state.game_over = False

# ----------------------------
# Instructions and Name Input
# ----------------------------
if st.session_state.trial_mode is None:
    st.title("🏆 Card Game Experiment")
    st.write(f"""
**Instructions:**  
You will be shown three cards. One hides a trophy 🏆.  

1️⃣ Pick a card.  
2️⃣ One of the remaining cards will be revealed.  
3️⃣ Pick again (same or different card).  

**Points System:**  
- Each round, picking the trophy gives **100 points**.  
- Depending on the rules, switching or staying may reduce your points by 10.  
- Highest scorers will receive prizes: 20, 30, 50 CHF.  

If you want to be contacted for prizes, enter your email or phone number below. You can leave it empty if you do not wish to participate.
""")
    st.session_state.participant_contact = st.text_input("Email or phone for prizes (optional):", key="contact")
    col1, col2 = st.columns(2)
    if col1.button("✅ Confirm Name"):
        name_input = st.session_state.participant_contact.strip()
        st.session_state.player_name = name_input if name_input else "Anonymous"
        st.session_state.trial_mode = True  # start with trial mode
        st.rerun()
    st.stop()

player_name = st.session_state.player_name

# ----------------------------
# Determine Current Heuristic
# ----------------------------
def current_heuristic():
    if st.session_state.current_block == 1:
        return st.session_state.assigned_heuristic
    else:
        return "familiarity" if st.session_state.assigned_heuristic == "representativeness" else "representativeness"

# ----------------------------
# Card Emoji Display
# ----------------------------
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

# ----------------------------
# Header Text for Current Phase
# ----------------------------
def get_header_text():
    if st.session_state.trial_mode:
        block_prefix = f"Trial Block"
    else:
        block_prefix = f"Round {st.session_state.experiment_rounds + 1}/{MAX_ROUNDS}"

    if st.session_state.phase == "first_pick":
        return f"{block_prefix}: Pick your first card"
    elif st.session_state.phase == "second_pick":
        return f"{block_prefix}: Pick Again (same or new card)"
    elif st.session_state.phase == "reveal_all" or st.session_state.game_over:
        return f"{block_prefix}: Result"

# ----------------------------
# Display Cards
# ----------------------------
if st.session_state.experiment_rounds < MAX_ROUNDS or st.session_state.trial_mode:
    st.header(get_header_text())
    cols = st.columns(3)
    emojis = get_card_emojis()
    for i, col in enumerate(cols):
        col.markdown(f"<h1 style='font-size:{EMOJI_SIZE}; text-align:center'>{emojis[i]}</h1>", unsafe_allow_html=True)
        if not st.session_state.game_over and col.button("Pick", key=f"card_{i}", use_container_width=True):
            # First pick
            if st.session_state.phase == "first_pick":
                st.session_state.first_choice = i
                losing_cards = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
                st.session_state.flipped_card = random.choice(losing_cards)
                st.session_state.phase = "second_pick"
            # Second pick
            elif st.session_state.phase == "second_pick" and i != st.session_state.flipped_card:
                st.session_state.second_choice = i
                st.session_state.phase = "reveal_all"
                st.session_state.game_over = True

# ----------------------------
# Feedback and Next Round
# ----------------------------
if st.session_state.game_over:
    switched = st.session_state.second_choice != st.session_state.first_choice
    heuristic_active = current_heuristic()
    reward = 100 if st.session_state.second_choice == st.session_state.trophy_pos else 0
    # Apply hidden heuristic penalties
    if heuristic_active == "familiarity" and switched and reward > 0:
        reward -= 10
    elif heuristic_active == "representativeness" and not switched and reward > 0:
        reward -= 10

    # Show result
    st.header("Result")
    if reward > 0:
        if switched:
            st.success(f"🎉 You won the trophy because you switched! You earned {reward} points!")
        else:
            st.success(f"🎉 You won the trophy because you stayed! You earned {reward} points!")
    else:
        st.error("❌ You picked the wrong card. You earned 0 points.")

    # Log round
    round_number = st.session_state.experiment_rounds + 1
    new_row = pd.DataFrame([{
        "round_number": round_number,
        "block": st.session_state.current_block,
        "time_pressure": st.session_state.time_pressure,
        "heuristic": heuristic_active,
        "first_choice": st.session_state.first_choice,
        "flipped_card": st.session_state.flipped_card,
        "second_choice": st.session_state.second_choice,
        "switched": switched,
        "reward": reward,
        "result": reward > 0,
        "email_or_phone": st.session_state.participant_contact
    }])
    st.session_state.log_df = pd.concat([st.session_state.log_df, new_row], ignore_index=True)

    # Next round button
    if st.session_state.trial_mode or st.session_state.experiment_rounds + 1 < MAX_ROUNDS:
        if st.button("Next Round"):
            st.session_state.experiment_rounds += 1
            reset_game()
    else:
        # Show summary
        if st.button("Show Summary"):
            total_score = st.session_state.log_df["reward"].sum()
            total_correct = st.session_state.log_df["result"].sum()
            st.header("🎉 Thank you for participating!")
            st.write(f"Your total score: {total_score} points")
            st.write(f"Correct picks: {total_correct} / {2*MAX_ROUNDS}")
            # Save CSV to GitHub
            try:
                token = st.secrets["GITHUB_TOKEN"]
                g = Github(token)
                repo = g.get_repo("joojoosch/monty-hall-card-edition")
                csv_data = st.session_state.log_df.to_csv(index=False)
                path = f"player_logs/{player_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                repo.create_file(path, f"Add results for {player_name}", csv_data)
                st.success(f"Results saved to GitHub as {path}")
            except Exception as e:
                st.error(f"⚠️ Couldn't save: {e}")

# ----------------------------
# Show Log (optional)
# ----------------------------
st.divider()
st.subheader("📊 Game Log")
st.dataframe(st.session_state.log_df, use_container_width=True)
