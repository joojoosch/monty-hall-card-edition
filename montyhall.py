import streamlit as st
import random

st.set_page_config(page_title="Monty Hall - Card Edition", page_icon="🏆", layout="centered")

st.title("🏆 Monty Hall Problem — Card Edition")
st.write("""
Pick one of the **three cards** — one hides a 🏆 **trophy (win)**, the other two hide ❌.  
After your choice, Monty flips one losing card and asks if you want to **switch**.
""")

cards = ["🂠", "🂠", "🂠"]
trophy_position = random.randint(0, 2)
chosen = st.radio("Choose a card:", [1, 2, 3], horizontal=True)

if st.button("Flip one losing card"):
    losing_options = [i for i in range(3) if i != (chosen - 1) and i != trophy_position]
    monty_flips = random.choice(losing_options)
    st.write(f"Monty flips card **{monty_flips + 1}** revealing ❌")

    remaining = [i for i in range(3) if i not in [(chosen - 1), monty_flips]][0]
    switch = st.radio("Do you want to switch?", ["Stay", "Switch"], horizontal=True)

    final_choice = remaining if switch == "Switch" else (chosen - 1)
    revealed_cards = ["🏆" if i == trophy_position else "❌" for i in range(3)]

    st.write("Final result:")
    cols = st.columns(3)
    for i in range(3):
        with cols[i]:
            st.metric(f"Card {i+1}", revealed_cards[i])

    if final_choice == trophy_position:
        st.success("🎉 You found the 🏆 trophy — you win!")
        st.balloons()
    else:
        st.error("❌ You picked a losing card.")

st.divider()

st.header("📊 Run automatic simulations")
num_sims = st.slider("Number of simulations", 100, 100000, 1000, step=100)

def monty_hall(simulations, switch=True):
    wins = 0
    for _ in range(simulations):
        trophy = random.randint(0, 2)
        choice = random.randint(0, 2)
        losing = [i for i in range(3) if i != choice and i != trophy]
        monty_flips = random.choice(losing)
        if switch:
            choice = [i for i in range(3) if i not in [choice, monty_flips]][0]
        if choice == trophy:
            wins += 1
    return wins / simulations

if st.button("Run simulation"):
    switch_rate = monty_hall(num_sims, switch=True)
    stay_rate = monty_hall(num_sims, switch=False)
    st.metric("Winning % when Switching", f"{switch_rate*100:.2f}%")
    st.metric("Winning % when Staying", f"{stay_rate*100:.2f}%")
    st.info("📈 Switching should win about **66.7%** of the time.")

