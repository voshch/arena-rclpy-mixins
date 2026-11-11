"""A ClientWrapper answers its probe before the first call, and call_forever cannot hang on a dropped reply."""

from __future__ import annotations

import asyncio
import threading
import time

import pytest
import rclpy
from std_srvs.srv import SetBool


def _make_node(name: str):
    from arena_rclpy_mixins.Async import AsyncNode

    return AsyncNode(name)


def _spin(nodes: list[rclpy.node.Node]) -> tuple[threading.Event, threading.Thread]:
    executor = rclpy.executors.MultiThreadedExecutor(num_threads=2)
    for node in nodes:
        executor.add_node(node)
    stop = threading.Event()

    def _loop() -> None:
        while not stop.is_set():
            executor.spin_once(timeout_sec=0.02)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    return stop, thread


class Service:
    """A SetBool server recording what it was sent, answering at once or after `held`."""

    def __init__(self, name: str, held: threading.Event | None = None) -> None:
        self.node = rclpy.create_node(f"{name}_service")
        self.sent: list[bool] = []
        self._held = held
        self.node.create_service(SetBool, f"/{name}", self._answer)

    def _answer(self, request, response):
        self.sent.append(request.data)
        if self._held is not None:
            self._held.wait(5.0)
        response.success = True
        return response


def test_the_probe_is_answered_before_the_first_call() -> None:
    async def main() -> None:
        service = Service("wrapper_probe")
        node = _make_node("wrapper_probe_client")
        stop, thread = _spin([service.node, node])
        try:
            client = node.create_client_wrapper(SetBool, "/wrapper_probe", timeout=5.0, probe=SetBool.Request(data=False))
            assert await client.call_timeout(SetBool.Request(data=True))
        finally:
            stop.set()
            thread.join(timeout=5.0)
            node.destroy_node()
            service.node.destroy_node()
        assert service.sent == [False, True]

    asyncio.run(main())


def test_without_a_probe_the_first_call_is_the_first_request() -> None:
    async def main() -> None:
        service = Service("wrapper_no_probe")
        node = _make_node("wrapper_no_probe_client")
        stop, thread = _spin([service.node, node])
        try:
            client = node.create_client_wrapper(SetBool, "/wrapper_no_probe", timeout=5.0)
            assert await client.call_timeout(SetBool.Request(data=True))
        finally:
            stop.set()
            thread.join(timeout=5.0)
            node.destroy_node()
            service.node.destroy_node()
        assert service.sent == [True]

    asyncio.run(main())


def test_call_forever_gives_up_when_the_reply_never_comes() -> None:
    async def main() -> None:
        release = threading.Event()
        service = Service("wrapper_stalls", held=release)
        node = _make_node("wrapper_stalls_client")
        stop, thread = _spin([service.node, node])
        try:
            client = node.create_client_wrapper(SetBool, "/wrapper_stalls", timeout=5.0)
            started = time.monotonic()
            with pytest.raises(TimeoutError, match="/wrapper_stalls"):
                await client.call_forever(SetBool.Request(data=True), timeout_sec=0.3)
            assert time.monotonic() - started < 5.0
        finally:
            release.set()
            stop.set()
            thread.join(timeout=5.0)
            node.destroy_node()
            service.node.destroy_node()

    asyncio.run(main())
