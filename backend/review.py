

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import base64
import time

# --- Các hàm hỗ trợ ---
CURRENT_REVIEW = []

def encode_url_key(url):
    """
    Mã hóa URL để làm Document ID an toàn.
    Firestore ID không được chứa dấu '/'
    """
    return base64.urlsafe_b64encode(url.encode()).decode().strip('=')

def has_user_reviewed(uid, url):
    """
    Check if a user has already reviewed a URL.
    Returns True if user has reviewed, False otherwise.
    """
    try:
        db = firestore.client()
        safe_url_id = encode_url_key(url)
        
        # Query for reviews by this user for this URL
        reviews_ref = db.collection('reviews').document(safe_url_id).collection('list_reviews')
        from google.cloud.firestore_v1.base_query import FieldFilter
        query = reviews_ref.where(filter=FieldFilter('uid', '==', uid)).limit(1)
        docs = list(query.stream())
        
        return len(docs) > 0
        
    except Exception as e:
        print(f"[ERROR] Error checking user review: {e}")
        return False

def save_review(uid, url, review_data):
    try:
        db = firestore.client()
        
        # Check if user has already reviewed
        if has_user_reviewed(uid, url):
            print(f"[ERROR] User {uid} has already reviewed {url}")
            return False
        
        # 1. Chuẩn bị ID và Key
        safe_url_id = encode_url_key(url)
        timestamp = int(time.time() * 1000)
        review_id = f"{timestamp}_{uid}" # ID theo format bạn yêu cầu
        
        # 2. Bổ sung thông tin vào data (nên lưu lại uid và timestamp trong data để dễ query)
        review_data['uid'] = uid
        review_data['timestamp'] = timestamp
        review_data['reviewId'] = review_id

        # 3. Tạo reference đến vị trí lưu
        # Cấu trúc: Collection 'reviews' -> Doc (URL) -> Sub-collection 'list_reviews' -> Doc (ReviewID)
        doc_ref = db.collection('reviews').document(safe_url_id)\
                    .collection('list_reviews').document(review_id)
        
        # 4. Lưu dữ liệu (.set sẽ ghi đè nếu ID đã tồn tại, hoặc tạo mới nếu chưa)
        doc_ref.set(review_data)
        return True
        
    except Exception as e:
        print(f"[ERROR] Error saving review: {e}")
        return False   

def delete_review(uid, url, review_id):
    """
    Delete a review by review ID.
    Only the user who created the review can delete it.
    """
    try:
        db = firestore.client()
        safe_url_id = encode_url_key(url)
        
        # Verify the review belongs to this user before deleting
        doc_ref = db.collection('reviews').document(safe_url_id)\
                    .collection('list_reviews').document(review_id)
        
        doc = doc_ref.get()
        if doc.exists:
            review_data = doc.to_dict()
            # Check if this review belongs to the current user
            if review_data.get('uid') == uid:
                doc_ref.delete()
                return True
            else:
                print(f"[ERROR] User {uid} cannot delete review {review_id} (not owner)")
                return False
        else:
            print(f"[ERROR] Review {review_id} not found")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error deleting review: {e}")
        return False

def get_reviews(url):
    try:
        db = firestore.client()
        
        # 1. Mã hóa URL để tìm đúng Document cha
        safe_url_id = encode_url_key(url) # Hàm encode đã viết ở bước trước
        
        # 2. Truy cập vào Sub-collection
        reviews_ref = db.collection('reviews').document(safe_url_id).collection('list_reviews')
        
        # 3. Lấy dữ liệu (stream() tốt hơn get() cho dữ liệu lớn)
        docs = reviews_ref.stream()
        
        all_reviews = []
        CURRENT_REVIEW.clear()
        for doc in docs:
            review_data = doc.to_dict()
            all_reviews.append(review_data)
            CURRENT_REVIEW.append(review_data)
        return all_reviews

    except Exception as e:
        print(f"[ERROR] Error getting reviews: {e}")
        return []
