"""Minimal Streamlit Web Application for Kuku Promo Discovery.

Accepts uploaded screenplay files or local folder, runs the promo discovery pipeline,
and presents ranked promos with conversion rationales and exact cutpoints.
"""

from __future__ import annotations

import json
import os
import tempfile
import streamlit as st

from run import process_single_episode
from src.judge import rank_survivors
from src.llm import get_usage_summary, reset_usage_summary
from src.parser import parse_all_episodes, parse_episode_text

st.set_page_config(page_title="Kuku Promo Finder", layout="wide")

st.title("🎬 Kuku Microdrama Promo Discovery")
st.caption("AI-assisted promotional cutpoint extractor for 20-60s TikTok, Reels & Shorts ads")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    provider = st.selectbox(
        "LLM Provider",
        options=["mock", "gemini", "openai", "anthropic"],
        index=0,
        help="Select AI model provider (or 'mock' for offline testing).",
    )

    api_key = st.text_input(
        f"{provider.capitalize()} API Key",
        type="password",
        help="Optional if already set in environment variables.",
    )
    if api_key:
        if provider == "gemini":
            os.environ["GEMINI_API_KEY"] = api_key
        elif provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key

    input_mode = st.radio("Script Input Source", ["Upload Screenplays", "Local Directory"], index=0)

episodes = []

if input_mode == "Upload Screenplays":
    uploaded_files = st.file_uploader(
        "Upload Screenplay Files (.txt)",
        type=["txt"],
        accept_multiple_files=True,
        help="Upload one or multiple episode script files.",
    )
    if uploaded_files:
        for uf in uploaded_files:
            content = uf.read().decode("utf-8")
            ep_data = parse_episode_text(content, filename=uf.name)
            episodes.append(ep_data)
        episodes.sort(key=lambda x: x["episode"])
        st.success(f"Loaded {len(episodes)} screenplay(s) from upload.")
else:
    local_dir = st.text_input(
        "Directory Path",
        value="assets/I Married a Broken Soldier. He was a Duke",
    )
    if os.path.isdir(local_dir):
        if st.button("Load Local Files"):
            episodes = parse_all_episodes(local_dir)
            st.session_state["loaded_episodes"] = episodes
            st.success(f"Loaded {len(episodes)} episodes.")
        elif "loaded_episodes" in st.session_state:
            episodes = st.session_state["loaded_episodes"]
    else:
        st.warning("Please provide a valid local directory path or use 'Upload Screenplays'.")

if episodes:
    st.markdown(f"**Loaded Episodes:** `{len(episodes)}` | **Total Beats:** `{sum(len(e['beats']) for e in episodes)}`")

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        run_clicked = st.button("🚀 Discover Promos", type="primary")

    if run_clicked:
        reset_usage_summary()
        progress_bar = st.progress(0)
        status_text = st.empty()

        all_outputs = []
        survivors = []

        for idx, ep in enumerate(episodes):
            status_text.text(f"Processing Episode {ep['episode']} ({idx + 1}/{len(episodes)})...")
            res = process_single_episode(ep, provider=provider)
            all_outputs.append(res)
            for c in res["candidates"]:
                if c.get("verdict") == "PASS":
                    survivors.append(c)
            progress_bar.progress((idx + 1) / len(episodes))

        status_text.text("Ranking top survivor clips...")
        ranked = rank_survivors(survivors, provider=provider)

        st.session_state["results"] = {
            "all_outputs": all_outputs,
            "ranked": ranked,
            "usage": get_usage_summary(),
        }
        status_text.text("✅ Discovery complete!")

if "results" in st.session_state:
    results = st.session_state["results"]
    ranked_promos = results["ranked"]
    all_outputs = results["all_outputs"]
    usage = results["usage"]

    st.divider()
    st.subheader(f"🏆 Top Ranked Promos ({len(ranked_promos)} Found)")

    top_n = min(15, len(ranked_promos))
    for idx, p in enumerate(ranked_promos[:top_n], 1):
        with st.container(border=True):
            st.markdown(
                f"### #{idx}: Episode {p['episode']} (`{p['start_formatted']} - {p['end_formatted']}` | {p['duration']:.1f}s)"
            )
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.metric("Composite Rating", f"{p.get('composite_score', 8.5):.1f} / 10")
            with col2:
                st.metric("Hook Beat", p["hook_beat_id"])
            with col3:
                st.metric("Cliffhanger Beat", p["cliffhanger_beat_id"])

            st.markdown(f"**🪝 Hook (0-3s):** *\"{p.get('hook_text', '')}\"*")
            st.markdown(f"**⚡ Cliffhanger Cut:** *\"{p.get('cliffhanger_text', '')}\"*")
            st.markdown(
                f"**🎯 Why it Works:** {p.get('rank_rationale') or p.get('judge_rationale') or p.get('rationale', '')}"
            )
            st.caption(f"**Campaign & Spoiler Strategy:** {p.get('spoiler_note', 'Early series asset.')}")

            if p.get("repairs"):
                st.info(f"**Automated Repairs Applied:** {'; '.join(p['repairs'])}")

    # Downloads
    st.divider()
    st.download_button(
        label="📥 Download Full Promos JSON",
        data=json.dumps(all_outputs, indent=2),
        file_name="kuku_promos_full.json",
        mime="application/json",
    )

    with st.expander("📊 LLM Usage & Cost Telemetry"):
        st.json(usage)
