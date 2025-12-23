# 🔥 テスト実行ガイド - 開発AI vs テスターAI

このガイドでは、開発AIとテスターAIの役割分担と、テスト実行方法を説明します。

---

## 📋 役割分担

### 🛠️ 開発AI（あなたがコードを書く時）

**目的**: 堅牢で保守性の高いコードを実装する

**心構え**:
- テスターAIに壊されないコードを書く
- 防衛的プログラミングを徹底する
- 型安全性とエラーハンドリングを重視する

**プロンプト例**:
```
[開発AIモード]
app/config/settings.py の Settings クラスに、
以下の機能を追加してください：

- チャンクサイズとオーバーラップの論理的整合性チェック
- 環境変数の厳格なバリデーション
- 負数やゼロの拒否

SOLID原則に従い、依存性の注入を使用し、
すべてのエッジケースに対応してください。
```

### 🔥 テスターAI（あなたがテストを書く時）

**目的**: 開発者のコードを徹底的に壊す

**心構え**:
- 正常系のテストは書かない
- 異常系、境界値、型攻撃に専念する
- 開発者の盲点を突く

**プロンプト例**:
```
[テスターAIモード]
app/config/settings.py の Settings クラスに対して、
tests/test_config/ に意地悪なテストを作成してください。

攻撃観点：
- 環境変数に None, 空文字列, スペースのみ
- CHUNK_OVERLAP > CHUNK_SIZE の矛盾
- 極端に大きい/小さい値
- 型の不一致
- パストラバーサル攻撃

発見したバグを痛烈に批判し、修正案を提示してください。
```

---

## 🚀 テスト実行フロー

### ステップ 1: テスト環境のセットアップ

```bash
# プロジェクトルートに移動
cd /Users/tetsuroh/Documents/議事メモツール

# 仮想環境を有効化（既に作成済みの場合）
source venv/bin/activate

# テスト用パッケージのインストール（初回のみ）
pip install -r requirements.txt
```

### ステップ 2: テスト実行

#### 基本的なテスト実行
```bash
# すべてのテストを実行
pytest tests/ -v

# 特定のファイルのみ実行
pytest tests/test_config/test_settings_adversarial.py -v

# 特定のテストクラスのみ実行
pytest tests/test_config/test_settings_adversarial.py::TestSettingsInitializationAttacks -v

# 特定のテストメソッドのみ実行
pytest tests/test_config/test_settings_adversarial.py::TestSettingsInitializationAttacks::test_missing_openai_api_key_should_raise_error -v
```

#### マーカーを使ったフィルタリング
```bash
# 意地悪なテストのみ実行
pytest tests/ -m adversarial -v

# 境界値テストのみ
pytest tests/ -m boundary -v

# 型攻撃テストのみ
pytest tests/ -m type_attack -v

# セキュリティテストのみ
pytest tests/ -m security -v

# リソース攻撃テストのみ
pytest tests/ -m resource_attack -v

# 統合テストのみ
pytest tests/ -m integration -v
```

#### カバレッジ測定
```bash
# カバレッジを測定しながらテスト実行
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# カバレッジレポートの確認（ブラウザで開く）
open htmlcov/index.html
```

#### 高度な実行オプション
```bash
# 並列実行（高速化）
pytest tests/ -n auto

# 失敗したテストのみ再実行
pytest tests/ --lf

# 失敗したテストを優先的に実行
pytest tests/ --ff

# 詳細な出力（標準出力を表示）
pytest tests/ -v -s

# タイムアウト設定（無限ループ対策）
pytest tests/ --timeout=30

# 最初の失敗で停止
pytest tests/ -x

# 失敗したテストを3回まで再試行
pytest tests/ --reruns 3
```

---

## 🔄 開発・テストサイクル

### サイクル 1: 初期実装

1. **開発AI**: 機能を実装
   ```bash
   # 開発中...
   # app/config/settings.py を編集
   ```

2. **テスターAI**: テストを作成して実行
   ```bash
   pytest tests/test_config/ -v
   ```

3. **結果確認**: どれだけ失敗したか？
   ```bash
   # 例: 15 failed, 3 passed
   ```

### サイクル 2: 修正

4. **開発AI**: 失敗したテストを修正
   ```bash
   # テスト結果を見て、コードを修正
   ```

5. **再実行**: 失敗したテストのみ実行
   ```bash
   pytest tests/ --lf -v
   ```

6. **すべてパス**: 全テストを実行
   ```bash
   pytest tests/ -v
   ```

### サイクル 3: さらなる攻撃

7. **テスターAI**: 新しい攻撃を追加
   ```bash
   # さらに意地悪なテストを追加
   ```

8. **繰り返し**: テスターAIが降参するまで続ける

---

## 📊 テスト結果の見方

### 成功（PASSED）
```
tests/test_config/test_settings_adversarial.py::TestSettingsInitializationAttacks::test_missing_openai_api_key_should_raise_error PASSED
```
✅ テストが期待通りに動作した

### 失敗（FAILED）
```
tests/test_config/test_settings_adversarial.py::TestSettingsInitializationAttacks::test_whitespace_only_api_key_should_raise_error FAILED

AssertionError: スペースだけのAPIキーが通ってしまっている！validation が甘い！
```
❌ バグ発見！開発者は修正が必要

### エラー（ERROR）
```
ERROR at setup of test_something
TypeError: __init__() missing 1 required positional argument: 'metadata_path'
```
❌ テストのセットアップに問題がある

