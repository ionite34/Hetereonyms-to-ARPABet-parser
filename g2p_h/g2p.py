# -*- coding: utf-8 -*-
# /usr/bin/python
'''
Based on work by kyubyong park(kbpark.linguist@gmail.com)
and Jongseok Kim(https://github.com/ozmig77)
Modified for use with hetereonyms by ionite34
https://github.com/ionite34/g2pH
'''

import string
from nltk import pos_tag
from nltk.corpus import cmudict
import nltk
from nltk.tokenize import TweetTokenizer
word_tokenize = TweetTokenizer().tokenize
import numpy as np
import codecs
import re
import os
import unicodedata
from builtins import str as unicode

try:
    nltk.data.find('taggers/averaged_perceptron_tagger.zip')
except LookupError:
    nltk.download('averaged_perceptron_tagger')
try:
    nltk.data.find('corpora/cmudict.zip')
except LookupError:
    nltk.download('cmudict')

dirname = os.path.dirname(__file__)

def construct_homograph_dictionary():
    f = os.path.join(dirname,'heteronyms.en')
    homograph2features = dict()
    for line in codecs.open(f, 'r', 'utf8').read().splitlines():
        if line.startswith("#"): continue # comment
        headword, pron1, pron2, pos1 = line.strip().split("|")
        homograph2features[headword.lower()] = (pron1.split(), pron2.split(), pos1)
    return homograph2features

# def segment(text):
#     '''
#     Splits text into `tokens`.
#     :param text: A string.
#     :return: A list of tokens (string).
#     '''
#     print(text)
#     text = re.sub('([.,?!]( |$))', r' \1', text)
#     print(text)
#     return text.split()

