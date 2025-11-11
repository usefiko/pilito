/**
 * Pilito Product Sync - Admin JavaScript
 * Minimal & Professional
 */

(function($) {
    'use strict';
    
    $(document).ready(function() {
        
        /**
         * Test Connection
         */
        $('#pilito-test-connection').on('click', function() {
            const button = $(this);
            const token = $('#pilito_ps_api_token').val();
            const resultDiv = $('#pilito-test-result');
            
            if (!token) {
                showAlert('لطفاً ابتدا API Token را وارد کنید', 'error');
                return;
            }
            
            button.prop('disabled', true).html('<span class="pilito-spinner"></span> در حال تست...');
            resultDiv.hide();
            
            $.ajax({
                url: pilitoPS.ajax_url,
                method: 'POST',
                data: {
                    action: 'pilito_ps_test_connection',
                    nonce: pilitoPS.nonce,
                    token: token
                },
                success: function(response) {
                    if (response.success) {
                        showAlert(
                            `✅ ${response.data.message}<br>` +
                            `کاربر: ${response.data.data.user.email}`,
                            'success'
                        );
                    } else {
                        showAlert(`❌ ${response.data.message}`, 'error');
                    }
                },
                error: function() {
                    showAlert('❌ خطا در برقراری ارتباط', 'error');
                },
                complete: function() {
                    button.prop('disabled', false).html('<span>🔍</span> تست اتصال');
                }
            });
        });
        
        /**
         * Bulk Sync Products
         */
        let bulkSyncInProgress = false;
        let totalErrors = [];
        
        $('#pilito-bulk-sync').on('click', function(e) {
            e.preventDefault();
            
            if (bulkSyncInProgress) {
                showAlert('همگام‌سازی در حال انجام است. لطفاً صبر کنید...', 'warning');
                return;
            }
            
            if (!confirm('همگام‌سازی همه محصولات شروع می‌شود.\n\nآیا ادامه می‌دهید؟')) {
                return;
            }
            
            bulkSyncInProgress = true;
            totalErrors = [];
            
            $('#pilito-bulk-sync-progress').fadeIn();
            $('#pilito-test-result').hide();
            $(this).prop('disabled', true).html('<span class="pilito-spinner"></span> در حال پردازش...');
            
            syncBatch(0);
        });
        
        function syncBatch(offset) {
            $.ajax({
                url: pilitoPS.ajax_url,
                method: 'POST',
                data: {
                    action: 'pilito_ps_bulk_sync',
                    nonce: pilitoPS.bulk_nonce,
                    offset: offset
                },
                success: function(response) {
                    if (response.success) {
                        const data = response.data;
                        
                        $('#pilito-progress-bar').css('width', data.progress_percent + '%');
                        $('#pilito-progress-text').html(
                            `${data.progress_percent}% - ${data.processed} از ${data.total} محصول`
                        );
                        
                        let details = `✅ موفق: ${data.success}`;
                        if (data.failed > 0) {
                            details += ` | ❌ خطا: ${data.failed}`;
                            totalErrors = totalErrors.concat(data.errors);
                        }
                        $('#pilito-progress-details').html(details);
                        
                        if (data.has_more) {
                            setTimeout(() => syncBatch(data.next_offset), 1000);
                        } else {
                            bulkSyncCompleted(data);
                        }
                    } else {
                        bulkSyncFailed(response.data.message);
                    }
                },
                error: function() {
                    bulkSyncFailed('خطا در برقراری ارتباط');
                }
            });
        }
        
        function bulkSyncCompleted(data) {
            bulkSyncInProgress = false;
            $('#pilito-bulk-sync').prop('disabled', false).html('<span>🔄</span> همگام‌سازی همه');
            
            let message = `<strong>✅ همگام‌سازی کامل شد!</strong><br>` +
                `کل: ${data.total} | موفق: ${data.success} | خطا: ${totalErrors.length}`;
            
            if (totalErrors.length > 0) {
                message += '<br><br><strong>محصولات با خطا:</strong><ul style="margin: 8px 0; padding-right: 20px;">';
                totalErrors.slice(0, 5).forEach(err => {
                    message += `<li>${err.title} - ${err.error}</li>`;
                });
                if (totalErrors.length > 5) {
                    message += `<li>... و ${totalErrors.length - 5} مورد دیگر</li>`;
                }
                message += '</ul>';
            }
            
            showAlert(message, 'success');
            $('#pilito-progress-text').html('✅ تمام شد!');
            
            setTimeout(() => location.reload(), 2000);
        }
        
        function bulkSyncFailed(errorMessage) {
            bulkSyncInProgress = false;
            $('#pilito-bulk-sync').prop('disabled', false).html('<span>🔄</span> همگام‌سازی همه');
            showAlert(`❌ خطا: ${errorMessage}`, 'error');
            $('#pilito-bulk-sync-progress').fadeOut();
        }
        
        /**
         * Helper: Show Alert
         */
        function showAlert(message, type = 'info') {
            const alertClass = `pilito-alert pilito-alert-${type}`;
            const html = `<div class="${alertClass}">${message}</div>`;
            
            $('#pilito-test-result').html(html).fadeIn();
            
            setTimeout(() => {
                $('#pilito-test-result').fadeOut();
            }, 5000);
        }
        
    });
    
})(jQuery);

/**
 * Quick sync from list (global function for inline onclick)
 */
function pilitoQuickSyncFromList(postId, nonce) {
    var confirmed = confirm('آیا می‌خواهید این مورد را به پیلیتو ارسال کنید؟');
    if (!confirmed) return false;
    
    jQuery.post(ajaxurl, {
        action: 'pilito_ps_quick_sync',
        nonce: nonce,
        post_id: postId
    }, function(response) {
        if (response.success) {
            alert('✅ با موفقیت ارسال شد');
            location.reload();
        } else {
            alert('❌ خطا: ' + response.data.message);
        }
    });
    
    return false;
}
