# 🤖 AI チャットアシスタント

LangChainとOpenAI APIを使用した、専門家を選択できる高機能チャットアプリケーションです。

## ✨ 機能

- **7人の専門家から選択可能**
  - 🤖 汎用AI - 一般的な質問に対応
  - 💻 プログラマー - コーディング・技術的な質問
  - 📚 教師 - 学習・教育に関する質問
  - ⚕️ 医療アドバイザー - 健康・医療の一般情報
  - 🍳 シェフ - 料理・レシピの質問
  - 💼 ビジネスコンサルタント - 経営戦略・マーケティング
  - ✍️ ライター - 文章作成・編集

- **LangChain統合** - 会話の文脈を保持、ストリーミングレスポンス対応
- **カスタマイズ可能な設定** - AIモデル選択、Temperature調整、最大トークン数設定
- **チャット履歴管理** - 会話履歴のクリア、JSON形式でのダウンロード

## 🚀 ローカルでの実行方法

### 1. 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

プロジェクトルートに `.env` ファイルを作成し、OpenAI APIキーを設定します：

```env
OPENAI_API_KEY=your-api-key-here
```

**APIキーの取得:** [OpenAI Platform](https://platform.openai.com/api-keys)

⚠️ `.env` ファイルは `.gitignore` に含まれており、Gitにコミットされません。

### 3. アプリの起動

```bash
streamlit run app.py
```

ブラウザで http://localhost:8501 にアクセス

## ☁️ Streamlit Cloudでのデプロイ

1. [Streamlit Community Cloud](https://share.streamlit.io/) にアクセス
2. 「New app」でこのリポジトリを選択
3. **Settings → Secrets** で以下を設定：

```toml
OPENAI_API_KEY = "your-api-key-here"
```

## 🔧 環境変数の読み込み順序

1. **`.env` ファイル** （ローカル開発用・優先）
2. **Streamlit Secrets** （デプロイ用）

## 📦 依存パッケージ

- streamlit, openai, python-dotenv
- langchain, langchain-openai, langchain-community