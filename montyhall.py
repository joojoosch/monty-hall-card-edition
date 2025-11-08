import streamlit as st
import random
import pandas as pd
from datetime import datetime
from github import Github

st.set_page_config(page_title="Card Game Experiment", page_icon="🏆", layout="wide")

max_experiment_rounds = 6  # 2 rounds × 3 trials each

# --- Initialize session state ---
if "player_name" not in st.session_state:
    st.session_state.player_name = None
if "trial_mode" not in st.session_state:
    st.session_state.trial_mode = True
if "experiment_rounds" not in st.session_state:
    st.session_state.experiment_rounds = 0
if "trial_runs_done" not in st.session_state:
    st.session_state.trial_runs_done = 0
if "cards" not in st.session_state:
    st.session_state.cards = ["🂠"] * 3
if "trophy_pos" not in st.session_state:
    st.session_state.trophy_pos = random.randint(0, 2)
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
    st.session_state.points = 0
if "current_round_set" not in st.session_state:
    st.session_state.current_round_set = 1
if "round_transition" not in st.session_state:
    st.session_state.round_transition = False
if "ready_page" not in st.session_state:
    st.session_state.ready_page = False
if "rules_page" not in st.session_state:
    st.session_state.rules_page = False  # ### 🔵 NEW: for "Now we add new rules" page
if "experiment_finished" not in st.session_state:
    st.session_state.experiment_finished = False
if "logged_this_round" not in st.session_state:
    st.session_state.logged_this_round = False
if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame(
        columns=[
            "round_number",
            "first_choice",
            "flipped_card",
            "second_choice",
            "trophy_card",
            "result",
            "phase_type",
            "points_after_round",
        ]
    )

# --- Reset game function ---
def reset_game():
    st.session_state.cards = ["🂠"] * 3
    st.session_state.trophy_pos = random.randint(0, 2)
    st.session_state.first_choice = None
    st.session_state.flipped_card = None
    st.session_state.second_choice = None
    st.session_state.phase = "first_pick"
    st.session_state.game_over = False
    st.session_state.logged_this_round = False


# --- Instructions and name input ---
st.title("🏆 Card Game Experiment")
st.write(
    """
You will be shown three cards and your goal is to find the trophy 🏆 behind one of them.

1️⃣ Choose a card.  
2️⃣ One of the NOT chosen cards will be revealed.  
3️⃣ Choose to stick with your first choice or switch to the other remaining card.  
The winning trophy card is then revealed!
"""
)

if st.session_state.player_name is None:
    name_input = st.text_input("Enter your first and last name:", key="name_input")
    if st.button("✅ Confirm Name"):
        if name_input.strip() != "":
            st.session_state.player_name = name_input.strip()
            st.rerun()
        else:
            st.warning("Please enter a valid name.")
    st.stop()

player_name = st.session_state.player_name

# --- Trial section ---
st.markdown("## 🔁 Trial Runs (Practice)")
st.write(
    "You must complete **at least 10 trial runs** before starting the real experiment. "
    "Trials are practice and do not affect points. You may do more than 10 trials if you like."
)
st.write(f"Trials completed so far: **{st.session_state.trial_runs_done}** (need 10 to unlock real experiment)")

if st.session_state.trial_runs_done >= 10 and not st.session_state.ready_page and not st.session_state.rules_page:
    if st.button("🚀 Prepare to Start Real Experiment"):
        st.session_state.rules_page = True  # ### 🔵 NEW: go to new rules page
        st.rerun()

# --- Page: "Now we add new rules" ---
if st.session_state.rules_page:
    st.title("🧮 Now we add new rules!")
    st.write(
        """
You have practiced enough — now we begin the **real experiment**.

### 🪙 Point System Overview
You will now earn and lose points:

- You start with **50 points**.  
- You will play **2 rounds of 3 trials each (6 total).**

#### 🎯 Round 1 Rules
- Each correct card gives **+100 points**.  
- **Switching** after the reveal costs **10 points**.  
- Staying is free.

#### 🎯 Round 2 Rules
- Each correct card gives **+100 points**.  
- **Staying** with your first choice costs **10 points**.  
- Switching is free.
"""
    )

    if st.button("✅ Start Real Experiment"):
        st.session_state.trial_mode = False
        st.session_state.points = 50
        st.session_state.experiment_rounds = 0
        st.session_state.current_round_set = 1
        st.session_state.rules_page = False
        reset_game()
        st.success("Real experiment started — Round 1 of 2, starting with 50 points!")
        st.rerun()
    st.stop()


