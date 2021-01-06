# Bundlewrap nginx
Install nginx on Debian, Amazon Linux or CentOs and configure vHost.

__Don't use this for production! It's still work in progress!__

## Options
```python
'nginx': {
    'enable_websockets': False,
    'resolver': ['1.1.1.1', '1.0.0.1', '[2606:4700:4700::1111]', '[2606:4700:4700::1001]'],
    'ssl': {
        'protocols': ['TLSv1.2', 'TLSv1.3'],
        'ecdh_curves': ['X25519', 'secp521r1', 'secp384r1', 'prime256v1'],
        'prefer_server_ciphers': 'off',
        'ciphers': ['ECDHE-ECDSA-CHACHA20-POLY1305', 'ECDHE-RSA-CHACHA20-POLY1305', 'ECDHE-ECDSA-AES128-GCM-SHA256', 'ECDHE-RSA-AES128-GCM-SHA256', 'ECDHE-ECDSA-AES256-GCM-SHA384', 'ECDHE-RSA-AES256-GCM-SHA384', 'DHE-RSA-AES128-GCM-SHA256', 'DHE-RSA-AES256-GCM-SHA384', 'ECDHE-ECDSA-AES128-SHA256', 'ECDHE-RSA-AES128-SHA256', 'ECDHE-ECDSA-AES128-SHA', 'ECDHE-RSA-AES256-SHA384', 'ECDHE-RSA-AES128-SHA', 'ECDHE-ECDSA-AES256-SHA384', 'ECDHE-ECDSA-AES256-SHA', 'ECDHE-RSA-AES256-SHA', 'DHE-RSA-AES128-SHA256', 'DHE-RSA-AES128-SHA', 'DHE-RSA-AES256-SHA256', 'DHE-RSA-AES256-SHA', 'ECDHE-ECDSA-DES-CBC3-SHA', 'ECDHE-RSA-DES-CBC3-SHA', 'EDH-RSA-DES-CBC3-SHA', 'AES128-GCM-SHA256', 'AES256-GCM-SHA384', 'AES128-SHA256', 'AES256-SHA256', 'AES128-SHA', 'AES256-SHA', 'DES-CBC3-SHA', '!DSS'],
        'stapling': 'on',
        'staping_verify': 'on',
    },
    'sites': {
        'www.example.org': {
            'default': False,
            'additional_server_names': ['example.test', 'example.local'],
            'enabled': True,
            'ssl': {
                'redirect_insecure': True,
                'snakeoil': False,
                'letsencrypt': False,
                'files': {
                    'cert': 'example.org.crt',
                    'key': 'example.org.key'
                },
                'session': {
                    'timeout': '1d',
                    'cache': 'shared:SSL:50m',
                    'tickets': 'off',
                },
            },
            'upstream': {
              'backend': [
                'server 127.0.0.1:8080',
              ],
            },
            'root': '/var/www/www.example.org/public',
            'location': {
              '/': [
                'root /var/www/html;'
                'try_files $uri $uri/ index.php$is_args$args;',
              ],
              '/backend': [
                'proxy_pass http://backend;',
              ],
            },
        },
    },
}
```
