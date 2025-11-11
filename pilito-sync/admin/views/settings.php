<?php
/**
 * Settings Page - Minimal & Professional
 */
defined('ABSPATH') || exit;

$token = get_option('pilito_ps_api_token', '');
$enable_logging = get_option('pilito_ps_enable_logging', false);
$user_email = '';

// Handle settings save
if (isset($_POST['pilito_ps_save_settings']) && check_admin_referer('pilito_ps_settings')) {
    update_option('pilito_ps_api_token', sanitize_text_field($_POST['pilito_ps_api_token']));
    update_option('pilito_ps_enable_logging', isset($_POST['pilito_ps_enable_logging']));
    echo '<div class="notice notice-success is-dismissible"><p>' . __('تنظیمات ذخیره شد.', 'pilito-sync') . '</p></div>';
    $token = get_option('pilito_ps_api_token');
    $enable_logging = get_option('pilito_ps_enable_logging');
}

?>
<div class="wrap pilito-dashboard">
    
    <h1 class="pilito-page-title">
        <img src="<?php echo PILITO_PS_PLUGIN_URL . 'assets/logo.svg'; ?>" alt="<?php esc_attr_e('پیلیتو', 'pilito-sync'); ?>" class="pilito-page-logo">
        <?php esc_html_e('تنظیمات', 'pilito-sync'); ?>
    </h1>
    <p class="pilito-page-description"><?php esc_html_e('تنظیمات اتصال به پلتفرم پیلیتو', 'pilito-sync'); ?></p>
    
    <!-- Settings Form -->
    <div class="pilito-card">
        <div class="pilito-card-header">
            <h2 class="pilito-card-title"><?php esc_html_e('تنظیمات اتصال', 'pilito-sync'); ?></h2>
        </div>
        
        <form method="post" action="">
            <?php wp_nonce_field('pilito_ps_settings'); ?>
            
            <div class="pilito-form-group">
                <label for="pilito_ps_api_token" class="pilito-label"><?php esc_html_e('API Token', 'pilito-sync'); ?></label>
                <input 
                    type="text" 
                    id="pilito_ps_api_token" 
                    name="pilito_ps_api_token" 
                    value="<?php echo esc_attr($token); ?>" 
                    class="pilito-input"
                    placeholder="<?php esc_attr_e('توکن API خود را وارد کنید', 'pilito-sync'); ?>"
                >
                <span class="pilito-input-hint">
                    <?php esc_html_e('از داشبورد پیلیتو دریافت کنید.', 'pilito-sync'); ?>
                </span>
            </div>
            
            <div class="pilito-form-group">
                <label>
                    <input 
                        type="checkbox" 
                        name="pilito_ps_enable_logging" 
                        <?php checked($enable_logging); ?>
                    >
                    <?php esc_html_e('فعال‌سازی لاگ‌گذاری (برای عیب‌یابی)', 'pilito-sync'); ?>
                </label>
            </div>
            
            <div class="pilito-action-bar">
                <div class="pilito-action-left">
                    <?php if ($token): ?>
                    <span class="pilito-connection-status connected">● <?php esc_html_e('متصل', 'pilito-sync'); ?></span>
                    <span id="pilito-user-email" style="margin-right: 12px; color: #666; font-size: 13px;"></span>
                    <?php else: ?>
                    <span class="pilito-connection-status disconnected">● <?php esc_html_e('غیرمتصل', 'pilito-sync'); ?></span>
                    <?php endif; ?>
                </div>
                <div class="pilito-action-right">
                    <button type="button" id="pilito-test-connection" class="pilito-btn pilito-btn-secondary">
                        <?php esc_html_e('تست اتصال', 'pilito-sync'); ?>
                    </button>
                    <button type="submit" name="pilito_ps_save_settings" class="pilito-btn pilito-btn-primary">
                        <?php esc_html_e('ذخیره تنظیمات', 'pilito-sync'); ?>
                    </button>
                </div>
            </div>
        </form>
    </div>
    
    <!-- Test Result -->
    <div id="pilito-test-result" style="display:none;"></div>
    
</div>

