# 議事メモRAGチャットボット - 納品パッケージ

## 📦 納品物の概要

このパッケージには、議事メモを自動学習し質問応答を行うRAGチャットボットシステムが含まれています。

---

## 🎯 主な特徴

### 機能面
- ✅ 議事メモの自動取り込みとベクトル化
- ✅ 自然言語での質問応答（RAG方式）
- ✅ 差分更新による効率的なデータ管理
- ✅ Google Drive / SharePoint 両対応
- ✅ 日次自動更新機能
- ✅ 使いやすいWebインターフェース

### 品質面
- ✅ **75個のテストケース**による品質保証
- ✅ 開発AI・テスターAIの二重チェック体制
- ✅ 型安全性（全関数に型ヒント）
- ✅ 包括的なエラーハンドリング
- ✅ SOLID原則に基づいた設計
- ✅ 依存性の注入によるテスタビリティ

---

## 📂 パッケージ構成

```
議事メモツール/
├── 📚 ドキュメント（必読）
│   ├── README.md                  # プロジェクト概要とクイックスタート
│   ├── INSTALLATION.md            # 詳細インストール手順
│   ├── DEPLOYMENT.md              # デプロイ・運用ガイド
│   ├── TESTING_GUIDE.md           # テスト実行ガイド
│   ├── CONTRIBUTING.md            # 開発貢献ガイド
│   ├── PROJECT_STRUCTURE.md       # プロジェクト構造
│   ├── CHANGELOG.md               # 変更履歴
│   └── DELIVERY_README.md         # このファイル
│
├── 🎯 アプリケーション
│   ├── app/                       # メインアプリケーション
│   │   ├── main.py               # Streamlit Webアプリ
│   │   ├── config/               # 設定管理
│   │   ├── data_sources/         # データソース抽象化
│   │   ├── vector_store/         # ベクターDB管理
│   │   ├── rag/                  # RAGエンジン
│   │   └── utils/                # ユーティリティ
│   │
│   └── scripts/                   # 運用スクリプト
│       └── update_vector_store.py # ベクターストア更新
│
├── 🧪 テスト
│   ├── tests/                     # テストコード（75個）
│   │   ├── test_config/          # 設定テスト
│   │   ├── test_data_sources/    # データソーステスト
│   │   ├── test_utils/           # ユーティリティテスト
│   │   └── test_adversarial/     # 統合攻撃テスト
│   │
│   └── pytest.ini                 # pytest設定
│
├── 📄 設定ファイル
│   ├── .env.example              # 環境変数テンプレート
│   ├── credentials.json.example  # Google認証テンプレート
│   ├── requirements.txt          # 依存パッケージ
│   ├── .gitignore               # Git除外設定
│   ├── .cursorrules             # AI開発ルール
│   └── LICENSE                  # MITライセンス
│
└── 📦 その他
    └── Archive/                  # 参考資料・テストデータ
```

---

## 🚀 セットアップ（クイックスタート）

### ステップ1: 環境準備

```bash
# プロジェクトディレクトリに移動
cd 議事メモツール

# 仮想環境の作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

### ステップ2: 環境変数の設定

```bash
# テンプレートをコピー
cp .env.example .env

# .envファイルを編集
# 最低限必要な設定:
# - OPENAI_API_KEY
# - DATA_SOURCE (google_drive または sharepoint)
# - データソースに応じた認証情報
```

### ステップ3: 認証情報の設定

**Google Driveの場合:**
```bash
# credentials.jsonを配置
cp /path/to/your/credentials.json ./credentials.json
```

**SharePointの場合:**
`.env`にAzure認証情報を設定

### ステップ4: 初回データ取り込み

```bash
python scripts/update_vector_store.py
```

### ステップ5: アプリケーション起動

```bash
streamlit run app/main.py
```

ブラウザで `http://localhost:8501` にアクセス

---

## 📖 詳細ドキュメント

### 必読ドキュメント

1. **[README.md](README.md)**
   - プロジェクトの全体像
   - 主要機能の説明
   - 基本的な使い方

2. **[INSTALLATION.md](INSTALLATION.md)**
   - 詳細なインストール手順
   - Google Drive / SharePoint の設定方法
   - トラブルシューティング

3. **[DEPLOYMENT.md](DEPLOYMENT.md)**
   - 本番環境へのデプロイ方法
   - systemd / Docker での運用
   - 日次更新の設定
   - 監視とメンテナンス

### 開発者向けドキュメント

4. **[TESTING_GUIDE.md](TESTING_GUIDE.md)**
   - テストの実行方法
   - テストの種類と観点
   - カバレッジ測定

