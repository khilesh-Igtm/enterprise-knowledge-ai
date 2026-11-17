"""Add conversations and messages.

Revision ID: p5_chat_001
Revises: 8610436f5690
"""

import sqlalchemy as sa

from alembic import op

revision = "p5_chat_001"
down_revision = "8610436f5690"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "knowledge_base_id",
            sa.Uuid(),
            sa.ForeignKey(
                "knowledge_bases.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=200),
            nullable=False,
            server_default="New conversation",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_conversations_user_id",
        "conversations",
        ["user_id"],
    )

    op.create_index(
        "ix_conversations_user_updated",
        "conversations",
        ["user_id", "updated_at"],
    )

    op.create_index(
        "ix_conversations_knowledge_base",
        "conversations",
        ["knowledge_base_id"],
    )

    op.create_table(
        "messages",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            sa.Uuid(),
            sa.ForeignKey(
                "conversations.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "citations",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('user', 'assistant')",
            name="ck_messages_role",
        ),
    )

    op.create_index(
        "ix_messages_conversation_id",
        "messages",
        ["conversation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_messages_conversation_id",
        table_name="messages",
    )

    op.drop_table("messages")

    op.drop_index(
        "ix_conversations_knowledge_base",
        table_name="conversations",
    )

    op.drop_index(
        "ix_conversations_user_updated",
        table_name="conversations",
    )

    op.drop_index(
        "ix_conversations_user_id",
        table_name="conversations",
    )

    op.drop_table("conversations")