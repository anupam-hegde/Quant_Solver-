import streamlit as st
import time
import json
from orchestrator import Orchestrator

st.set_page_config(page_title="Team DeepMind", page_icon="", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .agent-card { border: 1px solid #444; padding: 15px; border-radius: 10px; background-color: #1E1E1E; }
    .success-badge { color: #4CAF50; font-weight: bold; }
    .fail-badge { color: #FF5252; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("Team DeepMinds: Aptitude Generator")
st.caption("Autonomous Generation • Adversarial Validation • Live Deployment")

# --- STATE ---
if "orch" not in st.session_state:
    st.session_state.orch = Orchestrator()
if "stats" not in st.session_state:
    st.session_state.stats = st.session_state.orch.stats
if "research_done" not in st.session_state:
    st.session_state.research_done = False

# --- SIDEBAR (LEFT COLUMN) ---
with st.sidebar:
    st.header("⚙️ Mission Control")
    
    # --- SOURCE SELECTION ---
    st.markdown("### 1. Research Source")
    source_mode = st.radio("Select Context:", ["Embedded Reference (Default)", "Upload Custom PDF"])
    
    uploaded_file = None
    if source_mode == "Upload Custom PDF":
        uploaded_file = st.file_uploader("Upload Math PDF", type=["pdf"])
        if uploaded_file:
            st.success("PDF Loaded! Ready to research.")
            st.session_state.research_done = False
    
    st.divider()
    target_q = st.slider("Target Questions", 1, 50, 3)
    
    if st.button("🧹 Clear Stats"):
        st.session_state.stats = {
            "SUCCESS": 0, "HALLUCINATION": 0,
            "CONSENSUS_FAILURE": 0, "PARSING_ERROR": 0, "DUPLICATE": 0
        }
        st.session_state.research_done = False
    
    st.divider()
    with st.expander("📊 System Health"):
        metric_ph = st.empty()
        dup_metric = st.empty()
        chart_ph = st.empty()

# --- MAIN LAYOUT ---
st.subheader("📝 Live Operations")
start_btn = st.button("🚀 Start Generation Loop")
q_display = st.container()

if start_btn:
    if source_mode == "Upload Custom PDF" and not uploaded_file:
        st.error("⚠️ Please upload a PDF file first!")
        st.stop()

    # --- PHASE 1: RESEARCH ---
    if not st.session_state.research_done:
        with st.spinner("🕵️ Agent is analyzing source material..."):
            # ✅ PASS FILE TO ORCHESTRATOR
            findings = st.session_state.orch.perform_research(custom_file=uploaded_file)
            st.session_state.research_done = True
            with st.expander("View Research Findings"):
                st.json(findings)
    
    # --- PHASE 2: GENERATION ---
    success_count = 0
    attempt = 0
    progress_bar = st.progress(0)
    
    while success_count < target_q:
        attempt += 1
        with st.spinner(f"Attempt {attempt}: The Council is deliberating..."):
            if attempt == 1:
                # ✅ INITIALIZE WITH FILE
                st.session_state.orch.init_generator(custom_file=uploaded_file)

            result_data = st.session_state.orch.run_loop()
            st.session_state.stats = st.session_state.orch.stats
            
            # Update Metrics
            with metric_ph.container():
                c1, c2 = st.columns(2)
                c1.metric("Success", st.session_state.stats["SUCCESS"])
                c2.metric("Errors", st.session_state.stats["HALLUCINATION"] + st.session_state.stats["CONSENSUS_FAILURE"])
            
            dup_metric.metric("Duplicates Avoided", st.session_state.stats["DUPLICATE"])
            
            # --- VISUALIZATION (Standard Bar Chart) ---
            with chart_ph.container():
                st.bar_chart(st.session_state.stats)

            # --- RESULT HANDLING ---
            if result_data and "story" in result_data:
                success_count += 1
                progress_bar.progress(success_count / target_q)
                
                with q_display:
                    cat = result_data.get('category', 'General')
                    diff = result_data.get('difficulty', 'Medium')
                    color = "green" if diff == "Easy" else "orange" if diff == "Medium" else "red"
                    
                    st.markdown(f"### {cat} :grey[[{diff}]]")
                    st.info(f"**Q:** {result_data['story']}")
                    
                    st.markdown("#### 🏛️ The Council's Verdict")
                    tab1, tab2, tab3 = st.tabs(["🤖 Solver A (Code)", "🧠 Solver B (Logic)", "🕵️ Solver C (Skeptic)"])
                    
                    with tab1:
                        st.code(result_data['solver_a_raw'], language="python")
                        if result_data.get('equation_visual'):
                            st.latex(result_data['equation_visual'])
                    with tab2:
                        st.markdown(f"> {result_data['solver_b_raw']}")
                    with tab3:
                        st.warning(result_data['solver_c_raw'])
                    
                    st.success("✅ Validated & Deployed")
                    st.divider()
            
            elif result_data and "failure_type" in result_data:
                fail_type = result_data["failure_type"]
                reason = result_data["reason"]
                st.error(f"❌ Attempt {attempt} Rejected: {fail_type}")
                if reason:
                    with st.expander("Details"): st.text(reason)
            else:
                st.toast(f"Attempt {attempt} Skipped: {result_data.get('failure_type', 'Unknown')}", icon="⚠️")
            
            time.sleep(1)

    st.balloons()
    st.success("🎉 Batch Generation Complete!")
