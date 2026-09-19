import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

import app.main as main

BACKEND_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BACKEND_DIR.parents[0] / "frontend"


@pytest.fixture
def clean_root_logging():
    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level
    try:
        yield root_logger
    finally:
        root_logger.handlers.clear()
        root_logger.handlers.extend(original_handlers)
        root_logger.setLevel(original_level)


def test_configure_logging_adds_one_info_handler_idempotently(clean_root_logging):
    root_logger = clean_root_logging
    root_logger.handlers.clear()
    root_logger.setLevel(logging.WARNING)

    main._configure_logging()
    assert len(root_logger.handlers) == 1
    assert root_logger.level == logging.INFO

    main._configure_logging()
    assert len(root_logger.handlers) == 1


def test_configure_logging_preserves_existing_handlers(clean_root_logging):
    root_logger = clean_root_logging
    root_logger.handlers.clear()
    root_logger.setLevel(logging.ERROR)
    handler = logging.NullHandler()
    root_logger.addHandler(handler)

    main._configure_logging()

    assert root_logger.handlers == [handler]
    assert root_logger.level == logging.ERROR


def test_import_logs_effective_configuration_without_logging_setup():
    environment = os.environ.copy()
    environment["MAGI_STATIC_DIR"] = str(FRONTEND_DIR)
    environment.pop("MAGI_RATE_LIMIT_PER_MINUTE", None)
    environment.pop("MAGI_TRUST_PROXY", None)

    result = subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=BACKEND_DIR,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Magi configuration:" in result.stderr
    assert "(mounted)" in result.stderr
