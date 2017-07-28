### Huffman Encoding in Python

Huffman encoding is a popular lossless compression algorithm. It works by constructing a prefix tree based on the occurences of characters in the text. The cool thing about huffman encoding is that characters that occur very frequently can be represented with fewer bits. Once the tree is constructed, it can be traversed, assigning encodings to characters. The final compressed result is composed of two things: the compressed text (created by subtituting the bits for characters) and a dict mapping the characters to bits. With this, decoding is just a matter of iterating through the compressed bit-representation and looking up the corresponding character. 

### Usage

Compress: `python3 huffman.py encode data.txt` writes the compressed file to `compressed.txt`
Decompress: `python3 huffman.py decode compressed.txt` writes the decoded file to `decoded.txt`
`diff decoded.txt data.txt` should not output anything. 

