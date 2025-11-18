# Safe migration that checks if columns exist before adding them
# This handles the case where columns were added manually or in a previous migration

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web_knowledge', '0024_change_qapair_page_to_set_null'),
    ]

    operations = [
        # Add external_id field only if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'web_knowledge_product' 
                        AND column_name = 'external_id'
                    ) THEN
                        ALTER TABLE web_knowledge_product
                        ADD COLUMN external_id VARCHAR(100) NULL;
                        CREATE INDEX IF NOT EXISTS web_knowledge_product_external_id_idx 
                        ON web_knowledge_product(external_id);
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE web_knowledge_product
                DROP COLUMN IF EXISTS external_id;
            """
        ),
        # Add external_source field only if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'web_knowledge_product' 
                        AND column_name = 'external_source'
                    ) THEN
                        ALTER TABLE web_knowledge_product
                        ADD COLUMN external_source VARCHAR(20) DEFAULT 'manual';
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE web_knowledge_product
                DROP COLUMN IF EXISTS external_source;
            """
        ),
        # Add constraint if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint 
                        WHERE conname = 'unique_external_product_per_user'
                    ) THEN
                        ALTER TABLE web_knowledge_product
                        ADD CONSTRAINT unique_external_product_per_user
                        UNIQUE (user_id, external_id)
                        WHERE external_id IS NOT NULL;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE web_knowledge_product
                DROP CONSTRAINT IF EXISTS unique_external_product_per_user;
            """
        ),
        # Add index if it doesn't exist
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = 'idx_product_external'
                    ) THEN
                        CREATE INDEX idx_product_external 
                        ON web_knowledge_product(user_id, external_source, is_active);
                    END IF;
                END $$;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS idx_product_external;
            """
        ),
    ]

