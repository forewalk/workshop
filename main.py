from fastapi import FastAPI, Request, Form, HTTPException, Depends, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional, Dict
import json
from datetime import datetime, timedelta
import secrets
from starlette.middleware.sessions import SessionMiddleware
import os
import shutil
from urllib.parse import quote

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="cruxdata_workshop_secret_key")

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 비밀번호 설정
PASSWORD = "CruxData1!"
ADMIN_PASSWORD = "nadaimma"

# 사용자 데이터 파일 경로
USERS_FILE = "data/users.json"
MILEAGE_FILE = "data/mileage.json"
MBTI_GAME_FILE = "data/mbti_game.json"
PHOTO_GAME_FILE = "data/photo_game.json"

# 사진 저장 경로
PHOTO_UPLOAD_DIR = "static/photos"

# 사진 게임 설정
GRID_SIZE = 10  # 10x10 그리드
REVEAL_COST = 100  # 셀 하나 공개 비용
GUESS_COST = 300  # 추측 비용
CORRECT_REWARD = 1000  # 정답 보상

def load_json_file(file_path: str) -> Dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json_file(file_path: str, data: Dict):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_users(): return load_json_file(USERS_FILE)
def save_users(users): save_json_file(USERS_FILE, users)
def load_mileage(): return load_json_file(MILEAGE_FILE)
def save_mileage(mileage): save_json_file(MILEAGE_FILE, mileage)
def load_mbti_game(): return load_json_file(MBTI_GAME_FILE)
def save_mbti_game(data): save_json_file(MBTI_GAME_FILE, data)
def load_photo_game(): return load_json_file(PHOTO_GAME_FILE)
def save_photo_game(data): save_json_file(PHOTO_GAME_FILE, data)

# 데이터
workshop_data = {
    "location": "경기 안산시 단원구 대부남동 3-181",
    "cars": {
        "김민재": ["박정우", "김경수", "홍석영", "+ 장보기"],
        "이한희": ["김민수", "박상현", "최지호"],
        "배예슬": ["전성욱", "김해니", "김서경", "김명진"],
        "김장훈": ["오원우", "김경인", "한예지", "+ 장보기"],
        "개인차량": ["정승환", "김정성", "김민수"]
    },
    "teams": {
        "김민재팀": ["김민재", "김명진", "한예지", "홍석영", "김민수(개발)", "전성욱"],
        "이한희팀": ["이한희", "정승환", "배예슬", "김서경", "김경수", "박상현", "김정성"],
        "김경인팀": ["김경인", "박정우", "오원우", "최지호", "김해니", "김민수(영업)"],
        "진행": "김장훈"
    },
    "schedule": {
        "11:00": "출발",
        "14:00": "숙소도착\n준비 및 세미나 진행 시작(산출물: 사업 진행상황)",
        "14:30": "단체게임 대표 정하기 & 단체게임 시작\n\n휴지띄우기(2~3명 참가, 점수뺏기 1등이 참가자 중 한명 뺏기)\n제기차기(1명, 점수획득 1등)\n몸으로 말해요(1명이 퀴즈 나머지 팀원들이 맞추기, 점수획득 1등)\n종이비행기 날리기(전체게임, 등수별 점수획득)\n주사위 뒤집기(2명, 점수뺏기 1등팀이 각자 참가자 중 한명 뺏기)",
        "15:30": "돼지씨름(전체게임)",
        "16:00": "여자팀 배트민턴(김민재팀 남자한명 포함) || 남자팀 족구(우천시, 탁구)\n개별활동 안됨. 응원 점수 있음",
        "17:00": "다른팀 팀장 불러서 손밀치기 게임(5명 참가, 뒤에 수영장물) 이기면, 해당 팀에서 점수 뺏기\n상식퀴즈, 각팀에서 한명씩 쪼그려 앉아서 게임 시작(5명 참가, 뒤에 수영장물), 서바이벌(점수획득 1등팀)",
        "18:00": "눈가리고 물바가지 뒤로 넘겨서 많이 모으기(팀 전체 점수부여)",
        "19:00": "고기파티 시작, 점수합산 결과 발표",
        "20:00": "고기 먹으면서 블라인드 옥션 시작"
    }
}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    user = request.session.get("user")
    mileage_data = load_mileage()
    mileage = mileage_data.get(user, 0) if user else 0
    
    # 팀별 마일리지 평균 계산
    team_averages = {}
    for team_name, members in workshop_data["teams"].items():
        if team_name == "진행":  # 진행자는 제외
            continue
        
        total_mileage = 0
        member_count = 0
        
        for member in members:
            # 사용자 이름 매핑 (예: 김정성(영업팀) -> 김정성, 김민수(영업팀) -> 김민수(영업))
            mapped_member = member
            if member == "김정성(영업팀)":
                mapped_member = "김정성"
            elif member == "김민수(영업팀)":
                mapped_member = "김민수(영업)"
            
            if mapped_member in mileage_data:
                total_mileage += mileage_data[mapped_member]
                member_count += 1
        
        if member_count > 0:
            team_averages[team_name] = round(total_mileage / member_count, 1)
        else:
            team_averages[team_name] = 0
    
    # 에러 메시지 가져오기 및 세션에서 제거
    error_message = request.session.pop("error_message", None)
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "location": workshop_data["location"],
            "cars": workshop_data["cars"],
            "teams": workshop_data["teams"],
            "team_averages": team_averages,
            "user": user,
            "mileage": mileage,
            "error_message": error_message
        }
    )

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    users = load_users()
    if username in users and users[username]["password"] == password:
        request.session["user"] = username
        
        # 비밀번호 변경 필요 여부 확인
        if not users[username]["password_changed"]:
            return {"success": True, "redirect": "/change-password"}
            
        return {"success": True, "message": "로그인 성공"}
    raise HTTPException(status_code=401, detail="잘못된 사용자명 또는 비밀번호입니다.")

