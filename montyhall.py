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
    st.session_state.trial_mode = True  # ### 🔵 NEW: force trial mode initially (must do trials)
if "experiment_rounds" not in st.session_state:
    st.session_state.experiment_rounds = 0  # counts real experiment trials completed (0..6)
if "trial_runs_done" not in st.session_state:
    st.session_state.trial_runs_done = 0  # ### 🔵 NEW: counts how many trial trials completed
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
    st.session_state.points = 0  # total points (only meaningful in real experiment)
if "current_round_set" not in st.session_state:
    st.session_state.current_round_set = 1  # 1 = Round 1 (first 3 real trials), 2 = Round 2
if "round_transition" not in st.session_state:
    st.session_state.round_transition = False  # ### 🔵 NEW: show transition page between Round1 & Round2
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
            "points_after_round",  # ### 🔵 NEW: store points after each trial
        ]
    )
if "experiment_finished" not in st.session_state:
    st.session_state.experiment_finished = False
if "logged_this_round" not in st.session_state:
    st.session_state.logged_this_round = False
if "ready_page" not in st.session_state:
    st.session_state.ready_page = False

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

# --- NEW: Mandatory trial-run instruction and Start Real Experiment gating ---
### 🔵 NEW:
st.markdown("## 🔁 Trial Runs (Practice)")
st.write(
    "You must complete **at least 10 trial runs** before starting the real experiment. "
    "Trials are practice and do not affect points. You may do more than 10 trials if you like."
)
st.write(f"Trials completed so far: **{st.session_state.trial_runs_done}** (need 10 to unlock real experiment)")

# Offer the real experiment "ready" button only after 10 trial runs:
if st.session_state.trial_runs_done >= 10 and not st.session_state.ready_page:
    if st.button("🚀 Prepare to Start Real Experiment"):
        st.session_state.ready_page = True
        st.rerun()

# --- Phase type: 0 for trial, 1 for real experiment ---
phase_type = 0 if st.session_state.trial_mode else 1

# --- Ready page (round explanation) ---
if st.session_state.ready_page:
    st.title("🚀 Ready for the Real Experiment?")
    st.write("You will complete **2 rounds of 3 trials each (6 total).**")

    # Explain only Round 1 here (per your request)
    st.write(
        """
### 🎯 Round 1 Rules (starting rules)
- When the real experiment starts you will get **50 starting points**.  
- Each correct card gives **+100 points**.  
- **Switching** after the reveal costs **10 points** in Round 1.  
- Staying is free in Round 1.
"""
    )

    if st.button("✅ Start Real Experiment"):
        # initialize real experiment variables
        st.session_state.trial_mode = False
        st.session_state.points = 50  # starting points
        st.session_state.experiment_rounds = 0
        st.session_state.current_round_set = 1
        st.session_state.round_transition = False
        st.session_state.ready_page = False
        reset_game()
        st.success("Real experiment started — Round 1 of 2, starting with 50 points!")
        st.rerun()
    st.stop()


# --- Transition page between Round 1 and Round 2 ---
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
        # experiment_rounds remains at 3 (first 3 real trials completed)
        st.rerun()
    st.stop()


# --- Determine emojis for each card ---
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


# --- Show summary and hide everything else if finished ---
if st.session_state.experiment_finished:
    st.title("🎉 Thank you for participating!")
    total_correct = st.session_state.log_df[st.session_state.log_df["phase_type"] == 1]["result"].sum()
    st.write(f"✅ Correct picks (total): {total_correct}")
    st.write(f"💰 Final points: {st.session_state.points}")
    st.stop()


# --- Display header depending on phase ---
header_text = ""
if st.session_state.phase == "first_pick":
    header_text = "Pick your first card"
elif st.session_state.phase == "second_pick":
    header_text = "Pick Again (same or new card)"
elif st.session_state.phase == "reveal_all" and not st.session_state.trial_mode:
    header_text = "Reveal"

# Add current round / total rounds for real experiment
if not st.session_state.trial_mode:
    current_round = st.session_state.experiment_rounds + 1
    header_text = f"Round {current_round}/6: {header_text}"

if header_text and not st.session_state.experiment_finished:
    st.header(header_text)

# --- Show current score (for real experiment) ---
### 🔵 NEW: Only show score at top during real experiment, not during trials
if not st.session_state.trial_mode:
    st.markdown(f"### 💰 Current Score: {st.session_state.points} points")


