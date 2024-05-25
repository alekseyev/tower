from litestar import Request, Response, get, post
from litestar.security.jwt import JWTAuth, Token
from litestar.status_codes import HTTP_401_UNAUTHORIZED

from backend.core.models import JWTUser, LoginData, PasswordData, RegisterData, User
from backend.settings import settings


async def retrieve_user_handler(token: Token, *args) -> JWTUser:
    return JWTUser(
        id=token.extras["id"],
        email=token.sub,
    )


jwt_auth = JWTAuth[User](
    retrieve_user_handler=retrieve_user_handler,
    token_secret=settings.AUTH_SECRET,
    # we are specifying which endpoints should be excluded from authentication. In this case the login endpoint
    # and our openAPI docs.
    exclude=["/login", "/schema", "/register", "/$"],
)


def login_user(user: User) -> Response:
    return jwt_auth.login(identifier=user.email, token_extras={"id": str(user.id)}, send_token_as_response_body=True)


@post("/login")
async def login_handler(data: LoginData) -> Response:
    user = await User.by_email(data.email)

    if user and user.verify_password(data.password):
        return login_user(user)

    return Response(
        {"error": "Invalid user and/or password"},
        status_code=HTTP_401_UNAUTHORIZED,
    )


@post("/register")
async def register_handler(data: RegisterData) -> Response:
    user = await User.create_user(**data.model_dump())
    return login_user(user)


@get("/me")
async def me_handler(request: Request) -> JWTUser:
    return request.user


@post("/change-password")
async def change_password_handler(request: Request, data: PasswordData) -> Response:
    user = await User.get(request.user.id)
    user.set_password(data.password)
    await user.save()
    return Response({"okie": "dokie"})


auth_handlers = [login_handler, me_handler, register_handler, change_password_handler]
