# Copyright 2021-2024 by Vytautas Liuolia.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Private type aliases used internally by Falcon.."""

from __future__ import annotations

from enum import auto
from enum import Enum
import http
from http.cookiejar import Cookie
import sys
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Pattern,
    Protocol,
    Tuple,
    TYPE_CHECKING,
    TypeVar,
    Union,
)

# NOTE(vytas): Mypy still struggles to handle a conditional import in the EAFP
#   fashion, so we branch on Py version instead (which it does understand).
if sys.version_info >= (3, 11):
    from wsgiref.types import StartResponse as StartResponse
    from wsgiref.types import WSGIEnvironment as WSGIEnvironment
else:
    WSGIEnvironment = Dict[str, Any]
    StartResponse = Callable[[str, List[Tuple[str, str]]], Callable[[bytes], None]]

if TYPE_CHECKING:
    from falcon.asgi import Request as AsgiRequest
    from falcon.asgi import Response as AsgiResponse
    from falcon.asgi import WebSocket
    from falcon.asgi_spec import AsgiEvent
    from falcon.asgi_spec import AsgiSendMsg
    from falcon.http_error import HTTPError
    from falcon.request import Request
    from falcon.response import Response


class _Unset(Enum):
    UNSET = auto()


# GENERICS
_T = TypeVar('_T')
# there are used to type callables in a way that accept subclasses
_BE = TypeVar('_BE', bound=BaseException)
_REQ = TypeVar('_REQ', bound='Request')
_A_REQ = TypeVar('_A_REQ', bound='AsgiRequest')
_RESP = TypeVar('_RESP', bound='Response')
_A_RESP = TypeVar('_A_RESP', bound='AsgiResponse')

_UNSET = _Unset.UNSET
UnsetOr = Union[Literal[_Unset.UNSET], _T]

Link = Dict[str, str]
CookieArg = Mapping[str, Union[str, Cookie]]
# Error handlers
ErrorHandler = Callable[[_REQ, _RESP, _BE, Dict[str, Any]], None]


class AsgiErrorHandler(Protocol[_A_REQ, _A_RESP, _BE]):
    async def __call__(
        self,
        req: _A_REQ,
        resp: Optional[_A_RESP],
        error: _BE,
        params: Dict[str, Any],
        /,
        *,
        ws: Optional[WebSocket] = ...,
    ) -> None: ...


# Error serializers
ErrorSerializer = Callable[[_REQ, _RESP, 'HTTPError'], None]

# Sinks
SinkPrefix = Union[str, Pattern[str]]


class SinkCallable(Protocol[_REQ, _RESP]):
    def __call__(self, req: _REQ, resp: _RESP, /, **kwargs: str) -> None: ...


class AsgiSinkCallable(Protocol[_A_REQ, _A_RESP]):
    async def __call__(self, req: _A_REQ, resp: _A_RESP, /, **kwargs: str) -> None: ...


HeaderMapping = Mapping[str, str]
HeaderIter = Iterable[Tuple[str, str]]
HeaderArg = Union[HeaderMapping, HeaderIter]
ResponseStatus = Union[http.HTTPStatus, str, int]
StoreArg = Optional[Dict[str, Any]]
Resource = object
RangeSetHeader = Union[Tuple[int, int, int], Tuple[int, int, int, str]]


# WSGI
class ResponderMethod(Protocol[_REQ, _RESP]):
    def __call__(
        self,
        resource: Resource,
        req: _REQ,
        resp: _RESP,
        /,
        **kwargs: Any,
    ) -> None: ...


class ResponderCallable(Protocol[_REQ, _RESP]):
    def __call__(self, req: _REQ, resp: _RESP, /, **kwargs: Any) -> None: ...


ProcessRequestMethod = Callable[[_REQ, _RESP], None]
ProcessResourceMethod = Callable[[_REQ, _RESP, Resource, Dict[str, Any]], None]
ProcessResponseMethod = Callable[[_REQ, _RESP, Resource, bool], None]


# ASGI
class AsgiResponderMethod(Protocol[_A_REQ, _A_RESP]):
    async def __call__(
        self,
        resource: Resource,
        req: _A_REQ,
        resp: _A_RESP,
        /,
        **kwargs: Any,
    ) -> None: ...


class AsgiResponderCallable(Protocol[_A_REQ, _A_RESP]):
    async def __call__(self, req: _A_REQ, resp: _A_RESP, /, **kwargs: Any) -> None: ...


class AsgiResponderWsCallable(Protocol[_A_REQ]):
    async def __call__(self, req: _A_REQ, ws: WebSocket, /, **kwargs: Any) -> None: ...


AsgiReceive = Callable[[], Awaitable['AsgiEvent']]
AsgiSend = Callable[['AsgiSendMsg'], Awaitable[None]]
AsgiProcessRequestMethod = Callable[[_A_REQ, _A_RESP], Awaitable[None]]
AsgiProcessResourceMethod = Callable[
    [_A_REQ, _A_RESP, Resource, Dict[str, Any]], Awaitable[None]
]
AsgiProcessResponseMethod = Callable[[_A_REQ, _A_RESP, Resource, bool], Awaitable[None]]
AsgiProcessRequestWsMethod = Callable[['_A_REQ', 'WebSocket'], Awaitable[None]]
AsgiProcessResourceWsMethod = Callable[
    [_A_REQ, 'WebSocket', Resource, Dict[str, Any]], Awaitable[None]
]
ResponseCallbacks = Union[
    Tuple[Callable[[], None], Literal[False]],
    Tuple[Callable[[], Awaitable[None]], Literal[True]],
]


# Routing

MethodDict = Union[
    Dict[str, ResponderCallable],
    Dict[str, Union[AsgiResponderCallable, AsgiResponderWsCallable]],
]


class FindMethod(Protocol[_REQ]):
    def __call__(
        self, uri: str, req: Optional[_REQ]
    ) -> Optional[Tuple[object, MethodDict, Dict[str, Any], Optional[str]]]: ...


# Media
class SerializeSync(Protocol):
    def __call__(self, media: Any, content_type: Optional[str] = ...) -> bytes: ...


DeserializeSync = Callable[[bytes], Any]

Responder = Union[ResponderMethod, AsgiResponderMethod]
