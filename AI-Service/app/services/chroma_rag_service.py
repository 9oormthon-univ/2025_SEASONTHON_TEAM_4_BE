"""ChromaDB를 사용한 RAG 서비스"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from app.db.database import SessionLocal
from app.models.database_models import Glucose, Quest, Food, Exercise, Member
from app.core.ai import call_openai_api
from app.core.config import settings
from app.utils.glucose_utils import calculate_weekly_glucose_summary


class ChromaRAGService:
    """ChromaDB를 사용한 RAG 서비스"""
    
    def __init__(self, model_name: str = None):
        """
        ChromaDB 기반으로 초기화
        """
        self.model_name = model_name or settings.RAG_MODEL_NAME
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self.vector_dim = 768  # RoBERTa 기본 차원
        
        # ChromaDB 저장소 디렉토리
        self.chroma_persist_dir = os.path.join(settings.RAG_CACHE_DIR, "chroma_db")
        os.makedirs(self.chroma_persist_dir, exist_ok=True)
        
        # 초기화
        self._initialize_model()
        self._initialize_chroma()
        self._load_or_create_knowledge_base()
    
    def _initialize_model(self):
        """임베딩 모델 초기화"""
        try:
            print(f"임베딩 모델 로딩 중: {self.model_name}")
            self.embedding_model = SentenceTransformer(self.model_name)
            print("임베딩 모델 로딩 완료")
        except Exception as e:
            print(f"모델 로딩 실패, 기본 모델 사용: {e}")
            # fallback to multilingual model
            self.embedding_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
            self.vector_dim = 384  # multilingual model dimension
    
    def _initialize_chroma(self):
        """ChromaDB 클라이언트 초기화"""
        try:
            # ChromaDB 클라이언트 생성 (로컬 저장소 사용)
            self.chroma_client = chromadb.PersistentClient(
                path=self.chroma_persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 컬렉션 생성 또는 가져오기
            collection_name = "medical_knowledge"
            try:
                self.collection = self.chroma_client.get_collection(collection_name)
                print(f"기존 ChromaDB 컬렉션 로드: {collection_name}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"description": "의료 지식베이스"}
                )
                print(f"새 ChromaDB 컬렉션 생성: {collection_name}")
                
        except Exception as e:
            print(f"ChromaDB 초기화 실패: {e}")
            self.chroma_client = None
            self.collection = None
    
    def _load_or_create_knowledge_base(self):
        """의료 지식베이스 로드 또는 생성"""
        if not self.collection:
            print("ChromaDB 컬렉션이 없어 지식베이스 로드 불가")
            return
        
        # 컬렉션에 데이터가 있는지 확인
        try:
            count = self.collection.count()
            if count > 0:
                print(f"ChromaDB에 {count}개 문서가 이미 존재합니다.")
                return
        except:
            pass
        
        # embedding_data 폴더에서 데이터 로드 (설정된 배치 크기 사용)
        self._load_embedding_data(batch_size=settings.RAG_BATCH_SIZE)
    
    def _load_embedding_data(self, batch_size: int = 10):
        """embedding_data 폴더에서 데이터를 배치 단위로 로드하여 ChromaDB에 저장"""
        if not self.collection:
            return
        
        embedding_data_dir = "app/embedding_data"
        if not os.path.exists(embedding_data_dir):
            print("embedding_data 폴더가 없습니다.")
            return
        
        # 모든 JSON 파일에서 데이터 수집
        all_documents = []
        all_metadatas = []
        all_ids = []
        
        print("의료 지식 문서 로딩 중...")
        
        for filename in os.listdir(embedding_data_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(embedding_data_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        category = data.get('category', '기타')
                        docs = data.get('documents', [])
                        
                        print(f"  {filename}: {len(docs)}개 문서 발견")
                        
                        for i, doc in enumerate(docs):
                            doc_id = f"{category}_{doc.get('title', f'doc_{i}')}".replace(' ', '_')
                            content = doc.get('content', '')
                            keywords = doc.get('keywords', [])
                            
                            # 문서 ID, 내용, 메타데이터 추가
                            all_ids.append(doc_id)
                            all_documents.append(content)
                            all_metadatas.append({
                                "category": category,
                                "title": doc.get('title', ''),
                                "keywords": json.dumps(keywords, ensure_ascii=False),
                                "source_file": filename,
                                "created_at": datetime.now().isoformat()
                            })
                            
                except Exception as e:
                    print(f"  파일 로드 실패 {filename}: {e}")
        
        if not all_documents:
            print("로드할 문서가 없습니다.")
            return
        
        print(f"총 {len(all_documents)}개 문서를 {batch_size}개씩 배치 처리합니다...")
        
        # 배치 단위로 ChromaDB에 추가
        total_batches = (len(all_documents) + batch_size - 1) // batch_size
        success_count = 0
        
        for batch_idx in range(0, len(all_documents), batch_size):
            batch_end = min(batch_idx + batch_size, len(all_documents))
            batch_documents = all_documents[batch_idx:batch_end]
            batch_metadatas = all_metadatas[batch_idx:batch_end]
            batch_ids = all_ids[batch_idx:batch_end]
            
            current_batch = (batch_idx // batch_size) + 1
            
            try:
                print(f"  배치 {current_batch}/{total_batches} 처리 중... ({len(batch_documents)}개 문서)")
                
                # ChromaDB에 배치 추가
                self.collection.add(
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                
                success_count += len(batch_documents)
                print(f"  배치 {current_batch} 완료: {len(batch_documents)}개 문서 추가")
                
                # 메모리 정리를 위한 짧은 대기
                import time
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  배치 {current_batch} 실패: {e}")
                # 개별 문서로 재시도
                for i, (doc, meta, doc_id) in enumerate(zip(batch_documents, batch_metadatas, batch_ids)):
                    try:
                        self.collection.add(
                            documents=[doc],
                            metadatas=[meta],
                            ids=[doc_id]
                        )
                        success_count += 1
                        print(f"    개별 문서 {i+1} 추가 성공")
                    except Exception as individual_error:
                        print(f"    개별 문서 {i+1} 추가 실패: {individual_error}")
        
        print(f"ChromaDB 임베딩 완료: {success_count}/{len(all_documents)}개 문서 성공적으로 추가")
        
        # 최종 통계 출력
        try:
            final_count = self.collection.count()
            print(f"ChromaDB 총 문서 수: {final_count}개")
        except Exception as e:
            print(f"최종 통계 조회 실패: {e}")
    
    def search_relevant_knowledge(self, query: str, top_k: int = 3) -> List[Dict]:
        """쿼리에 대한 관련 의료 지식 검색"""
        if not self.collection:
            return []
        
        try:
            # ChromaDB에서 유사도 검색
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            knowledge_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    # ChromaDB의 distance는 작을수록 유사하므로 similarity로 변환
                    similarity_score = 1.0 / (1.0 + distance)
                    
                    knowledge_results.append({
                        'key': results['ids'][0][i] if results['ids'] and results['ids'][0] else f"doc_{i}",
                        'content': doc,
                        'category': metadata.get('category', '기타'),
                        'title': metadata.get('title', ''),
                        'keywords': json.loads(metadata.get('keywords', '[]')),
                        'similarity_score': similarity_score,
                        'source_file': metadata.get('source_file', ''),
                        'created_at': metadata.get('created_at', '')
                    })
            
            return knowledge_results
            
        except Exception as e:
            print(f"ChromaDB 검색 실패: {e}")
            return []
    
    def search_user_patterns(self, member_id: int, glucose_metrics: Dict) -> List[Dict]:
        """사용자의 혈당 패턴 검색 (기존과 동일)"""
        try:
            db = SessionLocal()
            
            # 최근 30일간의 혈당 데이터 조회
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            glucose_data = db.query(Glucose).filter(
                Glucose.member_id == member_id,
                Glucose.date >= start_date,
                Glucose.date <= end_date
            ).order_by(Glucose.date.desc()).all()
            
            if not glucose_data:
                return []
            
            # 일별 혈당 패턴 분석
            daily_patterns = {}
            for reading in glucose_data:
                date_str = str(reading.date)
                if date_str not in daily_patterns:
                    daily_patterns[date_str] = []
                daily_patterns[date_str].append(reading.glucose_mg_dl)
            
            # 패턴 분석
            patterns = []
            for date_str, readings in daily_patterns.items():
                if len(readings) < 2:
                    continue
                
                avg_glucose = sum(readings) / len(readings)
                max_glucose = max(readings)
                min_glucose = min(readings)
                variability = max_glucose - min_glucose
                
                # 성공 패턴 분류
                if 70 <= avg_glucose <= 140 and variability < 50:
                    pattern_type = "excellent"
                elif 70 <= avg_glucose <= 180 and variability < 80:
                    pattern_type = "good"
                elif avg_glucose > 180:
                    pattern_type = "high"
                else:
                    pattern_type = "unstable"
                
                patterns.append({
                    'date': date_str,
                    'avg_glucose': avg_glucose,
                    'max_glucose': max_glucose,
                    'min_glucose': min_glucose,
                    'variability': variability,
                    'pattern_type': pattern_type,
                    'readings_count': len(readings)
                })
            
            return sorted(patterns, key=lambda x: x['date'], reverse=True)[:5]
            
        except Exception as e:
            print(f"사용자 패턴 검색 실패: {e}")
            return []
        finally:
            db.close()
    
    def search_similar_cases(self, glucose_metrics: Dict, top_k: int = 3) -> List[Dict]:
        """유사한 혈당 패턴을 가진 사례 검색 (기존과 동일)"""
        try:
            db = SessionLocal()
            
            # 최근 30일간의 모든 사용자 혈당 데이터 조회
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            all_glucose_data = db.query(Glucose).filter(
                Glucose.date >= start_date,
                Glucose.date <= end_date
            ).all()
            
            if not all_glucose_data:
                return []
            
            # 사용자별로 그룹화
            user_data = {}
            for reading in all_glucose_data:
                if reading.member_id not in user_data:
                    user_data[reading.member_id] = []
                user_data[reading.member_id].append(reading.glucose_mg_dl)
            
            # 유사한 패턴 찾기
            similar_cases = []
            target_avg = glucose_metrics.get('average_glucose', 0)
            target_max = glucose_metrics.get('max_glucose', 0)
            target_min = glucose_metrics.get('min_glucose', 0)
            target_spikes = glucose_metrics.get('spike_count', 0)
            
            for member_id, readings in user_data.items():
                if len(readings) < 5:  # 충분한 데이터가 있는 경우만
                    continue
                
                avg_glucose = sum(readings) / len(readings)
                max_glucose = max(readings)
                min_glucose = min(readings)
                spikes = sum(1 for i in range(1, len(readings)) 
                           if readings[i] - readings[i-1] >= 30)
                
                # 유사도 계산 (다차원 유클리드 거리)
                avg_diff = abs(avg_glucose - target_avg)
                max_diff = abs(max_glucose - target_max)
                min_diff = abs(min_glucose - target_min)
                spike_diff = abs(spikes - target_spikes)
                
                # 정규화된 유사도 점수
                similarity_score = 1.0 / (1.0 + (avg_diff/50) + (max_diff/100) + (min_diff/50) + (spike_diff/2))
                
                if similarity_score > 0.6:  # 유사도 임계값
                    similar_cases.append({
                        "member_id": member_id,
                        "average_glucose": avg_glucose,
                        "max_glucose": max_glucose,
                        "min_glucose": min_glucose,
                        "spike_count": spikes,
                        "similarity_score": similarity_score,
                        "readings_count": len(readings)
                    })
            
            return sorted(similar_cases, key=lambda x: x['similarity_score'], reverse=True)[:top_k]
            
        except Exception as e:
            print(f"유사 사례 검색 실패: {e}")
            return []
        finally:
            db.close()
    
    def generate_rag_enhanced_analysis(self, glucose_metrics: Dict, member_id: int, 
                                     analysis_type: str = "child") -> Dict[str, Any]:
        """RAG를 활용한 향상된 혈당 분석"""
        
        # 1. 혈당 데이터 기반 쿼리 생성
        query = self._generate_glucose_query(glucose_metrics)
        
        # 2. 관련 의료 지식 검색
        relevant_knowledge = self.search_relevant_knowledge(query, top_k=3)
        
        # 3. 사용자 패턴 검색
        user_patterns = self.search_user_patterns(member_id, glucose_metrics)
        
        # 4. 유사 사례 검색
        similar_cases = self.search_similar_cases(glucose_metrics, top_k=2)
        
        # 5. RAG 컨텍스트 구축
        rag_context = self._build_enhanced_context(
            relevant_knowledge, user_patterns, similar_cases, glucose_metrics
        )
        
        # 6. 기존 프롬프트와 RAG 컨텍스트 결합
        base_prompt = self._load_prompt(analysis_type)
        
        enhanced_prompt = f"""
{base_prompt}

