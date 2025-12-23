"""
🔥 DataSourceBase と DocumentInfo への意地悪な攻撃的テスト

データクラス、抽象基底クラスの脆弱性を徹底的に突く。
"""

import pytest
from datetime import datetime
from typing import Dict
from unittest.mock import Mock, patch

from app.data_sources.base import DocumentInfo, DataSourceBase


class TestDocumentInfoAttacks:
    """DocumentInfo データクラスへの攻撃"""
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_document_info_with_none_values(self):
        """❌ すべてのフィールドに None を渡したら？"""
        with pytest.raises((TypeError, ValueError)):
            doc = DocumentInfo(
                file_id=None,
                name=None,
                content=None,
                modified_time=None,
                folder_path=None,
                content_hash=None
            )
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_document_info_with_wrong_types(self):
        """❌ 型が違うデータを渡したら？"""
        # dataclass は型チェックをしないので通ってしまう
        doc = DocumentInfo(
            file_id=12345,  # 数値（文字列のはず）
            name=["not", "a", "string"],  # リスト
            content={"dict": "instead"},  # 辞書
            modified_time="not a datetime",  # 文字列
            folder_path=None,
            content_hash=b"bytes_instead"  # バイト列
        )
        
        # 型ヒントがあっても実行時チェックはされない
        assert doc.file_id == 12345, \
            "型が違うのに通った！後で文字列操作でクラッシュする！"
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_document_info_with_empty_strings(self):
        """❌ 空文字列だけのドキュメント"""
        doc = DocumentInfo(
            file_id="",
            name="",
            content="",
            modified_time=datetime.now(),
            folder_path="",
            content_hash=""
        )
        
        # 空文字列でも作成できるが、これは有効なデータか？
        assert doc.file_id == "", "空のファイルIDが通った！"
        assert doc.content == "", "空のコンテンツが通った！"
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_document_info_with_extremely_long_content(self):
        """❌ 極端に長いコンテンツでメモリを圧迫"""
        huge_content = "A" * (100 * 1024 * 1024)  # 100MB
        
        doc = DocumentInfo(
            file_id="huge_file",
            name="huge.txt",
            content=huge_content,
            modified_time=datetime.now(),
            folder_path="/test",
            content_hash="hash123"
        )
        
        # メモリを大量に消費する
        assert len(doc.content) == 100 * 1024 * 1024, \
            "巨大なコンテンツでメモリが圧迫される！"
    
    @pytest.mark.adversarial
    @pytest.mark.security
    def test_document_info_with_malicious_file_paths(self):
        """❌ 悪意のあるファイルパスを含むドキュメント"""
        doc = DocumentInfo(
            file_id="../../../etc/passwd",
            name="<script>alert('XSS')</script>",
            content="'; DROP TABLE documents; --",
            modified_time=datetime.now(),
            folder_path="../../root/",
            content_hash="hash"
        )
        
        # パストラバーサル、XSS、SQLインジェクションのパターンがそのまま保存される
        assert "../" in doc.file_id, "パストラバーサルが通った！"
        assert "<script>" in doc.name, "XSSパターンが通った！"
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_document_info_metadata_is_none_by_default(self):
        """❌ metadata のデフォルト値が正しく初期化されるか"""
        doc = DocumentInfo(
            file_id="test",
            name="test.txt",
            content="content",
            modified_time=datetime.now(),
            folder_path="/test",
            content_hash="hash"
        )
        
        # __post_init__ で空の辞書が設定される
        assert doc.metadata == {}, "metadata が None のまま残った！"
        
        # しかし、metadata=None を明示的に渡した場合も同じ
        doc2 = DocumentInfo(
            file_id="test2",
            name="test2.txt",
            content="content",
            modified_time=datetime.now(),
            folder_path="/test",
            content_hash="hash",
            metadata=None
        )
        assert doc2.metadata == {}, "__post_init__ が実行された"
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_document_info_metadata_with_wrong_type(self):
        """❌ metadata にリストを渡したら？"""
        doc = DocumentInfo(
            file_id="test",
            name="test.txt",
            content="content",
            modified_time=datetime.now(),
            folder_path="/test",
            content_hash="hash",
            metadata=["not", "a", "dict"]  # リストを渡す
        )
        
        # __post_init__ は metadata が None の場合のみ処理するので、
        # リストのまま保存される
        assert isinstance(doc.metadata, list), \
            "metadata の型チェックが無い！辞書を期待しているのに！"


class TestDataSourceBaseAttacks:
    """DataSourceBase 抽象基底クラスへの攻撃"""
    
    @pytest.mark.adversarial
    def test_cannot_instantiate_abstract_class(self):
        """❌ 抽象基底クラスを直接インスタンス化できないことを確認"""
        with pytest.raises(TypeError):
            DataSourceBase()
    
    @pytest.mark.adversarial
    def test_subclass_without_implementing_abstract_methods(self):
        """❌ 抽象メソッドを実装しないサブクラス"""
        
        # 抽象メソッドを実装していないサブクラス
        class IncompleteDataSource(DataSourceBase):
            pass
        
        # インスタンス化できない
        with pytest.raises(TypeError):
            IncompleteDataSource()
    
    @pytest.mark.adversarial
    def test_subclass_with_wrong_signature(self):
        """❌ 間違ったシグネチャで抽象メソッドを実装"""
        
        class WrongSignatureDataSource(DataSourceBase):
            def authenticate(self):
                return True
            
            def list_documents(self):  # folder_path 引数が無い
                return []
            
            def get_document_content(self, file_id: str) -> str:
                return ""
            
            def get_document_info(self, file_id: str):
                return None
        
        # インスタンス化はできるが、シグネチャが違う
        ds = WrongSignatureDataSource()
        
        # folder_path を渡すとエラーになる
        with pytest.raises(TypeError):
            ds.list_documents(folder_path="/test")
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_get_all_documents_recursive_default_implementation(self):
        """❌ get_all_documents_recursive のデフォルト実装の脆弱性"""
        
        class MockDataSource(DataSourceBase):
            def authenticate(self) -> bool:
                return True
            
            def list_documents(self, folder_path=None):
                # 常に自分自身を返す（無限ループを作る）
                return [
                    DocumentInfo(
                        file_id="loop",
                        name="loop.txt",
                        content="loop",
                        modified_time=datetime.now(),
                        folder_path=folder_path or "/",
                        content_hash="hash"
                    )
                ]
            
            def get_document_content(self, file_id: str) -> str:
                return "content"
            
            def get_document_info(self, file_id: str):
                return None
        
        ds = MockDataSource()
        
        # get_all_documents_recursive は単に list_documents を呼ぶだけ
        # 再帰的には取得しない！メソッド名が嘘！
        docs = ds.get_all_documents_recursive("/test")
        assert len(docs) == 1, "再帰的に取得していない！名前詐欺！"