### スキップ（SKIPPED）
```
tests/test_integration.py::test_slow_integration SKIPPED
```
⏭️ 意図的にスキップされた（例: @pytest.mark.skip）

---

## 🎯 典型的なバグパターンとテスト方法

### パターン 1: 型安全性の欠如

**バグ**: 文字列を期待している場所に数値を渡しても通る

**テスト**:
```python
@pytest.mark.adversarial
@pytest.mark.type_attack
def test_file_id_with_integer(self):
    with pytest.raises(TypeError):
        DocumentInfo(file_id=12345, ...)  # 数値を渡す
```

### パターン 2: 境界値の未チェック

**バグ**: 負数やゼロを受け入れてしまう

**テスト**:
```python
@pytest.mark.adversarial
@pytest.mark.boundary
def test_chunk_size_negative(self):
    settings = Settings(chunk_size=-100)
    assert settings.chunk_size > 0, "負数が通った！"
```

### パターン 3: エラーハンドリングの甘さ

**バグ**: 例外を print() で流すだけ

**テスト**:
```python
@pytest.mark.adversarial
def test_error_is_logged(self, caplog):
    # エラーが発生する操作
    detector.load_metadata()
    
    # ログに記録されているか確認
    assert "エラー" in caplog.text, "エラーがロギングされていない！"
```

### パターン 4: セキュリティホール

**バグ**: パストラバーサル攻撃への対策が無い

**テスト**:
```python
@pytest.mark.adversarial
@pytest.mark.security
def test_path_traversal_attack(self):
    malicious_path = "../../etc/passwd"
    with pytest.raises(ValueError):
        Settings(log_path=malicious_path)
```

### パターン 5: リソース管理の欠如

**バグ**: 大量のデータでメモリを使い切る

**テスト**:
```python
@pytest.mark.adversarial
@pytest.mark.resource_attack
def test_memory_exhaustion(self):
    huge_data = "A" * (100 * 1024 * 1024)  # 100MB
    # メモリ制限を超えるべき
    with pytest.raises(MemoryError):
        process_data(huge_data)
```

---

## 🛡️ 修正のベストプラクティス

### 1. 入力検証を追加
```python
# Before
def __init__(self, file_id: str):
    self.file_id = file_id

# After
def __init__(self, file_id: str):
    if not isinstance(file_id, str):
        raise TypeError("file_id must be a string")
    if not file_id.strip():
        raise ValueError("file_id cannot be empty")
    self.file_id = file_id
```

### 2. エラーハンドリングを改善
```python
# Before
try:
    data = json.load(f)
except Exception as e:
    print(f"エラー: {e}")
    return {}

# After
import logging
logger = logging.getLogger(__name__)

try:
    data = json.load(f)
except json.JSONDecodeError as e:
    logger.error(f"JSON解析エラー: {e}", exc_info=True)
    raise
except Exception as e:
    logger.error(f"予期しないエラー: {e}", exc_info=True)
    raise
```

### 3. セキュリティチェックを追加
```python
# Before
self.log_path = Path(os.getenv("LOG_PATH", "./logs"))

# After
log_path_str = os.getenv("LOG_PATH", "./logs")
self.log_path = Path(log_path_str).resolve()  # 絶対パスに正規化

# パストラバーサルのチェック
if ".." in str(self.log_path):
    raise ValueError("Path traversal detected")
```

### 4. リソース制限を追加
```python
# Before
def process_content(self, content: str):
    return content.upper()

# After
MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10MB

def process_content(self, content: str):
    if len(content) > MAX_CONTENT_SIZE:
        raise ValueError(f"Content size exceeds {MAX_CONTENT_SIZE} bytes")
    return content.upper()
```

---

## 📈 カバレッジ目標

### ⚠️ 重要な注意
カバレッジ100%を目指さないでください！

**理由**:
- カバレッジが高くてもバグは存在する
- **バグ発見数**を重視する
- 異常系のテストを優先する

**目安**:
- カバレッジ: 70-80% で十分
- 重要なのは「どれだけバグを見つけたか」

---

## 🏆 成功の定義

### テスターAIの勝利条件
- 10個以上の深刻なバグを発見した
- セキュリティホールを見つけた
- 開発者が「想定外」と言うバグを見つけた

### 開発AIの勝利条件
- すべての意地悪なテストがパスした
- テスターAIが「もう壊せない」と降参した
- コードレビューで高評価を得た

---

## 🔧 トラブルシューティング

### テストが実行できない
```bash
# pytest がインストールされているか確認
pip list | grep pytest

# パスを確認
echo $PYTHONPATH

# 仮想環境を確認
which python
```

### テストが見つからない
```bash
# テストファイルの命名規則を確認（test_*.py）
ls tests/

# pytest のテスト発見ルールを確認
pytest --collect-only
```

### モジュールがインポートできない
```bash
# プロジェクトルートから実行しているか確認
pwd

# PYTHONPATH にプロジェクトルートを追加
export PYTHONPATH=/Users/tetsuroh/Documents/議事メモツール:$PYTHONPATH
```

---

## 📚 参考資料

- [pytest 公式ドキュメント](https://docs.pytest.org/)
- [Python Testing Best Practices](https://realpython.com/pytest-python-testing/)
- [Defensive Programming](https://en.wikipedia.org/wiki/Defensive_programming)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

---

開発AI、テスターAIの両方を使いこなし、
堅牢で保守性の高いシステムを構築してください！

**戦いは今始まったばかりだ！** 🔥

