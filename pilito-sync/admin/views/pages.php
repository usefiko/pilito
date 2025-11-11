<?php
/**
 * Pages & Posts Sync - Modern & Minimal
 */
defined('ABSPATH') || exit;

$token = get_option('pilito_ps_api_token', '');

// Stats
global $wpdb;
$pages_count = wp_count_posts('page')->publish ?? 0;
$pages_synced = $wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = '_pilito_page_sync_status' AND meta_value = 'success' AND post_id IN (SELECT ID FROM {$wpdb->posts} WHERE post_type = 'page' AND post_status = 'publish')");

$posts_count = wp_count_posts('post')->publish ?? 0;
$posts_synced = $wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = '_pilito_page_sync_status' AND meta_value = 'success' AND post_id IN (SELECT ID FROM {$wpdb->posts} WHERE post_type = 'post' AND post_status = 'publish')");

$has_woocommerce = class_exists('WooCommerce');
$products_count = 0;
$products_synced = 0;
if ($has_woocommerce) {
    $stats = pilito_ps_get_sync_stats();
    $total_products = wp_count_posts('product');
    $products_count = $total_products->publish ?? 0;
    $products_synced = $stats['success'] ?? 0;
}

$current_tab = isset($_GET['tab']) ? sanitize_text_field(wp_unslash($_GET['tab'])) : 'pages';
$current_filter = isset($_GET['filter']) ? sanitize_text_field(wp_unslash($_GET['filter'])) : 'all';
?>

