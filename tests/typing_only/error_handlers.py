from __future__ import annotations

from typing import Any

import falcon
from falcon import asgi


class MyRequest(falcon.Request):
    def some(self) -> bool:
        return True


class MyResponse(falcon.Response):
    def method(self) -> bool:
        return True


def hook_1(
    req: MyRequest, resp: falcon.Response, err: ValueError, params: dict[str, Any]
) -> None: ...
def hook_2(
    req: falcon.Request, resp: MyResponse, err: NameError, params: dict[str, Any]
) -> None: ...
def hook_3(
    req: MyRequest, resp: MyResponse, err: LookupError, params: dict[str, Any]
) -> None: ...
def hook_4(
    req: falcon.Request,
    resp: falcon.Response,
    err: AttributeError,
    params: dict[str, Any],
) -> None: ...


app1 = falcon.App()
app1.add_error_handler(ValueError, hook_1)
app1.add_error_handler(NameError, hook_2)
app1.add_error_handler(LookupError, hook_3)
app1.add_error_handler(AttributeError, hook_4)
app1.add_error_handler([ValueError], hook_1)
app1.add_error_handler([NameError], hook_2)
app1.add_error_handler([LookupError], hook_3)
app1.add_error_handler([AttributeError], hook_4)
# TODO: test these errors somehow
# app1.add_error_handler(BufferError, hook_1)
# app1.add_error_handler(BufferError, hook_2)
# app1.add_error_handler(BufferError, hook_3)
# app1.add_error_handler(BufferError, hook_4)

app2 = falcon.App(request_type=MyRequest, response_type=MyResponse)
app2.add_error_handler(ValueError, hook_1)
app2.add_error_handler(NameError, hook_2)
app2.add_error_handler(LookupError, hook_3)
app2.add_error_handler(AttributeError, hook_4)
app2.add_error_handler([ValueError], hook_1)
app2.add_error_handler([NameError], hook_2)
app2.add_error_handler([LookupError], hook_3)
app2.add_error_handler([AttributeError], hook_4)

# ----
# asgi
# ----


class AMyRequest(asgi.Request):
    def some(self) -> bool:
        return True


class AMyResponse(asgi.Response):
    def method(self) -> bool:
        return True


async def a_hook_1(
    req: AMyRequest,
    resp: asgi.Response | None,
    err: ValueError,
    params: dict[str, Any],
    *,
    ws: asgi.WebSocket | None = None,
) -> None: ...
async def a_hook_2(
    req: asgi.Request,
    resp: AMyResponse | None,
    err: NameError,
    params: dict[str, Any],
    *,
    ws: asgi.WebSocket | None = None,
) -> None: ...
async def a_hook_3(
    req: AMyRequest,
    resp: AMyResponse | None,
    err: LookupError,
    params: dict[str, Any],
    *,
    ws: asgi.WebSocket | None = None,
) -> None: ...
async def a_hook_4(
    req: asgi.Request,
    resp: asgi.Response | None,
    err: AttributeError,
    params: dict[str, Any],
    *,
    ws: asgi.WebSocket | None = None,
) -> None: ...


a_app1 = asgi.App()
a_app1.add_error_handler(ValueError, a_hook_1)
a_app1.add_error_handler(NameError, a_hook_2)
a_app1.add_error_handler(LookupError, a_hook_3)
a_app1.add_error_handler(AttributeError, a_hook_4)
a_app1.add_error_handler([ValueError], a_hook_1)
a_app1.add_error_handler([NameError], a_hook_2)
a_app1.add_error_handler([LookupError], a_hook_3)
a_app1.add_error_handler([AttributeError], a_hook_4)


a_app2 = asgi.App(request_type=AMyRequest, response_type=AMyResponse)
a_app2.add_error_handler(ValueError, a_hook_1)
a_app2.add_error_handler(NameError, a_hook_2)
a_app2.add_error_handler(LookupError, a_hook_3)
a_app2.add_error_handler(AttributeError, a_hook_4)
a_app2.add_error_handler([ValueError], a_hook_1)
a_app2.add_error_handler([NameError], a_hook_2)
a_app2.add_error_handler([LookupError], a_hook_3)
a_app2.add_error_handler([AttributeError], a_hook_4)
