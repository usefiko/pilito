<?php
/**
 * Pages & Posts Sync
 */
defined('ABSPATH') || exit;

$token = get_option('pilito_ps_api_token', '');
?>

<div class="wrap pilito-dashboard">
    
    <h1 class="pilito-page-title">
        <img src="<?php echo PILITO_PS_PLUGIN_URL . 'assets/logo.svg'; ?>" alt="پیلیتو" class="pilito-page-logo">
        برگه‌ها و نوشته‌ها
    </h1>
    <p class="pilito-page-description">محتوای سایت خود را با هوش مصنوعی پیلیتو همگام کنید</p>
    
    <?php if (!$token): ?>
    <div class="pilito-alert pilito-alert-warning">
        <strong>⚠️ توکن API تنظیم نشده است</strong><br>
        لطفاً ابتدا از بخش <a href="<?php echo admin_url('admin.php?page=pilito-settings'); ?>">تنظیمات</a> توکن خود را تنظیم کنید.
    </div>
    <?php else: ?>
    
    <div class="pilito-nav">
        <button class="pilito-nav-item active" data-tab="pages">
            برگه‌ها
            <span class="pilito-nav-badge" id="pages-count">...</span>
        </button>
        <button class="pilito-nav-item" data-tab="posts">
            نوشته‌ها
            <span class="pilito-nav-badge" id="posts-count">...</span>
        </button>
    </div>
    
    <div id="tab-pages" class="pilito-tab-content active">
        <div class="pilito-card">
            <div class="pilito-card-header">
                <h2 class="pilito-card-title">برگه‌های سایت</h2>
                <p class="pilito-card-description">
                    برگه‌هایی که می‌خواهید با پیلیتو همگام شوند را انتخاب کنید.
                </p>
            </div>
            
            <div class="pilito-filters">
                <button class="pilito-filter-btn active" data-filter="all" data-type="page">همه</button>
                <button class="pilito-filter-btn" data-filter="not_synced" data-type="page">ارسال نشده</button>
                <button class="pilito-filter-btn" data-filter="need_update" data-type="page">نیاز به آپدیت</button>
                <button class="pilito-filter-btn" data-filter="synced" data-type="page">همگام شده</button>
            </div>
            
            <div id="pages-list" class="pilito-content-list">
                <div style="padding: 40px; text-align: center; color: #999;">
                    <div class="pilito-spinner"></div>
                    <div style="margin-top: 12px;">در حال بارگذاری...</div>
                </div>
            </div>
            
            <div class="pilito-action-bar">
                <div class="pilito-action-left">
                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                        <input type="checkbox" id="select-all-pages">
                        <span style="font-size: 13px; color: #666;">انتخاب همه</span>
                    </label>
                    <span id="pages-selected-count" style="color: #999; font-size: 13px;">0 انتخاب شده</span>
                </div>
                <div class="pilito-action-right">
                    <button id="send-selected-pages" class="pilito-btn pilito-btn-primary" disabled>
                        ارسال انتخاب شده
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <div id="tab-posts" class="pilito-tab-content">
        <div class="pilito-card">
            <div class="pilito-card-header">
                <h2 class="pilito-card-title">نوشته‌های بلاگ</h2>
                <p class="pilito-card-description">نوشته‌هایی که می‌خواهید با پیلیتو همگام شوند را انتخاب کنید.</p>
            </div>
            
            <div class="pilito-filters">
                <button class="pilito-filter-btn active" data-filter="all" data-type="post">همه</button>
                <button class="pilito-filter-btn" data-filter="not_synced" data-type="post">ارسال نشده</button>
                <button class="pilito-filter-btn" data-filter="need_update" data-type="post">نیاز به آپدیت</button>
                <button class="pilito-filter-btn" data-filter="synced" data-type="post">همگام شده</button>
            </div>
            
            <div id="posts-list" class="pilito-content-list">
                <div style="padding: 40px; text-align: center; color: #999;">
                    <div class="pilito-spinner"></div>
                    <div style="margin-top: 12px;">در حال بارگذاری...</div>
                </div>
            </div>
            
            <div class="pilito-action-bar">
                <div class="pilito-action-left">
                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                        <input type="checkbox" id="select-all-posts">
                        <span style="font-size: 13px; color: #666;">انتخاب همه</span>
                    </label>
                    <span id="posts-selected-count" style="color: #999; font-size: 13px;">0 انتخاب شده</span>
                </div>
                <div class="pilito-action-right">
                    <button id="send-selected-posts" class="pilito-btn pilito-btn-primary" disabled>
                        ارسال انتخاب شده
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <div id="pilito-sync-progress" style="display:none;">
        <div class="pilito-card">
            <h3 style="margin-top: 0;">در حال ارسال...</h3>
            <div class="pilito-progress-container">
                <div id="pilito-pages-progress-bar" class="pilito-progress-bar"></div>
            </div>
            <div id="pilito-pages-progress-text" class="pilito-progress-text"></div>
        </div>
    </div>
    
    <?php endif; ?>
    
