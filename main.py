import asyncio
import contextlib
import cProfile
import pstats

from fastapi import FastAPI
from langchain_core.runnables import RunnableParallel, RunnableLambda


@contextlib.asynccontextmanager
async def lifespan(app=FastAPI):
    pr = cProfile.Profile()
    pr.enable()
    try:
        yield
    finally:
        # CUMULATIVE is total time spent within function including callees
        ps = pstats.Stats(pr).sort_stats(pstats.SortKey.CUMULATIVE)
        ps.dump_stats("profile.stats")  # Dump profiling info to profile.stats
        ps.print_stats(.01)


app = FastAPI(lifespan=lifespan)


async def one(inputs):
    await asyncio.sleep(0.1)
    return 1


async def stream():
    for i in range(10):
        await asyncio.sleep(0.01)
        yield i


@app.get("/api/generate")
async def generate():
    chain = RunnableParallel(one=RunnableLambda(one))
    output_stream = chain.astream({})
    # output_stream = stream()
    async for _ in output_stream:
        pass
    return {}
