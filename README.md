# OpenTelemetry OpenAI instrumentation performance investigation

My team encountered performance issues with our gunicorn / uvicorn / FastAPI / OpenAI based service. The service reached 100% CPU utilisation on lower loads than expected, capping the overall throughput. This repo is a minimal reproducible example of the issue, which we suspect caused by the opentelemetry-instrumentation-openai library being CPU intensive.

## Prerequisites

- [uv](https://docs.astral.sh/uv/).
- [ApacheBenchmark](https://httpd.apache.org/docs/2.4/programs/ab.html) (`ab`) for loading the system.
- [graphviz](https://graphviz.org/) and [xdot](https://graphviz.org/docs/attr-types/xdot/) for interacting with the visual profiling outputs.
- OpenAI API key. Make sure it's in `.env` (i.e. `echo "OPENAI_API_KEY=<your-key>" > .env`).
- `uv sync`

### Run and load the service

```bash
./run.sh
```

On another terminal

```bash
ab -l -c 75 -n 200 http://localhost:9000/
```

When done stop the service (`Ctrl-C`).


## Working with profiling info

When the service is stopped it writes profiling information to `stdout` and to `profile.stats`. The profile is generated with [yappi](https://github.com/sumerc/yappi/tree/master). This profiler was chosen over cProfile because of the [reasons here](https://github.com/sumerc/yappi/blob/master/doc/coroutine-profiling.md). TL;DR: The total time measured with cProfile includes time in callees.

Some useful things you can do with `profile.stats`:

```bash
uv run gprof2dot -f pstats profile.stats > profile.dot
dot -Tpng profile.dot -o profile.png  # to convert the dot file to png
xdot profile.dot  # for interactive view of the dot file
```

## Investigation

Load testing produces these results:

- Requests per second: 1.43
- Median response time: 42951ms

Profiling information:

```
         20727930 function calls (21725562 primitive calls) in 98.452 seconds

   Ordered by: internal time
   List reduced from 1946 to 20 due to restriction <20>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
    43450   16.802    0.000   73.513    0.002 /home/tgurion/.local/share/uv/python/cpython-3.12.6-linux-x86_64-gnu/lib/python3.12/email/feedparser.py:216(FeedParser._parsegen)
  5497700   15.427    0.000   22.207    0.000 /home/tgurion/.local/share/uv/python/cpython-3.12.6-linux-x86_64-gnu/lib/python3.12/email/feedparser.py:77(BufferedSubFile.readline)
  5497700   14.446    0.000   36.653    0.000 /home/tgurion/.local/share/uv/python/cpython-3.12.6-linux-x86_64-gnu/lib/python3.12/email/feedparser.py:127(BufferedSubFile.__next__)
...
```

A lot of time was spent in `feedparser.py`. We can find the callers with `xdot`. All of the calls are coming from the OTEL OpenAI instrumentation library, specifically from `utils:is_openai_v1` and `shared:model_as_dict`. If my understanding of [the `.dot` file format is correct](https://github.com/jrfonseca/gprof2dot?tab=readme-ov-file#output) the code spent 48% and 24% of the entire execution time of the service in these two functions, including time spent in callees.

### Removing the OTEL OpenAI instrumentation library and trying again

```bash
uv remove opentelemetry-instrumentation-openai
```

New load testing results:
- Requests per second: 6.08
- Median response time: 12025ms
