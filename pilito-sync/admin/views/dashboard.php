<?php
/**
 * Main Dashboard - Professional & Minimal
 */
defined('ABSPATH') || exit;

global $wpdb;

$token = get_option('pilito_ps_api_token', '');

// Stats
$has_woocommerce = class_exists('WooCommerce');
$products_count = 0;
$products_synced = 0;
if ($has_woocommerce) {
    $stats = pilito_ps_get_sync_stats();
    $total_products = wp_count_posts('product');
    $products_count = $total_products->publish ?? 0;
    $products_synced = $stats['success'] ?? 0;
}

$pages_count = wp_count_posts('page')->publish ?? 0;
$pages_synced = $wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = '_pilito_page_sync_status' AND meta_value = 'success' AND post_id IN (SELECT ID FROM {$wpdb->posts} WHERE post_type = 'page' AND post_status = 'publish')");

$posts_count = wp_count_posts('post')->publish ?? 0;
$posts_synced = $wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = '_pilito_page_sync_status' AND meta_value = 'success' AND post_id IN (SELECT ID FROM {$wpdb->posts} WHERE post_type = 'post' AND post_status = 'publish')");

?>
<div class="wrap pilito-dashboard">
    
    <h1 class="pilito-page-title">
        <img src="<?php echo PILITO_PS_PLUGIN_URL . 'assets/logo.svg'; ?>" alt="<?php esc_attr_e('پیلیتو', 'pilito-sync'); ?>" class="pilito-page-logo">
        <?php esc_html_e('داشبورد', 'pilito-sync'); ?>
    </h1>
    <p class="pilito-page-description"><?php esc_html_e('وضعیت همگام‌سازی محتوای سایت با هوش مصنوعی', 'pilito-sync'); ?></p>
    
    <?php if (!$token): ?>
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
    
    <!-- Stats Grid -->
    <div class="pilito-stats-grid-new">
        
        <?php if ($has_woocommerce): ?>
        <div class="pilito-stat-card-new">
            <h3 class="stat-title"><?php esc_html_e('محصولات', 'pilito-sync'); ?></h3>
            <div class="stat-numbers">
                <span class="stat-main-number"><?php echo number_format_i18n($products_synced); ?></span>
                <span class="stat-total-number"><?php echo sprintf(__('از %s', 'pilito-sync'), number_format_i18n($products_count)); ?></span>
            </div>
            <p class="stat-description"><?php esc_html_e('همگام‌سازی شده', 'pilito-sync'); ?></p>
        </div>
        <?php endif; ?>
        
        <div class="pilito-stat-card-new">
            <h3 class="stat-title"><?php esc_html_e('صفحات', 'pilito-sync'); ?></h3>
            <div class="stat-numbers">
                <span class="stat-main-number"><?php echo number_format_i18n($pages_synced); ?></span>
                <span class="stat-total-number"><?php echo sprintf(__('از %s', 'pilito-sync'), number_format_i18n($pages_count)); ?></span>
            </div>
            <p class="stat-description"><?php esc_html_e('همگام‌سازی شده', 'pilito-sync'); ?></p>
        </div>
        
        <div class="pilito-stat-card-new">
            <h3 class="stat-title"><?php esc_html_e('نوشته‌ها', 'pilito-sync'); ?></h3>
            <div class="stat-numbers">
                <span class="stat-main-number"><?php echo number_format_i18n($posts_synced); ?></span>
                <span class="stat-total-number"><?php echo sprintf(__('از %s', 'pilito-sync'), number_format_i18n($posts_count)); ?></span>
            </div>
            <p class="stat-description"><?php esc_html_e('همگام‌سازی شده', 'pilito-sync'); ?></p>
        </div>
        
    </div>
    <?php endif; ?>
    
</div>
