"""
🔥 統合的な意地悪テスト - システム全体への攻撃

複数のコンポーネントを組み合わせた悪意のあるシナリオで、
システムの限界を徹底的に試す。
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# テスト対象のインポート
from app.config.settings import Settings
from app.data_sources.base import DocumentInfo
from app.utils.diff_detector import DiffDetector


class TestSystemIntegrationAttacks:
    """システム統合への攻撃"""
    
    @pytest.mark.adversarial
    @pytest.mark.integration
    @pytest.mark.slow
    def test_full_workflow_with_corrupted_data(self, temp_dir, monkeypatch):
        """❌ 全ワークフローで壊れたデータを流し込む"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        # 設定を初期化
        settings = Settings()
        
        # 差分検出器を初期化
        detector = DiffDetector(temp_dir)
        
        # 壊れたドキュメントデータ
        corrupted_docs = {
            "": {"content_hash": "empty_id"},  # 空のID
            None: {"content_hash": "none_id"},  # None ID
            "normal": {"content_hash": ""},  # 空のハッシュ
            "missing": {},  # ハッシュフィールド無し
        }
        
        # 差分検出を実行（例外が出ないか確認）
        try:
            new, updated, deleted = detector.detect_changes(corrupted_docs)
            # 壊れたデータでも処理が続くべき（落ちてはいけない）
            assert True, "壊れたデータでも処理が継続できた"
        except Exception as e:
            pytest.fail(f"壊れたデータで例外が発生: {e}")
    
    @pytest.mark.adversarial
    @pytest.mark.integration
    @pytest.mark.resource_attack
    def test_memory_exhaustion_attack(self, temp_dir, monkeypatch):
        """❌ メモリ枯渇攻撃"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("CHUNK_SIZE", "10000000")  # 10MB チャンク
        
        settings = Settings()
        
        # 10万ファイルの巨大なデータセット
        massive_data = {}
        for i in range(100000):
            massive_data[f"file_{i}"] = {
                "content_hash": f"hash_{i}" * 100,  # 長いハッシュ
                "name": f"document_{i}.txt" * 50,  # 長いファイル名
                "content": "A" * 10000,  # 10KB コンテンツ
            }
        
        detector = DiffDetector(temp_dir)
        
        # メモリ使用量が爆発する可能性
        try:
            new, updated, deleted = detector.detect_changes(massive_data)
            assert len(new) == 100000, "大量のファイルを処理できた"
        except MemoryError:
            pytest.fail("メモリ不足で失敗！リソース管理が甘い！")
    
    @pytest.mark.adversarial
    @pytest.mark.integration
    @pytest.mark.security
    def test_combined_injection_attacks(self, temp_dir):
        """❌ 複合インジェクション攻撃"""
        # SQL + XSS + パストラバーサルを組み合わせた悪意のあるドキュメント
        malicious_doc = DocumentInfo(
            file_id="'; DROP TABLE files; --",
            name="<script>alert('XSS')</script>",
            content="{{constructor.constructor('return process')().exit()}}",
            modified_time=datetime.now(),
            folder_path="../../etc/",
            content_hash="../../../root/.ssh/id_rsa"
        )
        
        # これが保存され、後で読み込まれる
        detector = DiffDetector(temp_dir)
        detector.update_metadata(
            malicious_doc.file_id,
            {
                "name": malicious_doc.name,
                "content_hash": malicious_doc.content_hash,
                "folder_path": malicious_doc.folder_path,
            }
        )
        
        # メタデータを読み込み直す
        detector2 = DiffDetector(temp_dir)
        
        # 悪意のあるデータがそのまま保存されている
        stored = detector2.get_file_info(malicious_doc.file_id)
        assert stored is not None, "悪意のあるデータが保存された"
        assert "<script>" in stored["name"], "XSSパターンが保存された！"
        assert ".." in stored["folder_path"], "パストラバーサルが保存された！"
    
    @pytest.mark.adversarial
    @pytest.mark.integration
    @pytest.mark.boundary
    def test_race_condition_simulation(self, temp_dir, monkeypatch):
        """❌ 競合状態のシミュレーション"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        detector1 = DiffDetector(temp_dir)
        detector2 = DiffDetector(temp_dir)
        
        # 同じファイルを異なるインスタンスから同時に更新
        detector1.update_metadata("file1", {"content_hash": "hash_v1"})
        detector2.update_metadata("file1", {"content_hash": "hash_v2"})
        
        # どちらのバージョンが保存されたか？
        detector3 = DiffDetector(temp_dir)
        stored = detector3.get_file_info("file1")
        
        # 最後の書き込みが勝つ（Last Write Wins）
        assert stored["content_hash"] == "hash_v2", \
            "競合状態でデータが失われた！ロック機構が無い！"
    
    @pytest.mark.adversarial
    @pytest.mark.integration
    def test_circular_dependency_detection(self, temp_dir):
        """❌ 循環参照の検出"""
        detector = DiffDetector(temp_dir)
        
        # 循環参照を作る（Pythonではリストで可能）
        circular_data = {"file1": {}}
        circular_data["file1"]["self_reference"] = circular_data["file1"]
        
        # JSONにシリアライズできない
        detector.metadata = circular_data
        
        with pytest.raises((ValueError, RecursionError)):
            detector._save_metadata()