@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/")

@app.post("/add-mileage")
async def add_mileage(request: Request, username: str = Form(...), points: int = Form(...)):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    mileage = load_mileage()
    if username not in mileage:
        mileage[username] = 0
    mileage[username] += points
    save_mileage(mileage)
    return {"success": True, "new_mileage": mileage[username]}

@app.post("/use-mileage")
async def use_mileage(request: Request, points: int = Form(...)):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    mileage = load_mileage()
    if user not in mileage or mileage[user] < points:
        raise HTTPException(status_code=400, detail="마일리지가 부족합니다.")
    
    mileage[user] -= points
    save_mileage(mileage)
    return {"success": True, "new_mileage": mileage[user]}

@app.post("/verify-password")
async def verify_password(password: str = Form(...)):
    if password == PASSWORD:
        return {"success": True}
    raise HTTPException(status_code=401, detail="잘못된 비밀번호입니다.")

@app.get("/change-password")
async def change_password_page(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/")
    
    return templates.TemplateResponse(
        "change_password.html",
        {"request": request, "user": user}
    )

@app.post("/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...)
):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    users = load_users()
    if users[user]["password"] != current_password:
        raise HTTPException(status_code=400, detail="현재 비밀번호가 일치하지 않습니다.")
    
    users[user]["password"] = new_password
    users[user]["password_changed"] = True
    save_users(users)
    return {"success": True, "message": "비밀번호가 변경되었습니다."}

@app.get("/mbti-game")
async def get_mbti_game(request: Request):
    user = request.session.get("user")
    if not user:
        response = RedirectResponse(url="/")
        response.status_code = 302
        request.session["error_message"] = "로그인 후 게임에 참여해 주세요."
        return response
    
    # 비밀번호 변경 여부 확인
    users = load_users()
    if not users[user]["password_changed"]:
        response = RedirectResponse(url="/change-password")
        response.status_code = 302
        return response
    
    mbti_game = load_mbti_game()
    mileage = load_mileage()
    
    return templates.TemplateResponse(
        "mbti_game.html",
        {
            "request": request,
            "user": user,
            "users": users,
            "mbti_data": mbti_game.get("mbti_data", {}),
            "correct_guesses": mbti_game.get("correct_guesses", {}),
            "wrong_guesses": mbti_game.get("wrong_guesses", {}),
            "mileage": mileage.get(user, 0),
            "guess_cost": 100
        }
    )

@app.post("/submit-mbti")
async def submit_mbti(request: Request, mbti: str = Form(...)):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    mbti = mbti.upper()
    if not is_valid_mbti(mbti):
        raise HTTPException(status_code=400, detail="MBTI 형태로 입력해주세요. (예: ENFP)")
    
    mbti_game = load_mbti_game()
    if user not in mbti_game["mbti_data"]:
        # 처음 입력하는 경우에만 마일리지 지급
        mileage = load_mileage()
        mileage[user] = mileage.get(user, 0) + 100
        save_mileage(mileage)
    
    mbti_game["mbti_data"][user] = mbti
    save_mbti_game(mbti_game)
    
    return {"success": True, "message": "MBTI가 등록되었습니다. 100 포인트가 적립되었습니다."}

@app.post("/guess-mbti")
async def guess_mbti(
    request: Request,
    target_user: str = Form(...),
    guess: str = Form(...)
):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    guess = guess.upper()
    if not is_valid_mbti(guess):
        raise HTTPException(status_code=400, detail="MBTI 형태로 입력해주세요. (예: ENFP)")
    
    mbti_game = load_mbti_game()
    mileage = load_mileage()
    
    # 마일리지 차감 체크
    if mileage.get(user, 0) < 100:
        raise HTTPException(status_code=400, detail="마일리지가 모두 소진되었습니다.")
    
    # 이미 맞춘 경우 체크
    correct_guesses = mbti_game.get("correct_guesses", {})
    if target_user in correct_guesses.get(user, []):
        raise HTTPException(status_code=400, detail="이미 맞추신 사용자입니다.")
    
    # 대상 사용자의 MBTI 입력 여부 체크
    if target_user not in mbti_game.get("mbti_data", {}):
        raise HTTPException(status_code=400, detail="해당 사용자가 아직 MBTI를 입력하지 않았습니다.")
    
    # 마일리지 차감
    mileage[user] = mileage.get(user, 0) - 100
    
    # 정답 체크
    if guess == mbti_game["mbti_data"][target_user]:
        # 맞춘 경우 마일리지 적립 및 기록
        mileage[user] = mileage.get(user, 0) + 200  # 차감된 100 + 보상 100
        if user not in correct_guesses:
            correct_guesses[user] = []
        correct_guesses[user].append(target_user)
        mbti_game["correct_guesses"] = correct_guesses
        save_mbti_game(mbti_game)
        save_mileage(mileage)
        return {"success": True, "message": f"정답입니다! 100 포인트가 적립되었습니다. (현재 마일리지: {mileage[user]} 포인트)"}
    
    # 틀린 경우
    save_mileage(mileage)
    return {"success": False, "message": f"틀렸습니다. 100 포인트가 차감되었습니다. (현재 마일리지: {mileage[user]} 포인트)"}

def is_valid_mbti(mbti: str) -> bool:
    valid_types = {
        'E': 'I', 'I': 'E',
        'S': 'N', 'N': 'S',
        'T': 'F', 'F': 'T',
        'J': 'P', 'P': 'J'
    }
    
    if len(mbti) != 4:
        return False
    
    return (
        mbti[0] in 'EI' and
        mbti[1] in 'SN' and
        mbti[2] in 'TF' and
        mbti[3] in 'JP'
    )

@app.get("/teams")
async def get_teams(request: Request):
    mileage_data = load_mileage()
    
    # 팀별 마일리지 평균 계산
    team_averages = {}
    team_totals = {}
    for team_name, members in workshop_data["teams"].items():
        if team_name == "진행":  # 진행자는 제외
            continue
        
        total_mileage = 0
        member_count = 0
        
        for member in members:
            if member in mileage_data:
                total_mileage += mileage_data[member]
                member_count += 1
        
        if member_count > 0:
            team_averages[team_name] = round(total_mileage / member_count, 1)
            team_totals[team_name] = total_mileage
        else:
            team_averages[team_name] = 0
            team_totals[team_name] = 0
    
    return templates.TemplateResponse(
        "teams.html",
        {
            "request": request, 
            "teams": workshop_data["teams"],
            "team_averages": team_averages,
            "team_totals": team_totals,
            "mileage_data": mileage_data
        }
    )

@app.get("/schedule")
async def get_schedule(request: Request):
    return templates.TemplateResponse(
        "schedule.html",
        {"request": request, "schedule": workshop_data["schedule"]}
    )

@app.get("/photo-game")
async def get_photo_game(request: Request):
    user = request.session.get("user")
    if not user:
        response = RedirectResponse(url="/")
        response.status_code = 302
        request.session["error_message"] = "로그인 후 게임에 참여해 주세요."
        return response
    
    # 비밀번호 변경 여부 확인
    users = load_users()
    if not users[user]["password_changed"]:
        response = RedirectResponse(url="/change-password")
        response.status_code = 302
        return response
    
    photo_game = load_photo_game()
    mileage = load_mileage()
    
    # URL 인코딩된 사진 경로로 변환
    photos = {}
    for user_name, photo_path in photo_game.get("photos", {}).items():
        filename = os.path.basename(photo_path)
        encoded_filename = quote(filename)
        photos[user_name] = f"/static/photos/{encoded_filename}"
    
    return templates.TemplateResponse(
        "photo_game.html",
        {
            "request": request,
            "user": user,
            "photos": photos,
            "correct_guesses": photo_game.get("correct_guesses", {}),
            "wrong_guesses": photo_game.get("wrong_guesses", {}),
            "revealed_cells": photo_game.get("revealed_cells", {}),
            "mileage": mileage.get(user, 0),
            "guess_cost": GUESS_COST,
            "correct_reward": CORRECT_REWARD,
            "users": users
        }
    )

@app.post("/upload-photo")
async def upload_photo(request: Request, photo: UploadFile = File(...)):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    # 파일 확장자 검사
    ext = os.path.splitext(photo.filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png']:
        raise HTTPException(status_code=400, detail="JPG 또는 PNG 파일만 업로드 가능합니다.")
    
    # 업로드 디렉토리 생성
    os.makedirs(PHOTO_UPLOAD_DIR, exist_ok=True)
    
    # 파일 저장
    file_path = os.path.join(PHOTO_UPLOAD_DIR, f"{user}{ext}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)
    
    # 게임 데이터 업데이트
    photo_game = load_photo_game()
    photo_game["photos"][user] = f"/static/photos/{user}{ext}"
    save_photo_game(photo_game)
    
    return {"success": True, "message": "사진이 업로드되었습니다."}

@app.post("/reveal-cell")
async def reveal_cell(
    request: Request,
    target_user: str = Form(...),
    x: int = Form(...),
    y: int = Form(...)
):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    # 좌표 유효성 검사
    if not (0 <= x < 5 and 0 <= y < 5):
        raise HTTPException(status_code=400, detail="잘못된 좌표입니다.")
    
    photo_game = load_photo_game()
    mileage = load_mileage()
    
    # 대상 사용자의 사진 존재 여부 확인
    if target_user not in photo_game.get("photos", {}):
        raise HTTPException(status_code=400, detail="해당 사용자의 사진이 없습니다.")
    
    # 이미 누군가가 맞춘 사진인지 확인
    correct_guesses = photo_game.get("correct_guesses", {})
    if target_user in correct_guesses and len(correct_guesses[target_user]) > 0:
        raise HTTPException(status_code=400, detail="이미 다른 사람이 맞춘 사진입니다.")
    
    # 마일리지 확인
    if mileage.get(user, 0) < REVEAL_COST:
        raise HTTPException(status_code=400, detail="마일리지가 부족합니다.")
    
    # 셀 공개 처리
    cell_key = f"{target_user}:{x}:{y}"
    revealed_cells = photo_game.get("revealed_cells", {})
    if cell_key not in revealed_cells:
        revealed_cells[cell_key] = True
        photo_game["revealed_cells"] = revealed_cells
        save_photo_game(photo_game)
        
        # 마일리지 차감
        mileage[user] = mileage.get(user, 0) - REVEAL_COST
        save_mileage(mileage)
    
    return {
        "success": True,
        "message": f"셀이 공개되었습니다. ({REVEAL_COST} 포인트 차감)",
        "mileage": mileage[user]
    }

@app.post("/guess-photo")
async def guess_photo(
    request: Request,
    target_user: str = Form(...),
    guess: str = Form(...)
):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    photo_game = load_photo_game()
    mileage = load_mileage()
    
    # 대상 사용자의 사진 존재 여부 확인
    if target_user not in photo_game.get("photos", {}):
        raise HTTPException(status_code=400, detail="해당 사용자의 사진이 없습니다.")
    
    # 이미 누군가가 맞춘 사진인지 확인
    correct_guesses = photo_game.get("correct_guesses", {})
    if target_user in correct_guesses and len(correct_guesses[target_user]) > 0:
        raise HTTPException(status_code=400, detail="이미 다른 사람이 맞춘 사진입니다.")
    
    # 마일리지 확인
    if mileage.get(user, 0) < GUESS_COST:
        raise HTTPException(status_code=400, detail="마일리지가 부족합니다.")
    
    # 마일리지 차감
    mileage[user] = mileage.get(user, 0) - GUESS_COST
    save_mileage(mileage)  # 즉시 저장
    
    # 정답 확인 - answers 매핑을 사용
    answers = photo_game.get("answers", {})
    correct_answers = answers.get(target_user, [target_user])  # 매핑이 없으면 target_user 자체가 정답
    
    # 배열이 아닌 경우 배열로 변환
    if not isinstance(correct_answers, list):
        correct_answers = [correct_answers]
    
    # 정답 목록 중 하나라도 맞으면 정답 처리
    is_correct = False
    for correct_answer in correct_answers:
        if guess.replace(" ", "") == correct_answer.replace(" ", ""):
            is_correct = True
            break
    
    if is_correct:
        # 정답 처리 - target_user 사진을 맞춘 사람으로 user 추가
        if target_user not in correct_guesses:
            correct_guesses[target_user] = []
        correct_guesses[target_user].append(user)
        photo_game["correct_guesses"] = correct_guesses
        
        # 전체 사진 공개 - 5x5 그리드의 모든 셀을 공개
        revealed_cells = photo_game.get("revealed_cells", {})
        for x in range(5):
            for y in range(5):
                cell_key = f"{target_user}:{x}:{y}"
                revealed_cells[cell_key] = True
        photo_game["revealed_cells"] = revealed_cells
        
        save_photo_game(photo_game)
        
        # 보상 지급
        mileage[user] = mileage.get(user, 0) + CORRECT_REWARD
        save_mileage(mileage)
        
        return {
            "success": True,
            "correct": True,
            "message": f"정답입니다! {CORRECT_REWARD} 포인트를 획득했습니다!",
            "mileage": mileage[user]
        }
    
    # 오답 처리
    wrong_guesses = photo_game.get("wrong_guesses", {})
    if target_user not in wrong_guesses:
        wrong_guesses[target_user] = []
    wrong_guesses[target_user].append({"user": user, "guess": guess})
    photo_game["wrong_guesses"] = wrong_guesses
    save_photo_game(photo_game)
    
    return {
        "success": True,
        "correct": False,
        "message": f"틀렸습니다. {GUESS_COST} 포인트가 차감되었습니다.",
        "mileage": mileage[user]
    }

@app.get("/admin")
async def get_admin(request: Request):
    # 관리자 인증 확인
    if not request.session.get("admin_authenticated"):
        return templates.TemplateResponse(
            "admin_login.html",
            {"request": request}
        )
    
    mileage_data = load_mileage()
    users_data = load_users()
    
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "mileage_data": mileage_data,
            "users_data": users_data
        }
    )

@app.post("/admin-login")
async def admin_login(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        request.session["admin_authenticated"] = True
        return {"success": True, "message": "관리자 인증 성공"}
    raise HTTPException(status_code=401, detail="잘못된 관리자 비밀번호입니다.")

@app.post("/admin/update-mileage")
async def update_mileage(
    request: Request,
    username: str = Form(...),
    points: int = Form(...)
):
    # 관리자 인증 확인
    if not request.session.get("admin_authenticated"):
        raise HTTPException(status_code=401, detail="관리자 인증이 필요합니다.")
    
    mileage_data = load_mileage()
    
    if username not in mileage_data:
        mileage_data[username] = 0
    
    mileage_data[username] += points
    
    # 마일리지가 음수가 되지 않도록 제한
    if mileage_data[username] < 0:
        mileage_data[username] = 0
    
    save_mileage(mileage_data)
    
    return {
        "success": True,
        "message": f"{username}의 마일리지가 {points:+d}점 변경되었습니다.",
        "new_mileage": mileage_data[username]
    }

@app.get("/admin/logout")
async def admin_logout(request: Request):
    request.session.pop("admin_authenticated", None)
    return RedirectResponse(url="/admin")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8890)
