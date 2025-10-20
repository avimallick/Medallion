.PHONY: build lint test run install clean

# Build variables
BINARY_NAME=medallion
BUILD_DIR=bin
GO_FILES=$(shell find . -name "*.go" -not -path "./vendor/*")

# Default target
all: build

# Build the binary
build:
	@echo "Building $(BINARY_NAME)..."
	@mkdir -p $(BUILD_DIR)
	go build -o $(BUILD_DIR)/$(BINARY_NAME) ./cmd/medallion

# Install binary to GOPATH/bin
install: build
	@echo "Installing $(BINARY_NAME)..."
	go install ./cmd/medallion

# Run linter
lint:
	@echo "Running linter..."
	golangci-lint run
	gofumpt -l $(GO_FILES)

# Run tests
test:
	@echo "Running tests..."
	go test -v ./...

# Run with example workflow
run: build
	@echo "Running example workflow..."
	./$(BUILD_DIR)/$(BINARY_NAME) run --workflow examples/research_and_answer/workflow.yaml --var question="What is the capital of France?"

# Clean build artifacts
clean:
	@echo "Cleaning..."
	rm -rf $(BUILD_DIR)

# Format code
fmt:
	@echo "Formatting code..."
	gofumpt -w $(GO_FILES)

# Generate protobuf
proto:
	@echo "Generating protobuf..."
	protoc --go_out=. --go-grpc_out=. proto/medallion.proto

# Database migrations
migrate-up:
	@echo "Running database migrations..."
	goose -dir internal/kg/migrations sqlite3 medallion.db up

migrate-down:
	@echo "Rolling back database migrations..."
	goose -dir internal/kg/migrations sqlite3 medallion.db down

# Help
help:
	@echo "Available targets:"
	@echo "  build      - Build the binary"
	@echo "  install    - Install binary to GOPATH/bin"
	@echo "  lint       - Run linter"
	@echo "  test       - Run tests"
	@echo "  run        - Run with example workflow"
	@echo "  clean      - Clean build artifacts"
	@echo "  fmt        - Format code"
	@echo "  proto      - Generate protobuf"
	@echo "  migrate-up - Run database migrations"
	@echo "  migrate-down - Rollback database migrations"
