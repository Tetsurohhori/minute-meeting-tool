# プロジェクト構造ドキュメント

## 📁 プロジェクトの全体像

このドキュメントは、議事メモRAGチャットボットのファイル構造と、各コンポーネントの役割を説明します。

## 📂 ディレクトリ構造

```
議事メモツール/
├── 📄 設定・管理ファイル
│   ├── .cursorrules           # AI開発環境ルール（開発AI・テスターAI）
│   ├── .gitignore            # Git除外設定
│   ├── .env.example          # 環境変数テンプレート
│   ├── pytest.ini            # pytest設定
│   ├── requirements.txt      # Python依存パッケージ
│   └── credentials.json.example  # Google認証情報テンプレート
│
├── 📚 ドキュメント
│   ├── README.md             # プロジェクト概要とクイックスタート
│   ├── INSTALLATION.md       # 詳細インストールガイド
│   ├── DEPLOYMENT.md         # デプロイ・運用ガイド
│   ├── TESTING_GUIDE.md      # テストガイド
│   └── PROJECT_STRUCTURE.md  # このファイル
│
├── 🎯 アプリケーションコード (app/)
│   ├── main.py               # Streamlit Webアプリケーション
│   ├── config/               # 設定管理
│   ├── data_sources/         # データソース抽象化層
│   ├── vector_store/         # ベクターDB管理
│   ├── rag/                  # RAGエンジン
│   └── utils/                # ユーティリティ
│
├── 🧪 テストコード (tests/)
│   ├── conftest.py           # pytest共通設定
│   ├── test_config/          # 設定モジュールのテスト
│   ├── test_data_sources/    # データソースのテスト
│   ├── test_utils/           # ユーティリティのテスト
│   └── test_adversarial/     # 統合攻撃テスト
│
├── 🔧 運用スクリプト (scripts/)
│   └── update_vector_store.py  # ベクターストア更新
│
└── 📦 アーカイブ (Archive/)
    ├── ARCHITECTURE.md       # アーキテクチャドキュメント
    ├── SETUP_GUIDE.md        # 詳細セットアップガイド
    └── 議事メモツール_PoC用/  # テストデータ

実行時に自動生成されるディレクトリ:
├── data/                     # ベクターストアとメタデータ
├── logs/                     # アプリケーションログ
└── venv/                     # Python仮想環境
```

---

## 🎯 AI開発体制の構成ファイル

### .cursorrules
開発AI・テスターAIの役割定義と実行ルール

### pytest.ini
テスト実行の設定（マーカー、タイムアウト等）

### tests/conftest.py
共通フィクスチャとモック定義

### 🔥 意地悪なテスト実装（75個のテスト）

#### 1. 設定モジュールのテスト
```
tests/test_config/
├── __init__.py
└── test_settings_adversarial.py    # 18テスト
    ├── TestSettingsInitializationAttacks (10テスト)
    ├── TestSettingsValidationAttacks (4テスト)
    ├── TestSettingsSingletonAttacks (2テスト)
    └── TestSettingsResourceAttacks (2テスト)
```

**攻撃観点**:
- 環境変数の欠如、空文字列、スペースのみ
- 負数やゼロの値
- チャンクサイズとオーバーラップの論理矛盾
- パストラバーサル攻撃
- シングルトンの状態汚染
- 極端に大きな値でメモリ/コスト爆発

#### 2. データソースのテスト
```
tests/test_data_sources/
├── __init__.py
└── test_base_adversarial.py        # 13テスト
    ├── TestDocumentInfoAttacks (7テスト)
    ├── TestDataSourceBaseAttacks (4テスト)
    └── TestDocumentInfoHashingAttacks (2テスト)
```

**攻撃観点**:
- None、間違った型のデータ
- 空文字列だけのドキュメント
- 100MBの巨大コンテンツ
- SQLインジェクション、XSS、パストラバーサル
- 抽象クラスの不正な実装
- ハッシュ整合性の欠如

#### 3. ユーティリティのテスト
```
tests/test_utils/
├── __init__.py
└── test_diff_detector_adversarial.py   # 26テスト
    ├── TestDiffDetectorInitializationAttacks (6テスト)
    ├── TestCalculateHashAttacks (4テスト)
    ├── TestDetectChangesAttacks (6テスト)
    ├── TestUpdateMetadataAttacks (6テスト)
    ├── TestSaveMetadataAttacks (2テスト)
    └── TestRemoveMetadataAttacks (2テスト)
```

