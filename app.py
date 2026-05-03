import streamlit as st

from src.ingestion.google_trends_scraper import (
    GEO_OPTIONS,
    ScraperError,
    get_trending_topics,
)
from src.ingestion.news_researcher import (
    ResearchError,
    fetch_news_articles,
    format_articles_for_prompt,
    pick_top_topics,
)
from src.ai.analyzer import AnalysisError, analyze_trend
from src.ai.generator import GenerationError, generate_content, generate_topic_post
from src.publishing.twitter_publisher import TwitterPublishError, post_to_twitter
from src.publishing.instagram_publisher import InstagramPublishError, post_to_instagram
from src.publishing.image_generator import ImageGenerationError, generate_image
from src.config import AppConfig
from src.auth.cognito import AuthError, CognitoAuth

# ── Auth setup ────────────────────────────────────────────────────────────────
_cfg = AppConfig()
_auth = CognitoAuth(
    user_pool_id=_cfg.cognito_user_pool_id,
    client_id=_cfg.cognito_client_id,
    region=_cfg.cognito_region,
)


def _render_auth() -> bool:
    """
    Render the login/signup/confirm UI.
    Returns True if the user is authenticated, False otherwise.
    """
    # Already logged in
    if st.session_state.get("access_token"):
        return True

    st.title("📈 Trend-to-Content Automation Engine")
    st.markdown("---")

    tab_login, tab_signup, tab_confirm, tab_reset = st.tabs(
        ["🔐 Login", "📝 Sign Up", "✅ Confirm Account", "🔑 Reset Password"]
    )

    # ── Login ──────────────────────────────────────────────────────────────────
    with tab_login:
        st.subheader("Sign in to your account")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", use_container_width=True, key="login_btn"):
            if not email or not password:
                st.error("Please enter your email and password.")
            else:
                with st.spinner("Signing in..."):
                    try:
                        tokens = _auth.login(email, password)
                        user = _auth.get_user(tokens["access_token"])
                        st.session_state["access_token"] = tokens["access_token"]
                        st.session_state["refresh_token"] = tokens["refresh_token"]
                        st.session_state["user_email"] = user["email"]
                        st.rerun()
                    except AuthError as e:
                        st.error(str(e))

    # ── Sign Up ────────────────────────────────────────────────────────────────
    with tab_signup:
        st.subheader("Create a new account")
        su_email = st.text_input("Email", key="su_email")
        su_password = st.text_input(
            "Password",
            type="password",
            key="su_password",
            help="Min 8 chars, must include uppercase, lowercase, and number.",
        )
        su_password2 = st.text_input(
            "Confirm Password", type="password", key="su_password2"
        )
        if st.button("Create Account", use_container_width=True, key="signup_btn"):
            if not su_email or not su_password:
                st.error("Please fill in all fields.")
            elif su_password != su_password2:
                st.error("Passwords do not match.")
            else:
                with st.spinner("Creating account..."):
                    try:
                        _auth.signup(su_email, su_password)
                        st.success(
                            "Account created! Check your email for a confirmation code, then use the 'Confirm Account' tab."
                        )
                    except AuthError as e:
                        st.error(str(e))

    # ── Confirm Account ────────────────────────────────────────────────────────
    with tab_confirm:
        st.subheader("Confirm your account")
        st.caption("Enter the 6-digit code sent to your email after sign up.")
        cf_email = st.text_input("Email", key="cf_email")
        cf_code = st.text_input("Confirmation Code", key="cf_code")
        if st.button("Confirm Account", use_container_width=True, key="confirm_btn"):
            if not cf_email or not cf_code:
                st.error("Please enter your email and confirmation code.")
            else:
                with st.spinner("Confirming..."):
                    try:
                        _auth.confirm_signup(cf_email, cf_code)
                        st.success("Account confirmed! You can now log in.")
                    except AuthError as e:
                        st.error(str(e))

    # ── Reset Password ─────────────────────────────────────────────────────────
    with tab_reset:
        st.subheader("Reset your password")
        rp_email = st.text_input("Email", key="rp_email")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "Send Reset Code", use_container_width=True, key="rp_send_btn"
            ):
                if not rp_email:
                    st.error("Please enter your email.")
                else:
                    with st.spinner("Sending..."):
                        try:
                            _auth.forgot_password(rp_email)
                            st.success("Reset code sent to your email.")
                        except AuthError as e:
                            st.error(str(e))
        with col2:
            rp_code = st.text_input("Reset Code", key="rp_code")
            rp_new_pw = st.text_input("New Password", type="password", key="rp_new_pw")
            if st.button(
                "Set New Password", use_container_width=True, key="rp_confirm_btn"
            ):
                if not all([rp_email, rp_code, rp_new_pw]):
                    st.error("Please fill in all fields.")
                else:
                    with st.spinner("Resetting..."):
                        try:
                            _auth.confirm_forgot_password(rp_email, rp_code, rp_new_pw)
                            st.success("Password reset! You can now log in.")
                        except AuthError as e:
                            st.error(str(e))

    return False


