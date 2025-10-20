package orchestrator

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/medallion-ai/medallion/internal/kg"
	"github.com/medallion-ai/medallion/internal/providers"
)

// Orchestrator manages workflow execution
type Orchestrator struct {
	kg        *kg.Driver
	providers map[string]providers.Provider
}

// NewOrchestrator creates a new orchestrator
func NewOrchestrator(kgDriver *kg.Driver) *Orchestrator {
	return &Orchestrator{
		kg:        kgDriver,
		providers: make(map[string]providers.Provider),
	}
}

// RegisterProvider registers a provider with the orchestrator
func (o *Orchestrator) RegisterProvider(name string, provider providers.Provider) {
	o.providers[name] = provider
}

// Workflow represents a workflow configuration
type Workflow struct {
	Name        string                 `yaml:"name"`
	Description string                 `yaml:"description"`
	Agents      []string               `yaml:"agents"`
	Steps       []WorkflowStep         `yaml:"steps"`
	Variables   map[string]interface{} `yaml:"variables"`
}

// WorkflowStep represents a step in a workflow
type WorkflowStep struct {
	Name        string   `yaml:"name"`
	Agent       string   `yaml:"agent"`
	Input       string   `yaml:"input"`
	DependsOn   []string `yaml:"depends_on"`
	SuccessWhen string   `yaml:"success_when"`
}

// ExecutionResult represents the result of workflow execution
type ExecutionResult struct {
	RunID     string                 `json:"run_id"`
	Status    string                 `json:"status"`
	StartTime time.Time              `json:"start_time"`
	EndTime   *time.Time             `json:"end_time"`
	Duration  *time.Duration         `json:"duration"`
	Steps     map[string]StepResult  `json:"steps"`
	Output    map[string]interface{} `json:"output"`
	Error     string                 `json:"error,omitempty"`
}

