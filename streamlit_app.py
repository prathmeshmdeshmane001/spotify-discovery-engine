"""
Spotify Discovery Engine — Streamlit Frontend
Phase 5: Live demo dashboard
"""

import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import pandas as pd

from backend import run_live_demo, trigger_full_pipeline, get_pipeline_step_status, load_insights

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
st.caption("Live demo of the discovery-frustration classifier")

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
    ["Live Demo", "Pipeline Insights", "Architecture", "Research Insights"]
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
        st.markdown(
            "[View live logs on GitHub Actions →](https://github.com/pbehuray/spotify-discovery-engine/actions)"
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
        elif poll_count < 60:
            st.session_state["pipeline_poll_count"] = poll_count + 1
            _time.sleep(8)
            st.rerun()
        else:
            st.session_state["pipeline_polling"] = False
            st.warning("Pipeline tracker timed out. Check GitHub Actions for status.")


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
# Tab 2: Research Insights
# ========================
with tab_research:
    st.header("Research Insights")
    st.caption(
        "Initial research dataset — 456 reviews collected June 2026. These findings drove the Discovery Dial concept."
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
    st.header("Pipeline Insights")
    st.caption(
        "Live pipeline data — updates daily via GitHub Actions scheduler. "
        "Total includes all reviews classified since June 2026."
    )

    try:
        insights = load_insights()
    except Exception as e:
        st.warning(f"Could not load insights.json: {e}")
        insights = {}

    if insights:
        # Last updated
        last_updated = insights.get("generated_at") or insights.get("last_updated")
        if last_updated:
            st.caption(f"Last updated: {last_updated}")

        total_pi = insights.get("total_reviews", 0)
        disc_pi = insights.get("discovery_related", {})
        disc_count_pi = disc_pi.get("count", 0)
        disc_pct_pi = disc_pi.get("percent", 0)

        by_seg_pi = insights.get("by_segment", {})
        dom_seg_pi = max(by_seg_pi, key=by_seg_pi.get) if by_seg_pi else "N/A"
        dom_seg_cnt_pi = by_seg_pi.get(dom_seg_pi, 0)

        by_frust_pi = insights.get("by_frustration_type", {})
        top_frust_pi = max(by_frust_pi, key=by_frust_pi.get) if by_frust_pi else "N/A"
        top_frust_cnt_pi = by_frust_pi.get(top_frust_pi, 0)

        pi_c1, pi_c2, pi_c3, pi_c4 = st.columns(4)
        pi_c1.metric("Total Reviews", str(total_pi))
        pi_c2.metric("Discovery-related", str(disc_count_pi), f"{disc_pct_pi}%")
        pi_c3.metric("Dominant Segment", dom_seg_pi, str(dom_seg_cnt_pi))
        pi_c4.metric("Top Frustration", top_frust_pi, str(top_frust_cnt_pi))

        st.divider()

        pi_col_a, pi_col_b = st.columns(2)

        with pi_col_a:
            st.subheader("Frustration Types")
            if by_frust_pi:
                df_pi_frust = pd.DataFrame(
                    {"Frustration Type": list(by_frust_pi.keys()), "Count": list(by_frust_pi.values())}
                ).sort_values("Count", ascending=True)
                fig = px.bar(df_pi_frust, x="Count", y="Frustration Type", orientation="h",
                             color="Count", color_continuous_scale=["#181818", SPOTIFY_GREEN],
                             template="plotly_dark")
                fig.update_layout(paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG,
                                  font_color="#ffffff", margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)

        with pi_col_b:
            st.subheader("Segment Distribution")
            if by_seg_pi:
                df_pi_seg = pd.DataFrame(
                    {"Segment": list(by_seg_pi.keys()), "Count": list(by_seg_pi.values())}
                ).sort_values("Count", ascending=False)
                fig = px.bar(df_pi_seg, x="Segment", y="Count",
                             color="Count", color_continuous_scale=["#181818", SPOTIFY_GREEN],
                             template="plotly_dark")
                fig.update_layout(paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG,
                                  font_color="#ffffff", margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)

        crosstab_pi = insights.get("segment_x_frustration_crosstab", {})
        if crosstab_pi:
            st.subheader("Segment × Frustration Crosstab")
            pi_segs = list(crosstab_pi.keys())
            pi_frusts = sorted(set(f for sv in crosstab_pi.values() for f in sv.keys()))
            df_pi_heat = pd.DataFrame(
                {seg: [crosstab_pi[seg].get(f, 0) for f in pi_frusts] for seg in pi_segs},
                index=pi_frusts,
            ).T
            fig = px.imshow(df_pi_heat, color_continuous_scale=["#181818", SPOTIFY_GREEN],
                            template="plotly_dark", aspect="auto", text_auto=True)
            fig.update_layout(paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG,
                              font_color="#ffffff", xaxis_title="Frustration Type", yaxis_title="Segment")
            st.plotly_chart(fig, use_container_width=True)

        pi_col_c, pi_col_d = st.columns(2)

        with pi_col_c:
            st.subheader("Top Root Causes")
            root_pi = insights.get("top_root_causes", {})
            if root_pi:
                df_pi_root = pd.DataFrame(
                    {"Root Cause": list(root_pi.keys())[:10], "Count": list(root_pi.values())[:10]}
                )
                fig = px.bar(df_pi_root, x="Count", y="Root Cause", orientation="h",
                             color="Count", color_continuous_scale=["#181818", SPOTIFY_GREEN],
                             template="plotly_dark")
                fig.update_layout(paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG,
                                  font_color="#ffffff", margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)

        with pi_col_d:
            st.subheader("Top Unmet Needs")
            needs_pi = insights.get("top_unmet_needs", {})
            if needs_pi:
                df_pi_needs = pd.DataFrame(
                    {"Unmet Need": list(needs_pi.keys())[:10], "Count": list(needs_pi.values())[:10]}
                )
                fig = px.bar(df_pi_needs, x="Count", y="Unmet Need", orientation="h",
                             color="Count", color_continuous_scale=["#181818", SPOTIFY_GREEN],
                             template="plotly_dark")
                fig.update_layout(paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG,
                                  font_color="#ffffff", margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)

        by_src_pi = insights.get("by_source", {})
        if by_src_pi:
            st.subheader("Review Source Breakdown")
            df_pi_src = pd.DataFrame({"Source": list(by_src_pi.keys()), "Count": list(by_src_pi.values())})
            fig = px.pie(df_pi_src, names="Source", values="Count",
                         color_discrete_sequence=["#1DB954", "#1ed760", "#2a2a2a", "#333333", "#444444"],
                         template="plotly_dark")
            fig.update_layout(paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG,
                              font_color="#ffffff", margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No insights data available yet. Run the pipeline to generate insights.")


# ========================
# Tab 4: Architecture
# ========================
with tab_architecture:
    st.header("Architecture")

    # Lazy import graphviz here to avoid startup import failures
    try:
        from graphviz import Digraph
    except Exception as e:
        st.error(f"Could not load graphviz: {e}")
        st.stop()

    # --- Graphviz pipeline diagram ---
    dot = Digraph(
        format="png",
        graph_attr={"bgcolor": "#121212", "rankdir": "LR", "splines": "ortho"},
        node_attr={"shape": "box", "style": "rounded,filled", "fontcolor": "#ffffff", "fontsize": "12"},
        edge_attr={"color": "#1DB954", "fontcolor": "#B3B3B3", "fontsize": "10"},
    )

    dot.node("play", "Play Store", fillcolor="#1DB954")
    dot.node("app", "App Store", fillcolor="#333333")
    dot.node("reddit", "Reddit", fillcolor="#333333")
    dot.node("forum", "Forum", fillcolor="#333333")
    dot.node("social", "Social", fillcolor="#333333")
    dot.node("scraper", "Scraper", fillcolor="#2a2a2a")
    dot.node("paste", "Paste Importer", fillcolor="#2a2a2a")
    dot.node("supabase", "Supabase", fillcolor="#2a2a2a")
    dot.node("classifier", "Groq Classifier\nllama-3.3-70b-versatile", fillcolor="#2a2a2a")
    dot.node("aggregator", "Aggregator", fillcolor="#2a2a2a")
    dot.node("insights", "insights.json", fillcolor="#333333")
    dot.node("actions", "GitHub Actions\ncron 04:30 UTC", fillcolor="#1DB954")

    dot.edge("play", "scraper")
    dot.edge("app", "paste")
    dot.edge("reddit", "paste")
    dot.edge("forum", "paste")
    dot.edge("social", "paste")
    dot.edge("scraper", "supabase", label="raw_reviews")
    dot.edge("paste", "supabase", label="raw_reviews")
    dot.edge("supabase", "classifier", label="classify")
    dot.edge("classifier", "supabase", label="tagged_reviews")
    dot.edge("supabase", "aggregator", label="query")
    dot.edge("aggregator", "insights", label="generate")
    dot.edge("insights", "actions", label="commit")

    st.graphviz_chart(dot)

    # --- Pipeline stats ---
    st.subheader("Pipeline Stats")
    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
    stats_col1.metric("Reviews", "456")
    stats_col2.metric("Sources", "6")
    stats_col3.metric("Classification Fields", "7")
    stats_col4.metric("Classifier", "llama-3.3-70b-versatile")

    # --- Link buttons ---
    st.subheader("Links")
    link_col1, link_col2 = st.columns(2)
    with link_col1:
        st.link_button(
            "View Pipeline on GitHub",
            "https://github.com/pbehuray/spotify-discovery-engine",
            width="stretch",
        )
    with link_col2:
        st.link_button(
            "View Prototype",
            "https://discovery-dial-mu.vercel.app",
            width="stretch",
        )
