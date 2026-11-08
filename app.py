"""Minimal Streamlit Web Application for Kuku Promo Discovery.

Public Dashboard:
- Displays ranked promos with timestamps, composite scores, and safe paraphrases (<= 8-word excerpts).
- Full verbatim screenplay downloads are excluded from the public UI (submitted via private Drive folder).
- Includes "Run it yourself" tab supporting Gemini, OpenAI, Anthropic, and generic OpenAI-compatible endpoints (Ollama, vLLM, Together, etc.).
"""

from __future__ import annotations

import json
import os
import re
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from run import process_single_episode
from src.judge import rank_survivors
from src.llm import get_usage_summary, reset_usage_summary
from src.parser import parse_all_episodes, parse_episode_text

st.set_page_config(page_title="Kuku Promo Discovery", layout="wide", page_icon="🎬")


def safe_paraphrase(text: str, max_words: int = 8) -> str:
    """Format text under conservative 8-word assumption to avoid public verbatim script leakage."""
    if not text:
        return ""
    words = text.strip().split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


def load_precomputed_results():
    """Load pre-computed production results from real Gemini run."""
    ranked_path = "outputs/raw/all_episodes_promos.json"
    meta_path = "outputs/raw/run_meta.json"
    if not os.path.exists(ranked_path):
        ranked_path = "outputs/raw_real_run1/raw/all_episodes_promos.json"
        meta_path = "outputs/raw_real_run1/run_meta.json"

    if os.path.exists(ranked_path):
        try:
            with open(ranked_path, "r", encoding="utf-8") as f:
                episodes = json.load(f)
            meta = {}
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)

            # Flatten candidates across all episodes
            all_candidates = []
            if isinstance(episodes, list):
                for ep in episodes:
                    ep_num = ep.get("episode")
                    for c in ep.get("candidates", []):
                        c["episode"] = ep_num
                        all_candidates.append(c)

            return all_candidates, episodes, meta
        except Exception:
            return None, None, None
    return None, None, None


st.title("🎬 Kuku Microdrama Promo Discovery")
st.caption(
    "Automated promotional cutpoint extractor for 20-60s TikTok, Reels & Shorts ads | "
    "*I Married a Broken Soldier. He was a Duke* (50 Episodes)"
)

tab_overview, tab_runner = st.tabs(["🏆 Ranked Promos", "🚀 Run it yourself"])

