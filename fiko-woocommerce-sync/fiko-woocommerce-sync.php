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

