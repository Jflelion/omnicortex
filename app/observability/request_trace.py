from time import perf_counter
from uuid import uuid4

from app.observability.request_context import get_request_id
from app.observability.logger import get_logger


logger = get_logger(__name__)


class RequestTrace:
    """
    Track the execution of a single application request.

    The trace stores a unique request identifier, stage durations, total
    execution time, and final status. It is intended to make AI pipelines
    observable without coupling individual services to external monitoring
    platforms.
    """

    def __init__(
        self,
        operation: str,
        user_id: int | None = None,
    ) -> None:
        """
        Initialize a new request trace.

        Args:
            operation: Name of the operation being observed.
            user_id: Optional identifier of the authenticated user.
        """

        self.trace_id = get_request_id() or uuid4().hex[:12]
        self.operation = operation
        self.user_id = user_id

        self._started_at = perf_counter()
        self._active_stages: dict[str, float] = {}
        self._stage_durations_ms: dict[str, float] = {}
        self._metrics: dict[str, str | int | float | bool] = {}
        self._total_elapsed_ms: float | None = None

        self.status = "IN_PROGRESS"

    def start_stage(self, stage: str) -> None:
        """
        Start measuring a pipeline stage.

        Args:
            stage: Unique name of the stage.

        Raises:
            RuntimeError: If the same stage is already active.
        """

        if stage in self._active_stages:
            raise RuntimeError(
                f"Stage '{stage}' is already active."
            )

        self._active_stages[stage] = perf_counter()

    def stop_stage(self, stage: str) -> float:
        """
        Stop measuring a pipeline stage.

        Args:
            stage: Name of the active stage.

        Returns:
            Elapsed stage duration in milliseconds.

        Raises:
            RuntimeError: If the stage was never started.
        """

        started_at = self._active_stages.pop(
            stage,
            None,
        )

        if started_at is None:
            raise RuntimeError(
                f"Stage '{stage}' has not been started."
            )

        elapsed_ms = (
            perf_counter() - started_at
        ) * 1000

        self._stage_durations_ms[stage] = elapsed_ms

        logger.info(
            "trace_id=%s operation=%s stage=%s elapsed_ms=%.2f",
            self.trace_id,
            self.operation,
            stage,
            elapsed_ms,
        )

        return elapsed_ms

    def add_metric(
        self,
        name: str,
        value: str | int | float | bool,
    ) -> None:
        """
        Attach a metric or metadata value to the trace.

        Args:
            name: Unique metric name.
            value: Serializable metric value.

        Raises:
            ValueError: If the metric name is empty.
        """

        if not name.strip():
            raise ValueError(
                "Metric name cannot be empty."
            )

        self._metrics[name] = value
    
    def finish(self, status: str = "SUCCESS") -> float:
        """
        Finish the trace and log its summary.

        Args:
            status: Final request status.

        Returns:
            Total execution time in milliseconds.
        """

        self._total_elapsed_ms = (
            perf_counter() - self._started_at
        ) * 1000

        self.status = status

        logger.info(
            (
                "trace_id=%s operation=%s user_id=%s "
                "status=%s total_elapsed_ms=%.2f stages=%s metrics=%s"
            ),
            self.trace_id,
            self.operation,
            self.user_id,
            self.status,
            self._total_elapsed_ms,
            self._stage_durations_ms,
            self._metrics,
        )

        return self._total_elapsed_ms

    def fail(self, error: Exception) -> float:
        """
        Mark the trace as failed and log the associated exception.

        Args:
            error: Exception that caused the operation to fail.

        Returns:
            Total execution time in milliseconds.
        """

        self._total_elapsed_ms = (
            perf_counter() - self._started_at
        ) * 1000

        self.status = "FAILED"

        logger.exception(
            (
                "trace_id=%s operation=%s user_id=%s "
                "status=%s total_elapsed_ms=%.2f error=%s"
            ),
            self.trace_id,
            self.operation,
            self.user_id,
            self.status,
            self._total_elapsed_ms,
            str(error),
        )

        return self._total_elapsed_ms

    @property
    def stage_durations_ms(self) -> dict[str, float]:
        """
        Return a copy of all recorded stage durations.

        Returns:
            Dictionary containing stage names and durations in milliseconds.
        """

        return self._stage_durations_ms.copy()

    @property
    def total_elapsed_ms(self) -> float:
        """
        Return the total request duration.

        Returns:
            Total execution time in milliseconds.

        Raises:
            RuntimeError: If the trace has not finished.
        """

        if self._total_elapsed_ms is None:
            raise RuntimeError(
                "The request trace has not finished yet."
            )

        return self._total_elapsed_ms