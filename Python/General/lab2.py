##def printAll1(xs):
##    for x in xs:
##        print(x)
##
##def printAll1(xs):
##    xsi = iter(xs)
##    while True:
##        try:
##            x = next(xsi)
##            print(x)
##        except StopIteration:
##            break
##
##def safeDiv(m,n):
##    try:
##        return m/n
##    except:
##        return "You tried to divide by zero."
##
##
##printAll1([1,2,3,4,5])

class RLE:
  def __init__(self, sequence):
    self._seq = sequence
    self._index = 0

  def __iter__(self):
    return self

  def __next__(self):
    if self._index < len(self._seq):
      value = self._seq[self._index][1]
      if self._seq[self._index][0] == 1:
        self._index += 1
      else:
        self._seq[self._index] = (self._seq[self._index][0] - 1, self._seq[self._index][1])
      return value
    else:
      raise StopIteration

def sieve(s):
    n = next(s)
    yield n
    sieve((i for i in s if i % n != 0))
