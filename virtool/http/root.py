import virtool.http.routes
from virtool.api.response import json_response

API_URL_ROOT = "https://www.virtool.ca/docs/developer/api"

routes = virtool.http.routes.Routes()


@routes.get("/api")
async def get(req):
    """
    Returns a generic message. Used during testing for acquiring a ``session_id``.

    """
    return json_response(
        {
            "endpoints": {
                "account": {
                    "url": "/api/account",
                    "doc": f"{API_URL_ROOT}/account.html",
                },
                "analyses": {
                    "url": "/api/analyses",
                    "doc": f"{API_URL_ROOT}/analyses.html",
                },
                "genbank": {
                    "url": "/api/genbank",
                    "doc": f"{API_URL_ROOT}/genbank.html",
                },
                "groups": {"url": "/api/groups", "doc": f"{API_URL_ROOT}/groups.html"},
                "history": {
                    "url": "/api/history",
                    "doc": f"{API_URL_ROOT}/history.html",
                },
                "hmm": {"url": "/api/hmm", "doc": f"{API_URL_ROOT}/hmm.html"},
                "indexes": {
                    "url": "/api/indexes",
                    "doc": f"{API_URL_ROOT}/indexes.html",
                },
                "jobs": {"url": "/api/jobs", "doc": f"{API_URL_ROOT}/jobs.html"},
                "otus": {"url": "/api/otus", "doc": f"{API_URL_ROOT}/otus.html"},
                "processes": {
                    "url": "/api/processes",
                    "doc": f"{API_URL_ROOT}/processes.html",
                },
                "references": {
                    "url": "/api/references",
                    "doc": f"{API_URL_ROOT}/references.html",
                },
                "samples": {
                    "url": "/api/samples",
                    "doc": f"{API_URL_ROOT}/samples.html",
                },
                "settings": {
                    "url": "/api/settings",
                    "doc": f"{API_URL_ROOT}/settings.html",
                },
                "subtraction": {
                    "url": "/api/subtraction",
                    "doc": f"{API_URL_ROOT}/subtraction.html",
                },
                "users": {"url": "/api/users", "doc": f"{API_URL_ROOT}/users.html"},
            },
            "version": req.app["version"],
        }
    )
