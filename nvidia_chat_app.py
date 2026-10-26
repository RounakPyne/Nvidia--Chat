import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="NVIDIA AI Chat", page_icon="🟢")
st.title("🟢 NVIDIA AI Chat")

# ---------- Sidebar: just paste your key ----------
with st.sidebar:
    api_key = st.text_input("NVIDIA API Key", type="password", placeholder="nvapi-...")
    model = st.text_input("Model ID", value="nvidia/nemotron-3-ultra-550b-a55b")
    thinking = st.toggle("Thinking mode", value=True)
    system_prompt = st.text_area("System prompt", "You are a helpful assistant.")
    temperature = st.slider("Temperature", 0.0, 1.5, 1.0, 0.05)
    max_tokens = st.slider("Max tokens", 256, 16384, 4096, 256)
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- Show history ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if m.get("reasoning"):
            with st.expander("Thinking"):
                st.markdown(m["reasoning"])
        st.markdown(m["content"])

# ---------- Chat ----------
if prompt := st.chat_input("Ask something..."):
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
                model=model,
                messages=msgs,
                temperature=temperature,
                top_p=0.95,
                max_tokens=max_tokens,
                extra_body={"chat_template_kwargs": {"enable_thinking": thinking}},
                stream=True,
            )
            think_box = st.expander("Thinking", expanded=True) if thinking else None
            think_ph = think_box.empty() if think_box else None
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
            st.session_state.messages.append(
                {"role": "assistant", "content": reply, "reasoning": reasoning}
            )
        except Exception as e:
            st.error(f"Error: {e}")
