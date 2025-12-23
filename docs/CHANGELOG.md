# 変更履歴

このプロジェクトの主要な変更はすべてこのファイルに記録されます。

フォーマットは[Keep a Changelog](https://keepachangelog.com/ja/1.0.0/)に基づいており、
このプロジェクトは[セマンティックバージョニング](https://semver.org/lang/ja/)に準拠しています。

## [Unreleased]

### 計画中
- ユーザー認証機能
- 複数ユーザーのチャット履歴管理
- 議事メモのタグ付け機能
- より高度なRAG戦略（HyDE、Self-RAG等）

---

## [1.0.0] - 2025-01-XX

### 🎉 初回リリース

#### ✨ 新機能
- **RAGチャットボット**: OpenAI APIを使用した質問応答システム
- **データソース抽象化**: Google DriveとSharePointの両対応
- **ベクターストア管理**: ChromaDBを使用したベクトル検索
- **差分更新**: 変更のあったファイルのみを更新する効率的な仕組み
- **Streamlit UI**: 使いやすいWebインターフェース
- **日次自動更新**: cron/systemd timerによる自動更新

#### 🏗️ アーキテクチャ
- **Strategy Pattern**: データソースの切り替え可能な設計
- **依存性の注入**: テスタビリティの高い設計
- **型安全性**: 全ての関数に型ヒントを適用
- **エラーハンドリング**: 包括的な例外処理
- **ロギング**: 構造化されたログ出力

#### 🧪 テスト
- **75個のテストケース**を実装
  - 境界値攻撃テスト: 25個
  - 型攻撃テスト: 20個
  - セキュリティテスト: 10個
  - リソース攻撃テスト: 8個
  - 統合テスト: 12個
- **開発AI vs テスターAI**: 二重チェックシステムによる品質保証
- **pytest-cov**: カバレッジ測定
- **pytest-timeout**: 無限ループ対策

#### 📚 ドキュメント
- README.md: プロジェクト概要
- INSTALLATION.md: 詳細インストールガイド
- DEPLOYMENT.md: デプロイ・運用ガイド
- TESTING_GUIDE.md: テスト実行ガイド
- PROJECT_STRUCTURE.md: プロジェクト構造
- CONTRIBUTING.md: コントリビューションガイド
- .cursorrules: AI開発環境ルール

#### 🔧 設定管理
- `.env.example`: 環境変数テンプレート
- `credentials.json.example`: Google認証情報テンプレート
- `.gitignore`: Git除外設定
- `pytest.ini`: pytest設定

#### 📦 依存パッケージ
- openai>=1.0.0
- chromadb>=0.4.0
- langchain>=0.1.0
- streamlit>=1.28.0
- google-api-python-client>=2.0.0
- Office365-REST-Python-Client>=2.5.0
- pytest>=7.4.0（テスト用）

---

## バージョニング規則

- **MAJOR**: 互換性のない大きな変更
- **MINOR**: 後方互換性のある機能追加
- **PATCH**: 後方互換性のあるバグ修正

---

## 変更タイプの定義

- **✨ Added**: 新機能
- **🔧 Changed**: 既存機能の変更
- **🗑️ Deprecated**: 非推奨となった機能
- **🔥 Removed**: 削除された機能
- **🐛 Fixed**: バグ修正
- **🔒 Security**: セキュリティ関連の修正

---

[Unreleased]: https://github.com/your-org/your-repo/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/your-org/your-repo/releases/tag/v1.0.0

