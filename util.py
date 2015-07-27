from hashlib import md5

def digest(fname):
    '''
    get mp5 digest of a file
    '''
    with open(fname) as target:
        return md5(target.read()).hexdigest() 
