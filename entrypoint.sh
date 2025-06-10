#!/bin/sh

alembic upgrade head
exec python -m app