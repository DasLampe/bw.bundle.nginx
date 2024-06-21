# Bundlewrap nginx
Install nginx on Debian and configure vHost.

## Use includes
You can define includes via `default_includes` or `includes` list.
You can either specify a file on your server or you can put the file into `data/nginx/includes/[basename]`, the file will be placed in the defined filepath.

`default_includes` will be added to each site. If you want to ignore `default_includes` in one site you could use `'includes': bundlewrap.metadata.atomic([])`

## Options
```python
'nginx': {
	'user': 'nginx',
	'compress': True,
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
    'default_includes': [
        '/etc/nginx/snippets/caching.conf',
    ],
    'sites': {
        'www.example.org': {
            'enabled': True,
            'default': False,
            'additional_server_names': ['example.test', 'example.local'],
            'redirect_to_main_server_name': True,
            'additional_config': [
                'error 503 /error/503.json;',
            ],
            'includes': [
                '/etc/nginx/snippets/piwik.conf',
            ]
            'ssl': {
                'http2': True,
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
