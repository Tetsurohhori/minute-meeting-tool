# コントリビューションガイド

このプロジェクトへの貢献に興味を持っていただき、ありがとうございます！

このドキュメントでは、開発に参加するためのガイドラインを説明します。

## 🎯 開発哲学

このプロジェクトは「**開発AI**」と「**テスターAI**」の二重チェックシステムを採用しています。

### 開発AI（開発者）の役割
- 堅牢で保守性の高いコードを実装
- SOLID原則に従った設計
- 型安全性の確保
- 適切なエラーハンドリング
- 包括的なドキュメント作成

### テスターAI（QA）の役割
- 意地悪なテストケースの作成
- 境界値・異常系の徹底的なテスト
- セキュリティ脆弱性の発見
- エッジケースの洗い出し

詳細は`.cursorrules`ファイルを参照してください。

---

## 🚀 開発環境のセットアップ

### 1. リポジトリのフォーク

```bash
# リポジトリをフォーク後、クローン
git clone https://github.com/your-username/議事メモツール.git
cd 議事メモツール
```

### 2. 仮想環境の作成

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 環境設定

```bash
cp .env.example .env
# .envファイルを編集して必要な情報を設定
```

### 4. テストの実行

```bash
# すべてのテストを実行
pytest tests/ -v

# カバレッジ付きで実行
pytest tests/ --cov=app --cov-report=html
```

---

## 📝 開発ワークフロー

### 1. ブランチの作成

```bash
# メインブランチから最新を取得
git checkout main
git pull origin main

# 機能ブランチを作成
git checkout -b feature/your-feature-name
# または
git checkout -b bugfix/your-bugfix-name
```

ブランチ命名規則:
- `feature/機能名` - 新機能の追加
- `bugfix/バグ名` - バグ修正
- `refactor/対象` - リファクタリング
- `docs/対象` - ドキュメントのみの変更
- `test/対象` - テストのみの変更

### 2. コードの実装

#### コーディング規約

**型ヒント**
```python
# ✅ Good
def process_documents(documents: List[Document]) -> Dict[str, Any]:
    """ドキュメントを処理する"""
    pass

# ❌ Bad
def process_documents(documents):
    pass
```

**エラーハンドリング**
```python
# ✅ Good
def load_config(path: str) -> Config:
    """設定ファイルを読み込む"""
    if not path:
        raise ValueError("パスが指定されていません")
    
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise ConfigError(f"設定ファイルが見つかりません: {path}")
    except json.JSONDecodeError as e:
        raise ConfigError(f"JSONパースエラー: {e}")

# ❌ Bad
def load_config(path):
    with open(path, 'r') as f:
        return json.load(f)
```

**依存性の注入**
```python
# ✅ Good
class VectorStoreManager:
    def __init__(self, client: ChromaClient, embedder: Embedder):
        self.client = client
        self.embedder = embedder

# ❌ Bad
class VectorStoreManager:
    def __init__(self):
        self.client = ChromaClient()
        self.embedder = OpenAIEmbedder()
```

**ドキュメント**
```python
# ✅ Good
def calculate_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    2つのベクトルのコサイン類似度を計算する
    
    Args:
        vec1: 1つ目のベクトル
        vec2: 2つ目のベクトル
    
    Returns:
        コサイン類似度（-1.0～1.0）
    
    Raises:
        ValueError: ベクトルの次元が一致しない場合
    """
    if vec1.shape != vec2.shape:
        raise ValueError("ベクトルの次元が一致しません")
    
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
```

### 3. テストの作成

**すべての新機能にはテストが必要です。**

#### テストの種類

**正常系テスト**
```python
def test_calculate_similarity_normal():
    """正常なベクトルで類似度計算が成功する"""
    vec1 = np.array([1, 0, 0])
    vec2 = np.array([1, 0, 0])
    
    result = calculate_similarity(vec1, vec2)
    
    assert result == 1.0
```

**異常系テスト（意地悪テスト）**
```python
@pytest.mark.adversarial
def test_calculate_similarity_dimension_mismatch():
    """次元が一致しないベクトルでエラーが発生する"""
    vec1 = np.array([1, 0, 0])
    vec2 = np.array([1, 0])
    
    with pytest.raises(ValueError, match="次元が一致しません"):
        calculate_similarity(vec1, vec2)

@pytest.mark.boundary
def test_calculate_similarity_zero_vectors():
    """ゼロベクトルで適切に処理される"""
    vec1 = np.array([0, 0, 0])
    vec2 = np.array([1, 0, 0])
    
    result = calculate_similarity(vec1, vec2)
    
    assert np.isnan(result) or result == 0.0
```

#### テストマーカー
- `@pytest.mark.adversarial` - 意地悪なテスト
- `@pytest.mark.boundary` - 境界値テスト
- `@pytest.mark.type_attack` - 型攻撃テスト
- `@pytest.mark.security` - セキュリティテスト

### 4. テストの実行

