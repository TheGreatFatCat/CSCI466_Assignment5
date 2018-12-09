import queue
import threading
import time

## Implements a link layer frame
# Needed to tell the network layer the type of the payload
class LinkFrame:
    ## packet encoding lengths
    type_S_length = 1

    ##@param type_S: type of packet in the frame - what higher layer should handle it
    # @param data_S: frame payload
    def __init__(self, type_S, data_S):
        self.type_S = type_S
        self.data_S = data_S

    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()

    ## convert frame to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = ''
        if self.type_S == 'MPLS':
            byte_S += 'M' # of length type_S_length
        elif self.type_S == 'Network':
            byte_S += 'N'
        else:
            raise('%s: unknown type_S option: %s' %(self, self.type_S))
        byte_S += self.data_S
        return byte_S

    ## extract a frame object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        type_S = byte_S[0 : self.type_S_length]
        if type_S == 'M':
            type_S = 'MPLS'
        elif type_S == 'N':
            type_S = 'Network'
        else:
            raise('%s: unknown type_S field: %s' % (self, type_S))
        data_S = byte_S[self.type_S_length: ]        
        return self(type_S, data_S)

    

## An abstraction of a link between router interfaces
class Link:
    
    ## creates a link between two objects by looking up and linking node interfaces.
    # @param node_1: node from which data will be transfered
    # @param node_1_intf: number of the interface on that node
    # @param node_2: node to which data will be transfered
    # @param node_2_intf: number of the interface on that node
    def __init__(self, node_1, node_1_intf, node_2, node_2_intf):
        self.node_1 = node_1
        self.node_1_intf = node_1_intf
        self.node_2 = node_2
        self.node_2_intf = node_2_intf
        print('Created link %s' % self.__str__())
        
    ## called when printing the object
    def __str__(self):
        return 'Link %s-%d - %s-%d' % (self.node_1, self.node_1_intf, self.node_2, self.node_2_intf)
        
    ##transmit a packet between interfaces in each direction
    def tx_pkt(self):
        for (node_a, node_a_intf, node_b, node_b_intf) in \
        [(self.node_1, self.node_1_intf, self.node_2, self.node_2_intf), 
         (self.node_2, self.node_2_intf, self.node_1, self.node_1_intf)]: 
            intf_a = node_a.intf_L[node_a_intf]
            intf_b = node_b.intf_L[node_b_intf]
            if intf_a.out_queue.empty():
                continue #continue if no packet to transfer
            #otherwise try transmitting the packet
            try:
                #check if the interface is free to transmit a packet
                if intf_a.next_avail_time <= time.time():
                    #transmit the packet
                    # set pkt_s to be the pkt with highest priority


                    pkt_S = intf_a.get('out')
                    # go through que and find packet with highest priority value (should be in [0] if start packet
                    if(intf_a.out_queue.qsize() is not 0):
                        for pkt in intf_a.out_queue.queue:
                            # get the biggest value
                            if (str(pkt[0]).isdigit() and pkt is not None):
                                if (str(pkt_S[0]).isdigit()):
                                    # compare the two and get larger
                                    if (int(pkt[0]) > int(pkt_S[0])):
                                        pkt_S = pkt
    # in the above code we check for highest priority from a network type packet entering the router that needs
    # to be forwarded, we then choose the highest priority

                    intf_b.put(pkt_S, 'in')
                    #update the next free time of the interface according to serialization delay
                    pkt_size = len(pkt_S)*8 #assuming each character is 8 bits
                    intf_a.next_avail_time = time.time() + pkt_size/intf_a.capacity                
                    print('%s: transmitting frame "%s" on %s %s -> %s %s \n' \
                          ' - seconds until the next available time %f\n' \
                          ' - queue size %d' \
                          % (self, pkt_S, node_a, node_a_intf, node_b, node_b_intf, intf_a.next_avail_time - time.time(), intf_a.out_queue.qsize()))

                if intf_a.out_queue.qsize() is not 0:
                    print_queue = ''
                    print_queue += '\n~~~~~~~~~~BEGIN QUEUE~~~~~~~~~~~~~~~~~\n\n'
                    # pkt is contained as a string and the size will vary due to the MLPS packet,
                    # to account for this have to grab the
                    for pkt in intf_a.out_queue.queue:
                        if(pkt[2] == '1' or pkt[2] == '0'):
                            print_queue += 'Packet with Priority '
                            print_queue += pkt[2]
                            print_queue += '\n\n'
                        elif(pkt[3] == '1' or pkt[3] == '0'):
                            print_queue += 'Packet with Priority '
                            print_queue+=pkt[3]
                            print_queue += '\n\n'
                        else:
                            print_queue += 'Packet with Priority '
                            print_queue += pkt
                            print_queue += '\n\n'
                    print_queue += '~~~~~~~~~~END QUEUE~~~~~~~~~~~~~~~~~~~\n\n'
                    print(print_queue)


                # uncomment the lines below to see waiting time until next transmission
#                 else:
#                     print('%s: waiting to transmit packet on %s %s -> %s, %s for another %f milliseconds' % (self, node_a, node_a_intf, node_b, node_b_intf, intf_a.next_avail_time - time.time()))    
            except queue.Full:
                print('%s: packet lost' % (self))
                pass
        
        
## An abstraction of the link layer
class LinkLayer:
    
    def __init__(self):
        ## list of links in the network
        self.link_L = []
        self.stop = False #for thread termination
        
    ## called when printing the object
    def __str__(self):
        return 'Network'
    
    ##add a Link to the network
    def add_link(self, link):
        self.link_L.append(link)
        
    ##transfer a packet across all links
    def transfer(self):
        for link in self.link_L:
            link.tx_pkt()
                
    ## thread target for the network to keep transmitting data across links
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #transfer one packet on all the links
            self.transfer()
            #terminate
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return
