<?php
/**
 * Admin Settings Page
 */

defined('ABSPATH') || exit;

class Pilito_PS_Admin_Page {
    
    /**
     * Initialize
     */
    public static function init() {
        add_action('admin_menu', [__CLASS__, 'add_menu']);
        add_action('admin_init', [__CLASS__, 'register_settings']);
        add_action('admin_enqueue_scripts', [__CLASS__, 'enqueue_assets']);
        
        // AJAX handlers
        add_action('wp_ajax_pilito_ps_test_connection', [__CLASS__, 'ajax_test_connection']);
    }
    
    /**
     * Add admin menu
     */
    public static function add_menu() {
        add_submenu_page(
            'woocommerce',
            'پیلیتو - سینک محصولات',
            'پیلیتو Sync',
            'manage_woocommerce',
            'pilito-product-sync',
            [__CLASS__, 'render_page']
        );
    }
    
    /**
     * Register settings
     */
    public static function register_settings() {
        register_setting('pilito_ps_sync', 'pilito_ps_api_token', [
            'type' => 'string',
            'sanitize_callback' => 'sanitize_text_field',
        ]);
        
        register_setting('pilito_ps_sync', 'pilito_ps_enable_logging', [
            'type' => 'boolean',
        ]);
        
        register_setting('pilito_ps_sync', 'pilito_ps_api_url', [
            'type' => 'string',
            'sanitize_callback' => 'esc_url_raw',
            'default' => 'https://api.pilito.com/api/integrations/woocommerce',
        ]);
    }
    
    /**
     * Enqueue assets
     */
    public static function enqueue_assets($hook) {
        if ($hook !== 'woocommerce_page_pilito-product-sync') {
            return;
        }
        
        wp_enqueue_style(
            'pilito-ps-admin',
            PILITO_PS_PLUGIN_URL . 'admin/css/admin.css',
            [],
            PILITO_PS_VERSION
        );
        
        wp_enqueue_script(
            'pilito-ps-admin',
            PILITO_PS_PLUGIN_URL . 'admin/js/admin.js',
            ['jquery'],
            PILITO_PS_VERSION,
            true
        );
        
        wp_localize_script('pilito-ps-admin', 'pilitoPS', [
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('pilito_ps_test'),
        ]);
    }
    
    /**
     * Render settings page
     */
    public static function render_page() {
        include PILITO_PS_PLUGIN_DIR . 'admin/views/settings.php';
    }
    
    /**
     * AJAX: Test connection
     */
    public static function ajax_test_connection() {
        check_ajax_referer('pilito_ps_test', 'nonce');
        
        if (!current_user_can('manage_woocommerce')) {
            wp_send_json_error(['message' => 'عدم دسترسی']);
        }
        
        $token = sanitize_text_field($_POST['token'] ?? '');
        
        if (empty($token)) {
            wp_send_json_error(['message' => 'لطفاً ابتدا token را وارد کنید']);
        }
        
        $result = Pilito_PS_API::test_connection($token);
        
        if ($result['success']) {
            wp_send_json_success($result);
        } else {
            wp_send_json_error($result);
        }
    }
}
