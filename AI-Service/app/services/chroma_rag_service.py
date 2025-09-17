import os
import json
import chromadb
from typing import List, Dict, Any, Optional
from app.core.ai import call_openai_api
from app.core.config import settings


class ChromaRAGService:
    """ChromaDB 기반 RAG 서비스"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.embedding_data_path = os.path.join(os.path.dirname(__file__), "..", "embedding_data")
        self.cache_path = os.path.join(os.path.dirname(__file__), "..", "cache", "rag", "chroma_db")
        self._initialize_chromadb()
    
    def _initialize_chromadb(self):
        """ChromaDB 초기화 및 컬렉션 설정"""
        try:
            # ChromaDB 클라이언트 초기화
            self.client = chromadb.PersistentClient(path=self.cache_path)
            
            # 컬렉션 생성 또는 가져오기
            collection_name = "medical_knowledge"
            try:
                self.collection = self.client.get_collection(name=collection_name)
                print(f"기존 컬렉션 '{collection_name}' 로드됨")
            except Exception:
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": "의료 지식 데이터베이스"}
                )
                print(f"새 컬렉션 '{collection_name}' 생성됨")
                self._load_embedding_data()
                
        except Exception as e:
            print(f"ChromaDB 초기화 실패: {e}")
            self.client = None
            self.collection = None
    
    def _load_embedding_data(self):
        """임베딩 데이터 로드 및 ChromaDB에 저장"""
        if not self.collection:
            return
        
        try:
            # 기존 데이터 확인
            existing_count = self.collection.count()
            if existing_count > 0:
                print(f"이미 {existing_count}개의 문서가 로드되어 있습니다.")
                return
            
            # JSON 파일들 로드
            json_files = [f for f in os.listdir(self.embedding_data_path) if f.endswith('.json')]
            
            documents = []
            metadatas = []
            ids = []
            
            for json_file in json_files:
                file_path = os.path.join(self.embedding_data_path, json_file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    category = data.get('category', '기타')
                    for i, doc in enumerate(data.get('documents', [])):
                        doc_id = f"{json_file}_{i}"
                        documents.append(doc['content'])
                        metadatas.append({
                            'title': doc['title'],
                            'category': category,
                            'keywords': ', '.join(doc.get('keywords', [])),
                            'source_file': json_file
                        })
                        ids.append(doc_id)
                        
                except Exception as e:
                    print(f"파일 {json_file} 로드 실패: {e}")
                    continue
            
            if documents:
                # ChromaDB에 문서 추가
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"{len(documents)}개의 의료 지식 문서가 ChromaDB에 로드되었습니다.")
            else:
                print("로드할 문서가 없습니다.")
                
        except Exception as e:
            print(f"임베딩 데이터 로드 실패: {e}")
    
    def _search_relevant_documents(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """관련 문서 검색"""
        if not self.collection:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            documents = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    documents.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                        'distance': results['distances'][0][i] if results['distances'] and results['distances'][0] else 0
                    })
            
            return documents
            
        except Exception as e:
            print(f"문서 검색 실패: {e}")
            return []
    
    def generate_rag_enhanced_analysis(self, metrics: Dict[str, Any], member_id: str, analysis_type: str = "child") -> Dict[str, Any]:
        """RAG 강화된 혈당 분석 생성"""
        try:
            # 혈당 지표 기반 검색 쿼리 생성
            avg_glucose = metrics.get('average_glucose', 0)
            spike_count = metrics.get('spike_count', 0)
            health_index = metrics.get('health_index', 0)
            
            # 검색 쿼리 생성
            if avg_glucose <= 120:
                glucose_status = "정상 혈당"
            elif avg_glucose <= 140:
                glucose_status = "경계 혈당"
            else:
                glucose_status = "고혈당"
            
            query = f"{glucose_status} 관리 혈당 {avg_glucose}mg/dL 스파이크 {spike_count}회"
            
            # 관련 문서 검색
            relevant_docs = self._search_relevant_documents(query, n_results=3)
            
            # RAG 강화 프롬프트 생성
            rag_context = self._build_rag_context(relevant_docs)
            
            # 분석 타입에 따른 프롬프트 선택
            if analysis_type == "child":
                base_prompt = self._get_child_analysis_prompt()
            else:
                base_prompt = self._get_parent_analysis_prompt()
            
            # RAG 컨텍스트와 함께 프롬프트 구성
            enhanced_prompt = f"""
{base_prompt}

