import json


def load_json_data(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": f"{file_path} 파일이 존재하지 않습니다."}
    except json.JSONDecodeError:
        return {"error": f"{file_path} 파일의 JSON 형식이 올바르지 않습니다."}


def load_text(file_path: str, default_text: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return default_text