## RAG 기반 의료 지식 컨텍스트 (ChromaDB)
{rag_context}

## 현재 혈당 데이터
{json.dumps(glucose_metrics, ensure_ascii=False, indent=2)}

위의 의료 지식, 사용자 패턴, 유사 사례를 참고하여 더 정확하고 개인화된 분석을 제공해주세요.

CRITICAL: 반드시 다음 JSON 형식으로만 응답하세요!
```json
{{
  "result": {{
    "혈당 스파이크 분석": "혈당 급상승 패턴과 안정성 평가입니다. 잘하셨어요! 또는 노력이 필요해요!",
    "평균 혈당 분석": "일일 평균 혈당 수치와 의학적 평가입니다. 잘하셨어요! 또는 노력이 필요해요!",
    "최고 혈당 분석": "최고 혈당 수치와 관리 상태 평가입니다. 잘하셨어요! 또는 노력이 필요해요!",
    "최저 혈당 분석": "최저 혈당 수치와 저혈당 위험성 평가입니다. 잘하셨어요! 또는 노력이 필요해요!"
  }}
}}
```

절대로 다른 형식으로 응답하지 마세요! 반드시 위의 JSON 형식으로만 응답하세요!
"""
        
        try:
            # 분석 타입에 따른 시스템 프롬프트 설정
            system_prompt = ""
            if analysis_type == "analyze":
                system_prompt = """당신은 당뇨 관리 전문 비서입니다. 