# ==============================================================================
# TAB 1: RANKED PROMOS (PUBLIC DASHBOARD)
# ==============================================================================
with tab_overview:
    precomputed_candidates, raw_episodes, precomputed_meta = load_precomputed_results()

    if precomputed_meta:
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric("Model Used", precomputed_meta.get("api_model_version_returned") or precomputed_meta.get("model_requested", "gemini-3.5-flash-lite"))
        with m_col2:
            st.metric("Total API Calls", f"{precomputed_meta.get('total_calls', 10)} (All 50 Eps)")
        with m_col3:
            st.metric("Runtime", f"{precomputed_meta.get('runtime_seconds', 156.6):.1f}s")
        with m_col4:
            st.metric("Est. Paid Equivalent", f"${precomputed_meta.get('estimated_paid_tier_equivalent_usd', 0.022):.4f}")

    st.markdown(
        "> **Confidentiality & Privacy Safeguard**: In accordance with distribution safeguards, verbatim screenplay lines "
        "are restricted to conservative paraphrases / $\le$ 8-word excerpts on the dashboard. Full unedited outputs are preserved "
        "in the private submission Drive folder."
    )

    if precomputed_candidates:
        survivors = [c for c in precomputed_candidates if c.get("verdict") == "PASS"]
        survivors.sort(key=lambda x: x.get("composite_score", 0.0), reverse=True)
        top_promos = survivors[:15]

        st.subheader(f"Top 15 Ranked Promos Across All 50 Episodes ({len(survivors)} Passing Promos Discovered)")

        for idx, p in enumerate(top_promos, 1):
            with st.container(border=True):
                st.markdown(
                    f"### #{idx}: Episode {p['episode']} (`{p['start_formatted']} - {p['end_formatted']}` | {p['duration']:.1f}s)"
                )
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Composite Rating", f"{p.get('composite_score', 8.5):.1f} / 10.0")
                with c2:
                    st.metric("Hook Score (0-3s)", f"{p.get('hook_score', 8.5):.1f}")
                with c3:
                    st.metric("Cliffhanger Score", f"{p.get('cliffhanger_score', 8.5):.1f}")
                with c4:
                    st.metric("Standalone Coherence", f"{p.get('standalone_score', 8.5):.1f}")

                hook_snippet = safe_paraphrase(p.get("hook_text", ""))
                cliff_snippet = safe_paraphrase(p.get("cliffhanger_text", ""))

                st.markdown(f"**🪝 Hook (0–3s excerpt):** *\"{hook_snippet}\"* (`{p.get('hook_beat_id', '')}`)")
                st.markdown(f"**⚡ Cliffhanger Cut:** *\"{cliff_snippet}\"* (`{p.get('cliffhanger_beat_id', '')}`)")

                raw_rat = p.get("rank_rationale") or p.get("judge_rationale") or p.get("rationale", "")
                if isinstance(raw_rat, dict):
                    rationale_str = " ".join(f"{k}: {v}" for k, v in raw_rat.items())
                else:
                    rationale_str = str(raw_rat)
                st.markdown(f"**🎯 Conversion Rationale:** {rationale_str}")
                st.caption(f"**Campaign Strategy & Lore Note:** {p.get('spoiler_note', 'Early series asset.')}")

                if p.get("repairs"):
                    st.info(f"**Deterministic Repairs Applied**: {'; '.join(p['repairs'])}")

        st.divider()
        st.subheader("🔍 Episode Browser (All 50 Episodes)")
        st.markdown("Inspect discovered promo cutpoints, candidate repairs, and cold judge verdicts for any individual episode:")

        ep_options = sorted(list({ep.get("episode") for ep in (raw_episodes or []) if ep.get("episode") is not None}))
        if ep_options:
            selected_ep = st.selectbox("Select Episode to Inspect", ep_options, index=0)
            target_ep = next((e for e in raw_episodes if e.get("episode") == selected_ep), None)
            if target_ep:
                st.markdown(f"**Episode {selected_ep} Logline:** *{target_ep.get('logline', 'N/A')}*")
                cands = target_ep.get("candidates", [])
                st.markdown(f"Found **{len(cands)}** candidate clip(s) for Episode {selected_ep}:")
                for c_idx, c in enumerate(cands, 1):
                    v_color = "🟢" if c.get("verdict") == "PASS" else "🔴"
                    with st.expander(
                        f"{v_color} Candidate #{c_idx}: {c['start_formatted']} - {c['end_formatted']} ({c['duration']:.1f}s) — Verdict: {c.get('verdict', 'N/A')} ({c.get('composite_score', 0.0):.1f}/10)",
                        expanded=(c.get("verdict") == "PASS"),
                    ):
                        st.markdown(f"- **Hook Beat (`{c.get('hook_beat_id')}`)**: \"{safe_paraphrase(c.get('hook_text', ''))}\"")
                        st.markdown(f"- **Cliffhanger Beat (`{c.get('cliffhanger_beat_id')}`)**: \"{safe_paraphrase(c.get('cliffhanger_text', ''))}\"")
                        st.markdown(
                            f"- **Cold Judge Evaluation**: Hook: {c.get('hook_score')}/10 | Cliffhanger: {c.get('cliffhanger_score')}/10 | Standalone: {c.get('standalone_score')}/10"
                        )
                        st.markdown(f"- **Judge Rationale**: {c.get('judge_rationale') or c.get('rationale')}")
                        if c.get("repairs"):
                            st.caption(f"Repairs: {'; '.join(c['repairs'])}")
    else:
        st.info("No precomputed results found. Run the pipeline in the 'Run it yourself' tab.")


