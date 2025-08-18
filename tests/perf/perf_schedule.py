import asyncio
import sys
import time
import tracemalloc

from gtfs_station_stop.schedule import GtfsSchedule

tracemalloc.start(25)


async def main(*target: str):
    s = GtfsSchedule()
    await s.async_build_schedule(*target)


if __name__ == "__main__":
    start_time = time.perf_counter()

    asyncio.run(main(*sys.argv[1:]))

    end_time = time.perf_counter()

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("traceback")

    stat = top_stats[0]

    print(f"{stat.count} memory blocks: {stat.size / 1024:.1f} KiB")

    for line in stat.traceback.format():
        print(line)

    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.1f} seconds")
