import aiohttp.web


def parse_value(value):
    if value == "false" or value == "False":
        return False

    if value == "true" or value == "True":
        return True

    return value


@aiohttp.web.middleware
async def middleware(
    req: aiohttp.web.Request, handler: callable
) -> aiohttp.web.Response:
    """
    Middleware for parsing URL queries and attaching them as a dict to the request object.

    :param req: the handled request
    :param handler: the next handler
    :return: the response

    """
    if req.method == "GET":
        req["query"] = {key: parse_value(value) for key, value in req.query.items()}

    return await handler(req)