# ── Auth gate — stop here if not logged in ────────────────────────────────────
if not _render_auth():
    st.stop()

from src.publishing.instagram_publisher import InstagramPublishError, post_to_instagram

st.set_page_config(page_title="Trend-to-Content Engine", page_icon="📈", layout="wide")
st.title("📈 Trend-to-Content Automation Engine")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # User info + logout
    user_email = st.session_state.get("user_email", "")
    st.caption(f"Logged in as **{user_email}**")
    if st.button("🚪 Logout", use_container_width=True):
        access_token = st.session_state.get("access_token", "")
        if access_token:
            _auth.logout(access_token)
        for key in [
            "access_token",
            "refresh_token",
            "user_email",
            "trend_summary",
            "combined_content",
            "topic_posts",
            "all_topics",
            "country",
        ]:
            st.session_state.pop(key, None)
        st.rerun()
    st.divider()
    st.header("⚙️ Settings")
    country = st.selectbox("Country", options=list(GEO_OPTIONS.keys()), index=0)
    limit = st.slider("Trends to fetch", min_value=5, max_value=20, value=10)
    fetch_button = st.button("🔍 Fetch & Analyze Trends", use_container_width=True)

    st.divider()
    st.subheader("🎨 Image Generation")
    st.caption("Cloudflare Worker endpoint. Add CLOUDFARE_API_KEY to your .env file.")
    cf_api_key_input = st.text_input(
        "Cloudflare API Key (override)",
        type="password",
        key="cf_api_key_input",
        help="Leave blank to use CLOUDFARE_API_KEY from .env",
    )

    st.divider()
    st.subheader("🐦 Twitter / X")
    st.caption("Requires a Twitter Developer account with Read & Write permissions.")
    tw_api_key = st.text_input("API Key", type="password", key="tw_api_key")
    tw_api_secret = st.text_input("API Secret", type="password", key="tw_api_secret")
    tw_access_token = st.text_input(
        "Access Token", type="password", key="tw_access_token"
    )
    tw_access_secret = st.text_input(
        "Access Token Secret", type="password", key="tw_access_secret"
    )

    st.divider()
    st.subheader("📸 Instagram")
    st.caption(
        "Requires an Instagram Business/Creator account linked to a Facebook Page."
    )
    ig_access_token = st.text_input(
        "Access Token", type="password", key="ig_access_token"
    )
    ig_account_id = st.text_input("Instagram Account ID", key="ig_account_id")
    ig_image_url = st.text_input(
        "Image URL (optional)",
        placeholder="https://example.com/image.jpg",
        key="ig_image_url",
        help="Publicly accessible image URL. Leave blank to use a default placeholder.",
    )

