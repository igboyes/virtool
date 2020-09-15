import typing

import aiohttp.web_app

#: Can be an application or `dict` posing as an aiohttp.web_app.Application (a dict-like object).
App = typing.Union[aiohttp.web_app.Application, dict]
