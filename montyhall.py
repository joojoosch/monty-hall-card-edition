import streamlit as st
import random
import pandas as pd
from datetime import datetime
from github import Github

# --- Config ---
st.set_page_config(page_title="Card Game Experiment", page_icon="🏆", layout="wide")
MAX_ROUNDS = 20

# --- Initialize session state ---
for key, default in {
    "participant_name": None,
    "participant_contact": "",
    "trial_mode": None,
    "experiment_rounds": 0,
    "current_block": 1,
    "heuristic": None,
    "time_pressure": None,
    "cards": ["🂠"]*3,
    "trophy_pos": random.randint(0,2),
    "first_choice": None,
    "flipped_card": None,
    "second_choice": None,
    "phase": "first_pick",
    "game_over": False,
    "show_summary": False,
    "log_df": pd.DataFrame(columns=[
        "block","round_number","heuristic","time_pressure",
        "first_choice","flipped_card","second_choice","switched",
        "reward","result","participant_contact"
    ])
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- Helper functions ---
def reset_round():
    st.session_state.cards = ["🂠"]*3
    st.session_state.trophy_pos = random.randint(0,2)
    st.session_state.first_choice = None
    st.session_state.flipped_card = None
    st.session_state.second_choice = None
    st.session_state.phase = "first_pick"
    st.session_state.game_over = False

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

# --- Participant info page ---
if st.session_state.participant_name is None:
    st.title("🏆 Card Game Experiment")
    st.write("""
**Instructions:**  
You will be shown three cards. One hides a trophy 🏆.

1️⃣ Pick a card.  
2️⃣ One of the remaining cards will be revealed.  
3️⃣ Pick again (same or different card).  

**Points system:**  
- Picking the trophy gives **100 points**.  
- Depending on the rules for this block, switching or staying may reduce your points by 10.  
- Highest scorers may receive prizes (20, 30, 50 CHF).  

If you want to be contacted for prizes, enter your email or phone below. Otherwise leave it blank.
""")
    st.session_state.participant_name = st.text_input("First and last name:")
    st.session_state.participant_contact = st.text_input("Email or phone (optional):")
    if st.button("✅ Confirm"):
        if st.session_state.participant_name.strip() != "":
            st.session_state.trial_mode = True
            st.rerun()
        else:
            st.warning("Please enter a valid name.")
    st.stop()

# --- Trial selection ---
if st.session_state.trial_mode is None:
    st.write("Do you want to do a few trial runs first?")
    col1, col2 = st.columns(2)
    if col1.button("Yes, trial runs"):
        st.session_state.trial_mode = True
        st.rerun()
    if col2.button("No, start experiment"):
        st.session_state.trial_mode = False
        st.rerun()
    st.stop()

# --- Ready page for real experiment ---
if not st.session_state.trial_mode and st.session_state.experiment_rounds == 0 and st.session_state.current_block == 1:
    st.title("🏆 Get Ready for the Real Experiment")
    st.write(f"You will now start **Block 1** of the real experiment with {MAX_ROUNDS} rounds.")
    st.write("Instructions are the same as in the trial rounds. Remember the points system!")
    if st.button("Start Real Experiment"):
        st.session_state.heuristic = random.choice(["familiarity","representativeness"])
        st.session_state.time_pressure = random.choice([True, False])
        st.rerun()
    st.stop()

# --- Determine current header ---
header_text = ""
if st.session_state.trial_mode:
    if st.session_state.phase == "first_pick":
        header_text = "Pick your first card"
    elif st.session_state.phase == "second_pick":
        header_text = "Pick again (same or new card)"
    elif st.session_state.phase == "reveal_all":
        header_text = "Result"
else:
    if st.session_state.experiment_rounds < MAX_ROUNDS:
        round_num = st.session_state.experiment_rounds + 1
        if st.session_state.phase == "first_pick":
            header_text = f"Block {st.session_state.current_block}, Round {round_num}/{MAX_ROUNDS}: Pick your first card"
        elif st.session_state.phase == "second_pick":
            header_text = f"Block {st.session_state.current_block}, Round {round_num}/{MAX_ROUNDS}: Pick again (same or new card)"
        elif st.session_state.phase == "reveal_all":
            header_text = f"Block {st.session_state.current_block}, Round {round_num}/{MAX_ROUNDS}: Result"
    else:
        header_text = f"Block {st.session_state.current_block} completed"

st.header(header_text)

# --- Display cards ---
if not st.session_state.show_summary:
    cols = st.columns(3)
    emojis = get_card_emojis()
    for i, col in enumerate(cols):
        col.markdown(f"<h1 style='font-size:10rem; text-align:center'>{emojis[i]}</h1>", unsafe_allow_html=True)
        if not st.session_state.game_over and col.button("Pick", key=f"card_{i}", use_container_width=True):
            # First pick
            if st.session_state.phase == "first_pick":
                st.session_state.first_choice = i
                losing_cards = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
                st.session_state.flipped_card = random.choice(losing_cards)
                st.session_state.phase = "second_pick"
                st.experimental_rerun()
            # Second pick
            elif st.session_state.phase == "second_pick" and i != st.session_state.flipped_card:
                st.session_state.second_choice = i
                st.session_state.phase = "reveal_all"
                st.session_state.game_over = True
                st.experimental_rerun()

# --- Show feedback and log round ---
if st.session_state.phase == "reveal_all" and st.session_state.game_over:
    switched = st.session_state.second_choice != st.session_state.first_choice
    won = st.session_state.second_choice == st.session_state.trophy_pos
    # Reward calculation
    base_reward = 100
    if not st.session_state.trial_mode:
        if st.session_state.heuristic == "familiarity":
            reward = base_reward - 10 if switched else base_reward
        else:
            reward = base_reward - 10 if not switched else base_reward
    else:
        reward = base_reward

    # Feedback
    st.subheader("Result")
    if won:
        if switched:
            st.success(f"🎉 You won by switching! Points: {reward}")
        else:
            st.success(f"🎉 You won by staying! Points: {reward}")
    else:
        st.error(f"❌ You picked the wrong card. Points: {reward}")

    # Log round
    round_number = st.session_state.experiment_rounds + 1 if not st.session_state.trial_mode else 0
    new_row = pd.DataFrame([{
        "block": st.session_state.current_block,
        "round_number": round_number,
        "heuristic": st.session_state.heuristic if not st.session_state.trial_mode else "trial",
        "time_pressure": st.session_state.time_pressure if not st.session_state.trial_mode else None,
        "first_choice": st.session_state.first_choice,
        "flipped_card": st.session_state.flipped_card,
        "second_choice": st.session_state.second_choice,
        "switched": switched,
        "reward": reward,
        "result": won,
        "participant_contact": st.session_state.participant_contact
    }])
    st.session_state.log_df = pd.concat([st.session_state.log_df, new_row], ignore_index=True)

# --- Next Round / Show Summary ---
if st.session_state.game_over and not st.session_state.show_summary:
    col1, col2 = st.columns(2)
    if st.session_state.trial_mode or st.session_state.experiment_rounds + 1 < MAX_ROUNDS:
        if col1.button("Next Round"):
            if not st.session_state.trial_mode:
                st.session_state.experiment_rounds += 1
            reset_round()
            st.experimental_rerun()
    else:
        # End of block
        if col1.button("Next Block"):
            if st.session_state.current_block == 1:
                # Setup block 2 with opposite time pressure
                st.session_state.current_block = 2
                st.session_state.experiment_rounds = 0
                st.session_state.time_pressure = not st.session_state.time_pressure
                st.session_state.heuristic = random.choice(["familiarity","representativeness"])
                reset_round()
                st.experimental_rerun()
            else:
                # Both blocks done
                st.session_state.show_summary = True
                st.experimental_rerun()
    if st.session_state.trial_mode:
        if col2.button("Start Real Experiment"):
            st.session_state.trial_mode = False
            st.session_state.current_block = 1
            st.session_state.experiment_rounds = 0
            st.session_state.heuristic = random.choice(["familiarity","representativeness"])
            st.session_state.time_pressure = random.choice([True, False])
            reset_round()
            st.experimental_rerun()

# --- Show final summary ---
if st.session_state.show_summary:
    st.title("✅ Thank You for Participating!")
    total_points = st.session_state.log_df["reward"].sum()
    total_correct = st.session_state.log_df["result"].sum()
    st.write(f"Total points earned: {total_points}")
    st.write(f"Correct picks: {total_correct}")
    st.write(f"Total rounds: {len(st.session_state.log_df)}")
    
    # Save CSV to GitHub
    try:
        token = st.secrets["GITHUB_TOKEN"]
        g = Github(token)
        repo = g.get_repo("joojoosch/monty-hall-card-edition")
        csv_data = st.session_state.log_df.to_csv(index=False)
        path = f"player_logs/{st.session_state.participant_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        repo.create_file(path, f"Add results for {st.session_state.participant_name}", csv_data)
        st.success(f"Results saved to GitHub as {path}")
    except Exception as e:
        st.error(f"⚠️ Couldn't save CSV to GitHub: {e}")