**攻撃観点**:
- Noneパス、パストラバーサル
- 壊れたJSON、空ファイル
- 100MBデータのハッシュ計算
- 10万ファイルの大量処理
- メタデータの上書きとデータ損失
- 極端に深いネスト構造
- シリアライズ不可能なデータ

#### 4. 統合テスト
```
tests/test_adversarial/
├── __init__.py
└── test_integration_attacks.py     # 18テスト
    ├── TestSystemIntegrationAttacks (5テスト)
    ├── TestConfigurationCombinationAttacks (6テスト)
    ├── TestBoundaryValueCombinations (5テスト)
    └── TestErrorPropagation (2テスト)
```

**攻撃観点**:
- 壊れたデータの全ワークフロー
- 10万ファイルでメモリ枯渇
- SQL+XSS+パストラバーサル複合攻撃
- 競合状態（Race Condition）
- 循環参照
- 設定の論理矛盾の組み合わせ
- 極端な境界値（Null文字、絵文字等）
- エラーの静かな飲み込み

### 📚 ドキュメント
```
TESTING_GUIDE.md               # テスト実行ガイド（詳細な使い方）
PROJECT_STRUCTURE.md           # このファイル
README.md                      # 更新済み（新しい体制を説明）
```

### 📦 依存関係
```
requirements.txt               # 更新済み（テスト用パッケージ追加）
    - pytest>=7.4.0
    - pytest-cov>=4.1.0
    - pytest-mock>=3.12.0
    - pytest-timeout>=2.2.0
    - pytest-xdist>=3.5.0
```

---

## 🎯 テストの統計

- **総テスト数**: 75個
- **テストクラス数**: 16個
- **テストファイル数**: 4個

### カテゴリ別
- 境界値攻撃: 25個
- 型攻撃: 20個
- セキュリティ攻撃: 10個
- リソース攻撃: 8個
- 統合テスト: 12個

---

## 🚀 クイックスタート

### 1. テスト用パッケージのインストール
```bash
cd /Users/tetsuroh/Documents/議事メモツール
source venv/bin/activate
pip install -r requirements.txt
```

### 2. すべてのテストを実行
```bash
pytest tests/ -v
```

### 3. 意地悪なテストのみ実行
```bash
pytest tests/ -m adversarial -v
```

### 4. カバレッジ測定
```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

---

## 📊 期待される結果

### 現状のコードでテストを実行すると...

**予想**: 多くのテストが失敗する 🔥

**理由**:
- 入力検証が不十分
- エラーハンドリングが甘い
- 型安全性が欠如
- セキュリティチェックが無い
- リソース管理が未実装

### これは**正常**です！

テスターAIの目的は、コードの弱点を暴くことです。
失敗したテストは「修正すべき箇所」を示しています。

---

## 🔄 推奨ワークフロー

1. **現状確認**: テストを実行して、何が失敗するか確認
   ```bash
   pytest tests/ -v
   ```

2. **優先順位付け**: セキュリティ > データ整合性 > 型安全性

3. **修正**: 開発AIモードで失敗したテストを修正

4. **再テスト**: 修正後のテストを実行
   ```bash
   pytest tests/ --lf -v  # 失敗したテストのみ再実行
   ```

5. **追加攻撃**: テスターAIモードで新しいテストを追加

6. **繰り返し**: すべてのテストがパスするまで

---

## 💡 重要な注意事項

### 開発者へ
- このテストは「意地悪」です
- 現実的な脆弱性を指摘しています
- 失敗は恥ではなく、改善の機会です
- 「動く」ことと「堅牢」は別物です

### テスターへ
- 建設的な批判を心がけてください
- 修正案を提示してください
- 単なる文法エラーやtypoは報告不要です
- **深刻なバグ**を見つけることが目標です

---

## 📈 次のステップ

1. ✅ 基本的なテスト環境の構築（完了）
2. ⏳ 既存コードのテスト実行とバグ発見
3. ⏳ 発見したバグの修正
4. ⏳ 追加のテストケース作成
5. ⏳ カバレッジ向上（目標: 70-80%）
6. ⏳ CI/CD パイプラインへの統合

---

**開発AI vs テスターAI の戦いが今始まる！** 🔥

堅牢で保守性の高いシステムを目指して、頑張ってください！

