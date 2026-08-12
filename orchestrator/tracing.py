"""
Lightweight OTel tracing so you can show a live node-by-node trace during
the demo (swap ConsoleSpanExporter for an OTLP exporter to feed Jaeger, same
pattern as the original agent-orchestrator).
"""

import functools
import time

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter
)


_provider = TracerProvider(
    resource=Resource.create(
        {
            "service.name": "x402-research-orchestrator"
        }
    )
)

_provider.add_span_processor(
    BatchSpanProcessor(
        ConsoleSpanExporter()
    )
)

trace.set_tracer_provider(_provider)

tracer = trace.get_tracer("orchestrator")


def traced_node(name: str):

    def decorator(fn):

        @functools.wraps(fn)
        def wrapper(state, *args, **kwargs):

            start = time.perf_counter()

            with tracer.start_as_current_span(name) as span:

                if isinstance(state, dict):
                    span.set_attribute(
                        "task_id",
                        str(state.get("task_id", "unknown"))
                    )

                try:
                    return fn(
                        state,
                        *args,
                        **kwargs
                    )

                finally:
                    span.set_attribute(
                        "duration_ms",
                        (time.perf_counter() - start) * 1000
                    )

        return wrapper

    return decorator
