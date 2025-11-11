<?php
/**
 * Main Dashboard - Products Sync
 */
defined('ABSPATH') || exit;

global $wpdb;

$token = get_option('pilito_ps_api_token', '');
$enable_logging = get_option('pilito_ps_enable_logging', false);

// Handle settings save
if (isset($_POST['pilito_ps_save_settings']) && check_admin_referer('pilito_ps_settings')) {
    update_option('pilito_ps_api_token', sanitize_text_field($_POST['pilito_ps_api_token']));
    update_option('pilito_ps_enable_logging', isset($_POST['pilito_ps_enable_logging']));
    update_option('pilito_ps_debug_mode', isset($_POST['pilito_ps_debug_mode']));
    echo '<div class="notice notice-success is-dismissible"><p>✅ تنظیمات ذخیره شد.</p></div>';
    $token = get_option('pilito_ps_api_token');
}

// آمار محصولات
$has_woocommerce = class_exists('WooCommerce');
$products_count = 0;
$products_synced = 0;
$not_synced = 0;
if ($has_woocommerce) {
    $stats = pilito_ps_get_sync_stats();
    $total_products = wp_count_posts('product');
    $products_count = $total_products->publish ?? 0;
    $products_synced = $stats['success'] ?? 0;
    $not_synced = $products_count - $products_synced;
}

// آمار صفحات
$pages_count = wp_count_posts('page')->publish ?? 0;
$pages_synced = $wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = '_pilito_page_sync_status' AND meta_value = 'success' AND post_id IN (SELECT ID FROM {$wpdb->posts} WHERE post_type = 'page' AND post_status = 'publish')");

// آمار نوشته‌ها
$posts_count = wp_count_posts('post')->publish ?? 0;
$posts_synced = $wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = '_pilito_page_sync_status' AND meta_value = 'success' AND post_id IN (SELECT ID FROM {$wpdb->posts} WHERE post_type = 'post' AND post_status = 'publish')");
?>

