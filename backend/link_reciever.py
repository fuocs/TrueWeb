# Biến này sẽ lưu trữ tất cả các hàm đã "đăng ký lắng nghe"
_subscribers = []

def register(callback_function):
    """
    Hàm này cho phép các module khác đăng ký một hàm để nhận tín hiệu.
    'callback_function' là hàm sẽ được gọi khi có link mới.
    """
    if callable(callback_function):
        _subscribers.append(callback_function)

def trigger(url):
    """
    Hàm này được gọi bởi "người phát tín hiệu" (ví dụ: server).
    Nó sẽ lặp qua tất cả các hàm đã đăng ký và gọi chúng với URL nhận được.
    """
    if not _subscribers:
        return
    
    for func in _subscribers:
        try:
            func(url)  # Gọi hàm listener với dữ liệu là URL
        except Exception as e:
            print(f"[Receiver] Lỗi khi thực thi hàm '{func.__name__}': {e}")