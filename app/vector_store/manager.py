"""
ベクターストア管理モジュール
LangChainとChromaDBを使用してドキュメントのベクターストアを管理
"""

from pathlib import Path
from typing import List, Optional, Dict
import os

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from ..data_sources.base import DocumentInfo
from ..utils.logger import setup_logger
from ..utils.diff_detector import DiffDetector


class VectorStoreManager:
    """ベクターストア管理クラス"""
    
    def __init__(
        self,
        vector_store_path: Path,
        metadata_path: Path,
        openai_api_key: str,
        embedding_model: str = "text-embedding-3-small",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        log_path: Path = None
    ):
        """
        Args:
            vector_store_path: ベクターストア保存先
            metadata_path: メタデータ保存先
            openai_api_key: OpenAI APIキー
            embedding_model: 使用するEmbeddingモデル
            chunk_size: チャンクサイズ
            chunk_overlap: チャンクオーバーラップ
            log_path: ログ出力先
        """
        self.vector_store_path = vector_store_path
        self.metadata_path = metadata_path
        self.openai_api_key = openai_api_key
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # ロガー設定
        if log_path is None:
            log_path = metadata_path.parent / "logs"
        self.logger = setup_logger("VectorStore", log_path)
        
        # OpenAI Embeddings
        os.environ["OPENAI_API_KEY"] = openai_api_key
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        
        # テキスト分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        # 差分検出器
        self.diff_detector = DiffDetector(metadata_path)
        
        # ベクターストア
        self.vector_store: Optional[Chroma] = None
        self._load_or_create_vector_store()
    
    def _load_or_create_vector_store(self):
        """ベクターストアを読み込みまたは作成"""
        try:
            if self.vector_store_path.exists() and list(self.vector_store_path.glob("*")):
                # 既存のベクターストアを読み込み
                self.vector_store = Chroma(
                    persist_directory=str(self.vector_store_path),
                    embedding_function=self.embeddings
                )
                self.logger.info("既存のベクターストアを読み込みました")
            else:
                # 新規作成
                self.vector_store = Chroma(
                    persist_directory=str(self.vector_store_path),
                    embedding_function=self.embeddings
                )
                self.logger.info("新規ベクターストアを作成しました")
        except Exception as e:
            self.logger.error(f"ベクターストアの読み込み/作成に失敗: {e}")
            raise
    
    def _document_to_langchain_docs(
        self,
        doc_info: DocumentInfo
    ) -> List[Document]:
        """DocumentInfoをLangChain Documentに変換し、チャンクに分割"""
        # テキストをチャンクに分割
        chunks = self.text_splitter.split_text(doc_info.content)
        
        # LangChain Documentに変換
        langchain_docs = []
        for i, chunk in enumerate(chunks):
            metadata = {
                "source": doc_info.name,
                "file_id": doc_info.file_id,
                "folder_path": doc_info.folder_path,
                "modified_time": doc_info.modified_time.isoformat(),
                "chunk_index": i,
                "total_chunks": len(chunks),
                **doc_info.metadata
            }
            langchain_docs.append(Document(page_content=chunk, metadata=metadata))
        
        return langchain_docs
    
    def add_documents(self, documents: List[DocumentInfo]) -> int:
        """
        ドキュメントをベクターストアに追加
        
        Args:
            documents: 追加するドキュメントのリスト
        
        Returns:
            追加されたチャンク数
        """
        if not documents:
            self.logger.info("追加するドキュメントがありません")
            return 0
        
        total_chunks = 0
        
        for doc_info in documents:
            try:
                # LangChain Documentに変換
                langchain_docs = self._document_to_langchain_docs(doc_info)
                
                # ベクターストアに追加
                self.vector_store.add_documents(langchain_docs)
                total_chunks += len(langchain_docs)
                
                # メタデータ更新
                self.diff_detector.update_metadata(
                    doc_info.file_id,
                    {
                        "name": doc_info.name,
                        "content_hash": doc_info.content_hash,
                        "modified_time": doc_info.modified_time.isoformat(),
                        "folder_path": doc_info.folder_path,
                        "chunk_count": len(langchain_docs)
                    }
                )
                
                self.logger.info(
                    f"追加: {doc_info.name} ({len(langchain_docs)} チャンク)"
                )
                
            except Exception as e:
                self.logger.error(f"ドキュメント追加エラー ({doc_info.name}): {e}")
        
        self.logger.info(f"合計 {total_chunks} チャンクを追加しました")
        return total_chunks
    
    def update_documents(self, documents: List[DocumentInfo]) -> int:
        """
        ドキュメントを更新（削除して再追加）
        
        Args:
            documents: 更新するドキュメントのリスト
        
        Returns:
            更新されたチャンク数
        """
        if not documents:
            self.logger.info("更新するドキュメントがありません")
            return 0
        
        total_chunks = 0
        
        for doc_info in documents:
            try:
                # 既存のチャンクを削除
                self.remove_document(doc_info.file_id)
                
                # 再追加
                langchain_docs = self._document_to_langchain_docs(doc_info)
                self.vector_store.add_documents(langchain_docs)
                total_chunks += len(langchain_docs)
                
                # メタデータ更新
                self.diff_detector.update_metadata(
                    doc_info.file_id,
                    {
                        "name": doc_info.name,
                        "content_hash": doc_info.content_hash,
                        "modified_time": doc_info.modified_time.isoformat(),
                        "folder_path": doc_info.folder_path,
                        "chunk_count": len(langchain_docs)
                    }
                )
                
                self.logger.info(
                    f"更新: {doc_info.name} ({len(langchain_docs)} チャンク)"
                )
                
            except Exception as e:
                self.logger.error(f"ドキュメント更新エラー ({doc_info.name}): {e}")
        
        self.logger.info(f"合計 {total_chunks} チャンクを更新しました")
        return total_chunks
    
    def remove_document(self, file_id: str):
        """
        ドキュメントをベクターストアから削除
        
        Args:
            file_id: ファイルID
        """
        try:
            # file_idでフィルタして削除
            self.vector_store.delete(where={"file_id": file_id})
            self.logger.info(f"削除: file_id={file_id}")
            
        except Exception as e:
            self.logger.error(f"ドキュメント削除エラー (file_id={file_id}): {e}")
    
    def process_incremental_update(
        self,
        current_documents: List[DocumentInfo]
    ) -> Dict[str, int]:
        """
        差分を検出して増分更新を実行
        
        Args:
            current_documents: 現在のドキュメント一覧
        
        Returns:
            更新統計情報
        """
        self.logger.info("差分検出を開始します")
        
        # 現在のファイル情報をマップに変換
        current_files = {
            doc.file_id: {
                "name": doc.name,
                "content_hash": doc.content_hash,
                "modified_time": doc.modified_time.isoformat()
            }
            for doc in current_documents
        }
        
        # 差分を検出
        new_files, updated_files, deleted_files = self.diff_detector.detect_changes(current_files)
        
        self.logger.info(
            f"差分検出結果: 新規={len(new_files)}, "
            f"更新={len(updated_files)}, 削除={len(deleted_files)}"
        )
        
        stats = {
            "new_count": 0,
            "updated_count": 0,
            "deleted_count": 0,
            "total_chunks": 0
        }
        
        # 新規ファイルを追加
        new_docs = [doc for doc in current_documents if doc.file_id in new_files]
        if new_docs:
            chunks = self.add_documents(new_docs)
            stats["new_count"] = len(new_docs)
            stats["total_chunks"] += chunks
        
        # 更新ファイルを処理
        updated_docs = [doc for doc in current_documents if doc.file_id in updated_files]
        if updated_docs:
            chunks = self.update_documents(updated_docs)
            stats["updated_count"] = len(updated_docs)
            stats["total_chunks"] += chunks
        
        # 削除ファイルを処理
        for file_id in deleted_files:
            self.remove_document(file_id)
            self.diff_detector.remove_metadata(file_id)
            stats["deleted_count"] += 1
        
        self.logger.info(
            f"増分更新完了: 新規={stats['new_count']}, "
            f"更新={stats['updated_count']}, 削除={stats['deleted_count']}, "
            f"チャンク数={stats['total_chunks']}"
        )
        
        return stats
    
    def search(
        self,
        query: str,
        k: int = 5
    ) -> List[Document]:
        """
        類似ドキュメントを検索
        
        Args:
            query: 検索クエリ
            k: 取得する結果数
        
        Returns:
            関連ドキュメントのリスト
        """
        try:
            results = self.vector_store.similarity_search(query, k=k)
            return results
        except Exception as e:
            self.logger.error(f"検索エラー: {e}")
            return []
    
    def search_with_score(
        self,
        query: str,
        k: int = 5
    ) -> List[tuple[Document, float]]:
        """
        類似度スコア付きでドキュメントを検索
        
        Args:
            query: 検索クエリ
            k: 取得する結果数
        
        Returns:
            (ドキュメント, 距離スコア)のタプルのリスト
            ※ChromaDBは距離を返すため、小さいほど類似度が高い
        """
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            self.logger.error(f"検索エラー: {e}")
            return []
    
    def get_retriever(self, k: int = 5):
        """
        Retrieverを取得（RAGで使用）
        
        Args:
            k: 取得する結果数
        
        Returns:
            VectorStoreRetriever
        """
        return self.vector_store.as_retriever(search_kwargs={"k": k})

