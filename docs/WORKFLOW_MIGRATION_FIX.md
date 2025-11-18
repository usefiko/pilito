# Workflow Migration Conflict - Fixed

## Problem
Django detected conflicting migrations in the `workflow` app:
- `0013_add_instagram_comment_filters`
- `0013_alter_action_action_type_and_more`
- `0015_add_instagram_action_fields`

## Solution Applied

1. **Renamed migration**: `0014_add_instagram_comment_filters.py` → `0013_add_instagram_comment_filters.py`
   - This matches what the database expects

2. **Created merge migration**: `0013_merge_instagram_migrations.py`
   - Merges the two conflicting 0013 branches

3. **Updated dependencies**:
   - `0015_add_instagram_action_fields.py` now depends on `0013_merge_instagram_migrations`

## Current Migration Structure

```
0012_alter_whennode_tags
├── 0013_add_instagram_comment_filters (file exists)
├── 0013_alter_action_action_type_and_more (in database, file may be missing)
└── 0013_merge_instagram_migrations (merge migration)
    └── 0015_add_instagram_action_fields
```

## Next Steps

If the migration conflict persists, you may need to:

1. **Run Django's merge command** (recommended):
   ```bash
   python manage.py makemigrations --merge workflow
   ```
   This will create a proper merge migration with correct dependencies.

2. **If the other 0013 migration file is missing**, you may need to:
   - Check the database for the migration record
   - Create the missing migration file, OR
   - Fake the migration if it's already applied

3. **Apply migrations**:
   ```bash
   python manage.py migrate workflow
   ```

## Files Changed

- ✅ Renamed: `0014_add_instagram_comment_filters.py` → `0013_add_instagram_comment_filters.py`
- ✅ Created: `0013_merge_instagram_migrations.py`
- ✅ Updated: `0015_add_instagram_action_fields.py` (dependencies)

## Backup

A backup of the original migrations is in: `src/workflow/migrations_backup/`

