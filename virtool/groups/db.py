import asyncio
import typing

import virtool.users.db
import virtool.groups.utils
import virtool.utils


async def get_merged_permissions(db, id_list: typing.List[str]) -> dict:
    """
    Get the merged permissions that are inherited as a result of membership in the groups defined in `id_list`.

    :param db: the application database interface
    :param id_list: a list of group ids
    :return: the merged permissions

    """
    groups = await asyncio.shield(
        db.groups.find({"_id": {"$in": id_list}}, {"_id": False}).to_list(None)
    )
    return virtool.groups.utils.merge_group_permissions(groups)


async def update_member_users(db, group_id: str, remove: bool = False):
    """
    Update all user documents that may need to change as a result of changes to their member groups.

    :param db: the application database object
    :param group_id: the ID of the group that has been updated
    :param remove: was the group removed

    """
    groups = await asyncio.shield(db.groups.find().to_list(None))

    async for user in db.users.find(
        {"groups": group_id},
        ["administrator", "groups", "permissions", "primary_group"],
    ):
        if remove:
            user["groups"].remove(group_id)

        new_permissions = virtool.groups.utils.merge_group_permissions(
            [group for group in groups if group["_id"] in user["groups"]]
        )

        # Skip updating this user if their group membership and permissions haven't changed.
        if not remove and new_permissions == user["permissions"]:
            continue

        update_dict = {"$set": {"permissions": new_permissions}}

        if user["primary_group"] == group_id:
            update_dict["$set"]["primary_group"] = ""

        if remove:
            update_dict["$pull"] = {"groups": group_id}

        document = await db.users.find_one_and_update(
            {"_id": user["_id"]}, update_dict, projection=["groups", "permissions"]
        )

        await virtool.users.db.update_sessions_and_keys(
            db,
            user["administrator"],
            user["_id"],
            document["groups"],
            document["permissions"],
        )
