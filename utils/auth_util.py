import time
from django.core import signing
import hashlib

from django.http import JsonResponse

HEADER = {'typ': 'JWP', 'alg': 'default'}
KEY = 'four_s'
SALT = 'Luonatic_Jiesus'


def encrypt(obj):
    """加密：signing 加密 and Base64 编码"""
    value = signing.dumps(obj, key=KEY, salt=SALT)
    value = signing.b64_encode(value.encode()).decode()
    return value


def decrypt(src):
    """解密：Base64 解码 and signing 解密"""
    src = signing.b64_decode(src.encode()).decode()
    raw = signing.loads(src, key=KEY, salt=SALT)
    return raw


def create_token(username):
    """生成token信息"""
    # 1. 加密头信息
    header = encrypt(HEADER)
    # 2. 构造Payload(有效期 5分钟)
    payload = {"username": username, "iat": time.time(),
               "exp": time.time() + 5 * 60}
    payload = encrypt(payload)
    # 3. MD5 生成签名
    md5 = hashlib.md5()
    md5.update(("%s.%s" % (header, payload)).encode())
    signature = md5.hexdigest()
    token = "%s.%s.%s" % (header, payload, signature)
    return token


def get_payload(token):
    """解析 token 获取 payload 数据"""
    payload = str(token).split('.')[1]
    payload = decrypt(payload)
    return payload


def get_username(token):
    """解析 token 获取 username"""
    payload = get_payload(token)
    return payload['username']


def get_exp_time(token):
    """解析 token 获取过期时间"""
    payload = get_payload(token)
    return payload['exp']


def check_token(username, token):
    """验证 token：检查 username 和 token 是否一致且未过期"""
    return get_username(token) == username and get_exp_time(token) > time.time()


try:
    from django.utils.deprecation import MiddlewareMixin  # Django 1.10.x
except ImportError:
    MiddlewareMixin = object

# 白名单，表示请求里面的路由时不验证登录信息
API_WHITELIST = [
    '/four_s/user/login/',
    '/four_s/user/signup/'
]


class AuthorizeMiddleware(MiddlewareMixin):

    def process_request(self, request):
        try:
            if request.path in API_WHITELIST:
                return
            username = request.META.get('HTTP_USERNAME')
            token = request.META.get('HTTP_TOKEN')
            if username is None or token is None:
                return JsonResponse({'status': -100, 'info': '请登录'})
            if not check_token(username, token):
                return JsonResponse({'status': -100, 'info': '请重新登录'})

        except Exception as e:
            print(e)
            return JsonResponse({'status': -1, 'info': '服务器错误，注册失败'})
