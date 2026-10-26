import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Nemotron Chat", page_icon="✻", layout="centered")

# ---------- Claude-style look ----------
st.markdown("""
<style>
:root { --bg:#FAF9F5; --side:#F0EEE6; --text:#3D3929; --muted:#83827D; --accent:#C96442; --bubble:#EDEADF; --line:#E3E0D5; }
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: var(--bg) !important; color: var(--text); }
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stSidebar"] { background: var(--side) !important; border-right: 1px solid var(--line); }
[data-testid="stSidebar"] * { color: var(--text); }
h1, h2, h3, .welcome { font-family: Georgia, "Times New Roman", serif !important; font-weight: 400 !important; color: var(--text) !important; }
.welcome { text-align:center; font-size: 2.4rem; margin-top: 22vh; line-height: 1.3; }
.welcome span { color: var(--accent); margin-right: 10px; }
.sub { text-align:center; color: var(--muted); margin-top: -6px; }

/* messages */
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] { display:none !important; }
[data-testid="stChatMessage"] { background: transparent; padding: 0.4rem 0; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background: var(--bubble); border-radius: 16px; padding: 0.7rem 1rem; margin: 0.8rem 0 0.4rem auto; width: fit-content; max-width: 85%;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li { font-size: 1.02rem; line-height: 1.65; }
[data-testid="stExpander"] { border: 1px solid var(--line) !important; border-radius: 12px; background: transparent; }

/* input box */
[data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"] { background: var(--bg) !important; }
[data-testid="stChatInput"] { border: 1px solid var(--line) !important; border-radius: 22px !important; background: #FFFFFF !important; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
[data-testid="stChatInput"] textarea { background: #FFFFFF !important; color: var(--text) !important; }
[data-testid="stChatInputSubmitButton"] { background: var(--accent) !important; color:#fff !important; border-radius: 10px; }

/* buttons & inputs */
.stButton > button { background: transparent; border: 1px solid var(--line); border-radius: 10px; color: var(--text); }
.stButton > button:hover { border-color: var(--accent); color: var(--accent); }
[data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea { background: #FFFFFF !important; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    if st.button("＋  New chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("### Settings")
    api_key = st.text_input("NVIDIA API Key", type="password", placeholder="nvapi-...")
    model = st.text_input("Model ID", value="nvidia/nemotron-3-ultra-550b-a55b")
    thinking = st.toggle("Thinking mode", value=True)
    system_prompt = st.text_area("System prompt", "You are a helpful assistant.")
    temperature = st.slider("Temperature", 0.0, 1.5, 1.0, 0.05)
    max_tokens = st.slider("Max tokens", 256, 16384, 4096, 256)

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- Welcome screen ----------
if not st.session_state.messages:
    st.markdown('<div class="welcome"><span>✻</span>How can I help you today?</div>', unsafe_allow_html=True)
    if not api_key:
        st.markdown('<p class="sub">Paste your NVIDIA API key in the sidebar to begin.</p>', unsafe_allow_html=True)

# ---------- History ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if m.get("reasoning"):
            with st.expander("Thinking"):
                st.markdown(m["reasoning"])
        st.markdown(m["content"])

# ---------- Chat ----------
if prompt := st.chat_input("How can I help you today?"):
    if not api_key:
        st.warning("Paste your NVIDIA API key in the sidebar first.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)
    msgs = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model=model, messages=msgs, temperature=temperature, top_p=0.95,
                max_tokens=max_tokens,
                extra_body={"chat_template_kwargs": {"enable_thinking": thinking}},
                stream=True,
            )
            think_ph = st.expander("Thinking", expanded=True).empty() if thinking else None
            answer_ph = st.empty()
            reasoning, reply = "", ""
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                r = getattr(delta, "reasoning_content", None)
                if r and think_ph:
                    reasoning += r
                    think_ph.markdown(reasoning)
                if delta.content:
                    reply += delta.content
                    answer_ph.markdown(reply + "▌")
            answer_ph.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply, "reasoning": reasoning})
        except Exception as e:
            st.error(f"Error: {e}")