# ── Pipeline ──────────────────────────────────────────────────────────────────
if fetch_button:
    geo = GEO_OPTIONS[country]

    # Step 1: Fetch trends
    with st.spinner("Fetching trending topics..."):
        try:
            all_topics = get_trending_topics(geo=geo, limit=limit)
        except ScraperError as e:
            st.error(f"Failed to fetch trends: {e}")
            st.stop()

    # Step 2: Pick top 5 by traffic
    top5 = pick_top_topics(all_topics, n=5)

    # Step 3: Fetch news for each of the top 5 in sequence
    topic_news: dict[str, str] = {}
    topic_articles: dict[str, list] = {}
    progress = st.progress(0, text="Researching news articles...")
    for i, topic in enumerate(top5):
        progress.progress((i + 1) / len(top5), text=f"Researching: {topic['title']}")
        try:
            articles = fetch_news_articles(topic["title"], limit=4)
            topic_articles[topic["title"]] = articles
            topic_news[topic["title"]] = format_articles_for_prompt(articles)
        except ResearchError:
            topic_articles[topic["title"]] = []
            topic_news[topic["title"]] = ""
    progress.empty()

    # Step 4: Overall trend analysis (uses all top 5 together)
    with st.spinner("Analyzing overall trend..."):
        try:
            trend_summary = analyze_trend(top5)
        except AnalysisError as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

    # Step 5: Generate one combined video script from overall trend
    with st.spinner("Generating combined video script..."):
        combined_news = "\n\n".join(
            f"[{t['title']}]\n{topic_news[t['title']]}"
            for t in top5
            if topic_news.get(t["title"])
        )
        try:
            combined_content = generate_content(
                trend_summary, news_context=combined_news
            )
        except GenerationError as e:
            st.error(f"Video script generation failed: {e}")
            st.stop()

    # Step 6: Generate individual text post + image prompt per topic
    topic_posts: list[dict] = []
    post_progress = st.progress(0, text="Generating individual posts...")
    for i, topic in enumerate(top5):
        post_progress.progress(
            (i + 1) / len(top5), text=f"Writing post for: {topic['title']}"
        )
        try:
            post = generate_topic_post(
                topic_title=topic["title"],
                news_context=topic_news.get(topic["title"], ""),
            )
            topic_posts.append(
                {
                    "topic": topic,
                    "articles": topic_articles.get(topic["title"], []),
                    "post": post,
                    "error": None,
                }
            )
        except GenerationError as e:
            topic_posts.append(
                {
                    "topic": topic,
                    "articles": topic_articles.get(topic["title"], []),
                    "post": None,
                    "error": str(e),
                }
            )
    post_progress.empty()

    st.session_state.update(
        {
            "trend_summary": trend_summary,
            "combined_content": combined_content,
            "topic_posts": topic_posts,
            "all_topics": all_topics,
            "country": country,
        }
    )

