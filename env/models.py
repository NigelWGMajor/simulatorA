from enum import Enum
import random
import math

# Controlling dimensions

# Coordinates map to:
#        G
#       /  \
#      B -- R

scale = 360
 
# because this factors nicely by possible bucket sizes:
#   1    2    3    4   5   6   8   9  10  12  15  18 
#   x    x    x    x   x   x   x   x   x   x   x   x  
# #360  180  120  90  72  60  45  40  36  30  24  20 
# Number of elements is n*(n+1)/2
# at the default of n = 24, 300 elements.
# at the finest in our model,
# n = 90, 4,095 elements. 
# this is set in the quantize value in the Settings class.

##############################################################################
## The allowable states an element can be in
class Status(Enum):
    OWNED = 0
    NEW = 1
    RECOMMENDED = 2
    ACCEPTED = 3
    REJECTED = 4
    STALE = 5 # stale recommendations

##############################################################################
## Handle a list of elements
class ElementList(list):

    # take a number of elements randomly as ElementList
    def take_random(self, n):
        candidates = ElementList(self)
        random.shuffle(candidates)
        return candidates.take(n)
    
    def take(self, n, skip=0):
        i = min(n + skip, len(self))
        result = ElementList()
        j = skip
        while j < i:
           result.append(self[j])
           j += 1
        return result
    
    def drop_head(self, n):
        del self[:n]
      
    def append_list(self, elementList):
        for e in elementList:
            self.append(e)
        return self
          
    # return those elements that are owned, new or accepted, most recently added first.  
    def get_eligible(self):  
        x = [item for item in self if item.state == Status.NEW or item.state == Status.OWNED or item.state == Status.ACCEPTED]
        x.sort(key = lambda x : x.serial, reverse = True )
        return ElementList(x)

    # get a number of elements within an age range as ElementList
    # the instance is proportional to the age
    def take_in_age_range(self, newest, oldest, n):
        results = ElementList()
        count = len(self)
        if newest > count - 1:
            return results
        if (oldest > count -1): 
            oldest = count -1
        for index in range(newest, oldest):
            results.append(self[count - index - 1])
        return results
        
    # add an intial element in the center
    def add_element_center(self):
        self.append(Element(Location(), Status.NEW))    
        
    # add a new random element not already in the list
    def add_new_element(self):
        self = self.clear()
        tries = 4000
        while True:
            location = Location.Random()
            if not self.location_is_populated(location):
                break
            else:
                tries -= 1
                if (tries < 0):
                    return self # give up!
        self.append(Element(location, Status.NEW))        
        return self

    # add a new random element with user bias
    def add_new_element_biased(self):
        self = self.clear()
        tries = 4000
        while True:
            location = Location.RandomBiased()
            if not self.location_is_populated(location):
                break
            else:
                tries -= 1
                if (tries < 0):
                    return self # give up!
        self.append(Element(location, Status.NEW))        
        return self

    # get adjacent (first tier) objects not in the collection
    def new_adjacent(self, element):
        return ElementList(get_adjacent(self, element, 1))

    # get close (second tier) elements not in the collection
    def new_close(self, element):
        return ElementList(get_adjacent(self, element, 2))
    
    def clear(self):
        for item in [item for item in self if item.state == Status.RECOMMENDED]:
            item.state = Status.STALE
        for item in [item for item in self if item.state == Status.NEW]:
            item.state = Status.OWNED
        return self
        
    # get any existing element that matches the location
    def get_existing(self, element):
        # optimized to reduce iterations
        for candidate in self:
            if candidate.location.coincides(element.location):
                return candidate
        return None
        
    def location_is_populated(self, location):
        x = [item for item in self if item.location.coincides(location)]
        if len(x) > 0:
            return True
        return False
    
    def add_element(self, location, state):
        self.append(Element(location, state))

##############################################################################
## Handles the element position
class Location:
    # quantizes any value to an allowable value within the range of 0 - (scale-1) mod bucket
    def quantize_value(value):
        quantize = Settings.get_quantize()
        return min(max(math.floor((value+quantize/2)/quantize) * quantize, 0), scale - 1)
       
    def Random():
        global scale
        global quantize
        # anywhere is legal!
        location = Location()
        x = Location.quantize_value(random.randint(0, scale - 1))
        y = Location.quantize_value(random.randint(0, scale - 1))
        if (x > y):
            t = x
            x = y
            y = t
        location.a = Location.quantize_value(x)
        location.b = Location.quantize_value(y - x)
        location.c = Location.quantize_value(scale - 1 - y)
        return location
     
    def RandomBiased(): 
        global scale
        location = Location.Random().skew()
        return location
        # generate a delta based on a value. Used to skew the value towards the extreme

    def __init__(self):
        self.a = Location.quantize_value(scale / 3)
        self.b = self.a
        self.c = scale - self.a - self.b
    
    def skew(self):
        # function to add bias towards channel b, away from channel a with c neutral
        # The amount of skewing is proprtional to the amount that we don't have c
        #ratio = 2 # reciprocal of the compression strength
        #drift = (scale - self.a) 
        # pull away from the a corner
        #self.a = self.a - (self.a / ratio)                
        #self.c = self.c + drift
        fs = scale - 1
        ratio = 0.33
        # need to pull away from the red corner in the direction of the green corner, 
        # proportinally to how far from the blue corner and how close to the red
        delta = (scale - self.c) * self.a * ratio / fs
        self.a -= delta
        self.b += delta
        self.a = Location.quantize_value(self.a)
        self.b = Location.quantize_value(self.b)
        self.c = scale - 1 - self.a - self.b
        return self
    
    def to_color_string(self):
        r = int(self.a / scale * 255)
        g = int(self.b / scale * 255)
        b = int(self.c / scale * 255)
        # all should be between 255 and 0
        return '#' + '{:02X}'.format(r) + '{:02X}'.format(g) + '{:02X}'.format(b)
    
    def coordinates(self):
        return [self.a, self.b, self.c]
    
    def is_in_range(self):
        for x in (self.a, self.b, self.c):
            if x < 0:
                return False
            elif x > scale:
                return False
        return True
    
    def coincides(self, other):
        if abs(other.a - self.a) > 2:
            return False
        elif abs(other.b - self.b) > 2:
            return False
        elif abs(other.c - self.c) > 2:
            return False
        return True
 
