import aiohttp
import aiohttp.web

import virtool.errors
from virtool.api.response import json_response


class ProxyRequest:
    """
    An asynchronous context manager for simplifying outgoing HTTP requests from Virtool (Genbank, GitHub, etc).

    Handles proxy errors and proxy settings without the developer having to write this out for each `aiohttp` client
    request individually.

    """

    def __init__(self, settings, method, url, **kwargs):
        self.proxy = settings["proxy"] or None
        self.method = method
        self.url = url
        self.resp = None
        self._kwargs = kwargs

    async def __aenter__(self):
        try:
            self.resp = await self.method(self.url, proxy=self.proxy, **self._kwargs)
        except aiohttp.ClientHttpProxyError as err:
            if err.status == 407:
                raise virtool.errors.ProxyError("Proxy authentication required")

        if self.resp.status == 407:
            raise virtool.errors.ProxyError("Proxy authentication failed")

        return self.resp

    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            print(exc_type, exc_value, traceback)

        self.resp.close()


@aiohttp.web.middleware
async def middleware(req, handler):
    """
    Returns JSON errors describing proxy problems if a proxy exception is encountered during request handling.
    Exceptions are raise by :class:`ProxyRequest`.

    """
    try:
        return await handler(req)

    except virtool.errors.ProxyError as err:
        return json_response({"id": "proxy_error", "message": str(err)}, status=500)

    except aiohttp.ClientProxyConnectionError:
        return json_response(
            {"id": "proxy_error", "message": "Could not connect to proxy"}, status=500
        )
