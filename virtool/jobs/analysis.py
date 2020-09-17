import asyncio
import json
import logging
import os
import pathlib
import shutil
import typing

import pymongo.errors

import virtool.caches.db
import virtool.caches.utils
import virtool.db
import virtool.history.db
import virtool.jobs.fastqc
import virtool.jobs.job
import virtool.jobs.utils
import virtool.samples.db
import virtool.samples.utils
import virtool.samples.utils
import virtool.subtractions.utils
import virtool.utils
from virtool.jobs.caching import create_cache, set_cache_id

TRIMMING_PROGRAM = "skewer-0.2.2"

logger = logging.getLogger(__name__)


async def check_db(job: virtool.jobs.job.Job):
    """
    Get some initial information from the database that will be required during the course of the job. Attach the data to the job object.

    :param job: the job object

    """
    logger.debug("Retrieving job parameters")

    job.params = {
        # The document id for the sample being analyzed. and the analysis document the results will be committed to.
        "sample_id": job.task_args["sample_id"],
        # The document id for the reference to analyze against.
        "ref_id": job.task_args["ref_id"],
        # The document id for the analysis being run.
        "analysis_id": job.task_args["analysis_id"],
    }

    # The document for the sample being analyzed. Assigned after database connection is made.
    sample = await job.db.samples.find_one(job.params["sample_id"])

    # The parent folder for all data associated with the sample
    sample_path = os.path.join(
        job.settings["data_path"], "samples", job.params["sample_id"]
    )

    analysis_path = os.path.join(sample_path, "analysis", job.params["analysis_id"])

    analysis = await job.db.analyses.find_one(
        job.params["analysis_id"], ["subtraction"]
    )

    temp_analysis_path = os.path.join(job.temp_dir.name, job.task_args["analysis_id"])

    job.params.update(
        {
            # The path to the directory where all analysis result files will be written.
            "analysis_path": analysis_path,
            "index_path": os.path.join(
                job.settings["data_path"],
                "references",
                job.params["ref_id"],
                job.task_args["index_id"],
                "reference",
            ),
            "sample_path": sample_path,
            "paired": sample["paired"],
            #: The number of reads in the sample library. Assigned after database connection is made.
            "read_count": int(sample["quality"]["count"]),
            "sample_read_length": int(sample["quality"]["length"][1]),
            "library_type": sample["library_type"],
            "reads_path": os.path.join(job.temp_dir.name, "reads"),
            "subtraction_path": virtool.subtractions.utils.join_subtraction_index_path(
                job.settings, analysis["subtraction"]["id"]
            ),
            "raw_path": os.path.join(job.temp_dir.name, "raw"),
            "temp_cache_path": os.path.join(job.temp_dir.name, "cache"),
            "temp_analysis_path": temp_analysis_path,
        }
    )

    index_info = await get_index_info(job.db, job.settings, job.task_args["index_id"])

    job.params.update(index_info)

    read_paths = [os.path.join(job.params["reads_path"], "reads_1.fq.gz")]

    if job.params["paired"]:
        read_paths.append(os.path.join(job.params["reads_path"], "reads_2.fq.gz"))

    job.params["read_paths"] = read_paths


async def make_analysis_dir(job):
    """
    Make a directory for the analysis in the sample/analysis directory.

    """
    await job.run_in_executor(os.mkdir, job.params["temp_analysis_path"])
    await job.run_in_executor(os.mkdir, job.params["raw_path"])
    await job.run_in_executor(os.mkdir, job.params["reads_path"])


async def prepare_reads(job):
    """
    Fetch cache.

    """
    paired = job.params["paired"]

    parameters = get_trimming_parameters(
        paired, job.params["library_type"], job.params["sample_read_length"]
    )

    cache = await virtool.caches.db.find(
        job.db, job.params["sample_id"], TRIMMING_PROGRAM, parameters
    )

    if cache:
        logger.debug("Found cache")
        logger.debug("Fetching cache")
        return await fetch_cache(job, cache)

    sample = await job.db.samples.find_one(job.params["sample_id"])
    paths = virtool.samples.utils.join_legacy_read_paths(job.settings, sample)

    if paths:
        logger.debug("Found legacy sample")
        logger.debug("Fetching legacy sample data")
        return await fetch_legacy(job, paths)

    logger.debug("Creating new cache for sample")
    return await create_cache(job, parameters)


async def delete_analysis(job):
    await job.db.analyses.delete_one({"_id": job.params["analysis_id"]})

    try:
        shutil.rmtree(job.params["analysis_path"], ignore_errors=True)
    except FileNotFoundError:
        pass

    await virtool.samples.db.recalculate_workflow_tags(job.db, job.params["sample_id"])


