from asyncio import Event
from dataclasses import dataclass, field
from typing import NamedTuple, cast

_ASSUME_ONE_SHOT_SENT_IS_TRUE_MEANS_ALREADY_SENT = None


@dataclass(slots=True)
class _SharedState[T]:
    waker: Event = field(default_factory=Event, init=False)
    sent: bool = field(default=False, init=False)
    value: T | None = field(default=None, init=False)


@dataclass(slots=True)
class OneShotReceiver[T]:
    _state: _SharedState[T]

    def try_recv(self) -> T | None:
        """Try to receive the value sent through the one-shot channel.
        @return the value if already sent, or None if not yet sent.
        Examples:
            >>> sender, receiver = OneShot[str].channel()
            >>> receiver.try_recv() is None
            True
            >>> sender.send("hello")
            >>> receiver.try_recv()
            'hello'
        """
        if self._state.waker.is_set():
            _ = _ASSUME_ONE_SHOT_SENT_IS_TRUE_MEANS_ALREADY_SENT
            assert self._state.sent, (
                "OneShot `sent` should've been set when waker is set.",
                self._state,
            )
            return self._state.value
        else:
            return None

    async def recv(self) -> T:
        """Wait to receive the value sent through the one-shot channel.
        Examples:
            >>> import asyncio
            >>> async def main():
            ...     sender, receiver = OneShot[int].channel()
            ...     sender.send(9)
            ...     return await receiver.recv()
            >>> asyncio.run(main())
            9
        """
        _ = await self._state.waker.wait()
        _ = _ASSUME_ONE_SHOT_SENT_IS_TRUE_MEANS_ALREADY_SENT
        assert self._state.sent, (
            "OneShot `sent` should've been set when waker is set.",
            self._state,
        )
        return cast(T, self._state.value)


@dataclass(slots=True)
class OneShotSender[T]:
    _state: _SharedState[T]

    def send(self, value: T):
        """Send a value through the one-shot channel, immediately.
        @raise ValueError if sending more than once.
        Examples:
            >>> sender, receiver = OneShot[int].channel()
            >>> sender.send(4)
            >>> receiver.try_recv()
            4
        """
        if self._state.waker.is_set():
            raise ValueError(f"OneShot can only send once, {self}.")
        self._state.value = value
        _ = _ASSUME_ONE_SHOT_SENT_IS_TRUE_MEANS_ALREADY_SENT
        self._state.sent = True
        self._state.waker.set()


def oneshot_channel[T]() -> tuple[OneShotSender[T], OneShotReceiver[T]]:
    """Create a one-shot channel.
    Prefer using `OneShot[T].channel` instead.
    @return: (sender, receiver) pair.
    Examples:
        >>> sender, receiver = oneshot_channel()
        >>> sender.send(1)
        >>> receiver.try_recv()
        1
    """
    state = _SharedState[T]()
    return OneShotSender(state), OneShotReceiver(state)


class OneShot[T](NamedTuple):
    """One-shot channel `NamedTuple` for convenience of type-parametrized construction.
    Examples:
        >>> sender, receiver = OneShot[int].channel()
        >>> sender.send(1)
        >>> receiver.try_recv()
        1
    """

    sender: OneShotSender[T]
    receiver: OneShotReceiver[T]

    @classmethod
    def channel(cls) -> tuple[OneShotSender[T], OneShotReceiver[T]]:
        """Create a one-shot channel.
        @return: (sender, receiver) pair.
        Examples:
            >>> sender, receiver = OneShot[int].channel()
            >>> sender.send(1)
            >>> receiver.try_recv()
            1
        """
        sender: OneShotSender[T]
        receiver: OneShotReceiver[T]
        sender, receiver = oneshot_channel()
        return cls(sender, receiver)