class G2p(object):
    def __init__(self):
        super().__init__()
        self.graphemes = ["<pad>", "<unk>", "</s>"] + list("abcdefghijklmnopqrstuvwxyz")
        self.phonemes = ["<pad>", "<unk>", "<s>", "</s>"] + ['AA0', 'AA1', 'AA2', 'AE0', 'AE1', 'AE2', 'AH0', 'AH1', 'AH2', 'AO0',
                                                             'AO1', 'AO2', 'AW0', 'AW1', 'AW2', 'AY0', 'AY1', 'AY2', 'B', 'CH', 'D', 'DH',
                                                             'EH0', 'EH1', 'EH2', 'ER0', 'ER1', 'ER2', 'EY0', 'EY1',
                                                             'EY2', 'F', 'G', 'HH',
                                                             'IH0', 'IH1', 'IH2', 'IY0', 'IY1', 'IY2', 'JH', 'K', 'L',
                                                             'M', 'N', 'NG', 'OW0', 'OW1',
                                                             'OW2', 'OY0', 'OY1', 'OY2', 'P', 'R', 'S', 'SH', 'T', 'TH',
                                                             'UH0', 'UH1', 'UH2', 'UW',
                                                             'UW0', 'UW1', 'UW2', 'V', 'W', 'Y', 'Z', 'ZH']
        self.g2idx = {g: idx for idx, g in enumerate(self.graphemes)}
        self.idx2g = {idx: g for idx, g in enumerate(self.graphemes)}

        self.p2idx = {p: idx for idx, p in enumerate(self.phonemes)}
        self.idx2p = {idx: p for idx, p in enumerate(self.phonemes)}

        self.cmu = cmudict.dict()
        self.load_variables()
        self.homograph2features = construct_homograph_dictionary()

    def load_variables(self):
        self.variables = np.load(os.path.join(dirname,'checkpoint20.npz'))
        self.enc_emb = self.variables["enc_emb"]  # (29, 64). (len(graphemes), emb)
        self.enc_w_ih = self.variables["enc_w_ih"]  # (3*128, 64)
        self.enc_w_hh = self.variables["enc_w_hh"]  # (3*128, 128)
        self.enc_b_ih = self.variables["enc_b_ih"]  # (3*128,)
        self.enc_b_hh = self.variables["enc_b_hh"]  # (3*128,)

        self.dec_emb = self.variables["dec_emb"]  # (74, 64). (len(phonemes), emb)
        self.dec_w_ih = self.variables["dec_w_ih"]  # (3*128, 64)
        self.dec_w_hh = self.variables["dec_w_hh"]  # (3*128, 128)
        self.dec_b_ih = self.variables["dec_b_ih"]  # (3*128,)
        self.dec_b_hh = self.variables["dec_b_hh"]  # (3*128,)
        self.fc_w = self.variables["fc_w"]  # (74, 128)
        self.fc_b = self.variables["fc_b"]  # (74,)

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def grucell(self, x, h, w_ih, w_hh, b_ih, b_hh):
        rzn_ih = np.matmul(x, w_ih.T) + b_ih
        rzn_hh = np.matmul(h, w_hh.T) + b_hh

        rz_ih, n_ih = rzn_ih[:, :rzn_ih.shape[-1] * 2 // 3], rzn_ih[:, rzn_ih.shape[-1] * 2 // 3:]
        rz_hh, n_hh = rzn_hh[:, :rzn_hh.shape[-1] * 2 // 3], rzn_hh[:, rzn_hh.shape[-1] * 2 // 3:]

        rz = self.sigmoid(rz_ih + rz_hh)
        r, z = np.split(rz, 2, -1)

        n = np.tanh(n_ih + r * n_hh)
        h = (1 - z) * n + z * h

        return h

    def gru(self, x, steps, w_ih, w_hh, b_ih, b_hh, h0=None):
        if h0 is None:
            h0 = np.zeros((x.shape[0], w_hh.shape[1]), np.float32)
        h = h0  # initial hidden state
        outputs = np.zeros((x.shape[0], steps, w_hh.shape[1]), np.float32)
        for t in range(steps):
            h = self.grucell(x[:, t, :], h, w_ih, w_hh, b_ih, b_hh)  # (b, h)
            outputs[:, t, ::] = h
        return outputs

    def encode(self, word):
        chars = list(word) + ["</s>"]
        x = [self.g2idx.get(char, self.g2idx["<unk>"]) for char in chars]
        x = np.take(self.enc_emb, np.expand_dims(x, 0), axis=0)

        return x

    def predict(self, word):
        # encoder
        enc = self.encode(word)
        enc = self.gru(enc, len(word) + 1, self.enc_w_ih, self.enc_w_hh,
                       self.enc_b_ih, self.enc_b_hh, h0=np.zeros((1, self.enc_w_hh.shape[-1]), np.float32))
        last_hidden = enc[:, -1, :]

        # decoder
        dec = np.take(self.dec_emb, [2], axis=0)  # 2: <s>
        h = last_hidden

        preds = []
        for i in range(20):
            h = self.grucell(dec, h, self.dec_w_ih, self.dec_w_hh, self.dec_b_ih, self.dec_b_hh)  # (b, h)
            logits = np.matmul(h, self.fc_w.T) + self.fc_b
            pred = logits.argmax()
            if pred == 3: break  # 3: </s>
            preds.append(pred)
            dec = np.take(self.dec_emb, [pred], axis=0)

        preds = [self.idx2p.get(idx, "<unk>") for idx in preds]
        return preds
    
    # Checks if a string line contains a heteronym or not
    def contains_het(self, line):
        # preprocessing for encoding
        text = unicode(line)
        # Strip accents
        text = ''.join(char for char in unicodedata.normalize('NFD', text)
                       if unicodedata.category(char) != 'Mn')
        # Convert to lower case
        text = text.lower()
        # Remove all puntuaction
        text = re.sub("[^ a-z'.,?!\-]", "", text)
        # tokenization
        words = word_tokenize(text)
        # Check match
        for word in words:
            if word in self.homograph2features:
                return True
        # No match
        return False

    # Returns a list of heteronyms and their replacement phonemes, in order
    def het_replace(self, line, gen_unknown=False, get_cmu=False):
        # preprocessing
        text = unicode(line)
        #text = normalize_numbers(text)
        text = ''.join(char for char in unicodedata.normalize('NFD', text)
                       if unicodedata.category(char) != 'Mn')  # Strip accents
        text = text.lower()
        text = re.sub("[^ a-z'.,?!\-]", "", text)

        # tokenization
        words = word_tokenize(text)
        tokens = pos_tag(words)  # tuples of (word, tag)

        # steps
        replacements = []
        originals = []
        typeWord = []
        for word, pos in tokens:
            if word in self.homograph2features:
                # Heteronym match, record original to list
                originals.append(word)
                # Get homograph features
                type1, type2, pos1 = self.homograph2features[word]
                typeWord.append(pos)
                # Run special case for read
                if word == 'read':
                    # Verb, past tense
                    if pos.startswith('VBD'):
                        het_as_phoneme = type2
                    # Verb, past participle
                    elif pos.startswith('VBN'):
                        het_as_phoneme = type2
                    elif pos.startswith('VBP'):
                        het_as_phoneme = type2
                    else:
                        het_as_phoneme = type1
                else:
                    # Depending on pos, choose type of replacement pronunciation
                    if pos.startswith(pos1):
                        het_as_phoneme = type1
                    else:
                        het_as_phoneme = type2
                # Add to replacements list
                phoneme = []
                phoneme.extend(het_as_phoneme)
                replacements.append(phoneme)
            elif get_cmu and word in self.cmu:
                # CMU dictionary match, record original to list
                originals.append(word)
                # Get CMU pronunciation
                phoneme = self.cmu[word][0]
                # Add to replacements list
                replacements.append(phoneme)
            elif gen_unknown and (word not in self.cmu) and not word.isnumeric():
                # Skip if the word is a single length punctuation
                if len(word) == 1 and not word.isalpha():
                    continue
                # Skip if the entire word has no letters, check with regex
                if not re.search('[a-zA-Z]', word):
                    continue
                # Unknown word, record original to list
                originals.append(word)
                # Generate unknown phoneme
                phoneme = self.predict(word)
                # Add to replacements list
                replacements.append(phoneme)

        # Form replacements and originals into a list of tuples
        # return replacements[:-1]
        return (originals, replacements, typeWord)

    # Returns a list of heteronyms by prediction from line
    def predict_text_line(self, line, get_cmu=False):
        # preprocessing
        text = unicode(line)
        #text = normalize_numbers(text)
        text = ''.join(char for char in unicodedata.normalize('NFD', text)
                       if unicodedata.category(char) != 'Mn')  # Strip accents
        text = text.lower()
        text = re.sub("[^ a-z'.,?!\-]", "", text)

        # tokenization
        words = word_tokenize(text)
        tokens = pos_tag(words)  # tuples of (word, tag)

        # steps
        replacements = []
        originals = []
        for word, pos in tokens:
            if get_cmu and word in self.cmu:
                # CMU dictionary match, record original to list
                originals.append(word)
                # Get CMU pronunciation
                phoneme = self.cmu[word][0]
                # Add to replacements list
                replacements.append(phoneme)
            else:
                # Skip if the word is a single length punctuation
                if len(word) == 1 and not word.isalpha():
                    continue
                # Skip if the entire word consists of puntuation
                if word in string.punctuation:
                    continue
                # Unknown word, record original to list
                originals.append(word)
                # Generate unknown phoneme
                phoneme = self.predict(word)
                # Add to replacements list
                replacements.append(phoneme)

        # Form replacements and originals into a list of tuples
        # return replacements[:-1]
        return (originals, replacements)

    def __call__(self, text):
        # preprocessing
        text = unicode(text)
        #text = normalize_numbers(text)
        text = ''.join(char for char in unicodedata.normalize('NFD', text)
                       if unicodedata.category(char) != 'Mn')  # Strip accents
        text = text.lower()
        text = re.sub("[^ a-z'.,?!\-]", "", text)
        text = text.replace("i.e.", "that is")
        text = text.replace("e.g.", "for example")

        # tokenization
        words = word_tokenize(text)
        tokens = pos_tag(words)  # tuples of (word, tag)

        # steps
        prons = []
        for word, pos in tokens:
            if re.search("[a-z]", word) is None:
                pron = [word]
            elif word in self.homograph2features:  # Check homograph
                pron1, pron2, pos1 = self.homograph2features[word]
                if pos.startswith(pos1):
                    pron = pron1
                else:
                    pron = pron2
            elif word in self.cmu:  # lookup CMU dict
                pron = self.cmu[word][0]
                #pron = word
            else:  # predict for oov
                pron = self.predict(word)

            prons.extend(pron)
            prons.extend([" "])

        return prons[:-1]

# Example testing
if __name__ == '__main__':
    texts = ["I refuse to collect the refuse around here.",
             "Did you want to read the book? I thought you read it already."]
    g2p = G2p()
    for text in texts:
        out = g2p(text)
        print(out)

