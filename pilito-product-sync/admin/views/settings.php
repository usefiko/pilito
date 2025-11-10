<?php
/**
 * Admin Settings Template
 */
defined('ABSPATH') || exit;

$token = get_option('pilito_ps_api_token', '');
$enable_logging = get_option('pilito_ps_enable_logging', false);

if (isset($_POST['pilito_ps_save_settings']) && check_admin_referer('pilito_ps_settings')) {
    update_option('pilito_ps_api_token', sanitize_text_field($_POST['pilito_ps_api_token']));
    update_option('pilito_ps_enable_logging', isset($_POST['pilito_ps_enable_logging']));
    echo '<div class="notice notice-success is-dismissible"><p>تنظیمات ذخیره شد.</p></div>';
    $token = get_option('pilito_ps_api_token');
}

$stats = pilito_ps_get_sync_stats();
?>

<div class="wrap pilito-ps-settings">
    <h1>🔄 پیلیتو - سینک محصولات</h1>
    
    <div class="pilito-ps-card">
        <h2>📌 راهنمای نصب</h2>
        <ol>
            <li>به داشبورد پیلیتو بروید: <a href="https://app.pilito.com" target="_blank">app.pilito.com</a></li>
            <li>به بخش <strong>تنظیمات > ادغام‌ها > محصولات</strong> بروید</li>
            <li>روی دکمه <strong>"ایجاد Token"</strong> کلیک کنید</li>
            <li>Token را کپی کرده و در کادر زیر paste کنید</li>
            <li>روی دکمه <strong>"تست اتصال"</strong> کلیک کنید</li>
            <li>در صورت موفقیت، <strong>"ذخیره"</strong> را بزنید</li>
        </ol>
    </div>
    
    <form method="post" action="" class="pilito-ps-form">
        <?php wp_nonce_field('pilito_ps_settings'); ?>
        
        <table class="form-table">
            <tr>
                <th scope="row">
                    <label for="pilito_ps_api_token">🔑 API Token</label>
                </th>
                <td>
                    <input 
                        type="text" 
                        id="pilito_ps_api_token" 
                        name="pilito_ps_api_token" 
                        value="<?php echo esc_attr($token); ?>" 
                        class="regular-text"
                        placeholder="wc_sk_live_..."
                    >
                    <p class="description">
                        Token را از داشبورد پیلیتو دریافت کنید
                    </p>
                </td>
            </tr>
            
            <tr>
                <th scope="row">⚙️ تنظیمات</th>
                <td>
                    <label>
                        <input 
                            type="checkbox" 
                            name="pilito_ps_enable_logging" 
                            <?php checked($enable_logging); ?>
                        >
                        فعال‌سازی لاگ‌ها (برای debugging)
                    </label>
                </td>
            </tr>
        </table>
        
        <p class="submit">
            <button type="button" id="pilito-test-connection" class="button">
                🔍 تست اتصال
            </button>
            <button type="submit" name="pilito_ps_save_settings" class="button button-primary">
                💾 ذخیره تنظیمات
            </button>
        </p>
    </form>
    
    <div id="pilito-test-result" style="display:none; margin-top: 20px;"></div>
    
    <?php if ($token): ?>
    <div class="pilito-ps-card" style="margin-top: 30px;">
        <h2>✅ وضعیت سینک</h2>
        <p>پلاگین فعال است و تغییرات محصولات به‌صورت خودکار به پیلیتو ارسال می‌شود.</p>
        
        <h3>رویدادهای سینک شده:</h3>
        <ul>
            <li>✅ ایجاد محصول جدید</li>
            <li>✅ ویرایش محصول</li>
            <li>✅ حذف محصول</li>
        </ul>
        
        <?php if ($stats['total'] > 0): ?>
        <h3>📊 آمار:</h3>
        <ul>
            <li>کل محصولات سینک شده: <strong><?php echo $stats['total']; ?></strong></li>
            <li style="color: green;">موفق: <strong><?php echo $stats['success']; ?></strong></li>
            <?php if ($stats['error'] > 0): ?>
            <li style="color: red;">خطا: <strong><?php echo $stats['error']; ?></strong></li>
            <?php endif; ?>
        </ul>
        <?php endif; ?>
    </div>
    <?php endif; ?>
    
    <div class="pilito-ps-card" style="margin-top: 30px; background: #f0f6fc; border-left: 4px solid #0078d4;">
        <h3>💡 نکات مهم:</h3>
        <ul>
            <li>پلاگین به‌صورت خودکار محصولات را سینک می‌کند (بدون نیاز به تنظیم اضافه)</li>
            <li>تنها محصولات منتشر شده (Published) سینک می‌شوند</li>
            <li>برای جلوگیری از فشار به سرور، سینک با تاخیر 30 ثانیه انجام می‌شود</li>
            <li>در لیست محصولات، ستون "🔄 Pilito" وضعیت سینک هر محصول را نمایش می‌دهد</li>
        </ul>
    </div>
</div>