5. **[CONTRIBUTING.md](CONTRIBUTING.md)**
   - 開発環境のセットアップ
   - コーディング規約
   - プルリクエストの方法

6. **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)**
   - ディレクトリ構造の詳細
   - 各コンポーネントの役割

---

## 🧪 品質保証

### テスト体制

このプロジェクトは「**開発AI vs テスターAI**」の二重チェック体制で開発されました。

- **開発AI**: 堅牢なコードの実装
- **テスターAI**: 意地悪なテストによるバグ発見

### テスト統計

- **総テスト数**: 75個
- **テストカテゴリ**:
  - 境界値攻撃: 25個
  - 型攻撃: 20個
  - セキュリティ攻撃: 10個
  - リソース攻撃: 8個
  - 統合テスト: 12個

### テストの実行

```bash
# すべてのテストを実行
pytest tests/ -v

# カバレッジ付きで実行
pytest tests/ --cov=app --cov-report=html

# 意地悪なテストのみ実行
pytest tests/ -m adversarial -v
```

---

## 🔧 技術スタック

### コア技術
- **Python 3.9+**: プログラミング言語
- **OpenAI API**: 埋め込み生成・質問応答
- **ChromaDB**: ベクターデータベース
- **LangChain**: RAGフレームワーク
- **Streamlit**: Webインターフェース

### データソース
- **Google Drive API**: プロトタイプ環境
- **Microsoft Graph API**: 本番環境（SharePoint）

### テスト
- **pytest**: テストフレームワーク
- **pytest-cov**: カバレッジ測定
- **pytest-mock**: モック機能
- **pytest-timeout**: タイムアウト設定
- **pytest-xdist**: 並列実行

---

## 📊 システム要件

### 最小要件
- Python 3.9以上
- 2GB RAM
- 10GB ディスク容量
- インターネット接続

### 推奨要件
- Python 3.11以上
- 4GB RAM
- 20GB ディスク容量（SSD推奨）
- 安定したインターネット接続

### 必要なアカウント
- OpenAI API（有料プラン推奨）
- Google Cloud Platform（Google Drive使用時）
- Microsoft Azure（SharePoint使用時）

---

## 💰 コスト見積もり

### OpenAI API コスト（目安）

**初回データ取り込み（100件の議事メモ）:**
- Embedding: 約 $0.10 - $0.50
- 初回質問応答: 約 $0.01 - $0.05 / 質問

**日次更新（10件の新規/更新）:**
- Embedding: 約 $0.01 - $0.05 / 日

**月間運用コスト（想定）:**
- 100質問/日の場合: 約 $5 - $20 / 月

※実際のコストは使用量により変動します

---

## 🔒 セキュリティ

### 実装済みのセキュリティ対策

- ✅ 環境変数による機密情報の管理
- ✅ 入力値の検証とサニタイゼーション
- ✅ パストラバーサル攻撃への対策
- ✅ SQLインジェクション対策
- ✅ XSS対策
- ✅ 適切なエラーハンドリング

### 推奨事項

- 本番環境では HTTPS を使用
- 定期的なセキュリティアップデート
- アクセスログの監視
- APIキーのローテーション

---

## 🆘 サポート

### トラブルシューティング

問題が発生した場合:

1. [INSTALLATION.md](INSTALLATION.md#-トラブルシューティング)を確認
2. ログファイル（`logs/`）を確認
3. テストを実行して問題を特定

### お問い合わせ

以下の情報を添えてお問い合わせください:
- エラーメッセージの全文
- 実行したコマンド
- ログファイル
- 環境情報（Python バージョン、OS）

```bash
# 環境情報の取得
python --version
pip list > installed_packages.txt
```

---

## 📝 ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下で公開されています。

---

## 🎉 謝辞

このプロジェクトは、以下の技術・ツールを活用して開発されました:

- OpenAI GPT-4 & Embeddings
- LangChain Framework
- ChromaDB
- Streamlit
- pytest

また、開発AI・テスターAIの二重チェック体制により、高品質なコードを実現しました。

---

## 📞 次のステップ

1. ✅ [INSTALLATION.md](INSTALLATION.md)を読んでセットアップ
2. ✅ テストデータで動作確認
3. ✅ 本番データで初回取り込み
4. ✅ [DEPLOYMENT.md](DEPLOYMENT.md)を読んで本番デプロイ
5. ✅ 日次更新の設定
6. ✅ 運用開始

---

**プロジェクトの成功を祈っています！🚀**

何か質問があれば、ドキュメントを参照するか、開発チームにお問い合わせください。

