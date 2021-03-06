import tensorflow as tf

def PNN(I_in,param):
    I_in,reg1 = resCNNnet('ResBlock',I_in,1,param['channel1']+param['channel2'],param['NumResNet'],param['regol'])
    reg2=0

    w = create_kernel('wn', [5, 5, param['channel1']+param['channel2'], param['channel2']])
    if param['regol']:
        reg2i = tf.reduce_sum(w**2)
        reg2=reg2+reg2i
    I_in = tf.nn.conv2d(I_in, w, [1, 1, 1, 1], padding='SAME')
    reg = reg1+reg2
    return I_in,reg

def create_kernel(name, shape, initializer=tf.truncated_normal_initializer(mean = 0, stddev = 0.1)):
    regularizer = tf.contrib.layers.l2_regularizer(scale = 1e-10)
    new_variables = tf.get_variable(name=name, shape=shape, initializer=initializer, regularizer=regularizer, trainable=True)
    return new_variables

def resCNNnet(name,X,j,channel,levelN,regol):
    reg=0
    with tf.variable_scope(name): 
        for i in range(levelN-1):
            X,reg_i = resLevel(('resCNN_%s_%s'%(j,i+1)), 3, X, channel,regol)
            if regol:
                reg = reg+reg_i                               
    return X , reg
    
def resLevel(name, Fsize,X,Channel,regol): #2层
    with tf.variable_scope(name):
        reg=0
        kernel = create_kernel(name='weights1', shape=[Fsize, Fsize, Channel, Channel+3])
        biases = tf.get_variable(name='biases1',shape=[Channel+3],dtype=tf.float32,initializer=tf.constant_initializer(0.0),trainable=True)
        scale = tf.get_variable(name='scale1',shape=[Channel+3],dtype=tf.float32,initializer=tf.constant_initializer(1.0/100),trainable=True)
        beta = tf.get_variable(name='beta1',shape=[Channel+3],dtype=tf.float32,initializer=tf.constant_initializer(0.0),trainable=True)
        if regol:
            reg1 = tf.reduce_sum(kernel**2)
        conv = tf.nn.conv2d(X, kernel, [1, 1, 1, 1], padding='SAME')
        feature = tf.nn.bias_add(conv, biases)

        mean, var  = tf.nn.moments(feature,[0, 1, 2])
        feature_normal = tf.nn.batch_normalization(feature, mean, var, beta, scale, 1e-5)

        feature_relu = tf.nn.relu(feature_normal)
        
        # 我又加了一层
        kernel = create_kernel(name='weights2', shape=[Fsize, Fsize, Channel+3, Channel])
        biases = tf.get_variable(name='biases2',shape=[Channel],dtype=tf.float32,initializer=tf.constant_initializer(0.0),trainable=True)
        scale = tf.get_variable(name='scale2',shape=[Channel],dtype=tf.float32,initializer=tf.constant_initializer(1.0/100),trainable=True)
        beta = tf.get_variable(name='beta2',shape=[Channel],dtype=tf.float32,initializer=tf.constant_initializer(0.0),trainable=True)
        if regol:
            reg2 = tf.reduce_sum(kernel**2)
        conv = tf.nn.conv2d(feature_relu, kernel, [1, 1, 1, 1], padding='SAME')
        feature = tf.nn.bias_add(conv, biases)

        mean, var  = tf.nn.moments(feature,[0, 1, 2])
        feature_normal = tf.nn.batch_normalization(feature, mean, var, beta, scale, 1e-5)
        feature_relu = tf.nn.relu(feature_normal)

        X = tf.add(X, feature_relu)  #  shortcut  
        if regol:
            reg = reg1+reg2
        return X,reg
