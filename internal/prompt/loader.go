package prompt

import (
	"bytes"
	"fmt"
	"text/template"

	"github.com/Masterminds/sprig/v3"
)

// Loader handles loading and rendering prompts from YAML
type Loader struct {
	templates map[string]*template.Template
}

// NewLoader creates a new prompt loader
func NewLoader() *Loader {
	return &Loader{
		templates: make(map[string]*template.Template),
	}
}

// Prompt represents a prompt configuration
type Prompt struct {
	Name        string            `yaml:"name"`
	Description string            `yaml:"description"`
	Template    string            `yaml:"template"`
	Variables   map[string]string `yaml:"variables"`
	Guards      []Guard           `yaml:"guards"`
}

// Guard represents a conditional guard for prompt execution
type Guard struct {
	Condition string `yaml:"condition"`
	Message   string `yaml:"message"`
}

// LoadPrompt loads a prompt from YAML content
func (l *Loader) LoadPrompt(name, content string) error {
	// Parse YAML content (simplified - would use proper YAML parser)
	// For now, we'll assume the content is the template string directly

	tmpl, err := template.New(name).Funcs(sprig.TxtFuncMap()).Parse(content)
	if err != nil {
		return fmt.Errorf("failed to parse template: %w", err)
	}

	l.templates[name] = tmpl
	return nil
}

// RenderPrompt renders a prompt with the given variables
func (l *Loader) RenderPrompt(name string, variables map[string]interface{}) (string, error) {
	tmpl, exists := l.templates[name]
	if !exists {
		return "", fmt.Errorf("prompt template '%s' not found", name)
	}

	var buf bytes.Buffer
	if err := tmpl.Execute(&buf, variables); err != nil {
		return "", fmt.Errorf("failed to render template: %w", err)
	}

	return buf.String(), nil
}

// ValidateGuards validates prompt guards against variables
func (p *Prompt) ValidateGuards(variables map[string]interface{}) error {
	for _, guard := range p.Guards {
		// Simple guard validation (would need proper expression evaluator)
		// For now, just check if required variables exist
		if guard.Condition == "required" {
			// Check if all required variables are present
			for key := range p.Variables {
				if _, exists := variables[key]; !exists {
					return fmt.Errorf("guard validation failed: required variable '%s' not provided", key)
				}
			}
		}
	}
	return nil
}

// GetAvailablePrompts returns a list of available prompt names
func (l *Loader) GetAvailablePrompts() []string {
	names := make([]string, 0, len(l.templates))
	for name := range l.templates {
		names = append(names, name)
	}
	return names
}
