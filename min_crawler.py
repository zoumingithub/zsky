#encoding: utf-8
from hashlib import sha1
from random import randint
from struct import unpack, pack
from socket import inet_aton, inet_ntoa, socket
import socket
from bisect import bisect_left
from threading import Timer
from time import sleep
from bencode import bencode, bdecode
import logging
import traceback
import time
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s %(filename)s %(funcName)s %(levelname)s %(message)s',
                    datefmt='%d %b %Y %H:%M:%S',
                    filename='crawler.log',
                    filemode='w')

BOOTSTRAP_NODES = [ ("router.bittorrent.com", 6881), ("dht.transmissionbt.com", 6881), ("router.utorrent.com", 6881) ]
TID_LENGTH = 4
KRPC_TIMEOUT = 10
REBORN_TIME = 5 * 60
K = 8
TOKEN_LENGTH = 2
def entropy(bytes):
    s = ""
    for i in range(bytes):
        s += chr(randint(0, 255))
    return s
# """The crawler"Camouflage"Cheng Zhengchangnode, A normal node Yes ip, port, node ID Three attributes, Because it is based on theUDPAgreement,
#  So to send information, Even if no"To make clear"To illustrate hisipAndportWhen the, You will naturally know youipAndport,
#  And vice versa. So our ownnodeYou only need to generate anode IDOn the line, The agreement saysnode IDUsesha1Generation algorithm,
#  sha1The algorithm generated value is the length is20 byte, That is20 * 8 = 160 bit, Just asDHTThe scope of protocol said: 0 To 2The160Times Square,
#  It is altogether can generate1461501637330902918203684832716283019655932542976One of the one and onlynode.
#  ok, Becausesha1Always generate20 byteThe value of the, So even if you writeSHA1(20)OrSHA1(19)OrSHA1("I am a 2B")Fine,
#  As long as the guarantee that greatly reduces the repeated probability and others.. Be careful, node IDNon base sixteen,
#  That is to say notFF5C85FE1FDB933503999F9EB2EF59E4B0F51ECALike this., Nonhash.hexdigest(). """
def random_id():
    hash = sha1()
    hash.update(entropy(20))
    return hash.digest()
def decode_nodes(nodes):
    n = []
    length = len(nodes)
    if (length % 26) != 0:
        return n
    for i in range(0, length, 26):
        nid = nodes[i:i+20]
        ip = inet_ntoa(nodes[i+20:i+24])
        port = unpack("!H", nodes[i+24:i+26])[0]
        n.append( (nid, ip, port) )
    return n

def encode_nodes(nodes):
    strings = []
    for node in nodes:
        s = "%s%s%s" % (node.nid, inet_aton(node.ip), pack("!H", node.port))
        strings.append(s)
    return "".join(strings)

def intify(hstr):
#"""This is a gadget, Put anode IDConversion to digital. Frequently used.."""
 return long(hstr.encode('hex'), 16)
#Convert16Hexadecimal, And then into digital

def timer(t, f):
    Timer(t, f).start()

class BucketFull(Exception):
    pass

class KRPC(object):
    def __init__(self):
        self.types = { "r": self.response_received, "q": self.query_received ,"e":self.error_received}
        self.actions = { "ping": self.ping_received,
                         "find_node": self.find_node_received,
                         "get_peers": self.get_peers_received,
                         "announce_peer": self.announce_peer_received,
                         "e": self.error_received,
                        }
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024*1024*2)
        self.socket.bind(("0.0.0.0", self.port))
        self.total_send = 0
        self.err_send = 0

    def response_received(self, msg, address):
        logging.info("response received from {}".format(address))
        self.find_node_handler(msg)

    def query_received(self, msg, address):
        #logging.info("query_received {} {}".format(msg,address))
        try:
            self.actions[msg["q"]](msg, address)
        except KeyError:
            pass

    def send_krpc(self, msg, address):
        #logging.info("send_krpc {} {}".format(msg,address))
        try:
            self.total_send += 1
            self.socket.sendto(bencode(msg), address)
        except OSError, exc:
            self.err_send += 1
            if self.err_send%100==0:
                logging.warning("{}/{} errors happened".format(self.err_send,self.total_send))
                logging.warning("send_krpc exception {} ".format(traceback.format_exc(exc)))
            time.sleep(0.1)



