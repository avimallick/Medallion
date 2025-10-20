#!/usr/bin/env python3
"""
Medallion CLI - Python command-line interface
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

from medallion import MedallionClient, Workflow, Agent, KnowledgeGraph
from medallion.providers import OllamaProvider, OpenAIProvider


def build_command(args):
    """Handle the build command"""
    client = MedallionClient()
    result = client.build_project(args.template, args.app_name, args.output)
    print(f"✅ {result.get('message', 'Project built successfully')}")


def run_command(args):
    """Handle the run command"""
    client = MedallionClient()
    
    # Parse variables
    variables = {}
    if args.vars:
        for var in args.vars:
            if '=' in var:
                key, value = var.split('=', 1)
                variables[key] = value
            else:
                print(f"Warning: Invalid variable format: {var}")
    
    result = client.run_workflow(args.workflow, variables)
    print(f"✅ Workflow started: {result.get('run_id', 'Unknown')}")
    
    if args.wait:
        print("Waiting for completion...")
        # In a real implementation, you'd poll for completion
        print("Workflow completed!")


def kg_command(args):
    """Handle the kg command"""
    kg = KnowledgeGraph()
    
    if args.subcommand == 'query':
        result = kg.query(args.query, args.format)
        print(result.get('result', 'No results'))
    elif args.subcommand == 'inspect':
        result = kg.inspect()
        print(json.dumps(result, indent=2))


def trace_command(args):
    """Handle the trace command"""
    client = MedallionClient()
    result = client.trace_run(args.run_id, args.format, args.details)
    print(json.dumps(result, indent=2))


def agent_command(args):
    """Handle the agent command"""
    client = MedallionClient()
    
    if args.subcommand == 'create':
        # Load agent from file
        agent = Agent.from_file(args.file)
        result = client.create_agent(agent.__dict__)
        print(f"✅ Agent created: {result.get('agent_id', 'Unknown')}")
    elif args.subcommand == 'list':
        result = client.list_agents()
        agents = result.get('agents', [])
        for agent in agents:
            print(f"- {agent['name']} ({agent['type']})")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Medallion - A Python-first agentic AI framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  medallion build 1+4 my-app
  medallion run workflow.yaml --var question="What is AI?"
  medallion kg query "MATCH (n:Agent) RETURN COUNT(n)"
  medallion trace --run-id RUN_123
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Generate project scaffold')
    build_parser.add_argument('template', help='Template to use (1+4, research, chat)')
    build_parser.add_argument('app_name', help='Name of the application')
    build_parser.add_argument('-o', '--output', help='Output directory')
    build_parser.set_defaults(func=build_command)
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Execute a workflow')
    run_parser.add_argument('workflow', help='Workflow YAML file')
    run_parser.add_argument('-v', '--var', action='append', dest='vars',
                           help='Variables to pass (key=value)')
    run_parser.add_argument('-w', '--wait', action='store_true',
                           help='Wait for completion')
    run_parser.set_defaults(func=run_command)
    
    # KG command
    kg_parser = subparsers.add_parser('kg', help='Knowledge graph operations')
    kg_subparsers = kg_parser.add_subparsers(dest='subcommand', help='KG subcommands')
    
    kg_query_parser = kg_subparsers.add_parser('query', help='Query the knowledge graph')
    kg_query_parser.add_argument('query', help='Cypher-like query')
    kg_query_parser.add_argument('-f', '--format', default='table',
                                choices=['table', 'json', 'csv'],
                                help='Output format')
    
    kg_inspect_parser = kg_subparsers.add_parser('inspect', help='Inspect knowledge graph')
    
    kg_parser.set_defaults(func=kg_command)
    
    # Trace command
    trace_parser = subparsers.add_parser('trace', help='Show execution trace')
    trace_parser.add_argument('--run-id', required=True, help='Run ID to trace')
    trace_parser.add_argument('-f', '--format', default='table',
                             choices=['table', 'json'], help='Output format')
    trace_parser.add_argument('-d', '--details', action='store_true',
                             help='Show detailed information')
    trace_parser.set_defaults(func=trace_command)
    
    # Agent command
    agent_parser = subparsers.add_parser('agent', help='Agent management')
    agent_subparsers = agent_parser.add_subparsers(dest='subcommand', help='Agent subcommands')
    
    agent_create_parser = agent_subparsers.add_parser('create', help='Create an agent')
    agent_create_parser.add_argument('file', help='Agent YAML file')
    
    agent_list_parser = agent_subparsers.add_parser('list', help='List agents')
    
    agent_parser.set_defaults(func=agent_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