## Represents a displayable element.
class Element:
    
    current_serial:int = 0 # used for serial numbers for history
    
    def __init__(self, location: Location, state):
        self.serial = Element.current_serial # used for history
        Element.current_serial += 1
        self.location: Location = location
        self.state = state
        self.recommendationCount = 0
        
    def accept(self):
        self.state = Status.ACCEPTED
        
    def reject(self):
        self.state = Status.REJECTED

# A particular use case. Holds the collectionof elements.
class Actor:
    def __init__(self):
        self.Elements = ElementList()
        self.Elements.add_element_center()

    # this also serves the purpose of an is_location_used method
    def get_Element_at_location(self, location: Location):
        x = [Element for Element in self.Elements if Element.location.coincides(location)]
        if len(x) == 1:
            return x[0]
        return None
    
##   def add_Element(self, location: Location, state: Status):
##       if state != Status.ACCEPTED and state != Status.REJECTED:
##           if not self.get_Element_at_location(location) is None:
##               # if there is already an element at that position, do nothing.
##               return self
##           if state == Status.NEW:
##               # turn all old news into owned
##               for element in self.Elements:
##                   if element.state == Status.NEW:
##                       element.state = Status.OWNED
##               element = Element(location, state)
##               self.Elements.append(element) 
##               self.make_recommendations_stale()
##           elif state == Status.RECOMMENDED:
##               element = Element(location, state)
##               element.recommendationCount += 1
##               self.Elements.append(element) 
##       elif state == Status.ACCEPTED or state == Status.DECLINED:
##           x = get_Element_at_location(location)
##           x.state = state
##       return self
##
##   def make_recommendations_stale(self):
##       recommended = [element for element in self.Elements if element.state == Status.RECOMMENDED]
##       for element in recommended:
##           element.state = Status.STALE
##       return self

 # Control resolution to specific bucket sizes
class Settings:
    # quantize boundaries
    bucket = [6,8,9,10,15,18,20,24,30,36,40,45,60,72,90]
    quantizeIndex = 8
    def quantize_more():
        if Settings.quantizeIndex < len(Settings.bucket) - 1:
            Settings.quantizeIndex += 1
    def quantize_less():
        if Settings.quantizeIndex > 0:
            Settings.quantizeIndex -= 1
    def get_quantize():
        return Settings.bucket[Settings.quantizeIndex]

# Used to exchange data with the UI
class Data:
    def __init__(self, n:int, text: str):
        self.n = n
        self.text = text

############################################################################################
## Adjacency calculations
    
# returns a set of elements within the first or second tier that are not owned, new, or accepted.
def get_adjacent(elements: ElementList, element: Element, tier: int):
    # there are 6 possible relative displacements from a quantized location.
    if tier == 1:
        motions = [
            (1, -1, 0), (1, 0, -1), (0, 1, -1), 
            (0, -1, 1), (-1, 0, 1), (-1, 1, 0)]
    else : # second tier
        motions = [
            (2, 0, -2), (2, -1, -1), (2, -2, 0),
            (0, 2, -2), (-1, 2, -1), (-2, 2, 0),
            (0, -2, 2), (-1, -1, 2), (-2, 0, 2),
            (-2, 1, 1), (1, -2, 1), (1, 1, -2)]
        
    adjacents : [Element] = [] # set operations may be better suited for this because they use a hash table
    for motion in motions:
        adjacents.append(apply_motion(motion, element))
    # filter out any out of range elements
    adjacents = [element for element in adjacents if element.location.is_in_range()] 
    # filter out any already listed in the element
    existingLocations = ElementList([element for element in elements if element.state == Status.NEW or element.state == Status.OWNED or element.state == Status.ACCEPTED])
    candidates = []
    for candidate in adjacents:
        if (existingLocations.get_existing(candidate)) == None:
            candidates.append(candidate)
    return candidates
    
def apply_motion(motion: (int, int, int), element: Element ):
    quantize = Settings.get_quantize()
    location = Location()
    location.a = element.location.a + quantize * motion[0]
    location.b = element.location.b + quantize * motion[1]
    location.c = element.location.c + quantize * motion[2]
    return Element(location, element.state)