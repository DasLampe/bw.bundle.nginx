global node
global repo

@metadata_processor
def add_apt_packages(metadata):
    if node.has_bundle("apt"):
        metadata.setdefault('apt', {})
        metadata['apt'].setdefault('packages', {})

        metadata['apt']['packages']['nginx'] = {'installed': True, 'needs': ['action:update_nginx_repo']}
        metadata['apt']['packages']['openssl'] = {'installed': True}

    return metadata, DONE


@metadata_processor
def add_iptables(metadata):
    if node.has_bundle("iptables"):
        metadata += repo.libs.iptables.accept().chain('INPUT').tcp().dest_port(80)


        enableSSL = False
        for _,config in metadata.get('nginx', {}).get('sites', {}).items():
            if config.get('ssl', False):
                enableSSL = True

        if enableSSL == True:
            metadata += repo.libs.iptables.accept().chain('INPUT').tcp().dest_port(443)

    return metadata, DONE