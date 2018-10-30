# Bundlewrap nginx
Install nginx on Debian and configure vHost.

__Don't use this for production! It's still work in progress!__

## Dependencies
* pkg_wrapper (https://github.com/DasLampe/bw.item.pkg_wrapper)


## Options
```python
'nginx': {
  'enable_websockets': False,
    'sites': {
        'www.example.test': {
            'servernames': ['example.test', 'example.local'],
            'enabled': True,
            'ssl': True,
            'ssl_snakeoil': True,
            'php': True,
            'upstream': {
              'backend': [
                'server 127.0.0.1:8080',
              ],
            },
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