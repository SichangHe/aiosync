import asyncio
import pytest
from aio_sync.oneshot import OneShot


def test_oneshot_send_and_try_recv():
    async def _run():
        sender, receiver = OneShot[int].channel()
        assert receiver.try_recv() is None
        sender.send(4)
        assert receiver.try_recv() == 4
        with pytest.raises(ValueError):
            sender.send(5)

    asyncio.run(_run())


def test_oneshot_recv_waits_for_value():
    async def _run():
        sender, receiver = OneShot[int].channel()

        async def _send():
            await asyncio.sleep(0)
            sender.send(9)

        task = asyncio.create_task(_send())
        assert await receiver.recv() == 9
        await task

    asyncio.run(_run())
