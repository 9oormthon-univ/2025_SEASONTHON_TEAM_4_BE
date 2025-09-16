import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# OpenAI 클라이언트 초기화 (버전 호환성 처리)
try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
except ImportError:
    # 구버전 openai 라이브러리 사용
    import openai
    openai.api_key = api_key
    client = None
except Exception as e:
    print(f"OpenAI 초기화 오류: {e}")
    client = None


def call_openai_api(prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
    """OpenAI API를 호출하여 응답을 반환합니다."""
    try:
        if client is not None:
            # 신버전 OpenAI 라이브러리
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        else:
            # 구버전 OpenAI 라이브러리
            import openai
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"Error calling OpenAI API: {str(e)}"
