<?php
/**
 * Content Sync with Backend
 */

defined('ABSPATH') || exit;

class Pilito_PS_Content {
    
    /**
     * Initialize
     */
    public static function init() {
        // Meta boxes
        add_action('add_meta_boxes', [__CLASS__, 'add_meta_box']);
        add_action('save_post', [__CLASS__, 'save_meta_box'], 10, 2);
        
        // Quick edit link
        add_filter('page_row_actions', [__CLASS__, 'add_quick_sync_link'], 10, 2);
        add_filter('post_row_actions', [__CLASS__, 'add_quick_sync_link'], 10, 2);
        
        // AJAX for quick sync
        add_action('wp_ajax_pilito_ps_quick_sync', [__CLASS__, 'ajax_quick_sync']);
    }
    
    /**
     * Add meta box to pages & posts
     */
    public static function add_meta_box() {
        $post_types = ['page', 'post'];
        
        foreach ($post_types as $post_type) {
            add_meta_box(
                'pilito_sync_meta',
                'پیلیتو - همگام‌سازی',
                [__CLASS__, 'render_meta_box'],
                $post_type,
                'side',
                'high'
            );
        }
    }
    
    /**
     * Render meta box
     */
    public static function render_meta_box($post) {
        $sync_status = get_post_meta($post->ID, '_pilito_page_sync_status', true);
        $last_sync = get_post_meta($post->ID, '_pilito_page_last_sync', true);
        $content_hash = md5($post->post_content);
        $old_hash = get_post_meta($post->ID, '_pilito_page_content_hash', true);
        
        $needs_update = !empty($old_hash) && $content_hash !== $old_hash;
        
        wp_nonce_field('pilito_sync_meta_save', 'pilito_sync_meta_nonce');
        ?>
        
        <div class="pilito-meta-box" style="text-align: center;">
            
            <?php if ($sync_status === 'success'): ?>
                <?php if ($needs_update): ?>
                    <div style="padding: 12px; background: #fff3cd; border-radius: 4px; margin-bottom: 12px;">
                        <strong style="color: #856404;">⚠️ نیاز به بروزرسانی</strong><br>
                        <small style="color: #856404;">محتوا تغییر کرده است</small>
                    </div>
                <?php else: ?>
                    <div style="padding: 12px; background: #d4edda; border-radius: 4px; margin-bottom: 12px;">
                        <strong style="color: #155724;">✅ همگام شده</strong><br>
                        <small style="color: #155724;">آخرین همگام‌سازی: <?php echo esc_html(date_i18n('Y/m/d H:i', strtotime($last_sync))); ?></small>
                    </div>
                <?php endif; ?>
            <?php elseif ($sync_status === 'error'): ?>
                <div style="padding: 12px; background: #f8d7da; border-radius: 4px; margin-bottom: 12px;">
                    <strong style="color: #721c24;">❌ خطا در همگام‌سازی</strong>
                </div>
            <?php else: ?>
                <div style="padding: 12px; background: #e2e3e5; border-radius: 4px; margin-bottom: 12px;">
                    <strong style="color: #383d41;">📭 ارسال نشده</strong>
                </div>
            <?php endif; ?>
            
            <label style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 12px;">
                <input type="checkbox" name="pilito_sync_on_publish" value="1" <?php checked(get_post_meta($post->ID, '_pilito_sync_on_publish', true), '1'); ?>>
                <span style="font-size: 13px;">همگام‌سازی خودکار</span>
            </label>
            
            <button type="button" class="button button-primary button-large" onclick="pilitoQuickSync(<?php echo esc_js($post->ID); ?>)" style="width: 100%;">
                📤 ارسال به پیلیتو
            </button>
            
            <p style="margin-top: 12px; font-size: 11px; color: #666;">
                محتوای این <?php echo $post->post_type === 'page' ? 'صفحه' : 'نوشته'; ?> به هوش مصنوعی پیلیتو ارسال می‌شود
            </p>
        </div>
        
        <script>
        function pilitoQuickSync(postId) {
            var btn = event.target;
            btn.disabled = true;
            btn.innerHTML = '⏳ در حال ارسال...';
            
            jQuery.post(ajaxurl, {
                action: 'pilito_ps_quick_sync',
                nonce: '<?php echo wp_create_nonce('pilito_ps_quick_sync'); ?>',
                post_id: postId
            }, function(response) {
                if (response.success) {
                    btn.innerHTML = '✅ ارسال شد';
                    btn.style.background = '#46b450';
                    setTimeout(function() {
                        location.reload();
                    }, 1000);
                } else {
                    btn.innerHTML = '❌ خطا';
                    btn.style.background = '#dc3232';
                    alert('خطا: ' + response.data.message);
                    btn.disabled = false;
                }
            });
        }
        </script>
        
        <?php
    }
    
