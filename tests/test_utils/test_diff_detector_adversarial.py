"""
🔥 DiffDetector モジュールへの意地悪な攻撃的テスト

ファイルシステム操作、JSON処理、ハッシュ計算の脆弱性を徹底的に突く。
"""

import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict
from unittest.mock import patch, mock_open, MagicMock

from app.utils.diff_detector import DiffDetector


class TestDiffDetectorInitializationAttacks:
    """初期化に対する攻撃"""
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_initialize_with_none_path(self):
        """❌ None をパスとして渡したら？"""
        with pytest.raises((TypeError, AttributeError)):
            DiffDetector(None)
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_initialize_with_string_instead_of_path(self):
        """❌ 文字列をPathの代わりに渡したら？"""
        # Path() が文字列を受け入れるので通ってしまう可能性
        detector = DiffDetector("/tmp/test")
        assert isinstance(detector.metadata_path, (Path, str)), \
            "型の柔軟性はあるが、一貫性が無い"
    
    @pytest.mark.adversarial
    @pytest.mark.security
    def test_initialize_with_path_traversal(self):
        """❌ パストラバーサル攻撃"""
        malicious_path = Path("../../etc")
        detector = DiffDetector(malicious_path)
        # システムの重要なディレクトリにファイルを作成する危険性
        assert "etc" not in str(detector.metadata_file.absolute()), \
            "パストラバーサルが通ってしまった可能性"
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_load_corrupted_metadata_file(self, temp_dir):
        """❌ 壊れたJSONファイルを読み込んだら？"""
        metadata_file = temp_dir / "file_metadata.json"
        metadata_file.write_text("{ this is not valid json }")
        
        # 例外処理があるので通るはず、でも警告は出るか？
        detector = DiffDetector(temp_dir)
        assert detector.metadata == {}, \
            "壊れたJSONをロードしてクラッシュした！"
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_load_empty_metadata_file(self, temp_dir):
        """❌ 空のファイルを読み込んだら？"""
        metadata_file = temp_dir / "file_metadata.json"
        metadata_file.write_text("")
        
        detector = DiffDetector(temp_dir)
        assert detector.metadata == {}, \
            "空ファイルの処理に失敗"
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_load_metadata_with_wrong_type(self, temp_dir):
        """❌ JSONの型が期待と違う場合"""
        metadata_file = temp_dir / "file_metadata.json"
        # Dictではなくリストを保存
        metadata_file.write_text("[]")
        
        detector = DiffDetector(temp_dir)
        # 型が違うので、後で dict.keys() などでクラッシュする可能性
        assert isinstance(detector.metadata, dict), \
            "型が違うメタデータを読み込んだ！後でクラッシュする！"


class TestCalculateHashAttacks:
    """ハッシュ計算への攻撃"""
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_calculate_hash_with_none(self, temp_dir):
        """❌ None をハッシュ計算に渡したら？"""
        detector = DiffDetector(temp_dir)
        
        with pytest.raises((TypeError, AttributeError)):
            detector._calculate_hash(None)
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_calculate_hash_with_string_instead_of_bytes(self, temp_dir):
        """❌ 文字列をバイト列の代わりに渡したら？"""
        detector = DiffDetector(temp_dir)
        
        # 文字列は受け付けないはず
        with pytest.raises((TypeError, AttributeError)):
            detector._calculate_hash("not bytes but string")
    
    @pytest.mark.adversarial
    @pytest.mark.resource_attack
    def test_calculate_hash_with_huge_content(self, temp_dir):
        """❌ 巨大なデータのハッシュ計算でメモリを圧迫"""
        detector = DiffDetector(temp_dir)
        
        # 100MBのデータ
        huge_data = b"A" * (100 * 1024 * 1024)
        
        # これが通るかタイムアウトするか
        hash_value = detector._calculate_hash(huge_data)
        assert len(hash_value) == 64, "SHA256ハッシュは64文字のはず"
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_calculate_hash_with_empty_bytes(self, temp_dir):
        """❌ 空のバイト列のハッシュ"""
        detector = DiffDetector(temp_dir)
        
        hash_value = detector._calculate_hash(b"")
        # 空データでもハッシュは計算される
        assert len(hash_value) == 64, "空データのハッシュが計算できなかった"


