# Bundlewrap nginx
Install nginx on Debian and configure vHost.

__Don't use this for production! It's still work in progress!__

## Options
```json
'nginx': {
    'sites': {
        'www.example.test': {
            'servernames': ['example.test', 'example.local'],
            'enabled': True,
            'ssl': True,
            'ssl_snakeoil': True,
            'php': True,
        },
    },
}
```