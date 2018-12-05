#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 17:31:27 2018

@author: zqwu, mguo123
"""
import os
import numpy as np
import torch as t
from models.enc import GraphConvEnc, WeaveEnc
from models.dec import InnerProductDecoder, AffineDecoder
from models.vae import GraphVAE, Trainer
from utils.load_molecules import load_molecules
from utils.metrics import eval_reconstruction_rate
import pickle

class Config:
    lr = 0.0001
    batch_size = 128
    max_epoch = 2000
    n_epochs = 10 # higher???
    n_tries = 150 # how many training iterations to do
    kl_rate = 0.1 
    lambd = 0.5
    gpu = True
    mpm = False
opt=Config()

"""
Mols = load_molecules('./data/qm9_clean.smi')
n_mols = len(Mols)
np.random.seed(123)
np.random.shuffle(Mols)
train_mols = Mols[:int(0.8*n_mols)]
valid_mols = Mols[int(0.8*n_mols):int(0.9*n_mols)]
test_mols = Mols[int(0.9*n_mols):]
pickle.dump([train_mols, valid_mols, test_mols], open('./data/featurized_qm9.pkl', 'w'))
"""

with open('./data/featurized_qm9.pkl', 'r') as f:
  train_mols, valid_mols, test_mols = pickle.load(f)
print('loaded molecules')

enc = GraphConvEnc(n_node_feat=train_mols[0][0].shape[1])  
dec = AffineDecoder()
vae = GraphVAE(enc, dec, gpu=opt.gpu)
model = Trainer(vae, opt, lambd=opt.lambd, kl_rate=opt.kl_rate)

best_valid_score = 0.
valid_scores = []
if __name__ == '__main__':
  for i in range(opt.n_tries):
    print("On %d, best till now: %f" % (i, best_valid_score))
    model.opt.lr = 0.001 * 0.4**(i//10) #Staircase lr decay
    model.train(train_mols, n_epochs=opt.n_epochs, log_every_n_step=100)
    valid_scores.append(eval_reconstruction_rate(valid_mols, model.predict(valid_mols)))
    if valid_scores[-1] > best_valid_score or i==0:
      best_valid_score = valid_scores[-1]
      print("New Best: %f" % best_valid_score)
      model.save('./model_qm9_'+str(opt.n_epochs)+'.pth')
  model.load('./model_qm9_'+str(opt.n_epochs)+'.pth')
  print(eval_reconstruction_rate(train_mols, model.predict(train_mols)))
  print(eval_reconstruction_rate(valid_mols, model.predict(valid_mols)))
  print(eval_reconstruction_rate(test_mols, model.predict(test_mols)))
  pickle.dump(valid_scores, open('logging_iter.pkl', 'wb'))
