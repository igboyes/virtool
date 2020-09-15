"""
Functions and constants for constructing the Virtool Content Security Policy (CSP). Nonces are used to allow safe inline
blocks.

A nonce is generated when a request is received and attached to the nonce as a `dict` value.

The nonce is used in :func:`virtool.auth.index_handler` when rendering the application HTML to allow inline scripts. The
nonce is added to the CSP header when preparing the response in :func:`.on_prepare`).

Content Security Policy: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
Info on Nonces: https://content-security-policy.com/nonce/

"""
import secrets
import aiohttp.web

URL_FONT_AWESOME = "https://use.fontawesome.com"
CSP_CONNECT_SRC = "connect-src 'self' sentry.io"
CSP_DEFAULT_SRC = "default-src 'self'"
CSP_FONT_SRC = f"font-src 'self' https://fonts.gstatic.com {URL_FONT_AWESOME}"
CSP_IMG_SRC = "img-src 'self' data:"


def generate_csp_header(nonce: str) -> str:
    """
    Put all of the CSP parts together to make a value for the Content-Security-Policy header.

    :param nonce: a nonce to add to the policy where appropriate
    :return: CSP policy value

    """
    return "; ".join(
        [
            CSP_CONNECT_SRC,
            CSP_DEFAULT_SRC,
            CSP_FONT_SRC,
            CSP_IMG_SRC,
            generate_csp_script_src(nonce),
            generate_csp_style_src(nonce),
        ]
    )


def generate_csp_script_src(nonce: str) -> str:
    """
    Generate script-src policy given a nonce.

    :param nonce: a nonce to add to the policy
    :return: script-src policy

    """
    return f"script-src 'self' 'nonce-{nonce}' {URL_FONT_AWESOME}"


def generate_csp_style_src(nonce):
    """
    Generate style-src policy given a nonce.

    :param nonce: a nonce to add to the policy
    :return: style-src policy

    """
    return f"style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com {URL_FONT_AWESOME};"


def generate_nonce() -> str:
    """
    Generate a nonce.

    :return: the nonce
    """
    return secrets.token_hex(20)


@aiohttp.web.middleware
async def middleware(
    req: aiohttp.web.Request, handler: callable
) -> aiohttp.web.Response:
    """
    AIOHTTP middleware for adding a nonce value to the :class:`aiohttp.web.Request object`.

    :param req: the request to handle
    :param handler: the next handler
    :return: a response

    """
    # Allow the nonce to be accessed from request handlers and signals. The index handler will add the nonce to the
    # index.html template.
    req["nonce"] = generate_nonce()
    return await handler(req)


async def on_prepare(req: aiohttp.web.Request, resp: aiohttp.web.Response):
    """
    Signal handler for generating CSP header and adding to response headers before the response is prepared. Accesses
    nonce generated in middleware and attached to request object.

    See https://aiohttp.readthedocs.io/en/stable/web_advanced.html#signals.

    :param req: the request object
    :param resp: the response object

    """
    nonce = req["nonce"]

    resp.headers["Content-Security-Policy"] = generate_csp_header(nonce)
    resp.headers["X-Virtool-Version"] = req.app["version"]
