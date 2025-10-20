package cli

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/cobra"
)

// NewBuildCommand creates the build command for project scaffolding
func NewBuildCommand() *cobra.Command {
	var template string
	var outputDir string

	cmd := &cobra.Command{
		Use:   "build [template] [app-name]",
		Short: "Generate project scaffold with agents, configs, and prompts",
		Long: `Build generates a complete project scaffold based on the specified template.
Available templates:
  1+4: Basic scaffold with 1 planner agent and 4 worker agents
  research: Research-focused workflow with retriever and writer agents
  chat: Simple chat interface with single agent`,
		Args: cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			template = args[0]
			appName := args[1]

			if outputDir == "" {
				outputDir = appName
			}

			return buildProject(template, appName, outputDir)
		},
	}

	cmd.Flags().StringVarP(&outputDir, "output", "o", "", "Output directory (default: app-name)")

	return cmd
}

func buildProject(template, appName, outputDir string) error {
	fmt.Printf("Building project '%s' with template '%s' in directory '%s'\n", appName, template, outputDir)

	// Create output directory
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Generate scaffold based on template
	switch template {
	case "1+4":
		return generateBasicScaffold(appName, outputDir)
	case "research":
		return generateResearchScaffold(appName, outputDir)
	case "chat":
		return generateChatScaffold(appName, outputDir)
	default:
		return fmt.Errorf("unknown template: %s", template)
	}
}

func generateBasicScaffold(appName, outputDir string) error {
	// Create directory structure
	dirs := []string{
		"agents",
		"configs",
		"prompts",
		"workflows",
		"data",
	}

	for _, dir := range dirs {
		if err := os.MkdirAll(filepath.Join(outputDir, dir), 0755); err != nil {
			return fmt.Errorf("failed to create %s directory: %w", dir, err)
		}
	}

	// Generate planner agent config
	plannerConfig := `name: planner
type: planner
description: "Main planning agent that breaks down tasks"
model:
  provider: ollama
  model: llama3.1
prompts:
  system: "You are a task planning agent. Break down complex tasks into smaller, manageable steps."
tools: []
`

	if err := os.WriteFile(filepath.Join(outputDir, "agents", "planner.yaml"), []byte(plannerConfig), 0644); err != nil {
		return fmt.Errorf("failed to create planner config: %w", err)
	}

	// Generate worker agents
	workerConfigs := []struct {
		name string
		desc string
	}{
		{"researcher", "Agent that researches and gathers information"},
		{"analyzer", "Agent that analyzes data and extracts insights"},
		{"writer", "Agent that writes and formats content"},
		{"reviewer", "Agent that reviews and validates outputs"},
	}

	for _, worker := range workerConfigs {
		config := fmt.Sprintf(`name: %s
type: worker
description: "%s"
model:
  provider: ollama
  model: llama3.1
prompts:
  system: "You are a %s agent. %s"
tools: []
`, worker.name, worker.desc, worker.name, worker.desc)

		if err := os.WriteFile(filepath.Join(outputDir, "agents", worker.name+".yaml"), []byte(config), 0644); err != nil {
			return fmt.Errorf("failed to create %s config: %w", worker.name, err)
		}
	}

	// Generate main workflow
	workflow := `name: main_workflow
description: "Main workflow for the application"
agents:
  - planner
  - researcher
  - analyzer
  - writer
  - reviewer
steps:
  - name: plan
    agent: planner
    input: "{{.input}}"
  - name: research
    agent: researcher
    depends_on: [plan]
    input: "{{.plan.output}}"
  - name: analyze
    agent: analyzer
    depends_on: [research]
    input: "{{.research.output}}"
  - name: write
    agent: writer
    depends_on: [analyze]
    input: "{{.analyze.output}}"
  - name: review
    agent: reviewer
    depends_on: [write]
    input: "{{.write.output}}"
`

	if err := os.WriteFile(filepath.Join(outputDir, "workflows", "main.yaml"), []byte(workflow), 0644); err != nil {
		return fmt.Errorf("failed to create workflow: %w", err)
	}

	// Generate config file
	config := `app:
  name: "` + appName + `"
  version: "1.0.0"

database:
  type: sqlite
  path: "./medallion.db"

providers:
  ollama:
    base_url: "http://localhost:11434"
    timeout: 30s
  openai:
    api_key: "${OPENAI_API_KEY}"
    base_url: "https://api.openai.com/v1"
    timeout: 30s

logging:
  level: info
  format: json
`

	if err := os.WriteFile(filepath.Join(outputDir, "config.yaml"), []byte(config), 0644); err != nil {
		return fmt.Errorf("failed to create config: %w", err)
	}

	fmt.Printf("✅ Project scaffold generated successfully in '%s'\n", outputDir)
	fmt.Println("Next steps:")
	fmt.Printf("  1. cd %s\n", outputDir)
	fmt.Println("  2. Configure your agents in the agents/ directory")
	fmt.Println("  3. Update config.yaml with your settings")
	fmt.Println("  4. Run: medallion run --workflow workflows/main.yaml --var input='your input here'")

	return nil
}

func generateResearchScaffold(appName, outputDir string) error {
	// Similar implementation for research-focused scaffold
	return generateBasicScaffold(appName, outputDir) // Simplified for now
}

func generateChatScaffold(appName, outputDir string) error {
	// Similar implementation for chat-focused scaffold
	return generateBasicScaffold(appName, outputDir) // Simplified for now
}
