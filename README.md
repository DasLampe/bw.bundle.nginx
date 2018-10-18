# Bundlewrap nginx
Install nginx on Debian and configure vHost.

__Don't use this for production! It's still work in progress!__

## Options
```json
'nginx': {
  'enable_websockets': False,
    'sites': {
        'www.example.test': {
            'servernames': ['example.test', 'example.local'],
            'enabled': True,
            'ssl': True,
            'ssl_snakeoil': True,
            'php': True,
            'location': {
              '/': {
                'root /var/www/html;'
                'try_files $uri $uri/ index.php$is_args$args;',
              }
            }
        },
    },
}
```