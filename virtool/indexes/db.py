import asyncio
import typing

import pymongo
from typing import Union

import virtool.api.utils
import virtool.history.db
import virtool.utils

PROJECTION = [
    "_id",
    "created_at",
    "has_files",
    "job",
    "otu_count",
    "modification_count",
    "modified_count",
    "user",
    "ready",
    "reference",
    "version",
]


async def processor(db, document: dict) -> dict:
    """
    A processor for index documents. Adds computed data about the index.

    :param db: the application database client
    :param document: the document to be processed
    :return: the processed document

    """
    document = virtool.utils.base_processor(document)

    query = {"index.id": document["id"]}

    change_count, otu_ids = await asyncio.gather(
        db.history.count_documents(query), db.history.distinct("otu.id", query)
    )

    return {
        **document,
        "change_count": change_count,
        "modified_otu_count": len(otu_ids),
    }


async def find(db, req_query: dict, ref_id: typing.Optional[str] = None):
    """
    Find indexes given a URL query (`req_query`). The search can be limited to a single reference using the `ref_id`
    argument.

    :param db: the application database object
    :param req_query: the request query
    :param ref_id: option reference ID to limit the search
    :return: the search data

    """
    base_query = None

    if ref_id:
        base_query = {"reference.id": ref_id}

    data = await virtool.api.utils.paginate(
        db.indexes,
        {},
        req_query,
        base_query=base_query,
        projection=PROJECTION,
        reverse=True,
        sort="version",
    )

    data["documents"] = [await processor(db, d) for d in data["documents"]]

    data.update(await get_unbuilt_stats(db, ref_id))

    return data


async def get_contributors(db, index_id: str) -> typing.List[dict]:
    """
    Return an list of contributors and their contribution count for a specific index.

    :param db: the application database object
    :param index_id: the id of the index to get contributors for
    :return: a list of contributors to the index

    """
    return await virtool.history.db.get_contributors(db, {"index.id": index_id})


async def get_current_id_and_version(
    db, ref_id: str
) -> typing.Tuple[Union[None, str], int]:
    """
    Return the current index id and version number.

    :param db: the application database object
    :param ref_id: the id of the reference to get the current index for
    :return: the index and version of the current index

    """
    document = await db.indexes.find_one(
        {"reference.id": ref_id, "ready": True},
        sort=[("version", pymongo.DESCENDING)],
        projection=["_id", "version"],
    )

    if document is None:
        return None, -1

    return document["_id"], document["version"]


async def get_otus(db, index_id: str) -> typing.List[dict]:
    """
    Return a list of otus and number of changes for a specific index.

    :param db: the application database object
    :param index_id: the id of the index to get otus for
    :return: a list of otus modified in the index

    """
    cursor = db.history.aggregate(
        [
            {"$match": {"index.id": index_id}},
            {"$sort": {"otu.id": 1, "otu.version": -1}},
            {
                "$group": {
                    "_id": "$otu.id",
                    "name": {"$first": "$otu.name"},
                    "count": {"$sum": 1},
                }
            },
            {"$match": {"name": {"$ne": None}}},
            {"$sort": {"name": 1}},
        ]
    )

    return [
        {"id": v["_id"], "name": v["name"], "change_count": v["count"]}
        async for v in cursor
    ]


async def get_next_version(db, ref_id: str) -> int:
    """
    Get the version number that should be used for the next index build.

    :param db: the application database client
    :param ref_id: the id of the reference to get the next version for
    :return: the next version number

    """
    return await db.indexes.count_documents({"reference.id": ref_id, "ready": True})


async def get_unbuilt_stats(db, ref_id: Union[str, None] = None) -> dict:
    """
    Get the number of unbuilt changes and number of OTUs affected by those changes. Used to populate the metadata for a
    index find request.

    Can search against a specific reference or all references.

    :param db: the application database client
    :param ref_id: the ref id to search unbuilt changes for
    :return: the change count and modified OTU count

    """
    ref_query = dict()

    if ref_id:
        ref_query["reference.id"] = ref_id

    history_query = {**ref_query, "index.id": "unbuilt"}

    return {
        "total_otu_count": await db.otus.count_documents(ref_query),
        "change_count": await db.history.count_documents(history_query),
        "modified_otu_count": len(await db.history.distinct("otu.id", history_query)),
    }


async def tag_unbuilt_changes(db, ref_id: str, index_id: str, index_version: int):
    """
    Update the ``index`` field for all unbuilt history changes for a specific ref to be included in the index described
    the passed ``index_id`` and ``index_version``.

    :param db: the application database object
    :param ref_id: the ref id to tag changes for
    :param index_id: the index id to tag changes unbuilt with
    :param index_version: the index version to tag unbuilt changes with

    """
    await db.history.update_many(
        {"reference.id": ref_id, "index.id": "unbuilt"},
        {"$set": {"index": {"id": index_id, "version": index_version}}},
    )