<div class="wrap pilito-dashboard">
    
    <h1 class="pilito-page-title">
        <img src="<?php echo esc_url(PILITO_PS_PLUGIN_URL . 'assets/logo.svg'); ?>" alt="پیلیتو" class="pilito-page-logo">
        برگه‌ها و نوشته‌ها
    </h1>
    <p class="pilito-page-description">محتوای سایت خود را با هوش مصنوعی پیلیتو همگام کنید</p>
    
    <?php 
    // Show messages
    if (isset($_GET['pilito_message'])) {
        $message = sanitize_text_field(wp_unslash($_GET['pilito_message']));
        $success = isset($_GET['success']) ? absint($_GET['success']) : 0;
        $failed = isset($_GET['failed']) ? absint($_GET['failed']) : 0;
        
        if ($message === 'success') {
            /* translators: %d: number of successfully synced items */
            echo '<div class="notice notice-success is-dismissible"><p>' . esc_html(sprintf(__('%d مورد با موفقیت ارسال شد.', 'pilito-sync'), $success)) . '</p></div>';
        } elseif ($message === 'partial') {
            /* translators: 1: number of successful items, 2: number of failed items */
            echo '<div class="notice notice-warning is-dismissible"><p>' . esc_html(sprintf(__('%1$d مورد موفق، %2$d مورد ناموفق', 'pilito-sync'), $success, $failed)) . '</p></div>';
        } elseif ($message === 'no_selection') {
            echo '<div class="notice notice-error is-dismissible"><p>' . esc_html__('هیچ موردی انتخاب نشده است.', 'pilito-sync') . '</p></div>';
        }
    }
    
    if (!$token): ?>
    <div class="pilito-alert pilito-alert-warning">
        <strong>توکن API تنظیم نشده است</strong><br>
        لطفاً ابتدا از بخش <a href="<?php echo admin_url('admin.php?page=pilito-settings'); ?>">تنظیمات</a> توکن خود را تنظیم کنید.
    </div>
    <?php else: ?>
    
    <!-- Stats -->
    <div class="pilito-stats-grid">
        <?php if ($has_woocommerce): ?>
        <div class="pilito-stat-box">
            <div class="stat-label">محصولات</div>
            <div class="stat-value"><?php echo esc_html(number_format_i18n($products_synced)); ?> <span class="stat-total">/ <?php echo esc_html(number_format_i18n($products_count)); ?></span></div>
        </div>
        <?php endif; ?>
        <div class="pilito-stat-box">
            <div class="stat-label">برگه‌ها</div>
            <div class="stat-value"><?php echo esc_html(number_format_i18n($pages_synced)); ?> <span class="stat-total">/ <?php echo esc_html(number_format_i18n($pages_count)); ?></span></div>
        </div>
        <div class="pilito-stat-box">
            <div class="stat-label">نوشته‌ها</div>
            <div class="stat-value"><?php echo esc_html(number_format_i18n($posts_synced)); ?> <span class="stat-total">/ <?php echo esc_html(number_format_i18n($posts_count)); ?></span></div>
        </div>
    </div>
    
    <!-- Tabs -->
    <div class="pilito-nav">
        <a href="<?php echo esc_url(admin_url('admin.php?page=pilito-pages&tab=pages')); ?>" class="pilito-nav-item <?php echo esc_attr($current_tab === 'pages' ? 'active' : ''); ?>">
            برگه‌ها
            <span class="pilito-nav-badge"><?php echo esc_html($pages_count); ?></span>
        </a>
        <a href="<?php echo esc_url(admin_url('admin.php?page=pilito-pages&tab=posts')); ?>" class="pilito-nav-item <?php echo esc_attr($current_tab === 'posts' ? 'active' : ''); ?>">
            نوشته‌ها
            <span class="pilito-nav-badge"><?php echo esc_html($posts_count); ?></span>
        </a>
    </div>
    
    <!-- Content -->
    <div class="pilito-card">
        <div class="pilito-card-header">
            <h2 class="pilito-card-title"><?php echo $current_tab === 'pages' ? 'برگه‌های سایت' : 'نوشته‌های بلاگ'; ?></h2>
            <p class="pilito-card-description">
                <?php echo $current_tab === 'pages' ? 'برگه‌هایی که می‌خواهید با پیلیتو همگام شوند را انتخاب کنید.' : 'نوشته‌هایی که می‌خواهید با پیلیتو همگام شوند را انتخاب کنید.'; ?>
            </p>
        </div>
        
        <div class="pilito-filters">
            <a href="<?php echo esc_url(admin_url('admin.php?page=pilito-pages&tab=' . $current_tab . '&filter=all')); ?>" class="pilito-filter-btn <?php echo esc_attr($current_filter === 'all' ? 'active' : ''); ?>">همه</a>
            <a href="<?php echo esc_url(admin_url('admin.php?page=pilito-pages&tab=' . $current_tab . '&filter=not_synced')); ?>" class="pilito-filter-btn <?php echo esc_attr($current_filter === 'not_synced' ? 'active' : ''); ?>">ارسال نشده</a>
            <a href="<?php echo esc_url(admin_url('admin.php?page=pilito-pages&tab=' . $current_tab . '&filter=need_update')); ?>" class="pilito-filter-btn <?php echo esc_attr($current_filter === 'need_update' ? 'active' : ''); ?>">نیاز به آپدیت</a>
            <a href="<?php echo esc_url(admin_url('admin.php?page=pilito-pages&tab=' . $current_tab . '&filter=synced')); ?>" class="pilito-filter-btn <?php echo esc_attr($current_filter === 'synced' ? 'active' : ''); ?>">همگام شده</a>
        </div>
        
        <div id="pilito-content-list" class="pilito-content-list">
            <div class="pilito-loading">
                <div class="pilito-spinner"></div>
                <div>در حال بارگذاری...</div>
            </div>
        </div>
        
            <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>" id="pilito-sync-form" style="display:none;">
            <?php wp_nonce_field('pilito_sync_pages', 'pilito_sync_nonce'); ?>
            <input type="hidden" name="action" value="pilito_sync_selected_pages">
            <input type="hidden" name="post_type" id="sync-post-type" value="">
            <input type="hidden" name="post_ids[]" id="sync-post-ids" value="">
            
            <div class="pilito-action-bar">
                <div class="pilito-action-left">
                    <label class="pilito-checkbox-label">
                        <input type="checkbox" id="select-all-items">
                        <span>انتخاب همه</span>
                    </label>
                    <span id="selected-count" class="pilito-selected-count">0 انتخاب شده</span>
                </div>
                <div class="pilito-action-right">
                    <button type="submit" class="pilito-btn pilito-btn-primary" id="send-selected-btn" disabled>
                        ارسال انتخاب شده
                    </button>
                </div>
            </div>
        </form>
    </div>
    
    <?php endif; ?>
    
