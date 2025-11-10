# 🔌 WordPress Plugin - نمونه کدهای کامل

نمونه کدهای آماده برای پلاگین WordPress

---

## 📄 Main Plugin File

### fiko-woocommerce-sync.php

```php
<?php
/**
 * Plugin Name: Fiko WooCommerce Sync
 * Plugin URI: https://fiko.ai
 * Description: سینک خودکار محصولات WooCommerce با پلتفرم فیکو برای هوش مصنوعی
 * Version: 1.0.0
 * Author: Fiko Team
 * Author URI: https://fiko.ai
 * Text Domain: fiko-woocommerce-sync
 * Domain Path: /languages
 * Requires at least: 5.8
 * Requires PHP: 7.4
 * WC requires at least: 5.0
 * WC tested up to: 8.5
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 */

defined('ABSPATH') || exit;

// Plugin constants
define('FIKO_WC_SYNC_VERSION', '1.0.0');
define('FIKO_WC_SYNC_PLUGIN_FILE', __FILE__);
define('FIKO_WC_SYNC_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('FIKO_WC_SYNC_PLUGIN_URL', plugin_dir_url(__FILE__));
define('FIKO_WC_SYNC_PLUGIN_BASENAME', plugin_basename(__FILE__));

/**
 * Check if WooCommerce is active
 */
function fiko_wc_check_woocommerce() {
    if (!class_exists('WooCommerce')) {
        add_action('admin_notices', function() {
            ?>
            <div class="notice notice-error">
                <p><strong>Fiko WooCommerce Sync:</strong> این پلاگین نیاز به WooCommerce دارد. لطفاً ابتدا WooCommerce را نصب و فعال کنید.</p>
            </div>
            <?php
        });
        return false;
    }
    return true;
}

/**
 * Initialize plugin
 */
function fiko_wc_init() {
    // Load text domain
    load_plugin_textdomain('fiko-woocommerce-sync', false, dirname(FIKO_WC_SYNC_PLUGIN_BASENAME) . '/languages');
    
    // Load classes
    require_once FIKO_WC_SYNC_PLUGIN_DIR . 'includes/helpers.php';
    require_once FIKO_WC_SYNC_PLUGIN_DIR . 'includes/class-fiko-api.php';
    require_once FIKO_WC_SYNC_PLUGIN_DIR . 'includes/class-fiko-hooks.php';
    
    // Initialize hooks
    Fiko_WC_Hooks::init();
    
    // Admin only
    if (is_admin()) {
        require_once FIKO_WC_SYNC_PLUGIN_DIR . 'admin/class-admin-page.php';
        Fiko_WC_Admin_Page::init();
    }
}

// Check WooCommerce and initialize
if (fiko_wc_check_woocommerce()) {
    add_action('plugins_loaded', 'fiko_wc_init');
}

/**
 * Activation hook
 */
register_activation_hook(__FILE__, function() {
    // Set default options
    if (!get_option('fiko_wc_api_token')) {
        add_option('fiko_wc_api_token', '');
    }
    if (!get_option('fiko_wc_enable_logging')) {
        add_option('fiko_wc_enable_logging', false);
    }
    if (!get_option('fiko_wc_api_url')) {
        add_option('fiko_wc_api_url', 'https://api.fiko.ai/api/integrations/woocommerce');
    }
});

/**
 * Deactivation hook
 */
register_deactivation_hook(__FILE__, function() {
    // Clean up transients
    global $wpdb;
    $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_fiko_sync_%'");
    $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_timeout_fiko_sync_%'");
});
```

---

## 🌐 API Communication Class

### includes/class-fiko-api.php

