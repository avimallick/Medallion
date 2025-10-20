package ollama

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/medallion-ai/medallion/internal/providers"
)

// Client represents an Ollama client
type Client struct {
	baseURL    string
	httpClient *http.Client
	model      string
}

// NewClient creates a new Ollama client
func NewClient(config *providers.Config) *Client {
	return &Client{
		baseURL: config.BaseURL,
		httpClient: &http.Client{
			Timeout: config.Timeout,
		},
		model: config.Model,
	}
}

// GenerateRequest represents the Ollama API request format
type GenerateRequest struct {
	Model   string                 `json:"model"`
	Prompt  string                 `json:"prompt"`
	System  string                 `json:"system,omitempty"`
	Stream  bool                   `json:"stream"`
	Options map[string]interface{} `json:"options,omitempty"`
}

// GenerateResponse represents the Ollama API response format
type GenerateResponse struct {
	Model              string `json:"model"`
	CreatedAt          string `json:"created_at"`
	Response           string `json:"response"`
	Done               bool   `json:"done"`
	Context            []int  `json:"context,omitempty"`
	TotalDuration      int64  `json:"total_duration,omitempty"`
	LoadDuration       int64  `json:"load_duration,omitempty"`
	PromptEvalCount    int    `json:"prompt_eval_count,omitempty"`
	PromptEvalDuration int64  `json:"prompt_eval_duration,omitempty"`
	EvalCount          int    `json:"eval_count,omitempty"`
	EvalDuration       int64  `json:"eval_duration,omitempty"`
}

// Generate implements the Provider interface
func (c *Client) Generate(ctx context.Context, req *providers.GenerateRequest) (*providers.GenerateResponse, error) {
	ollamaReq := GenerateRequest{
		Model:  c.model,
		Prompt: req.Prompt,
		System: req.SystemPrompt,
		Stream: false,
		Options: map[string]interface{}{
			"temperature": req.Temperature,
			"top_p":       req.TopP,
		},
	}

	jsonData, err := json.Marshal(ollamaReq)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", c.baseURL+"/api/generate", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(body))
	}

	var ollamaResp GenerateResponse
	if err := json.NewDecoder(resp.Body).Decode(&ollamaResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &providers.GenerateResponse{
		Text:         ollamaResp.Response,
		TokensUsed:   ollamaResp.EvalCount,
		FinishReason: "stop",
		Metadata: map[string]string{
			"model":          ollamaResp.Model,
			"total_duration": fmt.Sprintf("%d", ollamaResp.TotalDuration),
			"eval_duration":  fmt.Sprintf("%d", ollamaResp.EvalDuration),
		},
	}, nil
}

// GetEmbedding implements the Provider interface
func (c *Client) GetEmbedding(ctx context.Context, text string) ([]float64, error) {
	// Ollama doesn't have a direct embedding endpoint in the same way
	// This would need to be implemented based on the specific model
	// For now, return an error indicating it's not supported
	return nil, fmt.Errorf("embeddings not supported by Ollama provider")
}

// GetModelInfo implements the Provider interface
func (c *Client) GetModelInfo() *providers.ModelInfo {
	return &providers.ModelInfo{
		Name:               c.model,
		Provider:           "ollama",
		MaxTokens:          4096, // Default, would need to be fetched from model info
		ContextSize:        4096,
		SupportsEmbeddings: false,
		CreatedAt:          time.Now(),
	}
}

// Close implements the Provider interface
func (c *Client) Close() error {
	// Ollama client doesn't need explicit cleanup
	return nil
}
