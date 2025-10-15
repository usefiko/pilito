from django.db import migrations


def create_free_trial_fullplan(apps, schema_editor):
    FullPlan = apps.get_model('billing', 'FullPlan')

    # Ensure a single canonical free trial plan exists
    plan, created = FullPlan.objects.get_or_create(
        name='Free Trial',
        defaults={
            'tokens_included': 5000,
            'duration_days': 14,
            'is_recommended': False,
            'is_yearly': False,
            'price_en': 0,
            'price_tr': 0,
            'price_ar': 0,
            'is_active': True,
            'description': 'Automatic free trial plan for new users',
        }
    )

    # If it already exists, make sure critical fields match desired values
    if not created:
        updated = False
        if plan.tokens_included != 5000:
            plan.tokens_included = 5000
            updated = True
        if plan.duration_days != 14:
            plan.duration_days = 14
            updated = True
        # Ensure prices are zero and plan is active
        if plan.price_en != 0 or plan.price_tr != 0 or plan.price_ar != 0:
            plan.price_en = 0
            plan.price_tr = 0
            plan.price_ar = 0
            updated = True
        if plan.is_active is False:
            plan.is_active = True
            updated = True
        if updated:
            plan.save()


def delete_free_trial_fullplan(apps, schema_editor):
    FullPlan = apps.get_model('billing', 'FullPlan')
    FullPlan.objects.filter(name='Free Trial').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0004_alter_tokenplan_options_remove_tokenplan_price_and_more'),
    ]

    operations = [
        migrations.RunPython(create_free_trial_fullplan, delete_free_trial_fullplan),
    ]


