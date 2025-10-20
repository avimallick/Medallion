# ---- Go builder ----
FROM golang:1.21 as gobuilder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY cmd/ cmd/
COPY internal/ internal/
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/medallion-cli ./cmd/medallion

# ---- Python runtime ----
FROM python:3.12-slim as runtime
ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends     ca-certificates     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python package
COPY medallion/ medallion/
COPY README.md LICENSE pyproject.toml ./

# Copy Go binary from builder into package location
COPY --from=gobuilder /out/medallion-cli medallion/bin/medallion-cli

# Install package
RUN pip install --no-cache-dir .

# Default command shows help
ENTRYPOINT [medallion]
CMD [--help]
