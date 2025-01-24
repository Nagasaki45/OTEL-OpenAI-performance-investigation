import contextlib
import pstats

import yappi
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI

load_dotenv()




@contextlib.asynccontextmanager
async def lifespan(app=FastAPI):
    yappi.start()
    try:
        yield
    finally:
        stats = yappi.get_func_stats()
        ps = yappi.convert2pstats(stats.get())
        # TIME is total time spent within function excluding callees
        ps = ps.sort_stats(pstats.SortKey.TIME)
        ps.dump_stats("profile.stats")  # Dump profiling info to profile.stats
        ps.print_stats(20)  # Printing the top 20 calls


app = FastAPI(lifespan=lifespan)


async def generate_joke():
    client = AsyncOpenAI()
    stream = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Tell me a dad joke"}],
        stream=True
    )

    async for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content

    yield "\n"


@app.get("/")
async def joke():
    return StreamingResponse(generate_joke(), media_type="text/plain")
