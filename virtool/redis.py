import asyncio
import logging
import json
import sys
import typing

import aioredis

import virtool.types

logger = logging.getLogger(__name__)


async def connect(redis_connection_strong: str) -> aioredis.Redis:
    """
    Connect to a Redis server.

    :param redis_connection_strong: the Redis server connection string
    :return: a connection object

    """
    try:
        redis = await aioredis.create_redis_pool(redis_connection_strong)
        await check_version(redis)

        return redis
    except ConnectionRefusedError:
        logger.fatal("Could not connect to Redis: Connection refused")
        sys.exit(1)


async def check_version(redis: aioredis.Redis):
    """
    Get the Redis server version and log it.

    :param redis: a Redis connection object

    """
    info = await redis.execute("INFO", encoding="utf-8")

    for line in info.split("\n"):
        if line.startswith("redis_version"):
            version = line.replace("redis_version:", "")
            logger.info(f"Found Redis {version}")
            return


def create_dispatch(redis: aioredis.Redis) -> callable:
    """
    Create and return a dispatch coroutine that will dispatch messages via PubSub over the given Redis connection.

    :param redis: a Redis connection
    :return: a dispatch coroutine
    
    """

    async def func(interface, operation, id_list):
        json_string = json.dumps(
            {"interface": interface, "operation": operation, "id_list": id_list}
        )

        await redis.publish("channel:dispatch", json_string)

        logger.debug(f"Dispatched message via Redis: {interface}.{operation}")

    return func


async def listen_for_changes(app: virtool.types.App):
    """
    Listen for dispatch messages on the appropriate Redis PubSub channel and handle them.

    :param app: the application object

    """
    logging.debug("Started listening for changes")

    (dispatch_channel,) = await app["redis"].subscribe("channel:dispatch")

    try:
        while True:
            message = await dispatch_channel.get_json()

            if message is not None:
                interface = message["interface"]
                operation = message["operation"]

                await app["change_queue"].put(
                    [interface, operation, message["id_list"]]
                )

                logger.debug(f"Received change: {interface}.{operation}")
    except asyncio.CancelledError:
        pass

    logging.debug("Stopped listening for changes")
