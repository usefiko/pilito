<?php
/**
 * Pilito API Communication Class
 * Handles all communication with Pilito backend
 */

defined('ABSPATH') || exit;

class Pilito_PS_API {
    
    /**
     * Sync product to Pilito
     */
    public static function sync_product($product_id, $event_type = 'product.updated') {
        $token = get_option('pilito_ps_api_token');
        
        if (empty($token)) {
            self::log('No API token configured', 'error');
            return new WP_Error('no_token', 'API Token تنظیم نشده است');
        }
        
        // Debounce check (prevent spam)
        $transient_key = 'pilito_sync_' . $product_id;
        if (get_transient($transient_key)) {
            self::log("Product $product_id debounced (too soon)", 'debug');
            return new WP_Error('debounced', 'درخواست قبلی در حال پردازش است');
        }
        set_transient($transient_key, true, 30); // 30 seconds
        
        // Get product
        $product = wc_get_product($product_id);
        if (!$product) {
            self::log("Product $product_id not found", 'error');
            return new WP_Error('invalid_product', 'محصول یافت نشد');
        }
        
        // Build payload
        $payload = self::build_payload($product, $event_type);
        
        self::log("Syncing product: {$product->get_name()} (ID: $product_id, Type: $event_type)", 'info');
        
        // Send request (non-blocking for performance)
        $response = wp_remote_post(self::get_api_url() . '/webhook/', [
            'headers' => [
                'Content-Type' => 'application/json',
                'Authorization' => 'Bearer ' . $token,
            ],
            'body' => wp_json_encode($payload),
            'timeout' => 10,
            'blocking' => false, // Non-blocking! Returns immediately
            'sslverify' => true,
        ]);
        
        if (is_wp_error($response)) {
            self::log("Sync failed: " . $response->get_error_message(), 'error');
            self::log_product_error($product_id, $response->get_error_message());
            return $response;
        }
        
        // Log success
        self::log_product_success($product_id, $event_type);
        
        return true;
    }
    
    /**
     * Delete product from Pilito
     */
    public static function delete_product($product_id) {
        $token = get_option('pilito_ps_api_token');
        if (empty($token)) {
            return;
        }
        
        $product = wc_get_product($product_id);
        if (!$product) {
            return;
        }
        
        $payload = self::build_payload($product, 'product.deleted');
        
        self::log("Deleting product: {$product->get_name()} (ID: $product_id)", 'info');
        
        wp_remote_post(self::get_api_url() . '/webhook/', [
            'headers' => [
                'Content-Type' => 'application/json',
                'Authorization' => 'Bearer ' . $token,
            ],
            'body' => wp_json_encode($payload),
            'timeout' => 10,
            'blocking' => false,
        ]);
    }
    
    /**
     * Test API connection
     */
    public static function test_connection($token) {
        $response = wp_remote_get(self::get_api_url() . '/health/', [
            'headers' => [
                'Authorization' => 'Bearer ' . $token,
            ],
            'timeout' => 15,
        ]);
        
        if (is_wp_error($response)) {
            return [
                'success' => false,
                'message' => $response->get_error_message()
            ];
        }
        
        $code = wp_remote_retrieve_response_code($response);
        $body = json_decode(wp_remote_retrieve_body($response), true);
        
        if ($code === 200 && isset($body['status']) && $body['status'] === 'ok') {
            return [
                'success' => true,
                'message' => 'اتصال برقرار است! ✅',
                'data' => $body
            ];
        }
        
        return [
            'success' => false,
            'message' => $body['error'] ?? 'خطای ناشناخته (کد: ' . $code . ')'
        ];
    }
    
    /**
     * Build JSON payload
     */
    private static function build_payload($product, $event_type) {
        $event_id = 'wc_' . gmdate('Y_m_d_His') . '_' . $product->get_id() . '_' . wp_rand(1000, 9999);
        
        return [
            'event_id' => $event_id,
            'event_type' => $event_type,
            'product' => [
                'id' => $product->get_id(),
                'sku' => $product->get_sku() ?: '',
                'name' => $product->get_name(),
                'short_description' => $product->get_short_description(),
                'description' => $product->get_description(),
                'price' => (float) $product->get_price(),
                'regular_price' => (float) $product->get_regular_price(),
                'sale_price' => $product->get_sale_price() ? (float) $product->get_sale_price() : null,
                'currency' => get_woocommerce_currency(),
                'stock_quantity' => $product->get_stock_quantity(),
                'stock_status' => $product->get_stock_status(),
                'categories' => self::get_product_categories($product),
                'tags' => self::get_product_tags($product),
                'image' => wp_get_attachment_url($product->get_image_id()) ?: '',
                'gallery' => self::get_gallery_images($product),
                'permalink' => get_permalink($product->get_id()),
                'type' => $product->get_type(),
                'on_sale' => $product->is_on_sale(),
                'date_modified' => $product->get_date_modified() ? $product->get_date_modified()->format('c') : null,
            ]
        ];
    }
    
    /**
     * Get product categories
     */
    private static function get_product_categories($product) {
        $terms = get_the_terms($product->get_id(), 'product_cat');
        if (!$terms || is_wp_error($terms)) {
            return [];
        }
        return array_map(function($term) {
            return $term->name;
        }, $terms);
    }
    
    /**
     * Get product tags
     */
    private static function get_product_tags($product) {
        $terms = get_the_terms($product->get_id(), 'product_tag');
        if (!$terms || is_wp_error($terms)) {
            return [];
        }
        return array_map(function($term) {
            return $term->name;
        }, $terms);
    }
    
    /**
     * Get gallery images
     */
    private static function get_gallery_images($product) {
        $image_ids = $product->get_gallery_image_ids();
        $images = [];
        
        foreach ($image_ids as $image_id) {
            $url = wp_get_attachment_url($image_id);
            if ($url) {
                $images[] = $url;
            }
        }
        
        return $images;
    }
    
    /**
     * Get API URL
     */
    private static function get_api_url() {
        $url = get_option('pilito_ps_api_url');
        if (empty($url)) {
            $url = 'https://api.pilito.com/api/integrations/woocommerce';
        }
        return rtrim($url, '/');
    }
    
    /**
     * Log product success
     */
    private static function log_product_success($product_id, $action) {
        update_post_meta($product_id, '_pilito_last_sync', current_time('mysql'));
        update_post_meta($product_id, '_pilito_sync_status', 'success');
        update_post_meta($product_id, '_pilito_sync_action', $action);
        delete_post_meta($product_id, '_pilito_sync_error');
    }
    
    /**
     * Log product error
     */
    private static function log_product_error($product_id, $message) {
        update_post_meta($product_id, '_pilito_last_sync', current_time('mysql'));
        update_post_meta($product_id, '_pilito_sync_status', 'error');
        update_post_meta($product_id, '_pilito_sync_error', $message);
    }
    
    /**
     * General logging
     */
    private static function log($message, $level = 'info') {
        if (!get_option('pilito_ps_enable_logging')) {
            return;
        }
        
        $log_entry = sprintf(
            '[%s] [%s] %s',
            gmdate('Y-m-d H:i:s'),
            strtoupper($level),
            $message
        );
        
        // Only log if explicitly enabled
        if (defined('WP_DEBUG') && WP_DEBUG && defined('WP_DEBUG_LOG') && WP_DEBUG_LOG) {
            error_log('Pilito Product Sync: ' . $log_entry);
        }
    }
}
