-- HITL Infrastructure: Initial Schema Migration
-- Creates the three tables for the human review gate state machine.
--
-- To apply: psql -d keystone -f 001_create_hitl_tables.sql
-- To rollback: see DROP statements at the bottom.
--
-- Note: SQLAlchemy's Base.metadata.create_all() also creates these tables
-- automatically in dev/test. This migration is for production deployments
-- and explicit schema versioning.

BEGIN;

-- 1. Review Gates: pipeline checkpoints awaiting human decision
CREATE TABLE IF NOT EXISTS review_gates (
    id              VARCHAR     PRIMARY KEY,
    engagement_id   VARCHAR     NOT NULL,
    client_id       VARCHAR     NOT NULL,
    gate_type       VARCHAR     NOT NULL,   -- 'post_specification' | 'post_deliberation'
    status          VARCHAR     NOT NULL DEFAULT 'pending',  -- 'pending' | 'approved' | 'modified' | 'rejected'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at     TIMESTAMPTZ,
    resolved_by     VARCHAR,

    CONSTRAINT ck_gate_type CHECK (gate_type IN ('post_specification', 'post_deliberation')),
    CONSTRAINT ck_gate_status CHECK (status IN ('pending', 'approved', 'modified', 'rejected'))
);

CREATE INDEX IF NOT EXISTS ix_review_gates_engagement_id
    ON review_gates (engagement_id);
CREATE INDEX IF NOT EXISTS ix_review_gates_engagement_gate_type
    ON review_gates (engagement_id, gate_type);
CREATE INDEX IF NOT EXISTS ix_review_gates_status
    ON review_gates (status);

-- 2. Review Items: artifacts presented for human review
CREATE TABLE IF NOT EXISTS review_items (
    id              VARCHAR     PRIMARY KEY,
    gate_id         VARCHAR     NOT NULL REFERENCES review_gates(id) ON DELETE CASCADE,
    item_type       VARCHAR     NOT NULL,   -- 'issue_tree' | 'agent_config' | 'confidence_map' | 'divergence_points' | 'sprint_contract'
    content_json    JSONB       NOT NULL,
    display_order   INTEGER     NOT NULL,

    CONSTRAINT ck_item_type CHECK (item_type IN (
        'issue_tree', 'agent_config', 'confidence_map',
        'divergence_points', 'sprint_contract'
    ))
);

CREATE INDEX IF NOT EXISTS ix_review_items_gate_id
    ON review_items (gate_id);

-- 3. Review Decisions: the human's verdict
CREATE TABLE IF NOT EXISTS review_decisions (
    id                  VARCHAR     PRIMARY KEY,
    gate_id             VARCHAR     NOT NULL UNIQUE REFERENCES review_gates(id) ON DELETE CASCADE,
    decision            VARCHAR     NOT NULL,   -- 'approve' | 'modify' | 'reject'
    modifications_json  JSONB,
    reasoning           TEXT,
    decided_by          VARCHAR     NOT NULL,
    decided_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_decision_type CHECK (decision IN ('approve', 'modify', 'reject'))
);

COMMIT;

-- Rollback (uncomment to execute):
-- DROP TABLE IF EXISTS review_decisions CASCADE;
-- DROP TABLE IF EXISTS review_items CASCADE;
-- DROP TABLE IF EXISTS review_gates CASCADE;
