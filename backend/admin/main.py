from nicegui import app, ui

from backend.admin.common import render_navigation
from backend.app_ctx import AppCtx

render_navigation("Home")
ui.label("Hello there")

initialized = False


async def on_start():
    global initialized
    if not initialized:
        await AppCtx.start()
    initialized = True


app.on_startup(on_start)
# app.on_shutdown(AppCtx.shutdown)

ui.run()