    /**
     * Save meta box
     */
    public static function save_meta_box($post_id, $post) {
        // Checks
        if (!isset($_POST['pilito_sync_meta_nonce']) || !wp_verify_nonce($_POST['pilito_sync_meta_nonce'], 'pilito_sync_meta_save')) {
            return;
        }
        
        if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
            return;
        }
        
        if (!current_user_can('edit_post', $post_id)) {
            return;
        }
        
        // Save auto-sync preference
        $auto_sync = isset($_POST['pilito_sync_on_publish']) ? '1' : '0';
        update_post_meta($post_id, '_pilito_sync_on_publish', $auto_sync);
        
        // Auto sync on publish
        if ($post->post_status === 'publish' && $auto_sync === '1') {
            self::sync_page($post_id);
        }
    }
    
    /**
     * Add quick sync link in list
     */
    public static function add_quick_sync_link($actions, $post) {
        if (in_array($post->post_type, ['page', 'post'])) {
            $nonce = wp_create_nonce('pilito_ps_quick_sync');
            $actions['pilito_sync'] = sprintf(
                '<a href="#" onclick="pilitoQuickSyncFromList(%d, \'%s\'); return false;">📤 ارسال به پیلیتو</a>',
                $post->ID,
                $nonce
            );
        }
        return $actions;
    }
    
    /**
     * AJAX: Quick sync single page/post
     */
    public static function ajax_quick_sync() {
        check_ajax_referer('pilito_ps_quick_sync', 'nonce');
        
        if (!current_user_can('edit_posts')) {
            wp_send_json_error(['message' => 'عدم دسترسی']);
        }
        
        $post_id = intval($_POST['post_id'] ?? 0);
        
        if (!$post_id) {
            wp_send_json_error(['message' => 'شناسه نامعتبر']);
        }
        
        $result = self::sync_page($post_id);
        
        if ($result['success']) {
            wp_send_json_success($result);
        } else {
            wp_send_json_error($result);
        }
    }
    
    /**
     * Get full content for display (public method)
     */
    public static function get_full_content_for_display($post) {
        // اگر ID ارسال شده، post object بگیر
        if (is_numeric($post)) {
            $post = get_post($post);
        }
        
        // اگر post object نبود، string خالی برگردون
        if (!$post || !is_object($post)) {
            return '';
        }
        
        return self::extract_full_content($post);
    }
    
    /**
     * Extract full content from page builders (Elementor, Visual Composer, Divi, etc.)
     * بهینه شده برای سرعت و جلوگیری از هنگ
     */
    private static function extract_full_content($post) {
        if (!$post || !is_object($post)) {
            return '';
        }
        
        $content = '';
        
        // 1. اول Elementor رو چک کن (سریع‌ترین روش)
        if (class_exists('\Elementor\Plugin')) {
            $elementor_data = get_post_meta($post->ID, '_elementor_data', true);
            if (!empty($elementor_data)) {
                $content = self::extract_elementor_content_fast($elementor_data);
                if (strlen($content) > 50) { // اگه محتوای معقول پیدا کرد
                    return self::clean_text($content);
                }
            }
        }
        
        // 2. Divi
        $divi_active = get_post_meta($post->ID, '_et_pb_use_builder', true);
        if ($divi_active === 'on') {
            $content = self::extract_divi_content_fast($post->post_content);
            if (strlen($content) > 50) {
                return self::clean_text($content);
            }
        }
        
        // 3. محتوای معمولی + Shortcodeها (سریع)
        if (!empty($post->post_content)) {
            // فقط shortcodeهای ساده رو process کن
            $content = wp_strip_all_tags($post->post_content);
            return self::clean_text($content);
        }
        
        return '';
    }
    
    /**
     * پاکسازی متن (سریع)
     */
    private static function clean_text($text) {
        // حذف HTML tags
        $text = wp_strip_all_tags($text);
        
        // حذف فضاهای خالی اضافی
        $text = preg_replace('/\s+/', ' ', $text);
        
        // Trim
        $text = trim($text);
        
        // حداکثر 50000 کاراکتر
        if (strlen($text) > 50000) {
            $text = substr($text, 0, 50000);
        }
        
        return $text;
    }
    
    /**
     * Extract content from Elementor JSON (FAST version)
     */
    private static function extract_elementor_content_fast($elementor_data) {
        if (is_string($elementor_data)) {
            // سریع‌تر: با regex بجای JSON decode
            preg_match_all('/"(?:editor|title|description|text|content|html)"\s*:\s*"([^"]{10,})"/i', $elementor_data, $matches);
            if (!empty($matches[1])) {
                return implode(' ', $matches[1]);
            }
            
            // اگه regex کار نکرد، JSON decode
            $elementor_data = @json_decode($elementor_data, true);
        }
        
        if (!is_array($elementor_data)) {
            return '';
        }
        
        $text_content = [];
        
        // پیمایش سریع
        array_walk_recursive($elementor_data, function($value, $key) use (&$text_content) {
            if (in_array($key, ['editor', 'title', 'text', 'content']) && is_string($value) && strlen($value) > 10) {
                $text_content[] = $value;
            }
        });
        
        return implode(' ', $text_content);
    }
    
    /**
     * Extract content from Elementor JSON (OLD - compatible)
     */
    private static function extract_elementor_content($elementor_data) {
        return self::extract_elementor_content_fast($elementor_data);
    }
    
    /**
     * Extract content from Divi shortcodes (FAST version)
     */
    private static function extract_divi_content_fast($content) {
        if (empty($content)) {
            return '';
        }
        
        // فقط متن بین et_pb_text رو Extract کن (سریع)
        preg_match_all('/\[et_pb_text[^\]]*\](.*?)\[\/et_pb_text\]/s', $content, $matches);
        
        if (!empty($matches[1])) {
            return implode(' ', $matches[1]);
        }
        
        // بدون do_shortcode برای سرعت بیشتر
        return wp_strip_all_tags($content);
    }
    
    /**
     * Extract content from Divi shortcodes (OLD)
     */
    private static function extract_divi_content($content) {
        return self::extract_divi_content_fast($content);
    }
    
    /**
     * Sync page/post to backend
     */
    public static function sync_page($post_id) {
        
        try {
            // Step 1: Get post
            $post = get_post($post_id);
            if (!$post) {
                return ['success' => false, 'message' => '❌ پست یافت نشد (ID: ' . $post_id . ')'];
            }
            $error_details['post_id'] = $post_id;
            $error_details['post_title'] = $post->post_title;
            
            // Step 2: Check API token
            $api_token = get_option('pilito_ps_api_token', '');
            if (empty($api_token)) {
                return ['success' => false, 'message' => '❌ توکن API تنظیم نشده است'];
            }
            
            // Step 3: Build API URL
            $base_url = get_option('pilito_ps_api_url', '');
            
            if (empty($base_url)) {
                return ['success' => false, 'message' => '❌ تنظیمات API کامل نیست. لطفاً از بخش محصولات، توکن را تنظیم کنید.'];
            }
            
            // پاکسازی URL
            $base_url = rtrim($base_url, '/');
            
            // حذف /webhook اگر وجود داشت
            $base_url = str_replace('/webhook/', '', $base_url);
            $base_url = str_replace('/webhook', '', $base_url);
            
            // تبدیل woocommerce به wordpress-content
            if (strpos($base_url, 'woocommerce') !== false) {
                $api_endpoint = str_replace('woocommerce', 'wordpress-content', $base_url) . '/webhook/';
            } else {
                // اگه base URL اصلاً woocommerce نداره، پس خودمون بسازیم
                // مثلاً: http://185.164.72.165/api/v1/integrations/wordpress-content/webhook/
                if (strpos($base_url, '/api/') !== false) {
                    // داره /api/ داره
                    $parts = explode('/api/', $base_url);
                    $api_endpoint = $parts[0] . '/api/v1/integrations/wordpress-content/webhook/';
                } else {
                    // بدون /api/
                    $api_endpoint = $base_url . '/api/v1/integrations/wordpress-content/webhook/';
                }
            }
            
            $error_details['api_endpoint'] = $api_endpoint;
            $error_details['base_url'] = $base_url;
            
            // Step 4: Extract content (با timeout protection)
            set_time_limit(30); // max 30 seconds
            $full_content = self::extract_full_content_safe($post);
            $error_details['content_length'] = strlen($full_content);
            $error_details['word_count'] = str_word_count($full_content);
            
            // Step 5: Prepare payload
            $payload = [
                'event_type' => $post->post_type . '.updated',
                'event_id' => 'wp_' . $post->ID . '_' . time(),
                'content' => [
                    'id' => $post->ID,
                    'post_type' => $post->post_type,
                    'title' => $post->post_title,
                    'content' => $full_content,
                    'excerpt' => self::safe_excerpt($post),
                    'permalink' => get_permalink($post),
                    'author' => get_the_author_meta('display_name', $post->post_author),
                    'categories' => self::safe_categories($post->ID),
                    'tags' => self::safe_tags($post->ID),
                    'featured_image' => get_the_post_thumbnail_url($post, 'full') ?: '',
                    'status' => $post->post_status,
                    'modified_date' => $post->post_modified_gmt . 'Z',
                    'metadata' => []
                ]
            ];
            
            // Step 6: Send to API
            $response = wp_remote_post($api_endpoint, [
                'headers' => [
                    'Authorization' => 'Bearer ' . $api_token,
                    'Content-Type' => 'application/json',
                ],
                'body' => json_encode($payload),
                'timeout' => 15,
                'sslverify' => false, // در محیط development
            ]);
            
            // Step 7: Check response
            if (is_wp_error($response)) {
                $error_msg = $response->get_error_message();
                update_post_meta($post_id, '_pilito_page_sync_status', 'error');
                update_post_meta($post_id, '_pilito_page_sync_error', $error_msg);
                
                return ['success' => false, 'message' => '❌ خطای اتصال: ' . $error_msg];
            }
            
            $status_code = wp_remote_retrieve_response_code($response);
            $body = wp_remote_retrieve_body($response);
            
            // Success: 200 (OK), 201 (Created), 202 (Accepted - async processing)
            if ($status_code >= 200 && $status_code < 300) {
                // Success
                update_post_meta($post_id, '_pilito_page_sync_status', 'success');
                update_post_meta($post_id, '_pilito_page_last_sync', current_time('mysql'));
                update_post_meta($post_id, '_pilito_page_content_hash', md5($full_content));
                delete_post_meta($post_id, '_pilito_page_sync_error');
                
                $body_data = @json_decode($body, true);
                $message = isset($body_data['message']) ? $body_data['message'] : 'با موفقیت ارسال شد';
                
                return ['success' => true, 'message' => '✅ ' . $message];
            } else {
                // Error
                $error_msg = 'خطای سرور ' . $status_code;
                update_post_meta($post_id, '_pilito_page_sync_status', 'error');
                update_post_meta($post_id, '_pilito_page_sync_error', $error_msg . ': ' . substr($body, 0, 200));
                
                return ['success' => false, 'message' => '❌ ' . $error_msg];
            }
            
        } catch (Exception $e) {
            $error_msg = $e->getMessage();
            update_post_meta($post_id, '_pilito_page_sync_status', 'error');
            update_post_meta($post_id, '_pilito_page_sync_error', $error_msg);
            
            return ['success' => false, 'message' => '❌ خطای سیستم: ' . $error_msg];
        }
    }
    
    /**
     * Safe content extraction (با timeout protection)
     */
    private static function extract_full_content_safe($post) {
        try {
            $content = self::extract_full_content($post);
            // اگر خیلی طولانی شد، کوتاه کن (max 50000 chars)
            if (strlen($content) > 50000) {
                $content = substr($content, 0, 50000);
            }
            return $content;
        } catch (Exception $e) {
            // اگر extract کردن ناموفق بود، فقط post_content ساده رو برگردون
            return wp_strip_all_tags($post->post_content);
        }
    }
    
    /**
     * Safe excerpt extraction
     */
    private static function safe_excerpt($post) {
        try {
            return wp_strip_all_tags($post->post_excerpt);
        } catch (Exception $e) {
            return '';
        }
    }
    
    /**
     * Safe categories extraction
     */
    private static function safe_categories($post_id) {
        try {
            return wp_get_post_categories($post_id, ['fields' => 'names']);
        } catch (Exception $e) {
            return [];
        }
    }
    
    /**
     * Safe tags extraction
     */
    private static function safe_tags($post_id) {
        try {
            return wp_get_post_tags($post_id, ['fields' => 'names']);
        } catch (Exception $e) {
            return [];
        }
    }
}