class TestConfigurationCombinationAttacks:
    """設定の組み合わせ攻撃"""
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    @pytest.mark.parametrize("chunk_size,chunk_overlap", [
        (100, 200),  # オーバーラップがチャンクより大きい
        (0, 0),  # どちらもゼロ
        (-100, 50),  # 負のチャンクサイズ
        (100, -50),  # 負のオーバーラップ
        (1, 0),  # 極端に小さいチャンク
    ])
    def test_invalid_chunk_configurations(self, chunk_size, chunk_overlap, monkeypatch):
        """❌ 不正なチャンク設定の組み合わせ"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("CHUNK_SIZE", str(chunk_size))
        monkeypatch.setenv("CHUNK_OVERLAP", str(chunk_overlap))
        
        settings = Settings()
        
        # これらの設定は論理的に矛盾している
        # しかし、現状の実装では通ってしまう可能性が高い
        if chunk_overlap >= chunk_size and chunk_size > 0:
            pytest.fail("オーバーラップがチャンクサイズより大きいのに通った！")
        
        if chunk_size <= 0 or chunk_overlap < 0:
            pytest.fail("負数やゼロの設定が通った！")
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_all_environment_variables_empty(self, monkeypatch):
        """❌ すべての環境変数が空の場合"""
        # OpenAI API キー以外を全て空に
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("DATA_SOURCE", "")
        monkeypatch.setenv("GOOGLE_DRIVE_FOLDER_ID", "")
        monkeypatch.setenv("CHUNK_SIZE", "")
        
        # 空文字列が int() に渡されてエラー
        with pytest.raises(ValueError):
            Settings()


class TestBoundaryValueCombinations:
    """境界値の組み合わせテスト"""
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    @pytest.mark.parametrize("input_data", [
        {"": ""},  # 両方空
        {" ": " "},  # 両方スペース
        {"\n": "\n"},  # 両方改行
        {"\x00": "\x00"},  # Null バイト
        {"🔥": "💀"},  # 絵文字
    ])
    def test_extreme_boundary_values_in_metadata(self, temp_dir, input_data):
        """❌ 極端な境界値をメタデータに保存"""
        detector = DiffDetector(temp_dir)
        
        for key, value in input_data.items():
            detector.update_metadata(key, {"content_hash": value})
        
        # 再読み込み
        detector2 = DiffDetector(temp_dir)
        
        # すべてのキーが保存されているか確認
        for key in input_data.keys():
            stored = detector2.get_file_info(key)
            assert stored is not None, f"キー '{repr(key)}' が保存されなかった"


class TestErrorPropagation:
    """エラー伝播のテスト"""
    
    @pytest.mark.adversarial
    @pytest.mark.integration
    def test_error_in_metadata_loading_propagates_silently(self, temp_dir):
        """❌ メタデータ読み込みエラーが静かに飲み込まれる"""
        metadata_file = temp_dir / "file_metadata.json"
        
        # 壊れたJSONを書き込む
        metadata_file.write_text("{ broken json }")
        
        # エラーが print() されるだけで、例外は発生しない
        detector = DiffDetector(temp_dir)
        
        # メタデータは空になっている
        assert detector.metadata == {}, \
            "エラーが静かに飲み込まれた！ロギングさえされていない可能性！"
    
    @pytest.mark.adversarial
    @pytest.mark.integration
    def test_permission_error_handling(self, temp_dir, monkeypatch):
        """❌ パーミッションエラーの処理"""
        
        # ファイルを読み込み専用にする
        metadata_file = temp_dir / "file_metadata.json"
        metadata_file.write_text("{}")
        metadata_file.chmod(0o444)  # 読み込み専用
        
        detector = DiffDetector(temp_dir)
        
        # 書き込もうとすると失敗する
        detector.update_metadata("file1", {"content_hash": "hash"})
        
        # パーミッションエラーが発生するはず
        # しかし、例外処理が無いのでクラッシュする
        
        # クリーンアップ
        metadata_file.chmod(0o644)


# =====================================
# 最終批判
# =====================================

"""
🔥🔥🔥 最終的な痛烈な批判 🔥🔥🔥

このシステムには以下の深刻な問題がある：

## 1. セキュリティ問題（致命的）
- パストラバーサル攻撃への対策ゼロ
- インジェクション攻撃がそのまま保存される
- 入力の検証が一切無い

## 2. データ整合性の欠如（深刻）
- 競合状態でデータが失われる
- トランザクション機構が無い
- バックアップやロールバックが無い

## 3. エラーハンドリングの甘さ（深刻）
- エラーが print() で流れるだけ
- ロギングが不十分
- ユーザーがエラーに気づけない

## 4. リソース管理の欠如（深刻）
- メモリ使用量の制限が無い
- 大量のファイルでパフォーマンスが劣化
- タイムアウト機構が無い

## 5. 型安全性の問題（中程度）
- 型ヒントがあっても実行時チェックが無い
- None, 空文字列, 不正な型がすべて通る
- 後でクラッシュする時限爆弾

## 6. テスタビリティの問題（中程度）
- シングルトンのリセットができない
- モック化が困難
- 外部依存が強い

---

📝 **推奨される修正**

1. **入力検証の徹底**
   - すべての入力に対してバリデーションを実装
   - ホワイトリスト方式の検証
   - 正規表現による厳格なチェック

2. **エラーハンドリングの改善**
   - ロギングフレームワークの使用
   - 例外の適切な処理と伝播
   - ユーザーへの分かりやすいエラーメッセージ

3. **リソース管理の実装**
   - ファイルサイズの上限設定
   - メモリ使用量の監視
   - タイムアウトの実装

4. **セキュリティ対策**
   - パス正規化（Path.resolve()）
   - サニタイゼーション
   - 権限チェック

5. **データ整合性の保証**
   - ファイルロック機構
   - アトミックな書き込み
   - バックアップとロールバック

---

開発者よ、これらの問題を修正するまで、
このシステムは本番環境に投入してはならない！

テスターAIは降参しない。
まだまだバグを見つけてやる。
"""

