"""WebSocket uchun JWT autentifikatsiyasi.

Brauzerning WebSocket API'si maxsus header yubora olmaydi, shuning uchun
token query string orqali keladi: ws://.../ws/notifications/?token=<access>
"""
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def get_user_from_token(raw_token):
    from rest_framework_simplejwt.exceptions import TokenError
    from rest_framework_simplejwt.tokens import AccessToken

    from apps.users.models import User

    try:
        token = AccessToken(raw_token)
        user = User.objects.filter(id=token["user_id"]).first()
    except (TokenError, KeyError):
        return AnonymousUser()

    if user is None or not user.is_active:
        return AnonymousUser()
    return user


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        token = (query.get("token") or [None])[0]

        # Subprotocol orqali ham qabul qilamiz (ba'zi klientlar shunday yuboradi)
        if not token:
            for proto in scope.get("subprotocols", []):
                if proto.startswith("token."):
                    token = proto.split(".", 1)[1]
                    break

        scope["user"] = await get_user_from_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)
