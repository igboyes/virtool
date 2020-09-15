"""
Wrappers for AIOHTTP routing that add security and validation features to API endpoints.

"""
import json.decoder

import aiohttp.web
from cerberus import Validator

import virtool.users.utils
from virtool.api.response import invalid_input, json_response


class Routes(aiohttp.web.RouteTableDef):
    """
    An extension of :class:`aiohttp.web.RouteTableDef` that adds security functionality.

    - `admin`: user must be administrator to use endpoint
    - `permission`: user must have this permission to use endpoint
    - `public`: endpoint is public and does not require authorization
    - `schema: a Cerberus schema for handling the JSON request body`

    """

    def __init__(self):
        super().__init__()

    def get(
        self, *args, admin=False, permission=None, public=False, schema=None, **kwargs
    ):
        route_decorator = super().get(*args, **kwargs)
        return protect(route_decorator, admin, permission, public, schema)

    def post(
        self, *args, admin=False, permission=None, public=False, schema=None, **kwargs
    ):
        route_decorator = super().post(*args, **kwargs)
        return protect(route_decorator, admin, permission, public, schema)

    def patch(
        self, *args, admin=False, permission=None, public=False, schema=None, **kwargs
    ):
        route_decorator = super().patch(*args, **kwargs)
        return protect(route_decorator, admin, permission, public, schema)

    def put(
        self, *args, admin=False, permission=None, public=False, schema=None, **kwargs
    ):
        route_decorator = super().put(*args, **kwargs)
        return protect(route_decorator, admin, permission, public, schema)

    def delete(
        self, *args, admin=False, permission=None, public=False, schema=None, **kwargs
    ):
        route_decorator = super().delete(*args, **kwargs)
        return protect(route_decorator, admin, permission, public, schema)


def protect(
    route_decorator: callable, admin: bool, permission: str, public: bool, schema: dict
) -> callable:
    """
    Protect the route wrapped by the passed `route_decorator`.

    :param route_decorator: the route decorator from AIOHTTP
    :param admin: flags the endpoint as requiring the administrator role
    :param permission: the endpoint requires the permission to be called
    :param public: flags the endpoint as being public (no authorization required)
    :param schema: a Cerberus schema for handling JSON input
    :return: a decorator function

    """
    if permission and permission not in virtool.users.utils.PERMISSIONS:
        raise ValueError("Invalid permission: " + permission)

    def decorator(handler):
        async def wrapped(req):

            if not public and not req["client"].user_id:
                return json_response(
                    {
                        "id": "requires_authorization",
                        "message": "Requires authorization",
                    },
                    status=401,
                )

            if not req["client"].administrator:
                if admin:
                    return json_response(
                        {
                            "id": "not_permitted",
                            "message": "Requires administrative privilege",
                        },
                        status=403,
                    )

                if permission and not req["client"].permissions[permission]:
                    return json_response(
                        {"id": "not_permitted", "message": "Not permitted"}, status=403
                    )

            content_type = req.headers.get("Content-type", "")

            if "multipart/form-data" not in content_type:
                try:
                    data = await req.json()
                except (json.decoder.JSONDecodeError, UnicodeDecodeError):
                    data = dict()

                if schema:
                    v = Validator(schema, purge_unknown=True)

                    if not v.validate(data):
                        return invalid_input(v.errors)

                    data = v.document

                req["data"] = data

            return await handler(req)

        return route_decorator(wrapped)

    return decorator
