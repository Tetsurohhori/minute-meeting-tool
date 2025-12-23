"""
RAGチャットエンジン
ベクターストアを使用した質問応答システム
"""

from pathlib import Path
from typing import List, Dict, Optional
import os

from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from ..vector_store.manager import VectorStoreManager
from ..utils.logger import setup_logger


# システムプロンプト
SYSTEM_PROMPT = """あなたは議事メモを管理するアシスタントです。
以下の議事メモの内容に基づいて、ユーザーの質問に正確に答えてください。

【回答の指針】
1. 提供された議事メモの内容のみに基づいて回答してください
2. 情報が不足している場合は、その旨を明確に伝えてください
3. 複数の議事メモに関連情報がある場合は、それらを統合して回答してください
4. 回答には、参照した議事メモの名前を明記してください
5. 日本語で丁寧に回答してください

【注意事項】
- 議事メモに記載がない内容について推測で答えないでください
- 日付や数値などの具体的な情報は正確に引用してください
"""

QA_PROMPT_TEMPLATE = """
以下の議事メモの情報を参考にして、質問に答えてください。

【議事メモの情報】
{context}

【質問】
{question}

【回答】
"""


class RAGChatEngine:
    """RAGチャットエンジンクラス"""
    
    def __init__(
        self,
        vector_store_manager: VectorStoreManager,
        openai_api_key: str,
        chat_model: str = "gpt-4o-mini",
        top_k: int = 5,
        temperature: float = 0.3,
        log_path: Optional[Path] = None
    ):
        """
        Args:
            vector_store_manager: ベクターストアマネージャー
            openai_api_key: OpenAI APIキー
            chat_model: 使用するチャットモデル
            top_k: 検索結果の取得数
            temperature: 生成の温度パラメータ
            log_path: ログ出力先
        """
        self.vector_store_manager = vector_store_manager
        self.openai_api_key = openai_api_key
        self.chat_model = chat_model
        self.top_k = top_k
        self.temperature = temperature
        
        # ロガー設定
        if log_path is None:
            log_path = vector_store_manager.metadata_path.parent / "logs"
        self.logger = setup_logger("RAGChat", log_path)
        
        # OpenAI APIキーを設定
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # LLM設定
        self.llm = ChatOpenAI(
            model=chat_model,
            temperature=temperature
        )
        
        # プロンプトテンプレート
        self.qa_prompt = PromptTemplate(
            template=QA_PROMPT_TEMPLATE,
            input_variables=["context", "question"]
        )
        
        # メモリ（会話履歴）
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # RAGチェーン
        self.chain = self._create_chain()
        
        self.logger.info(f"RAGチャットエンジンを初期化しました (model={chat_model})")
    
    def _create_chain(self) -> ConversationalRetrievalChain:
        """RAGチェーンを作成"""
        retriever = self.vector_store_manager.get_retriever(k=self.top_k)
        
        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=self.memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": self.qa_prompt},
            verbose=False
        )
        
        return chain
    
    def chat(self, question: str, max_sources: int = 1) -> Dict[str, any]:
        """
        質問に対して回答を生成
        
        Args:
            question: ユーザーの質問
            max_sources: 表示する最大ソース数（デフォルト1件）
        
        Returns:
            回答と関連ドキュメント情報
        """
        try:
            self.logger.info(f"質問: {question}")
            
            # 類似度スコア付きで検索（回答生成とソース表示の両方で使用）
            # 「最新」を含む質問の場合、または具体的な数値が含まれる場合は多めに取得
            has_latest_keyword = any(keyword in question for keyword in ['最新', '最後', '直近', '現在'])
            
            # 質問から数値を抽出（金額、日付など）
            import re
            numbers_in_question = re.findall(r'(\d+(?:[.,]\d+)?)\s*(?:万円|円|回|年|月|日)', question)
            has_specific_numbers = len(numbers_in_question) > 0
            
            search_k = 10 if (has_latest_keyword or has_specific_numbers) else max_sources
            
            search_results = self.vector_store_manager.search_with_score(
                question, 
                k=search_k
            )
            
            if has_specific_numbers:
                self.logger.info(f"質問に含まれる数値: {numbers_in_question}")
            
            if not search_results:
                self.logger.warning("関連するドキュメントが見つかりませんでした")
                return {
                    "answer": "申し訳ございません。質問に関連する議事メモが見つかりませんでした。",
                    "sources": [],
                    "question": question
                }
            
            # 質問に具体的な数値が含まれている場合は、その数値が一致するドキュメントを優先
            if has_specific_numbers and search_results:
                self.logger.info(f"数値一致フィルタリングを実行")
                
                # 「回目」「回の」が含まれている場合は、ファイル名の「第〇回」とマッチング
                is_meeting_number_query = any(keyword in question for keyword in ['回目', '回の', '回目の'])
                
                # 各ドキュメントに含まれる数値を抽出
                docs_with_matching_numbers = []
                for doc, score in search_results:
                    if is_meeting_number_query:
                        # ファイル名から「第〇回」を抽出
                        source = doc.metadata.get('source', '')
                        meeting_numbers = re.findall(r'第(\d+)回', source)
                        # 質問の数値とファイル名の回数が一致するか
                        match_count = sum(1 for num in numbers_in_question if num in meeting_numbers)
                        self.logger.info(f"ファイル名マッチング: {source} - 回数={meeting_numbers}, 一致数={match_count}")
                    else:
                        # ドキュメント内容から数値を抽出（金額など）
                        doc_numbers = re.findall(r'(\d+(?:[.,]\d+)?)\s*(?:万円|円|年|月|日)', doc.page_content)
                        # 質問の数値と一致する数が多いほど優先
                        match_count = sum(1 for num in numbers_in_question if num in doc_numbers)
                    docs_with_matching_numbers.append((doc, score, match_count))
                
                # 一致数でソート（多い順）、次に距離スコア（小さい順）
                docs_sorted = sorted(docs_with_matching_numbers, key=lambda x: (-x[2], x[1]))
                
                # 一致がある場合は、最も一致度の高いものを選択
                if docs_sorted[0][2] > 0:
                    filtered_results = [(doc, score) for doc, score, count in docs_sorted[:max_sources] if count > 0]
                    self.logger.info(f"数値一致によるフィルタリング: {[(doc.metadata.get('source', 'unknown'), count) for doc, score, count in docs_sorted[:3]]}")
                else:
                    # 一致がない場合は通常通り
                    filtered_results = search_results[:max_sources]
            
            # 「最新」キーワードが含まれている場合は開催日時でソート
            elif any(keyword in question for keyword in ['最新', '最後', '直近', '現在']) and search_results:
                self.logger.info(f"「最新」キーワード検出 - 開催日時でソート")
                
                import re
                from datetime import datetime
                
                def extract_meeting_date(doc_content):
                    """ドキュメント内容から開催日時を抽出"""
                    # ■日時: YYYY/MM/DD HH:MM のパターンをマッチ
                    date_pattern = r'■日時[：:]\s*(\d{4})[//-](\d{1,2})[//-](\d{1,2})'
                    match = re.search(date_pattern, doc_content)
                    if match:
                        try:
                            year, month, day = match.groups()
                            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                            return datetime.strptime(date_str, "%Y-%m-%d")
                        except:
                            return datetime.min
                    return datetime.min  # 日付が見つからない場合は最古の日付
                
                def extract_company_keywords(question_text):
                    """質問文から会社名・プロジェクトのキーワードを抽出"""
                    # 一般的な会社名パターン
                    company_patterns = [
                        r'([\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+(?:株式会社|インダストリー|商事|ソリューションズ|フロンティア))',
                        r'([A-Z][a-z]+)',  # 英語の会社名
                    ]
                    keywords = []
                    for pattern in company_patterns:
                        matches = re.findall(pattern, question_text)
                        keywords.extend(matches)
                    return keywords
                
                # 質問から会社名キーワードを抽出
                company_keywords = extract_company_keywords(question)
                self.logger.info(f"抽出された会社キーワード: {company_keywords}")
                
                # 会社名が含まれるドキュメントをフィルタリング
                if company_keywords:
                    # いずれかのキーワードが含まれるドキュメントのみ
                    filtered_by_company = [
                        (doc, score) for doc, score in search_results
                        if any(keyword in doc.metadata.get('source', '') or keyword in doc.page_content 
                               for keyword in company_keywords)
                    ]
                    if filtered_by_company:
                        search_results = filtered_by_company
                        self.logger.info(f"会社名フィルタリング後: {len(search_results)}件")
                
                # 開催日時でソート（新しい順）
                search_results_with_dates = []
                for doc, score in search_results:
                    meeting_date = extract_meeting_date(doc.page_content)
                    search_results_with_dates.append((doc, score, meeting_date))
                
                # 日付でソート（新しい順）
                search_results_sorted = sorted(
                    search_results_with_dates, 
                    key=lambda x: x[2], 
                    reverse=True
                )
                
                # (doc, score)の形式に戻す
                filtered_results = [(doc, score) for doc, score, date in search_results_sorted[:max_sources]]
                
                self.logger.info(f"開催日時順ソート後の最上位: {[(doc.metadata.get('source', 'unknown'), date.strftime('%Y-%m-%d') if date != datetime.min else 'N/A') for doc, score, date in search_results_sorted[:max_sources]]}")
            else:
                # 通常は距離スコア順
                filtered_results = search_results[:max_sources] if search_results else []
            
            # ログに距離スコアを出力（デバッグ用）
            if filtered_results:
                self.logger.info(f"最終選択ドキュメント: {[(doc.metadata.get('source', 'unknown'), round(score, 3)) for doc, score in filtered_results]}")
            
            # フィルタリング後のドキュメントを使用して回答を生成
            # チェーンを直接実行するのではなく、LLMに直接問い合わせる
            if filtered_results:
                # コンテキストを構築
                context_parts = []
                for doc, _ in filtered_results[:max_sources]:
                    source_name = doc.metadata.get('source', '不明')
                    context_parts.append(f"【{source_name}】\n{doc.page_content}")
                context = "\n\n".join(context_parts)
                
                # プロンプトを構築
                prompt = self.qa_prompt.format(context=context, question=question)
                
                # 会話履歴を取得
                chat_history = self.memory.chat_memory.messages
                
                # LLMで回答を生成
                from langchain_core.messages import HumanMessage, SystemMessage
                messages = [SystemMessage(content=SYSTEM_PROMPT)]
                messages.extend(chat_history)
                messages.append(HumanMessage(content=prompt))
                
                answer = self.llm.invoke(messages).content
                
                # メモリに追加
                self.memory.save_context({"question": question}, {"answer": answer})
            else:
                answer = "申し訳ございません。質問に関連する議事メモが見つかりませんでした。"
            
            # ソースドキュメント情報を整形（filtered_resultsをそのまま使用）
            sources = []
            seen_sources = set()
            
            for doc, score in filtered_results[:max_sources]:
                source_name = doc.metadata.get("source", "不明")
                folder_path = doc.metadata.get("folder_path", "")
                file_id = doc.metadata.get("file_id", "")
                file_url = doc.metadata.get("file_url", "")
                data_source = doc.metadata.get("data_source", "unknown")
                
                # 重複を避ける（ファイル単位で）
                source_key = f"{file_id}"
                if source_key not in seen_sources:
                    # ドキュメント全文を取得（同じfile_idのチャンクを結合）
                    full_content = self._get_full_document_content(file_id, filtered_results)
                    
                    sources.append({
                        "name": source_name,
                        "folder_path": folder_path,
                        "content": full_content,
                        "file_id": file_id,
                        "file_url": file_url,
                        "data_source": data_source,
                        "distance": round(score, 3),  # 距離スコア（デバッグ用）
                        "relevance_score": round(1.0 - min(score, 1.0), 3)  # 距離を類似度に変換
                    })
                    seen_sources.add(source_key)
            
            self.logger.info(f"回答生成完了 (参照ドキュメント数: {len(sources)})")
            
            return {
                "answer": answer,
                "sources": sources,
                "question": question
            }
            
        except Exception as e:
            self.logger.error(f"チャットエラー: {e}")
            return {
                "answer": f"エラーが発生しました: {str(e)}",
                "sources": [],
                "question": question
            }
    
    def _get_full_document_content(
        self, 
        file_id: str, 
        search_results: List[tuple]
    ) -> str:
        """
        同じfile_idを持つ全チャンクを結合して全文を取得
        
        Args:
            file_id: ファイルID
            search_results: (Document, score)のタプルのリスト
        
        Returns:
            ドキュメント全文
        """
        # 同じfile_idのチャンクを収集
        chunks = []
        for doc, _ in search_results:
            if doc.metadata.get("file_id") == file_id:
                chunk_index = doc.metadata.get("chunk_index", 0)
                chunks.append((chunk_index, doc.page_content))
        
        # チャンクインデックス順にソートして結合
        chunks.sort(key=lambda x: x[0])
        return "\n".join([content for _, content in chunks])
    
    def search_documents(self, query: str, k: Optional[int] = None) -> List[Dict]:
        """
        関連ドキュメントを検索
        
        Args:
            query: 検索クエリ
            k: 取得する結果数（Noneの場合はデフォルト値）
        
        Returns:
            関連ドキュメントのリスト
        """
        if k is None:
            k = self.top_k
        
        try:
            results = self.vector_store_manager.search(query, k=k)
            
            documents = []
            for doc in results:
                documents.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "不明"),
                    "folder_path": doc.metadata.get("folder_path", ""),
                    "chunk_index": doc.metadata.get("chunk_index", 0),
                    "metadata": doc.metadata
                })
            
            return documents
            
        except Exception as e:
            self.logger.error(f"ドキュメント検索エラー: {e}")
            return []
    
    def clear_history(self):
        """会話履歴をクリア"""
        self.memory.clear()
        self.logger.info("会話履歴をクリアしました")
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """
        会話履歴を取得
        
        Returns:
            会話履歴のリスト
        """
        history = []
        messages = self.memory.chat_memory.messages
        
        for msg in messages:
            role = "user" if msg.type == "human" else "assistant"
            history.append({
                "role": role,
                "content": msg.content
            })
        
        return history