// StepResult represents the result of a workflow step
type StepResult struct {
	Name      string                 `json:"name"`
	Agent     string                 `json:"agent"`
	Status    string                 `json:"status"`
	Input     string                 `json:"input"`
	Output    string                 `json:"output"`
	StartTime time.Time              `json:"start_time"`
	EndTime   *time.Time             `json:"end_time"`
	Duration  *time.Duration         `json:"duration"`
	Error     string                 `json:"error,omitempty"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// ExecuteWorkflow executes a workflow
func (o *Orchestrator) ExecuteWorkflow(ctx context.Context, workflow *Workflow, variables map[string]interface{}) (*ExecutionResult, error) {
	runID := fmt.Sprintf("RUN_%d", time.Now().Unix())

	result := &ExecutionResult{
		RunID:     runID,
		Status:    "running",
		StartTime: time.Now(),
		Steps:     make(map[string]StepResult),
		Output:    make(map[string]interface{}),
	}

	// Create run record in knowledge graph
	run := &kg.Run{
		ID:           runID,
		WorkflowName: workflow.Name,
		Status:       "running",
		InputData:    fmt.Sprintf("%v", variables),
		Metadata:     fmt.Sprintf("%v", workflow.Variables),
	}

	if err := o.kg.CreateRun(run); err != nil {
		return nil, fmt.Errorf("failed to create run record: %w", err)
	}

	// Execute steps in dependency order
	executedSteps := make(map[string]bool)
	stepResults := make(map[string]StepResult)

	for len(executedSteps) < len(workflow.Steps) {
		progress := false

		for _, step := range workflow.Steps {
			if executedSteps[step.Name] {
				continue
			}

			// Check if dependencies are satisfied
			if !o.areDependenciesSatisfied(step.DependsOn, executedSteps) {
				continue
			}

			// Execute step
			stepResult, err := o.executeStep(ctx, runID, step, variables, stepResults)
			if err != nil {
				result.Status = "failed"
				result.Error = err.Error()
				endTime := time.Now()
				result.EndTime = &endTime
				duration := endTime.Sub(result.StartTime)
				result.Duration = &duration

				// Update run status
				o.kg.UpdateRunStatus(runID, "failed", "", err.Error())
				return result, err
			}

			stepResults[step.Name] = stepResult
			result.Steps[step.Name] = stepResult
			executedSteps[step.Name] = true
			progress = true
		}

		if !progress {
			return nil, fmt.Errorf("workflow execution stalled - circular dependency or missing step")
		}
	}

	// Mark workflow as completed
	result.Status = "completed"
	endTime := time.Now()
	result.EndTime = &endTime
	duration := endTime.Sub(result.StartTime)
	result.Duration = &duration

	// Update run status
	o.kg.UpdateRunStatus(runID, "completed", fmt.Sprintf("%v", result.Output), "")

	return result, nil
}

func (o *Orchestrator) areDependenciesSatisfied(dependencies []string, executedSteps map[string]bool) bool {
	for _, dep := range dependencies {
		if !executedSteps[dep] {
			return false
		}
	}
	return true
}

func (o *Orchestrator) executeStep(ctx context.Context, runID string, step WorkflowStep, variables map[string]interface{}, stepResults map[string]StepResult) (StepResult, error) {
	stepResult := StepResult{
		Name:      step.Name,
		Agent:     step.Agent,
		Status:    "running",
		StartTime: time.Now(),
		Metadata:  make(map[string]interface{}),
	}

	// Get agent from knowledge graph
	agent, err := o.kg.GetAgent(step.Agent)
	if err != nil {
		stepResult.Status = "failed"
		stepResult.Error = fmt.Sprintf("failed to get agent: %v", err)
		return stepResult, err
	}

	// Prepare input by substituting variables
	input := o.substituteVariables(step.Input, variables, stepResults)

	// Get provider for agent
	provider, exists := o.providers[agent.ModelProvider]
	if !exists {
		stepResult.Status = "failed"
		stepResult.Error = fmt.Sprintf("provider '%s' not found", agent.ModelProvider)
		return stepResult, err
	}

	// Generate response using provider
	generateReq := &providers.GenerateRequest{
		Prompt:       input,
		SystemPrompt: agent.SystemPrompt,
		Temperature:  0.7,
		MaxTokens:    1000,
	}

	resp, err := provider.Generate(ctx, generateReq)
	if err != nil {
		stepResult.Status = "failed"
		stepResult.Error = fmt.Sprintf("failed to generate response: %v", err)
		return stepResult, err
	}

	// Update step result
	stepResult.Status = "completed"
	stepResult.Output = resp.Text
	endTime := time.Now()
	stepResult.EndTime = &endTime
	duration := endTime.Sub(stepResult.StartTime)
	stepResult.Duration = &duration
	stepResult.Metadata["tokens_used"] = resp.TokensUsed
	stepResult.Metadata["finish_reason"] = resp.FinishReason

	// Create artifact in knowledge graph
	artifact := &kg.Artifact{
		ID:          fmt.Sprintf("ART_%s_%d", step.Name, time.Now().Unix()),
		RunID:       runID,
		StepName:    step.Name,
		AgentID:     agent.ID,
		Content:     resp.Text,
		ContentType: "text/plain",
		Metadata:    fmt.Sprintf("%v", stepResult.Metadata),
	}

	if err := o.kg.CreateArtifact(artifact); err != nil {
		// Log error but don't fail the step
		fmt.Printf("Warning: failed to create artifact: %v\n", err)
	}

	return stepResult, nil
}

func (o *Orchestrator) substituteVariables(input string, variables map[string]interface{}, stepResults map[string]StepResult) string {
	result := input

	// Substitute workflow variables
	for key, value := range variables {
		placeholder := fmt.Sprintf("{{.%s}}", key)
		valueStr := fmt.Sprintf("%v", value)
		result = strings.ReplaceAll(result, placeholder, valueStr)
	}

	// Substitute step outputs
	for stepName, stepResult := range stepResults {
		placeholder := fmt.Sprintf("{{.%s.output}}", stepName)
		result = strings.ReplaceAll(result, placeholder, stepResult.Output)
	}

	return result
}
