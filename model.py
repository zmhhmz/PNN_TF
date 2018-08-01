import theano
import theano.tensor as T
import numpy as np
#import scipy.io as sio
from utils import saveLayer    

class Network(object):
     """define a network given a list of layers"""
     def __init__ (self,layers):
        
        self.layers = layers
        self.params = [param for layer in self.layers for param in layer.params]
        self.x = T.ftensor4("x")
        self.y = T.ftensor4("y")
        lay1 = self.x
        last = False
        for i in range(len(self.layers)):
            if i==len(self.layers) - 1:
                 last=True
            lay = self.layers[i]
            lay1 = lay.set_inpt(lay1,last)
        self.output = lay1
        
     # gradient descent function   
     def SGD(self, data, ref, model):

        epochs = model['in_epoch']
        lr = model['lr']
        residual = model['residual']
        costo = model['cost']
        regol = model['regol']
        folder = model['train_dir']
        save_model_name = model['save_model_name']
        loss = np.zeros((2,1))
        
        
        blk=0
        for i in self.layers:
            blk=blk+i.w.eval().shape[2]-1
        blk=blk//2

        if costo=='L1':
            cost = T.sum(T.mean(abs(self.output - self.y[:,:,blk:-blk,blk:-blk]),axis=0))
            #print('L1')
        elif costo=='L2':
            cost = T.sum(T.mean((self.output - self.y[:,:,blk:-blk,blk:-blk])**2, axis=0))/2 
            if regol==True:
                l2_norm_squared = sum([(layer.w**2).sum() for layer in self.layers])
                cost = cost + 0.0001*l2_norm_squared        
        else:
            print('Error: cost function must be L1 or L2')
            
        cost2 = T.mean((self.output - self.y[:,:,blk:-blk,blk:-blk])**2)   
        grads = T.grad(cost, self.params)

        #sgd with momentum
        updates=[]
        k=0
        eta=lr
        for param, grad in zip(self.params,grads):
            if k>=len(self.params)-2:
                eta=lr/10
            else:
                eta=lr
            prev = theano.shared(param.get_value()*0.,borrow=True)
            step = 0.9*prev - eta*grad
            updates.append((prev, step))
            updates.append((param, param + step))
            k+=1
            
        #training function            
        train= theano.function([], [cost,cost2], updates=updates,
            givens={
                self.x: data,
                self.y: ref
            })
            
        #validation function    
        valid_loss = theano.function([], [cost,cost2],
            givens={
                self.x: data,
                self.y: ref
            })
        
        cost_1=np.zeros(epochs)
        cost_2=np.zeros(epochs)
        
        t=100000000     #value to compare with cost function
        mod=model
        
        #text file to save notes
        info=open(folder+'/PNN_model.txt','a')
        info.write('\n')
        for epoch in range(epochs):
            
            cost_1[epoch], cost_2[epoch]=valid_loss() 
            train() 
            info.write('\nepoch %g:, l1_batch=%f,\tl2_pixel:%f'%(epoch+1,cost_1[epoch],cost_2[epoch]))
            
            #save model at epoch with minimum cost value
            # if cost_1[epoch]<t:
            #     t=cost_1[epoch]
            mod=saveLayer(self.layers,mod)
                #mod['epoch_min']=epoch
                #file_model=folder + save_model_name
                #sio.savemat(file_model,mod)
            
            print('in_epoch: {}, cost: {}, l2_norm: {} '.format(epoch+1, cost_1[epoch],cost_2[epoch]))
        loss[0]=cost_2[0]
        loss[1]=cost_2[-1]
        info.close()

        return mod
        


class ConvLayer:
    """define convolutional layer with given wegight and biases"""
    def __init__ (self,weigth,bias, filter_shape=None):
        
        self.w=theano.shared(np.asarray(weigth,dtype=theano.config.floatX),borrow=False)
        self.b=theano.shared(np.asarray(np.squeeze(bias),dtype=theano.config.floatX),borrow=False)      
        self.filter_shape=self.w.get_value().shape
        self.params = [self.w, self.b]
         
    def set_inpt(self, inpt,last):
        self.last = last
        self.inpt = inpt
        conv_out = T.nnet.conv2d(self.inpt, self.w,
                        filter_shape=self.filter_shape, filter_flip=False)#use false to enable correlation with GPU
        #no Relu on last layer
        if self.last==False:
            self.output = T.nnet.relu(conv_out + self.b.dimshuffle('x', 0, 'x', 'x'))
        else:
            self.output = conv_out + self.b.dimshuffle('x', 0, 'x', 'x')
        return self.output