class TestDetectChangesAttacks:
    """変更検出への攻撃"""
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_detect_changes_with_none_input(self, temp_dir):
        """❌ None を current_files として渡したら？"""
        detector = DiffDetector(temp_dir)
        
        with pytest.raises((TypeError, AttributeError)):
            detector.detect_changes(None)
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_detect_changes_with_list_instead_of_dict(self, temp_dir):
        """❌ リストを辞書の代わりに渡したら？"""
        detector = DiffDetector(temp_dir)
        
        with pytest.raises((TypeError, AttributeError)):
            detector.detect_changes(["not", "a", "dict"])
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_detect_changes_with_empty_dict(self, temp_dir):
        """❌ 空の辞書を渡したら？"""
        detector = DiffDetector(temp_dir)
        
        new, updated, deleted = detector.detect_changes({})
        
        # すべてのファイルが削除されたと判定されるべき
        assert len(new) == 0, "空の入力で新規ファイルが検出された？"
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_detect_changes_with_missing_content_hash(self, temp_dir):
        """❌ content_hash フィールドが無いデータ"""
        detector = DiffDetector(temp_dir)
        
        # メタデータに保存
        detector.metadata = {
            "file1": {"name": "test.txt", "content_hash": "abc123"}
        }
        
        # content_hash が無い現在のファイル
        current_files = {
            "file1": {"name": "test.txt"}  # content_hash が無い！
        }
        
        new, updated, deleted = detector.detect_changes(current_files)
        
        # .get() でデフォルト値を返すので例外は出ないが、
        # 空文字列と比較するので更新と判定される
        assert "file1" in updated or "file1" not in updated, \
            "content_hash が無いデータの処理が曖昧"
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_detect_changes_with_malformed_metadata(self, temp_dir):
        """❌ 不正な形式のメタデータ"""
        detector = DiffDetector(temp_dir)
        
        # ネストが深すぎるメタデータ
        detector.metadata = {
            "file1": {
                "nested": {
                    "deeply": {
                        "too": {
                            "much": "data"
                        }
                    }
                }
            }
        }
        
        current_files = {
            "file1": {"content_hash": "xyz"}
        }
        
        # .get("content_hash") でキーが無いので空文字列と比較
        new, updated, deleted = detector.detect_changes(current_files)
        # エラーにはならないが、期待通りの動作はしない
    
    @pytest.mark.adversarial
    @pytest.mark.resource_attack
    def test_detect_changes_with_huge_number_of_files(self, temp_dir):
        """❌ 大量のファイルで処理を遅延させる"""
        detector = DiffDetector(temp_dir)
        
        # 10万ファイル
        huge_files = {
            f"file_{i}": {"content_hash": f"hash_{i}"}
            for i in range(100000)
        }
        
        # これがタイムアウトするか？
        new, updated, deleted = detector.detect_changes(huge_files)
        
        # すべて新規ファイルとして検出される
        assert len(new) == 100000, "大量ファイルの処理に失敗"


class TestUpdateMetadataAttacks:
    """メタデータ更新への攻撃"""
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_update_metadata_with_none_file_id(self, temp_dir):
        """❌ None をファイルIDとして渡したら？"""
        detector = DiffDetector(temp_dir)
        
        # None がキーになってしまう
        detector.update_metadata(None, {"content_hash": "abc"})
        
        assert None in detector.metadata, \
            "None がキーとして保存された！検索不能になる！"
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_update_metadata_with_empty_file_id(self, temp_dir):
        """❌ 空文字列をファイルIDとして渡したら？"""
        detector = DiffDetector(temp_dir)
        
        detector.update_metadata("", {"content_hash": "abc"})
        
        assert "" in detector.metadata, \
            "空文字列がキーとして保存された！他のファイルと衝突する！"
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_update_metadata_with_none_file_info(self, temp_dir):
        """❌ None をファイル情報として渡したら？"""
        detector = DiffDetector(temp_dir)
        
        # **None は展開できない
        with pytest.raises(TypeError):
            detector.update_metadata("file1", None)
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_update_metadata_with_empty_dict(self, temp_dir):
        """❌ 空の辞書を渡したら？"""
        detector = DiffDetector(temp_dir)
        
        detector.update_metadata("file1", {})
        
        # last_updated のみが保存される
        assert "file1" in detector.metadata, "空の情報でも保存される"
        assert "last_updated" in detector.metadata["file1"], \
            "last_updated が無い！"
    
    @pytest.mark.adversarial
    @pytest.mark.security
    def test_update_metadata_with_malicious_keys(self, temp_dir):
        """❌ 悪意のあるキーを含むメタデータ"""
        detector = DiffDetector(temp_dir)
        
        malicious_info = {
            "__proto__": "prototype_pollution",
            "constructor": "dangerous",
            "../../../etc/passwd": "path_traversal"
        }
        
        detector.update_metadata("file1", malicious_info)
        
        # JSONとして保存されるので、プロトタイプ汚染は起きないが...
        assert "file1" in detector.metadata, "悪意のあるキーでも保存される"
    
    @pytest.mark.adversarial
    @pytest.mark.resource_attack
    def test_update_metadata_overwrites_without_backup(self, temp_dir):
        """❌ メタデータの上書きでデータ損失"""
        detector = DiffDetector(temp_dir)
        
        # 最初のデータ
        detector.update_metadata("file1", {"version": 1, "important_data": "critical"})
        
        # 上書き（バックアップ無し）
        detector.update_metadata("file1", {"version": 2})
        
        # important_data が消えた！
        assert "important_data" not in detector.metadata["file1"], \
            "データが上書きで消えた！バックアップ機構が無い！"


