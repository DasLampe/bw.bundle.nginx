from bundlewrap.exceptions import BundleError
from os.path import dirname

# noinspection PyGlobalUndefined
global node

packages = {
    "nginx": {
        "installed": True,
    },
    "openssl": {
        "installed": True,
    },
}

pkg_apt = {}
pkg_yum = {}

for pkg, config in packages.items():
    if node.os == "debian":
        if pkg not in pkg_apt.keys():
            pkg_apt[pkg] = config
    if node.os == "centos":
        if pkg not in pkg_yum.keys():
            pkg_yum[pkg] = config

# TODO: systemv compatible
svc_systemd = {
    "nginx": {
    }
}

directories = {}
actions = {}
symlinks = {}
files = {}

if 'nginx' in node.metadata:
    files['/etc/nginx/nginx.conf'] = {
        'source': 'etc/nginx/nginx.conf',
        'content_type': 'mako',
        'context': {
            'nginx': node.metadata['nginx'],
        },
        'mode': '0644',
    }

    for vhost_name in node.metadata['nginx'].get('sites', {}):
        vhost = node.metadata['nginx']['sites'][vhost_name]

        # Setup SSL
        if vhost.get('ssl', False):
            directories['/etc/nginx/ssl'] = {
                'mode': '0755',
                'owner': 'root',
                'group': 'root'
            }

            if vhost.get('ssl_snakeoil', False):
                actions['generate_sneakoil_{}'.format(vhost_name)] = {
                    'command': 'openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 '
                               '-subj "{}" -keyout {} -out {}'.format(
                                    "/C=DE/ST=NRW/L=Aachen/O=Kisters AG/CN={}".format(vhost_name),
                                    '/etc/nginx/ssl/{}.key'.format(vhost_name),
                                    '/etc/nginx/ssl/{}.crt'.format(vhost_name), ),
                    'unless': 'test -f {} && test -f {}'.format('/etc/nginx/ssl/{}.crt'.format(vhost_name),
                                                                '/etc/nginx/ssl/{}.key'.format(vhost_name)),
                    'cascade_skip': False,
                    'needed_by': [
                        "svc_systemd:nginx"
                    ],
                }

                if node.os == "debian":
                    actions['generate_sneakoil_{}'.format(vhost_name)].get('need', []).append('pkg_apt:openssl')
                    actions['generate_sneakoil_{}'.format(vhost_name)]['need_by'].append('pkg_apt:nginx')
                if node.os == "centos":
                    actions['generate_sneakoil_{}'.format(vhost_name)].get('need', []).append('pkg_yum:openssl')
                    actions['generate_sneakoil_{}'.format(vhost_name)].get('need_by', []).append('pkg_yum:nginx')
            else:
                # TODO: Implement LetsEncrypt
                continue

        # Write vHost file
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

        # Enable vHost
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

        # Create vHost dir
        directories["/var/www/{}/public_html".format(vhost_name)] = {
            "mode": "755",
        }
