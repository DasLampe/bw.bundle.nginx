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
        'command': 'rpm --import  https://nginx.org/packages/keys/nginx_signing.key',
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
            22: 'jammy',
            20: 'focal',
            18: 'bionic',
            16: 'xenial',
        }
    }

    files["/etc/apt/sources.list.d/nginx.list"] = {
        'source': 'etc/apt/sources.list.d/nginx.list',
        'content_type': 'mako',
        'context': {
            'codename': release_names.get(node.os, 'debian').get(node.os_version[0], '11'),
            'distro': node.os,
        },
        'triggers': {
            'action:update_nginx_repo',
        },
        'tags': ['.pre'],
    }

    actions['getSignKey'] = {
        'command': 'curl https://nginx.org/keys/nginx_signing.key | '
                   'gpg --dearmor > /etc/apt/trusted.gpg.d/nginx_signing.gpg',
        'tags': [
            '.pre',
        ],
        'needs': [
            'pkg_apt:gpg',
        ],
        'unless': 'test -f /etc/apt/trusted.gpg.d/nginx_signing.gpg',
    }

    actions["update_nginx_repo"] = {
        'command': 'apt-get update',
        'needs': [
            'action:getSignKey',
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
        'running': True,
        'enabled': True,
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
files['/etc/nginx/snippets/ssl.conf'] = {
    'source': 'etc/nginx/snippets/ssl.conf',
    'content_type': 'mako',
    'context': {
        'config': node.metadata.get('nginx', {}),
    },
    'mode': '0644',
}

files['/etc/nginx/snippets/letsencrypt.conf'] = {
    'source': 'etc/nginx/snippets/letsencrypt.conf',
    'content_type': 'mako',
    'context': {
        'nginx': node.metadata.get('nginx', {}),
    },
    'mode': '0644',
}

for vhost_name, vhost in node.metadata.get('nginx', {}).get('sites', {}).items():
    # Setup SSL
    if vhost.get('ssl', {}):
        ssl = vhost.get('ssl')

        directories['/etc/nginx/ssl'] = {
            'mode': '0755',
            'owner': 'root',
            'group': 'root'
        }

        # Generate Snakeoil certificate
        if ssl.get('snakeoil', False):
            actions['generate_sneakoil_{}'.format(vhost_name)] = {
                'command': 'openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:4096 '
                '-subj "{}" -keyout {} -out {}'.format(
                    "/C=DE/ST=NRW/L=Cologne/O=DieSchoensteStadtDeutschlands/CN={}".format(vhost_name),
                    '/etc/nginx/ssl/{}.key'.format(vhost_name),
                    '/etc/nginx/ssl/{}.crt'.format(vhost_name), ),
                'unless': 'test -f {} && test -f {}'.format('/etc/nginx/ssl/{}.crt'.format(vhost_name),
                                                            '/etc/nginx/ssl/{}.key'.format(vhost_name)),
                'cascade_skip': False,
                'tags': ['nginx-config', 'nginx-ssl-config'],
                'needs': [
                    'directory:/etc/nginx/ssl',
                    'bundle:openssl'
                ],
            }

        # Enable LetsEncrypt
        if ssl.get('letsencrypt', False):
            if node.has_bundle('lego'):
                lego_path = node.metadata.get('lego').get('path')
                symlinks[f'/etc/nginx/ssl/{vhost_name}.crt'] = {
                    'target': f'{lego_path}/certificates/{vhost_name}.crt',
                    'tags': [
                        'nginx-config',
                        'nginx-ssl-config'
                    ],
                    'needs': [
                        'bundle:lego',
                    ],
                    'triggers': [
                        'svc_systemd:nginx:restart'
                    ],
                }
                symlinks[f'/etc/nginx/ssl/{vhost_name}.key'] = {
                    'target': f'{lego_path}/certificates/{vhost_name}.key',
                    'tags': [
                        'nginx-config',
                        'nginx-ssl-config'
                    ],
                    'needs': [
                        'bundle:lego',
                    ],
                    'triggers': [
                        'svc_systemd:nginx:restart'
                    ],
                }

        # Use static files, from data/ folder
        ssl_files = ssl.get('files', {})
        if ssl_files:
            files['/etc/nginx/ssl/{}'.format(ssl_files.get('cert'))] = {
                'source': ssl_files.get('cert'),
                'owner': node.metadata.get('nginx', {}).get('user'),
                'group': node.metadata.get('nginx', {}).get('group'),
                'mode': '0640',
                'tags': [
                    'nginx-config',
                    'nginx-ssl-config'
                ]
            }
            files['/etc/nginx/ssl/{}'.format(ssl_files.get('key'))] = {
                'content': repo.vault.decrypt_file(f"nginx/files/{ssl_files.get('key')}"),
                'owner': node.metadata.get('nginx', {}).get('user'),
                'group': node.metadata.get('nginx', {}).get('group'),
                'mode': '0640',
                'tags': [
                    'nginx-config',
                    'nginx-ssl-config'
                ]
            }

            if not '.'.join(ssl_files.get('cert').split('.')[:-1]) == vhost_name:
                symlinks['/etc/nginx/ssl/{}.crt'.format(vhost_name)] = {
                    'target': '/etc/nginx/ssl/{}'.format(ssl_files.get('cert')),
                    'tags': [
                        'nginx-config',
                        'nginx-ssl-config'
                    ]
                }
            if not '.'.join(ssl_files.get('key').split('.')[:-1]) == vhost_name:
                symlinks['/etc/nginx/ssl/{}.key'.format(vhost_name)] = {
                    'target': '/etc/nginx/ssl/{}'.format(ssl_files.get('key')),
                    'tags': [
                        'nginx-config',
                        'nginx-ssl-config'
                    ]
                }

        files['/etc/nginx/sites-available/{}.conf'.format(vhost_name)] = {
            'source': 'etc/nginx/sites-available/template_ssl.conf',
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
    else:
        files['/etc/nginx/sites-available/{}.conf'.format(vhost_name)] = {
            'source': 'etc/nginx/sites-available/template.conf',
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
    root_dir = vhost.get('root', '/var/www/{}/public_html'.format(vhost_name))
    directories[root_dir] = {
        "mode": "755",
        "unless": "test -d {}".format(root_dir),
    }
