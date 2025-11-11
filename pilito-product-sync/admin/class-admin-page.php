<?php
/**
 * Admin Settings Page - Minimal & Professional
 */

defined('ABSPATH') || exit;

class Pilito_PS_Admin_Page {
    
    /**
     * Initialize
     */
    public static function init() {
        add_action('admin_menu', [__CLASS__, 'add_menu']);
        add_action('admin_init', [__CLASS__, 'register_settings']);
        add_action('admin_enqueue_scripts', [__CLASS__, 'enqueue_assets']);
        
        // AJAX handlers
        add_action('wp_ajax_pilito_ps_test_connection', [__CLASS__, 'ajax_test_connection']);
        add_action('wp_ajax_pilito_ps_bulk_sync', [__CLASS__, 'ajax_bulk_sync']);
        add_action('wp_ajax_pilito_ps_get_pages', [__CLASS__, 'ajax_get_pages']);
        add_action('wp_ajax_pilito_ps_sync_pages', [__CLASS__, 'ajax_sync_pages']);
    }
    
    /**
     * Add admin menu
     */
    public static function add_menu() {
        // منوی اصلی پیلیتو (با SVG icon)
        $icon_svg = 'data:image/svg+xml;base64,' . base64_encode(file_get_contents(PILITO_PS_PLUGIN_DIR . 'assets/icon.svg'));
        
        add_menu_page(
            'پیلیتو',
            'پیلیتو',
            'manage_options',
            'pilito-dashboard',
            [__CLASS__, 'render_dashboard'],
            $icon_svg,
            56
        );
        
        // زیرمنو: محصولات (بدون ایکون)
        add_submenu_page(
            'pilito-dashboard',
            'همگام‌سازی محصولات',
            'محصولات',
            'manage_options',
            'pilito-dashboard'
        );
        
        // زیرمنو: صفحات (بدون ایکون)
        add_submenu_page(
            'pilito-dashboard',
            'همگام‌سازی صفحات و نوشته‌ها',
            'صفحات و نوشته‌ها',
            'manage_options',
            'pilito-pages',
            [__CLASS__, 'render_pages']
        );
        
        // زیرمنو: چت (بدون ایکون)
        add_submenu_page(
            'pilito-dashboard',
            'چت آنلاین',
            'چت آنلاین',
            'manage_options',
            'pilito-chat',
            [__CLASS__, 'render_chat']
        );
    }
    
    /**
     * Register settings
     */
    public static function register_settings() {
        register_setting('pilito_ps_sync', 'pilito_ps_api_token', [
            'type' => 'string',
            'sanitize_callback' => 'sanitize_text_field',
        ]);
        
        register_setting('pilito_ps_sync', 'pilito_ps_enable_logging', [
            'type' => 'boolean',
        ]);
        
        register_setting('pilito_ps_sync', 'pilito_ps_api_url', [
            'type' => 'string',
            'sanitize_callback' => 'esc_url_raw',
            'default' => 'https://api.pilito.com/api/integrations/woocommerce',
        ]);
        
        register_setting('pilito_ps_sync', 'pilito_ps_auto_sync_pages', [
            'type' => 'boolean',
        ]);
        
        register_setting('pilito_ps_sync', 'pilito_ps_auto_sync_posts', [
            'type' => 'boolean',
        ]);
    }
    
    /**
     * Enqueue assets
     */
    public static function enqueue_assets($hook) {
        // Load on all Pilito pages (check both slug and parent)
        if (strpos($hook, 'pilito-') === false && strpos($hook, 'پیلیتو') === false) {
            return;
        }
        
        wp_enqueue_style(
            'pilito-ps-admin',
            PILITO_PS_PLUGIN_URL . 'admin/css/admin.css',
            [],
            PILITO_PS_VERSION
        );
        
        wp_enqueue_script(
            'pilito-ps-admin',
            PILITO_PS_PLUGIN_URL . 'admin/js/admin.js',
            ['jquery'],
            PILITO_PS_VERSION,
            true
        );
        
        wp_localize_script('pilito-ps-admin', 'pilitoPS', [
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('pilito_ps_test'),
            'bulk_nonce' => wp_create_nonce('pilito_ps_bulk'),
            'pages_nonce' => wp_create_nonce('pilito_ps_pages'),
            'logo_url' => PILITO_PS_PLUGIN_URL . 'assets/logo.svg',
        ]);
    }
    
    /**
     * Render main dashboard (Products)
     */
    public static function render_dashboard() {
        include PILITO_PS_PLUGIN_DIR . 'admin/views/dashboard.php';
    }
    
    /**
     * Render pages sync
     */
    public static function render_pages() {
        include PILITO_PS_PLUGIN_DIR . 'admin/views/pages.php';
    }
    
    /**
     * Render chat (Coming Soon)
     */
    public static function render_chat() {
        include PILITO_PS_PLUGIN_DIR . 'admin/views/chat.php';
    }
    
