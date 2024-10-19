from fastapi import FastAPI, HTTPException
import subprocess
import config
from pydantic import BaseModel

app = FastAPI()

# 요청 본문 모델 정의
class TextInput(BaseModel):
  text: str

# 맞춤법 검사 함수
def run_spell_check(text: str):
  if not text:
    raise HTTPException(status_code=400, detail="입력된 텍스트가 비어있습니다.")
    
  try:
    # CLI 대화형 입력을 자동화하기 위해 Popen 사용
    process = subprocess.Popen(
      ["node", config.HAN_SPELL_PATH],
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True,
      encoding="utf-8"
    )

    # CLI에 텍스트 입력
    stdout, stderr = process.communicate(input=text)

    # 디버깅 정보 출력
    if config.DEBUG_MODE:
      print(f"Command: {process.args}")
      print(f"Return code: {process.returncode}")
      print(f"corrected_text: {stdout}")
      print(f"spelling_errors: {stderr}")

    # 맞춤법 오류 설명 없이 교정된 텍스트만 추출
    corrected_lines = []
    for line in stderr.splitlines():
      if "->" in line:  # '->'가 포함된 줄만 필터링
        corrected_lines.append(line.strip())

    # stdout과 stderr를 보기 좋게 정리하여 반환
    return {
      "original_text": text.strip(),  # 입력한 원문 텍스트
      "corrected_text": stdout.strip(),  # 맞춤법 교정된 텍스트
      "spelling_corrections": "\n".join(corrected_lines)  # 맞춤법 교정만 반환
    }

  except Exception as e:
    raise HTTPException(status_code=500, detail=f"맞춤법 검사 실행 중 오류가 발생했습니다: {str(e)}")

# POST 요청을 처리하는 부분
@app.post("/check_spelling")
def check_spelling(input: TextInput):
  try:
    # 맞춤법 검사 함수 호출
    result = run_spell_check(input.text)
    return result
  except HTTPException as http_exc:
    raise http_exc
  except Exception as e:
    # 기타 오류 발생 시 예외 메시지를 반환
    raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

# FastAPI 서버 실행
if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=8000)
