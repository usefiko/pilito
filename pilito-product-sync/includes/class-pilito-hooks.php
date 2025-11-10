<?php
/**
 * WooCommerce Hooks Handler
 * Listens to WooCommerce events and triggers sync
 */

defined('ABSPATH') || exit;

class Pilito_PS_Hooks {
    
    /**
     * Initialize hooks
     */
    public static function init() {
        // Only if token exists
        if (!get_option('pilito_ps_api_token')) {
            return;
        }
        
        // Product created
        add_action('woocommerce_new_product', [__CLASS__, 'on_product_created'], 10, 1);
        
        // Product updated
        add_action('woocommerce_update_product', [__CLASS__, 'on_product_updated'], 10, 1);
        
        // Product deleted
        add_action('before_delete_post', [__CLASS__, 'on_product_deleted'], 10, 1);
        
        // Add sync status column to products list
        add_filter('manage_product_posts_columns', [__CLASS__, 'add_sync_column']);
        add_action('manage_product_posts_custom_column', [__CLASS__, 'render_sync_column'], 10, 2);
    }
    
    /**
     * Handle product created
     */
    public static function on_product_created($product_id) {
        self::sync_product($product_id, 'product.created');
    }
    
    /**
     * Handle product updated
     */
    public static function on_product_updated($product_id) {
        self::sync_product($product_id, 'product.updated');
    }
    
    /**
     * Handle product deleted
     */
    public static function on_product_deleted($post_id) {
        if (get_post_type($post_id) !== 'product') {
            return;
        }
        
        Pilito_PS_API::delete_product($post_id);
    }
    
    /**
     * Sync product (with validation)
     */
    private static function sync_product($product_id, $event_type) {
        // Validate post type
        if (get_post_type($product_id) !== 'product') {
            return;
        }
        
        // Skip auto-saves and revisions
        if (wp_is_post_autosave($product_id) || wp_is_post_revision($product_id)) {
            return;
        }
        
        // Skip if product is trash
        if (get_post_status($product_id) === 'trash') {
            return;
        }
        
        // Sync
        Pilito_PS_API::sync_product($product_id, $event_type);
    }
    
    /**
     * Add Pilito sync column to products list
     */
    public static function add_sync_column($columns) {
        $new_columns = [];
        
        foreach ($columns as $key => $value) {
            $new_columns[$key] = $value;
            
            // Add after 'name' column
            if ($key === 'name') {
                $new_columns['pilito_sync'] = '🔄 Pilito';
            }
        }
        
        return $new_columns;
    }
    
    /**
     * Render Pilito sync column
     */
    public static function render_sync_column($column, $post_id) {
        if ($column !== 'pilito_sync') {
            return;
        }
        
        $status = get_post_meta($post_id, '_pilito_sync_status', true);
        $last_sync = get_post_meta($post_id, '_pilito_last_sync', true);
        
        if ($status === 'success') {
            echo '<span style="color: green;" title="آخرین سینک: ' . esc_attr($last_sync) . '">✅</span>';
        } elseif ($status === 'error') {
            $error = get_post_meta($post_id, '_pilito_sync_error', true);
            echo '<span style="color: red;" title="خطا: ' . esc_attr($error) . '">❌</span>';
        } else {
            echo '<span style="color: gray;" title="هنوز سینک نشده">—</span>';
        }
    }
}
