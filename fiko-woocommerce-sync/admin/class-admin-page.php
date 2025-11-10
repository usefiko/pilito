<?php
/**
 * Admin Settings Page
 */

defined('ABSPATH') || exit;

class Fiko_WC_Admin_Page {
    
    /**
     * Initialize
     */
    public static function init() {
        add_action('admin_menu', [__CLASS__, 'add_menu']);
        add_action('admin_init', [__CLASS__, 'register_settings']);
        add_action('admin_enqueue_scripts', [__CLASS__, 'enqueue_assets']);
        
        // AJAX handlers
        add_action('wp_ajax_fiko_wc_test_connection', [__CLASS__, 'ajax_test_connection']);
    }
    
    /**
     * Add admin menu
     */
    public static function add_menu() {
        add_submenu_page(
            'woocommerce',
            'فیکو - سینک محصولات',
            'فیکو Sync',
            'manage_woocommerce',
            'fiko-wc-sync',
            [__CLASS__, 'render_page']
        );
    }
    
    /**
     * Register settings
     */
    public static function register_settings() {
        register_setting('fiko_wc_sync', 'fiko_wc_api_token', [
            'type' => 'string',
            'sanitize_callback' => 'sanitize_text_field',
        ]);
        
        register_setting('fiko_wc_sync', 'fiko_wc_enable_logging', [
            'type' => 'boolean',
        ]);
        
        register_setting('fiko_wc_sync', 'fiko_wc_api_url', [
            'type' => 'string',
            'sanitize_callback' => 'esc_url_raw',
            'default' => 'https://api.fiko.ai/api/integrations/woocommerce',
        ]);
    }
    
    /**
     * Enqueue assets
     */
    public static function enqueue_assets($hook) {
        if ($hook !== 'woocommerce_page_fiko-wc-sync') {
            return;
        }
        
        wp_enqueue_style(
            'fiko-wc-admin',
            FIKO_WC_SYNC_PLUGIN_URL . 'admin/css/admin.css',
            [],
            FIKO_WC_SYNC_VERSION
        );
        
        wp_enqueue_script(
            'fiko-wc-admin',
            FIKO_WC_SYNC_PLUGIN_URL . 'admin/js/admin.js',
            ['jquery'],
            FIKO_WC_SYNC_VERSION,
            true
        );
        
        wp_localize_script('fiko-wc-admin', 'fikoWC', [
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('fiko_wc_test'),
        ]);
    }
    
    /**
     * Render settings page
     */
    public static function render_page() {
        include FIKO_WC_SYNC_PLUGIN_DIR . 'admin/views/settings.php';
    }
    
    /**
     * AJAX: Test connection
     */
    public static function ajax_test_connection() {
        check_ajax_referer('fiko_wc_test', 'nonce');
        
        if (!current_user_can('manage_woocommerce')) {
            wp_send_json_error(['message' => 'عدم دسترسی']);
        }
        
        $token = sanitize_text_field($_POST['token'] ?? '');
        
        if (empty($token)) {
            wp_send_json_error(['message' => 'لطفاً ابتدا token را وارد کنید']);
        }
        
        $result = Fiko_WC_API::test_connection($token);
        
        if ($result['success']) {
            wp_send_json_success($result);
        } else {
            wp_send_json_error($result);
        }
    }
}

