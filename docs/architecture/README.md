# アーキテクチャドキュメント

システムの構造と設計に関する情報をまとめています。

## 📄 ドキュメント

### [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
**プロジェクト構造**

このドキュメントでは、プロジェクトのファイル構造と各コンポーネントの役割を説明しています。

#### 内容
- プロジェクトの全体像
- ディレクトリ構造
  - アプリケーションコード (`app/`)
  - テストコード (`tests/`)
  - 運用スクリプト (`scripts/`)
  - ドキュメント (`docs/`)
  - アーカイブ (`Archive/`)
- AI開発体制の構成ファイル
- 各コンポーネントの詳細説明
- テスト構成（75個のテストケース）

#### 対象者
- プロジェクトの構造を理解したい方
- 新しいコンポーネントを追加したい開発者
- コードレビュアー

---

## 🏗️ システムアーキテクチャ

```
議事メモツール/
├── app/                    # アプリケーションコード
│   ├── main.py            # Streamlit Webアプリ
│   ├── config/            # 設定管理
│   ├── data_sources/      # データソース抽象化
│   ├── vector_store/      # ベクターDB管理
│   ├── rag/               # RAGエンジン
│   └── utils/             # ユーティリティ
│
├── tests/                  # テストコード（75個）
│   ├── test_config/
│   ├── test_data_sources/
│   ├── test_utils/
│   └── test_adversarial/
│
├── scripts/                # 運用スクリプト
├── docs/                   # ドキュメント
└── Archive/                # 参考資料
```

---

## 🎯 設計原則

### SOLID原則
- **Single Responsibility**: 各クラスは単一の責任
- **Open/Closed**: 拡張に開いて、修正に閉じている
- **Liskov Substitution**: 派生型は基底型と置き換え可能
- **Interface Segregation**: インターフェースの分離
- **Dependency Inversion**: 依存性の注入

### Strategy Pattern
データソース（Google Drive / SharePoint）の切り替えを可能にする設計

### 依存性の注入（DI）
テスタビリティを高めるための設計

詳細は [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) を参照してください。

---

## 📊 コンポーネント図

```
┌─────────────────┐
│  Streamlit UI   │
└────────┬────────┘
         │
    ┌────▼─────┐
    │ RAG Core │
    └────┬─────┘
         │
    ┌────▼──────────┐
    │ Vector Store  │
    └────┬──────────┘
         │
    ┌────▼────────────┐
    │ Data Sources    │
    │ (Google/SharePt)│
    └─────────────────┘
```

---

## 📚 関連ドキュメント

- [../CHANGELOG.md](../CHANGELOG.md) - 変更履歴
- [development/CONTRIBUTING.md](../development/CONTRIBUTING.md) - 開発ガイド

---

[← ドキュメントトップに戻る](../README.md)

