package cli

import (
	"github.com/spf13/cobra"
)

// NewRootCommand creates the root command for the Medallion CLI
func NewRootCommand() *cobra.Command {
	rootCmd := &cobra.Command{
		Use:   "medallion",
		Short: "Medallion CLI - A Go-first agentic AI framework",
		Long: `Medallion is a Go-first agentic AI framework where a Knowledge Graph (KG) 
is the source of truth. It ships as a CLI with a Python wrapper and provides
graph-native runtime, provider-agnostic LLM abstraction, and project scaffolding.`,
	}

	// Add subcommands
	rootCmd.AddCommand(NewBuildCommand())
	rootCmd.AddCommand(NewRunCommand())
	rootCmd.AddCommand(NewKGCommand())
	rootCmd.AddCommand(NewTraceCommand())

	return rootCmd
}
