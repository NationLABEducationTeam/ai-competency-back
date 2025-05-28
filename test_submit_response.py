import requests
import json

# API 엔드포인트
BASE_URL = "http://3.35.230.242:8080/api/v1"
SURVEY_ID = "a6b045fe-0d2c-40a3-bb51-55bcd572b854"

# 테스트 데이터
test_response = {
    "respondent_name": "민테익",
    "respondent_email": "edu@aination.kr",
    "respondent_age": 99,
    "respondent_organization": "테스트대학교",
    "respondent_education": "석사재학",
    "respondent_major": "미래기술학과",
    "answers": [
        {"question_id": "q6", "score": 3},
        {"question_id": "q7", "score": 4},
        {"question_id": "q8", "score": 2},
        {"question_id": "q9", "score": 3},
        {"question_id": "q10", "score": 4},
        {"question_id": "q11", "score": 4},
        {"question_id": "q12", "score": 1},
        {"question_id": "q13", "score": 2},
        {"question_id": "q14", "score": 3},
        {"question_id": "q15", "score": 2},
        {"question_id": "q16", "score": 5},
        {"question_id": "q17", "score": 4},
        {"question_id": "q18", "score": 3},
        {"question_id": "q19", "score": 2},
        {"question_id": "q20", "score": 4},
        {"question_id": "q21", "score": 5},
        {"question_id": "q22", "score": 1},
        {"question_id": "q23", "score": 2},
        {"question_id": "q24", "score": 3},
        {"question_id": "q25", "score": 4},
        {"question_id": "q26", "score": 5},
        {"question_id": "q27", "score": 4},
        {"question_id": "q28", "score": 3},
        {"question_id": "q29", "score": 2},
        {"question_id": "q30", "score": 1},
        {"question_id": "q31", "score": 5},
        {"question_id": "q32", "score": 4},
        {"question_id": "q33", "score": 5},
        {"question_id": "q34", "score": 4},
        {"question_id": "q35", "score": 1},
        {"question_id": "q36", "score": 1},
        {"question_id": "q37", "score": 1},
        {"question_id": "q38", "score": 1},
        {"question_id": "q39", "score": 1}
    ]
}

def test_submit_response():
    """설문 응답 제출 테스트"""
    url = f"{BASE_URL}/surveys/{SURVEY_ID}/responses"
    
    try:
        response = requests.post(url, json=test_response)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_submit_response() 