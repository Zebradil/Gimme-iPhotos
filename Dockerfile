# syntax=docker/dockerfile:experimental
FROM python:3.10.5-buster as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN \
    if [ `dpkg --print-architecture` = "armhf" ]; then \
    printf "[global]\nextra-index-url=https://www.piwheels.org/simple\n" > /etc/pip.conf ; \
    fi


FROM base as builder

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt > requirements.txt


FROM base as final

COPY --from=builder /app/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install .

ENTRYPOINT ["/usr/local/bin/gimme-iphotos"]