class DHTNode:
    def __init__(self,nid,ip,port):
        self.nid = nid
        self.ip = ip
        self.port = port
import Queue
import time
import threading
import traceback
class Client(KRPC):
    def __init__(self, table):
        self.table = table
        timer(KRPC_TIMEOUT, self.timeout)
        timer(REBORN_TIME, self.reborn)
        KRPC.__init__(self)
        self.node_queue = Queue.Queue(maxsize = 1000000)
    
    def process_node_queue(self):
        logging.info('start processing node queue')
        while True:
            while self.node_queue.empty():
                logging.info('node_queue is empty')
                time.sleep(5)
            node = self.node_queue.get()
            try:
                self.find_node((node.ip,node.port),node.nid)
                #logging.info('processed node {} remaining {}'.format(node,self.node_queue.qsize()))
            except Exception as e:
                logging.warning('failed to process node {}'.format(node))
    def start_query_thread(self):
        query_thread = threading.Thread(target=self.process_node_queue)
        query_thread.setDaemon(True)
        query_thread.start()
 
    def add_node(self,address,nid=None):
        self.node_queue.put(DHTNode(nid,address[0],address[1]))

    def find_node(self, address, nid=None):
        nid = self.get_neighbor(nid) if nid else self.table.nid
        tid = entropy(TID_LENGTH)
        msg = { "t": tid,
                "y": "q",
                "q": "find_node",
                "a": {"id": nid, "target": random_id()}
               }
        self.send_krpc(msg, address)

    def find_node_handler(self, msg):
        try:
            nodes = decode_nodes(msg["r"]["nodes"])
            for node in nodes:
                (nid, ip, port) = node
                if len(nid) != 20:
                    continue
                if nid == self.table.nid:
                    continue
                #logging.info("{}".format(nid.encode("hex")))
                self.add_node((ip,port),nid)
                #self.find_node( (ip, port), nid )
        except KeyError:
            pass

    def joinDHT(self):
        for address in BOOTSTRAP_NODES:
            self.add_node(address)
            #self.find_node(address)
    def timeout(self):
        if len( self.table.buckets ) <2:
            self.joinDHT()
            timer(KRPC_TIMEOUT, self.timeout)
    def reborn(self):
        self.table.nid = random_id()
        self.table.buckets = [ KBucket(0, 2**160) ]
        timer(REBORN_TIME, self.reborn)
    def start(self):
        self.joinDHT()
        while True:
            try:
                (data, address) = self.socket.recvfrom(65536)
                #logging.info("received data {} from address {}".format(data,address))
                msg = bdecode(data)
                self.types[msg["y"]](msg, address)
            except Exception, e:
                logging.warning('failed to process msg {} exception {}'.format(data,traceback.format_exc(e)))
                pass
    def get_neighbor(self, target):
        return target[:10]+random_id()[10:]
        
