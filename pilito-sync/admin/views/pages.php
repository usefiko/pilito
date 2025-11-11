<?php
/**
 * Pages & Posts Sync - Minimal & Professional
 */
defined('ABSPATH') || exit;

$token = get_option('pilito_ps_api_token', '');
?>

<div class="wrap pilito-dashboard">
    
    <h1 class="pilito-page-title">
        <img src="<?php echo PILITO_PS_PLUGIN_URL . 'assets/logo.svg'; ?>" alt="<?php esc_attr_e('پیلیتو', 'pilito-sync'); ?>" class="pilito-page-logo">
        <?php esc_html_e('همگام‌سازی صفحات و نوشته‌ها', 'pilito-sync'); ?>
    </h1>
    <p class="pilito-page-description"><?php esc_html_e('محتوای سایت خود را با هوش مصنوعی پیلیتو همگام کنید', 'pilito-sync'); ?></p>
    
    <?php if (!$token): ?>
    <!-- No Token Alert -->
    <div class="pilito-alert pilito-alert-warning">
        <strong><?php esc_html_e('⚠️ توکن API تنظیم نشده است', 'pilito-sync'); ?></strong><br>
        <?php esc_html_e('لطفاً ابتدا از بخش', 'pilito-sync'); ?> <a href="<?php echo admin_url('admin.php?page=pilito-settings'); ?>"><?php esc_html_e('تنظیمات', 'pilito-sync'); ?></a> <?php esc_html_e('توکن خود را تنظیم کنید.', 'pilito-sync'); ?>
    </div>
    <?php else: ?>
    
    <!-- Tabs: Pages / Posts -->
    <div class="pilito-nav">
        <button class="pilito-nav-item active" data-tab="pages">
            <?php esc_html_e('صفحات', 'pilito-sync'); ?>
            <span class="pilito-nav-badge" id="pages-count">...</span>
        </button>
        <button class="pilito-nav-item" data-tab="posts">
            <?php esc_html_e('نوشته‌ها', 'pilito-sync'); ?>
            <span class="pilito-nav-badge" id="posts-count">...</span>
        </button>
    </div>
    
    <!-- Tab Content: Pages -->
    <div id="tab-pages" class="pilito-tab-content active">
        <div class="pilito-card">
            <div class="pilito-card-header">
                <h2 class="pilito-card-title"><?php esc_html_e('صفحات سایت', 'pilito-sync'); ?></h2>
                <p class="pilito-card-description">
                    <?php esc_html_e('صفحاتی که می‌خواهید با پیلیتو همگام شوند را انتخاب کنید. هوش مصنوعی از محتوای این صفحات برای پاسخگویی به مشتریان استفاده خواهد کرد.', 'pilito-sync'); ?>
                </p>
            </div>
            
            <!-- Filters -->
            <div class="pilito-filters">
                <button class="pilito-filter-btn active" data-filter="all" data-type="page"><?php esc_html_e('همه', 'pilito-sync'); ?></button>
                <button class="pilito-filter-btn" data-filter="not_synced" data-type="page"><?php esc_html_e('ارسال نشده', 'pilito-sync'); ?></button>
                <button class="pilito-filter-btn" data-filter="need_update" data-type="page"><?php esc_html_e('نیاز به آپدیت', 'pilito-sync'); ?></button>
                <button class="pilito-filter-btn" data-filter="synced" data-type="page"><?php esc_html_e('همگام شده', 'pilito-sync'); ?></button>
            </div>
            
            <!-- List -->
            <div id="pages-list" class="pilito-content-list">
                <div style="padding: 40px; text-align: center; color: #999;">
                    <div class="pilito-spinner"></div>
                    <div style="margin-top: 12px;"><?php esc_html_e('در حال بارگذاری...', 'pilito-sync'); ?></div>
                </div>
            </div>
            
            <!-- Actions -->
            <div class="pilito-action-bar">
                <div class="pilito-action-left">
                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                        <input type="checkbox" id="select-all-pages">
                        <span style="font-size: 13px; color: #666;"><?php esc_html_e('انتخاب همه', 'pilito-sync'); ?></span>
                    </label>
                    <span id="pages-selected-count" style="color: #999; font-size: 13px;"><?php esc_html_e('0 انتخاب شده', 'pilito-sync'); ?></span>
                </div>
                <div class="pilito-action-right">
                    <button id="send-selected-pages" class="pilito-btn pilito-btn-primary" disabled>
                        <?php esc_html_e('ارسال انتخاب شده', 'pilito-sync'); ?>
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Tab Content: Posts -->
    <div id="tab-posts" class="pilito-tab-content">
        <div class="pilito-card">
            <div class="pilito-card-header">
                <h2 class="pilito-card-title"><?php esc_html_e('نوشته‌های بلاگ', 'pilito-sync'); ?></h2>
                <p class="pilito-card-description">
                    <?php esc_html_e('نوشته‌هایی که می‌خواهید با پیلیتو همگام شوند را انتخاب کنید.', 'pilito-sync'); ?>
                </p>
            </div>
            
            <!-- Filters -->
            <div class="pilito-filters">
                <button class="pilito-filter-btn active" data-filter="all" data-type="post"><?php esc_html_e('همه', 'pilito-sync'); ?></button>
                <button class="pilito-filter-btn" data-filter="not_synced" data-type="post"><?php esc_html_e('ارسال نشده', 'pilito-sync'); ?></button>
                <button class="pilito-filter-btn" data-filter="need_update" data-type="post"><?php esc_html_e('نیاز به آپدیت', 'pilito-sync'); ?></button>
                <button class="pilito-filter-btn" data-filter="synced" data-type="post"><?php esc_html_e('همگام شده', 'pilito-sync'); ?></button>
            </div>
            
            <!-- List -->
            <div id="posts-list" class="pilito-content-list">
                <div style="padding: 40px; text-align: center; color: #999;">
                    <div class="pilito-spinner"></div>
                    <div style="margin-top: 12px;"><?php esc_html_e('در حال بارگذاری...', 'pilito-sync'); ?></div>
                </div>
            </div>
            
            <!-- Actions -->
            <div class="pilito-action-bar">
                <div class="pilito-action-left">
                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                        <input type="checkbox" id="select-all-posts">
                        <span style="font-size: 13px; color: #666;"><?php esc_html_e('انتخاب همه', 'pilito-sync'); ?></span>
                    </label>
                    <span id="posts-selected-count" style="color: #999; font-size: 13px;"><?php esc_html_e('0 انتخاب شده', 'pilito-sync'); ?></span>
                </div>
                <div class="pilito-action-right">
                    <button id="send-selected-posts" class="pilito-btn pilito-btn-primary" disabled>
                        <?php esc_html_e('ارسال انتخاب شده', 'pilito-sync'); ?>
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Progress Modal -->
    <div id="pilito-sync-progress" style="display:none;">
        <div class="pilito-card">
            <h3 style="margin-top: 0;"><?php esc_html_e('در حال ارسال...', 'pilito-sync'); ?></h3>
            <div class="pilito-progress-container">
                <div id="pilito-pages-progress-bar" class="pilito-progress-bar"></div>
            </div>
            <div id="pilito-pages-progress-text" class="pilito-progress-text"></div>
        </div>
    </div>
    
    <?php endif; ?>
    
