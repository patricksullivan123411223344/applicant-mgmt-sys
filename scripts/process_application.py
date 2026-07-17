"""Command-triggered application processing (Phase 1 MVP runtime)."""

from __future__ import annotations

import argparse
import sys
from uuid import UUID

from housing_processor.application.commands.process import ProcessApplicationCommand
from housing_processor.application.dto.actor import ActorContext
from housing_processor.bootstrap import build_container
from housing_processor.domain.shared.identifiers import ApplicationId


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Process a housing application by ID")
    parser.add_argument("application_id", type=UUID, help="Application UUID")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocess regardless of current status",
    )
    args = parser.parse_args(argv)

    container = build_container()
    actor = ActorContext(
        actor_id=UUID("00000000-0000-4000-8000-000000000001"),
        role="operations",
        request_id="script-process-application",
    )
    result = container.process_handler.handle(
        ProcessApplicationCommand(
            application_id=ApplicationId(args.application_id),
            actor=actor,
            force_reprocess=args.force,
        )
    )
    print(
        f"application_id={result.application_id} "
        f"status={result.status.value} "
        f"warnings={list(result.warnings)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
