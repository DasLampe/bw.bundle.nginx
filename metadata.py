defaults = {
    'nginx': {
        'lego_renew_hook': '''
            install -u nginx -g nginx -m 0640 ${LEGO_CERT_KEY_PATH} /etc/nginx/ssl/
            install -u nginx -g nginx -m 0640 ${LEGO_CERT_PATH} /etc/nginx/ssl/

            systemctl restart nginx
        '''
    }
}


@metadata_reactor
def add_iptables(metadata):
    if not node.has_bundle("iptables"):
        raise DoNotRunAgain

    interfaces = ['main_interface']
    interfaces += metadata.get('nginx/additional_interfaces', [])

    enable_ssl = False
    for _, config in metadata.get('nginx', {}).get('sites', {}).items():
        if config.get('ssl', False):
            enable_ssl = True

    iptables_rules = {}
    for interface in interfaces:
        iptables_rules += repo.libs.iptables.accept(). \
            input(interface). \
            tcp(). \
            dest_port(80)
        if enable_ssl:
            iptables_rules += repo.libs.iptables.accept(). \
                input(interface). \
                tcp(). \
                dest_port(443)

    return iptables_rules


# See https://github.com/DasLampe/bw.bundle.nginx/issues/3
@metadata_reactor
def process_additional_config(metadata):
    return_dict = {
        'nginx': {
            'sites': {
            }
        }
    }

    process_additional_config = []
    for name, config in metadata.get('nginx/sites', {}).items():
        additional_config = config.get('additional_config', [])
        if isinstance(additional_config, str):
            process_additional_config = [additional_config.strip(), ],
        else:
            process_additional_config = additional_config

        return_dict['nginx']['sites'][name] = {
            'processed_additional_config': [entry + ';' if not entry.endswith(';') else entry for entry in process_additional_config],
        }

    return return_dict

@metadata_reactor
def add_default_includes_vhosts(metadata):
    return_dict = {
        'nginx': {
            'sites': {}
        }
    }

    default_includes = metadata.get('nginx/default_includes', [])
    for name, config in metadata.get('nginx/sites', {}).items():
        includes = []
        [includes.append(x) for x in default_includes + config.get('includes', []) if x not in includes]
        return_dict['nginx']['sites'][name] = {
            'includes': default_includes,
        }

    return return_dict

@metadata_reactor
def add_apt_packages(metadata):
    if node.has_bundle("apt"):
        return {
            'apt': {
                'packages': {
                    'gpg': {
                        'installed': True,
                    },
                },
            },
        }

@metadata_reactor
def add_lego_renew_hook(metadata):
    if node.has_bundle("lego"):
        return {
            'lego': {
                'renew_hooks': [metadata.get('nginx/lego_renew_hook', ""), ],
            }
        }
