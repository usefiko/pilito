<?php
/**
 * Products Sync Page - Minimal & Professional
 */
defined('ABSPATH') || exit;

$token = get_option('pilito_ps_api_token', '');
$has_woocommerce = class_exists('WooCommerce');

// Stats
$products_count = 0;
$products_synced = 0;
if ($has_woocommerce) {
    $stats = pilito_ps_get_sync_stats();
    $total_products = wp_count_posts('product');
    $products_count = $total_products->publish ?? 0;
    $products_synced = $stats['success'] ?? 0;
}

?>
<div class="wrap pilito-dashboard">
    
    <h1 class="pilito-page-title">
        <img src="<?php echo PILITO_PS_PLUGIN_URL . 'assets/logo.svg'; ?>" alt="<?php esc_attr_e('پیلیتو', 'pilito-sync'); ?>" class="pilito-page-logo">
        <?php esc_html_e('همگام‌سازی محصولات', 'pilito-sync'); ?>
    </h1>
    <p class="pilito-page-description"><?php esc_html_e('محصولات فروشگاه خود را با هوش مصنوعی پیلیتو همگام کنید', 'pilito-sync'); ?></p>
    
    <?php if (!$has_woocommerce): ?>
    <!-- WooCommerce Not Installed -->
    <div class="pilito-card">
        <div class="pilito-card-header">
            <h2 class="pilito-card-title"><?php esc_html_e('WooCommerce نصب نشده است', 'pilito-sync'); ?></h2>
        </div>
        <div class="pilito-form-group">
            <p><?php esc_html_e('برای همگام‌سازی محصولات، نیاز به نصب و فعال‌سازی WooCommerce دارید.', 'pilito-sync'); ?></p>
            <p><a href="<?php echo admin_url('plugin-install.php?s=woocommerce&tab=search&type=term'); ?>" class="pilito-btn pilito-btn-primary"><?php esc_html_e('نصب WooCommerce', 'pilito-sync'); ?></a></p>
        </div>
    </div>
    <?php elseif (!$token): ?>
    <!-- No Token Alert -->
    <div class="pilito-card">
        <div class="pilito-card-header">
            <h2 class="pilito-card-title"><?php esc_html_e('توکن API تنظیم نشده است', 'pilito-sync'); ?></h2>
        </div>
        <div class="pilito-form-group">
            <p><?php esc_html_e('لطفاً ابتدا از بخش', 'pilito-sync'); ?> <a href="<?php echo admin_url('admin.php?page=pilito-settings'); ?>"><?php esc_html_e('تنظیمات', 'pilito-sync'); ?></a> <?php esc_html_e('توکن خود را تنظیم کنید.', 'pilito-sync'); ?></p>
        </div>
    </div>
    <?php else: ?>
    
    <!-- Stats -->
    <div class="pilito-stats-grid-new">
        <div class="pilito-stat-card-new">
            <h3 class="stat-title"><?php esc_html_e('محصولات', 'pilito-sync'); ?></h3>
            <div class="stat-numbers">
                <span class="stat-main-number"><?php echo number_format_i18n($products_synced); ?></span>
                <span class="stat-total-number"><?php echo sprintf(__('از %s', 'pilito-sync'), number_format_i18n($products_count)); ?></span>
            </div>
            <p class="stat-description"><?php esc_html_e('همگام‌سازی شده', 'pilito-sync'); ?></p>
        </div>
    </div>
    
    <!-- Sync Button -->
    <div class="pilito-card">
        <div class="pilito-card-header">
            <h2 class="pilito-card-title"><?php esc_html_e('همگام‌سازی دستی', 'pilito-sync'); ?></h2>
        </div>
        <div class="pilito-form-group">
            <p><?php esc_html_e('برای همگام‌سازی همه محصولات با پیلیتو، دکمه زیر را کلیک کنید. این فرآیند ممکن است چند دقیقه طول بکشد.', 'pilito-sync'); ?></p>
        </div>
        <div class="pilito-action-bar">
            <div class="pilito-action-right">
                <button id="pilito-bulk-sync" class="pilito-btn pilito-btn-primary">
                    <?php esc_html_e('همگام‌سازی همه محصولات', 'pilito-sync'); ?>
                </button>
            </div>
        </div>
    </div>
    
    <!-- Progress -->
    <div id="pilito-bulk-sync-progress" class="pilito-card" style="display:none;">
        <div class="pilito-card-header">
            <h2 class="pilito-card-title"><?php esc_html_e('در حال همگام‌سازی...', 'pilito-sync'); ?></h2>
        </div>
        <div class="pilito-form-group">
            <div class="pilito-progress-container">
                <div id="pilito-progress-bar" class="pilito-progress-bar"></div>
            </div>
            <div id="pilito-progress-text" class="pilito-progress-text"></div>
            <div id="pilito-progress-details" class="pilito-progress-details"></div>
        </div>
    </div>
    
    <!-- Test Result -->
    <div id="pilito-test-result" style="display:none;"></div>
    
    <?php endif; ?>
    
</div>

