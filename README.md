# 議事メモRAGチャットボット

議事メモを自動的に学習し、質問に答えるRAGベースのチャットボットシステムです。

## 🔥 開発体制：二重チェックシステム

このプロジェクトでは「**開発AI**」と「**テスターAI**」の2つの役割を明確に分けています。

- **開発AI**: 堅牢で保守性の高いコードを実装
- **テスターAI**: 意地悪な攻撃的テストでバグを発見

詳細は `.cursorrules` ファイルを参照してください。

## 特徴

- 📚 議事メモの自動取り込みとベクターデータベース化
- 🔄 日次での差分更新（変更があった場合のみ）
- 💬 自然言語での議事メモ検索・質問応答
- 🔌 データソースの切り替え可能（Google Drive ⇄ SharePoint）
- 🎯 OpenAI APIを使用したRAG実装
- ✅ 意地悪なテストによる品質保証

## システム構成

```
プロトタイプ環境：Google Drive特定フォルダ
本番環境：SharePoint特定ディレクトリ

共通構造：
議事メモルートフォルダ/
  ├── 議事メモ1/
  │   └── 議事メモ.docx
  ├── 議事メモ2/
  │   └── 議事メモ.docx
  └── ...
```

## 🚀 クイックスタート

### 1. 依存パッケージのインストール

```bash
# 仮想環境の作成と有効化
python3 -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# パッケージのインストール
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
# .env.exampleをコピー
cp .env.example .env

# .envファイルを編集して必要な情報を設定
nano .env
```

最低限必要な設定:
- `OPENAI_API_KEY`: OpenAI APIキー
- `DATA_SOURCE`: `google_drive` または `sharepoint`
- データソースに応じた認証情報

### 3. 初回ベクターストアの構築

```bash
python scripts/update_vector_store.py
```

### 4. チャットボットの起動

```bash
streamlit run app/main.py
```

ブラウザが開き、`http://localhost:8501`でアクセスできます。

---

**📖 詳細なセットアップ手順は[docs/getting-started/INSTALLATION.md](docs/getting-started/INSTALLATION.md)を参照してください。**

## 📅 日次更新の設定

議事メモは日次で自動更新されます。設定方法は環境によって異なります：

- **Linux/macOS**: cron または systemd timer
- **Windows**: タスクスケジューラ
- **Docker**: docker-compose + cron

**📖 詳細な設定手順は[docs/deployment/DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md)を参照してください。**

## 使い方

1. Webインターフェースにアクセス
2. 質問を入力
3. 関連する議事メモから回答が生成されます

## 環境の切り替え

`.env`ファイルの`DATA_SOURCE`を変更してアプリを再起動：

```bash
# プロトタイプ環境
DATA_SOURCE=google_drive

# 本番環境
DATA_SOURCE=sharepoint
```

変更後、アプリを再起動：
```bash
streamlit run app/main.py
```

## ディレクトリ構造

```
.
├── .cursorrules                 # 【重要】AI開発環境ルール（開発AI・テスターAIの役割定義）
├── app/                         # 【開発AIの戦場】アプリケーションコード
│   ├── main.py                 # Streamlit Webアプリ（エントリーポイント）
│   ├── config/                 # 設定管理
│   ├── data_sources/           # データソース抽象化
│   ├── vector_store/           # ベクターストア管理
│   ├── rag/                    # RAGエンジン
│   └── utils/                  # ユーティリティ
├── tests/                       # 【テスターAIの戦場】テストコード（75個）
│   ├── conftest.py             # pytest共通設定とフィクスチャ
│   ├── test_config/            # 設定モジュールのテスト
│   ├── test_data_sources/      # データソースのテスト
│   ├── test_utils/             # ユーティリティのテスト
│   └── test_adversarial/       # 統合的な意地悪テスト
├── scripts/                     # 運用スクリプト
│   └── update_vector_store.py  # ベクターストア更新（日次実行用）
├── docs/                        # 📚 ドキュメント（機能別に整理）
│   ├── getting-started/        # セットアップガイド
│   ├── deployment/             # デプロイ・運用ガイド
│   ├── development/            # 開発者向けガイド
│   ├── architecture/           # アーキテクチャドキュメント
│   ├── delivery/               # 納品ドキュメント
│   └── CHANGELOG.md            # 変更履歴
├── Archive/                     # アーカイブ（参考資料・テストデータ）
├── data/                        # データ保存先（実行時に自動生成）
├── logs/                        # ログ保存先（実行時に自動生成）
├── pytest.ini                   # pytest設定ファイル
├── requirements.txt             # 依存パッケージ一覧
├── .env.example                 # 環境変数テンプレート
├── .gitignore                   # Git除外設定
├── LICENSE                      # MITライセンス
└── README.md                    # このファイル
```

