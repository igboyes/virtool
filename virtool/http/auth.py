"""
HTTP authentication.

"""
import base64
import os
from typing import Tuple

import aiofiles
import aiohttp.web
import jinja2

import virtool.db.utils
import virtool.errors
import virtool.http.utils
import virtool.http.utils
import virtool.routes
import virtool.templates
import virtool.users.db
import virtool.users.db
import virtool.users.sessions
import virtool.users.sessions
import virtool.users.utils
import virtool.utils
from virtool.api.response import bad_request

AUTHORIZATION_PROJECTION = ["user", "administrator", "groups", "permissions"]


class Client:
    """
    Allows access to HTTP client data when handling request. This includes

    This implementation needs to be changed at some point.

    """

    def __init__(self, ip):
        # These attributes are assigned even when the session is not authorized.
        self.ip = ip

        self.administrator = None
        self.authorized = False
        self.user_id = None
        self.groups = None
        self.permissions = None
        self.is_api = False
        self.session_id = None
        self.token = None
        self.force_reset = False

    def authorize(self, document, is_api):
        try:
            self.session_id = document["_id"]
            self.administrator = document.get("administrator", False)
            self.authorized = True
            self.user_id = document["user"]["id"]
            self.groups = document["groups"]
            self.permissions = document["permissions"]
            self.is_api = is_api
            self.force_reset = document.get("force_reset", False)
        except KeyError:
            pass

    def set_session_id(self, session_id):
        self.session_id = session_id


async def authorize_with_api_key(req, handler):
    db = req.app["db"]

    authorization = req.headers.get("AUTHORIZATION")

    try:
        user_id, key = decode_authorization(authorization)
    except virtool.errors.AuthError:
        return bad_request("Malformed Authorization header")

    document = await db.keys.find_one(
        {"_id": virtool.users.utils.hash_api_key(key), "user.id": user_id},
        AUTHORIZATION_PROJECTION,
    )

    if not document:
        return bad_request("Invalid Authorization header")

    req["client"].authorize(document, True)

    return await handler(req)


async def can_use_api_key(req: aiohttp.web.Request) -> bool:
    """
    Check if the URL can be authenticated with an API key. Takes into if public API access is enabled on the instance.

    :param req: the request
    :return: API key authentication is possible

    """
    return (req.path[0:4] == "/api" or req.path[0:7] == "/upload") and req.app[
        "settings"
    ]["enable_api"]


def decode_authorization(authorization: str) -> Tuple[str, str]:
    """
    Parse and decode an API key from an HTTP authorization header value.

    :param authorization: the authorization header value for a API request
    :return: a tuple containing the user id and API key parsed from the authorization header

    """
    split = authorization.split(" ")

    if len(split) != 2 or split[0] != "Basic":
        raise virtool.errors.AuthError("Malformed authorization header")

    decoded = base64.b64decode(split[1]).decode("utf-8")

    user_id, key = decoded.split(":")

    return user_id, key


def get_ip(req: aiohttp.web.Request) -> str:
    """
    A convenience function for getting the client IP address from a :class:`~web.Request` object.

    :param req: the request
    :return: the client's IP address string

    """
    return req.transport.get_extra_info("peername")[0]


async def index_handler(req: aiohttp.web.Request) -> aiohttp.web.Response:
    """
    A request handler for requests where the `index.html` should be returned.

    :param req: the request to handle
    :return: the response

    """
    requires_first_user = not await req.app["db"].users.count_documents({})

    requires_login = not req["client"].user_id

    path = os.path.join(req.app["client_path"], "index.html")

    async with aiofiles.open(path, "r") as f:
        template = jinja2.Template(await f.read(), autoescape=True)

    html = template.render(
        dev=req.app["settings"]["dev"],
        first=requires_first_user,
        login=requires_login,
        nonce=req["nonce"],
        version=req.app["version"],
    )

    return aiohttp.web.Response(body=html, content_type="text/html")


@aiohttp.web.middleware
async def middleware(req, handler):
    """
    Middleware for authenticating requests. Authentication data is attached to the request state.

    """
    db = req.app["db"]

    ip = get_ip(req)

    req["client"] = Client(ip)

    if req.path == "/api/account/login" or req.path == "/api/account/logout":
        return await handler(req)

    if req.headers.get("AUTHORIZATION") and await can_use_api_key(req):
        return await authorize_with_api_key(req, handler)

    # Get session information from cookies.
    session_id = req.cookies.get("session_id")
    session_token = req.cookies.get("session_token")

    session = await virtool.users.sessions.get_session(db, session_id, session_token)

    if session is None:
        session, _ = await virtool.users.sessions.create_session(db, ip)

    req["client"].authorize(session, is_api=False)
    req["client"].session_id = session["_id"]

    resp = await handler(req)

    if req.path != "/api/account/reset":
        await virtool.users.sessions.clear_reset_code(db, session["_id"])

    virtool.http.utils.set_session_id_cookie(resp, req["client"].session_id)

    if req.path == "/api/":
        resp.del_cookie("session_token")

    return resp
