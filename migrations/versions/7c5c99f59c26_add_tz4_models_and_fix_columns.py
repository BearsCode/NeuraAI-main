"""add_tz4_models_and_fix_columns"""

revision = '7c5c99f59c26'
down_revision = '20260621_000009'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Text
from sqlalchemy import inspect

from sqlalchemy.dialects import postgresql


NEW_TABLES = [
    "avatar_training_jobs",
    "avatars",
    "business_memory",
    "internship_states",
    "retail_catalog_syncs",
    "retail_products",
    "training_signals",
    "workflow_instances",
    "workflow_steps",
]


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return name in inspector.get_table_names()


def upgrade() -> None:
    if not _table_exists("avatar_training_jobs"):
        op.create_table('avatar_training_jobs',
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('avatar_id', sa.String(length=36), nullable=False),
        sa.Column('avatar_type', sa.String(length=16), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('provider', sa.String(length=64), nullable=False),
        sa.Column('provider_job_id', sa.String(length=256), nullable=True),
        sa.Column('input_data', postgresql.JSONB(astext_type=Text()), nullable=False),
        sa.Column('output_data', postgresql.JSONB(astext_type=Text()), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_avatar_training_jobs'))
        )
        op.create_index(op.f('ix_avatar_training_jobs_avatar_id'), 'avatar_training_jobs', ['avatar_id'], unique=False)
        op.create_index(op.f('ix_avatar_training_jobs_status'), 'avatar_training_jobs', ['status'], unique=False)
        op.create_index(op.f('ix_avatar_training_jobs_tenant_id'), 'avatar_training_jobs', ['tenant_id'], unique=False)
    if not _table_exists("avatars"):
        op.create_table('avatars',
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('avatar_type', sa.String(length=16), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('source_urls', postgresql.JSONB(astext_type=Text()), nullable=False),
        sa.Column('model_weights_url', sa.String(length=512), nullable=True),
        sa.Column('preview_url', sa.String(length=512), nullable=True),
        sa.Column('provider', sa.String(length=64), nullable=True),
        sa.Column('provider_model_id', sa.String(length=256), nullable=True),
        sa.Column('config', postgresql.JSONB(astext_type=Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_avatars'))
        )
        op.create_index(op.f('ix_avatars_tenant_id'), 'avatars', ['tenant_id'], unique=False)
    if not _table_exists("business_memory"):
        op.create_table('business_memory',
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('memory_type', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('content', postgresql.JSONB(astext_type=Text()), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=64), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_business_memory'))
        )
        op.create_index(op.f('ix_business_memory_memory_type'), 'business_memory', ['memory_type'], unique=False)
        op.create_index(op.f('ix_business_memory_project_id'), 'business_memory', ['project_id'], unique=False)
        op.create_index(op.f('ix_business_memory_tenant_id'), 'business_memory', ['tenant_id'], unique=False)
    if not _table_exists("internship_states"):
        op.create_table('internship_states',
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('stage', sa.String(length=32), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('total_days', sa.Integer(), nullable=False),
        sa.Column('approval_rate', sa.Float(), nullable=True),
        sa.Column('signals_count', sa.Integer(), nullable=False),
        sa.Column('generated_count', sa.Integer(), nullable=False),
        sa.Column('approved_count', sa.Integer(), nullable=False),
        sa.Column('preference_model', postgresql.JSONB(astext_type=Text()), nullable=False),
        sa.Column('recommended_mode', sa.String(length=32), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_extended', sa.Boolean(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_internship_states'))
        )
        op.create_index(op.f('ix_internship_states_project_id'), 'internship_states', ['project_id'], unique=True)
        op.create_index(op.f('ix_internship_states_tenant_id'), 'internship_states', ['tenant_id'], unique=False)
    if not _table_exists("retail_catalog_syncs"):
        op.create_table('retail_catalog_syncs',
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('source_system', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('total_products', sa.Integer(), nullable=True),
        sa.Column('synced_products', sa.Integer(), nullable=True),
        sa.Column('failed_products', sa.Integer(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('result', postgresql.JSONB(astext_type=Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_retail_catalog_syncs'))
        )
        op.create_index(op.f('ix_retail_catalog_syncs_project_id'), 'retail_catalog_syncs', ['project_id'], unique=False)
        op.create_index(op.f('ix_retail_catalog_syncs_status'), 'retail_catalog_syncs', ['status'], unique=False)
        op.create_index(op.f('ix_retail_catalog_syncs_tenant_id'), 'retail_catalog_syncs', ['tenant_id'], unique=False)
    if not _table_exists("retail_products"):
        op.create_table('retail_products',
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('external_id', sa.String(length=256), nullable=True),
        sa.Column('name', sa.String(length=512), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('old_price', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=8), nullable=True),
        sa.Column('category', sa.String(length=256), nullable=True),
        sa.Column('image_urls', postgresql.JSONB(astext_type=Text()), nullable=False),
        sa.Column('stock_quantity', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_on_sale', sa.Boolean(), nullable=False),
        sa.Column('sale_ends_at', sa.String(), nullable=True),
        sa.Column('source_system', sa.String(length=64), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(astext_type=Text()), nullable=False),
        sa.Column('last_synced_at', sa.String(), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_retail_products'))
        )
        op.create_index(op.f('ix_retail_products_category'), 'retail_products', ['category'], unique=False)
        op.create_index(op.f('ix_retail_products_external_id'), 'retail_products', ['external_id'], unique=False)
        op.create_index(op.f('ix_retail_products_is_active'), 'retail_products', ['is_active'], unique=False)
        op.create_index(op.f('ix_retail_products_project_id'), 'retail_products', ['project_id'], unique=False)
        op.create_index(op.f('ix_retail_products_tenant_id'), 'retail_products', ['tenant_id'], unique=False)
    if not _table_exists("training_signals"):
        op.create_table('training_signals',
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('content_item_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=32), nullable=False),
        sa.Column('signal_weight', sa.Float(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('context', postgresql.JSONB(astext_type=Text()), nullable=False),
        sa.Column('training_round', sa.Integer(), nullable=False),
        sa.Column('applied', sa.Boolean(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_training_signals'))
        )
        op.create_index(op.f('ix_training_signals_content_item_id'), 'training_signals', ['content_item_id'], unique=False)
        op.create_index(op.f('ix_training_signals_project_id'), 'training_signals', ['project_id'], unique=False)
        op.create_index(op.f('ix_training_signals_tenant_id'), 'training_signals', ['tenant_id'], unique=False)
    if not _table_exists("workflow_instances"):
        op.create_table('workflow_instances',
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('workflow_type', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('trigger', sa.String(length=64), nullable=True),
        sa.Column('current_step', sa.Integer(), nullable=False),
        sa.Column('total_steps', sa.Integer(), nullable=False),
        sa.Column('context', postgresql.JSONB(astext_type=Text()), nullable=False),
        sa.Column('result', postgresql.JSONB(astext_type=Text()), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('parent_workflow_id', sa.String(length=36), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_workflow_instances'))
        )
        op.create_index(op.f('ix_workflow_instances_parent_workflow_id'), 'workflow_instances', ['parent_workflow_id'], unique=False)
        op.create_index(op.f('ix_workflow_instances_project_id'), 'workflow_instances', ['project_id'], unique=False)
        op.create_index(op.f('ix_workflow_instances_status'), 'workflow_instances', ['status'], unique=False)
        op.create_index(op.f('ix_workflow_instances_tenant_id'), 'workflow_instances', ['tenant_id'], unique=False)
        op.create_index(op.f('ix_workflow_instances_workflow_type'), 'workflow_instances', ['workflow_type'], unique=False)
    if not _table_exists("workflow_steps"):
        op.create_table('workflow_steps',
        sa.Column('workflow_id', sa.String(length=36), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('step_type', sa.String(length=64), nullable=False),
        sa.Column('agent_type', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('input_data', postgresql.JSONB(astext_type=Text()), nullable=False),
        sa.Column('output_data', postgresql.JSONB(astext_type=Text()), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('async_job_id', sa.String(length=36), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_workflow_steps'))
        )
        op.create_index(op.f('ix_workflow_steps_async_job_id'), 'workflow_steps', ['async_job_id'], unique=False)
        op.create_index(op.f('ix_workflow_steps_status'), 'workflow_steps', ['status'], unique=False)
        op.create_index(op.f('ix_workflow_steps_workflow_id'), 'workflow_steps', ['workflow_id'], unique=False)

    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("content_plans")}
    if "plan_data" not in columns:
        op.add_column('content_plans', sa.Column('plan_data', sa.JSON(), nullable=True))

    columns = {col["name"] for col in inspector.get_columns("publications")}
    for col_name, col_type in [
        ("content_type", sa.Enum('POST', 'CAROUSEL', 'STORY', 'VIDEO', 'REEL', 'SHORT', 'THREAD', name='contenttype', native_enum=False)),
        ("published_at", sa.DateTime(timezone=True)),
        ("external_url", sa.String(length=500)),
        ("external_post_id", sa.String(length=255)),
    ]:
        if col_name not in columns:
            op.add_column('publications', sa.Column(col_name, col_type, nullable=True))


def downgrade() -> None:
    op.drop_column('publications', 'external_post_id')
    op.drop_column('publications', 'external_url')
    op.drop_column('publications', 'published_at')
    op.drop_column('publications', 'content_type')
    op.drop_column('content_plans', 'plan_data')
    op.drop_index(op.f('ix_workflow_steps_workflow_id'), table_name='workflow_steps')
    op.drop_index(op.f('ix_workflow_steps_status'), table_name='workflow_steps')
    op.drop_index(op.f('ix_workflow_steps_async_job_id'), table_name='workflow_steps')
    op.drop_table('workflow_steps')
    op.drop_index(op.f('ix_workflow_instances_workflow_type'), table_name='workflow_instances')
    op.drop_index(op.f('ix_workflow_instances_tenant_id'), table_name='workflow_instances')
    op.drop_index(op.f('ix_workflow_instances_status'), table_name='workflow_instances')
    op.drop_index(op.f('ix_workflow_instances_project_id'), table_name='workflow_instances')
    op.drop_index(op.f('ix_workflow_instances_parent_workflow_id'), table_name='workflow_instances')
    op.drop_table('workflow_instances')
    op.drop_index(op.f('ix_training_signals_tenant_id'), table_name='training_signals')
    op.drop_index(op.f('ix_training_signals_project_id'), table_name='training_signals')
    op.drop_index(op.f('ix_training_signals_content_item_id'), table_name='training_signals')
    op.drop_table('training_signals')
    op.drop_index(op.f('ix_retail_products_tenant_id'), table_name='retail_products')
    op.drop_index(op.f('ix_retail_products_project_id'), table_name='retail_products')
    op.drop_index(op.f('ix_retail_products_is_active'), table_name='retail_products')
    op.drop_index(op.f('ix_retail_products_external_id'), table_name='retail_products')
    op.drop_index(op.f('ix_retail_products_category'), table_name='retail_products')
    op.drop_table('retail_products')
    op.drop_index(op.f('ix_retail_catalog_syncs_tenant_id'), table_name='retail_catalog_syncs')
    op.drop_index(op.f('ix_retail_catalog_syncs_status'), table_name='retail_catalog_syncs')
    op.drop_index(op.f('ix_retail_catalog_syncs_project_id'), table_name='retail_catalog_syncs')
    op.drop_table('retail_catalog_syncs')
    op.drop_index(op.f('ix_internship_states_tenant_id'), table_name='internship_states')
    op.drop_index(op.f('ix_internship_states_project_id'), table_name='internship_states')
    op.drop_table('internship_states')
    op.drop_index(op.f('ix_business_memory_tenant_id'), table_name='business_memory')
    op.drop_index(op.f('ix_business_memory_project_id'), table_name='business_memory')
    op.drop_index(op.f('ix_business_memory_memory_type'), table_name='business_memory')
    op.drop_table('business_memory')
    op.drop_index(op.f('ix_avatars_tenant_id'), table_name='avatars')
    op.drop_table('avatars')
    op.drop_index(op.f('ix_avatar_training_jobs_tenant_id'), table_name='avatar_training_jobs')
    op.drop_index(op.f('ix_avatar_training_jobs_status'), table_name='avatar_training_jobs')
    op.drop_index(op.f('ix_avatar_training_jobs_avatar_id'), table_name='avatar_training_jobs')
    op.drop_table('avatar_training_jobs')
