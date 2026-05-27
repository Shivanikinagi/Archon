"""Initial schema migration - Create all core tables

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-05-27 10:00:00.000000

This migration creates the initial database schema including:
- User table with authentication fields
- ResearchSession for tracking research workflows
- Report for generated research reports
- Source for tracking research sources
- Citation for citations with multiple styles
- Document for uploaded research documents
- DocumentChunk for RAG document chunks
- Search for query history
- AuditLog for compliance tracking
- TokenBlacklist for logout token revocation

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all initial tables"""
    
    # Create extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create enums
    op.execute("""
        CREATE TYPE user_role AS ENUM ('user', 'researcher', 'admin')
    """)
    
    op.execute("""
        CREATE TYPE research_status AS ENUM (
            'planning', 'researching', 'generating', 'fact_checking', 'reviewing',
            'completed', 'failed', 'cancelled'
        )
    """)
    
    op.execute("""
        CREATE TYPE research_depth AS ENUM ('shallow', 'moderate', 'deep')
    """)
    
    op.execute("""
        CREATE TYPE citation_style AS ENUM ('apa', 'mla', 'chicago', 'harvard', 'ieee')
    """)
    
    op.execute("""
        CREATE TYPE source_type AS ENUM ('web', 'academic', 'document', 'internal')
    """)
    
    op.execute("""
        CREATE TYPE report_status AS ENUM ('draft', 'published', 'archived')
    """)
    
    op.execute("""
        CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'failed')
    """)
    
    op.execute("""
        CREATE TYPE search_type AS ENUM ('web', 'academic', 'document', 'entity')
    """)
    
    op.execute("""
        CREATE TYPE audit_status AS ENUM ('success', 'failure')
    """)
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('role', postgresql.ENUM('user', 'researcher', 'admin', name='user_role'), nullable=False, server_default='user'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username', name='uq_users_username'),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])
    
    # Create research_sessions table
    op.create_table('research_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.uuid_generate_v4()),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('query', sa.String(length=500), nullable=False),
        sa.Column('research_plan', sa.JSON(), nullable=True),
        sa.Column('status', postgresql.ENUM('planning', 'researching', 'generating', 'fact_checking', 'reviewing', 'completed', 'failed', 'cancelled', name='research_status'), nullable=False, server_default='planning'),
        sa.Column('depth', postgresql.ENUM('shallow', 'moderate', 'deep', name='research_depth'), nullable=False, server_default='moderate'),
        sa.Column('web_results', sa.JSON(), nullable=True),
        sa.Column('academic_results', sa.JSON(), nullable=True),
        sa.Column('document_results', sa.JSON(), nullable=True),
        sa.Column('retrieval_results', sa.JSON(), nullable=True),
        sa.Column('verification_report', sa.JSON(), nullable=True),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_step', sa.String(length=255), nullable=True),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('knowledge_graph_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_research_sessions_user_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_research_sessions_created_at', 'research_sessions', ['created_at'])
    op.create_index('ix_research_sessions_user_id', 'research_sessions', ['user_id'])
    op.create_index('ix_research_sessions_status', 'research_sessions', ['status'])
    op.create_index('ix_research_sessions_user_created', 'research_sessions', ['user_id', 'created_at'])
    
    # Create reports table
    op.create_table('reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.uuid_generate_v4()),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content_markdown', sa.Text(), nullable=False),
        sa.Column('content_json', sa.JSON(), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=False),
        sa.Column('citation_count', sa.Integer(), nullable=False),
        sa.Column('quality_scores', sa.JSON(), nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'published', 'archived', name='report_status'), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['research_sessions.id'], name='fk_reports_session_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_reports_user_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', name='uq_reports_session_id'),
    )
    op.create_index('ix_reports_created_at', 'reports', ['created_at'])
    op.create_index('ix_reports_user_id', 'reports', ['user_id'])
    op.create_index('ix_reports_session_id', 'reports', ['session_id'])
    
    # Create sources table
    op.create_table('sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.uuid_generate_v4()),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', postgresql.ENUM('web', 'academic', 'document', 'internal', name='source_type'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=True),
        sa.Column('authors', sa.JSON(), nullable=True),
        sa.Column('published_date', sa.DateTime(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('source_reliability', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['session_id'], ['research_sessions.id'], name='fk_sources_session_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sources_created_at', 'sources', ['created_at'])
    op.create_index('ix_sources_session_id', 'sources', ['session_id'])
    op.create_index('ix_sources_source_type', 'sources', ['source_type'])
    
    # Create citations table
    op.create_table('citations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.uuid_generate_v4()),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('claim_text', sa.String(length=1000), nullable=False),
        sa.Column('citation_text', sa.Text(), nullable=False),
        sa.Column('citation_style', postgresql.ENUM('apa', 'mla', 'chicago', 'harvard', 'ieee', name='citation_style'), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], name='fk_citations_report_id'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], name='fk_citations_source_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_citations_report_id', 'citations', ['report_id'])
    op.create_index('ix_citations_source_id', 'citations', ['source_id'])
    
    # Create documents table
    op.create_table('documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.uuid_generate_v4()),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('processing_status', postgresql.ENUM('pending', 'processing', 'completed', 'failed', name='processing_status'), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_documents_user_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_documents_created_at', 'documents', ['created_at'])
    op.create_index('ix_documents_user_id', 'documents', ['user_id'])
    op.create_index('ix_documents_processing_status', 'documents', ['processing_status'])
    
    # Create document_chunks table
    op.create_table('document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.uuid_generate_v4()),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding_id', sa.String(length=255), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name='fk_document_chunks_document_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_document_chunks_created_at', 'document_chunks', ['created_at'])
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('ix_document_chunks_chunk_index', 'document_chunks', ['document_id', 'chunk_index'])
    
    # Create searches table
    op.create_table('searches',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.uuid_generate_v4()),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('search_type', postgresql.ENUM('web', 'academic', 'document', 'entity', name='search_type'), nullable=False),
        sa.Column('query', sa.String(length=500), nullable=False),
        sa.Column('results_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['session_id'], ['research_sessions.id'], name='fk_searches_session_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_searches_created_at', 'searches', ['created_at'])
    op.create_index('ix_searches_session_id', 'searches', ['session_id'])
    op.create_index('ix_searches_search_type', 'searches', ['search_type'])
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.uuid_generate_v4()),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('resource_type', sa.String(length=255), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('status', postgresql.ENUM('success', 'failure', name='audit_status'), nullable=False, server_default='success'),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_audit_logs_user_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action_timestamp', 'audit_logs', ['action', 'timestamp'])
    op.create_index('ix_audit_logs_resource_type_timestamp', 'audit_logs', ['resource_type', 'timestamp'])
    
    # Create token_blacklist table
    op.create_table('token_blacklist',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.uuid_generate_v4()),
        sa.Column('token', sa.String(length=2000), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('blacklisted_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token', name='uq_token_blacklist_token'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_token_blacklist_user_id'),
    )
    op.create_index('ix_token_blacklist_blacklisted_at', 'token_blacklist', ['blacklisted_at'])
    op.create_index('ix_token_blacklist_expires_at', 'token_blacklist', ['expires_at'])
    op.create_index('ix_token_blacklist_user_id', 'token_blacklist', ['user_id'])


def downgrade() -> None:
    """Drop all tables and types"""
    
    # Drop tables (in reverse order of creation to respect foreign keys)
    op.drop_table('token_blacklist')
    op.drop_table('audit_logs')
    op.drop_table('searches')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('citations')
    op.drop_table('sources')
    op.drop_table('reports')
    op.drop_table('research_sessions')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS audit_status CASCADE')
    op.execute('DROP TYPE IF EXISTS search_type CASCADE')
    op.execute('DROP TYPE IF EXISTS processing_status CASCADE')
    op.execute('DROP TYPE IF EXISTS report_status CASCADE')
    op.execute('DROP TYPE IF EXISTS source_type CASCADE')
    op.execute('DROP TYPE IF EXISTS citation_style CASCADE')
    op.execute('DROP TYPE IF EXISTS research_depth CASCADE')
    op.execute('DROP TYPE IF EXISTS research_status CASCADE')
    op.execute('DROP TYPE IF EXISTS user_role CASCADE')
    
    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
