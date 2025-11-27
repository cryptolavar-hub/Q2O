"""create llm_usage_logs table

Revision ID: 001
Revises: 
Create Date: 2025-11-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create llm_usage_logs table
    op.create_table(
        'llm_usage_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.String(length=255), nullable=False),
        sa.Column('project_id', sa.String(length=255), nullable=True),
        sa.Column('task_id', sa.String(length=255), nullable=True),
        sa.Column('agent_type', sa.String(length=100), nullable=False),
        sa.Column('agent_id', sa.String(length=255), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('input_cost', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('output_cost', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('total_cost', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('duration_seconds', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('success', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('cache_hit', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('system_prompt_hash', sa.String(length=64), nullable=True),
        sa.Column('user_prompt_hash', sa.String(length=64), nullable=True),
        sa.Column('response_preview', sa.Text(), nullable=True),
        sa.Column('log_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_llm_usage_logs_request_id', 'llm_usage_logs', ['request_id'], unique=True)
    op.create_index('idx_llm_usage_logs_project_id', 'llm_usage_logs', ['project_id'])
    op.create_index('idx_llm_usage_logs_task_id', 'llm_usage_logs', ['task_id'])
    op.create_index('idx_llm_usage_logs_agent_type', 'llm_usage_logs', ['agent_type'])
    op.create_index('idx_llm_usage_logs_provider', 'llm_usage_logs', ['provider'])
    op.create_index('idx_llm_usage_logs_model', 'llm_usage_logs', ['model'])
    op.create_index('idx_llm_usage_logs_success', 'llm_usage_logs', ['success'])
    op.create_index('idx_llm_usage_logs_cache_hit', 'llm_usage_logs', ['cache_hit'])
    op.create_index('idx_llm_usage_logs_created_at', 'llm_usage_logs', ['created_at'])
    op.create_index('idx_llm_logs_provider_model', 'llm_usage_logs', ['provider', 'model'])
    op.create_index('idx_llm_logs_project_agent', 'llm_usage_logs', ['project_id', 'agent_type'])
    op.create_index('idx_llm_logs_success_cache', 'llm_usage_logs', ['success', 'cache_hit'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_llm_logs_success_cache', table_name='llm_usage_logs')
    op.drop_index('idx_llm_logs_project_agent', table_name='llm_usage_logs')
    op.drop_index('idx_llm_logs_provider_model', table_name='llm_usage_logs')
    op.drop_index('idx_llm_usage_logs_created_at', table_name='llm_usage_logs')
    op.drop_index('idx_llm_usage_logs_cache_hit', table_name='llm_usage_logs')
    op.drop_index('idx_llm_usage_logs_success', table_name='llm_usage_logs')
    op.drop_index('idx_llm_usage_logs_model', table_name='llm_usage_logs')
    op.drop_index('idx_llm_usage_logs_provider', table_name='llm_usage_logs')
    op.drop_index('idx_llm_usage_logs_agent_type', table_name='llm_usage_logs')
    op.drop_index('idx_llm_usage_logs_task_id', table_name='llm_usage_logs')
    op.drop_index('idx_llm_usage_logs_project_id', table_name='llm_usage_logs')
    op.drop_index('idx_llm_usage_logs_request_id', table_name='llm_usage_logs')
    
    # Drop table
    op.drop_table('llm_usage_logs')

