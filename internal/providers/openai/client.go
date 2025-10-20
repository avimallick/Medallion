package openai

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

// Client represents an OpenAI client
type Client struct {
	baseURL    string
	apiKey     string
	httpClient *http.Client
	model      string
}

// NewClient creates a new OpenAI client
func NewClient(config *providers.Config) *Client {
	return &Client{
		baseURL: config.BaseURL,
		apiKey:  config.APIKey,
		httpClient: &http.Client{
			Timeout: config.Timeout,
		},
		model: config.Model,
	}
}

// ChatCompletionRequest represents the OpenAI API request format
type ChatCompletionRequest struct {
	Model       string                  `json:"model"`
	Messages    []ChatCompletionMessage `json:"messages"`
	MaxTokens   int                     `json:"max_tokens,omitempty"`
	Temperature float64                 `json:"temperature,omitempty"`
	TopP        float64                 `json:"top_p,omitempty"`
	Stop        []string                `json:"stop,omitempty"`
}

// ChatCompletionMessage represents a message in the chat completion
type ChatCompletionMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// ChatCompletionResponse represents the OpenAI API response format
type ChatCompletionResponse struct {
	ID      string `json:"id"`
	Object  string `json:"object"`
	Created int64  `json:"created"`
	Model   string `json:"model"`
	Choices []struct {
		Index   int `json:"index"`
		Message struct {
			Role    string `json:"role"`
			Content string `json:"content"`
		} `json:"message"`
		FinishReason string `json:"finish_reason"`
	} `json:"choices"`
	Usage struct {
		PromptTokens     int `json:"prompt_tokens"`
		CompletionTokens int `json:"completion_tokens"`
		TotalTokens      int `json:"total_tokens"`
	} `json:"usage"`
}

// Generate implements the Provider interface
func (c *Client) Generate(ctx context.Context, req *providers.GenerateRequest) (*providers.GenerateResponse, error) {
	messages := []ChatCompletionMessage{}

	if req.SystemPrompt != "" {
		messages = append(messages, ChatCompletionMessage{
			Role:    "system",
			Content: req.SystemPrompt,
		})
	}

	messages = append(messages, ChatCompletionMessage{
		Role:    "user",
		Content: req.Prompt,
	})

	openaiReq := ChatCompletionRequest{
		Model:       c.model,
		Messages:    messages,
		MaxTokens:   req.MaxTokens,
		Temperature: req.Temperature,
		TopP:        req.TopP,
		Stop:        req.Stop,
	}

	jsonData, err := json.Marshal(openaiReq)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", c.baseURL+"/chat/completions", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+c.apiKey)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(body))
	}

	var openaiResp ChatCompletionResponse
	if err := json.NewDecoder(resp.Body).Decode(&openaiResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if len(openaiResp.Choices) == 0 {
		return nil, fmt.Errorf("no choices in response")
	}

	choice := openaiResp.Choices[0]

	return &providers.GenerateResponse{
		Text:         choice.Message.Content,
		TokensUsed:   openaiResp.Usage.TotalTokens,
		FinishReason: choice.FinishReason,
		Metadata: map[string]string{
			"model":             openaiResp.Model,
			"prompt_tokens":     fmt.Sprintf("%d", openaiResp.Usage.PromptTokens),
			"completion_tokens": fmt.Sprintf("%d", openaiResp.Usage.CompletionTokens),
		},
	}, nil
}

// GetEmbedding implements the Provider interface
func (c *Client) GetEmbedding(ctx context.Context, text string) ([]float64, error) {
	reqBody := map[string]interface{}{
		"model": "text-embedding-ada-002", // Default embedding model
		"input": text,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", c.baseURL+"/embeddings", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+c.apiKey)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(body))
	}

	var embeddingResp struct {
		Object string `json:"object"`
		Data   []struct {
			Object    string    `json:"object"`
			Index     int       `json:"index"`
			Embedding []float64 `json:"embedding"`
		} `json:"data"`
		Model string `json:"model"`
		Usage struct {
			PromptTokens int `json:"prompt_tokens"`
			TotalTokens  int `json:"total_tokens"`
		} `json:"usage"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&embeddingResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if len(embeddingResp.Data) == 0 {
		return nil, fmt.Errorf("no embedding data in response")
	}

	return embeddingResp.Data[0].Embedding, nil
}

// GetModelInfo implements the Provider interface
func (c *Client) GetModelInfo() *providers.ModelInfo {
	return &providers.ModelInfo{
		Name:               c.model,
		Provider:           "openai",
		MaxTokens:          4096, // Default, would need to be fetched from model info
		ContextSize:        4096,
		SupportsEmbeddings: true,
		CreatedAt:          time.Now(),
	}
}

// Close implements the Provider interface
func (c *Client) Close() error {
	// OpenAI client doesn't need explicit cleanup
	return nil
}