# --- Transition page between rounds ---
if st.session_state.round_transition:
    st.title("🏁 Round 1 Complete!")
    st.markdown(f"Your current score: **{st.session_state.points} points**")
    st.write(
        """
### 🎯 Round 2 Rules:
- Each correct card gives **+100 points**.  
- **Staying** with your first choice now costs **10 points**.  
- Switching is free in Round 2.
"""
    )
    if st.button("🚀 Start Round 2"):
        st.session_state.current_round_set = 2
        st.session_state.round_transition = False
        reset_game()
        st.rerun()
    st.stop()


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


# --- Experiment finished ---
if st.session_state.experiment_finished:
    st.title("🎉 Thank you for participating!")
    total_correct = st.session_state.log_df[st.session_state.log_df["phase_type"] == 1]["result"].sum()
    st.write(f"✅ Correct picks (total): {total_correct}")
    st.write(f"💰 Final points: {st.session_state.points}")
    st.stop()


# --- Header ---
header_text = ""
if st.session_state.phase == "first_pick":
    header_text = "Pick your first card"
elif st.session_state.phase == "second_pick":
    header_text = "Pick Again (same or new card)"
elif st.session_state.phase == "reveal_all" and not st.session_state.trial_mode:
    header_text = "Reveal"

if not st.session_state.trial_mode:
    current_round = st.session_state.experiment_rounds + 1
    header_text = f"Round {current_round}/6: {header_text}"

if header_text:
    st.header(header_text)

if not st.session_state.trial_mode:
    st.markdown(f"### 💰 Current Score: {st.session_state.points} points")

# --- Display cards ---
if not st.session_state.experiment_finished:
    cols = st.columns(3)
    emojis = get_card_emojis()
    for i, col in enumerate(cols):
        col.markdown(
            f"<h1 style='font-size:10rem; text-align:center'>{emojis[i]}</h1>",
            unsafe_allow_html=True,
        )
        if not st.session_state.game_over and col.button("Pick", key=f"card_{i}", use_container_width=True):
            if st.session_state.phase == "first_pick":
                st.session_state.first_choice = i
                losing_cards = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
                st.session_state.flipped_card = random.choice(losing_cards)
                st.session_state.phase = "second_pick"
                st.rerun()
            elif st.session_state.phase == "second_pick" and i != st.session_state.flipped_card:
                staying = (i == st.session_state.first_choice)
                cost = 0
                if not st.session_state.trial_mode:
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


# --- Results + Logging ---
if st.session_state.game_over:
    won = st.session_state.second_choice == st.session_state.trophy_pos
    stayed = st.session_state.first_choice == st.session_state.second_choice

    # simplified results without advice
    if won:
        st.success("🎉 You found the trophy!")
    else:
        st.error("❌ You picked the wrong card.")

    # compute point effect
    if not st.session_state.trial_mode:
        round_points_change = 0
        if won:
            round_points_change += 100
        # we already deducted cost when action chosen
        st.markdown(f"**You {'won' if round_points_change>0 else 'lost' if round_points_change<0 else 'got'} {abs(round_points_change)} points this round.**")
    else:
        st.info("Trial round — no points earned or lost.")

    if not st.session_state.logged_this_round:
        if not st.session_state.trial_mode and won:
            st.session_state.points += 100
        round_number = len(st.session_state.log_df[st.session_state.log_df["phase_type"] == (0 if st.session_state.trial_mode else 1)]) + 1
        new_row = pd.DataFrame([{
            "round_number": round_number,
            "first_choice": st.session_state.first_choice,
            "flipped_card": st.session_state.flipped_card,
            "second_choice": st.session_state.second_choice,
            "trophy_card": st.session_state.trophy_pos,
            "result": won,
            "phase_type": 0 if st.session_state.trial_mode else 1,
            "points_after_round": st.session_state.points,
        }])
        st.session_state.log_df = pd.concat([st.session_state.log_df, new_row], ignore_index=True)
        if st.session_state.trial_mode:
            st.session_state.trial_runs_done += 1
        else:
            st.session_state.experiment_rounds += 1
        st.session_state.logged_this_round = True

    # buttons
    if (not st.session_state.trial_mode and st.session_state.experiment_rounds == 3 and st.session_state.current_round_set == 1):
        if st.button("🏁 Continue to Round 2"):
            st.session_state.round_transition = True
            st.rerun()
    elif (not st.session_state.trial_mode and st.session_state.experiment_rounds >= max_experiment_rounds):
        if st.button("📊 Show Summary"):
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
            st.session_state.experiment_finished = True
            st.rerun()
    else:
        if st.button("Next"):  # ### 🔵 FIXED: button label
            st.session_state.logged_this_round = False
            reset_game()
            st.rerun()

# --- Log Display ---
st.divider()
st.subheader("📊 Game Log")
st.dataframe(st.session_state.log_df, use_container_width=True)