```bash
# 変更に関連するテストのみ実行
pytest tests/test_vector_store/ -v

# 意地悪なテストのみ実行
pytest tests/ -m adversarial -v

# カバレッジを確認
pytest tests/ --cov=app --cov-report=term-missing
```

### 5. コミット

```bash
# 変更をステージング
git add .

# コミット（わかりやすいメッセージで）
git commit -m "feat: ベクターストアの差分更新機能を追加"
```

#### コミットメッセージ規約

```
<type>: <subject>

<body>
```

**Type**:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメントのみの変更
- `style`: コードの意味に影響しない変更（空白、フォーマット等）
- `refactor`: リファクタリング
- `test`: テストの追加・修正
- `chore`: ビルドプロセスやツールの変更

**例**:
```bash
git commit -m "feat: SharePointデータソースを追加

- SharePointクライアントの実装
- 認証フローの追加
- エラーハンドリングの強化
- テストケースの追加"
```

### 6. プルリクエスト

```bash
# ブランチをプッシュ
git push origin feature/your-feature-name
```

GitHubでプルリクエストを作成:

1. プルリクエストのタイトルをわかりやすく記述
2. 変更内容の説明を記述
3. 関連するIssueがあればリンク
4. レビュワーをアサイン

#### プルリクエストテンプレート

```markdown
## 概要
<!-- 変更内容の概要を記述 -->

## 変更内容
- [ ] 新機能の追加
- [ ] バグ修正
- [ ] リファクタリング
- [ ] ドキュメント更新
- [ ] テスト追加

## 変更の詳細
<!-- 具体的な変更内容を記述 -->

## テスト
- [ ] 新しいテストを追加しました
- [ ] すべてのテストがパスしました
- [ ] カバレッジを確認しました

## チェックリスト
- [ ] 型ヒントを追加しました
- [ ] エラーハンドリングを実装しました
- [ ] ドキュメントを更新しました
- [ ] テストを追加しました
- [ ] `.cursorrules`に従っています

## 関連Issue
Closes #<issue-number>
```

---

## 🧪 テストガイドライン

### テストの基本原則

1. **AAA パターン**を使用
   - **Arrange**: テストの準備
   - **Act**: テスト対象の実行
   - **Assert**: 結果の検証

2. **FIRST 原則**
   - **Fast**: 高速に実行
   - **Independent**: 独立している
   - **Repeatable**: 再現可能
   - **Self-Validating**: 自己検証可能
   - **Timely**: タイムリーに作成

3. **意地悪なテスト**を作成
   - 境界値をテスト
   - 異常系をテスト
   - セキュリティをテスト

詳細は[TESTING_GUIDE.md](TESTING_GUIDE.md)を参照してください。

---

## 📚 ドキュメントガイドライン

### ドキュメントの種類

1. **コードコメント**: 複雑なロジックの説明
2. **Docstring**: 関数・クラスの説明
3. **README**: プロジェクト概要
4. **技術ドキュメント**: 詳細な説明

### Docstringの形式

Google形式を使用:

```python
def function_name(arg1: str, arg2: int = 0) -> bool:
    """
    関数の簡単な説明（1行）
    
    より詳細な説明が必要な場合はここに記述します。
    複数行にわたって記述することもできます。
    
    Args:
        arg1: 引数1の説明
        arg2: 引数2の説明（デフォルト: 0）
    
    Returns:
        戻り値の説明
    
    Raises:
        ValueError: 発生する例外の説明
        TypeError: 発生する例外の説明
    
    Examples:
        >>> function_name("test", 10)
        True
    """
    pass
```

---

## 🐛 バグ報告

バグを発見した場合は、GitHubのIssueで報告してください。

### バグ報告テンプレート

```markdown
## バグの説明
<!-- バグの内容を簡潔に記述 -->

## 再現手順
1. 
2. 
3. 

## 期待される動作
<!-- 本来どうあるべきか -->

## 実際の動作
<!-- 実際に何が起きたか -->

## 環境情報
- OS: 
- Python バージョン: 
- 依存パッケージのバージョン:

## ログ・エラーメッセージ
```
<!-- エラーメッセージやログを貼り付け -->
```

## 追加情報
<!-- スクリーンショットなど -->
```

---

## 💡 機能リクエスト

新機能のアイデアがある場合は、GitHubのIssueで提案してください。

### 機能リクエストテンプレート

```markdown
## 機能の概要
<!-- 提案する機能の概要 -->

## 動機
<!-- なぜこの機能が必要か -->

## 提案する実装
<!-- どのように実装すべきか（任意） -->

## 代替案
<!-- 他に考えられる方法（任意） -->

## 追加情報
<!-- 参考資料など -->
```

---

## 🎉 貢献者への感謝

このプロジェクトは、多くの貢献者の努力によって成り立っています。

貢献してくださった皆様、ありがとうございます！

---

## 📞 お問い合わせ

質問や提案がある場合は、GitHubのIssueまたはDiscussionsでお気軽にお問い合わせください。

---

**Happy Coding! 🚀**

