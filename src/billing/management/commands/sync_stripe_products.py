"""
Management command to sync billing plans to Stripe products and prices.

Usage:
    python manage.py sync_stripe_products
    python manage.py sync_stripe_products --dry-run
    python manage.py sync_stripe_products --plan-type full
    python manage.py sync_stripe_products --plan-type token
"""
import logging
import stripe
from django.core.management.base import BaseCommand
from decimal import Decimal

from billing.models import TokenPlan, FullPlan
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync billing plans to Stripe products and prices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating in Stripe',
        )
        parser.add_argument(
            '--plan-type',
            type=str,
            choices=['token', 'full', 'all'],
            default='all',
            help='Type of plans to sync (token, full, or all)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        plan_type = options['plan_type']
        
        if not getattr(settings, 'STRIPE_ENABLED', False):
            self.stdout.write(self.style.ERROR('❌ Stripe is not enabled'))
            return
        
        # Initialize Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        self.stdout.write(self.style.SUCCESS('\n🔄 Syncing Plans to Stripe'))
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))
        
        # Sync Token Plans
        if plan_type in ['token', 'all']:
            self.stdout.write(self.style.SUCCESS('\n📦 Processing Token Plans...'))
            token_plans = TokenPlan.objects.filter(is_active=True)
            for plan in token_plans:
                self._sync_token_plan(plan, dry_run)
        
        # Sync Full Plans
        if plan_type in ['full', 'all']:
            self.stdout.write(self.style.SUCCESS('\n📅 Processing Full Plans...'))
            full_plans = FullPlan.objects.filter(is_active=True)
            for plan in full_plans:
                self._sync_full_plan(plan, dry_run)
        
        self.stdout.write(self.style.SUCCESS('\n✅ Sync complete!\n'))
    
    def _sync_token_plan(self, plan, dry_run=False):
        """Sync a token plan to Stripe"""
        self.stdout.write(f'\n  📌 {plan.name}')
        self.stdout.write(f'     Tokens: {plan.tokens_included}')
        self.stdout.write(f'     Price: ${plan.price_en}')
        self.stdout.write(f'     Recurring: {plan.is_recurring}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('     ⏭️  Skipping (dry-run)'))
            return
        
        try:
            # Check if product already exists (you'd need to add stripe_product_id field to model)
            # For now, create new product
            product = stripe.Product.create(
                name=plan.name,
                description=f"{plan.tokens_included} AI tokens for automated responses",
                metadata={
                    'plan_type': 'token',
                    'plan_id': str(plan.id),
                    'tokens_included': str(plan.tokens_included),
                }
            )
            
            # Create price
            price_params = {
                'product': product.id,
                'unit_amount': int(plan.price_en * 100),  # Convert to cents
                'currency': getattr(settings, 'STRIPE_CURRENCY', 'usd'),
                'metadata': {
                    'plan_type': 'token',
                    'plan_id': str(plan.id),
                }
            }
            
            # Add recurring if needed
            if plan.is_recurring:
                price_params['recurring'] = {
                    'interval': 'month',
                    'interval_count': 1
                }
            
            price = stripe.Price.create(**price_params)
            
            self.stdout.write(self.style.SUCCESS(f'     ✅ Created Stripe product: {product.id}'))
            self.stdout.write(self.style.SUCCESS(f'     ✅ Created Stripe price: {price.id}'))
            
            # TODO: Store product.id and price.id in plan model
            # plan.stripe_product_id = product.id
            # plan.stripe_price_id = price.id
            # plan.save()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'     ❌ Error: {e}'))
    
    def _sync_full_plan(self, plan, dry_run=False):
        """Sync a full plan to Stripe"""
        self.stdout.write(f'\n  📌 {plan.name}')
        self.stdout.write(f'     Tokens: {plan.tokens_included}')
        self.stdout.write(f'     Duration: {plan.duration_days} days')
        self.stdout.write(f'     Price: ${plan.price_en}')
        self.stdout.write(f'     Yearly: {plan.is_yearly}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('     ⏭️  Skipping (dry-run)'))
            return
        
        try:
            # Create product
            product = stripe.Product.create(
                name=plan.name,
                description=f"{plan.tokens_included} tokens + {plan.duration_days} days subscription",
                metadata={
                    'plan_type': 'full',
                    'plan_id': str(plan.id),
                    'tokens_included': str(plan.tokens_included),
                    'duration_days': str(plan.duration_days),
                }
            )
            
            # Create recurring price
            interval = 'year' if plan.is_yearly else 'month'
            price = stripe.Price.create(
                product=product.id,
                unit_amount=int(plan.price_en * 100),  # Convert to cents
                currency=getattr(settings, 'STRIPE_CURRENCY', 'usd'),
                recurring={
                    'interval': interval,
                    'interval_count': 1
                },
                metadata={
                    'plan_type': 'full',
                    'plan_id': str(plan.id),
                }
            )
            
            self.stdout.write(self.style.SUCCESS(f'     ✅ Created Stripe product: {product.id}'))
            self.stdout.write(self.style.SUCCESS(f'     ✅ Created Stripe price: {price.id}'))
            
            # TODO: Store product.id and price.id in plan model
            # plan.stripe_product_id = product.id
            # plan.stripe_price_id = price.id
            # plan.save()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'     ❌ Error: {e}'))

