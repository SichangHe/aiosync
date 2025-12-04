from asyncio import Event
from dataclasses import dataclass, field

_ASSUME_ONE_SHOT_SENT_IS_TRUE_MEANS_ALREADY_SENT = None


@dataclass(slots=True)
class OneShot[T]:
    """A one-shot channel to send and receive 1 value."""

    _waker: Event = field(default_factory=Event, init=False, repr=True)
    _sent: bool = field(default=False, init=False, repr=True)
    _value: T | None = field(default=None, init=False, repr=True)

    def send(self, value: T):
        """Send a value through the one-shot channel, immediately.
        @raise ValueError if sending more than once."""
        if self._waker.is_set():
            raise ValueError(f"OneShot can only send once, {self=}.")
        self._value = value
        _ = _ASSUME_ONE_SHOT_SENT_IS_TRUE_MEANS_ALREADY_SENT
        self._sent = True
        self._waker.set()

    def try_recv(self) -> T | None:
        """Try to receive the value sent through the one-shot channel.
        @return the value if already sent, or None if not yet sent."""
        if self._waker.is_set():
            _ = _ASSUME_ONE_SHOT_SENT_IS_TRUE_MEANS_ALREADY_SENT
            assert self._sent, (
                "OneShot `_sent` should've been set when waker is set.",
                self,
            )
            return self._value
        else:
            return

    async def recv(self) -> T:
        """Wait to receive the value sent through the one-shot channel."""
        await self._waker.wait()
        _ = _ASSUME_ONE_SHOT_SENT_IS_TRUE_MEANS_ALREADY_SENT
        assert self._sent, (
            "OneShot `_sent` should've been set when waker is set.",
            self,
        )
        return self._value  # type:ignore[return-value]
