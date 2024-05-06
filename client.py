from communex.client import CommuneClient
from communex._common import get_node_url
from communex.compat.key import classic_load_key

client = CommuneClient(get_node_url())

client.compose_call(
    module="SubnetParams",
    fn="SubnetParams",
    key=classic_load_key(""),
    params=[0],
    wait_for_finalization=False,
    wait_for_inclusion=False,
    sudo=False,
)
