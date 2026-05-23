import time

from backend.runtime.dedupe import ClaimDeduper, claim_hash, normalize


def test_normalize_strips_punct_and_stopwords():
    assert normalize("The economy IS growing!!") == "economy growing"


def test_paraphrase_hash_differs_from_exact():
    # Pure normalization, not semantic — paraphrases SHOULD differ.
    assert claim_hash("Inflation hit 9%") != claim_hash("Prices rose nine percent")


def test_identical_claim_is_seen_twice():
    d = ClaimDeduper(ttl_seconds=10, max_size=5)
    assert d.seen("The CPI rose 3% in March") is False
    assert d.seen("the CPI ROSE 3% in March!") is True


def test_ttl_expires():
    d = ClaimDeduper(ttl_seconds=0, max_size=5)
    assert d.seen("a claim about something") is False
    time.sleep(0.01)
    assert d.seen("a claim about something") is False  # ttl=0 → never deduped


def test_lru_eviction():
    d = ClaimDeduper(ttl_seconds=60, max_size=2)
    d.seen("claim one")
    d.seen("claim two")
    d.seen("claim three")  # evicts "claim one"
    assert d.seen("claim one") is False  # no longer remembered
