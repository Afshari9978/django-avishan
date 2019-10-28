import bcrypt


def hash(password):
    return bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt()).decode('utf8')


a = hash('23153654326')
c = bcrypt.hashpw('23153654326'.encode('utf8'), bcrypt.gensalt())
d = c.decode('utf8')
b = 1