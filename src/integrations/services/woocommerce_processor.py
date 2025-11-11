import hashlib
from typing import Dict, Any
from decimal import Decimal, InvalidOperation
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class WooCommerceProcessor:
    """Process WooCommerce webhook events"""
    
    def __init__(self, user=None, token=None):
        self.user = user
        self.token = token
    
    def process_event(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Process a WooCommerce event
        
        Args:
            payload: Webhook payload from WordPress
            
        Returns:
            Processing result
        """
        event_type = payload.get('event_type')
        
        if event_type in ['product.created', 'product.updated']:
            return self._handle_product_upsert(payload)
        elif event_type == 'product.deleted':
            return self._handle_product_delete(payload)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    
    def _handle_product_upsert(self, payload: Dict) -> Dict:
        """Create or update product"""
        from web_knowledge.models import Product
        
        product_data = payload['product']
        
        # Calculate content hash
        content_hash = self._calculate_content_hash(product_data)
        
        external_id = f"woo_{product_data['id']}"
        
        # Find existing product
        existing_product = Product.objects.filter(
            user=self.user,
            external_id=external_id
        ).first()
        
        # Check if embedding regeneration needed
        needs_embedding = True
        if existing_product:
            old_hash = existing_product.extraction_metadata.get('content_hash', '')
            if old_hash == content_hash:
                needs_embedding = False
                logger.info(f"📝 Content unchanged, updating metadata only")
        
        # Prepare product data
        product_defaults = {
            'title': product_data['name'][:255],  # Max 255 chars
            'description': product_data.get('description', ''),
            'short_description': product_data.get('short_description', '')[:500],  # Truncate to 500
            'price': self._safe_decimal(product_data.get('price')),
            'currency': product_data.get('currency', 'IRT'),
            'stock_quantity': product_data.get('stock_quantity'),
            'in_stock': product_data.get('stock_status') == 'instock',
            'link': product_data.get('permalink', ''),
            'external_source': 'woocommerce',
            'is_active': True,
            'tags': product_data.get('tags', []),
            'category': ', '.join(product_data.get('categories', [])),
            'extraction_method': 'manual',
            'extraction_metadata': {
                'woo_product_id': product_data['id'],
                'sku': product_data.get('sku', ''),
                'content_hash': content_hash,
                'regular_price': product_data.get('regular_price'),
                'sale_price': product_data.get('sale_price'),
                'on_sale': product_data.get('on_sale', False),
                'images': {
                    'main': product_data.get('image'),
                    'gallery': product_data.get('gallery', [])
                },
                'needs_embedding': needs_embedding,
                'last_sync_at': str(timezone.now()),
            }
        }
        
        # Handle images
        if product_data.get('image'):
            product_defaults['main_image'] = product_data['image']
        
        if product_data.get('gallery'):
            product_defaults['images'] = product_data['gallery']
        
        # Handle pricing
        if product_data.get('regular_price') and product_data.get('sale_price'):
            regular = self._safe_decimal(product_data.get('regular_price'))
            sale = self._safe_decimal(product_data.get('sale_price'))
            if regular and sale and sale < regular:
                product_defaults['original_price'] = regular
                product_defaults['price'] = sale
                product_defaults['discount_amount'] = regular - sale
        
        # Create or Update
        product, created = Product.objects.update_or_create(
            user=self.user,
            external_id=external_id,
            defaults=product_defaults
        )
        
        # Signal will auto-chunk (web_knowledge/signals.py)
        
        action = "created" if created else "updated"
        logger.info(f"✅ Product {action}: {product.title} (ID: {product.id})")
        
        return {
            'status': 'success',
            'action': action,
            'product_id': str(product.id),
            'needs_embedding': needs_embedding
        }
    
    def _handle_product_delete(self, payload: Dict) -> Dict:
        """Soft delete product"""
        from web_knowledge.models import Product
        
        product_data = payload['product']
        
        external_id = f"woo_{product_data['id']}"
        
        # Soft delete
        deleted_count = Product.objects.filter(
            user=self.user,
            external_id=external_id
        ).update(is_active=False)
        
        # Signal will auto-cleanup chunks (web_knowledge/signals.py)
        
        logger.info(f"🗑️ Product soft-deleted: {external_id}")
        
        return {
            'status': 'success',
            'action': 'deleted',
            'deleted_count': deleted_count
        }
    
    def _calculate_content_hash(self, product_data: Dict) -> str:
        """Calculate hash from content fields only (for Smart Sync)"""
        critical_fields = [
            product_data.get('name', ''),
            product_data.get('short_description', ''),
            product_data.get('description', ''),
            ','.join(product_data.get('categories', [])),
            ','.join(product_data.get('tags', [])),
        ]
        content = '|'.join(critical_fields)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _safe_decimal(self, value) -> Decimal:
        """
        Safely convert to Decimal with overflow protection
        Max: 99,999,999.99 (fits in Decimal(10,2))
        """
        if not value:
            return None
        
        try:
            dec_value = Decimal(str(value))
            
            # Check if too large (max 8 digits before decimal)
            if dec_value >= Decimal('100000000'):  # 100 million
                logger.warning(f"Price too large: {dec_value}, capping at 99,999,999")
                return Decimal('99999999.99')
            
            return dec_value
            
        except (ValueError, TypeError, InvalidOperation) as e:
            logger.error(f"Invalid decimal value: {value} - {e}")
            return None

