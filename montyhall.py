import streamlit as st
import random
import pandas as pd
from datetime import datetime
from github import Github

st.set_page_config(page_title="Card Game Experiment", page_icon="🏆", layout="wide")

# ---------------- Constants ----------------
TRIALS_REQUIRED = 10
TRIALS_PER_ROUND = 3  # 3 trials per round, 2 rounds => 6 experiment trials total

# ---------------- Session state initialization ----------------
if "player_name" not in st.session_state:
    st.session_state.player_name = None

# page can be: instructions, trial, trial_summary, round1_instr, round1, round2_instr, round2, summary
if "page" not in st.session_state:
    st.session_state.page = "instructions"

if "trial_runs_done" not in st.session_state:
    st.session_state.trial_runs_done = 0
if "trial_log" not in st.session_state:
    st.session_state.trial_log = pd.DataFrame(columns=[
        "trial_number", "first_choice", "flipped_card", "second_choice",
        "trophy_card", "result", "switch_win", "stay_win"
    ])

# experiment counters
if "experiment_round" not in st.session_state:
    st.session_state.experiment_round = 0  # number of completed experiment trials (0..6)
if "current_round_set" not in st.session_state:
    st.session_state.current_round_set = 1  # 1 or 2
if "experiment_log" not in st.session_state:
    st.session_state.experiment_log = pd.DataFrame(columns=[
        "round_number", "first_choice", "flipped_card", "second_choice",
        "trophy_card", "result", "phase_type", "points_after_round",
        "switch_win", "stay_win"
    ])

# Game state
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
    st.session_state.phase = "first_pick"  # first_pick, second_pick, reveal_all
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "points" not in st.session_state:
    st.session_state.points = 50  # start points when real experiment starts (kept across rounds)
if "logged_this_round" not in st.session_state:
    st.session_state.logged_this_round = False

# ---------------- Helpers ----------------
def reset_game_state_for_trial():
    st.session_state.cards = ["🂠"] * 3
    st.session_state.trophy_pos = random.randint(0, 2)
    st.session_state.first_choice = None
    st.session_state.flipped_card = None
    st.session_state.second_choice = None
    st.session_state.phase = "first_pick"
    st.session_state.game_over = False
    st.session_state.logged_this_round = False

def card_emojis():
    em = []
    for i in range(3):
        if st.session_state.phase == "reveal_all" or st.session_state.game_over:
            em.append("🏆" if i == st.session_state.trophy_pos else "❌")
        elif st.session_state.phase == "second_pick":
            em.append("❌" if i == st.session_state.flipped_card else "🂠")
        else:
            em.append("🂠")
    return em

def compute_switch_stay(first, second, trophy):
    if second == trophy:
        if first == second:
            return 0, 1
        else:
            return 1, 0
    return 0, 0

# ---------------- Page 1: Instructions + Name ----------------
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
        name_input = st.text_input("Enter your first and last name:")
        if st.button("✅ Confirm Name"):
            if name_input.strip() != "":
                st.session_state.player_name = name_input.strip()
                st.session_state.page = "trial"
                reset_game_state_for_trial()
                st.rerun()
            else:
                st.warning("Please enter a valid name.")
    else:
        # If name already present, allow continuing (edge-case if reloaded)
        if st.button("➡️ Continue to Trials"):
            st.session_state.page = "trial"
            reset_game_state_for_trial()
            st.rerun()
    st.stop()

# ---------------- Page 2: Trial Runs (Practice) ----------------
if st.session_state.page == "trial":
    st.title("🔁 Trial Runs (Practice)")

    # Top area: progress + Next / See Results button (appears only after reveal)
    st.write(f"Trial runs completed: **{st.session_state.trial_runs_done}/{TRIALS_REQUIRED}**")

    # show top Next / See Results only if current trial finished (game_over True)
    if st.session_state.game_over:
        # use columns so button sits at top-left visually
        col_top, _ = st.columns([1, 4])
        with col_top:
            if st.session_state.trial_runs_done < TRIALS_REQUIRED:
                if st.button("Next", key="trial_next_top"):
                    reset_game_state_for_trial()
                    st.rerun()
            else:
                # after TRIALS_REQUIRED trials, replace Next with See Results
                if st.button("📄 See Results", key="trial_see_results_top"):
                    st.session_state.page = "trial_summary"
                    st.rerun()

    # phase header
    if st.session_state.phase == "first_pick":
        st.subheader("Pick your first card")
    elif st.session_state.phase == "second_pick":
        st.subheader("Pick Again (same or switch)")