<div class="wrap pilito-dashboard">
    
    <h1 class="pilito-page-title">
        <img src="<?php echo PILITO_PS_PLUGIN_URL . 'assets/logo.svg'; ?>" alt="پیلیتو" class="pilito-page-logo">
        داشبورد پیلیتو
    </h1>
    <p class="pilito-page-description">وضعیت همگام‌سازی محتوای سایت با هوش مصنوعی</p>
    
    <!-- Stats: Minimal & Clean -->
    <?php if ($token): ?>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 24px;">
        
        <!-- محصولات -->
        <?php if ($has_woocommerce): ?>
        <div class="pilito-card" style="padding: 20px;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <span style="font-size: 24px;">🛍️</span>
                <h3 style="margin: 0; font-size: 15px; font-weight: 600; color: #1a1a1a;">محصولات</h3>
            </div>
            <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px;">
                <span style="font-size: 32px; font-weight: 700; color: #1a1a1a;"><?php echo $products_synced; ?></span>
                <span style="font-size: 14px; color: #999;">از <?php echo $products_count; ?></span>
            </div>
            <div style="font-size: 13px; color: #666;">همگام‌سازی شده</div>
        </div>
        <?php endif; ?>
        
        <!-- صفحات -->
        <div class="pilito-card" style="padding: 20px;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <span style="font-size: 24px;">📄</span>
                <h3 style="margin: 0; font-size: 15px; font-weight: 600; color: #1a1a1a;">صفحات</h3>
            </div>
            <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px;">
                <span style="font-size: 32px; font-weight: 700; color: #1a1a1a;"><?php echo $pages_synced; ?></span>
                <span style="font-size: 14px; color: #999;">از <?php echo $pages_count; ?></span>
            </div>
            <div style="font-size: 13px; color: #666;">همگام‌سازی شده</div>
        </div>
        
        <!-- نوشته‌ها -->
        <div class="pilito-card" style="padding: 20px;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <span style="font-size: 24px;">📝</span>
                <h3 style="margin: 0; font-size: 15px; font-weight: 600; color: #1a1a1a;">نوشته‌ها</h3>
            </div>
            <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px;">
                <span style="font-size: 32px; font-weight: 700; color: #1a1a1a;"><?php echo $posts_synced; ?></span>
                <span style="font-size: 14px; color: #999;">از <?php echo $posts_count; ?></span>
            </div>
            <div style="font-size: 13px; color: #666;">همگام‌سازی شده</div>
        </div>
        
    </div>
    <?php endif; ?>
    
    <!-- Settings Form -->
    <div class="pilito-card">
        <div class="pilito-card-header">
            <h2 class="pilito-card-title">⚙️ تنظیمات اتصال</h2>
            <p class="pilito-card-description">
                برای استفاده از قابلیت‌های پیلیتو، ابتدا Token API خود را وارد کنید.
            </p>
        </div>
        
        <form method="post" action="">
            <?php wp_nonce_field('pilito_ps_settings'); ?>
            
            <div class="pilito-form-group">
                <label for="pilito_ps_api_token" class="pilito-label">🔑 API Token</label>
                <input 
                    type="text" 
                    id="pilito_ps_api_token" 
                    name="pilito_ps_api_token" 
                    value="<?php echo esc_attr($token); ?>" 
                    class="pilito-input"
                    placeholder="توکن API خود را وارد کنید"
                >
                <span class="pilito-input-hint">
                    از داشبورد Django دریافت کنید. برای محصولات، صفحات و نوشته‌ها یکسان است.
                </span>
            </div>
            
            <div class="pilito-form-group">
                <label>
                    <input 
                        type="checkbox" 
                        name="pilito_ps_enable_logging" 
                        <?php checked($enable_logging); ?>
                    >
                    فعال‌سازی لاگ‌گذاری (برای عیب‌یابی)
                </label>
            </div>
            
            <div class="pilito-form-group">
                <label>
                    <input 
                        type="checkbox" 
                        name="pilito_ps_debug_mode" 
                        <?php checked(get_option('pilito_ps_debug_mode', false)); ?>
                    >
                    <strong>🐛 حالت دیباگ</strong> - نمایش جزئیات کامل خطاها
                </label>
                <span class="pilito-input-hint" style="color: #dc2626;">
                    ⚠️ فقط برای رفع مشکل استفاده کنید. پس از رفع مشکل، غیرفعال کنید.
                </span>
            </div>
            
            <div class="pilito-action-bar">
                <div class="pilito-action-left">
                    <?php if ($token): ?>
                    <span style="color: #16a34a; font-weight: 500;">● متصل</span>
                    <?php else: ?>
                    <span style="color: #dc2626; font-weight: 500;">● غیرمتصل</span>
                    <?php endif; ?>
                </div>
                <div class="pilito-action-right">
                    <button type="button" id="pilito-test-connection" class="pilito-btn pilito-btn-secondary">
                        <span>🔍</span> تست اتصال
                    </button>
                    <button type="submit" name="pilito_ps_save_settings" class="pilito-btn pilito-btn-primary">
                        <span>💾</span> ذخیره تنظیمات
                    </button>
                    <?php if ($token && $not_synced > 0): ?>
                    <button type="button" id="pilito-bulk-sync" class="pilito-btn pilito-btn-secondary">
                        <span>🔄</span> همگام‌سازی همه (<?php echo $not_synced; ?>)
                    </button>
                    <?php endif; ?>
                </div>
            </div>
        </form>
    </div>
    
    <!-- Test Result -->
    <div id="pilito-test-result" style="display:none;"></div>
    
    <!-- Bulk Sync Progress -->
    <div id="pilito-bulk-sync-progress" style="display:none;">
        <div class="pilito-card">
            <h3 style="margin-top: 0;">⏳ در حال همگام‌سازی...</h3>
            <div class="pilito-progress-container">
                <div id="pilito-progress-bar" class="pilito-progress-bar" style="width: 0%;"></div>
            </div>
            <div id="pilito-progress-text" class="pilito-progress-text">0% - 0 از 0 محصول</div>
            <div id="pilito-progress-details" style="margin-top: 15px; font-size: 13px; color: #666;"></div>
        </div>
    </div>
    
    <!-- System Info (همیشه باز برای دیباگ) -->
    <?php if ($token): ?>
    <div class="pilito-card">
        <h3 style="margin: 0 0 16px 0; font-size: 16px; font-weight: 600; color: #1a1a1a;">🔧 اطلاعات دیباگ - مهم!</h3>
        <div class="pilito-system-info">
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #e0e0e0;">
                    <td style="padding: 12px 8px; font-weight: 600; width: 250px;">URL API ذخیره شده:</td>
                    <td style="padding: 12px 8px;">
                        <code style="background: #f5f5f5; padding: 4px 8px; border-radius: 4px; display: block; word-break: break-all;">
                            <?php echo esc_html(get_option('pilito_ps_api_url', 'خالی است!')); ?>
                        </code>
                    </td>
                </tr>
                <tr style="border-bottom: 1px solid #e0e0e0;">
                    <td style="padding: 12px 8px; font-weight: 600;">Endpoint محصولات:</td>
                    <td style="padding: 12px 8px;">
                        <code style="background: #f5f5f5; padding: 4px 8px; border-radius: 4px; display: block; word-break: break-all; color: #16a34a;">
                            <?php 
                            $api_url = get_option('pilito_ps_api_url', '');
                            echo esc_html($api_url ? rtrim($api_url, '/') . '/webhook/' : 'تنظیم نشده');
                            ?>
                        </code>
                    </td>
                </tr>
                <tr style="border-bottom: 1px solid #e0e0e0;">
                    <td style="padding: 12px 8px; font-weight: 600;">Endpoint صفحات (محاسبه شده):</td>
                    <td style="padding: 12px 8px;">
                        <code style="background: #fff3cd; padding: 4px 8px; border-radius: 4px; display: block; word-break: break-all; color: #856404;">
                            <?php 
                            $base = get_option('pilito_ps_api_url', '');
                            if ($base) {
                                $base = rtrim($base, '/');
                                $base = str_replace('/webhook/', '', $base);
                                $base = str_replace('/webhook', '', $base);
                                if (strpos($base, 'woocommerce') !== false) {
                                    echo esc_html(str_replace('woocommerce', 'wordpress-content', $base) . '/webhook/');
                                } elseif (strpos($base, '/api/') !== false) {
                                    $parts = explode('/api/', $base);
                                    echo esc_html($parts[0] . '/api/v1/integrations/wordpress-content/webhook/');
                                } else {
                                    echo esc_html($base . '/api/v1/integrations/wordpress-content/webhook/');
                                }
                            } else {
                                echo 'تنظیم نشده';
                            }
                            ?>
                        </code>
                        <div style="margin-top: 8px; padding: 8px; background: #fef3c7; border-radius: 4px; font-size: 13px;">
                            ⚠️ <strong>این endpoint باید در سرور شما وجود داشته باشه!</strong><br>
                            اگه 404 می‌ده، یعنی backend شما این مسیر رو نداره.
                        </div>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 12px 8px; font-weight: 600;">Token:</td>
                    <td style="padding: 12px 8px;">
                        <code style="background: #f5f5f5; padding: 4px 8px; border-radius: 4px;">
                            <?php echo esc_html(substr($token, 0, 20) . '...'); ?>
                        </code>
                    </td>
                </tr>
            </table>
        </div>
        
        <div style="margin-top: 16px; padding: 16px; background: #fee2e2; border-radius: 8px; border-left: 4px solid #dc2626;">
            <div style="font-weight: 600; color: #991b1b; margin-bottom: 8px;">❌ اگه بازم 404 می‌ده:</div>
            <ol style="margin: 0; padding-right: 20px; color: #991b1b; font-size: 13px; line-height: 1.8;">
                <li>اسکرین‌شات این بخش رو بفرست</li>
                <li>از Django admin، مسیر دقیق endpoint رو بفرست</li>
                <li>یک صفحه تست ارسال کن و پیام کامل خطا رو بفرست</li>
            </ol>
        </div>
    </div>
    <?php endif; ?>
    
</div>

