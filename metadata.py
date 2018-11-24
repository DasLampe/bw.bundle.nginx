global node
global repo

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