class Server(Client):
    def __init__(self, master, table, port):
        self.table = table
        self.master = master
        self.port = port
        Client.__init__(self, table)

    def ping_received(self, msg, address):
        try:
            nid = msg["a"]["id"]
            msg = { "t": msg["t"],
                    "y": "r",
                    "r": {"id": self.get_neighbor(nid)}
                    #"r": {"id": self.table.nid}
                }
            self.send_krpc(msg, address)
            #self.find_node(address, nid)
            self.add_node(address, nid)
            logging.info("{} {}".format(msg,address))
        except KeyError:
            pass

    def find_node_received(self, msg, address):
        try:
            target = msg["a"]["target"]
            neighbors = self.table.get_neighbors(target)
            nid = msg["a"]["id"]
            msg = { "t": msg["t"],
                    "y": "r",
                    "r": { "id": self.get_neighbor(nid),
                    "nodes": encode_nodes(neighbors) }
                }
            self.table.append(KNode(nid, *address))
            self.send_krpc(msg, address)
            #self.find_node(address, nid)
            self.add_node(address, nid)
            logging.info("{} {}".format(address,nid.encode('hex')))
        except KeyError:
            pass

    def get_peers_received(self, msg, address):
        try:
            infohash = msg["a"]["info_hash"]
            neighbors = self.table.get_neighbors(infohash)
            nid = msg["a"]["id"]
            msg = { "t": msg["t"],
                    "y": "r",
                    "r": {
                        "id": self.get_neighbor(infohash),
                        "nodes": encode_nodes(neighbors) }
                    }
            self.table.append(KNode(nid, *address))
            self.send_krpc(msg, address)
            #self.master.log(infohash)
            #self.master.log_hash(infohash, address)
            #self.find_node(address, nid)
            self.add_node(address,nid)
            logging.info('infohash %s'%infohash.encode('hex'))
        except Exception, e:
            logging.info("get_peers exception {}".format(traceback.format_exc(e)))
            pass
    def error_received(self,msg,address):
        logging.warning("error {} {}".format(msg,address))
    def announce_peer_received(self, msg, address):
        try:
            infohash = msg["a"]["info_hash"]
            nid = msg["a"]["id"]
            msg = { "t": msg["t"],
                    "y": "r",
                    "r": {"id": self.get_neighbor(infohash)}
                }
            token = msg["a"]["token"]
            self.table.append(KNode(nid, *address))
            self.send_krpc(msg, address)
            logging.info("annouce_peer {} {}".format(infohash.encode('hex'),address))
            #self.master.log(infohash)
            tid = msg["t"]
            if infohash[:TOKEN_LENGTH] == token:
                if msg["a"].has_key("implied_port ") and msg["a"]["implied_port "] != 0:
                    port = address[1]
                else:
                    port = msg["a"]["port"]
                #self.master.log_announce(infohash, (address[0], port))
                logging.info("verified infohash {} {}".format(infohash,address))
            self.add_node(address, nid)
        except KeyError:
            pass
# The class is instantiated once only.
class KTable(object):
    # HerenidIs throughnode_id()The generation function itselfnode ID. The agreement says, Each routing table has at least onebucket,
    #  Also provides the firstbucketThemin=0, max=2^160Times Square, So here is to give abucketsAttribute to storebucket, This is a list of.
    def __init__(self, nid):
        self.nid = nid
        self.buckets = [ KBucket(0, 2**160) ]
    def append(self, node):
        index = self.bucket_index(node.nid)
        try:
            bucket = self.buckets[index]
            bucket.append(node)
        except IndexError:
            return
        except BucketFull:
            if not bucket.in_range(self.nid):
                return self.split_bucket(index)
        #self.append(node)
    # Return with goalnode IDOrinfohashRecentlyKAnode.
    #  The location and targetnode IDOrinfohashWhere thebucket, If thebucuckYesKA node, Return.
    #  If not toKA node., ThebucketFrontbucketAnd thebucketBehind thebucketAdd up to, Just before returningKA node.
    # Or not toKA word, Repeat this action. Be careful not to exceed the minimum and maximum index range.
    #  In a word, No matter what you use algorithm, Try to find the nearestKA node.
    def get_neighbors(self, target):
        nodes = []
        if len(self.buckets) == 0:
            return nodes
        if len(target) != 20 :
            return nodes
        index = self.bucket_index(target)
        try:
            nodes = self.buckets[index].nodes
            min = index - 1
            max = index + 1
            while len(nodes) <K and ((min >= 0) or (max <len(self.buckets))):
                if min >= 0: nodes.extend(self.buckets[min].nodes)
                if max <len(self.buckets):
                    nodes.extend(self.buckets[max].nodes)
                min -= 1
                max += 1
            num = intify(target)
            nodes.sort(lambda a, b, num=num: cmp(num^intify(a.nid), num^intify(b.nid)))
            return nodes[:K]
        except Exception:
            pass
            #KIs a constant, K=8 except IndexError: return nodes
    def bucket_index(self, target):
                return bisect_left(self.buckets, intify(target))
            # Remove table # indexIs to be splitbucket(old bucket)The index value.
            #  Assuming that thisold bucketThemin:0, max:16. Resolution of theold bucketWords, The demarcation point is8, Then theold bucketThemaxInstead of8, minOr0.
            #  Create a newbucket, new bucketThemin=8, max=16.
            #  Then according to theold bucketIn eachnodeThenid, Have a look of yourbucketIn the range of, Loaded into the correspondingbucketLi.
            #  Each of the back,Find the mother.
            #  new bucketThe index value atold bucketBehind the, That isindex+1, The newbucketInserted into the routing table.
    def split_bucket(self, index):
        old = self.buckets[index]
        point = old.max - (old.max - old.min)/2
        new = KBucket(point, old.max)
        old.max = point
        self.buckets.insert(index + 1, new)
        for node in old.nodes[:]:
            if new.in_range(node.nid):
                new.append(node)
                old.remove(node)
        def __iter__(self):
            for bucket in self.buckets:
                yield bucket

