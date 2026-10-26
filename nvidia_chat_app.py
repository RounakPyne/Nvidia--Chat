import json
import uuid
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
h1, h2, h3, .welcome, .brand { font-family: Georgia, "Times New Roman", serif !important; font-weight: 400 !important; color: var(--text) !important; }
.brand { font-size: 1.5rem; margin-bottom: 0.6rem; }
.brand span { color: var(--accent); }
.sec { font-size: 0.8rem; color: var(--muted); margin: 0.9rem 0 0.2rem 0.2rem; }
.welcome { text-align:center; font-size: 2.4rem; margin-top: 22vh; line-height: 1.3; }
.welcome span { color: var(--accent); margin-right: 10px; }
.sub { text-align:center; color: var(--muted); margin-top: -6px; }

[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] { display:none !important; }
[data-testid="stChatMessage"] { background: transparent; padding: 0.4rem 0; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background: var(--bubble); border-radius: 16px; padding: 0.7rem 1rem; margin: 0.8rem 0 0.4rem auto; width: fit-content; max-width: 85%;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li { font-size: 1.02rem; line-height: 1.65; }
[data-testid="stExpander"] { border: 1px solid var(--line) !important; border-radius: 12px; background: transparent; }

[data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"] { background: var(--bg) !important; }
[data-testid="stChatInput"] { border: 1px solid var(--line) !important; border-radius: 22px !important; background: #FFFFFF !important; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
[data-testid="stChatInput"] textarea { background: #FFFFFF !important; color: var(--text) !important; }
[data-testid="stChatInputSubmitButton"] { background: var(--accent) !important; color:#fff !important; border-radius: 10px; }

.stButton > button { background: transparent; border: 1px solid transparent; border-radius: 10px; color: var(--text); text-align:left; justify-content:flex-start; }
.stButton > button:hover { background: #E6E3D8; border-color: transparent; color: var(--text); }
[data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea { background: #FFFFFF !important; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

S = st.session_state
S.setdefault("chats", {})      # id -> {"title", "messages", "pinned"}
S.setdefault("current", None)  # None = blank new chat
S.setdefault("imported", None)


def new_chat():
    S.current = None


def open_chat(cid):
    S.current = cid


def toggle_pin(cid):
    S.chats[cid]["pinned"] = not S.chats[cid]["pinned"]


def delete_chat(cid):
    S.chats.pop(cid, None)
    if S.current == cid:
        S.current = None


def chat_item(cid):
    chat = S.chats[cid]
    c1, c2, c3 = st.columns([6, 1.2, 1.2])
    title = chat["title"] if len(chat["title"]) <= 26 else chat["title"][:25] + "…"
    c1.button(title, key=f"open_{cid}", on_click=open_chat, args=(cid,), use_container_width=True)
    c2.button("★" if chat["pinned"] else "☆", key=f"pin_{cid}", on_click=toggle_pin, args=(cid,), help="Pin / unpin")
    c3.button("✕", key=f"del_{cid}", on_click=delete_chat, args=(cid,), help="Delete chat")


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div class="brand"><span>✻</span> Nemotron</div>', unsafe_allow_html=True)
    st.button("＋  New chat", on_click=new_chat, use_container_width=True)
    query = st.text_input("Search", placeholder="🔍  Search chats", label_visibility="collapsed").strip().lower()

    def matches(chat):
        if not query:
            return True
        text = chat["title"] + " " + " ".join(m["content"] for m in chat["messages"])
        return query in text.lower()

    ids = [cid for cid in reversed(list(S.chats)) if matches(S.chats[cid])]
    pinned = [c for c in ids if S.chats[c]["pinned"]]
    recent = [c for c in ids if not S.chats[c]["pinned"]]

    if pinned:
        st.markdown('<div class="sec">Pinned</div>', unsafe_allow_html=True)
        for cid in pinned:
            chat_item(cid)
    if recent:
        st.markdown('<div class="sec">Recents</div>', unsafe_allow_html=True)
        for cid in recent:
            chat_item(cid)
    if query and not ids:
        st.caption("No chats found.")

    st.markdown('<div class="sec">Customize</div>', unsafe_allow_html=True)
    with st.expander("Settings", expanded=not S.get("api_key")):
        user_name = st.text_input("Your name", value="Rounak", key="user_name")
        api_key = st.text_input("NVIDIA API Key", type="password", placeholder="nvapi-...", key="api_key")
        model = st.text_input("Model ID", value="nvidia/nemotron-3-ultra-550b-a55b")
        thinking = st.toggle("Thinking mode", value=False)
        system_prompt = st.text_area("System prompt", "You are a helpful assistant.")
        temperature = st.slider("Temperature", 0.0, 1.5, 1.0, 0.05)
        max_tokens = st.slider("Max tokens", 256, 16384, 4096, 256)

    with st.expander("Save / load chats"):
        st.caption("Chats vanish when you refresh. Download them to keep, upload to restore.")
        st.download_button("Download all chats", json.dumps(S.chats), "chats.json", "application/json", use_container_width=True)
        up = st.file_uploader("Load chats", type="json", label_visibility="collapsed")
        if up is not None and S.imported != (up.name, up.size):
            try:
                for cid, chat in json.loads(up.getvalue()).items():
                    S.chats[cid] = chat
                S.imported = (up.name, up.size)
                st.rerun()
            except Exception:
                st.error("That file couldn't be read.")

chat = S.chats.get(S.current)
messages = chat["messages"] if chat else []

# ---------- Welcome ----------
if not messages:
    st.markdown(f'<div class="welcome"><span>✻</span>Hi, {user_name or "there"}</div>', unsafe_allow_html=True)
    if not api_key:
        st.markdown('<p class="sub">Open Customize in the sidebar and paste your NVIDIA API key to begin.</p>', unsafe_allow_html=True)

# ---------- History ----------
for m in messages:
    with st.chat_message(m["role"]):
        if m.get("reasoning"):
            with st.expander("Thinking"):
                st.markdown(m["reasoning"])
        st.markdown(m["content"])

# ---------- Chat ----------
if prompt := st.chat_input("How can I help you today?"):
    if not api_key:
        st.warning("Paste your NVIDIA API key in Customize (sidebar) first.")
        st.stop()

    if chat is None:
        cid = uuid.uuid4().hex[:8]
        S.chats[cid] = {"title": prompt.strip().split("\n")[0][:40], "messages": [], "pinned": False}
        S.current = cid
        chat = S.chats[cid]
        messages = chat["messages"]

    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)
    msgs = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in messages
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
            for ch in stream:
                if not ch.choices:
                    continue
                delta = ch.choices[0].delta
                r = getattr(delta, "reasoning_content", None)
                if r and think_ph:
                    reasoning += r
                    think_ph.markdown(reasoning)
                if delta.content:
                    reply += delta.content
                    answer_ph.markdown(reply + "▌")
            answer_ph.markdown(reply)
            messages.append({"role": "assistant", "content": reply, "reasoning": reasoning})
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
