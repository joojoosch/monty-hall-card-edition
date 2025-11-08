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
if "email" not in st.session_state:
    st.session_state.email = ""  # optional

# page values: instructions, trial, trial_summary, round1_instr, round1, round2_instr, round2, summary
if "page" not in st.session_state:
    st.session_state.page = "instructions"

# Trials
if "trial_runs_done" not in st.session_state:
    st.session_state.trial_runs_done = 0
if "trial_log" not in st.session_state:
    st.session_state.trial_log = pd.DataFrame(columns=[
        "trial_number", "first_choice", "flipped_card", "second_choice",
        "trophy_card", "result", "switch_win", "stay_win", "email"
    ])

# Experiment
if "experiment_round" not in st.session_state:
    st.session_state.experiment_round = 0  # number of completed experiment trials (0..6)
if "current_round_set" not in st.session_state:
    st.session_state.current_round_set = 1  # 1 or 2
if "experiment_log" not in st.session_state:
    st.session_state.experiment_log = pd.DataFrame(columns=[
        "round_number", "first_choice", "flipped_card", "second_choice",
        "trophy_card", "result", "phase_type", "points_after_round",
        "switch_win", "stay_win", "email"
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
    st.session_state.points = 50  # start points when real experiment begins
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

# Utility: current trial index within current experiment round set (1..3)
def current_trial_index_in_set():
    # experiment_round counts completed trials (0..6). For display, we want 1..3 within current round set.
    completed = st.session_state.experiment_round
    idx = (completed % TRIALS_PER_ROUND) + 1
    return idx

# ---------------- Page 1: Instructions + Name + optional email ----------------
if st.session_state.page == "instructions":
    # clear any leftover game_over state
    reset_game_state_for_trial()

    st.title("🏆 Card Game Experiment")
    st.write("""
You will be shown three cards and your goal is to find the trophy 🏆 behind one of them.

1️⃣ Choose a card.  
2️⃣ One of the NOT chosen cards will be revealed.  
3️⃣ Choose to stick with your first choice or switch to the other remaining card.  
The winning trophy card is then revealed!
""")

    name_input = st.text_input("Enter your first and last name:", value=st.session_state.player_name or "")
    email_input = st.text_input("(Optional) Enter your email to be eligible for a prize if you're a top scorer:", value=st.session_state.email or "")

    if st.button("✅ Confirm Name and Continue"):
        if name_input.strip() == "":
            st.warning("Please enter a valid name.")
        else:
            st.session_state.player_name = name_input.strip()
            st.session_state.email = email_input.strip()
            # move to trials
            st.session_state.page = "trial"
            reset_game_state_for_trial()
            st.rerun()
    st.stop()

# ---------------- Page 2: Trial Runs (Practice) ----------------
if st.session_state.page == "trial":
    st.title("🔁 Trial Runs (Practice)")
    # Top area: progress + Next / See Results (top, visible after reveal)
    st.write(f"Trial runs completed: **{st.session_state.trial_runs_done}/{TRIALS_REQUIRED}**")

    # If the last trial finished (game_over), show top Next or See Results
    if st.session_state.game_over:
        col_top, _ = st.columns([1, 4])
        with col_top:
            if st.session_state.trial_runs_done < TRIALS_REQUIRED:
                if st.button("Next", key="trial_next_top"):
                    reset_game_state_for_trial()
                    st.rerun()
            else:
                # After exactly TRIALS_REQUIRED completed, show See Results (only after 10th finished)
                if st.button("📄 See Results", key="trial_see_results_top"):
                    st.session_state.page = "trial_summary"
                    st.rerun()

    # Phase header below top button
    if st.session_state.phase == "first_pick":
        st.subheader("Pick your first card")
    elif st.session_state.phase == "second_pick":
        st.subheader("Pick Again (same or switch)")

# ---------------- Card display & logic (Trials & Experiment) ----------------
if st.session_state.page in ["trial", "round1", "round2"]:
    # For real experiment pages, show header + points above cards (Round pages only)
    if st.session_state.page == "round1":
        # show trial index 1..3 and score above cards
        idx = current_trial_index_in_set()
        st.title(f"Round 1 — Trial {idx}/{TRIALS_PER_ROUND}")
        st.markdown(f"### 💰 Current Score: {st.session_state.points} points")
    elif st.session_state.page == "round2":
        idx = current_trial_index_in_set()
        st.title(f"Round 2 — Trial {idx}/{TRIALS_PER_ROUND}")
        st.markdown(f"### 💰 Current Score: {st.session_state.points} points")

    cols = st.columns(3)
    emojis = card_emojis()
    for i, col in enumerate(cols):
        col.markdown(f"<h1 style='font-size:10rem; text-align:center'>{emojis[i]}</h1>", unsafe_allow_html=True)
        # only allow picking when not game_over and not clicking revealed card
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
                # apply cost only in real experiment pages
                if st.session_state.page != "trial":
                    if st.session_state.current_round_set == 1 and not staying:
                        cost = 10
                    elif st.session_state.current_round_set == 2 and staying:
                        cost = 10
                    if st.session_state.points < cost:
                        st.warning("⚠️ You don’t have enough points for this action!")
                        st.stop()
                    # deduct cost immediately
                    st.session_state.points -= cost

                st.session_state.second_choice = i
                st.session_state.phase = "reveal_all"
                st.session_state.game_over = True
                st.rerun()

# ---------------- Display results area (below cards) ----------------
if st.session_state.game_over:
    first = st.session_state.first_choice
    second = st.session_state.second_choice
    trophy = st.session_state.trophy_pos
    won = (second == trophy)
    stayed = (first == second)
    switch_win, stay_win = compute_switch_stay(first, second, trophy)

    # TRIAL behavior (advice only on loss)
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
                "stay_win": stay_win,
                "email": st.session_state.email
            }])
            st.session_state.trial_log = pd.concat([st.session_state.trial_log, new_row], ignore_index=True)
            st.session_state.trial_runs_done += 1
            st.session_state.logged_this_round = True

    # REAL experiment behavior
    else:
        # We already deducted cost at selection time. Now award bonus if won (once).
        bonus = 100 if won else 0
        # compute lost_points for message display
        if st.session_state.current_round_set == 1:
            lost_points = 10 if (not stayed) else 0
        else:
            lost_points = 10 if stayed else 0

        if not st.session_state.logged_this_round:
            st.session_state.points += bonus

        st.markdown(f"**You won +{bonus} points and lost −{lost_points} points this round.**")

        # log experiment trial once
        if not st.session_state.logged_this_round:
            round_number = st.session_state.experiment_round + 1
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
                "stay_win": stay_win,
                "email": st.session_state.email
            }])
            st.session_state.experiment_log = pd.concat([st.session_state.experiment_log, new_row], ignore_index=True)
            st.session_state.experiment_round += 1
            st.session_state.logged_this_round = True

    # TOP Next button for experiment pages (placed at top logically but here we ensure appropriate navigation)
    # For trial page the top button is already handled in that page's block.
    if st.session_state.page in ["round1", "round2"]:
        # Show Next at top so user can easily continue (we re-render page, but here we handle navigation)
        col_top, _ = st.columns([1, 4])
        with col_top:
            if st.button("Next", key=f"exp_next_top_{st.session_state.page}"):
                # If finished Round 1 (3 trials) and currently in round1 -> go to round2 instructions
                if st.session_state.current_round_set == 1 and st.session_state.experiment_round >= TRIALS_PER_ROUND:
                    st.session_state.page = "round2_instr"
                    reset_game_state_for_trial()
                    st.rerun()
                # If in round2 and finished all experiment trials -> summary
                elif st.session_state.current_round_set == 2 and st.session_state.experiment_round >= (TRIALS_PER_ROUND * 2):
                    st.session_state.page = "summary"
                    st.rerun()
                else:
                    # continue next trial in same round set
                    # if we've just completed a trial and need to switch round set number when moving to round2, that is handled above
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
    # ensure no lingering "You won..." / game over display
    reset_game_state_for_trial()
    st.title("🎯 Round 1 Instructions")
    st.write("""
Now we add the point system for the real experiment.

- You start with **50 points**.
- Each correct card gives **+100 points**.
- **Switching** after the reveal costs **10 points** in Round 1.
- Staying is free in Round 1.
""")
    if st.button("✅ I understand, start Round 1"):
        st.session_state.points = 50
        st.session_state.current_round_set = 1
        st.session_state.experiment_round = 0
        st.session_state.page = "round1"
        reset_game_state_for_trial()
        st.rerun()

# ---------------- Page: Round 1 gameplay ----------------
if st.session_state.page == "round1":
    # top header & score handled in card rendering block above
    pass

# ---------------- Page: Round 2 Instructions ----------------
if st.session_state.page == "round2_instr":
    # clear any lingering game_over
    reset_game_state_for_trial()
    st.title("🎯 Round 2 Instructions")
    st.write("""
Round 2 rules:

- Each correct card gives **+100 points**.
- **Staying** with your first choice now costs **10 points**.
- Switching is free.
""")
    if st.button("✅ I understand, start Round 2"):
        st.session_state.current_round_set = 2
        # keep points as-is (carry over)
        st.session_state.page = "round2"
        reset_game_state_for_trial()
        st.rerun()

# ---------------- Page: Round 2 gameplay ----------------
if st.session_state.page == "round2":
    # top header & score handled in card rendering block above
    pass

# ---------------- Page: Final Summary & GitHub upload ----------------
if st.session_state.page == "summary":
    # ensure no Next button or 'you won' text shown here -- clean summary
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

    # Upload to GitHub
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

   