### 主要コンポーネントの説明

#### アプリケーション層 (`app/`)
- **main.py**: StreamlitベースのWebインターフェース
- **config/**: 環境変数の読み込みと設定管理
- **data_sources/**: Google Drive/SharePointからのデータ取得（Strategy Pattern）
- **vector_store/**: ChromaDBとの連携とベクトル化処理
- **rag/**: RAGエンジン（質問応答システム）
- **utils/**: 差分検出、ロギングなどのユーティリティ

#### 運用層
- **scripts/**: 日次更新などの運用スクリプト
- **data/**: ベクターストアとメタデータの保存先
- **logs/**: アプリケーションログの保存先

## 🔧 トラブルシューティング

よくある問題と解決方法は[docs/getting-started/INSTALLATION.md](docs/getting-started/INSTALLATION.md#-トラブルシューティング)を参照してください。

主な問題:
- Google Drive認証エラー
- SharePoint接続エラー
- OpenAI API エラー
- ベクターストアが空

詳細なログは`logs/`ディレクトリで確認できます。

## 🧪 開発・テストワークフロー

### Phase 1: 構築フェーズ（開発AI）
1. 機能要件を理解する
2. 堅牢な設計を考える（SOLID原則、DI、型安全性）
3. `app/` に実装する
4. 自己申告の弱点を報告する

### Phase 2: 攻撃フェーズ（テスターAI）
1. 開発AIのコードをレビュー
2. `tests/` に意地悪なテストを作成
3. テストを実行
4. バグを報告し、痛烈に批判する

### Phase 3: 防衛フェーズ（開発AI）
1. テスト失敗を確認
2. コードを修正
3. テストが全てパスすることを確認
4. さらに堅牢なコードにリファクタリング

### Phase 4: 完了判定（テスターAI）
- もう壊す手段がない場合、降参する
- それ以外は Phase 2 に戻る

## 🔧 テスト実行コマンド

### すべてのテストを実行
```bash
pytest tests/ -v
```

### カバレッジ付きで実行
```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
```

### 特定のカテゴリのみ実行
```bash
# 意地悪なテストのみ
pytest tests/ -m adversarial -v

# 境界値テストのみ
pytest tests/ -m boundary -v

# 型攻撃テストのみ
pytest tests/ -m type_attack -v

# セキュリティテストのみ
pytest tests/ -m security -v
```

### 並列実行（高速化）
```bash
pytest tests/ -n auto
```

### タイムアウト設定（無限ループ対策）
```bash
pytest tests/ --timeout=30
```

## 📝 テスト用パッケージのインストール

```bash
# テスト用パッケージを含めてインストール
pip install -r requirements.txt
```

主なテストパッケージ：
- `pytest`: テストフレームワーク
- `pytest-cov`: カバレッジ測定
- `pytest-mock`: モック機能
- `pytest-timeout`: タイムアウト設定
- `pytest-xdist`: 並列実行

## 🎯 開発時の注意事項

### 開発AIへ
- 「動くコード」ではなく「壊れないコード」を書いてください
- テスターAIは容赦しません
- 防衛的プログラミングを徹底してください

### テスターAIへ
- 単純なtypoや文法エラーは報告不要です
- **深刻なバグ、セキュリティホール、論理エラー**を見つけてください
- 開発者を成長させる建設的な批判を心がけてください

## 📖 ドキュメント

すべてのドキュメントは`docs/`ディレクトリに機能別に整理されています。

### クイックリンク
- [📚 ドキュメントトップ](docs/README.md) - ドキュメント一覧と参照ガイド
- [📥 インストールガイド](docs/getting-started/INSTALLATION.md) - 詳細なセットアップ手順
- [🚀 デプロイガイド](docs/deployment/DEPLOYMENT.md) - 本番環境への展開
- [💻 開発ガイド](docs/development/CONTRIBUTING.md) - 開発への参加方法
- [🧪 テストガイド](docs/development/TESTING_GUIDE.md) - テストの実行方法
- [🏛️ プロジェクト構造](docs/architecture/PROJECT_STRUCTURE.md) - システム構造
- [📦 納品ドキュメント](docs/delivery/DELIVERY_README.md) - 納品パッケージ概要

## 🤝 コントリビューション

プロジェクトへの貢献を歓迎します！詳細は[docs/development/CONTRIBUTING.md](docs/development/CONTRIBUTING.md)を参照してください。

## 📄 ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下で公開されています。

