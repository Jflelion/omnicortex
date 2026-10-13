from time import perf_counter


class Timer:
    """
    Measure elapsed execution time in milliseconds.

    The timer uses ``perf_counter`` because it provides a high-resolution,
    monotonic clock suitable for measuring application and AI pipeline stages.

    A Timer instance can be started once, stopped, and inspected through
    the ``elapsed_ms`` property.
    """

    def __init__(self) -> None:
        """
        Initialize a timer that has not been started.
        """

        self._started_at: float | None = None
        self._elapsed_ms: float | None = None

    def start(self) -> None:
        """
        Start or restart the timer.

        Starting the timer clears any previously recorded elapsed duration.
        """

        self._started_at = perf_counter()
        self._elapsed_ms = None

    def stop(self) -> float:
        """
        Stop the timer and return the elapsed duration in milliseconds.

        Returns:
            The number of milliseconds elapsed since ``start`` was called.

        Raises:
            RuntimeError: If the timer has not been started.
        """

        if self._started_at is None:
            raise RuntimeError("Timer has not been started")

        elapsed_seconds = perf_counter() - self._started_at
        self._elapsed_ms = elapsed_seconds * 1000

        return self._elapsed_ms

    @property
    def elapsed_ms(self) -> float | None:
        """
        Return the last measured duration in milliseconds.

        Returns:
            The recorded duration, or ``None`` if the timer has not been
            stopped since its most recent start.
        """

        return self._elapsed_ms