"""Print the configured trusted-source allowlist so you can verify env wiring."""
from backend.config import get_settings


def main() -> None:
    settings = get_settings()
    print(f"GEMINI_MODEL          = {settings.gemini_model}")
    print(f"LOCAL_MODE            = {settings.local_mode}")
    print(f"CHUNK_SECONDS         = {settings.chunk_seconds}")
    print(f"MAX_CLAIMS_PER_SESSION= {settings.max_claims_per_session}")
    print("Trusted domains:")
    for d in settings.trusted_domain_list:
        print(f"  - {d}")


if __name__ == "__main__":
    main()
