import firebase_admin
from . import firebaseDB
from firebase_admin import credentials, firestore, auth
import requests
import json
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]

# ---------------------------------------------------------
# CHỨC NĂNG: ĐĂNG KÝ (Dùng Admin SDK)
# Admin SDK có quyền tạo user trực tiếp mà không cần biết password cũ
# ---------------------------------------------------------

class user_info:
    uid = None 
    username = None 
    email = None
    def __init__(self) -> None:
        return 
    def login(self, uid: str, username: str, email: str):
        self.uid = uid
        self.username = username
        self.email = email
    
    def __str__(self):
        return f"User(username='{self.username}', email='{self.email}', uid='{self.uid}')"
    
    def __repr__(self):
        return self.__str__()

CURRENT_USER = user_info()

def register(email: str, password: str, name: str):
    
    try:
        user_record = auth.create_user(
            email=email,
            password=password,
            display_name=name
        )

        db = firestore.client()
        
        uid = user_record.uid
        user_data = {
            "userId": uid,
            "email": email,
            "username": name,
            "createdAt": firestore.SERVER_TIMESTAMP # pyright: ignore[reportAttributeAccessIssue]
        }

        db.collection('users').document(uid).set(user_data)
        return {'status': True, 'uid': uid}
    except ValueError as ve:
        print(f"{ve}")
        return {'status': False, 'message':ve}
    except Exception as e:
        print(f"{e}")
        return {'status': False, 'message':e}

# ---------------------------------------------------------
# CHỨC NĂNG: ĐĂNG NHẬP (Dùng REST API)
# Vì Admin SDK không thể 'đăng nhập' bằng pass, ta dùng Web API để giả lập
# ---------------------------------------------------------

def login(email: str, password: str):
    
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    try:
        # Gọi API kiểm tra pass
        GIT_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={firebaseDB.FIREBASE_WEB_API_KEY}"
        response = requests.post(GIT_URL, json=payload)
        data = response.json()

        if "error" in data:
            return {'status': False, 'message': data['error']['message']}

        uid = data['localId']
        return {'status': True, 'userId': uid}
    
    except Exception as e:
        return {'status': False, 'message': e}
    
    
def reset_password(email: str):

    try:
        # Hàm này sẽ ném lỗi UserNotFoundError nếu không tìm thấy email
        auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        return False, "There are no user using this email"
    
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={firebaseDB.FIREBASE_WEB_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    data = {
        "requestType": "PASSWORD_RESET",
        "email": email
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(response)
    if response.status_code == 200:
        return True, None
    else:
        print("Lỗi:", response.json())
        return False, response.json 

def login_with_google_flow():
    try:
        # Get config from firebaseDB module (embedded config)
        client_config = json.loads(firebaseDB.GOOGLE_CLIENT_CONFIG)

        # Sử dụng hàm from_client_config thay vì from_client_secrets_file
        flow = InstalledAppFlow.from_client_config(
            client_config, SCOPES
        )
        
        # Chạy local server để nhận callback từ Google
        creds = flow.run_local_server(port=0)
        google_id_token = creds.id_token # type: ignore

        if not google_id_token:
            return {"success": False, "error": "No Google ID Token found"}

        request_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={firebaseDB.FIREBASE_WEB_API_KEY}"
        
        payload = {
            "postBody": f"id_token={google_id_token}&providerId=google.com",
            "requestUri": "http://localhost",
            "returnIdpCredential": True,
            "returnSecureToken": True
        }

        response = requests.post(request_url, json=payload)
        data = response.json()

        if "error" in data:
            return {"success": False, "error": data["error"]["message"]}

        u_uid = data.get("localId")
        u_email = data.get("email")
        # displayName là tên từ Google, nếu không có thì lấy tạm email
        u_name = data.get("displayName", u_email.split('@')[0]) 

        # Khởi tạo class user_info
        new_user = user_info()
        new_user.login(uid=u_uid, username=u_name, email=u_email)

        return {
            "success": True, 
            "user": new_user,
            "idToken": data["idToken"],
            "refreshToken": data["refreshToken"]
        }

    except Exception as e:  
        return {"success": False, "error": str(e)}
    
def get_user_profile(uid):
    try:
        db = firestore.client()
        # Truy cập trực tiếp collection users
        doc_ref = db.collection('users').document(uid)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else: 
            return None 
    except Exception as e:
        print(f"❌ Lỗi đọc dữ liệu: {e}")
        return None
