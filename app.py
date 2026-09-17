"""Vibe Coder - Multi-Agent Coding Orchestrator with Streamlit UI."""
import streamlit as st
import sys
import os
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import run_pipeline, save_results, get_available_models

st.set_page_config(page_title="Vibe Coder", page_icon="\U0001f3b5", layout="wide")

st.title("\U0001f3b5 Vibe Coder")
st.caption("Multi-Agent AI Coding Pipeline: Planner \u2192 Coder \u2192 Reviewer")

# ── Sidebar ──
with st.sidebar:
    st.header("\U0001f916 Agent Status")
    models = get_available_models()
    if models:
        st.success(f"{len(models)} models available")
        for m in models:
            st.text(f"  \u2022 {m}")
    else:
        st.error("No Ollama models found!")

    st.divider()
    st.header("\U0001f4c1 History")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
    if os.path.exists(output_dir):
        files = sorted(os.listdir(output_dir), reverse=True)[:10]
        for f in files:
            st.text(f"\u2022 {f}")
    else:
        st.text("No outputs yet")

# ── Main Interface ──
st.markdown("---")
st.markdown("### What do you want to build?")

user_request = st.text_area(
    "Describe your app or feature:",
    placeholder="Example: Build a command-line todo list app with add, remove, list, and mark-done features. Store tasks in a JSON file.",
    height=120,
)

col1, col2 = st.columns([1, 4])
with col1:
    run_button = st.button("\U0001f680 Build It", type="primary", use_container_width=True)

if run_button and user_request.strip():
    if not models:
        st.error("No Ollama models available. Run `ollama pull mistral` to get started.")
    else:
        # Create status containers for each agent
        st.markdown("---")
        st.markdown("### \U0001f3ad Agent Pipeline")

        planner_container = st.container()
        coder_container = st.container()
        reviewer_container = st.container()

        containers = {
            "planner": planner_container,
            "coder": coder_container,
            "reviewer": reviewer_container,
        }
        labels = {
            "planner": "\U0001f4d0 Planner (Architect)",
            "coder": "\U0001f4bb Coder (Developer)",
            "reviewer": "\U0001f50d Reviewer (Safety Engineer)",
        }

        # Run pipeline with live status updates
        status_placeholders = {}
        output_placeholders = {}

        for agent_name, container in containers.items():
            with container:
                st.subheader(labels[agent_name])
                status_placeholders[agent_name] = st.empty()
                output_placeholders[agent_name] = st.empty()
                status_placeholders[agent_name].info("\u23f3 Waiting...")

        def progress_callback(agent_name, status, output):
            if status == "running":
                status_placeholders[agent_name].warning(f"\u26a1 Running...")
            elif status == "done":
                if output and output.startswith("ERROR"):
                    status_placeholders[agent_name].error(f"\u274c Failed")
                else:
                    status_placeholders[agent_name].success(f"\u2705 Complete")
                if output:
                    output_placeholders[agent_name].code(output, language="python")

        with st.spinner("Pipeline running... agents take turns to protect your system RAM"):
            results = run_pipeline(user_request, progress_callback=progress_callback)

        # Save results
        st.markdown("---")
        if "error" in results:
            st.error(results["error"])
        else:
            filepath = save_results(results)
            st.success(f"\u2705 Pipeline complete in {results.get('total_time', '?')}s")
            st.caption(f"Saved to: `{filepath}`")

            # Show final code prominently
            reviewer_output = results.get("agents", {}).get("reviewer", {}).get("output", "")
            if reviewer_output and not reviewer_output.startswith("ERROR"):
                st.markdown("### \U0001f3c6 Final Reviewed Code")
                st.code(reviewer_output, language="python")

                # Copy button
                st.download_button(
                    "\U0001f4cb Download Code",
                    data=reviewer_output,
                    file_name="vibe_output.py",
                    mime="text/plain",
                )

elif run_button:
    st.warning("Please describe what you want to build first.")
