"""What Claude calls cost, to show how much prompt caching saves. Estimates only: list prices,
standard tier, 5-minute cache writes. The bill itself comes from the Anthropic Console."""

from dataclasses import dataclass

from .models import HAIKU, SONNET

PER_MILLION = 1_000_000
# A 5-minute cache write costs 1.25x the normal input price; reads have their own price.
CACHE_WRITE_MULTIPLIER = 1.25


@dataclass(frozen=True)
class Price:
    """US dollars per million tokens."""

    input: float
    output: float
    cache_read: float


PRICES: dict[str, Price] = {
    SONNET: Price(input=2.00, output=10.00, cache_read=0.20),
    HAIKU: Price(input=1.00, output=5.00, cache_read=0.10),
}


@dataclass(frozen=True)
class CallCost:
    # Input as if every token were charged at the normal input price: cache reads count
    # for less than one token each, cache writes for more.
    billed_input_tokens: int
    # US dollars, or None for a model missing from PRICES.
    cost_usd: float | None
    cost_without_cache_usd: float | None


def call_cost(
    model: str, input_tokens: int, cache_read_tokens: int, cache_write_tokens: int, output: int
) -> CallCost:
    """`input_tokens` is all of the call's input, cached or not."""
    uncached = input_tokens - cache_read_tokens - cache_write_tokens
    price = _price_of(model)
    if price is None:
        # Without prices, use the usual ratios: reads at a tenth of the input price.
        billed = uncached + cache_read_tokens * 0.1 + cache_write_tokens * CACHE_WRITE_MULTIPLIER
        return CallCost(round(billed), None, None)

    input_cost = (
        uncached * price.input
        + cache_read_tokens * price.cache_read
        + cache_write_tokens * price.input * CACHE_WRITE_MULTIPLIER
    )
    output_cost = output * price.output
    return CallCost(
        billed_input_tokens=round(input_cost / price.input),
        cost_usd=(input_cost + output_cost) / PER_MILLION,
        cost_without_cache_usd=(input_tokens * price.input + output_cost) / PER_MILLION,
    )


def _price_of(model: str) -> Price | None:
    """Responses may name a dated version of the model, e.g. "claude-haiku-4-5-20251001"."""
    for name, price in PRICES.items():
        if model.startswith(name):
            return price
    return None
