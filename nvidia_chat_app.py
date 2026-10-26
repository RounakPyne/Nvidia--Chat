
import json
import uuid

import streamlit as st
from openai import OpenAI

# ---------- Page configuration ----------
st.set_page_config(
    page_title="Nemotron Chat",
    page_icon="✻",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown(
    """
    <style>
    :root {
        --bg: #FAF9F5;
        --side: #F0EEE6;
        --text: #3D3929;
        --muted: #83827D;
        --accent: #C96442;
        --bubble: #EDEADF;
        --line: #E3E0D5;
    }

    html, body, .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background: var(--bg) !important;
        color: var(--text);
    }

    /* Keep the header and sidebar toggle accessible */
    [data-testid="stHeader"] {
        background: var(--bg) !important;
    }

    [data-testid="stToolbar"] {
        visibility: visible !important;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--side) !important;
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] > div:first-child {
        background: var(--side) !important;
    }

    [data-testid="stSidebar"] * {
        color: var(--text);
    }

    /* Preserve the sidebar expand control when collapsed */
    [data-testid="stSidebarCollapsedControl"] {
        visibility: visible !important;
        display: flex !important;
    }

    /* Typography */
    h1, h2, h3, .welcome, .brand {
        font-family: Georgia, "Times New Roman", serif !important;
        font-weight: 400 !important;
        color: var(--text) !important;
    }

    .brand {
        font-size: 1.5rem;
        margin-bottom: 0.6rem;
    }

    .brand span {
        color: var(--accent);
    }

    .sec {
        font-size: 0.8rem;
        color: var(--muted);
        margin: 0.9rem 0 0.2rem 0.2rem;
    }

    .welcome {
        text-align: center;
        font-size: 2.4rem;
        margin-top: 18vh;
        line-height: 1.3;
    }

    .welcome span {
        color: var(--accent);
        margin-right: 10px;
    }

    .sub {
        text-align: center;
        color: var(--muted);
        margin-top: -6px;
    }

    /* Chat messages */
    [data-testid="stChatMessageAvatarUser"],
    [data-testid="stChatMessageAvatarAssistant"] {
        display: none;
    }

    [data-testid="stChatMessage"] {
        background: transparent;
        padding: 0.4rem 0;
    }

    [data-testid="stChatMessage"]:has(
        [data-testid="stChatMessageAvatarUser"]
    ) {
        background: var(--bubble);
        border-radius: 16px;
        padding: 0.7rem 1rem;
        margin: 0.8rem 0 0.4rem auto;
        width: fit-content;
        max-width: 85%;
    }

    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li {
        font-size: 1.02rem;
        line-height: 1.65;
    }

    [data-testid="stExpander"] {
        border: 1px solid var(--line) !important;
        border-radius: 12px;
        background: transparent;
    }

    /* Chat input */
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] {
        background: var(--bg) !important;
    }

    [data-testid="stChatInput"] {
        border: 1px solid var(--line) !important;
        border-radius: 22px !important;
        background: #FFFFFF !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    }

    [data-testid="stChatInput"] textarea {
        background: #FFFFFF !important;
        color: var(--text) !important;
    }

    [data-testid="stChatInputSubmitButton"] {
        background: var(--accent) !important;
        color: #FFFFFF !important;
        border-radius: 10px;
    }

    /* Buttons */
    .stButton > button {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 10px;
        color: var(--text);
        text-align: left;
        justify-content: flex-start;
    }

    .stButton > button:hover {
        background: #E6E3D8;
        border-color: transparent;
        color: var(--text);
    }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        background: #FFFFFF !important;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Session state ----------
S = st.session_state

if "chats" not in S:
    S.chats = {}

if "current" not in S:
    S.current = None

if "imported" not in S:
    S.imported = None


# ---------- Chat functions ----------
def new_chat():
    S.current = None


def open_chat(cid):
    S.current = cid


def toggle_pin(cid):
    if cid in S.chats:
        S.chats[cid]["pinned"] = not S.chats[cid].get(
            "pinned", False
        )


def delete_chat(cid):
    S.chats.pop(cid, None)

    if S.current == cid:
        S.current = None


def chat_item(cid):
    chat_data = S.chats[cid]

    c1, c2, c3 = st.columns([6, 1.2, 1.2])

    title = chat_data.get("title", "New chat")
    if len(title) > 26:
        title = title[:25] + "…"

    c1.button(
        title,
        key=f"open_{cid}",
        on_click=open_chat,
        args=(cid,),
        use_container_width=True,
    )

    c2.button(
        "★" if chat_data.get("pinned", False) else "☆",
        key=f"pin_{cid}",
        on_click=toggle_pin,
        args=(cid,),
        help="Pin / unpin",
    )

    c3.button(
        "✕",
        key=f"del_{cid}",
        on_click=delete_chat,
        args=(cid,),
        help="Delete chat",
    )


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(
        '<div class="brand"><span>✻</span> Nemotron</div>',
        unsafe_allow_html=True,
    )

    st.button(
        "＋ New chat",
        on_click=new_chat,
        use_container_width=True,
    )

    query = st.text_input(
        "Search",
        placeholder="🔍 Search chats",
        label_visibility="collapsed",
        key="chat_search",
    ).strip().lower()

    def matches(chat_data):
        if not query:
            return True

        searchable_text = (
            chat_data.get("title", "")
            + " "
            + " ".join(
                message.get("content", "")
                for message in chat_data.get("messages", [])
            )
        )

        return query in searchable_text.lower()

    ids = [
        cid
        for cid in reversed(list(S.chats.keys()))
        if matches(S.chats[cid])
    ]

    pinned = [
        cid for cid in ids
        if S.chats[cid].get("pinned", False)
    ]

    recent = [
        cid for cid in ids
        if not S.chats[cid].get("pinned", False)
    ]

    if pinned:
        st.markdown(
            '<div class="sec">Pinned</div>',
            unsafe_allow_html=True,
        )
        for cid in pinned:
            chat_item(cid)

    if recent:
        st.markdown(
            '<div class="sec">Recents</div>',
            unsafe_allow_html=True,
        )
        for cid in recent:
            chat_item(cid)

    if query and not ids:
        st.caption("No chats found.")

    st.markdown(
        '<div class="sec">Customize</div>',
        unsafe_allow_html=True,
    )

    with st.expander("Settings", expanded=not bool(S.get("api_key"))):
        user_name = st.text_input(
            "Your name",
            value="Rounak",
            key="user_name",
        )

        api_key = st.text_input(
            "NVIDIA API Key",
            type="password",
            placeholder="nvapi-...",
            key="api_key",
        )

        model = st.text_input(
            "Model ID",
            value="nvidia/nemotron-3-ultra-550b-a55b",
            key="model_id",
        )

        thinking = st.toggle(
            "Thinking mode",
            value=False,
            key="thinking_mode",
        )

        system_prompt = st.text_area(
            "System prompt",
            value="You are a helpful assistant.",
            key="system_prompt",
        )

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.5,
            value=1.0,
            step=0.05,
            key="temperature",
        )

        max_tokens = st.slider(
            "Max tokens",
            min_value=256,
            max_value=16384,
            value=4096,
            step=256,
            key="max_tokens",
        )

    with st.expander("Save / load chats"):
        st.caption(
            "Download chats to keep them, or upload a JSON backup "
            "to restore them."
        )

        st.download_button(
            "Download all chats",
            data=json.dumps(S.chats, ensure_ascii=False, indent=2),
            file_name="chats.json",
            mime="application/json",
            use_container_width=True,
        )

        uploaded_file = st.file_uploader(
            "Load chats",
            type="json",
            label_visibility="collapsed",
            key="chat_upload",
        )

        if uploaded_file is not None:
            upload_signature = (
                uploaded_file.name,
                uploaded_file.size,
            )

            if S.imported != upload_signature:
                try:
                    imported_chats = json.loads(
                        uploaded_file.getvalue()
                    )

                    if not isinstance(imported_chats, dict):
                        raise ValueError(
                            "The JSON must contain a chat dictionary."
                        )

                    for cid, chat_data in imported_chats.items():
                        if (
                            isinstance(chat_data, dict)
                            and isinstance(
                                chat_data.get("messages", []), list
                            )
                        ):
                            chat_data.setdefault("title", "Imported chat")
                            chat_data.setdefault("pinned", False)
                            S.chats[cid] = chat_data

                    S.imported = upload_signature
                    st.rerun()

                except (ValueError, TypeError, json.JSONDecodeError):
                    st.error("That file couldn't be read.")


# ---------- Current conversation ----------
chat = S.chats.get(S.current)
messages = chat["messages"] if chat else []

# ---------- Welcome screen ----------
if not messages:
    st.markdown(
        f'<div class="welcome"><span>✻</span> Hi, '
        f'{user_name or "there"}</div>',
        unsafe_allow_html=True,
    )

    if not api_key:
        st.markdown(
            '<p class="sub">Open Customize in the sidebar and '
            'paste your NVIDIA API key to begin.</p>',
            unsafe_allow_html=True,
        )

# ---------- Render history ----------
for message in messages:
    with st.chat_message(message["role"]):
        if message.get("reasoning"):
            with st.expander("Thinking"):
                st.markdown(message["reasoning"])

        st.markdown(message.get("content", ""))


# ---------- Chat input ----------
if prompt := st.chat_input("How can I help you today?"):

    if not api_key.strip():
        st.warning(
            "Paste your NVIDIA API key in Customize (sidebar) first."
        )
        st.stop()

    if chat is None:
        cid = uuid.uuid4().hex[:8]

        S.chats[cid] = {
            "title": prompt.strip().split("\n")[0][:40] or "New chat",
            "messages": [],
            "pinned": False,
        }

        S.current = cid
        chat = S.chats[cid]
        messages = chat["messages"]

    messages.append({
        "role": "user",
        "content": prompt,
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key.strip(),
    )

    api_messages = [
        {"role": "system", "content": system_prompt}
    ] + [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in messages
        if message["role"] in ("user", "assistant")
    ]

    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=api_messages,
                temperature=temperature,
                top_p=0.95,
                max_tokens=max_tokens,
                extra_body={
                    "chat_template_kwargs": {
                        "enable_thinking": thinking
                    }
                },
                stream=True,
            )

            think_placeholder = None

            if thinking:
                with st.expander("Thinking", expanded=True):
                    think_placeholder = st.empty()

            answer_placeholder = st.empty()
            reasoning = ""
            reply = ""

            for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                reasoning_chunk = getattr(
                    delta, "reasoning_content", None
                )

                if reasoning_chunk and think_placeholder is not None:
                    reasoning += reasoning_chunk
                    think_placeholder.markdown(reasoning)

                if delta.content:
                    reply += delta.content
                    answer_placeholder.markdown(reply + "▌")

            answer_placeholder.markdown(
                reply if reply else "The model returned an empty response."
            )

            messages.append({
                "role": "assistant",
                "content": reply,
                "reasoning": reasoning,
            })

            st.rerun()

        except Exception as error:
            st.error(f"API error: {error}")
