"""
Globals and utility functions for interacting with the jobs collection in the application database.

"""
import typing

import virtool.jobs.runner
import virtool.utils

OR_COMPLETE = [{"status.state": "complete"}]

OR_FAILED = [{"status.state": "error"}, {"status.state": "cancelled"}]

#: The default MongoDB projection for job documents.
PROJECTION = ["_id", "task", "status", "proc", "mem", "user"]


async def cancel(db, job_id: str):
    """
    Cancel the job identified by `job_id`. This function only sets the job as cancelled in the database. It will be
    called when the job

    :param db: the application database object
    :param job_id: the ID of the job to cancel

    """
    document = await db.jobs.find_one(job_id, ["status"])

    latest = document["status"][-1]

    await db.jobs.update_one(
        {"_id": job_id},
        {
            "$push": {
                "status": {
                    "state": "cancelled",
                    "stage": latest["stage"],
                    "error": None,
                    "progress": latest["progress"],
                    "timestamp": virtool.utils.timestamp(),
                }
            }
        },
    )


async def clear(db, complete: bool = False, failed: bool = False) -> typing.List[str]:
    """
    Delete multiple jobs based on the `complete` and `failed` parameters.

    complete: only complete jobs
    failed: only failed jobs
    both or neither: all non-running jobs

    :param db: the application database object
    :param complete: clear only complete jobs
    :param failed: clear only failed jobs
    :return: a list of removed job IDs

    """
    or_list = list()

    if complete:
        or_list = OR_COMPLETE

    if failed:
        or_list += OR_FAILED

    removed = list()

    if len(or_list):
        query = {"$or": or_list}

        removed = await db.jobs.distinct("_id", query)
        await db.jobs.delete_many(query)

    return removed


async def create(
    db,
    task_name: str,
    task_args: dict,
    user_id: str,
    job_id: typing.Optional[str] = None,
) -> dict:
    """
    Create a job document, insert it in the database, and return it.

    :param db: the application database object
    :param task_name: the name of the task
    :param task_args: the args for the job
    :param user_id: the id of the starting user
    :param job_id: force an id for the job (will be auto
    :return: the job document

    """
    document = {
        "task": task_name,
        "args": task_args,
        "user": {"id": user_id},
        "state": "waiting",
        "status": [
            {
                "state": "waiting",
                "stage": None,
                "error": None,
                "progress": 0,
                "timestamp": virtool.utils.timestamp(),
            }
        ],
    }

    if job_id:
        document["_id"] = job_id

    return await db.jobs.insert_one(document)


async def delete_zombies(db):
    """
    Delete running jobs. Called on application start to clean up zombie jobs.

    :param db: the application database object

    """
    await db.jobs.delete_many(
        {"status.state": {"$nin": ["complete", "cancelled", "error"]}}
    )


async def get_waiting_and_running_ids(db) -> typing.List[str]:
    """
    Get a list of IDs for all waiting and running jobs.

    :param db: the application database object
    :return: a list of job IDs

    """
    cursor = db.jobs.aggregate(
        [
            {"$project": {"status": {"$arrayElemAt": ["$status", -1]}}},
            {
                "$match": {
                    "$or": [{"status.state": "waiting"}, {"status.state": "running"},]
                }
            },
            {"$project": {"_id": True}},
        ]
    )

    return [a["_id"] async for a in cursor]


async def processor(db, document: dict) -> dict:
    """
    The default document processor for job documents. Transforms projected job documents to a structure that can be
    dispatches to clients.

    1. Removes the ``status`` and ``args`` fields from the job document.
    2. Adds a ``username`` field.
    3. Adds a ``created_at`` date taken from the first status entry in the job document.
    4. Adds ``state`` and ``progress`` fields derived from the most recent ``status`` entry in the job document.

    :param db: the application database object
    :param document: a document to process
    :return: a processed document

    """
    status = document.pop("status")

    last_update = status[-1]

    document.update(
        {
            "state": last_update["state"],
            "stage": last_update["stage"],
            "created_at": status[0]["timestamp"],
            "progress": status[-1]["progress"],
        }
    )

    return virtool.utils.base_processor(document)
