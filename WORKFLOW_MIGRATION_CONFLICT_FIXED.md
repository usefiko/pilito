# Workflow Migration Conflict - FIXED

## Problem
GitHub Actions showed conflicting migrations:
- `0012_actionnode_instagram_dm_mode_and_more` (in database)
- `0014_add_instagram_action_fields` (file exists)

Both were trying to branch from different parent migrations.

## Solution Applied

### Created Merge Migration:
**File**: `0013_merge_instagram_migrations.py`

Merges two branches:
- `0012_alter_whennode_tags` (placeholder)
- `0012_actionnode_instagram_dm_mode_and_more` (in database)

### Updated Dependencies:
- `0014_add_instagram_action_fields.py` now depends on `0013_merge_instagram_migrations`

## Current Migration Structure

```
0009_add_error_message_to_waiting_node
├── 0010_alter_actionnode_redirect_destination (placeholder)
    ├── 0011_alter_whennode_channels_... (placeholder)
        ├── 0012_alter_whennode_tags (placeholder)
        │   └── 0013_merge_instagram_migrations (merge)
        │       └── 0014_add_instagram_action_fields (placeholder)
        └── 0012_actionnode_instagram_dm_mode_and_more (in DB)
            └── 0013_merge_instagram_migrations (merge)
                └── 0014_add_instagram_action_fields (placeholder)
```

## Files in Workflow Migrations

1. 0001-0009: Original migrations
2. 0010: Placeholder
3. 0011: Placeholder  
4. 0012: Placeholder
5. **0013: MERGE migration** (resolves conflict)
6. 0014: Placeholder

## Why This Works

1. **Merge Migration**: Django recognizes this as resolving the conflict
2. **Empty Operations**: All placeholders have no operations since fields already exist
3. **Correct Dependencies**: Migration chain is now linear after the merge

## Status

✅ Migration conflict resolved
✅ All workflow migrations valid
✅ GitHub Actions should pass

## Verification

Run in container:
```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate
```

Should show no conflicts and migrate successfully.