class KBucket(object):
    __slots__ = ("min", "max", "nodes")
    # minAndmaxIs thisbucketThe scope of responsibility, For example, thebucketThemin:0, max:16Words,
    #  Then the storagenodeTheintify(nid)Values are: 0To15, The16We are not responsible for, This16Will be thebucketBehind thebucketTheminValue.
    #  nodesAttribute is a list, Storagenode. last_accessedOn behalf of the last access time, Because the protocol says,
    #  When thebucketBe responsible fornodeA request, In response to the operation; Deletenode; Add tonode; To updatenode; These operations,
    #  You must update thebucket, So set alast_accessedAttribute, This property indicates that thisbucketThe"The fresh degree". UselinuxWords, touchA.
    #  This is used to facilitate behind said refresh routing table.
    def __init__(self, min, max):
        self.min = min
        self.max = max
        self.nodes = []
    # Add tonode, ParametersnodeIsKNodeExample.
    #  If the newly insertednodeThenidThe attribute length is not equal to20, Termination.
    #  If the full, ThrowbucketA full error, Termination. Notice the code to remove table.
    #  If not full, Have a look first to the newly insertednodeIf there is already, If there is, They replace, Does not exist, Will add,
    #  Add to/Replacement, Update thebucketThe"The fresh degree".
    def append(self, node):
        if node in self:
            self.remove(node)
            self.nodes.append(node)
        else:
            if len(self) <K:
                self.nodes.append(node)
            else:
                raise BucketFull
    def remove(self, node):
        self.nodes.remove(node)
    def in_range(self, target):
        return self.min <= intify(target) <self.max
    def __len__(self):
        return len(self.nodes)
    def __contains__(self, node):
        return node in self.nodes
    def __iter__(self):
        for node in self.nodes:
            yield node
    def __lt__(self, target): return self.max <= target

class KNode(object):
# """ # nidYou're quite rightnode IDThe abbreviations, Don't takeidSo the fuzzy variable name.. __init__Method is equivalent to the otherOOPConstruction method in language,
#  In thepythonStrictly speaking not construction method, It is initialized, However, Function almost on the line.
#  """ __slots__ = ("nid", "ip", "port")
    def __init__(self, nid, ip, port):
        self.nid = nid
        self.ip = ip
        self.port = port
    def __eq__(self, other):
        return self.nid == other.nid
    #using example
'''
class Master(object):
    def __init__(self, f):
        self.f = f
    def log(self, infohash):
        logging.info("GetInfo Hash {}".format(infohash.encode("hex")+"\n"))
        self.f.write(infohash.encode("hex")+"\n")
        self.f.flush()
try:
    logging.info("Start dht crawler")
    f = open("infohash.log", "a")
    m = Master(f)
    s = Server(Master(f), KTable(random_id()), 8001)
    s.start()
except KeyboardInterrupt:
    s.socket.close()
    f.close()
'''

from crawler_log import Master,rpc_server
import threading
if __name__ == "__main__":
    # max_node_qsize bigger, bandwith bigger, spped higher
    '''
    logging.info("Crawler started")
    master = Master()
    master.setDaemon(True)
    master.start()
    logging.info("master set up")
    rpcthread = threading.Thread(target=rpc_server)
    rpcthread.setDaemon(True)
    rpcthread.start()
    '''
    print "starting DHTServer"
    master = None
    s = Server(master, KTable(random_id()), 6881)
    s.start_query_thread()
    s.start()