# ---------------- Card display & selection logic (trial and experiment) ----------------
if st.session_state.page in ["trial", "round1", "round2"]:
    cols = st.columns(3)
    emojis = card_emojis()
    for i, col in enumerate(cols):
        col.markdown(f"<h1 style='font-size:10rem; text-align:center'>{emojis[i]}</h1>", unsafe_allow_html=True)
        # Only show pick buttons when not in reveal state
        if not st.session_state.game_over and col.button("Pick", key=f"card_{i}", use_container_width=True):
            # First pick
            if st.session_state.phase == "first_pick":
                st.session_state.first_choice = i
                # pick a losing card that's not first_choice and not trophy
                losing_cards = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
                st.session_state.flipped_card = random.choice(losing_cards)
                st.session_state.phase = "second_pick"
                st.rerun()

            # Second pick (player decides to stay or switch)
            elif st.session_state.phase == "second_pick" and i != st.session_state.flipped_card:
                staying = (i == st.session_state.first_choice)
                cost = 0
                # Only apply costs in real experiment pages (round1 / round2)
                if st.session_state.page != "trial":
                    # Round1: switching costs 10
                    if st.session_state.current_round_set == 1 and not staying:
                        cost = 10
                    # Round2: staying costs 10
                    elif st.session_state.current_round_set == 2 and staying:
                        cost = 10
                    # Check funds
                    if st.session_state.points < cost:
                        st.warning("⚠️ You don’t have enough points for this action!")
                        st.stop()
                    # Deduct cost immediately
                    st.session_state.points -= cost

                st.session_state.second_choice = i
                st.session_state.phase = "reveal_all"
                st.session_state.game_over = True
                st.rerun()

# ---------------- Display results after a trial/trial-experiment selection ----------------
if st.session_state.game_over:
    first = st.session_state.first_choice
    second = st.session_state.second_choice
    trophy = st.session_state.trophy_pos
    won = (second == trophy)
    stayed = (first == second)
    switch_win, stay_win = compute_switch_stay(first, second, trophy)

    # --- TRIAL behavior (advice only on loss) ---
    if st.session_state.page == "trial":
        if won:
            st.success("🎉 You found the correct card!")
        else:
            st.error("❌ You picked the wrong card.")
            # advice for both loss-by-stay and loss-by-switch
            if first == trophy and second != trophy:
                st.info("💡 You should have stayed to win.")
            elif first != trophy and second != trophy:
                st.info("💡 You should have switched to win.")

        # log the trial once
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
            st.session_state.trial_log = pd.concat([st.session_state.trial_log, new_row], ignore_index=True)
            st.session_state.trial_runs_done += 1
            st.session_state.logged_this_round = True

    # --- REAL EXPERIMENT behavior (Round1 / Round2) ---
    else:
        # compute lost by cost (we deducted cost already), compute win bonus
        bonus = 100 if won else 0
        # compute lost_points for display: depends on round rule
        if st.session_state.current_round_set == 1:
            # switch cost in round1
            lost_points = 10 if (not stayed) else 0
        else:
            # round2: stay cost
            lost_points = 10 if stayed else 0

        # award bonus immediately (only once)
        if not st.session_state.logged_this_round:
            st.session_state.points += bonus

        st.markdown(f"**You won +{bonus} points and lost −{lost_points} points this round.**")

        # log experiment trial once
        if not st.session_state.logged_this_round:
            round_number = st.session_state.experiment_round + 1  # 1-based indexing for log clarity
            new_row = pd.DataFrame([{
                "round_number": round_number,
                "first_choice": first,
                "flipped_card": st.session_state.flipped_card,
                "second_choice": second,
                "trophy_card": trophy,
                "result": won,
                "phase_type": st.session_state.current_round_set,
                "points_after_round": st.session_state.points,
                "switch_win": switch_win,
                "stay_win": stay_win
            }])
            st.session_state.experiment_log = pd.concat([st.session_state.experiment_log, new_row], ignore_index=True)
            st.session_state.experiment_round += 1
            st.session_state.logged_this_round = True

    # ---------- TOP Next / See Results button (so it's always at top, visible after reveal) ----------
    if st.session_state.page == "trial":
        # Trial top buttons already handled in trial page rendering above, but keep guard here
        pass
    else:
        # For real experiment pages, show Next at top after reveal
        col_top, _ = st.columns([1, 4])
        with col_top:
            # If still within current round (less than 3 trials completed in this round set)
            # Determine overall completed in current round set:
            # If current_round_set==1, experiments 0..2 are round1; if >=3 then round1 done.
            if st.session_state.current_round_set == 1:
                completed_in_round_set = st.session_state.experiment_round  # counts from 0 upward but corresponds overall
                # after 3 completed (i.e., experiment_round >=3) we will move to round2 instructions
                show_next_label = "Next"
                if st.button("Next", key="exp_next_top"):
                    # if finished round1 (3 trials), navigate to round2 instructions
                    if st.session_state.experiment_round >= TRIALS_PER_ROUND:
                        st.session_state.page = "round2_instr"
                        reset_game_state_for_trial()
                        st.rerun()
                    else:
                        reset_game_state_for_trial()
                        st.rerun()
            else:
                # current_round_set == 2
                if st.button("Next", key="exp_next_top2"):
                    # if finished all experiment trials (6 completed), go to final summary
                    if st.session_state.experiment_round >= (TRIALS_PER_ROUND * 2):
                        st.session_state.page = "summary"
                        st.rerun()
                    else:
                        reset_game_state_for_trial()
                        st.rerun()

