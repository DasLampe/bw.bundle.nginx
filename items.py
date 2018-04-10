from bundlewrap.exceptions import BundleError
from os.path import dirname

# noinspection PyGlobalUndefined
global node

pkg_apt = {
    "nginx": {
        "installed": True,
    },
    "openssl": {
        "installed": True,
    }
}

#TODO: systemv compatible
svc_systemd = {
    "nginx": {
        'needs': ['pkg_apt:nginx'],
    }
}

directories = {}
actions = {}
symlinks = {}
files = {}


if 'nginx' in node.metadata:
    for vhost_name in node.metadata['nginx'].get('sites', {}):
        vhost = node.metadata['nginx']['sites'][vhost_name]

        #Setup SSL
        if vhost.get('ssl', False):
            directories['/etc/nginx/ssl'] = {
                'mode': '0755',
                'owner': 'root',
                'group': 'root'
            }

            if vhost.get('ssl_snakeoil', False):
                actions['generate_sneakoil_{}'.format(vhost_name)] = {
                    'command': 'openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 '\
                               '-subj "{}" -keyout {} -out {}'.format(\
                        "/C=DE/ST=NRW/L=Aachen/O=ScoutNet/CN={}".format(vhost_name),\
                        '/etc/nginx/ssl/{}.key'.format(vhost_name),\
                        '/etc/nginx/ssl/{}.crt'.format(vhost_name),\
                    ),
                    'unless': 'test -f {} && test -f {}'\
                        .format('/etc/nginx/ssl/{}.crt'.format(vhost_name),'/etc/nginx/ssl/{}.key'.format(vhost_name)),
                    'needs': ["pkg_apt:openssl"],
                    'cascade_skip': False,
                    'needed_by': [
                        "pkg_apt:nginx",
                        "svc_systemd:nginx"
                    ],
                }
            else:
                # TODO: Implement LetsEncrypt
                continue

    #Write vHost file
    files['/etc/nginx/sites-available/{}.conf'.format(vhost_name)] = {
        'source': 'etc/nginx/sites-available/template.conf',
        'content_type': 'mako',
        'mode': '0640',
        'owner': 'root',
        'group': 'root',
        'context': {'vhost_name': vhost_name, 'vhost': vhost},
        'triggers': [
            "svc_systemd:nginx:restart"
        ],
    }

    #Enable vHost
    if vhost.get('enabled', False):
        symlinks['/etc/nginx/sites-enabled/{}.conf'.format(vhost_name)] = {
            'group': 'root',
            'owner': 'root',
            'target': '../sites-available/{}.conf'.format(vhost_name),
            'triggers': [
                'svc_systemd:nginx:restart',
            ],
        }
    else:
        files['/etc/nginx/sites-enabled/{}.conf'.format(vhost_name)] = {
            'delete': True,
            'triggers': [
                'svc_systemd:nginx:restart',
            ],
        }

    #Create vHost dir
    directories["/var/www/{}/public_html".format(vhost_name)] = {
        "mode": "755",
    }