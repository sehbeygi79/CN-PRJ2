# Homework 9: Custom Routing Algorithms in an SDN Controller

##### This assignment is **optional** and is due at 11:59 pm on Friday May 1st.**

##### **You can access the homework starter code [here][hw9classroom].**

In this homework, you will implement a few different routing algorithms
within an SDN Controller.  To do this, you will use the [OpenFlow
Protocol][openflow], the [Ryu SDN Framework][ryu], and the [Mininet
Network Emulator][mininet].

The rest of this assignment description is organized into the following
sections:
1. [Environment Setup](#env)
2. [OpenFlow Overview](#openflow)
3. [Ryu SDN Controller Overview](#ryu)
4. [Skeleton Code](#skeleton)
5. [Program Requirements (Programming Tasks)](#reqs)
6. [Testing](#testing)
7. [Grading](#grading)

## <a name="env"></a> Environmental Setup

To write a simple SDN Controller, we are going to the using the [Ryu SDN
Controller][ryu].  To simplify things, it is recommend that you use a
[pre-built VM][vm] that already has both Ryu and Mininet installed.
However, it is also possible to install both of these programs locally,
if you would like.  The rest of this section describes both approaches.
However, the provided code is written for the versions of Ryu and
Mininet that are installed on the VM.  **If you use more recent versions
of Ryu or Mininet that you install yourself, you may have to forward
port the provided code.**

### Installing Either a VM or Packages

#### VM for Ryu/Mininet

Ryu provides [pre-built VMs][vm] that make it simple to get started.  If
you have never used a VM before, it is recommended that you install and
use the [VirtualBox](https://www.virtualbox.org/wiki/Downloads) Virtual
Machine Monitor (VMM/Hypervisor).

Note: The following two pages from the mininet wiki may also be helpful:
- [Set-up-Virtual-Machine](https://github.com/mininet/openflow-tutorial/wiki/Set-up-Virtual-Machine)
- [VirtualBox-specific-Instructions](https://github.com/mininet/openflow-tutorial/wiki/VirtualBox-specific-Instructions)

After installing VirtualBox, you will need to download the Ryu VM for
the OpenFlow Tutorial.  It is recommended that you download
[OpenFlow_Tutorial_Ryu3.6.ova](https://sourceforge.net/projects/ryu/files/vmimages/OpenFlowTutorial/OpenFlow_Tutorial_Ryu3.6.ova/download).
After downloading the `ova` file, you will need to import it into
VirtualBox and start it:
- `File` -> `Import Appliance...` -> Select `File:` -> `Next` -> Change settings if you want ->
  `Import`
- From there, you should select the VM and press "Start" to run the VM.

Once the VM is running, you can use its terminal directly and do not
need any more environmental configuration.  However, it is *highly
recommended* to set up the VM's network configuration so that you can
SSH into the VM.  This is because having two or more terminals open and
using X11 forwarding with Mininet is helpful.   To do this, you need to
also set up port forwarding for the VM.  
- Right-click the VM -> "Settings" -> Network -> Advanced -> Port
  Forwarding -> Add new rule
    - Name: SSH, Protocol: TCP, Host IP: 127.0.0.1, Host Port 2222,
      Guest IP: "" (Blank), Guest Port: 22.
- `ssh -X -p 2222 ryu@127.0.0.1` will now enable you to SSH into the guest.

#### Installing packages Locally

##### Installing Ryu Locally

You can install Ryu locally with:
```
pip install ryu
```

##### Installing Mininet Locally

If you are on a Debian/Ubuntu based Linux distro, installing Mininet is
easy:
```
sudo apt install mininet
```

For other platforms, see the [Mininet install
instructions](http://mininet.org/download/) from the official Mininet
website.

### Verifying the Installation and Learning Mininet

To verify that everything is working, you will be following the [Ryu
Tutorial](https://github.com/osrg/ryu/wiki/OpenFlow_Tutorial).  For
reference, some key commands will be included below.  Also, note that
the [Ryu Tutorial](https://github.com/osrg/ryu/wiki/OpenFlow_Tutorial)
is based on a much more in-depth [Mininet
Tutorial](https://github.com/mininet/openflow-tutorial/wiki/Learn-Development-Tools).
Additionally, this tutorial is based on another OpenFlow tutorial
(Archived
[here](http://140.120.7.21/LinuxRef/OpenFlow/OpenFlow_Tutorial.html) and
[here](https://homepages.dcc.ufmg.br/~mmvieira/cc/OpenFlow%20Tutorial%20-%20OpenFlow%20Wiki.htm))
created by Brandon Heller and Yiannis Yiakoumis and beta-tested by Bob
Lantz, KK Yap and Masayoshi Kobayashi. 

Kill any old controllers

    sudo killall controller

Note that you will likely want to have two open SSH connections to your
VM so that you can run Mininet in a separate window (tab) than starting
your controller application.  To quit Mininet, run:

    mininet> exit

Run Mininet as follows to clean any old instances of Mininet that may be
running and to start a simple topology with a single switch and three
hosts:

    sudo mn -c # Cleanup (remove old topologies)
    sudo mn --topo single,3 --mac --switch ovsk --controller remote

Note that your controller will be run on localhost:6633 

Now, run Ryu's example `simple_switch.py` program:

    cd ~/ryu/
    PYTHONPATH=. ./bin/ryu-manager --verbose ryu/app/simple_switch.py

Finally, verify that everything is working as expected by running the
following command within Mininet:

    mininet> pingall

Further, you can test the throughput of the virtual switch used with
Mininet by running the following:

    mininet> iperf

## <a name="openflow"></a> OpenFlow Overview

This homework is intended to introduce you to both high-level SDN
concepts as well as give you low-level experience with
[OpenFlow][openflow], an open SDN protocol.

Although this homework hides many aspects of the OpenFlow protocol from
you, it will probably be helpful to familiarize yourself with key
concepts related to OpenFlow before starting.  The following links can
help you familiarize yourself with OpenFlow.
- [Slides for an OpenFlow Tutorial](https://www.slideshare.net/openflow/openflow-tutorial)
- [The OpenFlow v1.0
  Specification](https://www.opennetworking.org/wp-content/uploads/2013/04/openflow-spec-v1.0.0.pdf)
  (Although this is an older version of the OpenFlow specification, this
  version is more simple than later versions, so it may be easier to
  understand.)
- [An SDNHub tutorial on OpenFlow v1.3](http://sdnhub.org/tutorials/openflow-1-3/)


Because you are required to implement a routing algorithm that is run in
a controller in response to `PacketIn` messages and to broadcast packets
on a spanning tree with `PacketOut` messages, you should pay particular
attention to the `PacketIn` and `PacketOut` concepts.  You should also
pay attention to `FlowMod` messages, matching, and actions.

## <a name="ryu"></a> Ryu SDN Controller Overview

This homework also hides many aspects of the Ryu controller from you.
However, it is reasonable that you may want to become more familiar with
the Ryu SDN Controller, especially if you are stuck debugging your
application.  The rest of this section gives an introduction to writing
applications in Ryu, the overall design of Ryu, and the automatically
generated function level documentation of Ryu.

For an introduction to Ryu, the following may be helpful:
- [Slides for an Introduction to Ryu](https://www.slideshare.net/ssusera21600/ryu-introduction)
- [Writing your first Ryu
  Application](https://ryu.readthedocs.io/en/latest/writing_ryu_app.html)
- [An SDN Hub Tutorial on the Ryu Controller](http://sdnhub.org/tutorials/ryu/)

For in-depth documentation on the design and use of Ryu, See the "Ryu
SDN Framework" book (Ryubook):
- [Ryubook 1.0 HTML](https://osrg.github.io/ryu-book/en/html/)
- [Ryubook PDF](https://osrg.github.io/ryu-book/en/Ryubook.pdf)

Finally, the automatically generated documentation for v3.6 of Ryu can
be found in the `ryu_documentation_release3_6.pdf` file in your starter
code.
(The documentation for the most up to date version of Ryu can be found
[here](https://ryu.readthedocs.io/en/latest/ryu_app_api.html))


## <a name="skeleton"></a> Skeleton Code

You should start this assignment by checking out your github classroom
repository into the home directory of the Ryu VM (`/home/ryu/`).  In
this repository, there is provided code in `hw9.py`, and this file
contains a complete Ryu application that implements the functionality of
an Ethernet switch.  However, all packets in this application flow
through the controller, which is inefficient, and this program fails to
correctly deliver packets on networks with cycles because it uses naive
broadcasting.  Your [assignment](#reqs) is to then implement additional
routing algorithms on top of this skeleton code.  Importantly, all of
the sections that require additional student code are marked by
`#HW9TODO`.  To help you with this task, this section introduces you to
the key functions in the `hw9.py` file:

- ``__init__``: In addition to initializing variables, this function
  reads data from a Ryu configuration file to configure which of a few
  routing algorithms will be used in response to a `PacketIn` message.
  There are four different routing algorithms in total, and all
  algorithms already have a configuration file created:
    - `noop`: "noop" (`conf/noop.conf`) is a NOOP (no-op) routing
      algorithm.  When this is used, no packets should flow through your
      network.
    - `flood`: "flood" (`conf/flood.conf`) is a routing algorithm that
      uses the controller to flood every packet recieved from a PacketIn
      message all of the ports of the switch that caused the PacketIn
      message.
    - `broadcast_stp`: "broadcast\_stp" (`conf/brodcast_stp.conf`) is a
      routing algorithm that uses the contorller to broadcast the packet
      out only the ports of the switch that are part of a spanning tree
      computed by the controller.  **Finishing writing this routing
      algorithm is part of this assignment.**
    - `per-flow`: "per-flow" (`conf/per_flow.conf`) is a routing
      algorithm that uses the controller to install a route for every
      source MAC/destination MAC (SMAC/DMAC) pair that try to
      communicate, falling back on broadcasting using the
      "broadcast\_stp" algorithm when it has yet to learn the
      destination for a packet. **Finishing writing this routing
      algorithm is part of this assignment.**
- `flood`: This function implements the flooding routing algorithm,
  using OpenFlow's `OFPP_FLOOD` action.  This function is already
  correctly implemented and is included as an example routing function.
- `output_packet_port`: This function will send a packet from the
  controller application to a given switch for outputting out a given
  port with the `PacketOut` message.
- `get_topology_data`: This function will fetch the full network
  topology from another Ryu application that you must ensure is running
  as well as your application (This assignments provides a script
  `run_hw9.sh` that already does this for you).  This function returns a
  graph G = (V, E) = (switch\_list, link\_list). You can uncomment
  debugging information in this function if you are confused by what
  objects exactly are returned.
- `build_spanning_tree`: This function gets the current topology, and
  builds a spanning tree that will be used to determine which ports
  packets will be broadcast out.  **Finishing writing this function is
  part of this assignment.**
- `broadcast_stp`: This function implements the "broadcast\_stp" routing
  algorithm.  **Finishing writing this function is part of this
  assignment.**
- `install_path`: Given a source MAC (`src`), a destination MAC (`dst`),
  and a path (`path`) that is a list of (DPID, input\_port,
  output\_port) tuples, build and send the appropriate `FlowMod`
  messages to every switch in the path.  This function is already
  implemented for you.
- `find_path`: Find a path given a source switch DPID and input port and
  a destination switch DPID and an output port.  As part of implementing
  this function, you are not allowed to use *any* outside libraries or
  additional imports.  **Finishing writing this function is part of this
  assignment.**
- `per_flow`: This function implements the "per-flow" routing algorithm.
  **Finishing writing this function is part of this assignment.**


## <a name="reqs"></a> Program Requirements (Programming Tasks)

The tasks to be completed as part of this assignment amount to finishing
implementing both the `broadcast_stp` and `per-flow` routing algorithms.
To help make things as clear as possible, the skeleton code marks
incomplete or temporary code that needs to be replaced.  The rest of
this section describes how these different routing algorithms should
behave and how you should approach completing the implementation of
these different algorithms.

#### "broadcast\_stp" Routing Algorithm

This algorithm is intended to solve a problem with using the `flood`
routing algorithm on a topology that contains cycles.  In particular,
the `flood` algorithm is not able to send pings on a network that has
cycles because broadcast storms will overwhelm the controller.  The
purpose of this algorithm is to, using full knowledge of the network
topology from another running Ryu application
(`ryu/ryu/topology/switches.py`), build a spanning tree that will be
used to determine how packets are broadcast at every switch.

In this routing algorithm, every packet that is received from a
`PacketIn` message is to be then forwarded out every single port of the
switch that generated the message that is a member of the spanning tree.
This includes ports that are connected to hosts, and this includes ports
connected to other switches that are a part of the spanning tree that is
computed the first time this routing algorithm is run.

The primary difficulty in completing this routing algorithm is in
searching the topology and creating a spanning tree.  For this, you
should implement a common spanning tree algorithm like [Breadth-first
search (BFS)](https://en.wikipedia.org/wiki/Breadth-first_search) or
[Depth-first search](https://en.wikipedia.org/wiki/Depth-first_search).

This routing algorithm is only practical for bootstrapping connectivity
in an SDN network.  This is because every packet in the entire network
flow though the controller via `PacketIn` messages.  In an operational
SDN network, it is necessary to install rules in flow tables for
performance.

#### `per-flow` Routing Algorithm

The `per-flow` routing algorithm learns the locations of end-hosts in
the network, computes routes between them, and installs rules in flow
tables in the appropriate switches along the path so as to ensure that
packets can flow in the network between the source and destination
**without the intervention of the controller**.  Because the skeleton
code for this algorithm is designed to fall back on the `broadcast_stp`
algorithm, it is easy to incorrectly conclude that this algorithm is
implemented correctly.  For this routing algorithm to be correctly
implemented, you should be able to run `pingall` and `iperf` without any
packets being forwarded to the controller.

In this algorithm, you must find a path from the source to destination.
For this, it is recommend that you implement with your own code an
algorithm like [Dijkstra's Shortest Path First
algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm).


## <a name="testing"></a> Testing

The homework template contains scripts and configuration files that are
intended to help with running and testing your Ryu application.  In
order to enable topology discovery, it is necessary to always run the
`switches.py` (ryu/ryu/topology/switches.py) Ryu application along with
the `hw3.py` Ryu application.  The `run_hw9.sh` script will take care of
invoking this for you.  However, if you want to invoke your Ryu program
without this script, or you are using a more recent version of Ryu, then
you will need to sure that you are also running the appropriate topology
discovery application.

The rest of this section contains useful information for testing your
Ryu application.

Run the skeleton code with the following command:

    sudo bash -c "/home/ryu/cs450-net-hw9-*/run_hw9.sh /home/ryu/cs450-net-hw9-*/conf/flood.conf"

    sudo bash -c "/home/ryu/cs450-net-hw9-*/run_hw9.sh /home/ryu/cs450-net-hw9-*/conf/broadcast_stp.conf"

    sudo bash -c "/home/ryu/cs450-net-hw9-*/run_hw9.sh /home/ryu/cs450-net-hw9-*/conf/per-flow.conf"


Topology is an important part of configuring Mininet.  For this
assignment, you should use the `single` and `linear` topologies that are
built into Mininet.  The template for this assignment also contains the
`mesh` (`topos/mesh.py`) and `fattree` (`topos/fattree.py`) topologies.
The following are useful commands for running Mininet with these
different topologies:

    sudo mn --topo single,4 --mac --switch ovsk --controller remote

    sudo mn --topo linear,4 --mac --switch ovsk --controller remote

    sudo bash -c "mn  --custom /home/ryu/cs450-net-hw9-*/topos/fattree.py --topo fattree,4 --mac --switch ovsk --controller remote"

    sudo bash -c "mn  --custom /home/ryu/cs450-net-hw9-*/topos/mesh.py --topo mesh,5 --mac --switch ovsk --controller remote"

All of the routing algorithms that you create should work correctly on
all of the above topologies.  However, none of the included algorithms
currently work correctly on all topologies.  This is because packet
flooding will overwhelm the controller, and no routes (`FlowMod`s) are
installed.  

Notes:
- Mininet will connect with OpenFlow v1.0.  
- Because topology auto-discovery is enabled, the `switches.py` Ryu
  program will automatically send LLDP packets in the network, so the
  controller will always be receiving some packets in any topology with
  more than one switch.
- The `-v debug` flag is very helpful for debugging Mininet topologies.
- In the Mininet terminal, using `xterm h1` through `xterm h<n>` is
  useful for gaining more control over the endhosts in your emulated
  network.

## <a name="grading"></a> Grading

For this homework we will be using an autograder to grade your work, and
`./tester.py` is the autograder that we will use.  Like before, you can
create as many backups as you like using `git commit -a` and `git push`. 

There is a total of **100 points** on this assignment, with extra bonus
points being awarded for exceptional new test cases.  Additionally,
there are extra credit points available for finding bugs in any part of
this assignment infrastructure.

The points for this assignment are broken down as follows:
* **35 Points**: Correctness of the `broadcast_stp` routing algorithm.
* **35 Points** Correctness of the `per-flow` routing algorithm.
* **10 Points**: Code style for routing algorithms
* **20 Points**: Questions in `WRITEUP.md`

There are two questions in the WRITEUP.  The first is to describe the
algorithm you used to compute a spanning tree.  The second is to
describe the algorithm you used to compute per-flow paths.

## Submission
You will be making the submission for this homework through github.

The files which will be submitted through github:
* `hw9.py`: This file will contain both of your routing algorithms
* `WRITEUP.md`: This file will contain a brief description of your
  implementation

To submit your work, run `git commit -a` and `git push`. Like previously, you are allowed to make multiple submissions 
but you have limited attempts with the grader.


[hw9classroom]: TODO
[piazza]: {{ site.discussion }}
[openflow]: https://www.opennetworking.org/software-defined-standards/specifications/
[ryu]: https://osrg.github.io/ryu/
[mininet]: http://mininet.org/
