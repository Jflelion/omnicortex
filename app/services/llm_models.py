from dataclasses import dataclass


@dataclass(slots=True)
class LLMResponse:
    """
    Normalized response returned by any language model provider.
    """

    text: str

    model: str

    done_reason: str

    total_duration_ns: int

    load_duration_ns: int

    prompt_eval_duration_ns: int

    eval_duration_ns: int

    prompt_eval_count: int

    eval_count: int

    @property
    def total_duration_ms(self) -> float:
        return self.total_duration_ns / 1_000_000

    @property
    def load_duration_ms(self) -> float:
        return self.load_duration_ns / 1_000_000

    @property
    def prompt_eval_duration_ms(self) -> float:
        return self.prompt_eval_duration_ns / 1_000_000

    @property
    def eval_duration_ms(self) -> float:
        return self.eval_duration_ns / 1_000_000

    @property
    def tokens_per_second(self) -> float:
        if self.eval_duration_ns == 0:
            return 0.0

        seconds = self.eval_duration_ns / 1_000_000_000

        return self.eval_count / seconds