=== 의료 지식 컨텍스트 ===
{rag_context}

=== 혈당 데이터 ===
평균 혈당: {avg_glucose}mg/dL
최고 혈당: {metrics.get('max_glucose', 0)}mg/dL
최저 혈당: {metrics.get('min_glucose', 0)}mg/dL
혈당 스파이크: {spike_count}회
건강 지수: {health_index}

위의 의료 지식 컨텍스트를 참고하여 혈당 데이터를 분석하고 개인화된 조언을 제공해주세요.
"""
            
            # OpenAI API 호출
            response = call_openai_api(enhanced_prompt)
            
            # JSON 파싱 시도
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                result = {
                    "analysis": response,
                    "rag_metadata": {
                        "knowledge_sources_used": len(relevant_docs),
                        "search_query": query,
                        "relevant_docs": [doc['metadata']['title'] for doc in relevant_docs]
                    }
                }
            
            # RAG 메타데이터 추가
            if 'rag_metadata' not in result:
                result['rag_metadata'] = {
                    "knowledge_sources_used": len(relevant_docs),
                    "search_query": query,
                    "relevant_docs": [doc['metadata']['title'] for doc in relevant_docs]
                }
            
            return result
            
        except Exception as e:
            print(f"RAG 분석 생성 실패: {e}")
            # 기본 분석으로 fallback
            return {
                "error": f"RAG 분석 실패: {str(e)}",
                "fallback": True
            }
    
    def _build_rag_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        """검색된 문서들로부터 컨텍스트 구성"""
        if not relevant_docs:
            return "관련 의료 지식이 없습니다."
        
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            title = doc['metadata'].get('title', f'문서 {i}')
            content = doc['content']
            category = doc['metadata'].get('category', '기타')
            
            context_parts.append(f"""
[{i}] {title} ({category})
{content}
""")
        
        return "\n".join(context_parts)
    
    def _get_child_analysis_prompt(self) -> str:
        """아이용 분석 프롬프트"""
        return """
당신은 아이의 혈당 관리를 도와주는 친근한 AI 어시스턴트입니다.

다음 조건을 반드시 지켜주세요:
1. 반말 + 다정한 말투로만 작성
2. 아이가 이해하기 쉬운 언어 사용
3. 긍정적이고 격려하는 톤
4. 구체적이고 실행 가능한 조언 제공
5. JSON 형식으로 응답

응답 형식:
{
  "analysis": "혈당 분석 내용",
  "recommendations": ["조언1", "조언2", "조언3"],
  "encouragement": "격려 메시지"
}
"""
    
    def _get_parent_analysis_prompt(self) -> str:
        """부모용 분석 프롬프트"""
        return """
당신은 소아 당뇨 관리 전문가입니다.

다음 조건을 반드시 지켜주세요:
1. 전문적이지만 이해하기 쉬운 언어 사용
2. 구체적이고 실행 가능한 조언 제공
3. 의료적 정확성 확보
4. JSON 형식으로 응답

응답 형식:
{
  "analysis": "혈당 분석 내용",
  "recommendations": ["조언1", "조언2", "조언3"],
  "concerns": ["주의사항1", "주의사항2"],
  "next_steps": "다음 단계 제안"
}
"""


# 싱글톤 인스턴스
_chroma_rag_service = None


def get_chroma_rag_service() -> ChromaRAGService:
    """ChromaRAGService 싱글톤 인스턴스 반환"""
    global _chroma_rag_service
    if _chroma_rag_service is None:
        _chroma_rag_service = ChromaRAGService()
    return _chroma_rag_service