"""
議事メモRAGチャットボット - Streamlit Web UI
"""

import streamlit as st
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_settings
from app.vector_store import VectorStoreManager
from app.rag import RAGChatEngine


# ページ設定
st.set_page_config(
    page_title="Salesチーム議事メモRAGチャット",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource(show_spinner="システムを初期化中...")
def initialize_system(_cache_version: str = "v1.1"):
    """
    システムを初期化（キャッシュ）
    
    Args:
        _cache_version: キャッシュのバージョン（コード更新時に変更することでキャッシュを無効化）
    """
    try:
        settings = get_settings()
        
        # ベクターストアマネージャーを初期化
        vector_store_manager = VectorStoreManager(
            vector_store_path=settings.vector_store_path,
            metadata_path=settings.metadata_path,
            openai_api_key=settings.openai_api_key,
            embedding_model=settings.embedding_model,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            log_path=settings.log_path
        )
        
        # RAGチャットエンジンを初期化
        chat_engine = RAGChatEngine(
            vector_store_manager=vector_store_manager,
            openai_api_key=settings.openai_api_key,
            chat_model=settings.chat_model,
            top_k=settings.top_k_results,
            log_path=settings.log_path
        )
        
        return chat_engine, settings
        
    except Exception as e:
        st.error(f"初期化エラー: {str(e)}")
        st.stop()


def main():
    """メインアプリケーション"""
    
    # システム初期化（キャッシュバージョンを指定）
    try:
        chat_engine, settings = initialize_system(_cache_version="v1.1")
    except Exception as e:
        st.error(f"システムの初期化に失敗しました: {str(e)}")
        st.info("`.env`ファイルが正しく設定されているか確認してください。")
        st.stop()
    
    # サイドバー
    with st.sidebar:
        # 登録ドキュメント数（ベクターストアから直接取得）
        try:
            # ベクターストアマネージャーを取得
            vector_store_manager = chat_engine.vector_store_manager
            
            # メソッドの存在を確認（Streamlit Cloudのキャッシュ問題に対応）
            if hasattr(vector_store_manager, 'get_document_count'):
                doc_count = vector_store_manager.get_document_count()
            else:
                # フォールバック: ChromaDBから直接取得を試みる
                doc_count = 0
                try:
                    if vector_store_manager.vector_store is not None:
                        results = vector_store_manager.vector_store.get()
                        if results and "metadatas" in results:
                            metadatas = results["metadatas"]
                            if metadatas:
                                unique_file_ids = set()
                                for metadata in metadatas:
                                    if metadata and "file_id" in metadata:
                                        unique_file_ids.add(metadata["file_id"])
                                doc_count = len(unique_file_ids)
                except Exception as e:
                    doc_count = 0
                    # デバッグ情報（開発環境のみ）
                    import os
                    if os.getenv("DEBUG", "false").lower() == "true":
                        st.exception(e)
                    
        except Exception as e:
            # エラーが発生した場合は0を表示
            doc_count = 0
            st.warning(f"ドキュメント数の取得に失敗しました: {str(e)}")
        
        st.metric("📄 登録ドキュメント数", doc_count)
        
        # ベクターストアが空の場合の警告
        if doc_count == 0:
            st.warning("⚠️ ベクターストアが空です。\n\n`scripts/update_vector_store.py`を実行してドキュメントを登録してください。")
        
        st.markdown("---")
        
        # 履歴クリアボタン
        if st.button("🗑️ 会話履歴をクリア", use_container_width=True):
            chat_engine.clear_history()
            st.session_state.messages = []
            st.success("会話履歴をクリアしました")
            st.rerun()
    
    # メインエリア
    # タイトルと説明（会話履歴がない場合のみ表示）
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if len(st.session_state.messages) == 0:
        st.title("💼 Salesチーム議事メモRAGチャットアプリ")
        
        # 説明文
        st.markdown("""
        💬 こちらはSalesチームの議事メモを検索・活用できるRAGチャットアプリです。  
        過去の会議メモから情報を検索し、プロジェクトの状況確認、決定事項の確認、ToDo整理などをサポートします。  
        画面下部のチャット欄から質問を送信してください。
        """)
        
        # 入力例
        st.info("""
        **入力例**
        - 「〇〇プロジェクトの最新状況をサマって教えて」
        - 「〇〇さんとの前回会議で決まったことは？」
        - 「〇〇における、弊社ToDoを再整理して」
        """)
    
    # 回答生成中かどうかを判定（最後のメッセージがユーザーで、まだアシスタントの回答が追加されていない場合）
    is_generating = (
        len(st.session_state.messages) > 0 and 
        st.session_state.messages[-1]["role"] == "user"
    )
    
    # 会話履歴の表示
    for msg_idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # ソース情報を表示（アシスタントの場合）
            # ただし、回答生成中で最後のアシスタントメッセージの場合は非表示（重複を防ぐ）
            if message["role"] == "assistant" and "sources" in message:
                # 回答生成中で、このメッセージが最後のアシスタントメッセージの場合は非表示
                # （最後のメッセージがユーザーの場合、その前のメッセージが最後のアシスタントメッセージ）
                should_hide = (
                    is_generating and 
                    msg_idx == len(st.session_state.messages) - 2 and
                    len(st.session_state.messages) > 1
                )
                
                if not should_hide and message["sources"]:
                    with st.expander(f"📄 参照した議事メモ（{len(message['sources'])}件）"):
                        for i, source in enumerate(message["sources"], 1):
                            folder = source.get("folder_path", "")
                            name = source.get("name", "不明")
                            path = f"{folder}/{name}" if folder else name
                            file_url = source.get("file_url", "")
                            relevance = source.get("relevance_score", 0)
                            
                            # タイトルとリンク（距離スコアも表示）
                            distance = source.get("distance", 0)
                            if file_url:
                                st.markdown(f"**{i}. [{path}]({file_url})** (関連度: {relevance:.1%}, 距離: {distance:.3f})")
                            else:
                                st.markdown(f"**{i}. {path}** (関連度: {relevance:.1%}, 距離: {distance:.3f})")
                            
                            # 全文表示
                            content = source.get("content", "")
                            if content:
                                # ユニークなキーを生成（メッセージインデックス + ソースインデックス）
                                st.text_area(
                                    f"内容_{i}",
                                    content,
                                    height=200,
                                    disabled=True,
                                    label_visibility="collapsed",
                                    key=f"hist_{msg_idx}_src_{i}"
                                )
                            
                            if i < len(message["sources"]):
                                st.markdown("---")
    
    # ユーザー入力
    if prompt := st.chat_input("議事メモについて質問してください..."):
        # ユーザーメッセージを追加
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # ユーザーメッセージを表示
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # アシスタントの応答
        with st.chat_message("assistant"):
            with st.spinner("考え中..."):
                # RAGエンジンで回答を生成
                response = chat_engine.chat(prompt)
                answer = response["answer"]
                sources = response["sources"]
                
                # 回答を表示
                st.markdown(answer)
                
                # ソース情報を表示
                if sources:
                    with st.expander(f"📄 参照した議事メモ（{len(sources)}件）"):
                        for i, source in enumerate(sources, 1):
                            folder = source.get("folder_path", "")
                            name = source.get("name", "不明")
                            path = f"{folder}/{name}" if folder else name
                            file_url = source.get("file_url", "")
                            relevance = source.get("relevance_score", 0)
                            
                            # タイトルとリンク（距離スコアも表示）
                            distance = source.get("distance", 0)
                            if file_url:
                                st.markdown(f"**{i}. [{path}]({file_url})** (関連度: {relevance:.1%}, 距離: {distance:.3f})")
                            else:
                                st.markdown(f"**{i}. {path}** (関連度: {relevance:.1%}, 距離: {distance:.3f})")
                            
                            # 全文表示
                            content = source.get("content", "")
                            if content:
                                # 新しい回答用のユニークなキー（"new"プレフィックス）
                                st.text_area(
                                    f"内容_{i}",
                                    content,
                                    height=200,
                                    disabled=True,
                                    label_visibility="collapsed",
                                    key=f"new_src_{i}"
                                )
                            
                            if i < len(sources):
                                st.markdown("---")
                else:
                    st.info("関連する議事メモが見つかりませんでした。")
        
        # アシスタントメッセージを保存
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })


if __name__ == "__main__":
    main()