async def delete_cache(job: virtool.jobs.job.Job):
    """
    Delete the cache associated with the passed `job`.

    :param job: the job object

    """
    cache_id = job.intermediate.get("cache_id")

    if cache_id:
        cache = await job.db.caches.find_one(cache_id, ["ready"])

        if not cache.get("ready"):
            await job.db.caches.delete_one({"_id": cache_id})

            cache_path = virtool.caches.utils.join_cache_path(job.settings, cache_id)

            try:
                await job.run_in_executor(virtool.utils.rm, cache_path, True)
            except FileNotFoundError:
                pass


async def fetch_cache(job: virtool.jobs.job.Job, cache: dict):
    """
    Copy the cache files for the passed `job` to the analysis directory.

    :param job: the job the files are required for
    :param cache: the cache document for the job

    """
    cached_read_paths = virtool.caches.utils.join_cache_read_paths(job.settings, cache)

    coros = list()

    for path in cached_read_paths:
        local_path = os.path.join(job.params["reads_path"], pathlib.Path(path).name)
        coros.append(job.run_in_executor(shutil.copy, path, local_path))

    await asyncio.gather(*coros)

    await set_cache_id(job, cache["id"])


async def fetch_legacy(job, legacy_read_paths):
    coros = list()

    for path in legacy_read_paths:
        local_path = os.path.join(job.params["reads_path"], pathlib.Path(path).name)

        coros.append(job.run_in_executor(shutil.copy, path, local_path))

    await asyncio.gather(*coros)


async def get_sequence_otu_map(db, settings, manifest):
    app_dict = {"db": db, "settings": settings}

    sequence_otu_map = dict()

    for otu_id, otu_version in manifest.items():
        _, patched, _ = await virtool.history.db.patch_to_version(
            app_dict, otu_id, otu_version
        )

        for isolate in patched["isolates"]:
            for sequence in isolate["sequences"]:
                sequence_id = sequence["_id"]
                sequence_otu_map[sequence_id] = patched["_id"]

    return sequence_otu_map


def copy_trimming_results(src: str, dest: str):
    """
    Copy read files resulting from trimming from the `src` directory to the `dest` directory.

    :param src: the path to the source directory
    :param dest: the path to the destination directory

    """
    shutil.copy(os.path.join(src, "reads_1.fq.gz"), dest)

    try:
        shutil.copy(os.path.join(src, "reads_2.fq.gz"), dest)
    except FileNotFoundError:
        pass


def get_trimming_min_length(library_type, sample_read_length) -> int:
    if library_type == "amplicon":
        return round(0.95 * sample_read_length)

    if sample_read_length < 80:
        return 35

    if sample_read_length < 160:
        return 100

    return 160


async def get_index_info(db, settings, index_id):
    document = await db.indexes.find_one(index_id, ["manifest", "sequence_otu_map"])

    try:
        sequence_otu_map = document["sequence_otu_map"]
    except KeyError:
        sequence_otu_map = await get_sequence_otu_map(
            db, settings, document["manifest"]
        )

    return {"manifest": document["manifest"], "sequence_otu_map": sequence_otu_map}


def get_trimming_parameters(paired: bool, library_type: str, sample_read_length: int):
    """

    :param paired:
    :param library_type:
    :param sample_read_length:
    :return:

    """
    min_length = get_trimming_min_length(library_type, sample_read_length)

    if library_type == "amplicon":
        return {
            **virtool.samples.utils.TRIM_PARAMETERS,
            "end_quality": 0,
            "mean_quality": 0,
            "min_length": min_length,
        }

    if library_type == "srna":
        return {
            **virtool.samples.utils.TRIM_PARAMETERS,
            "min_length": 20,
            "max_length": 22,
        }

    return {**virtool.samples.utils.TRIM_PARAMETERS, "min_length": min_length}


async def set_analysis_results(
    db, analysis_id: str, analysis_path: str, results: typing.Union[dict, list]
):
    """
    Save the analysis results to the database document or write them to disc if the document size limit is encountered.

    :param db: the application database object
    :param analysis_id: the ID of the analysis being saved
    :param analysis_path: the path to the analysis
    :param results: the results data

    """
    try:
        await db.analyses.update_one(
            {"_id": analysis_id}, {"$set": {"results": results, "ready": True}}
        )
    except pymongo.errors.DocumentTooLarge:
        with open(os.path.join(analysis_path, "results.json"), "w") as f:
            json_string = json.dumps(results)
            f.write(json_string)

        await db.analyses.update_one(
            {"_id": analysis_id}, {"$set": {"results": "file", "ready": True}}
        )


async def upload(job: virtool.jobs.job.Job):
    """
    Upload the temporary analysis job data path to the permanent analysis path.

    Eventually this needs to be changed to have the data path compressed and uploaded to an object storage service.

    :param job: the job to upload data for

    """
    await job.run_in_executor(
        shutil.copytree, job.params["temp_analysis_path"], job.params["analysis_path"]
    )
