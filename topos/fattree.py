"""
A simple full bisection bandwidth fattree topology where each swith has k ports
and connects to k/2 hosts.

See the following paper for an introduction to fattree topologies in data
centers if you are not familiar with them: Mysore et al., "PortLand: A Scalable
Fault-Tolerant Layer 2Data Center Network Fabric", SIGCOMM 09,
https://cseweb.ucsd.edu/~vahdat/papers/portland-sigcomm09.pdf
"""

from mininet.topo import Topo
from mininet.util import irange

class FatTreeTopo(Topo):
    "Full Bisection Bandwidth FatTree Topology"

    def __init__(self, k=4):
        "Create fattree topo."

        # Initialize topology
        Topo.__init__(self)

        # Save different parameters
        if (k % 2) != 0:
            print('Number of ports in a fattree must be even!')
            return
        num_pods = k
        num_core = k * k / 4
        num_agg = k * k / 2
        num_agg_per_pod = k / 2
        num_edge = k * k / 2
        num_edge_per_pod = k / 2
        hosts_per_sw = k / 2
        num_sws = num_core + num_agg + num_edge
        
        # Debug
        print('Create a fattree topology with {} switches'.format(num_sws))

        # Init all switches
        cores = [self.addSwitch('core%02d' % x) for x in range(num_core)]
        pods = [([self.addSwitch('p%02da%02d' % (podnum, aggnum)) \
                for aggnum in range(num_agg_per_pod)], \
               [self.addSwitch('p%02de%02d' % (podnum, edgenum)) \
                for edgenum in range(num_edge_per_pod)]) \
               for podnum in range(num_pods)]

        # Add hosts to switches
        pods_cpy = pods[:]
        host_i = 0
        while len(pods_cpy) > 0:
            agg, edge = pods_cpy.pop(0)
            edge_cpy = edge[:]
            while len(edge_cpy) > 0:
                e = edge_cpy.pop(0)
                for i in range(hosts_per_sw):
                    host = self.addHost('h{}'.format(host_i))
                    host_i += 1
                    self.addLink(e, host)

        # Connect pods
        for pod in pods:
            agg, edge = pod
            for e in edge:
                for a in agg:
                    self.addLink(a, e)

        # Connect core and agg
        for pod in pods:
            agg, edge = pod
            for agg_i in range(num_agg_per_pod):
                a = agg[agg_i]
                for core_i in range(k / 2): # k/2 == num_core/num_agg_per_pod
                    c = cores[core_i + (agg_i * k / 2)]
                    self.addLink(a, c)


# Allows the file to be imported using `mn --custom <filename> --topo fattree`
topos = {
    'fattree': FatTreeTopo
}
