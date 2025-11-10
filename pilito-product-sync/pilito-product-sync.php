<?php
/**
 * Plugin Name: Pilito Product Sync
 * Plugin URI: https://pilito.com
 * Description: سینک خودکار محصولات فروشگاه با پلتفرم پیلیتو برای استفاده از هوش مصنوعی
 * Version: 1.0.0
 * Author: Pilito Team
 * Author URI: https://pilito.com
 * Text Domain: pilito-product-sync
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
define('PILITO_PS_VERSION', '1.0.0');
define('PILITO_PS_PLUGIN_FILE', __FILE__);
define('PILITO_PS_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('PILITO_PS_PLUGIN_URL', plugin_dir_url(__FILE__));
define('PILITO_PS_PLUGIN_BASENAME', plugin_basename(__FILE__));

/**
 * Initialize plugin
 */
function pilito_ps_init() {
    // Check if WooCommerce is active (after all plugins loaded)
    if (!class_exists('WooCommerce')) {
        add_action('admin_notices', function() {
            ?>
            <div class="notice notice-error">
                <p><strong>Pilito Product Sync:</strong> این پلاگین نیاز به WooCommerce دارد. لطفاً ابتدا WooCommerce را نصب و فعال کنید.</p>
            </div>
            <?php
        });
        return;
    }
    
    // Load text domain
    load_plugin_textdomain('pilito-product-sync', false, dirname(PILITO_PS_PLUGIN_BASENAME) . '/languages');
    
    // Load classes
    require_once PILITO_PS_PLUGIN_DIR . 'includes/helpers.php';
    require_once PILITO_PS_PLUGIN_DIR . 'includes/class-pilito-api.php';
    require_once PILITO_PS_PLUGIN_DIR . 'includes/class-pilito-hooks.php';
    
    // Initialize hooks
    Pilito_PS_Hooks::init();
    
    // Admin only
    if (is_admin()) {
        require_once PILITO_PS_PLUGIN_DIR . 'admin/class-admin-page.php';
        Pilito_PS_Admin_Page::init();
    }
}

// Initialize after all plugins loaded
add_action('plugins_loaded', 'pilito_ps_init');

/**
 * Activation hook
 */
register_activation_hook(__FILE__, function() {
    // Set default options
    if (!get_option('pilito_ps_api_token')) {
        add_option('pilito_ps_api_token', '');
    }
    if (!get_option('pilito_ps_enable_logging')) {
        add_option('pilito_ps_enable_logging', false);
    }
    if (!get_option('pilito_ps_api_url')) {
        add_option('pilito_ps_api_url', 'https://api.pilito.com/api/integrations/woocommerce');
    }
});

/**
 * Deactivation hook
 */
register_deactivation_hook(__FILE__, function() {
    // Clean up transients
    global $wpdb;
    $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_pilito_sync_%'");
    $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_timeout_pilito_sync_%'");
});

