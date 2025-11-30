# Generated migration for WalletTransaction model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WalletTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('commission', 'Affiliate Commission'), ('payment', 'Payment'), ('refund', 'Refund'), ('withdrawal', 'Withdrawal'), ('adjustment', 'Manual Adjustment')], default='commission', max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, help_text='Transaction amount (positive for credit, negative for debit)', max_digits=10)),
                ('balance_after', models.DecimalField(decimal_places=2, help_text='Wallet balance after this transaction', max_digits=10)),
                ('description', models.TextField(help_text='Description of the transaction')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, help_text='Admin user who created manual adjustments', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_wallet_transactions', to=settings.AUTH_USER_MODEL)),
                ('referred_user', models.ForeignKey(blank=True, help_text='User who made the payment that generated this commission', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='generated_commissions', to=settings.AUTH_USER_MODEL)),
                ('related_payment', models.ForeignKey(blank=True, help_text='Related payment if this is a commission', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='wallet_transactions', to='billing.payment')),
                ('user', models.ForeignKey(help_text='User whose wallet is affected', on_delete=django.db.models.deletion.CASCADE, related_name='wallet_transactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '💰 Wallet Transaction',
                'verbose_name_plural': '💰 Wallet Transactions',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['user', '-created_at'], name='billing_wal_user_id_e7c8b5_idx'),
                    models.Index(fields=['related_payment'], name='billing_wal_related_a5c9d2_idx'),
                ],
            },
        ),
    ]