class TestDocumentInfoHashingAttacks:
    """DocumentInfo のハッシュ計算への攻撃"""
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_same_content_different_hash(self):
        """❌ 同じコンテンツなのに違うハッシュ？"""
        doc1 = DocumentInfo(
            file_id="file1",
            name="test.txt",
            content="same content",
            modified_time=datetime(2024, 1, 1),
            folder_path="/test",
            content_hash="hash1"
        )
        
        doc2 = DocumentInfo(
            file_id="file2",
            name="test.txt",
            content="same content",
            modified_time=datetime(2024, 1, 1),
            folder_path="/test",
            content_hash="hash2"  # 違うハッシュ
        )
        
        # content_hash はユーザーが渡すので、整合性チェックが無い
        assert doc1.content == doc2.content, "コンテンツは同じ"
        assert doc1.content_hash != doc2.content_hash, \
            "同じコンテンツなのに違うハッシュ！整合性チェックが無い！"
    
    @pytest.mark.adversarial
    @pytest.mark.security
    def test_hash_collision_attack(self):
        """❌ ハッシュ衝突攻撃（理論的）"""
        # SHA256 のハッシュ衝突は現実的には不可能だが、
        # もし同じハッシュを持つ異なるコンテンツがあったら？
        
        doc1 = DocumentInfo(
            file_id="file1",
            name="test1.txt",
            content="content A",
            modified_time=datetime.now(),
            folder_path="/test",
            content_hash="same_hash"  # 同じハッシュ
        )
        
        doc2 = DocumentInfo(
            file_id="file2",
            name="test2.txt",
            content="content B",  # 違うコンテンツ
            modified_time=datetime.now(),
            folder_path="/test",
            content_hash="same_hash"  # 同じハッシュ
        )
        
        # ハッシュが同じなので、差分検出で「変更なし」と判定される
        assert doc1.content_hash == doc2.content_hash, \
            "ハッシュ衝突が発生すると差分検出が機能しない！"


# =====================================
# 批判的フィードバック
# =====================================

"""
🔥 開発者への痛烈な批判 🔥

1. **データクラスの型安全性の欠如**
   - 型ヒントがあっても実行時には何もチェックされない
   - 間違った型のデータを受け入れてしまう
   - None, 空文字列, リストなど何でも通る

2. **バリデーションの完全な欠如**
   - file_id が空文字列でも通る
   - content が100MBでも制限が無い
   - パストラバーサル、XSS、SQLインジェクションのパターンがそのまま保存される

3. **metadata フィールドの脆弱性**
   - __post_init__ が None の場合のみ処理
   - リストなど違う型を渡しても通ってしまう
   - 後で辞書操作でクラッシュする

4. **抽象基底クラスの問題**
   - get_all_documents_recursive() が再帰的に取得しない
   - メソッド名が実装と一致していない（名前詐欺）
   - デフォルト実装が単なる list_documents() の呼び出し

5. **ハッシュの整合性チェック欠如**
   - content_hash はユーザーが渡すので、整合性が保証されない
   - 同じコンテンツでも違うハッシュを持てる
   - ハッシュ衝突（理論的）への対策が無い

📝 **修正案**

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
import hashlib

@dataclass
class DocumentInfo:
    file_id: str
    name: str
    content: str
    modified_time: datetime
    folder_path: str
    content_hash: str = field(default="")
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def __post_init__(self):
        # 型チェック
        if not isinstance(self.file_id, str) or not self.file_id.strip():
            raise ValueError("file_id must be a non-empty string")
        
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty string")
        
        if not isinstance(self.content, str):
            raise ValueError("content must be a string")
        
        if not isinstance(self.modified_time, datetime):
            raise ValueError("modified_time must be a datetime object")
        
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")
        
        # セキュリティチェック
        if ".." in self.file_id or ".." in self.folder_path:
            raise ValueError("Path traversal detected")
        
        # ハッシュの自動計算（整合性保証）
        if not self.content_hash:
            self.content_hash = self._calculate_hash()
        else:
            # ハッシュが渡された場合、整合性を確認
            expected_hash = self._calculate_hash()
            if self.content_hash != expected_hash:
                raise ValueError("content_hash does not match content")
        
        # コンテンツサイズの制限（10MB）
        if len(self.content) > 10 * 1024 * 1024:
            raise ValueError("Content size exceeds 10MB limit")
    
    def _calculate_hash(self) -> str:
        return hashlib.sha256(self.content.encode('utf-8')).hexdigest()
```

開発者よ、データの整合性を保証する機構を実装せよ！
"""