</div>

<script>
jQuery(document).ready(function($) {
    const currentTab = '<?php echo esc_js($current_tab); ?>';
    const currentFilter = '<?php echo esc_js($current_filter); ?>';
    
    // Load content via AJAX
    function loadContent() {
        const postType = currentTab === 'posts' ? 'post' : 'page';
        
        $.ajax({
            url: pilitoPS.ajax_url,
            type: 'POST',
            data: {
                action: 'pilito_ps_get_pages',
                nonce: pilitoPS.pages_nonce,
                post_type: postType,
                filter: currentFilter
            },
            success: function(response) {
                if (response.success && response.data) {
                    renderList(response.data.items);
                    $('#sync-post-type').val(postType);
                    $('#pilito-sync-form').show();
                } else {
                    $('#pilito-content-list').html('<div class="pilito-empty-state"><div class="pilito-empty-text">خطا در بارگذاری</div></div>');
                }
            },
            error: function() {
                $('#pilito-content-list').html('<div class="pilito-empty-state"><div class="pilito-empty-text">خطا در برقراری ارتباط</div></div>');
            }
        });
    }
    
    function renderList(items) {
        const container = $('#pilito-content-list');
        
        if (!items || items.length === 0) {
            container.html('<div class="pilito-empty-state"><div class="pilito-empty-text">موردی یافت نشد</div></div>');
            $('#pilito-sync-form').hide();
            return;
        }
        
        let html = '';
        items.forEach(item => {
            const statusClass = {
                'synced': 'status-synced',
                'not_synced': 'status-pending',
                'need_update': 'status-update',
                'error': 'status-error'
            }[item.status] || 'status-pending';
            
            const statusText = {
                'synced': 'همگام شده',
                'not_synced': 'ارسال نشده',
                'need_update': 'نیاز به آپدیت',
                'error': 'خطا'
            }[item.status] || 'نامشخص';
            
            html += `
                <div class="pilito-content-item">
                    <input type="checkbox" name="post_ids[]" value="${item.id}" class="pilito-content-checkbox" id="item-${item.id}">
                    <label for="item-${item.id}" class="pilito-item-label">
                        <div class="pilito-content-title">${item.title}</div>
                        <div class="pilito-content-meta">
                            <span class="pilito-word-count">${item.word_count} کلمه</span>
                            <span class="pilito-content-status ${statusClass}">${statusText}</span>
                        </div>
                    </label>
                </div>
            `;
        });
        
        container.html(html);
        updateSelectedCount();
    }
    
    // Select all
    $(document).on('change', '#select-all-items', function() {
        $('.pilito-content-checkbox').prop('checked', $(this).prop('checked'));
        updateSelectedCount();
    });
    
    // Update count
    $(document).on('change', '.pilito-content-checkbox', function() {
        updateSelectedCount();
    });
    
    function updateSelectedCount() {
        const count = $('.pilito-content-checkbox:checked').length;
        $('#selected-count').text(count + ' انتخاب شده');
        $('#send-selected-btn').prop('disabled', count === 0);
        
        // Update hidden field
        const selectedIds = $('.pilito-content-checkbox:checked').map(function() {
            return $(this).val();
        }).get();
        $('#sync-post-ids').val(selectedIds.join(','));
    }
    
    // Form submit
    $('#pilito-sync-form').on('submit', function(e) {
        const count = $('.pilito-content-checkbox:checked').length;
        if (count === 0) {
            e.preventDefault();
            return false;
        }
        
        if (!confirm(count + ' مورد ارسال خواهد شد. ادامه می‌دهید؟')) {
            e.preventDefault();
            return false;
        }
        
        $('#send-selected-btn').prop('disabled', true).html('<span class="pilito-spinner"></span> در حال ارسال...');
    });
    
    // Load on page load
    loadContent();
});
</script>
