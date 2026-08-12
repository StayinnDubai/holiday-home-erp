import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';

/** Online Accounts -- a standalone credential register, generalizing Building's
 * portal_* fields (buildings.config.ts) which are Building-only and deliberately
 * have no password field. This is broader (any service, any related record) and
 * does store a password: this app has no encryption/secrets layer anywhere yet, so
 * it's kept as plain text like every other string field -- a real limitation, not
 * an oversight. `related_to` is a free-text label, not a real link, since there's
 * no generic "pick any record" selector in this app. */
export const ONLINE_ACCOUNTS_CONFIG: EntityPageConfig = {
  title: 'Online Accounts',
  subtitle: 'Credential register -- utility portals, OTAs, banks, and other online accounts used to run the business.',
  resourcePath: 'online-accounts',
  auditEntityType: 'online_account',
  fields: [
    { key: 'service_name', label: 'Service name', type: 'text', required: true, gridWidth: 200 },
    { key: 'category', label: 'Category', type: 'text', gridWidth: 150 },
    { key: 'related_to', label: 'Related to', type: 'text', gridWidth: 200 },
    { key: 'url', label: 'URL', type: 'text', showInGrid: false },
    { key: 'username', label: 'Username', type: 'text', gridWidth: 160 },
    { key: 'password', label: 'Password', type: 'text', showInGrid: false },
    {
      key: 'sign_in_method',
      label: 'Sign-in method',
      type: 'select',
      options: [
        { label: 'Password', value: 'password' },
        { label: 'Two-factor', value: 'two_factor' },
        { label: 'SSO', value: 'sso' },
        { label: 'API key', value: 'api_key' },
        { label: 'Other', value: 'other' },
      ],
      gridWidth: 140,
    },
    { key: 'recovery_email', label: 'Recovery email', type: 'text', showInGrid: false },
    { key: 'comments', label: 'Comments', type: 'textarea', showInGrid: false },
    { key: 'active', label: 'Active', type: 'boolean', gridWidth: 90 },
  ],
};