    /**
     * AJAX: Test connection
     */
    public static function ajax_test_connection() {
        check_ajax_referer('pilito_ps_test', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error(['message' => 'عدم دسترسی']);
        }
        
        $token = sanitize_text_field($_POST['token'] ?? '');
        
        if (empty($token)) {
            wp_send_json_error(['message' => 'لطفاً ابتدا token را وارد کنید']);
        }
        
        $result = Pilito_PS_API::test_connection($token);
        
        if ($result['success']) {
            wp_send_json_success($result);
        } else {
            wp_send_json_error($result);
        }
    }
    
    /**
     * AJAX: Bulk sync products
     */
    public static function ajax_bulk_sync() {
        check_ajax_referer('pilito_ps_bulk', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error(['message' => 'عدم دسترسی']);
        }
        
        $batch_size = 10;
        $offset = intval($_POST['offset'] ?? 0);
        
        // Get published products
        $args = [
            'post_type' => 'product',
            'post_status' => 'publish',
            'posts_per_page' => $batch_size,
            'offset' => $offset,
            'orderby' => 'ID',
            'order' => 'ASC',
        ];
        
        $query = new WP_Query($args);
        $total = $query->found_posts;
        $products = $query->posts;
        
        $results = [
            'total' => $total,
            'processed' => $offset,
            'batch_size' => count($products),
            'success' => 0,
            'failed' => 0,
            'errors' => [],
        ];
        
        // Sync each product in batch
        foreach ($products as $post) {
            $result = Pilito_PS_API::sync_product($post->ID, 'product.updated');
            
            if (is_wp_error($result)) {
                $results['failed']++;
                $results['errors'][] = [
                    'id' => $post->ID,
                    'title' => get_the_title($post->ID),
                    'error' => $result->get_error_message()
                ];
            } else {
                $results['success']++;
            }
            
            $results['processed']++;
        }
        
        $results['has_more'] = ($offset + $batch_size) < $total;
        $results['next_offset'] = $offset + $batch_size;
        $results['progress_percent'] = min(100, round(($results['processed'] / $total) * 100));
        
        wp_send_json_success($results);
    }
    
    /**
     * AJAX: Get pages/posts for sync
     */
    public static function ajax_get_pages() {
        check_ajax_referer('pilito_ps_pages', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error(['message' => 'عدم دسترسی']);
        }
        
        $post_type = sanitize_text_field($_POST['post_type'] ?? 'page');
        $filter = sanitize_text_field($_POST['filter'] ?? 'all');
        
        $args = [
            'post_type' => $post_type,
            'post_status' => 'publish',
            'posts_per_page' => -1,
            'orderby' => 'title',
            'order' => 'ASC',
        ];
        
        $query = new WP_Query($args);
        $items = [];
        
        foreach ($query->posts as $post) {
            $sync_status = get_post_meta($post->ID, '_pilito_page_sync_status', true);
            $last_sync = get_post_meta($post->ID, '_pilito_page_last_sync', true);
            
            // Get real content (same as sync process)
            $full_content = Pilito_PS_Content::get_full_content_for_display($post);
            $content_hash = md5($full_content);
            $old_hash = get_post_meta($post->ID, '_pilito_page_content_hash', true);
            
            // Determine status
            $status = 'not_synced';
            if ($sync_status === 'success') {
                if (!empty($old_hash) && $content_hash !== $old_hash) {
                    $status = 'need_update';
                } else {
                    $status = 'synced';
                }
            } elseif ($sync_status === 'error') {
                $status = 'error';
            }
            
            // Apply filter
            if ($filter === 'not_synced' && $status !== 'not_synced') continue;
            if ($filter === 'need_update' && $status !== 'need_update') continue;
            if ($filter === 'synced' && $status !== 'synced') continue;
            
            // Calculate word count from extracted content
            $word_count = count(preg_split('/\s+/u', trim($full_content), -1, PREG_SPLIT_NO_EMPTY));
            
            $items[] = [
                'id' => $post->ID,
                'title' => $post->post_title,
                'status' => $status,
                'last_sync' => $last_sync,
                'modified' => $post->post_modified,
                'word_count' => $word_count,
            ];
        }
        
        wp_send_json_success([
            'items' => $items,
            'total' => count($items),
        ]);
    }
    
    /**
     * AJAX: Sync selected pages/posts
     */
    public static function ajax_sync_pages() {
        check_ajax_referer('pilito_ps_pages', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error(['message' => 'عدم دسترسی']);
        }
        
        $post_ids = array_map('intval', $_POST['post_ids'] ?? []);
        
        if (empty($post_ids)) {
            wp_send_json_error(['message' => 'هیچ موردی انتخاب نشده']);
        }
        
        $results = [
            'total' => count($post_ids),
            'success' => 0,
            'failed' => 0,
            'errors' => [],
        ];
        
        foreach ($post_ids as $post_id) {
            $result = Pilito_PS_Content::sync_page($post_id);
            
            if ($result['success']) {
                $results['success']++;
            } else {
                $results['failed']++;
                $results['errors'][] = [
                    'post_id' => $post_id,
                    'message' => $result['message']
                ];
            }
        }
        
        wp_send_json_success($results);
    }
}
