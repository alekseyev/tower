from litestar import Litestar, get

from backend.app_ctx import get_application_ctx
from backend.core.api_auth import auth_handlers, jwt_auth
from backend.courses.handlers import user_handlers


@get("/")
async def hello() -> str:
    return "Hello, world"


app = Litestar(
    [hello, *auth_handlers, *user_handlers],
    lifespan=[get_application_ctx],
    on_app_init=[jwt_auth.on_app_init],
    debug=True,
)