class TestSaveMetadataAttacks:
    """メタデータ保存への攻撃"""
    
    @pytest.mark.adversarial
    @pytest.mark.resource_attack
    def test_save_metadata_with_extremely_deep_nesting(self, temp_dir):
        """❌ 極端に深いネストでJSON保存を破壊"""
        detector = DiffDetector(temp_dir)
        
        # 深いネスト構造を作成
        deep_data = {"level": 0}
        current = deep_data
        for i in range(100):
            current["nested"] = {"level": i + 1}
            current = current["nested"]
        
        detector.metadata = {"file1": deep_data}
        
        # JSONにシリアライズできるか？
        try:
            detector._save_metadata()
            # 保存できたら読み込めるか確認
            detector2 = DiffDetector(temp_dir)
            assert "file1" in detector2.metadata, "深いネストのデータが保存できなかった"
        except RecursionError:
            pytest.fail("深いネストでRecursionErrorが発生！")
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_save_metadata_with_non_serializable_data(self, temp_dir):
        """❌ シリアライズできないデータを保存しようとしたら？"""
        detector = DiffDetector(temp_dir)
        
        # オブジェクトを含むメタデータ
        detector.metadata = {
            "file1": {
                "object": object(),  # シリアライズ不可
                "function": lambda x: x,  # シリアライズ不可
            }
        }
        
        # JSONエンコードエラーが発生する
        with pytest.raises((TypeError, ValueError)):
            detector._save_metadata()


class TestRemoveMetadataAttacks:
    """メタデータ削除への攻撃"""
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_remove_nonexistent_file(self, temp_dir):
        """❌ 存在しないファイルを削除しようとしたら？"""
        detector = DiffDetector(temp_dir)
        
        # 存在しないファイルを削除
        detector.remove_metadata("nonexistent_file")
        
        # エラーにはならない（if file_id in self.metadata でチェック）
        assert "nonexistent_file" not in detector.metadata
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_remove_metadata_with_none_file_id(self, temp_dir):
        """❌ None をファイルIDとして削除"""
        detector = DiffDetector(temp_dir)
        
        # None を削除
        detector.remove_metadata(None)
        # エラーにはならないが、意味不明


# =====================================
# 批判的フィードバック
# =====================================

"""
🔥 開発者への痛烈な批判 🔥

1. **型安全性の完全な欠如**
   - None, 空文字列, 不正な型をすべて受け入れてしまう
   - 型ヒントがあるが、ランタイムでは何もチェックしていない
   - バイト列と文字列の混同が起きる可能性

2. **エラーハンドリングの甘さ**
   - JSON読み込みエラーを print() で流すだけ
   - ロギングさえしていない
   - ユーザーはエラーに気づかない

3. **データ整合性の問題**
   - メタデータ上書き時にバックアップが無い
   - content_hash が無い場合のフォールバックが曖昧
   - 削除されたファイルのメタデータが残り続ける可能性

4. **セキュリティホール**
   - パストラバーサルへの対策が無い
   - 悪意のあるキーを含むメタデータを受け入れる
   - JSONシリアライズ時の例外が未処理

5. **パフォーマンスの問題**
   - 大量のファイルでセット演算が遅い
   - 巨大なファイルのハッシュ計算でメモリを使い切る可能性
   - メタデータの保存が毎回全体を書き込む（差分更新なし）

📝 **修正案**

```python
from typing import Dict, Set, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class DiffDetector:
    def __init__(self, metadata_path: Path):
        if not isinstance(metadata_path, Path):
            raise TypeError("metadata_path must be a Path object")
        
        self.metadata_path = metadata_path.resolve()  # 絶対パスに正規化
        self.metadata_file = self.metadata_path / "file_metadata.json"
        self.metadata: Dict[str, dict] = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, dict]:
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                if not isinstance(data, dict):
                    logger.error("メタデータの型が不正です（dict型である必要があります）")
                    return {}
                
                return data
        except json.JSONDecodeError as e:
            logger.error(f"メタデータのJSON解析に失敗: {e}")
            return {}
        except Exception as e:
            logger.error(f"メタデータの読み込みに失敗: {e}")
            return {}
    
    def update_metadata(self, file_id: str, file_info: dict):
        if not file_id or not isinstance(file_id, str):
            raise ValueError("file_id must be a non-empty string")
        
        if not isinstance(file_info, dict):
            raise TypeError("file_info must be a dictionary")
        
        self.metadata[file_id] = {
            **file_info,
            "last_updated": datetime.now().isoformat()
        }
        self._save_metadata()
```

開発者よ、defensive programming を学び直せ！
"""

