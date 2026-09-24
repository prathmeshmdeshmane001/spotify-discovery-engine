"""
Spotify Discovery Engine — Streamlit Frontend
Phase 5: Live demo dashboard
"""

import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import pandas as pd

from backend import run_live_demo, trigger_full_pipeline, get_pipeline_step_status, load_insights, load_cumulative_insights, _parse_repo, get_recent_tagged_reviews

# --- Page config ---
st.set_page_config(
    page_title="Spotify Discovery Engine",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Theme styling ---
SPOTIFY_GREEN = "#1DB954"
DARK_BG = "#121212"
GREY = "#B3B3B3"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {DARK_BG};
        color: #ffffff;
    }}
    .stButton>button {{
        background-color: {SPOTIFY_GREEN};
        color: #ffffff;
        border: none;
        border-radius: 500px;
        padding: 0.75rem 2rem;
        font-weight: 700;
    }}
    .stButton>button:hover {{
        background-color: #1ed760;
        color: #ffffff;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: #121212;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #282828;
        color: #ffffff;
        border-radius: 4px;
        padding: 8px 20px;
        font-weight: 600;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #1DB954;
        color: #000000;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: #1DB954;
        color: #000000;
    }}
    .stMetric label {{
        color: #b3b3b3;
    }}
    .stMetric [data-testid="stMetricValue"] {{
        color: #1DB954;
        font-size: 2rem;
    }}
    .review-card {{
        background-color: #181818;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        border-left: 4px solid {SPOTIFY_GREEN};
    }}
    .tag {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 500px;
        font-size: 0.85rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }}
    .tag-yes {{
        background-color: {SPOTIFY_GREEN};
        color: #ffffff;
    }}
    .tag-no {{
        background-color: #333333;
        color: {GREY};
    }}
    .tag-segment {{
        background-color: #2a2a2a;
        color: {SPOTIFY_GREEN};
        border: 1px solid {SPOTIFY_GREEN};
    }}
    .tag-frustration {{
        background-color: #2a2a2a;
        color: #ff6b6b;
        border: 1px solid #ff6b6b;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header ---
st.title("🎧 Spotify Discovery Engine")
st.caption("Live demo of the discovery-frustration classifier · Developed by [Prathamesh Deshmane](https://github.com/prathmeshmdeshmane001)")

# --- Programmatic tab navigation via JS ---
if st.session_state.get("goto_tab") is not None:
    tab_index = st.session_state.pop("goto_tab")
    components.html(
        f"""
        <script>
        (function() {{
            var tries = 0;
            function clickTab() {{
                var tabs = window.parent.document.querySelectorAll('[data-baseweb="tab"]');
                if (tabs.length > {tab_index}) {{
                    tabs[{tab_index}].click();
                }} else if (tries < 20) {{
                    tries++;
                    setTimeout(clickTab, 100);
                }}
            }}
            setTimeout(clickTab, 200);
        }})();
        </script>
        """,
        height=0,
    )


# --- Helper: render review cards ---
def render_review_cards(reviews):
    """Render a list of review dicts as HTML cards."""
    html = ""
    for r in reviews:
        text = r["review_text"]
        if len(text) > 200:
            text = text[:200] + "..."

        discovery = r.get("discovery_related", False)
        discovery_tag = (
            '<span class="tag tag-yes">YES</span>'
            if discovery
            else '<span class="tag tag-no">NO</span>'
        )

        html += f"""
        <div class="review-card">
            <p style="color: #ffffff; margin-bottom: 0.75rem;">{text}</p>
            <div style="margin-bottom: 0.5rem;">
                <span class="tag tag-segment">{r.get('segment', 'unknown')}</span>
                <span class="tag tag-frustration">{r.get('frustration_type', 'none')}</span>
                <span class="tag tag-no">{'⭐' * int(r.get('rating', 0))}</span>
                {discovery_tag}
            </div>
        </div>
        """
    return html


# --- Tabs ---
tab_live, tab_pipeline, tab_architecture, tab_research = st.tabs(
    ["🎧 Live Pipeline & Demo", "📊 Live Pipeline Insights", "🏗️ Architecture", "🔬 Baseline Study (456 Benchmark)"]
)

# ========================
# Tab 1: Live Demo
# ========================
with tab_live:
    st.header("Live Demo")
    st.markdown(
        "Scrape the freshest Spotify Play Store reviews and classify them live with Groq."
    )

    col1, col2 = st.columns(2)

    # --- Button 1: Live Demo ---
    with col1:
        if st.button("Live Demo: Classify 5 Fresh Reviews", use_container_width=True):
            status = st.empty()
            progress_bar = st.progress(0)
            cards_container = st.empty()
            results = []

            try:
                with st.spinner("Scraping the 5 most recent US Play Store reviews..."):
                    review_generator = run_live_demo(n=5)

                status.info("Scraping complete. Classifying with fast model...")

                for i, review in enumerate(review_generator, start=1):
                    progress = int((i / 5) * 100)
                    progress_bar.progress(progress)
                    status.info(f"Classifying review {i} of 5...")

                    results.append(review)
                    cards_container.markdown(
                        render_review_cards(results), unsafe_allow_html=True
                    )

                progress_bar.empty()
                status.success(f"Classified {len(results)} fresh reviews")

                st.success(
                    "✓ Pipeline complete — 5 reviews scraped from Play Store → classified via Groq → written to Supabase"
                )
                st.info(
                    "Full pipeline stats from the research dataset (456 curated reviews) are shown in Tab 4. "
                    "The GitHub Actions scheduler continues to ingest and classify new reviews daily."
                )
                st.session_state["live_demo_just_completed"] = True

            except Exception as e:
                progress_bar.empty()
                status.error(f"Demo failed: {e}")

    # --- Button 2: Trigger Full Pipeline ---
    with col2:
        if st.button("Trigger Full Pipeline", use_container_width=True):
            # Dispatch — returns run_id (int), True, or False
            try:
                result = trigger_full_pipeline()
                if result is False:
                    st.error("Failed to trigger pipeline. Check your GitHub token.")
                    st.stop()
            except Exception as e:
                st.error(f"Could not trigger pipeline: {e}")
                if "GITHUB_TOKEN" in str(e):
                    st.info(
                        "💡 **How to enable remote GitHub Actions triggering:**\n\n"
                        "To trigger GitHub Actions from Streamlit Cloud, add `GITHUB_TOKEN` to your Streamlit secrets:\n"
                        "1. Go to GitHub: **Settings → Developer Settings → Personal access tokens → Tokens (classic)**.\n"
                        "2. Click **Generate new token (classic)**, check `repo` and `workflow` scopes, and copy the token (`ghp_...`).\n"
                        "3. In your Streamlit app, open **Manage app → Settings → Secrets** and add:\n"
                        "```toml\n"
                        'GITHUB_TOKEN = "ghp_your_token_here"\n'
                        "```\n"
                        "*Note: You can also click **\"Live Demo: Classify 5 Fresh Reviews\"** on the left to test live scraping & Groq classification immediately without needing a GitHub token!*"
                    )
                st.stop()

            st.session_state["pipeline_run_id"] = result if isinstance(result, int) else None
            st.session_state["pipeline_polling"] = True
            st.session_state["pipeline_poll_count"] = 0
            st.rerun()

    # --- Pipeline stage tracker (rerun-based polling, survives script timeout) ---
    if st.session_state.get("pipeline_polling"):
        import time as _time

        st.markdown("""
<style>
@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}
.stage-active { animation: blink 1s infinite; color: #1DB954; font-size: 20px; }
.stage-complete { color: #1DB954; font-size: 20px; }
.stage-pending { color: #535353; font-size: 20px; }
</style>
""", unsafe_allow_html=True)

        st.info("Pipeline dispatched — tracking progress...")
        repo = _parse_repo()
        st.markdown(
            f"[View live logs on GitHub Actions →](https://github.com/{repo}/actions)"
        )

        def render_stages(stages):
            icons = []
            for s in stages:
                if s["state"] == "complete":
                    icons.append(f'<span class="stage-complete">&#9679; {s["name"]} &#10003;</span>')
                elif s["state"] == "active":
                    icons.append(f'<span class="stage-active">&#9679; {s["name"]}...</span>')
                else:
                    icons.append(f'<span class="stage-pending">&#9711; {s["name"]}</span>')
            return (
                '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;'
                'background:#1a1a1a;padding:1rem;border-radius:8px;">'
                + ' <span style="color:#535353;font-size:18px;">&#8594;</span> '.join(icons)
                + "</div>"
            )

        try:
            status_data = get_pipeline_step_status(
                run_id=st.session_state.get("pipeline_run_id")
            )
        except Exception as ex:
            status_data = {"run_status": "unknown", "active_stage": 0,
                           "stages": [{"name": n, "state": "pending"}
                                       for n in ["Ingestion","Classification","Aggregation","Insights Ready"]]}


        st.markdown(render_stages(status_data["stages"]), unsafe_allow_html=True)
        run_status = status_data["run_status"]
        poll_count = st.session_state.get("pipeline_poll_count", 0)

        if run_status in ("completed", "success"):
            st.session_state["pipeline_polling"] = False
            st.session_state["pipeline_run_id"] = None
            st.session_state["pipeline_poll_count"] = 0
            st.session_state["pipeline_just_completed"] = True
            st.rerun()
        elif run_status in ("failure", "cancelled", "timed_out"):
            st.session_state["pipeline_polling"] = False
            st.error(f"Pipeline ended with status: {run_status}")
        elif poll_count < 90:
            st.session_state["pipeline_poll_count"] = poll_count + 1
            _time.sleep(4)
            st.rerun()
        else:
            st.session_state["pipeline_polling"] = False
            st.warning("⏱️ Pipeline run is taking longer than usual on GitHub Actions.")
            st.info("💡 You can check live progress directly at: [GitHub Actions Runs](https://github.com/prathmeshmdeshmane001/spotify-discovery-engine/actions). When done, switch to '📊 Live Pipeline Insights' to see updated data!")


    # --- Persistent View Pipeline Insights button (inside Tab 1) ---
    if st.session_state.get("pipeline_just_completed") or st.session_state.get("live_demo_just_completed"):
        if st.session_state.get("pipeline_just_completed"):
            st.success("Pipeline complete! Fresh insights are ready.")
        else:
            st.success("✓ Classification complete — pipeline insights updated.")

        def _go_to_pipeline_tab():
            st.session_state["goto_tab"] = 1
            st.session_state["pipeline_just_completed"] = False
            st.session_state["live_demo_just_completed"] = False

        st.button(
            "View Pipeline Insights →",
            on_click=_go_to_pipeline_tab,
            key="persistent_pipeline_insights_btn",
        )


RESEARCH_FINDINGS = {
    "total_reviews": 456,
    "discovery_related_count": 159,
    "discovery_pct": 34.9,
    "dominant_segment": "active_explorer",
    "dominant_segment_count": 113,
    "top_frustration": "stale_recommendations",
    "top_frustration_count": 65,
    "frustration_types": {"stale_recommendations": 65, "control_loss": 37, "discovery_friction": 21, "none": 14, "context_blindness": 8, "filter_bubble_lock_in": 5, "poor_new_release_surfacing": 5, "over_personalization": 2, "algorithmic_sameness": 2},
    "segments": {"active_explorer": 113, "unknown": 15, "lapsed_explorer": 13, "podcast_first": 8, "genre_loyalist": 5, "mood_listener": 5},
    "crosstab": {"active_explorer + stale_recommendations": 53, "active_explorer + control_loss": 22, "active_explorer + discovery_friction": 15, "active_explorer + context_blindness": 4, "active_explorer + filter_bubble_lock_in": 4, "active_explorer + poor_new_release_surfacing": 4, "active_explorer + none": 8, "lapsed_explorer + stale_recommendations": 11, "podcast_first + control_loss": 6, "unknown + discovery_friction": 4},
    "root_causes": {"lack_of_variety": 20, "lack_of_control": 20, "poor_algorithm": 9, "none": 8, "lack_of_new_music": 4},
    "unmet_needs": {"new_music": 36, "none": 9, "music_variety": 6, "new_music_discovery": 6, "personalized_music": 3},
    "sources": {"play_store": 353, "forum": 42, "social": 33, "reddit": 18, "app_store": 10},
}

# ========================
# Tab 4: Baseline Benchmark Study (Static 456 Reviews)
# ========================
with tab_research:
    st.header("🔬 Baseline Research Study (456 Reviews Benchmark)")
    st.info(
        "📌 **Historical Benchmark Dataset (Fixed at 456 reviews)**: This tab displays the original foundational research dataset of 456 reviews collected across 6 sources in June 2026. "
        "It acts as a permanent baseline benchmark to evaluate how live listener frustrations compare against historical data.\n\n"
        "👉 **Looking for Live Data that updates when you run the pipeline?** Switch to the **'📊 Live Pipeline Insights'** tab!"
    )

    r = RESEARCH_FINDINGS

    # --- Metric cards ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Reviews", str(r["total_reviews"]))
    c2.metric("Discovery-related", str(r["discovery_related_count"]), f"{r['discovery_pct']}%")
    c3.metric("Dominant Segment", r["dominant_segment"], str(r["dominant_segment_count"]))
    c4.metric("Top Frustration", r["top_frustration"], str(r["top_frustration_count"]))

    st.divider()

    # --- Charts row 1 ---
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Frustration Types")
        df_frustration = pd.DataFrame(
            {
                "Frustration Type": list(r["frustration_types"].keys()),
                "Count": list(r["frustration_types"].values()),
            }
        ).sort_values("Count", ascending=True)
        fig = px.bar(
            df_frustration,
            x="Count",
            y="Frustration Type",
            orientation="h",
            color="Count",
            color_continuous_scale=["#181818", SPOTIFY_GREEN],
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor=DARK_BG,
            plot_bgcolor=DARK_BG,
            font_color="#ffffff",
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Segment Distribution")
        df_segment = pd.DataFrame(
            {
                "Segment": list(r["segments"].keys()),
                "Count": list(r["segments"].values()),
            }
        ).sort_values("Count", ascending=False)
        fig = px.bar(
            df_segment,
            x="Segment",
            y="Count",
            color="Count",
            color_continuous_scale=["#181818", SPOTIFY_GREEN],
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor=DARK_BG,
            plot_bgcolor=DARK_BG,
            font_color="#ffffff",
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Heatmap: segment × frustration from flat crosstab ---
    st.subheader("Segment × Frustration Crosstab")
    crosstab_flat = r["crosstab"]
    segments_seen = sorted(set(k.split(" + ")[0] for k in crosstab_flat))
    frustrations_seen = sorted(set(k.split(" + ")[1] for k in crosstab_flat))
    heatmap_data = {
        f: {s: crosstab_flat.get(f"{s} + {f}", 0) for s in segments_seen}
        for f in frustrations_seen
    }
    df_heatmap = pd.DataFrame(heatmap_data, index=segments_seen)
    fig = px.imshow(
        df_heatmap,
        color_continuous_scale=["#181818", SPOTIFY_GREEN],
        template="plotly_dark",
        aspect="auto",
        text_auto=True,
    )
    fig.update_layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font_color="#ffffff",
        xaxis_title="Frustration Type",
        yaxis_title="Segment",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"Highlight: **{r['dominant_segment']}** + **{r['top_frustration']}** = "
        f"{crosstab_flat.get(r['dominant_segment'] + ' + ' + r['top_frustration'], 0)} reviews"
    )

    # --- Root causes & unmet needs ---
    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("Top Root Causes")
        df_root = pd.DataFrame(
            {
                "Root Cause": list(r["root_causes"].keys()),
                "Count": list(r["root_causes"].values()),
            }
        )
        fig = px.bar(
            df_root,
            x="Count",
            y="Root Cause",
            orientation="h",
            color="Count",
            color_continuous_scale=["#181818", SPOTIFY_GREEN],
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor=DARK_BG,
            plot_bgcolor=DARK_BG,
            font_color="#ffffff",
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_d:
        st.subheader("Top Unmet Needs")
        df_needs = pd.DataFrame(
            {
                "Unmet Need": list(r["unmet_needs"].keys()),
                "Count": list(r["unmet_needs"].values()),
            }
        )
        fig = px.bar(
            df_needs,
            x="Count",
            y="Unmet Need",
            orientation="h",
            color="Count",
            color_continuous_scale=["#181818", SPOTIFY_GREEN],
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor=DARK_BG,
            plot_bgcolor=DARK_BG,
            font_color="#ffffff",
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Source breakdown ---
    st.subheader("Review Source Breakdown")
    df_source = pd.DataFrame(
        {
            "Source": list(r["sources"].keys()),
            "Count": list(r["sources"].values()),
        }
    )
    fig = px.pie(
        df_source,
        names="Source",
        values="Count",
        color="Source",
        color_discrete_sequence=["#1DB954", "#1ed760", "#2a2a2a", "#333333", "#444444"],
        template="plotly_dark",
    )
    fig.update_layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font_color="#ffffff",
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


# ========================
# Tab 3: Pipeline Insights (live)
# ========================
with tab_pipeline:
    c_title, c_toggle, c_sync = st.columns([3, 2, 1])
    with c_title:
        st.header("📊 Live Pipeline Insights")
        st.caption(
            "Real-time pipeline intelligence · Live aggregated from Supabase & classified via Groq (`openai/gpt-oss-20b`)."
        )
    with c_toggle:
        combine_baseline = st.checkbox(
            "Append live to 456 baseline",
            value=True,
            help="When enabled, newly scraped reviews are appended on top of the 456 baseline research study."
        )
    with c_sync:
        if st.button("🔄 Sync Live Data", use_container_width=True):
            st.rerun()

    try:
        insights = load_cumulative_insights(include_baseline=combine_baseline)
    except Exception as e:
        st.warning(f"Could not load insights: {e}")
        insights = {}

    if insights:
        total_pi = insights.get("total_reviews", 0)
        live_cnt = insights.get("live_reviews", 0)
        base_cnt = insights.get("baseline_reviews", 456)

        if combine_baseline:
            st.success(
                f"🟢 **Cumulative Dataset (456 + Live)** — {base_cnt} baseline research reviews + {live_cnt} live scraped reviews = **{total_pi} total reviews** analyzed."
            )
        else:
            st.info(f"🟢 **Live Scraped Reviews Only** — Showing {total_pi} newly ingested and classified reviews from Supabase.")

        disc_pi = insights.get("discovery_related", {})
        disc_count_pi = disc_pi.get("count", 0)
        disc_pct_pi = disc_pi.get("percent", 0)

        by_seg_pi = insights.get("by_segment", {})
        dom_seg_pi = max(by_seg_pi, key=by_seg_pi.get) if by_seg_pi else "N/A"
        dom_seg_cnt_pi = by_seg_pi.get(dom_seg_pi, 0)

        by_frust_pi = insights.get("by_frustration_type", {})
        top_frust_pi = max(by_frust_pi, key=by_frust_pi.get) if by_frust_pi else "N/A"
        top_frust_cnt_pi = by_frust_pi.get(top_frust_pi, 0)

        # KPI Metrics
        pi_c1, pi_c2, pi_c3, pi_c4 = st.columns(4)
        if combine_baseline:
            pi_c1.metric("Total Reviews", str(total_pi), f"+{live_cnt} Live Scraped")
        else:
            pi_c1.metric("Total Reviews", str(total_pi), "Live Only")
        pi_c2.metric("Discovery Frustration", f"{disc_pct_pi}%", f"{disc_count_pi} / {total_pi}")
        pi_c3.metric("Dominant Persona", dom_seg_pi.replace('_', ' ').title(), f"{dom_seg_cnt_pi} users")
        pi_c4.metric("Top Frustration", top_frust_pi.replace('_', ' ').title(), f"{top_frust_cnt_pi} reports")

        st.divider()

        # Primary Visualizations
        pi_col_a, pi_col_b = st.columns(2)

        with pi_col_a:
            st.subheader("🎯 Frustration Breakdown")
            if by_frust_pi:
                df_pi_frust = pd.DataFrame(
                    {"Frustration Type": list(by_frust_pi.keys()), "Count": list(by_frust_pi.values())}
                ).sort_values("Count", ascending=True)
                fig = px.bar(
                    df_pi_frust,
                    x="Count",
                    y="Frustration Type",
                    orientation="h",
                    color="Count",
                    color_continuous_scale=["#181818", SPOTIFY_GREEN],
                    text="Count",
                    template="plotly_dark",
                )
                fig.update_layout(
                    paper_bgcolor=DARK_BG,
                    plot_bgcolor=DARK_BG,
                    font_color="#ffffff",
                    margin=dict(l=20, r=20, t=20, b=20),
                    showlegend=False,
                )
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

        with pi_col_b:
            st.subheader("👥 User Persona Segmentation")
            if by_seg_pi:
                df_pi_seg = pd.DataFrame(
                    {"Segment": list(by_seg_pi.keys()), "Count": list(by_seg_pi.values())}
                ).sort_values("Count", ascending=False)
                fig = px.bar(
                    df_pi_seg,
                    x="Segment",
                    y="Count",
                    color="Count",
                    color_continuous_scale=["#181818", SPOTIFY_GREEN],
                    text="Count",
                    template="plotly_dark",
                )
                fig.update_layout(
                    paper_bgcolor=DARK_BG,
                    plot_bgcolor=DARK_BG,
                    font_color="#ffffff",
                    margin=dict(l=20, r=20, t=20, b=20),
                    showlegend=False,
                )
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

        # Crosstab Heatmap
        crosstab_pi = insights.get("segment_x_frustration_crosstab", {})
        if crosstab_pi:
            st.subheader("🔥 Segment × Frustration Pain-Point Matrix")
            pi_segs = list(crosstab_pi.keys())
            pi_frusts = sorted(set(f for sv in crosstab_pi.values() for f in sv.keys()))
            df_pi_heat = pd.DataFrame(
                {seg: [crosstab_pi[seg].get(f, 0) for f in pi_frusts] for seg in pi_segs},
                index=pi_frusts,
            ).T
            fig = px.imshow(
                df_pi_heat,
                color_continuous_scale=["#121212", "#1a3d24", SPOTIFY_GREEN],
                template="plotly_dark",
                aspect="auto",
                text_auto=True,
            )
            fig.update_layout(
                paper_bgcolor=DARK_BG,
                plot_bgcolor=DARK_BG,
                font_color="#ffffff",
                xaxis_title="Frustration Type",
                yaxis_title="User Segment",
                margin=dict(l=20, r=20, t=30, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

        # Root Causes & Unmet Needs
        pi_col_c, pi_col_d = st.columns(2)

        with pi_col_c:
            st.subheader("💡 Top AI-Extracted Root Causes")
            root_pi = insights.get("top_root_causes", {})
            if root_pi:
                for idx, (cause, count) in enumerate(list(root_pi.items())[:6], 1):
                    st.markdown(
                        f"""
                        <div style="background:#181818;padding:0.75rem 1rem;border-radius:8px;margin-bottom:0.5rem;border-left:3px solid {SPOTIFY_GREEN};">
                            <span style="color:#b3b3b3;font-size:0.85rem;">#{idx} Root Cause · {count} mentions</span>
                            <div style="color:#ffffff;font-size:0.95rem;margin-top:2px;">{cause}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        with pi_col_d:
            st.subheader("🎯 Top Unmet Listener Needs")
            needs_pi = insights.get("top_unmet_needs", {})
            if needs_pi:
                for idx, (need, count) in enumerate(list(needs_pi.items())[:6], 1):
                    st.markdown(
                        f"""
                        <div style="background:#181818;padding:0.75rem 1rem;border-radius:8px;margin-bottom:0.5rem;border-left:3px solid #1ed760;">
                            <span style="color:#b3b3b3;font-size:0.85rem;">#{idx} Unmet Need · {count} requests</span>
                            <div style="color:#ffffff;font-size:0.95rem;margin-top:2px;">{need}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        st.divider()

        # Review Source & Desired Behavior Breakdown
        pi_col_e, pi_col_f = st.columns(2)

        with pi_col_e:
            st.subheader("🎵 Desired Behaviors")
            by_beh_pi = insights.get("by_desired_behavior", {})
            if by_beh_pi:
                df_beh = pd.DataFrame({"Behavior": list(by_beh_pi.keys()), "Count": list(by_beh_pi.values())})
                fig = px.pie(
                    df_beh,
                    names="Behavior",
                    values="Count",
                    color_discrete_sequence=["#1DB954", "#1ed760", "#282828", "#3e3e3e", "#535353", "#737373"],
                    template="plotly_dark",
                )
                fig.update_layout(paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG, font_color="#ffffff", margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)

        with pi_col_f:
            st.subheader("📱 Data Ingestion Sources")
            by_src_pi = insights.get("by_source", {})
            if by_src_pi:
                df_pi_src = pd.DataFrame({"Source": list(by_src_pi.keys()), "Count": list(by_src_pi.values())})
                fig = px.pie(
                    df_pi_src,
                    names="Source",
                    values="Count",
                    color_discrete_sequence=["#1DB954", "#1ed760", "#282828", "#3e3e3e", "#535353"],
                    template="plotly_dark",
                )
                fig.update_layout(paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG, font_color="#ffffff", margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # --- Interactive Classified Reviews Feed ---
        st.subheader("📝 Live Classified Reviews Explorer")
        st.caption("Inspect individual reviews classified by the Groq taxonomy pipeline directly from Supabase.")

        all_tagged_reviews = get_recent_tagged_reviews(limit=60)
        if all_tagged_reviews:
            col_search, col_f_seg, col_f_frust = st.columns([2, 1, 1])
            with col_search:
                search_q = st.text_input("🔍 Search review text...", placeholder="e.g. recommend, repeat, daily mix, genre")
            with col_f_seg:
                seg_filter = st.selectbox("Filter Persona", ["All Personas"] + sorted(list(set(r["segment"] for r in all_tagged_reviews))))
            with col_f_frust:
                frust_filter = st.selectbox("Filter Frustration", ["All Frustrations"] + sorted(list(set(r["frustration_type"] for r in all_tagged_reviews))))

            # Filter data
            filtered_reviews = all_tagged_reviews
            if search_q:
                filtered_reviews = [r for r in filtered_reviews if search_q.lower() in r["text"].lower()]
            if seg_filter != "All Personas":
                filtered_reviews = [r for r in filtered_reviews if r["segment"] == seg_filter]
            if frust_filter != "All Frustrations":
                filtered_reviews = [r for r in filtered_reviews if r["frustration_type"] == frust_filter]

            st.caption(f"Showing **{len(filtered_reviews)}** matching reviews (out of {len(all_tagged_reviews)} most recent):")

            for r in filtered_reviews[:20]:
                rating_stars = "⭐" * int(r.get("rating") or 0)
                source_badge = r.get("source", "play_store").replace("_", " ").title()
                discovery_badge = (
                    '<span class="tag tag-yes">Discovery Frustration</span>'
                    if r.get("discovery_related")
                    else '<span class="tag tag-no">Non-Discovery</span>'
                )
                st.markdown(
                    f"""
                    <div class="review-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                            <span style="font-size:0.85rem;color:#b3b3b3;">{source_badge} · {rating_stars}</span>
                            <div>{discovery_badge}</div>
                        </div>
                        <p style="color:#ffffff;font-size:0.95rem;line-height:1.4;margin-bottom:12px;">"{r['text']}"</p>
                        <div>
                            <span class="tag tag-segment">👤 {r.get('segment')}</span>
                            <span class="tag tag-frustration">⚠️ {r.get('frustration_type')}</span>
                            <span class="tag" style="background:#282828;color:#b3b3b3;">🎯 {r.get('desired_behavior')}</span>
                        </div>
                        <div style="font-size:0.85rem;color:#b3b3b3;margin-top:6px;">
                            <b>Root Cause:</b> {r.get('root_cause', 'N/A')} &nbsp;|&nbsp; <b>Unmet Need:</b> {r.get('unmet_need', 'N/A')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No classified review records retrieved yet.")

    else:
        st.info("No insights data available yet. Run the pipeline to generate insights.")


# ========================
# Tab 4: Architecture
# ========================
with tab_architecture:
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h2 style="margin: 0 0 6px 0; font-size: 26px; font-weight: 700; color: #FFFFFF; display: flex; align-items: center; gap: 10px;">
                <span style="color: #1DB954;">⚡</span> Production Intelligence Pipeline Architecture
            </h2>
            <p style="margin: 0; color: #B3B3B3; font-size: 14px; line-height: 1.5;">
                An end-to-end automated data intelligence pipeline: continuously ingests multi-channel user feedback, 
                normalizes records in Supabase PostgreSQL, classifies root causes via ultra-fast Groq LPU inference across 7 taxonomy dimensions, 
                and computes decision-ready analytics for Spotify product & algorithmic teams.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- Dynamic Telemetry ---
    try:
        cum_data = load_cumulative_insights(include_baseline=True)
        total_revs = cum_data.get("total_reviews", 456)
        baseline_revs = cum_data.get("baseline_reviews", 456)
        live_revs = cum_data.get("live_reviews", 0)
    except Exception:
        total_revs, baseline_revs, live_revs = 456, 456, 0

    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
    stats_col1.metric(
        "Processed Dataset",
        f"{total_revs:,} Reviews",
        help=f"{baseline_revs} Cohort Baseline + {live_revs} Live Ingested",
    )
    stats_col2.metric(
        "Monitored Channels",
        "6 Sources",
        help="Google Play Store, Apple App Store, Reddit, Spotify Community, Twitter/X, Paste Importer",
    )
    stats_col3.metric(
        "AI Taxonomy Vectors",
        "7 Dimensions",
        help="Sentiment, Frustration Type, Desired Behavior, Churn Risk, Recommendation Impact, User Segment, Root Cause",
    )
    stats_col4.metric(
        "Active Classifier",
        "openai/gpt-oss-20b",
        help="Ultra-low latency Groq LPU inference (~250ms/review) with automated fallback cascade",
    )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # --- Sleek Modern SVG Pipeline Diagram ---
    st.markdown("""
    <div style="background: linear-gradient(180deg, #181818 0%, #121212 100%); padding: 24px; border-radius: 12px; border: 1px solid #282828; margin-bottom: 24px; overflow-x: auto;">
        <svg viewBox="0 0 1060 260" width="100%" height="auto" style="min-width: 850px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
            <defs>
                <linearGradient id="greenGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#1DB954" />
                    <stop offset="100%" stop-color="#14833b" />
                </linearGradient>
                <linearGradient id="cardGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="#242424" />
                    <stop offset="100%" stop-color="#1a1a1a" />
                </linearGradient>
                <linearGradient id="aiGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#2a2438" />
                    <stop offset="100%" stop-color="#1b1724" />
                </linearGradient>
                <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#1DB954" flood-opacity="0.25"/>
                </filter>
                <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#1DB954" />
                </marker>
                <marker id="arrowGray" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#535353" />
                </marker>
            </defs>

            <!-- Connector Lines -->
            <path d="M 185 130 L 235 130" stroke="#1DB954" stroke-width="2.5" stroke-dasharray="4 3" marker-end="url(#arrow)" />
            <path d="M 395 130 L 445 130" stroke="#1DB954" stroke-width="2.5" stroke-dasharray="4 3" marker-end="url(#arrow)" />
            <path d="M 605 130 L 655 130" stroke="#1DB954" stroke-width="2.5" stroke-dasharray="4 3" marker-end="url(#arrow)" />
            <path d="M 815 130 L 865 130" stroke="#1DB954" stroke-width="2.5" stroke-dasharray="4 3" marker-end="url(#arrow)" />

            <!-- FEEDBACK LOOP / CRON LINE -->
            <path d="M 945 60 C 945 20, 105 20, 105 60" fill="none" stroke="#535353" stroke-width="1.5" stroke-dasharray="5 5" marker-end="url(#arrowGray)" />
            <text x="525" y="24" fill="#888888" font-size="11" font-weight="600" text-anchor="middle">SCHEDULED AUTOMATION LOOP (GitHub Actions Cron @ 04:30 UTC)</text>

            <!-- STAGE 1: INGESTION -->
            <g transform="translate(25, 60)">
                <rect width="160" height="150" rx="10" fill="url(#cardGrad)" stroke="#333333" stroke-width="1.5" />
                <rect x="0" y="0" width="160" height="6" rx="3" fill="#1DB954" />
                <rect x="12" y="14" width="60" height="18" rx="4" fill="#0d2818" />
                <text x="42" y="27" fill="#1DB954" font-size="10" font-weight="700" text-anchor="middle">STAGE 01</text>
                <text x="12" y="48" fill="#FFFFFF" font-size="14" font-weight="700">Data Ingestion</text>
                <text x="12" y="65" fill="#A7A7A7" font-size="11">Multi-Source Feeds</text>
                <line x1="12" y1="75" x2="148" y2="75" stroke="#333333" stroke-width="1" />
                <text x="12" y="93" fill="#E0E0E0" font-size="11">✓ Play Store Scraper</text>
                <text x="12" y="111" fill="#E0E0E0" font-size="11">✓ App Store & Reddit</text>
                <text x="12" y="129" fill="#E0E0E0" font-size="11">✓ Paste Importer</text>
            </g>

            <!-- STAGE 2: SUPABASE RAW -->
            <g transform="translate(235, 60)">
                <rect width="160" height="150" rx="10" fill="url(#cardGrad)" stroke="#333333" stroke-width="1.5" />
                <rect x="0" y="0" width="160" height="6" rx="3" fill="#3ECF8E" />
                <rect x="12" y="14" width="60" height="18" rx="4" fill="#143026" />
                <text x="42" y="27" fill="#3ECF8E" font-size="10" font-weight="700" text-anchor="middle">STAGE 02</text>
                <text x="12" y="48" fill="#FFFFFF" font-size="14" font-weight="700">Supabase DB</text>
                <text x="12" y="65" fill="#A7A7A7" font-size="11">PostgreSQL 15 Lake</text>
                <line x1="12" y1="75" x2="148" y2="75" stroke="#333333" stroke-width="1" />
                <text x="12" y="93" fill="#E0E0E0" font-size="11">📁 raw_reviews</text>
                <text x="12" y="111" fill="#E0E0E0" font-size="11">🔒 Deduplication Index</text>
                <text x="12" y="129" fill="#E0E0E0" font-size="11">⚡ Unclassified Queue</text>
            </g>

            <!-- STAGE 3: GROQ AI -->
            <g transform="translate(445, 60)" filter="url(#glow)">
                <rect width="160" height="150" rx="10" fill="url(#aiGrad)" stroke="#1DB954" stroke-width="2" />
                <rect x="0" y="0" width="160" height="6" rx="3" fill="#1DB954" />
                <rect x="12" y="14" width="60" height="18" rx="4" fill="#0d2818" />
                <text x="42" y="27" fill="#1DB954" font-size="10" font-weight="700" text-anchor="middle">STAGE 03</text>
                <text x="12" y="48" fill="#FFFFFF" font-size="14" font-weight="700">Groq LPU AI</text>
                <text x="12" y="65" fill="#1DB954" font-size="11" font-weight="600">~250ms Ultra-Fast</text>
                <line x1="12" y1="75" x2="148" y2="75" stroke="#3a3250" stroke-width="1" />
                <text x="12" y="93" fill="#FFFFFF" font-size="10" font-weight="600">⚡ gpt-oss-20b</text>
                <text x="12" y="111" fill="#E0E0E0" font-size="11">🎯 7D Taxonomy</text>
                <text x="12" y="129" fill="#E0E0E0" font-size="11">🛡️ Cascade Fallbacks</text>
            </g>

            <!-- STAGE 4: AGGREGATOR -->
            <g transform="translate(655, 60)">
                <rect width="160" height="150" rx="10" fill="url(#cardGrad)" stroke="#333333" stroke-width="1.5" />
                <rect x="0" y="0" width="160" height="6" rx="3" fill="#1DB954" />
                <rect x="12" y="14" width="60" height="18" rx="4" fill="#0d2818" />
                <text x="42" y="27" fill="#1DB954" font-size="10" font-weight="700" text-anchor="middle">STAGE 04</text>
                <text x="12" y="48" fill="#FFFFFF" font-size="14" font-weight="700">Aggregator</text>
                <text x="12" y="65" fill="#A7A7A7" font-size="11">Pandas Intelligence</text>
                <line x1="12" y1="75" x2="148" y2="75" stroke="#333333" stroke-width="1" />
                <text x="12" y="93" fill="#E0E0E0" font-size="11">📁 tagged_reviews</text>
                <text x="12" y="111" fill="#E0E0E0" font-size="11">📊 Cross-Tabulations</text>
                <text x="12" y="129" fill="#E0E0E0" font-size="11">💾 insights.json</text>
            </g>

            <!-- STAGE 5: ORCHESTRATION & UI -->
            <g transform="translate(865, 60)">
                <rect width="170" height="150" rx="10" fill="url(#cardGrad)" stroke="#333333" stroke-width="1.5" />
                <rect x="0" y="0" width="170" height="6" rx="3" fill="#1DB954" />
                <rect x="12" y="14" width="60" height="18" rx="4" fill="#0d2818" />
                <text x="42" y="27" fill="#1DB954" font-size="10" font-weight="700" text-anchor="middle">STAGE 05</text>
                <text x="12" y="48" fill="#FFFFFF" font-size="14" font-weight="700">Presentation</text>
                <text x="12" y="65" fill="#A7A7A7" font-size="11">Executive Cockpit</text>
                <line x1="12" y1="75" x2="158" y2="75" stroke="#333333" stroke-width="1" />
                <text x="12" y="93" fill="#E0E0E0" font-size="11">🖥️ Live Streamlit UI</text>
                <text x="12" y="111" fill="#E0E0E0" font-size="11">📈 Discovery Analytics</text>
                <text x="12" y="129" fill="#E0E0E0" font-size="11">🚀 GitHub Actions CI</text>
            </g>
        </svg>
    </div>
    """, unsafe_allow_html=True)

    # --- Architectural Breakdown Cards ---
    st.subheader("Component Deep-Dive")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
            <div style="background: #181818; padding: 18px; border-radius: 10px; border: 1px solid #282828; height: 100%;">
                <div style="color: #1DB954; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Ingestion & Ingestion Lake</div>
                <h4 style="margin: 4px 0 10px 0; color: #FFFFFF;">1. Data Sourcing & Deduplication</h4>
                <p style="color: #B3B3B3; font-size: 13px; margin-bottom: 12px; line-height: 1.5;">
                    Extracts live feedback from <b>Google Play Store</b> via <code>google-play-scraper</code> alongside multi-channel inputs (Apple App Store, Reddit r/spotify, Spotify Community, Twitter/X, and In-App Paste Importer).
                </p>
                <div style="background: #121212; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 12px; color: #3ECF8E;">
                    Table: raw_reviews (id, source, text, rating, created_at, status)
                </div>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
            <div style="background: #181818; padding: 18px; border-radius: 10px; border: 1px solid #282828; height: 100%;">
                <div style="color: #1DB954; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Inference & Taxonomy</div>
                <h4 style="margin: 4px 0 10px 0; color: #FFFFFF;">2. Groq LPU Classification Engine</h4>
                <p style="color: #B3B3B3; font-size: 13px; margin-bottom: 12px; line-height: 1.5;">
                    Utilizes Groq's Language Processing Units (LPU) running <b>openai/gpt-oss-20b</b> for deterministic structured JSON output with under 300ms latency. Employs automatic fallbacks if model limits are reached.
                </p>
                <div style="background: #121212; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 12px; color: #1DB954;">
                    Dimensions: sentiment, frustration, behavior, churn_risk, segment...
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    c3, c4 = st.columns(2)

    with c3:
        st.markdown("""
            <div style="background: #181818; padding: 18px; border-radius: 10px; border: 1px solid #282828; height: 100%;">
                <div style="color: #1DB954; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Storage & Computation</div>
                <h4 style="margin: 4px 0 10px 0; color: #FFFFFF;">3. Analytics Aggregator</h4>
                <p style="color: #B3B3B3; font-size: 13px; margin-bottom: 12px; line-height: 1.5;">
                    Classified records are stored in <code>tagged_reviews</code>. The Python aggregator (<code>aggregate.py</code>) computes multi-dimensional cross-tabs (User Segment × Frustration Type) and generates static/live JSON artifacts.
                </p>
                <div style="background: #121212; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 12px; color: #B3B3B3;">
                    Output: insights.json & live cumulative telemetry state
                </div>
            </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown("""
            <div style="background: #181818; padding: 18px; border-radius: 10px; border: 1px solid #282828; height: 100%;">
                <div style="color: #1DB954; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">CI/CD & Delivery</div>
                <h4 style="margin: 4px 0 10px 0; color: #FFFFFF;">4. Scheduled Orchestration & Cockpit</h4>
                <p style="color: #B3B3B3; font-size: 13px; margin-bottom: 12px; line-height: 1.5;">
                    Automated daily via <b>GitHub Actions</b> (cron <code>04:30 UTC</code>) or on-demand via the Streamlit trigger button. Renders real-time executive discovery intelligence and opportunity spaces.
                </p>
                <div style="background: #121212; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 12px; color: #1DB954;">
                    Trigger: workflow_dispatch & daily scheduled cron
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --- Interactive Deep Dives ---
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    with st.expander("🔍 Deep Dive: Database Schemas (Supabase PostgreSQL 15)"):
        st.code("""
-- 1. Raw Reviews Staging Lake
CREATE TABLE raw_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,                  -- 'play_store', 'app_store', 'reddit', etc.
    review_text TEXT NOT NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    author TEXT,
    review_date TIMESTAMPTZ DEFAULT NOW(),
    review_hash TEXT UNIQUE,               -- Prevents duplicate ingestion
    status TEXT DEFAULT 'pending'          -- 'pending', 'classified', 'error'
);

-- 2. Tagged Reviews Intelligence Warehouse
CREATE TABLE tagged_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_review_id UUID REFERENCES raw_reviews(id),
    sentiment TEXT NOT NULL,               -- 'positive', 'neutral', 'negative'
    frustration_type TEXT,                 -- 'algorithm_fatigue', 'repetitive_recommendations', etc.
    desired_behavior TEXT,                 -- 'find_new_artists', 'break_routine', 'mood_alignment'
    churn_risk TEXT NOT NULL,              -- 'low', 'medium', 'high'
    recommendation_impact TEXT,            -- 'positive', 'neutral', 'negative'
    user_segment TEXT NOT NULL,            -- 'active_explorer', 'casual_listener', 'routine_listener'
    root_cause TEXT,                       -- Primary algorithmic or UX breakdown
    model_used TEXT NOT NULL,              -- e.g., 'openai/gpt-oss-20b'
    classified_at TIMESTAMPTZ DEFAULT NOW()
);
        """, language="sql")

    with st.expander("🧠 Deep Dive: 7-Dimensional AI Taxonomy Specification"):
        st.markdown("""
        Each ingested review is evaluated against a structured classification matrix:
        1. **Sentiment**: `positive`, `neutral`, `negative`
        2. **Frustration Type**: `repetitive_recommendations`, `genre_stagnation`, `algorithm_fatigue`, `playlist_decay`, `search_friction`, `none`
        3. **Desired Behavior**: `find_new_artists`, `break_routine`, `niche_deep_dive`, `mood_alignment`, `passive_discovery`
        4. **Churn Risk**: `low`, `medium`, `high` (identifies active cancellation intent)
        5. **Recommendation Impact**: `positive`, `neutral`, `negative`
        6. **User Persona Segment**: `active_explorer`, `casual_listener`, `routine_listener`, `deep_curator`
        7. **Root Cause**: Extracted core issue (e.g., *Collaborative filtering feedback loop trap*, *Home feed recency bias*)
        """)

    with st.expander("🔄 Deep Dive: GitHub Actions CI/CD Pipeline (.github/workflows/pipeline.yml)"):
        st.code("""
name: Spotify Discovery Intelligence Pipeline

on:
  schedule:
    - cron: '30 4 * * *'    # Runs daily at 04:30 UTC
  workflow_dispatch:        # Allows manual triggering from Streamlit or API

jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Codebase
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Dependencies
        run: pip install -r requirements.txt

      - name: Execute Full Intelligence Pipeline
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: |
          python scrape.py
          python classify.py
          python aggregate.py

      - name: Commit Fresh Insights
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add data/insights.json
          git diff --quiet && git diff --staged --quiet || git commit -m "chore: automated daily insights refresh [skip ci]"
          git push
        """, language="yaml")

    # --- Quick Resource Links ---
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.subheader("Repository & Pipeline Controls")
    repo = _parse_repo()
    link_col1, link_col2 = st.columns(2)
    with link_col1:
        st.link_button(
            "⚡ View GitHub Actions Pipeline",
            f"https://github.com/{repo}/actions",
            use_container_width=True,
        )
    with link_col2:
        st.link_button(
            "📂 Source Code Repository",
            f"https://github.com/{repo}",
            use_container_width=True,
        )

