package kg

import (
	"fmt"
	"strings"
)

// QueryParser parses Cypher-like queries and converts them to SQL
type QueryParser struct{}

// NewQueryParser creates a new query parser
func NewQueryParser() *QueryParser {
	return &QueryParser{}
}

// ParseQuery converts a Cypher-like query to SQL
func (p *QueryParser) ParseQuery(cypherQuery string) (string, error) {
	// Simple implementation for basic queries
	// In a full implementation, this would use a proper parser

	query := strings.TrimSpace(cypherQuery)
	query = strings.ToUpper(query)

	// Handle MATCH queries
	if strings.HasPrefix(query, "MATCH") {
		return p.parseMatchQuery(cypherQuery)
	}

	// Handle simple SELECT queries
	if strings.HasPrefix(query, "SELECT") {
		return cypherQuery, nil // Already SQL
	}

	return "", fmt.Errorf("unsupported query type: %s", query)
}

func (p *QueryParser) parseMatchQuery(query string) (string, error) {
	// Basic MATCH to SELECT conversion
	// This is a simplified implementation

	// Example: MATCH (n:Claim) RETURN COUNT(n)
	if strings.Contains(query, "COUNT") {
		return p.parseCountQuery(query)
	}

	// Example: MATCH (n:Agent) WHERE n.name = "planner" RETURN n
	if strings.Contains(query, "WHERE") {
		return p.parseWhereQuery(query)
	}

	// Example: MATCH (n:Claim) RETURN n
	return p.parseSimpleMatchQuery(query)
}

func (p *QueryParser) parseCountQuery(query string) (string, error) {
	// Extract entity type from MATCH clause
	// MATCH (n:Claim) RETURN COUNT(n) -> SELECT COUNT(*) FROM claims
	if strings.Contains(query, ":Claim") {
		return "SELECT COUNT(*) FROM claims", nil
	}
	if strings.Contains(query, ":Agent") {
		return "SELECT COUNT(*) FROM agents", nil
	}
	if strings.Contains(query, ":Run") {
		return "SELECT COUNT(*) FROM runs", nil
	}
	if strings.Contains(query, ":Artifact") {
		return "SELECT COUNT(*) FROM artifacts", nil
	}

	return "", fmt.Errorf("unsupported entity type in COUNT query")
}

func (p *QueryParser) parseWhereQuery(query string) (string, error) {
	// Extract entity type and WHERE conditions
	// MATCH (n:Agent) WHERE n.name = "planner" RETURN n -> SELECT * FROM agents WHERE name = 'planner'

	if strings.Contains(query, ":Agent") {
		// Extract WHERE condition
		whereStart := strings.Index(query, "WHERE")
		if whereStart == -1 {
			return "", fmt.Errorf("WHERE clause not found")
		}

		whereClause := query[whereStart+5:] // Skip "WHERE"
		whereClause = strings.TrimSpace(whereClause)
		whereClause = strings.ReplaceAll(whereClause, "n.", "")
		whereClause = strings.ReplaceAll(whereClause, "\"", "'")

		return fmt.Sprintf("SELECT * FROM agents WHERE %s", whereClause), nil
	}

	return "", fmt.Errorf("unsupported entity type in WHERE query")
}

func (p *QueryParser) parseSimpleMatchQuery(query string) (string, error) {
	// MATCH (n:Claim) RETURN n -> SELECT * FROM claims
	if strings.Contains(query, ":Claim") {
		return "SELECT * FROM claims", nil
	}
	if strings.Contains(query, ":Agent") {
		return "SELECT * FROM agents", nil
	}
	if strings.Contains(query, ":Run") {
		return "SELECT * FROM runs", nil
	}
	if strings.Contains(query, ":Artifact") {
		return "SELECT * FROM artifacts", nil
	}

	return "", fmt.Errorf("unsupported entity type in simple MATCH query")
}
