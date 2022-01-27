defaults = {}


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
    for name, config in metadata.get('nginx/sites').items():
        additional_config = config.get('additional_config', [])
        if isinstance(additional_config, str):
            return_dict['nginx']['sites'][name] = {
                'processed_additional_config': [additional_config.strip(), ],
            }
        else:
            return_dict['nginx']['sites'][name] = {
                'processed_additional_config': additional_config,
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
