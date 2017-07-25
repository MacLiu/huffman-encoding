from collections import defaultdict
import sys
import os
from heapq import heappush, heappop
from functools import total_ordering
import pickle
USAGE_STR = "Usage: python3 huffman.py [test] [encode FILENAME] [decode FILENAME]"

# class that holds data about a particular node in the tree.
@total_ordering
class TreeNode(object):
    # each one has a (str, freq) tuple
    def __init__(self, letter, num):
        self.letter = str(letter)
        self.freq = num
        self.left = None
        self.right = None
        self.encoding = ""

# the total ordering decorator defines the other comparators if these two are defined.
    def __eq__(self, other):
         return self.freq == other.freq
    def __lt__(self, other):
        return self.freq < other.freq
    # a utility function that I used while debugging.
    def print_node(self):
        print("Node with letter {} frequency {} and encoding {}".format(self.letter, self.freq, self.encoding))

# depth-first traverse the tree, creating the binary huffman strings for each node of the tree.
def tree_dfs(node, curstr, leaves):
    """Runs a depth-first traversal of a tree, eventually populating the leaf nodes with a string to indicate
    the path from the root. For example, if a leaf was reached by branching left and then right, the string
    attached to the leaf node will be "01".
    Params:
    node: TreeNode
    curstr: String (binary)
    leaves: list of currently discovered leaf nodes.
    """
    if node is None:
        return # we shouldn't get here unless None is passed into the first call of this.
    elif node.right is None and node.left is None:
        # we found a leaf node, so the encoding is finalized.
        node.encoding = curstr
        leaves.append(node)
    else:
        if node.right is not None:
            tree_dfs(node.right, curstr + "1", leaves)
        if node.left is not None:
            tree_dfs(node.left, curstr + "0", leaves)

# a sanity check that I used while debugging to make sure that each letter has the right encoding, and there are no duplicate encodings.
def sanity(node):
    if node.left is None and node.right is None:
        print("encoding: {} for letter {} and frequency {}".format(int(node.encoding, 2), node.letter, node.freq))
    else:
        if node.left:
            sanity(node.left)
        if node.right:
            sanity(node.right)

def make_dict(data):
    """Makes a char: frequency dict from a string
    Params: data - str
    Returns: freq_dict: { char: int }
    """
    freq_dict = defaultdict(int)
    for char in data:
        freq_dict[char]+=1
    return freq_dict

def encode(file):
    """Encodes file into a smaller representation using huffman encoding.
    The encoded file is written to the filename "compressed.txt"
    Params: file - str
    """
    # open the file
    try:
        s = open(file).read()
    except IOError:
        print("Error opening file: {}".format(file))
        exit(1)

    # build dict of character: frequency
    freqs = make_dict(s)

    # build the Huffman Tree.
    # 1. Make leaf nodes, and store the letter and frequency.
    # 2. Build a tree by taking the 2 nodes with the smallest frequency, and creating a parent with the
    #    letters concatenated and the frequencies summed.
    # I used a minheap for log(N) access to the 2 nodes with the smallest frequency each time I pop from the heap.
    minheap = []
    for k, v in freqs.items():
        heappush(minheap, TreeNode(k, v))

    # ASSUMPTION: since the bitmap is of size 100 x 100 it must be separated by newlines \n,
    # so there are at least 2 distinct characters in any input file.
    parent_node = None # save the current parent node
    # This is step 2 - building the tree by creating parent nodes and keeping track of child pointers.
    while True:
        node1, node2 = heappop(minheap), heappop(minheap)
        parent_node = TreeNode(node1.letter + node2.letter, node1.freq + node2.freq)
        parent_node.left = node1
        parent_node.right = node2
        if parent_node.freq == len(s):
            break
        else:
            heappush(minheap, parent_node)

    # We know the tree is built when a parent node's frequency equals the length of the original string.
    # 3. Recursively iterate through the tree, creating encodings for all of the leaf nodes.
    # Since there is a unique path from the root to any particular node, each encoding will be unique.
    leaves = []
    tree_dfs(parent_node, "", leaves)
    encoding_to_char = {}
    for leaf in leaves:
        assert len(leaf.letter) == 1
        assert leaf.encoding not in encoding_to_char # because the encodings should have been unique.
        encoding_to_char[leaf.encoding] = leaf.letter

    # 4. Create the dictionary that maps characters in our original file to their encodings.
    char_to_encoding = {v: k for k, v in encoding_to_char.items()}

    # Representation of the encoded file. First we convert it into a binary string and then hex to save space.
    int_str = "".join([char_to_encoding[char] for char in s])
    hex_str = hex(int(int_str, 2))

    # hack to fix in the future - This way of getting the hex form does not preserve leading zeros,
    # leading to occasional inaccuracy in converting back and forth between binary and hex.
    num_zeros_to_add = 0
    bin_str = bin(int(hex_str, 16))[2:]
    while bin_str != int_str:
        bin_str  = '0' + bin_str
        num_zeros_to_add+=1

    # 5. Write out the compressed file. We will need both the string and dictionary to dencode at a later time.

    try:
        os.remove('compressed.txt')
    except OSError:
        pass

    with open('compressed.txt', 'wb') as file:
        pickle.dump((hex_str, char_to_encoding, num_zeros_to_add), file)

    # A sanity check to make sure that the mapping and strings were written correctly.
    with open('compressed.txt', 'rb') as file:
        hs, mapping, add_zero = pickle.load(file)

    assert mapping == char_to_encoding, "houston we have a problem"
    assert bin_str == int_str, "{} {}".format(bin_str, int_str)

