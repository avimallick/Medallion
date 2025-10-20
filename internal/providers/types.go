package providers

import (
	"context"
	"time"
)

// Provider defines the interface for LLM providers
type Provider interface {
	// Generate generates text using the LLM
	Generate(ctx context.Context, req *GenerateRequest) (*GenerateResponse, error)

	// GetEmbedding generates embeddings for text
	GetEmbedding(ctx context.Context, text string) ([]float64, error)

	// GetModelInfo returns information about the model
	GetModelInfo() *ModelInfo

	// Close closes the provider
	Close() error
}

// GenerateRequest represents a request to generate text
type GenerateRequest struct {
	Prompt       string            `json:"prompt"`
	SystemPrompt string            `json:"system_prompt,omitempty"`
	MaxTokens    int               `json:"max_tokens,omitempty"`
	Temperature  float64           `json:"temperature,omitempty"`
	TopP         float64           `json:"top_p,omitempty"`
	Stop         []string          `json:"stop,omitempty"`
	Metadata     map[string]string `json:"metadata,omitempty"`
}

// GenerateResponse represents the response from text generation
type GenerateResponse struct {
	Text         string            `json:"text"`
	TokensUsed   int               `json:"tokens_used"`
	FinishReason string            `json:"finish_reason"`
	Metadata     map[string]string `json:"metadata"`
}

// ModelInfo contains information about the model
type ModelInfo struct {
	Name               string    `json:"name"`
	Provider           string    `json:"provider"`
	MaxTokens          int       `json:"max_tokens"`
	ContextSize        int       `json:"context_size"`
	SupportsEmbeddings bool      `json:"supports_embeddings"`
	CreatedAt          time.Time `json:"created_at"`
}

// Config represents provider configuration
type Config struct {
	BaseURL    string            `json:"base_url"`
	APIKey     string            `json:"api_key"`
	Timeout    time.Duration     `json:"timeout"`
	Headers    map[string]string `json:"headers"`
	Model      string            `json:"model"`
	MaxRetries int               `json:"max_retries"`
}
