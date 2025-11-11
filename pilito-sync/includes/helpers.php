<?php
/**
 * Helper functions
 */

defined('ABSPATH') || exit;

/**
 * Check if token is configured
 */
function pilito_ps_is_configured() {
    $token = get_option('pilito_ps_api_token');
    return !empty($token);
}

/**
 * Get sync statistics
 */
function pilito_ps_get_sync_stats() {
    global $wpdb;
    
    $total = $wpdb->get_var("
        SELECT COUNT(*)
        FROM {$wpdb->postmeta}
        WHERE meta_key = '_pilito_sync_status'
    ");
    
    $success = $wpdb->get_var("
        SELECT COUNT(*)
        FROM {$wpdb->postmeta}
        WHERE meta_key = '_pilito_sync_status'
        AND meta_value = 'success'
    ");
    
    $error = $wpdb->get_var("
        SELECT COUNT(*)
        FROM {$wpdb->postmeta}
        WHERE meta_key = '_pilito_sync_status'
        AND meta_value = 'error'
    ");
    
    return [
        'total' => (int) $total,
        'success' => (int) $success,
        'error' => (int) $error,
    ];
}

/**
 * Format date for display
 */
function pilito_ps_format_date($date) {
    if (empty($date)) {
        return '—';
    }
    
    return date_i18n(
        get_option('date_format') . ' ' . get_option('time_format'),
        strtotime($date)
    );
}
