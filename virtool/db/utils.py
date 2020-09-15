import typing

import virtool.utils


def apply_projection(document: dict, projection: typing.Union[dict, list]) -> dict:
    """
    Apply a Mongo-style projection to a document and return it.

    :param document: the document to project
    :param projection: the projection to apply
    :return: the projected document

    """
    if isinstance(projection, list):
        if "_id" not in projection:
            projection.append("_id")

        return {key: document[key] for key in document if key in projection}

    if not isinstance(projection, dict):
        raise TypeError(f"Invalid type for projection: {type(projection)}")

    if projection == {"_id": False}:
        return {key: document[key] for key in document if key != "_id"}

    if all(value is False for value in projection.values()):
        return {key: document[key] for key in document if key not in projection}

    if "_id" not in projection:
        projection["_id"] = True

    return {key: document[key] for key in document if projection.get(key, False)}


async def determine_mongo_version(db):
    """
    Return the MongoDB server version of a passed database object (`db`).

    :param db: a database object
    :return: the MongoDB server version

    """
    server_info = await db.motor_client.client.server_info()
    return server_info["version"]


async def get_new_id(collection, excluded: typing.Union[None, list, set] = None) -> str:
    """
    Returns a new, unique, id that can be used for inserting a new document. Will not return any id that is included
    in ``excluded``.

    :param collection: the Mongo collection to get a new _id for
    :param excluded: a list of ids to exclude from the search
    :return: an id unique to the collection

    """
    excluded = set(excluded or set())

    excluded.update(await collection.distinct("_id"))

    return virtool.utils.random_alphanumeric(length=8, excluded=excluded)


async def get_one_field(collection, field: str, query):
    """
    Get the value for a single `field` from a single document matching the `query`.

    :param collection: the database collection to search
    :param field: the field to return
    :param query: the document matching query
    :return: the field

    """
    projected = await collection.find_one(query, [field])

    if projected is None:
        return None

    return projected.get(field)


async def get_non_existent_ids(collection, id_list: typing.List[str]):
    """
    Return the IDs that are in `id_list`, but don't exist in the specified `collection`.

    :param collection: the database collection to check
    :param id_list: a list of document IDs to check for existence
    :return: a list of non-existent IDs

    """
    existing_ids = await collection.distinct("_id", {"_id": {"$in": id_list}})
    return set(id_list) - set(existing_ids)


async def id_exists(collection, _id: str) -> bool:
    """
    Check if the document id exists in the collection.

    :param collection: the Mongo collection to check the _id against
    :param _id: the _id to check for
    :return: does the id exist

    """
    return bool(await collection.count_documents({"_id": _id}))


async def ids_exist(collection, id_list: typing.List[str]) -> bool:
    """
    Check if all of the document IDs in ``id_list`` exist in the collection.

    :param collection: the Mongo collection to check ``id_list`` against
    :param id_list: the ids to check for
    :return: do the IDs exist

    """
    return await collection.count_documents({"_id": {"$in": id_list}}) == len(id_list)