# ── Display results ───────────────────────────────────────────────────────────
if "topic_posts" in st.session_state:
    trend_summary = st.session_state["trend_summary"]
    combined_content = st.session_state["combined_content"]
    topic_posts = st.session_state["topic_posts"]
    all_topics = st.session_state["all_topics"]
    country = st.session_state["country"]

    # Overall trend analysis
    with st.expander("🔍 Overall Trend Analysis", expanded=False):
        st.write("**Why it's trending:**", trend_summary.why_trending)
        st.write("**Sentiment:**", trend_summary.sentiment)
        st.write("**Key joke / cultural reference:**", trend_summary.key_joke)

    # Combined video script
    with st.expander("🎬 Combined Video Script (all 5 topics)", expanded=False):
        st.text_area(
            "video_script",
            value=combined_content.video_script,
            height=200,
            disabled=True,
            label_visibility="collapsed",
        )

    st.divider()
    st.subheader(f"📋 Individual Posts — Top 5 Trends in {country}")

    tw_creds_ok = all([tw_api_key, tw_api_secret, tw_access_token, tw_access_secret])
    ig_creds_ok = all([ig_access_token, ig_account_id])

    # Render 5 topic cards in a 2-column grid (3 on top row, 2 on bottom)
    for row_start in range(0, len(topic_posts), 2):
        cols = st.columns(2)
        for col_idx, item in enumerate(topic_posts[row_start : row_start + 2]):
            with cols[col_idx]:
                topic = item["topic"]
                articles = item["articles"]
                post = item["post"]
                error = item["error"]
                traffic = (
                    f" · {topic.get('traffic', 'N/A')} searches"
                    if topic.get("traffic") and topic["traffic"] != "N/A"
                    else ""
                )

                with st.container(border=True):
                    st.markdown(f"### 🔥 {topic['title']}{traffic}")

                    # News articles
                    if articles:
                        with st.expander("📰 News articles", expanded=False):
                            for a in articles:
                                st.markdown(f"- [{a.title}]({a.url}) — *{a.source}*")
                                if a.snippet:
                                    st.caption(a.snippet)
                    else:
                        st.caption("No news articles found.")

                    if error:
                        st.error(f"Generation failed: {error}")
                    elif post:
                        st.write("**📝 Text Post:**")
                        st.info(post.text_post)

                        st.write("**🎨 Image Prompt:**")
                        st.text_area(
                            f"img_{row_start}_{col_idx}",
                            value=post.image_prompt,
                            height=80,
                            disabled=True,
                            label_visibility="collapsed",
                        )

                        # Image generation button
                        cf_key = (
                            cf_api_key_input.strip()
                            or AppConfig().cloudfare_api_key
                            or ""
                        )
                        if st.button(
                            "🎨 Generate Image",
                            key=f"gen_img_{row_start}_{col_idx}",
                            use_container_width=True,
                            disabled=not cf_key,
                            help=(
                                "Add CLOUDFARE_API_KEY to .env or enter it in the sidebar."
                                if not cf_key
                                else ""
                            ),
                        ):
                            with st.spinner("Generating image..."):
                                try:
                                    img_bytes = generate_image(
                                        prompt=post.image_prompt,
                                        api_key=cf_key,
                                    )
                                    st.session_state[f"img_{row_start}_{col_idx}"] = (
                                        img_bytes
                                    )
                                except ImageGenerationError as e:
                                    st.error(f"Image generation failed: {e}")

                        # Display generated image if available
                        img_key = f"img_{row_start}_{col_idx}"
                        if img_key in st.session_state:
                            st.image(
                                st.session_state[img_key],
                                caption=topic["title"],
                                use_container_width=True,
                            )
                            st.download_button(
                                label="⬇️ Download Image",
                                data=st.session_state[img_key],
                                file_name=f"{topic['title'][:40].replace(' ', '_')}.png",
                                mime="image/png",
                                key=f"dl_{row_start}_{col_idx}",
                                use_container_width=True,
                            )

                        # Publish buttons
                        p1, p2 = st.columns(2)
                        with p1:
                            if st.button(
                                "🐦 Post to X",
                                key=f"tw_{row_start}_{col_idx}",
                                use_container_width=True,
                                disabled=not tw_creds_ok,
                                help=(
                                    "Add Twitter credentials in sidebar."
                                    if not tw_creds_ok
                                    else ""
                                ),
                            ):
                                with st.spinner("Posting..."):
                                    try:
                                        url = post_to_twitter(
                                            text=post.text_post,
                                            api_key=tw_api_key,
                                            api_secret=tw_api_secret,
                                            access_token=tw_access_token,
                                            access_token_secret=tw_access_secret,
                                        )
                                        st.success(f"[View tweet]({url})")
                                    except TwitterPublishError as e:
                                        st.error(str(e))

                        with p2:
                            if st.button(
                                "📸 Post to IG",
                                key=f"ig_{row_start}_{col_idx}",
                                use_container_width=True,
                                disabled=not ig_creds_ok,
                                help=(
                                    "Add Instagram credentials in sidebar."
                                    if not ig_creds_ok
                                    else ""
                                ),
                            ):
                                with st.spinner("Posting..."):
                                    try:
                                        kwargs = dict(
                                            caption=post.text_post,
                                            access_token=ig_access_token,
                                            instagram_account_id=ig_account_id,
                                        )
                                        if ig_image_url.strip():
                                            kwargs["image_url"] = ig_image_url.strip()
                                        url = post_to_instagram(**kwargs)
                                        st.success(f"[View post]({url})")
                                    except InstagramPublishError as e:
                                        st.error(str(e))
