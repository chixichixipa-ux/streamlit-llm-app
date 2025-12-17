import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from openai import OpenAI
import json
from datetime import datetime

st.set_page_config(
    page_title="🤖 AI チャットアシスタント",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッション状態の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0

# サイドバー設定
with st.sidebar:
    st.title("⚙️ 設定")
    
    st.subheader("モデル選択")
    model = st.selectbox(
        "AIモデル",
        ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        index=0,
        help="使用するOpenAIモデルを選択してください"
    )
    
    st.subheader("パラメータ調整")
    temperature = st.slider(
        "Temperature（創造性）",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="値が高いほど創造的で予測不可能な回答になります"
    )
    
    max_tokens = st.slider(
        "最大トークン数",
        min_value=100,
        max_value=4000,
        value=1000,
        step=100,
        help="生成される回答の最大長"
    )
    
    st.subheader("システムプロンプト")
    system_prompt = st.text_area(
        "AIの役割を設定",
        value="あなたは親切で知識豊富なAIアシスタントです。ユーザーの質問に対して、正確で分かりやすい日本語で回答してください。",
        height=150,
        help="AIの振る舞いや役割を設定できます"
    )
    
    st.divider()
    
    # 統計情報
    st.subheader("📊 統計情報")
    st.metric("会話のやり取り数", len(st.session_state.messages) // 2)
    st.metric("累計トークン使用量", st.session_state.total_tokens)
    
    st.divider()
    
    # チャット履歴管理
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ 履歴クリア", use_container_width=True):
            st.session_state.messages = []
            st.session_state.total_tokens = 0
            st.rerun()
    
    with col2:
        if st.button("💾 履歴保存", use_container_width=True):
            if st.session_state.messages:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"chat_history_{timestamp}.json"
                chat_data = {
                    "timestamp": timestamp,
                    "model": model,
                    "messages": st.session_state.messages
                }
                st.download_button(
                    label="📥 ダウンロード",
                    data=json.dumps(chat_data, ensure_ascii=False, indent=2),
                    file_name=filename,
                    mime="application/json",
                    use_container_width=True
                )

# メインエリア
st.title("🤖 AI チャットアシスタント")
st.markdown("---")

# OpenAIクライアント初期化
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# チャット履歴表示
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

# ユーザー入力
if prompt := st.chat_input("メッセージを入力してください..."):
    # ユーザーメッセージを追加
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)
    
    # AIレスポンス生成
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        full_response = ""
        
        # ストリーミングレスポンス
        with st.spinner("考え中..."):
            try:
                # メッセージリストを構築
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(st.session_state.messages)
                
                stream = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                
                # トークン使用量の更新（概算）
                st.session_state.total_tokens += len(prompt.split()) + len(full_response.split())
                
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
                full_response = "申し訳ございません。エラーが発生しました。"
        
        # アシスタントメッセージを追加
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# フッター
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    💡 ヒント: サイドバーでモデルやパラメータを調整できます
    </div>
    """,
    unsafe_allow_html=True
) 
