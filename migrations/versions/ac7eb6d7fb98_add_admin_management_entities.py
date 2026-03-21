from alembic import op
import sqlalchemy as sa

revision = 'ac7eb6d7fb98'
down_revision = '7c842816e3c8'
branch_labels = None
depends_on = None


shop_status = sa.Enum(
    'PENDING',
    'ACTIVE',
    'BANNED',
    name='shop_status'
)


def upgrade():
    bind = op.get_bind()
    shop_status.create(bind, checkfirst=True)

    op.create_table(
        'notifications',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    with op.batch_alter_table('notifications') as batch_op:
        batch_op.create_index('ix_notifications_user_id', ['user_id'])

    with op.batch_alter_table('flash_sales') as batch_op:
        batch_op.add_column(
            sa.Column('disabled_reason', sa.String(255))
        )

    with op.batch_alter_table('shops') as batch_op:
        batch_op.add_column(
            sa.Column(
                'status',
                shop_status,
                nullable=False,
                server_default='PENDING'
            )
        )
        batch_op.create_index('ix_shops_status', ['status'])

    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(
            sa.Column(
                'is_banned',
                sa.Boolean(),
                nullable=False,
                server_default=sa.false()
            )
        )


def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('is_banned')

    with op.batch_alter_table('shops') as batch_op:
        batch_op.drop_index('ix_shops_status')
        batch_op.drop_column('status')

    with op.batch_alter_table('flash_sales') as batch_op:
        batch_op.drop_column('disabled_reason')

    with op.batch_alter_table('notifications') as batch_op:
        batch_op.drop_index('ix_notifications_user_id')

    op.drop_table('notifications')

    bind = op.get_bind()
    shop_status.drop(bind, checkfirst=True)