def decode(file):
    """Given a file that has been compressed with encode(), this function decodes it back to the original
    representation. It writes the decoded file out to decoded.txt.
    Params: file - the name of the compressed file
    """
    # Read the data that we saved when we encoded
    with open(file, 'rb') as f:
        hex_str, char_to_encoding, num_zeros_to_add = pickle.load(f)

    # Convert the data so we can begin recreating the original file.
    bin_str = bin(int(hex_str, 16))[2:]
    for i in range(num_zeros_to_add):
        bin_str = '0' + bin_str
    encoding_to_char = {v : k for k, v in char_to_encoding.items()}
    # iterate through the binary string, looking up keys in the above map and adding the character when we find one.
    original = ""
    i = 0
    while i < len(bin_str):
        j = i + 1
        while j < len(bin_str) and bin_str[i:j] not in encoding_to_char.keys():
            j+=1
        if j >= len(bin_str):
            break
        original+=encoding_to_char[bin_str[i:j]]
        i = j

    #print(original)
    # Write out the decoded file.
    try:
        os.remove('decoded.txt')
    except OSError:
        pass
    with open('decoded.txt', 'w') as f:
        f.write(original)
        f.write("\n") # for convention

######### UNIT TESTS #########

def encode_decode_test():
    print("running encode() and decode() tests...")
    with open('encode-test.txt', 'w') as f:
        f.write("abracadabra\n")
    encode('encode-test.txt')
    decode('compressed.txt')
    original = open('encode-test.txt', 'r').read()
    decoded = open('decoded.txt', 'r').read()
    assert original == decoded, "TEST FAILED: Expected original file contents to exactly equal decoded file contents after encoding and decoding."
    os.remove('encode-test.txt')
    os.remove('decoded.txt')
    os.remove('compressed.txt')


def make_dict_test():
    print("running make_dict() tests...")
    """Tests the make_dict() function"""
    data = "abracadabra"
    freqs = make_dict(data)
    assert 'a' in freqs and freqs['a'] == 5, "TEST FAILED: Expected character 'a' to have a frequency of 5"
    assert 'b' in freqs and freqs['b'] == 2, "TEST FAILED: Expected 'b' to have a frequency of 2"
    assert 'r' in freqs and freqs['r'] == 2, "TEST FAILED: Expected 'r' to have a frequency of 2"
    assert 'c' in freqs and freqs['c'] == 1, "TEST FAILED: Expected 'c' to have a frequency of 2"

def tree_dfs_test():
    print("running tree_dfs tests...")
    """Tests the depth-first search tree logic."""
    root = TreeNode('r', 10)
    a = TreeNode('a', 4)
    b = TreeNode('b', 3)
    root.left = a
    root.right = b
    # leaf nodes
    c = TreeNode('c', 5)
    d = TreeNode('d', 2)
    a.left = c
    b.right = d
    # c's encoding should be 00 since we branch left and left. d's encoding should be 11 since we branch right and right.
    tree_dfs(root, "", [])
    assert c.encoding == "00", "TEST FAILED: Expected leaf node c's encoding to be 00."
    assert d.encoding == "11", "TEST FAILED: Expected leaf node d's encoding to be 11."

def run_tests():
    """Runs all of the tests."""
    make_dict_test()
    encode_decode_test()
    tree_dfs_test()
    print("All tests passed")
    exit(0)

###### MAIN FUNCTION ########

if __name__ == '__main__':
    # parse args
    if len(sys.argv) < 2:
        print(USAGE_STR)
        exit(1)

    if len(sys.argv) == 2:
        if sys.argv[1] != "test":
            print(USAGE_STR)
            exit(1)
        else:
            run_tests()

    if len(sys.argv) != 3:
        print(USAGE_STR)
        exit(1)
    else:
        if(sys.argv[1] == "encode"):
            encode(sys.argv[2]) # encode the file
        elif(sys.argv[1] == "decode"):
            decode(sys.argv[2]) # decode the file
        else:
            print(USAGE_STR)
            exit(1)
