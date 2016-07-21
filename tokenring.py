#!/usr/bin/env python3

import os
from socket import *
from struct import *
from fcntl import ioctl
from array import array
from subprocess import run

# TUN/TAP constants
TUNSETIFF = 0x400454ca
TUNSETOWNER = TUNSETIFF + 2
IFF_TUN = 0x0001
IFF_TAP = 0x0002
IFF_NO_PI = 0x1000
ETH_P_ALL = 3

class TokenRing():

    def __init__(self, phy_if="enp2s0", tr_if="tr0"):
        self.phy_if = phy_if
        self.tr_if = tr_if

    def phy(self):
        """
        Listen and forward Ethernet frames on physical interface
        """
        
        print("opening raw ethernet socket")
        #run(['ip', 'link', 'set', self.phy_if, 'promisc', 'on'])
        #run(['ip', 'link', 'set', self.phy_if, 'up'])
        self.eth = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL))
        #self.eth = socket(AF_INET, SOCK_RAW, IPPROTO_TCP)
        self.eth.bind((self.phy_if, 0))
        
        print("starting to read packets from ethernet socket")
        while True:
            packet, meta = self.eth.recvfrom(65565)
            mac = ":".join([hex(x)[2:] for x in meta[4]])
            packet_hex = "".join([hex(x)[2:] for x in packet])
            print("got packet from {}".format(self.phy_if), meta[:3], mac, "|", packet_hex[:64])
            

    def tap(self):
        """
        Listen on TAP interface for ethernet frames and forward them to physical
        interface.
        """
        
        print("opening the tun device for tap")
        self.tun = open('/dev/net/tun', 'r+b', buffering=0)
        ifr = pack('16sH', self.tr_if.encode(), IFF_TAP | IFF_NO_PI)
        ioctl(self.tun, TUNSETIFF, ifr)
        run(['ip', 'link', 'set', self.tr_if, 'up'])
        
        print("staring to read packets from tap")
        while True:
            packet = array('B', os.read(self.tun.fileno(), 65565))
            print("got packet from {}".format(self.tr_if), packet[:32])
            os.write(self.tun.fileno(), bytes(packet))


if __name__ == "__main__":
    tr = TokenRing()
    tr.phy()
    #tr.tap()
