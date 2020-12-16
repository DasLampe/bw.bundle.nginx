from bundlewrap.exceptions import BundleError
from os.path import dirname

# noinspection PyGlobalUndefined
global node

directories = {}
actions = {}
symlinks = {}
files = {}

users = {
    'nginx': {},
}

if node.os == 'amazonlinux':
    actions['enable_nginx_for_amazonlinux'] = {
        'command': 'amazon-linux-extras enable nginx1',
        'tags': ['.pre'],
    }

if node.os in node.OS_FAMILY_REDHAT:
    files["/etc/yum.repos.d/nginx.repo"] = {
        'source': 'etc/yum.repos.d/nginx.repo',
        'content_type': 'mako',
        'context': {
            'node_os': node.os,
            'node_os_version': node.os_version[0]
        },
        'tags': ['.pre'],
    }

    actions["import_nginx_key"] = {
        'command': 'rpm --import https://nginx.org/keys/nginx_signing.key',
        'unless': 'rpm -qa gpg-pubkey\* --qf "%{name}-%{version}-%{release}-%{summary}\n" | grep "signing-key@nginx.com"',
        'tags': ['.pre']
    }

if node.os in node.OS_FAMILY_REDHAT or node.os == 'amazonlinux':
    pkg_yum = {
        'nginx': {
            'installed': True,
            'tags': ['nginx-install'],
            'needs': [
                'tag:.pre'
            ],
        }
    }

if node.os in node.OS_FAMILY_DEBIAN:
    release_names = {
        'debian': {
            8: 'jessie',
            9: 'stretch',
            10: 'buster',
            11: 'bullseye',
            12: 'bookworm',
        },
        'ubuntu': {
            20: 'focal',
            18: 'bionic',
            16: 'xenial',
        }
    }

    files["/etc/apt/sources.list.d/nginx-repo.list"] = {
        'source': 'etc/apt/sources.list.d/nginx-repo.list',
        'content_type': 'mako',
        'context': {
            'codename': release_names.get(node.os, 'debian').get(node.os_version[0], '11'),
        },
        'triggers': {
            'action:update_nginx_repo',
        },
        'tags': ['.pre'],
    }

    actions["import_nginx_key"] = {
        'command': 'curl https://nginx.org/keys/nginx_signing.key | apt-key add -',
        'unless': 'apt-key list | grep "nginx signing key <signing-key@nginx.com>" &> /dev/null',
        'tags': ['.pre'],
    }

    actions["update_nginx_repo"] = {
        'command': 'apt-get update',
        'needs': [
            'action:import_nginx_key',
        ],
        'triggered': True,
        'tags': ['.pre'],
    }

    pkg_apt = {
        'nginx': {
            'installed': True,
            'tags': ['nginx-install'],
            'needs': [
                'tag:.pre'
            ],
        }
    }

svc_systemd = {
    "nginx": {
        'needs': [
            'tag:nginx-install',
            'user:nginx',
            'file:/etc/nginx/nginx.conf',
            'tag:nginx-config',
        ],
    }
}

users = {
    'nginx': {}
}

files['/etc/nginx/nginx.conf'] = {
    'source': 'etc/nginx/nginx.conf',
    'content_type': 'mako',
    'context': {
        'nginx': node.metadata.get('nginx', {}),
    },
    'mode': '0644',
}

for vhost_name, vhost in node.metadata.get('nginx', {}).get('sites', {}).items():
    # Setup SSL
    if vhost.get('ssl', False):
        directories['/etc/nginx/ssl'] = {
            'mode': '0755',
            'owner': 'root',
            'group': 'root'
        }

        if vhost.get('ssl_snakeoil', False):
            actions['generate_sneakoil_{}'.format(vhost_name)] = {
                'command': 'openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:4096 '
                '-subj "{}" -keyout {} -out {}'.format(
                    "/C=DE/ST=NRW/L=Cologne/O=DieSchoensteStadtDeutschlands/CN={}".format(vhost_name),
                    '/etc/nginx/ssl/{}.key'.format(vhost_name),
                    '/etc/nginx/ssl/{}.crt'.format(vhost_name), ),
                'unless': 'test -f {} && test -f {}'.format('/etc/nginx/ssl/{}.crt'.format(vhost_name),
                                                            '/etc/nginx/ssl/{}.key'.format(vhost_name)),
                'cascade_skip': False,
                'tags': ['nginx-config'],
                'needs': [
                    'bundle:openssl'
                ],
            }
        else:
            if vhost.get('letsencrypt', False):
                files['/etc/nginx/snippets/letsencrypt.conf'] = {
                    'source': 'etc/nginx/snippets/letsencrypt.conf',
                    'mode': '0644',
                    'tags': ['nginx-config'],
                }
            # TODO: Implement LetsEncrypt

    # Write vHost file
    if vhost.get('ssl', False):
        files['/etc/nginx/sites-available/{}.conf'.format(vhost_name)] = {
            'source': 'etc/nginx/sites-available/template_ssl.conf',
            'content_type': 'mako',
            'mode': '0644',
            'owner': 'root',
            'group': 'root',
            'context': {'vhost_name': vhost_name, 'vhost': vhost},
            'tags': ['nginx-config'],
            'triggers': [
                "svc_systemd:nginx:restart"
            ],
        }
    else:
        files['/etc/nginx/sites-available/{}.conf'.format(vhost_name)] = {
            'source': 'etc/nginx/sites-available/template.conf',
            'content_type': 'mako',
            'mode': '0644',
            'owner': 'root',
            'group': 'root',
            'tags': ['nginx-config'],
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
            'tags': ['nginx-config'],
            'triggers': [
                'svc_systemd:nginx:restart',
            ],
        }
    else:
        files['/etc/nginx/sites-enabled/{}.conf'.format(vhost_name)] = {
            'delete': True,
            'tags': ['nginx-config'],
            'triggers': [
                'svc_systemd:nginx:restart',
            ],
        }

    # Create vHost dir
    directories["/var/www/{}/public_html".format(vhost_name)] = {
        "mode": "755",
        "unless": "test -d /var/www/{}/public_html".format(vhost_name),
    }
