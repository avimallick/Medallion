package kg

import (
	"database/sql"
	"fmt"
	"time"

	_ "modernc.org/sqlite"
)

// Driver represents the knowledge graph database driver
type Driver struct {
	db *sql.DB
}

// NewDriver creates a new knowledge graph driver
func NewDriver(dbPath string) (*Driver, error) {
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	driver := &Driver{db: db}

	// Initialize schema
	if err := driver.initSchema(); err != nil {
		return nil, fmt.Errorf("failed to initialize schema: %w", err)
	}

	return driver, nil
}

// Close closes the database connection
func (d *Driver) Close() error {
	return d.db.Close()
}

// initSchema initializes the knowledge graph schema
func (d *Driver) initSchema() error {
	schema := `
	-- Agents table
	CREATE TABLE IF NOT EXISTS agents (
		id TEXT PRIMARY KEY,
		name TEXT NOT NULL,
		type TEXT NOT NULL,
		description TEXT,
		model_provider TEXT,
		model_name TEXT,
		system_prompt TEXT,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
	);

	-- Claims table (assertions made by agents)
	CREATE TABLE IF NOT EXISTS claims (
		id TEXT PRIMARY KEY,
		agent_id TEXT NOT NULL,
		run_id TEXT NOT NULL,
		content TEXT NOT NULL,
		confidence REAL DEFAULT 1.0,
		metadata TEXT, -- JSON metadata
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (agent_id) REFERENCES agents(id),
		FOREIGN KEY (run_id) REFERENCES runs(id)
	);

	-- Runs table (workflow executions)
	CREATE TABLE IF NOT EXISTS runs (
		id TEXT PRIMARY KEY,
		workflow_name TEXT NOT NULL,
		status TEXT NOT NULL DEFAULT 'running',
		input_data TEXT, -- JSON input
		output_data TEXT, -- JSON output
		started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		completed_at DATETIME,
		duration_ms INTEGER,
		error_message TEXT,
		metadata TEXT -- JSON metadata
	);

	-- Artifacts table (outputs from workflow steps)
	CREATE TABLE IF NOT EXISTS artifacts (
		id TEXT PRIMARY KEY,
		run_id TEXT NOT NULL,
		step_name TEXT NOT NULL,
		agent_id TEXT NOT NULL,
		content TEXT NOT NULL,
		content_type TEXT DEFAULT 'text/plain',
		metadata TEXT, -- JSON metadata
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (run_id) REFERENCES runs(id),
		FOREIGN KEY (agent_id) REFERENCES agents(id)
	);

	-- Relationships table (for graph connections)
	CREATE TABLE IF NOT EXISTS relationships (
		id TEXT PRIMARY KEY,
		source_type TEXT NOT NULL, -- 'agent', 'claim', 'artifact', etc.
		source_id TEXT NOT NULL,
		target_type TEXT NOT NULL,
		target_id TEXT NOT NULL,
		relationship_type TEXT NOT NULL,
		metadata TEXT, -- JSON metadata
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP
	);

	-- Spans table (for tracing)
	CREATE TABLE IF NOT EXISTS spans (
		id TEXT PRIMARY KEY,
		run_id TEXT NOT NULL,
		parent_span_id TEXT,
		name TEXT NOT NULL,
		start_time DATETIME NOT NULL,
		end_time DATETIME,
		duration_ms INTEGER,
		status TEXT DEFAULT 'running',
		metadata TEXT, -- JSON metadata including costs, tokens, etc.
		FOREIGN KEY (run_id) REFERENCES runs(id)
	);

	-- Create indexes for better performance
	CREATE INDEX IF NOT EXISTS idx_claims_agent_id ON claims(agent_id);
	CREATE INDEX IF NOT EXISTS idx_claims_run_id ON claims(run_id);
	CREATE INDEX IF NOT EXISTS idx_artifacts_run_id ON artifacts(run_id);
	CREATE INDEX IF NOT EXISTS idx_artifacts_agent_id ON artifacts(agent_id);
	CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_type, source_id);
	CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_type, target_id);
	CREATE INDEX IF NOT EXISTS idx_spans_run_id ON spans(run_id);
	CREATE INDEX IF NOT EXISTS idx_spans_parent ON spans(parent_span_id);
	`

	_, err := d.db.Exec(schema)
	return err
}

// Agent represents an AI agent in the knowledge graph
type Agent struct {
	ID            string    `json:"id"`
	Name          string    `json:"name"`
	Type          string    `json:"type"`
	Description   string    `json:"description"`
	ModelProvider string    `json:"model_provider"`
	ModelName     string    `json:"model_name"`
	SystemPrompt  string    `json:"system_prompt"`
	CreatedAt     time.Time `json:"created_at"`
	UpdatedAt     time.Time `json:"updated_at"`
}

// Claim represents an assertion made by an agent
type Claim struct {
	ID         string    `json:"id"`
	AgentID    string    `json:"agent_id"`
	RunID      string    `json:"run_id"`
	Content    string    `json:"content"`
	Confidence float64   `json:"confidence"`
	Metadata   string    `json:"metadata"`
	CreatedAt  time.Time `json:"created_at"`
}

