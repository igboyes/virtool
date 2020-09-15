"""
Defines a handler for websocket requests.

"""
import logging

import aiohttp.web

import virtool.dispatcher

logger = logging.getLogger(__name__)


async def root(req: aiohttp.web.Request):
    """
    Handles requests for WebSocket connections.

    """
    ws = aiohttp.web.WebSocketResponse(autoping=True, heartbeat=5)

    await ws.prepare(req)

    connection = virtool.dispatcher.Connection(ws, req["client"])

    req.app["dispatcher"].add_connection(connection)

    try:
        async for _ in ws:
            pass
    except RuntimeError as err:
        if "TCPTransport" not in str(err):
            raise

    logger.info("Connection closed")

    req.app["dispatcher"].remove_connection(connection)

    return ws