</div>

<script>
jQuery(document).ready(function($) {
    $('.pilito-nav-item').on('click', function() {
        if ($(this).hasClass('disabled')) return;
        
        const tab = $(this).data('tab');
        
        $('.pilito-nav-item').removeClass('active');
        $(this).addClass('active');
        
        $('.pilito-tab-content').removeClass('active');
        $('#tab-' + tab).addClass('active');
        
        if (tab === 'pages') {
            loadPages('all');
        } else if (tab === 'posts') {
            loadPosts('all');
        }
    });
    
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
            container.html('<div class="pilito-empty-state"><div class="pilito-empty-text">موردی یافت نشد</div></div>');
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
                'synced': 'همگام شده',
                'not_synced': 'ارسال نشده',
                'need_update': 'نیاز به آپدیت',
                'error': 'خطا'
            }[item.status] || 'نامشخص';
            
            html += `
                <div class="pilito-content-item">
                    <input type="checkbox" class="pilito-content-checkbox ${type}-checkbox" value="${item.id}">
                    <div class="pilito-content-title">${item.title}</div>
                    <span class="pilito-content-meta">${item.word_count} کلمه</span>
                    <span class="pilito-content-status ${statusClass}">${statusText}</span>
                </div>
            `;
        });
        
        container.html(html);
        updateSelectedCount(type);
    }
    
    $('#select-all-pages').on('change', function() {
        $('.pages-checkbox').prop('checked', $(this).prop('checked'));
        updateSelectedCount('pages');
    });
    
    $('#select-all-posts').on('change', function() {
        $('.posts-checkbox').prop('checked', $(this).prop('checked'));
        updateSelectedCount('posts');
    });
    
    $(document).on('change', '.pages-checkbox, .posts-checkbox', function() {
        const type = $(this).hasClass('pages-checkbox') ? 'pages' : 'posts';
        updateSelectedCount(type);
    });
    
    function updateSelectedCount(type) {
        const count = $(`.${type}-checkbox:checked`).length;
        $(`#${type}-selected-count`).text(`${count} انتخاب شده`);
        $(`#send-selected-${type}`).prop('disabled', count === 0);
    }
    
    $('#send-selected-pages, #send-selected-posts').on('click', function() {
        const isPages = $(this).attr('id') === 'send-selected-pages';
        const type = isPages ? 'pages' : 'posts';
        const selectedIds = $(`.${type}-checkbox:checked`).map(function() {
            return $(this).val();
        }).get();
        
        if (selectedIds.length === 0) return;
        
        if (!confirm(`${selectedIds.length} مورد ارسال خواهد شد. ادامه می‌دهید؟`)) {
            return;
        }
        
        $(this).prop('disabled', true).html('<span class="pilito-spinner"></span> در حال ارسال...');
        
        $.post(pilitoPS.ajax_url, {
            action: 'pilito_ps_sync_pages',
            nonce: pilitoPS.pages_nonce,
            post_ids: selectedIds
        }, function(response) {
            if (response.success) {
                const data = response.data;
                let msg = `✅ ${data.success} مورد با موفقیت ارسال شد`;
                
                if (data.failed > 0) {
                    msg += `\n⚠️ ${data.failed} مورد ناموفق`;
                    if (data.errors && data.errors.length > 0) {
                        msg += '\n\nخطاها:';
                        data.errors.slice(0, 3).forEach(err => {
                            msg += `\n- Post ${err.post_id}: ${err.message}`;
                        });
                    }
                }
                
                alert(msg);
                if (isPages) loadPages('all');
                else loadPosts('all');
            } else {
                alert('❌ خطا: ' + response.data.message);
            }
        }).always(function() {
            $(`#send-selected-${type}`).prop('disabled', false).html('ارسال انتخاب شده');
        });
    });
});
</script>
