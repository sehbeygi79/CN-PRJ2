"""
A simple mesh topology with one host per switch.
"""

from mininet.topo import Topo
from mininet.util import irange

class MeshTopo(Topo):
    "Full Mesh Topology with one host per switch"

    def __init__(self, numSws=5):
        "Create mesh topo."
        print('Create a mesh topology with {} switches'.format(numSws))

        # Initialize topology
        Topo.__init__(self)

        # Build Switches
        #XXX: Note "switches" is reserved
        self.sw_dict = {}
        for i in irange(1, numSws):
            switch = self.addSwitch('sw{}'.format(i), dpid='{}'.format(i))
            self.sw_dict[i] = switch
            host = self.addHost('h{}'.format(i))
            self.addLink(switch, host)

        # Connect Switches
        for src_i in irange(1, numSws):
            for dst_i in range(src_i+1, numSws+1):
                print('Connecting {} -> {}'.format(src_i, dst_i))
                self.addLink(self.sw_dict[src_i], self.sw_dict[dst_i])

# Allows the file to be imported using `mn --custom <filename> --topo mesh`
topos = {
    'mesh': MeshTopo
}
