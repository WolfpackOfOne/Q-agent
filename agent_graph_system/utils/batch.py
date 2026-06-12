"""Generic async batch-fan-out helper.

Inspired by QuantMind's ``flows/batch.py``: run an async function over many
inputs with bounded concurrency, collecting per-input results and errors
without letting one failure abort the rest of the batch.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


@dataclass(slots=True)
class BatchResult(Generic[OutputT]):
    """Aggregate result of running a flow over many inputs.

    ``results[i]`` is the output for ``inputs[i]``, which may legitimately be
    ``None`` on success — ``succeeded[i]`` disambiguates that from a failed
    input. ``errors`` carries ``(index, exception)`` for every failure, sorted
    by index.
    """

    total: int
    success_count: int
    failure_count: int
    results: list[OutputT | None]
    succeeded: list[bool]
    errors: list[tuple[int, Exception]]
    duration_seconds: float

    @property
    def successes(self) -> list[tuple[int, OutputT | None]]:
        """``(index, result)`` for every input that succeeded."""
        return [(i, r) for i, (ok, r) in enumerate(zip(self.succeeded, self.results)) if ok]

    @property
    def failures(self) -> list[tuple[int, Exception]]:
        """Alias for ``errors`` to mirror ``successes`` for symmetry."""
        return list(self.errors)


async def batch_run(
    fn: Callable[..., Awaitable[OutputT]],
    inputs: list[InputT],
    *,
    concurrency: int = 4,
    on_error: Literal["raise", "skip"] = "skip",
    on_progress: Callable[[int, int], None] | None = None,
    **fn_kwargs: Any,
) -> BatchResult[OutputT]:
    """Run ``fn`` over ``inputs`` with bounded concurrency.

    Args:
        fn: Any async callable with signature ``(input, **kwargs) -> Awaitable[OutputT]``.
        inputs: Inputs to fan out over. Empty list returns an empty
            ``BatchResult`` immediately.
        concurrency: Maximum number of in-flight calls. Must be >= 1.
        on_error: ``"raise"`` propagates the first failure (siblings get
            cancelled); ``"skip"`` records every failure into ``errors``
            and returns the batch normally.
        on_progress: Called as ``on_progress(done, total)`` after every
            completion (success or failure). Must be cheap and
            non-blocking — callbacks are invoked synchronously inside
            the worker loop.
        **fn_kwargs: Forwarded verbatim to ``fn``.

    Returns:
        ``BatchResult`` with ``results`` parallel to ``inputs`` (None for
        failures) and ``errors`` sorted by index.

    Raises:
        ValueError: If ``concurrency < 1``.
        Exception: Re-raised when ``on_error="raise"`` and any input
            fails. The exception is the first one raised by a worker;
            other workers may already be cancelled when this surfaces.
    """
    if concurrency < 1:
        raise ValueError(f"concurrency must be >= 1, got {concurrency}")

    if not inputs:
        return BatchResult(
            total=0,
            success_count=0,
            failure_count=0,
            results=[],
            succeeded=[],
            errors=[],
            duration_seconds=0.0,
        )

    sem = asyncio.Semaphore(concurrency)
    results: list[OutputT | None] = [None] * len(inputs)
    succeeded: list[bool] = [False] * len(inputs)
    errors: list[tuple[int, Exception]] = []
    started = time.monotonic()
    done_counter = 0

    async def run_one(i: int, inp: InputT) -> None:
        nonlocal done_counter
        async with sem:
            try:
                results[i] = await fn(inp, **fn_kwargs)
                succeeded[i] = True
            except Exception as exc:
                errors.append((i, exc))
                if on_error == "raise":
                    raise
            finally:
                done_counter += 1
                if on_progress is not None:
                    on_progress(done_counter, len(inputs))

    await asyncio.gather(*(run_one(i, inp) for i, inp in enumerate(inputs)))

    return BatchResult(
        total=len(inputs),
        success_count=sum(succeeded),
        failure_count=len(errors),
        results=results,
        succeeded=succeeded,
        errors=sorted(errors, key=lambda t: t[0]),
        duration_seconds=time.monotonic() - started,
    )
