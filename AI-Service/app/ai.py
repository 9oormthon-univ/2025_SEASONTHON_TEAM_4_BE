from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# OpenAI 클라이언트 초기화 (httpx 호환성 문제 해결)
try:
    client = OpenAI(api_key=api_key)
except TypeError:
    # httpx 버전 호환성 문제로 인한 fallback
    import httpx
    client = OpenAI(
        api_key=api_key,
        http_client=httpx.Client()
    )


def call_openai_api(prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
    """OpenAI API를 호출하여 응답을 반환합니다."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling OpenAI API: {str(e)}"
