import typing

import virtool.processes.steps
import virtool.db.utils
import virtool.processes.process
import virtool.utils


async def create(db, process_type: str, context: typing.Optional[dict] = None) -> dict:
    """
    Create a new process document, insert it, and return it.

    :param db: the application database object
    :param process_type: the type of process to create
    :param context: context data to make available in the process
    :return: the new process document
    """
    process_id = await virtool.db.utils.get_new_id(db.processes)

    document = {
        "_id": process_id,
        "complete": False,
        "count": 0,
        "created_at": virtool.utils.timestamp(),
        "progress": 0,
        "resumable": False,
        "context": context or dict(),
        "step": virtool.processes.steps.FIRST_STEPS[process_type],
        "type": process_type,
    }

    await db.processes.insert_one(document)

    return virtool.utils.base_processor(document)


async def update(
    db,
    process_id,
    count=None,
    progress=None,
    step=None,
    context_update=None,
    errors=None,
):
    update_dict = dict()

    if count is not None:
        update_dict["count"] = count

    if progress is not None:
        update_dict["progress"] = progress

    if step:
        update_dict["step"] = step

    if errors is not None:
        update_dict["errors"] = errors

    if context_update:
        for key, value in context_update.items():
            update_dict[f"context.{key}"] = value

    document = await db.processes.find_one_and_update(
        {"_id": process_id}, {"$set": update_dict}
    )

    return virtool.utils.base_processor(document)


async def complete(db, process_id: str):
    """
    Complete a process by setting its `complete` field to `True` and ensuring `progress` is set to `1`.

    :param db: the application database object
    :param process_id: the ID of the process

    """
    await db.processes.update_one(
        {"_id": process_id}, {"$set": {"complete": True, "progress": 1}}
    )
