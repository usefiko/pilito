/**
 * Pilito Product Sync - Admin JavaScript
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
                alert('لطفاً ابتدا API Token را وارد کنید');
                return;
            }
            
            // Disable button and show loading
            button.prop('disabled', true);
            button.html('<span class="pilito-loading"></span> در حال تست...');
            resultDiv.hide();
            
            // Send AJAX request
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
                        // Success
                        resultDiv.html(
                            '<div class="notice notice-success">' +
                            '<p><strong>✅ ' + response.data.message + '</strong></p>' +
                            '<p>کاربر: ' + response.data.data.user.email + '</p>' +
                            '<p>نام توکن: ' + response.data.data.token.name + '</p>' +
                            '</div>'
                        ).fadeIn();
                    } else {
                        // Error
                        resultDiv.html(
                            '<div class="notice notice-error">' +
                            '<p><strong>❌ خطا:</strong> ' + response.data.message + '</p>' +
                            '</div>'
                        ).fadeIn();
                    }
                },
                error: function(xhr, status, error) {
                    resultDiv.html(
                        '<div class="notice notice-error">' +
                        '<p><strong>❌ خطا در برقراری ارتباط</strong></p>' +
                        '<p>' + error + '</p>' +
                        '</div>'
                    ).fadeIn();
                },
                complete: function() {
                    // Re-enable button
                    button.prop('disabled', false);
                    button.html('🔍 تست اتصال');
                }
            });
        });
        
        /**
         * Auto-hide success messages
         */
        setTimeout(function() {
            $('.notice.is-dismissible').fadeOut();
        }, 5000);
        
    });
    
})(jQuery);