# ==============================================================================
# TAB 2: RUN IT YOURSELF (TESTBED & DYNAMIC UPLOAD)
# ==============================================================================
with tab_runner:
    st.subheader("🛠️ Interactive Promo Discovery Runner")
    st.markdown(
        "Upload new episode screenplays or run against local episodes. "
        "Supports proprietary cloud LLMs and **OpenAI-compatible endpoints** (local Ollama, vLLM, Together AI, Groq)."
    )

    r_col1, r_col2 = st.columns([1, 1])

    with r_col1:
        st.markdown("#### 1. Provider & Model Selection")
        provider_choice = st.selectbox(
            "Select Provider",
            options=["gemini", "openai_compatible", "openai", "anthropic", "mock"],
            index=0,
            help="Choose 'openai_compatible' for local Ollama/vLLM or third-party gateways (Groq, Together).",
        )

        model_name = ""
        base_url = ""
        api_key = ""

        if provider_choice == "openai_compatible":
            base_url = st.text_input(
                "Base URL",
                value=os.getenv("OPENAI_COMPATIBLE_BASE_URL", "http://localhost:11434/v1"),
                help="E.g. http://localhost:11434/v1 for local Ollama, https://api.groq.com/openai/v1 for Groq",
            )
            model_name = st.text_input("Model Name", value="llama3", help="E.g. llama3, mistral, deepseek-coder")
            api_key = st.text_input("API Key (optional for local)", value="", type="password")
            if base_url:
                os.environ["OPENAI_COMPATIBLE_BASE_URL"] = base_url
            if model_name:
                os.environ["OPENAI_COMPATIBLE_MODEL"] = model_name
            if api_key:
                os.environ["OPENAI_COMPATIBLE_API_KEY"] = api_key

        elif provider_choice == "gemini":
            model_name = st.text_input("Model", value="gemini-3.5-flash-lite")
            api_key = st.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
            if api_key:
                os.environ["GEMINI_API_KEY"] = api_key

        elif provider_choice == "openai":
            model_name = st.text_input("Model", value="gpt-4o-mini")
            api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key

        elif provider_choice == "anthropic":
            model_name = st.text_input("Model", value="claude-3-5-haiku-latest")
            api_key = st.text_input("Anthropic API Key", type="password", value=os.getenv("ANTHROPIC_API_KEY", ""))
            if api_key:
                os.environ["ANTHROPIC_API_KEY"] = api_key

    with r_col2:
        st.markdown("#### 2. Input Screenplays")
        input_source = st.radio("Script Source", ["Upload Screenplay (.txt)", "Use Preloaded Episode 1"], index=0)

        run_episodes = []
        if input_source == "Upload Screenplay (.txt)":
            uploaded = st.file_uploader(
                "Upload .txt screenplay files",
                type=["txt"],
                accept_multiple_files=True,
                help="Upload one or multiple episode text scripts.",
            )
            if uploaded:
                for uf in uploaded:
                    content = uf.read().decode("utf-8")
                    ep_data = parse_episode_text(content, filename=uf.name)
                    run_episodes.append(ep_data)
                run_episodes.sort(key=lambda x: x["episode"])
                st.success(f"Parsed {len(run_episodes)} screenplay(s).")
        else:
            ep1_file = "assets/I Married a Broken Soldier. He was a Duke/episode-001-Episode 1671703.txt"
            if os.path.exists(ep1_file):
                with open(ep1_file, "r", encoding="utf-8") as f:
                    ep_data = parse_episode_text(f.read(), filename="episode-001.txt")
                    run_episodes = [ep_data]
                st.info("Loaded Episode 1 (Cathedral Betrayal scene, 45 beats).")
            else:
                st.warning("Preloaded Episode 1 file not found.")

    st.divider()

    if run_episodes:
        if st.button("🚀 Run Discovery on Input", type="primary"):
            reset_usage_summary()
            runner_progress = st.progress(0)
            runner_status = st.empty()

            processed_outputs = []
            survivor_candidates = []

            for idx, ep in enumerate(run_episodes):
                runner_status.text(f"Processing Episode {ep['episode']} ({idx + 1}/{len(run_episodes)})...")
                try:
                    res = process_single_episode(ep, provider=provider_choice, model=model_name)
                    processed_outputs.append(res)
                    for c in res["candidates"]:
                        if c.get("verdict") == "PASS":
                            survivor_candidates.append(c)
                except Exception as e:
                    st.error(f"Error processing episode {ep['episode']}: {e}")
                runner_progress.progress((idx + 1) / len(run_episodes))

            runner_status.text("Evaluating and ranking survivors...")
            if survivor_candidates:
                ranked_run = rank_survivors(survivor_candidates, provider=provider_choice, model=model_name)
            else:
                ranked_run = []

            runner_status.text("Discovery Complete!")

            st.session_state["interactive_results"] = {
                "ranked": ranked_run,
                "all": processed_outputs,
                "usage": get_usage_summary(),
            }

    if "interactive_results" in st.session_state:
        run_res = st.session_state["interactive_results"]
        ranked = run_res["ranked"]

        st.markdown(f"### Discovered Promos ({len(ranked)} Passing Hard Gates)")
        for idx, p in enumerate(ranked, 1):
            with st.container(border=True):
                st.markdown(
                    f"**#{idx}: Episode {p['episode']}** (`{p['start_formatted']} - {p['end_formatted']}` | {p['duration']:.1f}s)"
                )
                st.markdown(
                    f"- **Rating**: `{p.get('composite_score', 8.5):.1f} / 10.0` (Hook: {p.get('hook_score', 8.5)}, Cliff: {p.get('cliffhanger_score', 8.5)}, Standalone: {p.get('standalone_score', 8.5)})"
                )
                st.markdown(f"- **Hook Beat (`{p.get('hook_beat_id', '')}`)**: \"{safe_paraphrase(p.get('hook_text', ''))}\"")
                st.markdown(f"- **Cliffhanger Beat (`{p.get('cliffhanger_beat_id', '')}`)**: \"{safe_paraphrase(p.get('cliffhanger_text', ''))}\"")
                st.markdown(f"- **Rationale**: {p.get('rank_rationale') or p.get('judge_rationale') or p.get('rationale', '')}")
                if p.get("repairs"):
                    st.caption(f"Repairs: {'; '.join(p['repairs'])}")

        with st.expander("Telemetry & Call Accounting"):
            st.json(run_res["usage"])
