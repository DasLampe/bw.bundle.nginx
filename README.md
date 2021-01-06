# Bundlewrap nginx
Install nginx on Debian, Amazon Linux or CentOs and configure vHost.

__Don't use this for production! It's still work in progress!__

## Options
```python
'nginx': {
  'enable_websockets': False,
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