</div>

<script>
// این بخش هنوز کامل نشده - فقط برای نمایش اولیه
jQuery(document).ready(function($) {
    // Tab switching
    $('.pilito-nav-item').on('click', function() {
        if ($(this).hasClass('disabled')) return;
        
        const tab = $(this).data('tab');
        
        $('.pilito-nav-item').removeClass('active');
        $(this).addClass('active');
        
        $('.pilito-tab-content').removeClass('active');
        $('#tab-' + tab).addClass('active');
        
        // Load content if not loaded
        if (tab === 'pages') {
            loadPages('all');
        } else if (tab === 'posts') {
            loadPosts('all');
        }
    });
    
    // Filter buttons
    $('.pilito-filter-btn').on('click', function() {
        const type = $(this).data('type');
        const filter = $(this).data('filter');
        
        $(`.pilito-filter-btn[data-type="${type}"]`).removeClass('active');
        $(this).addClass('active');
        
        if (type === 'page') {
            loadPages(filter);
        } else {
            loadPosts(filter);
        }
    });
    
    // Load pages on init
    loadPages('all');
    
    function loadPages(filter) {
        $('#pages-list').html('<div style="padding: 40px; text-align: center;"><div class="pilito-spinner"></div></div>');
        
        $.post(pilitoPS.ajax_url, {
            action: 'pilito_ps_get_pages',
            nonce: pilitoPS.pages_nonce,
            post_type: 'page',
            filter: filter
        }, function(response) {
            if (response.success) {
                renderList(response.data.items, 'pages');
                $('#pages-count').text(response.data.total);
            }
        });
    }
    
    function loadPosts(filter) {
        $('#posts-list').html('<div style="padding: 40px; text-align: center;"><div class="pilito-spinner"></div></div>');
        
        $.post(pilitoPS.ajax_url, {
            action: 'pilito_ps_get_pages',
            nonce: pilitoPS.pages_nonce,
            post_type: 'post',
            filter: filter
        }, function(response) {
            if (response.success) {
                renderList(response.data.items, 'posts');
                $('#posts-count').text(response.data.total);
            }
        });
    }
    
    function renderList(items, type) {
        const container = $(`#${type}-list`);
        
        if (items.length === 0) {
            container.html(
                '<div class="pilito-empty-state">' +
                '<div class="pilito-empty-text"><?php echo esc_js(__('موردی یافت نشد', 'pilito-sync')); ?></div>' +
                '</div>'
            );
            return;
        }
        
        let html = '';
        items.forEach(item => {
            const statusClass = {
                'synced': 'pilito-status-synced',
                'not_synced': 'pilito-status-pending',
                'need_update': 'pilito-status-need-update',
                'error': 'pilito-status-error'
            }[item.status] || 'pilito-status-pending';
            
            const statusText = {
                'synced': '<?php echo esc_js(__('همگام شده', 'pilito-sync')); ?>',
                'not_synced': '<?php echo esc_js(__('ارسال نشده', 'pilito-sync')); ?>',
                'need_update': '<?php echo esc_js(__('نیاز به آپدیت', 'pilito-sync')); ?>',
                'error': '<?php echo esc_js(__('خطا', 'pilito-sync')); ?>'
            }[item.status] || '<?php echo esc_js(__('نامشخص', 'pilito-sync')); ?>';
            
            html += `
                <div class="pilito-content-item">
                    <input type="checkbox" class="pilito-content-checkbox ${type}-checkbox" value="${item.id}">
                    <div class="pilito-content-title">${item.title}</div>
                    <span class="pilito-content-meta">${item.word_count} <?php echo esc_js(__('کلمه', 'pilito-sync')); ?></span>
                    <span class="pilito-content-status ${statusClass}">${statusText}</span>
                </div>
            `;
        });
        
        container.html(html);
        updateSelectedCount(type);
    }
    
    // Select all
    $('#select-all-pages').on('change', function() {
        $('.pages-checkbox').prop('checked', $(this).prop('checked'));
        updateSelectedCount('pages');
    });
    
    $('#select-all-posts').on('change', function() {
        $('.posts-checkbox').prop('checked', $(this).prop('checked'));
        updateSelectedCount('posts');
    });
    
    // Update count
    $(document).on('change', '.pages-checkbox, .posts-checkbox', function() {
        const type = $(this).hasClass('pages-checkbox') ? 'pages' : 'posts';
        updateSelectedCount(type);
    });
    
    function updateSelectedCount(type) {
        const count = $(`.${type}-checkbox:checked`).length;
        $(`#${type}-selected-count`).text(`${count} انتخاب شده`);
        $(`#send-selected-${type}`).prop('disabled', count === 0);
    }
    
    // Send selected
    $('#send-selected-pages, #send-selected-posts').on('click', function() {
        const isPages = $(this).attr('id') === 'send-selected-pages';
        const type = isPages ? 'pages' : 'posts';
        const selectedIds = $(`.${type}-checkbox:checked`).map(function() {
            return $(this).val();
        }).get();
        
        if (selectedIds.length === 0) return;
        
        if (!confirm('<?php echo esc_js(sprintf(__('%d مورد ارسال خواهد شد. ادامه می‌دهید؟', 'pilito-sync'), 'PLACEHOLDER'))); ?>'.replace('PLACEHOLDER', selectedIds.length))) {
            return;
        }
        
        // Send
        $(this).prop('disabled', true).html('<span class="pilito-spinner"></span> <?php echo esc_js(__('در حال ارسال...', 'pilito-sync')); ?>');
        
        $.post(pilitoPS.ajax_url, {
            action: 'pilito_ps_sync_pages',
            nonce: pilitoPS.pages_nonce,
            post_ids: selectedIds
        }, function(response) {
            if (response.success) {
                const data = response.data;
                let msg = '<?php echo esc_js(sprintf(__('%d مورد با موفقیت ارسال شد', 'pilito-sync'), 'SUCCESS')); ?>'.replace('SUCCESS', data.success);
                
                if (data.failed > 0) {
                    msg += '\n' + '<?php echo esc_js(sprintf(__('%d مورد ناموفق', 'pilito-sync'), 'FAILED')); ?>'.replace('FAILED', data.failed);
                    if (data.errors && data.errors.length > 0) {
                        msg += '\n\n<?php echo esc_js(__('خطاها:', 'pilito-sync')); ?>';
                        data.errors.slice(0, 3).forEach(err => {
                            msg += `\n- Post ${err.post_id}: ${err.message}`;
                        });
                    }
                }
                
                alert(msg);
                // Reload list
                if (isPages) loadPages('all');
                else loadPosts('all');
            } else {
                let msg = '<?php echo esc_js(__('خطا:', 'pilito-sync')); ?> ' + response.data.message;
                alert(msg);
            }
        }).always(function() {
            $(`#send-selected-${type}`).prop('disabled', false).html('<?php echo esc_js(__('ارسال انتخاب شده', 'pilito-sync')); ?>');
        });
    });
});
</script>

</div>