중요한 지침:
1. 반드시 존댓말로만 응답하세요 ('~입니다', '~됩니다', '~하시기 바랍니다', '~권장드립니다' 등)
2. 반말('~해', '~야', '~지', '~어', '~자') 절대 사용 금지
3. 전문적이고 분석적인 톤으로 작성
4. 의학적 근거와 분석적 접근을 바탕으로 한 조언 제공
5. 부모님을 대상으로 한 신뢰할 수 있는 전문 비서의 역할
6. 아이에 대한 언급 시 "자녀분", "아이", "어린이" 등으로 표현
7. 부모님의 관점에서 자녀의 혈당 관리 상태를 분석하고 조언

CRITICAL: 반드시 다음 JSON 형식으로만 응답하세요!
```json
{{
  "result": {{
    "혈당 스파이크 분석": "혈당 급상승 패턴과 안정성 평가입니다. 잘하셨어요! 또는 노력이 필요해요!",
    "평균 혈당 분석": "일일 평균 혈당 수치와 의학적 평가입니다. 잘하셨어요! 또는 노력이 필요해요!",
    "최고 혈당 분석": "최고 혈당 수치와 관리 상태 평가입니다. 잘하셨어요! 또는 노력이 필요해요!",
    "최저 혈당 분석": "최저 혈당 수치와 저혈당 위험성 평가입니다. 잘하셨어요! 또는 노력이 필요해요!"
  }}
}}
```

