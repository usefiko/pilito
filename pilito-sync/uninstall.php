<?php
/**
 * Uninstall Script
 * Fired when the plugin is uninstalled
 */

// If uninstall not called from WordPress, exit
if (!defined('WP_UNINSTALL_PLUGIN')) {
    exit;
}

// Delete options
delete_option('pilito_ps_api_token');
delete_option('pilito_ps_enable_logging');
delete_option('pilito_ps_api_url');

// Delete all transients
global $wpdb;
$wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_pilito_sync_%'");
$wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_timeout_pilito_sync_%'");

// Delete all product meta
$wpdb->query("DELETE FROM {$wpdb->postmeta} WHERE meta_key LIKE '_pilito_%'");