```php
<?php
/**
 * Fiko API Communication Class
 * Handles all communication with Fiko backend
 */

defined('ABSPATH') || exit;

class Fiko_WC_API {
    
    /**
     * Sync product to Fiko
     */
    public static function sync_product($product_id, $event_type = 'product.updated') {
        $token = get_option('fiko_wc_api_token');
        
        if (empty($token)) {
            self::log('No API token configured', 'error');
            return new WP_Error('no_token', 'API Token تنظیم نشده است');
        }
        
        // Debounce check (prevent spam)
        $transient_key = 'fiko_sync_' . $product_id;
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
     * Delete product from Fiko
     */
    public static function delete_product($product_id) {
        $token = get_option('fiko_wc_api_token');
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
        $event_id = 'wc_' . date('Y_m_d_His') . '_' . $product->get_id() . '_' . wp_rand(1000, 9999);
        
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
        $url = get_option('fiko_wc_api_url');
        if (empty($url)) {
            $url = 'https://api.fiko.ai/api/integrations/woocommerce';
        }
        return rtrim($url, '/');
    }
    
    /**
     * Log product success
     */
    private static function log_product_success($product_id, $action) {
        update_post_meta($product_id, '_fiko_last_sync', current_time('mysql'));
        update_post_meta($product_id, '_fiko_sync_status', 'success');
        update_post_meta($product_id, '_fiko_sync_action', $action);
        delete_post_meta($product_id, '_fiko_sync_error');
    }
    
    /**
     * Log product error
     */
    private static function log_product_error($product_id, $message) {
        update_post_meta($product_id, '_fiko_last_sync', current_time('mysql'));
        update_post_meta($product_id, '_fiko_sync_status', 'error');
        update_post_meta($product_id, '_fiko_sync_error', $message);
    }
    
    /**
     * General logging
     */
    private static function log($message, $level = 'info') {
        if (!get_option('fiko_wc_enable_logging')) {
            return;
        }
        
        $log_entry = sprintf(
            '[%s] [%s] %s',
            date('Y-m-d H:i:s'),
            strtoupper($level),
            $message
        );
        
        error_log('Fiko WC Sync: ' . $log_entry);
    }
}
```

---

## 🎣 WooCommerce Hooks Class

### includes/class-fiko-hooks.php

```php
<?php
/**
 * WooCommerce Hooks Handler
 * Listens to WooCommerce events and triggers sync
 */

defined('ABSPATH') || exit;

class Fiko_WC_Hooks {
    
    /**
     * Initialize hooks
     */
    public static function init() {
        // Only if token exists
        if (!get_option('fiko_wc_api_token')) {
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
        
        Fiko_WC_API::delete_product($post_id);
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
        Fiko_WC_API::sync_product($product_id, $event_type);
    }
    
    /**
     * Add Fiko sync column to products list
     */
    public static function add_sync_column($columns) {
        $new_columns = [];
        
        foreach ($columns as $key => $value) {
            $new_columns[$key] = $value;
            
            // Add after 'name' column
            if ($key === 'name') {
                $new_columns['fiko_sync'] = '🔄 Fiko';
            }
        }
        
        return $new_columns;
    }
    
    /**
     * Render Fiko sync column
     */
    public static function render_sync_column($column, $post_id) {
        if ($column !== 'fiko_sync') {
            return;
        }
        
        $status = get_post_meta($post_id, '_fiko_sync_status', true);
        $last_sync = get_post_meta($post_id, '_fiko_last_sync', true);
        
        if ($status === 'success') {
            echo '<span style="color: green;" title="آخرین سینک: ' . esc_attr($last_sync) . '">✅</span>';
        } elseif ($status === 'error') {
            $error = get_post_meta($post_id, '_fiko_sync_error', true);
            echo '<span style="color: red;" title="خطا: ' . esc_attr($error) . '">❌</span>';
        } else {
            echo '<span style="color: gray;" title="هنوز سینک نشده">—</span>';
        }
    }
}
```

---

## 🛠️ Helper Functions

### includes/helpers.php

```php
<?php
/**
 * Helper functions
 */

defined('ABSPATH') || exit;

/**
 * Check if token is configured
 */
function fiko_wc_is_configured() {
    $token = get_option('fiko_wc_api_token');
    return !empty($token);
}

/**
 * Get sync statistics
 */
function fiko_wc_get_sync_stats() {
    global $wpdb;
    
    $total = $wpdb->get_var("
        SELECT COUNT(*)
        FROM {$wpdb->postmeta}
        WHERE meta_key = '_fiko_sync_status'
    ");
    
    $success = $wpdb->get_var("
        SELECT COUNT(*)
        FROM {$wpdb->postmeta}
        WHERE meta_key = '_fiko_sync_status'
        AND meta_value = 'success'
    ");
    
    $error = $wpdb->get_var("
        SELECT COUNT(*)
        FROM {$wpdb->postmeta}
        WHERE meta_key = '_fiko_sync_status'
        AND meta_value = 'error'
    ");
    
    return [
        'total' => (int) $total,
        'success' => (int) $success,
        'error' => (int) $error,
    ];
}

/**
 * Format date for display
 */
function fiko_wc_format_date($date) {
    if (empty($date)) {
        return '—';
    }
    
    return date_i18n(
        get_option('date_format') . ' ' . get_option('time_format'),
        strtotime($date)
    );
}
```

---

## 🎨 Admin Settings Page

### admin/class-admin-page.php

```php
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
```

---

برای ادامه کدهای Admin UI (HTML, CSS, JS) به فایل معماری اصلی مراجعه کنید یا در صورت نیاز درخواست کنید.