// Run represents a workflow execution
type Run struct {
	ID           string     `json:"id"`
	WorkflowName string     `json:"workflow_name"`
	Status       string     `json:"status"`
	InputData    string     `json:"input_data"`
	OutputData   string     `json:"output_data"`
	StartedAt    time.Time  `json:"started_at"`
	CompletedAt  *time.Time `json:"completed_at"`
	DurationMs   *int       `json:"duration_ms"`
	ErrorMessage string     `json:"error_message"`
	Metadata     string     `json:"metadata"`
}

// Artifact represents an output from a workflow step
type Artifact struct {
	ID          string    `json:"id"`
	RunID       string    `json:"run_id"`
	StepName    string    `json:"step_name"`
	AgentID     string    `json:"agent_id"`
	Content     string    `json:"content"`
	ContentType string    `json:"content_type"`
	Metadata    string    `json:"metadata"`
	CreatedAt   time.Time `json:"created_at"`
}

// Span represents a tracing span
type Span struct {
	ID           string     `json:"id"`
	RunID        string     `json:"run_id"`
	ParentSpanID string     `json:"parent_span_id"`
	Name         string     `json:"name"`
	StartTime    time.Time  `json:"start_time"`
	EndTime      *time.Time `json:"end_time"`
	DurationMs   *int       `json:"duration_ms"`
	Status       string     `json:"status"`
	Metadata     string     `json:"metadata"`
}

// CreateAgent creates a new agent in the knowledge graph
func (d *Driver) CreateAgent(agent *Agent) error {
	query := `
		INSERT INTO agents (id, name, type, description, model_provider, model_name, system_prompt)
		VALUES (?, ?, ?, ?, ?, ?, ?)
	`
	_, err := d.db.Exec(query, agent.ID, agent.Name, agent.Type, agent.Description,
		agent.ModelProvider, agent.ModelName, agent.SystemPrompt)
	return err
}

// GetAgent retrieves an agent by ID
func (d *Driver) GetAgent(id string) (*Agent, error) {
	query := `
		SELECT id, name, type, description, model_provider, model_name, system_prompt, created_at, updated_at
		FROM agents WHERE id = ?
	`
	row := d.db.QueryRow(query, id)

	agent := &Agent{}
	err := row.Scan(&agent.ID, &agent.Name, &agent.Type, &agent.Description,
		&agent.ModelProvider, &agent.ModelName, &agent.SystemPrompt,
		&agent.CreatedAt, &agent.UpdatedAt)
	if err != nil {
		return nil, err
	}

	return agent, nil
}

// CreateRun creates a new workflow run
func (d *Driver) CreateRun(run *Run) error {
	query := `
		INSERT INTO runs (id, workflow_name, status, input_data, metadata)
		VALUES (?, ?, ?, ?, ?)
	`
	_, err := d.db.Exec(query, run.ID, run.WorkflowName, run.Status, run.InputData, run.Metadata)
	return err
}

// UpdateRunStatus updates the status of a run
func (d *Driver) UpdateRunStatus(runID, status string, outputData string, errorMessage string) error {
	query := `
		UPDATE runs 
		SET status = ?, output_data = ?, error_message = ?, completed_at = CURRENT_TIMESTAMP,
		    duration_ms = (strftime('%s', 'now') * 1000) - (strftime('%s', started_at) * 1000)
		WHERE id = ?
	`
	_, err := d.db.Exec(query, status, outputData, errorMessage, runID)
	return err
}

// CreateClaim creates a new claim
func (d *Driver) CreateClaim(claim *Claim) error {
	query := `
		INSERT INTO claims (id, agent_id, run_id, content, confidence, metadata)
		VALUES (?, ?, ?, ?, ?, ?)
	`
	_, err := d.db.Exec(query, claim.ID, claim.AgentID, claim.RunID, claim.Content, claim.Confidence, claim.Metadata)
	return err
}

// CreateArtifact creates a new artifact
func (d *Driver) CreateArtifact(artifact *Artifact) error {
	query := `
		INSERT INTO artifacts (id, run_id, step_name, agent_id, content, content_type, metadata)
		VALUES (?, ?, ?, ?, ?, ?, ?)
	`
	_, err := d.db.Exec(query, artifact.ID, artifact.RunID, artifact.StepName, artifact.AgentID,
		artifact.Content, artifact.ContentType, artifact.Metadata)
	return err
}

// CreateSpan creates a new tracing span
func (d *Driver) CreateSpan(span *Span) error {
	query := `
		INSERT INTO spans (id, run_id, parent_span_id, name, start_time, status, metadata)
		VALUES (?, ?, ?, ?, ?, ?, ?)
	`
	_, err := d.db.Exec(query, span.ID, span.RunID, span.ParentSpanID, span.Name, span.StartTime, span.Status, span.Metadata)
	return err
}

// UpdateSpan updates a tracing span
func (d *Driver) UpdateSpan(spanID string, endTime time.Time, status string, metadata string) error {
	duration := int(time.Until(endTime).Milliseconds())
	query := `
		UPDATE spans 
		SET end_time = ?, duration_ms = ?, status = ?, metadata = ?
		WHERE id = ?
	`
	_, err := d.db.Exec(query, endTime, duration, status, metadata, spanID)
	return err
}

// Query executes a simple query against the knowledge graph
func (d *Driver) Query(query string, args ...interface{}) (*sql.Rows, error) {
	return d.db.Query(query, args...)
}
