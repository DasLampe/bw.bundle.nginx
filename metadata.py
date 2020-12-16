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
