#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import chseg
import numpy as np
import tensorflow as tf
from rnn_seq2seq_clf import RNNTextClassifier
from collections import Counter


SEQ_LEN = 50
N_CLASS = 4 # B: 0, M: 1, E: 2, S: 3
sample = '没有孩子的世界是寂寞的'
py = int(sys.version[0])


def x_to_seq(*args):
    data = []
    for x in args:
        x = x[: (len(x) - len(x) % SEQ_LEN)]
        data.append(np.reshape(x, [-1, SEQ_LEN]))
    return data


def y_to_seq(*args):
    data = []
    for y in args:
        y = y[: (len(y) - len(y) % SEQ_LEN)]
        y = tf.contrib.keras.utils.to_categorical(y)
        data.append(np.reshape(y, [-1, SEQ_LEN, N_CLASS]))
    return data


if __name__ == '__main__':
    x_train, y_train, x_test, y_test, vocab_size, char2idx, idx2char = chseg.load_data()
    X_train, X_test = x_to_seq(x_train, x_test)
    Y_train, Y_test = y_to_seq(y_train, y_test)
    print('Vocab size: %d' % vocab_size)

    clf = RNNTextClassifier(SEQ_LEN, vocab_size, N_CLASS)
    clf.fit(X_train, Y_train, val_data=(X_test, Y_test), n_epoch=1)
    
    chars = list(sample) if py == 3 else list(sample.decode('utf-8'))
    preds = clf.infer([char2idx[c] for c in chars])
    labels = np.argmax(preds, 1)
    res = ''
    for i, l in enumerate(labels):
        c = sample[i] if py == 3 else sample.decode('utf-8')[i]
        if l == 2 or l == 3:
            c += ' '
        res += c
    print(res)