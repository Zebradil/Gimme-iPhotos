FROM python:3.8-alpine3.11 as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app


FROM base as builder

RUN apk add --no-cache openssl-dev musl-dev libffi-dev gcc
RUN pip install poetry
COPY pyproject.toml poetry.lock .
RUN poetry export -f requirements.txt > requirements.txt


FROM base as final

RUN apk add --no-cache openssl-dev gcc musl-dev libffi-dev
COPY --from=builder /app/requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN pip install .
ENTRYPOINT ["/usr/local/bin/gimme-iphotos"]