# --- Display cards ---
if not st.session_state.experiment_finished and (st.session_state.experiment_rounds < max_experiment_rounds or phase_type == 0):
    cols = st.columns(3)
    emojis = get_card_emojis()
    for i, col in enumerate(cols):
        col.markdown(
            f"<h1 style='font-size:10rem; text-align:center'>{emojis[i]}</h1>",
            unsafe_allow_html=True
        )
        if not st.session_state.game_over and col.button("Pick", key=f"card_{i}", use_container_width=True):
            if st.session_state.phase == "first_pick":
                st.session_state.first_choice = i
                losing_cards = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
                st.session_state.flipped_card = random.choice(losing_cards)
                st.session_state.phase = "second_pick"
                st.rerun()
            elif st.session_state.phase == "second_pick" and i != st.session_state.flipped_card:
                # determine whether this choice counts as "staying" or "switching"
                staying = (i == st.session_state.first_choice)
                cost = 0
                if not st.session_state.trial_mode:
                    # Round 1: switching costs 10. Round 2: staying costs 10.
                    if st.session_state.current_round_set == 1 and not staying:
                        cost = 10
                    elif st.session_state.current_round_set == 2 and staying:
                        cost = 10

                    # If not enough points, block the action
                    if st.session_state.points < cost:
                        st.warning("⚠️ You don’t have enough points for this action!")
                        st.stop()

                # Deduct cost (if any) immediately when action chosen
                st.session_state.points -= cost

                st.session_state.second_choice = i
                st.session_state.phase = "reveal_all"
                st.session_state.game_over = True
                st.rerun()


# --- Display results and control buttons ---
if st.session_state.game_over:
    st.header("Result:")
    won = st.session_state.second_choice == st.session_state.trophy_pos
    stayed = st.session_state.first_choice == st.session_state.second_choice

    if won:
        if stayed:
            st.success("🎉 You won the 🏆 trophy because you stayed!")
        else:
            st.success("🎉 You won the 🏆 trophy because you switched!")
    else:
        st.error("❌ You picked the wrong card. 😢")
        first = st.session_state.first_choice
        trophy = st.session_state.trophy_pos
        if first == trophy:
            st.info("💡 You should have stayed to win.")
        else:
            st.info("💡 You should have switched to win.")

    # --- 🟦 Update points: award +100 for correct (real experiment only)
    # Move awarding into the logging block to avoid double-adds across reruns/buttons.
    # (So we don't add here; we add when we log the row below.)

    # --- Log result (only once per trial)
    if not st.session_state.logged_this_round:
        # If this is real experiment, award points for correct BEFORE logging (only once)
        if not st.session_state.trial_mode and won:
            st.session_state.points += 100  # award +100 for a correct pick (done once)

        # Determine round number for logging (per phase_type)
        round_number = len(st.session_state.log_df[st.session_state.log_df["phase_type"] == phase_type]) + 1

        new_row = pd.DataFrame([{
            "round_number": round_number,
            "first_choice": st.session_state.first_choice,
            "flipped_card": st.session_state.flipped_card,
            "second_choice": st.session_state.second_choice,
            "trophy_card": st.session_state.trophy_pos,
            "result": won,
            "phase_type": phase_type,
            "points_after_round": st.session_state.points,  # ### 🔵 NEW: store current points
        }])
        st.session_state.log_df = pd.concat([st.session_state.log_df, new_row], ignore_index=True)

        # increment counters appropriately
        if phase_type == 0:
            # trial mode completed one trial
            st.session_state.trial_runs_done += 1  # ### 🔵 NEW
        else:
            # real experiment: completed one trial
            st.session_state.experiment_rounds += 1

        st.session_state.logged_this_round = True

    col1, col2 = st.columns(2)

    # --- After finishing a trial in the real experiment, check for Round transition or experiment end
    if (not st.session_state.trial_mode and st.session_state.experiment_rounds >= 3 and st.session_state.current_round_set == 1):
        # Completed 3 real trials => offer transition page (rules for round 2)
        if st.button("🏁 Continue to Round 2"):
            st.session_state.round_transition = True
            st.rerun()

    elif (not st.session_state.trial_mode and st.session_state.experiment_rounds >= max_experiment_rounds):
        # Completed all 6 real trials => final summary / save
        with col1:
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
        # Generic next-trial / continue button
        next_button_label = "Next Trial" if not st.session_state.trial_mode else "🔄 Try Another Trial"
        if st.button(next_button_label):
            st.session_state.logged_this_round = False
            # For trial mode: we do not increment experiment_rounds; trial_runs_done already incremented when logging.
            # For real experiment: experiment_rounds was incremented above during logging; simply reset for next trial.
            reset_game()
            st.rerun()

# --- Show game log ---
st.divider()
st.subheader("📊 Game Log")
st.dataframe(st.session_state.log_df, use_container_width=True)