# ---------------- Page: Trial Summary ----------------
if st.session_state.page == "trial_summary":
    st.title("📄 Trial Summary")
    st.write(f"Trials completed: **{st.session_state.trial_runs_done}**")
    total_switch_wins = int(st.session_state.trial_log['switch_win'].sum())
    total_stay_wins = int(st.session_state.trial_log['stay_win'].sum())
    total_wins = int(st.session_state.trial_log['result'].sum())
    st.write(f"Wins by switching: **{total_switch_wins}**")
    st.write(f"Wins by staying: **{total_stay_wins}**")
    st.write(f"Total wins: **{total_wins}**")

    st.subheader("Trial Log")
    st.dataframe(st.session_state.trial_log, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Another 10 Trial Rounds"):
            st.session_state.trial_runs_done = 0
            st.session_state.trial_log = pd.DataFrame(columns=st.session_state.trial_log.columns)
            st.session_state.page = "trial"
            reset_game_state_for_trial()
            st.rerun()
    with col2:
        if st.button("🚀 Go to Real Experiment"):
            st.session_state.page = "round1_instr"
            st.rerun()

# ---------------- Page: Round 1 Instructions ----------------
if st.session_state.page == "round1_instr":
    st.title("🎯 Round 1 Instructions")
    st.write("""
Now we add the point system for the real experiment.

- You start with **50 points**.
- Each correct card gives **+100 points**.
- **Switching** after the reveal costs **10 points** in Round 1.
- Staying is free in Round 1.
""")
    if st.button("✅ I understand, start Round 1"):
        # ensure points are at least 50 (if they came from trial set, keep points as is or set to 50)
        # requirement: start real experiment with 50 points -> reset to 50
        st.session_state.points = 50
        st.session_state.current_round_set = 1
        st.session_state.experiment_round = 0
        st.session_state.page = "round1"
        reset_game_state_for_trial()
        st.rerun()

# ---------------- Page: Round 1 (3 Trials) ----------------
if st.session_state.page == "round1":
    # top: show current points and header depending on phase
    st.title(f"Round {st.session_state.experiment_round+1}/{TRIALS_PER_ROUND * 2}:")
    st.markdown(f"### 💰 Current Score: {st.session_state.points} points")
    if st.session_state.phase == "first_pick":
        st.subheader("Pick your first card")
    elif st.session_state.phase == "second_pick":
        st.subheader("Pick Again (same or switch)")

# ---------------- Page: Round 2 Instructions ----------------
if st.session_state.page == "round2_instr":
    st.title("🎯 Round 2 Instructions")
    st.write("""
Round 2 rules:

- Each correct card gives **+100 points**.
- **Staying** with your first choice now costs **10 points**.
- Switching is free.
""")
    if st.button("✅ I understand, start Round 2"):
        st.session_state.current_round_set = 2
        # do not reset points (carry over)
        st.session_state.page = "round2"
        reset_game_state_for_trial()
        st.rerun()

# ---------------- Page: Round 2 (3 Trials) ----------------
if st.session_state.page == "round2":
    st.title(f"Round {st.session_state.experiment_round+1}/{TRIALS_PER_ROUND * 2}:")
    st.markdown(f"### 💰 Current Score: {st.session_state.points} points")
    if st.session_state.phase == "first_pick":
        st.subheader("Pick your first card")
    elif st.session_state.phase == "second_pick":
        st.subheader("Pick Again (same or switch)")

# ---------------- Page: Final Summary (and GitHub upload) ----------------
if st.session_state.page == "summary":
    st.title("🎉 Experiment Complete!")
    st.markdown(f"### 💰 Final points: {st.session_state.points} points")
    total_correct = int(st.session_state.experiment_log['result'].sum())
    st.write(f"✅ Total correct picks: **{total_correct}**")
    total_switch_wins = int(st.session_state.experiment_log['switch_win'].sum())
    total_stay_wins = int(st.session_state.experiment_log['stay_win'].sum())
    st.write(f"Wins by switching: **{total_switch_wins}**")
    st.write(f"Wins by staying: **{total_stay_wins}**")

    st.subheader("Experiment Log")
    st.dataframe(st.session_state.experiment_log, use_container_width=True)

    # Try upload to GitHub
    try:
        token = st.secrets["GITHUB_TOKEN"]
        g = Github(token)
        repo = g.get_repo("joojoosch/monty-hall-card-edition")
        csv_data = st.session_state.experiment_log.to_csv(index=False)
        path = f"player_logs/{st.session_state.player_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        repo.create_file(path, f"Add results for {st.session_state.player_name}", csv_data)
        st.success(f"Results saved to GitHub as {path}")
    except Exception as e:
        st.error(f"⚠️ Couldn't save to GitHub: {e}")

    # Optionally offer a download as well
    st.download_button("💾 Download CSV", st.session_state.experiment_log.to_csv(index=False), file_name=f"{st.session_state.player_name}_experiment_log.csv")




