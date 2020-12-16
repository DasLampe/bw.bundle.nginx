# Bundlewrap nginx
Install nginx on Debian and configure vHost.

__Don't use this for production! It's still work in progress!__

## Dependencies
* [apt-Bundle](https://github.com/sHorst/bw.bundle.apt)


## Options
```python
'nginx': {
  'enable_websockets': False,
    'sites': {
        'www.example.test': {
			'default': False,
            'additional_server_names': ['example.test', 'example.local'],
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