절대로 다른 형식으로 응답하지 마세요! 반드시 위의 JSON 형식으로만 응답하세요!"""
            
            print(f"RAG 분석 시작 - 분석 타입: {analysis_type}")
            response = call_openai_api(enhanced_prompt, system_prompt)
            print(f"RAG 분석 응답: {response[:200]}...")
            
            # JSON 파싱 개선
            try:
                # ```json으로 감싸진 경우 처리
                if "```json" in response:
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    if json_end != -1:
                        json_str = response[json_start:json_end].strip()
                        result = json.loads(json_str)
                    else:
                        result = {"analysis": response}
                # 일반 JSON인 경우
                elif response.strip().startswith('{'):
                    result = json.loads(response)
                else:
                    result = {"analysis": response}
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류: {e}")
                print(f"응답 내용: {response}")
                result = {"analysis": response}
            
            # RAG 메타데이터 추가
            result["rag_metadata"] = {
                "knowledge_sources": len(relevant_knowledge),
                "user_patterns_found": len(user_patterns),
                "similar_cases_found": len(similar_cases),
                "query_used": query,
                "database": "ChromaDB"
            }
            
            return result
        except Exception as e:
            print(f"RAG 분석 실패: {e}")
            return {"error": f"RAG 분석 생성 실패: {str(e)}"}
    
    def _generate_glucose_query(self, glucose_metrics: Dict) -> str:
        """혈당 데이터 기반 검색 쿼리 생성"""
        avg_glucose = glucose_metrics.get('average_glucose', 0)
        max_glucose = glucose_metrics.get('max_glucose', 0)
        spike_count = glucose_metrics.get('spike_count', 0)
        
        query_parts = []
        
        if avg_glucose > 180:
            query_parts.append("고혈당 관리 방법")
        elif avg_glucose < 70:
            query_parts.append("저혈당 관리 방법")
        else:
            query_parts.append("혈당 안정화 방법")
        
        if spike_count > 2:
            query_parts.append("혈당 급상승 방지")
        
        if max_glucose > 200:
            query_parts.append("심각한 고혈당 관리")
        
        return " ".join(query_parts) if query_parts else "당뇨 관리 기본"
    
    def _build_enhanced_context(self, knowledge: List[Dict], user_patterns: List[Dict], 
                               similar_cases: List[Dict], glucose_metrics: Dict) -> str:
        """향상된 RAG 컨텍스트 구축"""
        context = "### 의료 지식 기반 분석 (ChromaDB)\n"
        
        for item in knowledge:
            context += f"- {item['category']}: {item['title']}\n"
            context += f"  {item['content']} (관련도: {item['similarity_score']:.2f})\n"
            context += f"  키워드: {', '.join(item['keywords'])}\n\n"
        
        if user_patterns:
            context += "\n### 사용자 개인 패턴 분석\n"
            excellent_days = [p for p in user_patterns if p['pattern_type'] == 'excellent']
            if excellent_days:
                context += f"- 최근 우수한 혈당 관리: {len(excellent_days)}일\n"
                for pattern in excellent_days[:2]:
                    context += f"  * {pattern['date']}: 평균 {pattern['avg_glucose']:.1f}mg/dL (안정적)\n"
        
        if similar_cases:
            context += "\n### 유사한 사례 참고\n"
            for case in similar_cases:
                context += f"- 평균 {case['average_glucose']:.1f}mg/dL, 스파이크 {case['spike_count']}회 (유사도: {case['similarity_score']:.2f})\n"
        
        return context
    
    def _load_prompt(self, analysis_type: str) -> str:
        """프롬프트 파일 로드"""
        prompt_files = {
            "child": "app/prompts/child_report_prompt.txt",
            "parent": "app/prompts/parent_report_prompt.txt",
            "analyze": "app/prompts/parent_analyze_prompt.txt"
        }
        
        prompt_file = prompt_files.get(analysis_type, prompt_files["child"])
        
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"프롬프트 로드 실패: {e}")
            return "혈당 데이터를 분석하여 격려하는 메시지를 생성해주세요."
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """ChromaDB 컬렉션 통계 반환"""
        if not self.collection:
            return {"error": "ChromaDB 컬렉션이 없습니다."}
        
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection.name,
                "persist_directory": self.chroma_persist_dir,
                "model_name": self.model_name,
                "vector_dimension": self.vector_dim
            }
        except Exception as e:
            return {"error": f"통계 조회 실패: {str(e)}"}


# RAG 서비스 인스턴스 (지연 로딩)
chroma_rag_service = None

def get_chroma_rag_service():
    """ChromaDB RAG 서비스 인스턴스 반환 (지연 로딩)"""
    global chroma_rag_service
    if chroma_rag_service is None:
        chroma_rag_service = ChromaRAGService()
    return chroma_rag_service
