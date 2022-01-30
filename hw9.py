from oslo.config import cfg
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.topology import event, switches
from ryu.topology.switches import get_switch, get_link, LLDPPacket
from ryu.topology import switches as topo_api
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

# Simple Match Class


class SimpleMatch(object):
    pass

# Build a Ryu App


class Hw9Switch(app_manager.RyuApp):

    def __init__(self, *args, **kwargs):
        super(Hw9Switch, self).__init__(*args, **kwargs)

        # Read arguments from the config file
        CONF = cfg.CONF
        CONF.register_opts([
            cfg.StrOpt('routing_alg', default=None, help=('TODO')),
        ])
        self.routing_alg = CONF.routing_alg

        # Not great routing algorithm dispatching
        ALG_TO_FUNC = {
            'noop': self.noop,
            'flood': self.flood,
            'broadcast_stp': self.broadcast_stp,
            'per-flow': self.per_flow,
        }

        # Configure specifics related to the routing algorithm
        self.routing_func = ALG_TO_FUNC[self.routing_alg]
        self.spanning_tree = None
        self.logger.info('routing_alg = {}'.format(CONF.routing_alg))

        # End-host MAC and Location learning.  This is necessary because the
        # MAC addresses of end-hosts aren't known until they send a packet.
        self.mac_to_swport = {}
        self.adj_list = None
        self.all_ports = {}

    def noop(self, ev):
        self.logger.info('NOOP:')
        pass

    def flood(self, ev):
        self.logger.info('Flood:')

        # Get handles
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        # Send a message to the switch with the "FLOOD" action
        actions = [ofp_parser.OFPActionOutput(ofp.OFPP_FLOOD)]
        out = ofp_parser.OFPPacketOut(
            datapath=dp, buffer_id=msg.buffer_id, in_port=msg.in_port,
            actions=actions)
        dp.send_msg(out)

    def output_packet_port(self, msg, dp, port):
        # Get handles
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        # Create an OpenFlow Output Action message for the given port
        actions = [ofp_parser.OFPActionOutput(port)]
        out = ofp_parser.OFPPacketOut(
            datapath=dp, buffer_id=ofp.OFP_NO_BUFFER, in_port=msg.in_port,
            actions=actions, data=msg.data)
        # TODO is it better to use the dp.send_packet_out() instead?
        dp.send_msg(out)

    def get_topology_data(self):
        #self.logger.info('tag1')
        switch_list = get_switch(self, None)
        #self.logger.info('tag2')
        # XXX: Useful for getting familiar with the data structures
        # self.logger.info(switch_list[0].to_dict())
        switches = [switch.dp.id for switch in switch_list]
        #self.logger.info('tag3')
        link_list = get_link(self, None)
        #self.logger.info('tag4')
        links = [(link.src.dpid, link.dst.dpid, {
                  'port': link.src.port_no}) for link in link_list]

        # Uncomment to look at the topology
        #self.logger.info('switches: {}, links: {}'.format(switches, links))

        # A Graph = (V, E) = (switch_list, link_list)
        return (switch_list, link_list)

    def build_spanning_tree(self):
        # Note: Getting the graph will be helpful for building and storing a
        # spanning tree and then broadcasting over it
        graph = self.get_topology_data()
        switch_list, edge_list = graph
        
        # ADDED
        switches = [switch.dp.id for switch in switch_list]
        # links = [(link.src.dpid, link.dst.dpid, {
        #           'port': link.src.port_no}) for link in edge_list]
        # self.logger.info('graph: {}'.format(graph))

        # BFS
        # adj_list = {i:[] for i in switches}
        # for edge in links:
        #     adj_list[edge[0]].append(edge[1:])

        if self.adj_list == None:
            self.adj_list = self.generate_graph_adj_list()


        # now adj_list is ready
        visited = [False] * (max(self.adj_list) + 1)
        queue = []
        queue.append(switches[0])
        visited[switches[0]] = True

        in_use_ports = {i:set() for i in switches}
        while queue:
            s = queue.pop(0)

            for i in self.adj_list[s]:
                if visited[i[0]] == False:
                    queue.append(i[0])
                    in_use_ports[s].add(i[1]['src_port'])
                    in_use_ports[i[0]].add(s[1]['dst_port'])
                    # in_use_ports = self.update_in_use_ports(i[0], s, in_use_ports, links)
                    visited[i[0]] = True
    
        #self.logger.info('in use ports:\n {}'.format(in_use_ports))
        # BFS 
       
        # Save the spanning tree for use with all future broadcasts
        self.spanning_tree = in_use_ports

    # def update_in_use_ports(self, src, dst, in_use_ports, links):
    #     for link in links:
    #         if (link[0], link[1]) == (src, dst):
    #             in_use_ports[src].add(link[2]['port'])
    #             break
    #     return in_use_ports
        
    def get_all_ports(self, dpid):
       
        link_list = get_link(self, None)
        links = [(link.src.dpid, link.dst.dpid, {
                  'port': link.src.port_no}) for link in link_list]
        
        all_ports = set()
        for edge in links:
            if edge[0] == dpid:
                all_ports.add(edge[2]['port'])
        
        return all_ports

    def broadcast_stp(self, ev):
        self.logger.info('Broadcast STP:')

        # Build the spanning tree if this is the first time getting here
        if self.spanning_tree == None:
            self.build_spanning_tree()

        # Get handles
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        # This will show you that the switch is connecting via OpenFlow v1.0.
        # See ryu/ryu/ofproto/ofproto_v1_0.py for more information.
        #self.logger.info(ofp, ofp.OFP_VERSION)

        # Get the ports that the packet should not be broadcast on.  This
        # includes the switch's local port, the input port, and any port that
        # is not in the spanning tree on the appropriate ports
        always_skip_ports = [msg.in_port, ofp.OFPP_LOCAL]
        #self.logger.info('always_skip_ports: {}'.format(always_skip_ports))
        #
        # HW9TODO: Add in the ports that are not in the spanning tree for this
        # switch
        #
        #self.logger.info('I\'m switch{}'.format(dp.id))
        #all_ports = self.get_all_ports(dp.id)

        if dp.id not in self.all_ports:
            self.all_ports[dp.id] = self.get_all_ports(dp.id)

        
        spanning_tree_skip_ports = self.all_ports[dp.id] - self.spanning_tree[dp.id]
        skip_port_set = set(always_skip_ports).union(spanning_tree_skip_ports)
        
        #self.logger.info('spanning tree skipped ports for switch{} is {}'.format(dp.id, spanning_tree_skip_ports))
        self.logger.info('skip port set for switch{} is {}'.format(dp.id, skip_port_set))
        # For every port not being skipped, send the packet out that port.
        # Note: it is crucially important to flood out the ports that an
        # end-host is connected to
        # Note: When the packet is buffered at the switch, buffer_id can only be
        # used once.  Because of this, we use the packet data in the PacketIn.
        # Note: However, it is not requried for switches to include the entire
        # packet as data, so even this simple function is not guaranteed to be
        # correct. OFPC could be used to ensure correctness, but that is
        # outside the scope of this homework.
        for portno, port in dp.ports.iteritems():
            assert(portno == port.port_no)  # Sanity checking
            if portno not in skip_port_set:
                self.output_packet_port(msg, dp, portno)

    def install_path(self, path, src, dst):
        # Log
        self.logger.info("Installing path")

        for dpid, in_port, out_port in path:
            sw = get_switch(self, dpid)[0]
            dp = sw.dp
            ofp = dp.ofproto
            ofp_parser = dp.ofproto_parser

            # Build the match
            match = ofp_parser.OFPMatch(in_port=in_port,
                                        dl_dst=haddr_to_bin(dst), dl_src=haddr_to_bin(src))

            # Build the actions
            actions = [ofp_parser.OFPActionOutput(out_port)]

            # Build the FlowMod
            mod = ofp_parser.OFPFlowMod(
                datapath=dp, match=match, cookie=0,
                command=ofp.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
                priority=ofp.OFP_DEFAULT_PRIORITY,
                flags=ofp.OFPFF_SEND_FLOW_REM, actions=actions)

            # Send the FlowMod
            dp.send_msg(mod)

    def find_path(self, src_dpid, src_port, dst_dpid, dst_port):
        self.logger.info("Finding path {}.p{} -> {}.p{}".format(src_dpid, src_port,
                                                                dst_dpid, dst_port))

        # HW9 Note: As an example, the below code installs all "trivial" paths
        # where the source and destination share the same switch. You need to
        # write an algorithm that searches the topology to find a path.
        if src_dpid == dst_dpid:
            path = [(src_dpid, src_port, dst_port)]

        else:
            if self.adj_list == None:
                self.adj_list = self.generate_graph_adj_list()

            # for key, val in self.adj_list.items():
            #     self.logger.info('{} : {}'.format(key, val))

            parents = {i:None for i in self.adj_list}
            queue = [src_dpid]
            while queue:
                u = queue.pop(0)

                if u == dst_dpid:
                    break

                for v, ports in self.adj_list[u]:
                    if parents[v] == None:
                        queue.append(v)
                        parents[v] = (u, ports)

            path = self.generate_path_steps(src_dpid, src_port, dst_dpid, dst_port, parents)
            # self.logger.info('Path found: {}'.format(path))

        return path

    def generate_graph_adj_list(self):
        switch_list, edge_list = self.get_topology_data()
        
        switches = [switch.dp.id for switch in switch_list]
        links = [(link.src.dpid, link.dst.dpid, {
                  'src_port': link.src.port_no,
                  'dst_port': link.dst.port_no}) for link in edge_list]
                
        adj_list = {i:[] for i in switches}
        for link in links:
            adj_list[link[0]].append(link[1:])
        
        return adj_list

    def generate_path_steps(self, src, src_port, dst, dst_port, parents):
        path = []
        child = dst
        parent_port_out = dst_port
        
        while child != src:
            parent, ports = parents[child]
            child_port_in = ports['dst_port']
            path.append((child, child_port_in, parent_port_out))
            parent_port_out = ports['src_port']
            child = parent

        path.append((src, src_port, parent_port_out))
        path.reverse()
        return path
        
    def per_flow(self, ev):
        self.logger.info('Per-Flow:')

        # Get Handles
        msg = ev.msg
        dp = msg.datapath
        ofproto = dp.ofproto

        # Parse the packet to get the Ethernet dst and src
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        dst = eth.dst
        src = eth.src

        # Learn MAC Addresses because MAC addresses of end-hosts are unknown
        # until the end-host sends a packet
        src_dpid = dp.id
        src_port = msg.in_port
        # self.logger.info('mac2port: {}'.format(self.mac_to_swport))
        if src not in self.mac_to_swport:
            self.mac_to_swport[src] = (src_dpid, src_port)

        # DEBUG
        # self.logger.info("packet in %s %s %s %s",
        #                  src_dpid, src, dst, msg.in_port)

        # Fall back on STP Broadcast if we have not seen the destination yet
        if dst not in self.mac_to_swport:
            return self.broadcast_stp(ev)

        # Find the destination
        dst_dpid, dst_port = self.mac_to_swport[dst]

        # Build and install the forward path
        # Path -> [(SW DPID, Input Port, Output Port), ...]
        fwd_path = self.find_path(src_dpid, src_port, dst_dpid, dst_port)
        if fwd_path != None:
            self.install_path(fwd_path, src, dst)
        else:
            self.logger.warn("Unable to find path! Is the topology connected?")

        # Build and install the reverse path as well to avoid triggering
        # extra PacketIn messages
        rev_path = self.find_path(dst_dpid, dst_port, src_dpid, src_port)
        if rev_path != None:
            self.install_path(rev_path, dst, src)
        else:
            self.logger.warn("Unable to find path! Is the topology connected?")

        # Output the packet directly to the destination because it will not use
        # the newly installed rule
        self.output_packet_port(msg, get_switch(
            self, dst_dpid)[0].dp, dst_port)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        # Get the message
        msg = ev.msg

        # Ignore LLDPPackets used for topology discovery
        try:
            src_dpid, src_port_no = LLDPPacket.lldp_parse(msg.data)
            return
        except LLDPPacket.LLDPUnknownFormat as e:
            pass

        # Dispatch to the different routing algorithms
        self.routing_func(ev)
