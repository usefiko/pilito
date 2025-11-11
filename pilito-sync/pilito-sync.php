<?php
/**
 * Plugin Name: پیلیتو - همگام‌سازی
 * Plugin URI: https://pilito.com
 * Description: همگام‌سازی خودکار محتوای سایت (محصولات، صفحات و نوشته‌ها) با پلتفرم پیلیتو برای استفاده از هوش مصنوعی
 * Version: 3.1.0
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
define('PILITO_PS_VERSION', '3.1.0');
define('PILITO_PS_PLUGIN_FILE', __FILE__);
define('PILITO_PS_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('PILITO_PS_PLUGIN_URL', plugin_dir_url(__FILE__));
define('PILITO_PS_PLUGIN_BASENAME', plugin_basename(__FILE__));

/**
 * Initialize plugin
 */
function pilito_ps_init() {
    // WooCommerce اختیاری است - اگر نباشه فقط همگام‌سازی صفحات کار می‌کنه
    if (!class_exists('WooCommerce')) {
        add_action('admin_notices', function() {
            if (get_option('pilito_ps_hide_wc_notice')) {
                return;
            }
            ?>
            <div class="notice notice-info is-dismissible" data-notice="pilito-wc">
                <p><strong>پیلیتو:</strong> برای همگام‌سازی محصولات، نیاز به نصب WooCommerce دارید. در غیر این صورت می‌توانید فقط از همگام‌سازی صفحات و نوشته‌ها استفاده کنید.</p>
            </div>
            <script>
            jQuery(document).on('click', '.notice[data-notice="pilito-wc"] .notice-dismiss', function() {
                jQuery.post(ajaxurl, {action: 'pilito_hide_wc_notice'});
            });
            </script>
            <?php
        });
    }
    
    // Load text domain based on WordPress locale
    $locale = apply_filters('plugin_locale', get_locale(), 'pilito-product-sync');
    load_textdomain('pilito-product-sync', WP_LANG_DIR . '/pilito-product-sync/pilito-product-sync-' . $locale . '.mo');
    load_plugin_textdomain('pilito-product-sync', false, dirname(PILITO_PS_PLUGIN_BASENAME) . '/languages');
    
    // Load classes
    require_once PILITO_PS_PLUGIN_DIR . 'includes/helpers.php';
    require_once PILITO_PS_PLUGIN_DIR . 'includes/class-pilito-api.php';
    require_once PILITO_PS_PLUGIN_DIR . 'includes/class-pilito-content.php';
    
    // Initialize content sync (always available)
    Pilito_PS_Content::init();
    
    // Initialize hooks only if WooCommerce exists
    if (class_exists('WooCommerce')) {
        require_once PILITO_PS_PLUGIN_DIR . 'includes/class-pilito-hooks.php';
        Pilito_PS_Hooks::init();
    }
    
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

