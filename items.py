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

if node.os in node.OS_FAMILY_REDHAT:
    files["/etc/yum.repos.d/nginx.repo"] = {
        'source': 'etc/yum.repos.d/nginx.repo',
        'content_type': 'mako',
        'context': {
            'node_os': node.os,
            'node_os_version': node.os_version[0]
        },
    }

    actions["import_nginx_key"] = {
        'command': 'rpm --import https://nginx.org/keys/nginx_signing.key',
        'unless': 'rpm -qa gpg-pubkey\* --qf "%{name}-%{version}-%{release}-%{summary}\n" | grep "signing-key@nginx.com"'
    }

    actions["update_nginx_repo"] = {
        'command': '',# Nothing todo
        'needs': [
            'action:import_nginx_key',
            'file:/etc/yum.repos.d/nginx.repo',
        ],
    }


if node.os == "debian":
    codename = "stretch"
    if node.os_version[0] == 8:
        codename = "jessie"

    files["/etc/apt/sources.list.d/nginx-repo.list"] = {
        'source': 'etc/apt/sources.list.d/nginx-repo.list',
        'content_type': 'mako',
        'context': {
            'codename': codename,
        },
        'triggers': {
            'action:update_nginx_repo',
        }
    }

    actions["import_nginx_key"] = {
        'command': 'curl https://nginx.org/keys/nginx_signing.key | apt-key add -',
        'unless': 'apt-key list | grep "nginx signing key <signing-key@nginx.com>"',
    }

    actions["update_nginx_repo"] = {
        'command': 'apt-get update',
        'needs': [
            'action:import_nginx_key',
            'file:/etc/apt/sources.list.d/nginx-repo.list',
        ],
        'triggered': True,
    }

# TODO: systemv compatible
svc_systemd = {
    "nginx": {
        'needs': [
            'pkg_apt:nginx',
            'user:nginx',
            'file:/etc/nginx/nginx.conf',
        ],
    }
}

users = {
    'nginx': {}
}



if 'nginx' in node.metadata:
    files['/etc/nginx/nginx.conf'] = {
        'source': 'etc/nginx/nginx.conf',
        'content_type': 'mako',
        'context': {
            'nginx': node.metadata['nginx'],
        },
        'mode': '0644',
    }

    for vhost_name,vhost in node.metadata['nginx'].get('sites', {}).items():
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
                        'svc_systemd:nginx',
                        'pkg_apt:nginx',
                    ],
                    'needs': [
                        'pkg_apt:openssl'
                    ],
                }
            else:
                # TODO: Implement LetsEncrypt
                pass

        # Write vHost file
        if vhost.get('ssl', False):
            files['/etc/nginx/sites-available/{}.conf'.format(vhost_name)] = {
                'source': 'etc/nginx/sites-available/template_ssl.conf',
                'content_type': 'mako',
                'mode': '0644',
                'owner': 'root',
                'group': 'root',
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
            "unless": "test -d /var/www/{}/public_html".format(vhost_name),
        }
