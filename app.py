import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import json
from datetime import datetime

# 専門家のペルソナ定義
EXPERTS = {
    "🤖 汎用AI": {
        "name": "汎用AIアシスタント",
        "prompt": "あなたは親切で知識豊富なAIアシスタントです。ユーザーの質問に対して、正確で分かりやすい日本語で回答してください。",
        "description": "一般的な質問に幅広く対応"
    },
    "💻 プログラマー": {
        "name": "プログラミング専門家",
        "prompt": "あなたは経験豊富なシニアプログラマーです。コーディング、デバッグ、アーキテクチャ設計に関する質問に対して、実践的で具体的なアドバイスを日本語で提供してください。コード例を含めて説明してください。",
        "description": "プログラミング・技術的な質問に特化"
    },
    "📚 教師": {
        "name": "教育専門家",
        "prompt": "あなたは優秀な教師です。複雑な概念を分かりやすく、段階的に説明してください。例え話や図解を用いて、初心者にも理解できるよう丁寧に教えてください。日本語で回答してください。",
        "description": "学習・教育に関する質問に最適"
    },
    "⚕️ 医療アドバイザー": {
        "name": "医療知識アドバイザー",
        "prompt": "あなたは医療知識に詳しいアドバイザーです。健康や医療に関する一般的な情報を提供しますが、必ず「専門医に相談してください」という注意書きを含めてください。日本語で回答してください。",
        "description": "健康・医療の一般的な情報提供"
    },
    "🍳 シェフ": {
        "name": "料理の専門家",
        "prompt": "あなたは経験豊富なプロのシェフです。料理のレシピ、調理技術、食材の選び方について、実践的なアドバイスを日本語で提供してください。具体的な手順と調理のコツを含めて説明してください。",
        "description": "料理・レシピに関する質問に特化"
    },
    "💼 ビジネスコンサルタント": {
        "name": "ビジネス戦略家",
        "prompt": "あなたは経験豊富なビジネスコンサルタントです。経営戦略、マーケティング、業務改善について、データに基づいた実践的なアドバイスを日本語で提供してください。",
        "description": "ビジネス・経営に関する相談に対応"
    },
    "✍️ ライター": {
        "name": "文章作成の専門家",
        "prompt": "あなたはプロのライター・編集者です。魅力的で読みやすい文章の作成、編集、校正について、具体的なアドバイスを日本語で提供してください。文章の改善案も提示してください。",
        "description": "文章作成・編集に関する質問に特化"
    }
}

# APIキーの取得（ローカル環境とStreamlit Cloud両方に対応）
def get_api_key():
    """
    優先順位:
    1. 環境変数（.envファイル経由） - ローカル開発用
    2. Streamlit Cloud のシークレット - デプロイ用
    """
    # まず環境変数（.envファイル）から取得を試みる
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    # 環境変数がない場合、Streamlit Cloud のシークレットを確認
    if hasattr(st, "secrets") and "OPENAI_API_KEY" in st.secrets:
        return st.secrets["OPENAI_API_KEY"]
    
    # どちらもない場合はエラーメッセージを表示
    st.error("⚠️ OpenAI APIキーが設定されていません。")
    st.info("**ローカルで実行する場合:**\n.envファイルを作成し、`OPENAI_API_KEY=your-api-key`を追加してください。")
    st.info("**Streamlit Cloudで実行する場合:**\nアプリの設定（⋮ → Settings → Secrets）でシークレットを追加してください。")
    st.stop()
    return None

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
if "selected_expert" not in st.session_state:
    st.session_state.selected_expert = "🤖 汎用AI"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = ChatMessageHistory()

# サイドバー設定
with st.sidebar:
    st.title("⚙️ 設定")
    
    # 専門家選択
    st.subheader("🎭 専門家を選択")
    selected_expert = st.radio(
        "相談したい専門家",
        list(EXPERTS.keys()),
        index=list(EXPERTS.keys()).index(st.session_state.selected_expert),
        help="質問内容に応じて適切な専門家を選択してください"
    )
    
    # 専門家が変更された場合
    if selected_expert != st.session_state.selected_expert:
        st.session_state.selected_expert = selected_expert
        st.session_state.messages = []
        st.session_state.chat_history.clear()
        st.rerun()
    
    # 選択された専門家の説明を表示
    st.info(f"**{EXPERTS[selected_expert]['name']}**\n\n{EXPERTS[selected_expert]['description']}")
    
    st.divider()
    
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
            st.session_state.chat_history.clear()
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
current_expert = EXPERTS[st.session_state.selected_expert]
st.title(f"{st.session_state.selected_expert} AI チャットアシスタント")
st.caption(f"現在の専門家: {current_expert['name']}")
st.markdown("---")

# LangChain セットアップ
api_key = get_api_key()
if api_key:
    llm = ChatOpenAI(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=True
    )
    
    # プロンプトテンプレートの作成
    prompt = ChatPromptTemplate.from_messages([
        ("system", current_expert['prompt']),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])
    
    # チェーンの作成
    chain = prompt | llm
else:
    st.stop()

# チャット履歴表示
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

# ユーザー入力
if prompt_input := st.chat_input("メッセージを入力してください..."):
    # ユーザーメッセージを追加
    st.session_state.messages.append({"role": "user", "content": prompt_input})
    st.session_state.chat_history.add_user_message(prompt_input)
    
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt_input)
    
    # AIレスポンス生成
    with st.chat_message("assistant", avatar=st.session_state.selected_expert.split()[0]):
        message_placeholder = st.empty()
        full_response = ""
        
        # LangChainでストリーミングレスポンス
        with st.spinner("考え中..."):
            try:
                # ストリーミング対応
                for chunk in chain.stream({
                    "input": prompt_input,
                    "history": st.session_state.chat_history.messages
                }):
                    if hasattr(chunk, 'content'):
                        full_response += chunk.content
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                
                # チャット履歴に追加
                st.session_state.chat_history.add_ai_message(full_response)
                
                # トークン使用量の更新（概算）
                st.session_state.total_tokens += len(prompt_input.split()) + len(full_response.split())
                
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
                full_response = "申し訳ございません。エラーが発生しました。"
        
        # アシスタントメッセージを追加
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# フッター
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    💡 ヒント: サイドバーで異なる専門家を選択して、専門的なアドバイスを受けられます
    </div>
    """,
    unsafe_allow_html=True
) 
