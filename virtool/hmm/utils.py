import typing

import semver
import virtool.github


def format_hmm_release(
    updated: typing.Union[dict, None],
    release: typing.Union[dict, None],
    installed: typing.Union[dict, None],
):
    """
    Format an JSON HMM release obtained from GitHub.

    :param updated:
    :param release:
    :param installed: what release is installed
    :return:
    """
    # The release dict will only be replaced if there is a 200 response from GitHub. A 304 indicates the release
    # has not changed and `None` is returned from `get_release()`.
    if updated is None:
        return None

    formatted = virtool.github.format_release(updated)

    formatted["newer"] = bool(
        release is None
        or installed is None
        or (
            installed
            and semver.compare(
                formatted["name"].lstrip("v"), installed["name"].lstrip("v")
            )
            == 1
        )
    )

    return formatted
