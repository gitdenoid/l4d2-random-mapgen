from VMFFile import VMFFile
from VMFNode import getBounds
import copy
import numpy as np

OUTSIDE_MATERIAL = "DEV/DEV_BLENDMEASURE" # The material marking a portal
DOOR_DISTANCE_TOLERANCE = 16 # see pointNearPlane()

def oppositeDirection(direction):
  """Finds the opposite direction to the given one"""
  if direction == "north":
    return "south"
  elif direction == "south":
    return "north"
  elif direction == "east":
    return "west"
  elif direction == "west":
    return "east"
  elif direction == "up":
    return "down"
  elif direction == "down":
    return "up"
  else:
    raise AssertionError("Unknown direction \"" + direction + "\" for opposite")

# http://stackoverflow.com/questions/1401712/calculate-euclidean-distance-with-np
def euclideanDistance(x,y):
  """Returns the euclidean distance"""
  return np.sqrt(np.sum((x-y)**2))

def getLength(solid, direction):
  bounds = getBounds(solid)

  if "north" in direction or "south" in direction:
    axis = 0
  elif "east" in direction or "west" in direction:
    axis = 1
  else:
    axis = 2

  return abs(bounds[1][axis] - bounds[0][axis])

def pointNearPlane(point, bounds):
  """Checks whether a point is near a plane given by it's bounds"""
  pointDistance = euclideanDistance(bounds[0],point)
  portalSize = euclideanDistance(bounds[0],bounds[1])
  return pointDistance < portalSize + DOOR_DISTANCE_TOLERANCE
    
def findPortalOnSolid(solid):
  """Finds a portal on a solid"""
  side = None
  for child in solid.children:
    if child.name == "side": 
      if child.properties["material"] == OUTSIDE_MATERIAL :
        side = child
        break
  if side == None:
    return None
  return side.plane
    
def getTranslationVector(mapPortal, otherMapPortal):
  """Returns the vector needed to translate the otherMapPortal so that it is moved into the position of the given mapPortal"""
  portalBounds = getBounds(mapPortal)
  portalSize = portalBounds[1] - portalBounds[0]

  otherPortalBounds = getBounds(otherMapPortal)
  otherPortalSize = otherPortalBounds[1] - otherPortalBounds[0]

  if np.array_equal(portalSize,otherPortalSize):
    vector = portalBounds - otherPortalBounds
    return vector[0]
  else:
    return None
    
def translateBounds(bounds, vector):
  """Translates a bounding box by the given vector"""
  bounds = bounds.copy()
  bounds[0] += vector
  bounds[1] += vector
  return bounds
    
def intersect(bounds, otherBounds):
  """Intersects two bounding boxes"""
  upperBounds = np.append(bounds[1],otherBounds[1]).reshape((2,3))
  upperBound = np.min(upperBounds, axis=0)
  lowerBounds = np.append(bounds[0],otherBounds[0]).reshape((2,3))
  lowerBound = np.max(lowerBounds, axis=0)
  return np.array([lowerBound,upperBound])
    
def collide(bounds, otherBounds):
  """Checks whether two bounding boxes collide"""
  intersection = intersect(bounds, otherBounds)
  size = intersection[1]-intersection[0]
  collide = np.all(size > np.array([0,0,0]))
  # if collide:
    # print "Tiles collide",intersection
  return collide
    
class MapTile:
  """The MapTile yields data for a complete map"""
  
  def __init__(self):
    """Empty constructor"""
    pass
    
  def fromfile(self, filename):
    """Reads a map from a VMF file"""
    # TODO: make this a class method
    self.map = VMFFile()
    self.map.fromfile(filename)
    self.bounds = self.map.root.GetBoundsRecurse()
    self.filename = filename
    self.analyzePortals()
    self.once = False
    
  def deepcopy(self):
    """Returns a deep copy of this map"""
    deepcopy = MapTile()
    deepcopy.map = self.map.deepcopy()
    deepcopy.bounds = self.bounds
    deepcopy.doors = copy.deepcopy(self.doors)
    deepcopy.filename = self.filename
    deepcopy.once = self.once
    return deepcopy
  
  def setOnce(self, o):
    self.once = o

  def getOnce(self):
    return self.once
    
  def translate(self, vector):
    """Translate this map by the given vector"""
    self.map.root.TranslateRecurse(vector)
    self.bounds = translateBounds(self.bounds,vector)
  
  def getPortalDirection(self, portalPlane):
    """Find out on which side of the map tile a portal is located"""
    # this is probably stored in the U/V-axis material information
    portalBounds = getBounds(portalPlane)
    portalSize = portalBounds[1]-portalBounds[0]
    if portalSize[0] == 0:
      if portalBounds[0][0] == self.bounds[1][0]:
        return "east"
      elif portalBounds[0][2] == self.bounds[0][0]:
        return "west"
      else:
        raise AssertionError("Invalid portal plane "+str(portalBounds)+" neither bound matches "+str(self.bounds))
    elif portalSize[1] == 0:
      if portalBounds[0][1] == self.bounds[1][1]:
        return "north"
      elif portalBounds[0][1] == self.bounds[0][1]:
        return "south"
      else:
        raise AssertionError("Invalid portal plane "+str(portalBounds)+" neither bound matches "+str(self.bounds))
    elif portalSize[2] == 0:
      if portalBounds[0][2] == self.bounds[1][2]:
        return "up"
      elif portalBounds[0][2] == self.bounds[0][2]:
        return "down"
      else:
        raise AssertionError("Invalid portal plane "+str(portalBounds)+" neither bound matches "+str(self.bounds))
    else:
      raise AssertionError("Invalid portal plane "+str(portalBounds))
  
  def analyzePortals(self):
    """Find all IDs of solids with a portal and the portals' directions"""
    doors = dict({'north': [], 'east': [], 'south': [], 'west': [], 'up': [], 'down': []})
    solids = self.map.root.FindRecurse(lambda node : node.name == "solid" and not np.all(findPortalOnSolid(node)) == None)
    for solid in solids:
      portal = findPortalOnSolid(solid)
      direction = self.getPortalDirection(portal)
      doors[direction].append([solid.properties["id"], getLength(portal, direction)])
    
    self.doors = doors
    
  def findConnections(self, otherMap, tailLength=None):
    """Returns a list of possible connections between this and the other map.
    If tailLength is set, this map acts as if it only had tailLength portals with the highest IDs."""
    connections = []
    doorListsByDirection = list(self.doors.items())

    if tailLength:
      directionByDoor = dict()
      directionByDoorLength = dict()
      for direction, doorList in doorListsByDirection:
        for door in doorList:
          directionByDoor[int(door[0])] = direction
          directionByDoorLength[int(door[0])] = door[1]
      tailDoors = sorted(iter(list(directionByDoor.keys())),reverse=True)[:tailLength]
      doors = dict({'north': [], 'east': [], 'south': [], 'west': [], 'up': [], 'down': []})
      for door in tailDoors:
        doors[directionByDoor[door]].append([str(door), directionByDoorLength[door]])
    
    doorListsByDirection = list(doors.items())

    for direction, doorList in doorListsByDirection:
      if len(doorList) > 0:
        otherDoorList = otherMap.doors[oppositeDirection(direction)]
        
        # oh brother
        # love to see that n^2 runtime
        if len(otherDoorList) > 0:
          for i in range(len(doorList)):
            for j in range(len(otherDoorList)):
              if doorList[i][1] == otherDoorList[j][1]:
                print("Adding Connection", (direction, doorList[i][0], otherDoorList[j][0]))
                connections.append((direction, doorList[i][0], otherDoorList[j][0]))
          
    print("Total:", len(connections), "connections")
    return connections
    
  def findPortalsAndVector(self, otherMap, connection):
    """Returns all information needed to connect the otherMap to this one using the given connection"""
    mapPortal = self.findPortalOnSolidWithId(connection[1])
    otherMapPortal = otherMap.findPortalOnSolidWithId(connection[2])
    vector = getTranslationVector(mapPortal, otherMapPortal)
    return (vector, mapPortal, otherMapPortal)
    
  def append(self, otherMap, connection, vectors):
    """Appends the otherMap data to this one using the given connection and vectors.
       Mends the maps together by removing portal solids or doors where applicable."""
    otherMap = otherMap.deepcopy()
    return self.mend(otherMap, connection, vectors)
    
  def findPortalOnSolidWithId(self, id):
    """Finds a portal on the solid with the given ID."""
    object = self.map.root.FindRecurse(lambda node : node.name == "solid" and node.properties["id"] == id)
    solid = object[0]
    portal = findPortalOnSolid(solid)
    if np.all(portal) == None:
      print(("ERROR: Every portal must have a solid having a side with the material "+ OUTSIDE_MATERIAL +" marking the outside"))
    return portal
    
  def mend(self, otherMap, connection, vectors):
    """Mends the otherMap with this one using the given connection, portals and translation vector."""
    vector, mapPortal, otherMapPortal = vectors
    (direction, selfDoor, newDoor) = connection
    
    if not otherMap == self:
      removed = otherMap.map.root.DeleteRecurse(lambda node : "classname" in node.properties and node.properties["classname"] == "info_player_start")
      print("Removed", removed, "info_player_start from other map")
      removed = otherMap.map.root.DeleteRecurse(lambda node : "classname" in node.properties and node.properties["classname"] == "prop_door_rotating" and pointNearPlane(node.origin,otherMapPortal))
      print("Removed", removed, "doors from other map")
    removed = otherMap.map.root.DeleteRecurse(lambda node : node.name == "solid" and node.properties["id"] == newDoor)
    print("Removed", removed, "solids from other map")

    # we gotta hunt for the fabled portalIndex
    otherDoors = otherMap.doors[oppositeDirection(direction)]
    door = -1

    # not the best solution, but I'm not going for optimization rn
    for door in otherDoors:
      for item in door:
        if item == newDoor:
          break
      if item == newDoor:
        break
    
    # will error if it doesn't find the door, of course
    otherDoors.remove(door)
      
    entities = self.map.root.FindRecurse(lambda node : node.name == "entity" and not node.properties["classname"] == "func_detail" and pointNearPlane(node.origin,mapPortal))
    removed = 0
    for entity in entities:
      removed += entity.DeleteRecurse(lambda node : node.name == "editor")
    print("Removed", removed, "editor information from remaining entities in base map")

    removed = self.map.root.DeleteRecurse(lambda node : node.name == "solid" and node.properties["id"] == selfDoor)
    print("Removed", removed, "solids from base map")

    # we'll have to do the same thing again here
    selfDoors = self.doors[direction]
    door = -1

    for door in selfDoors:
      for item in door:
        if item == selfDoor:
          break
      if item == selfDoor:
        break

    selfDoors.remove(door)

    if not otherMap == self:
      maxId = self.map.root.GetMaximumIdRecurse(0)
      otherMap.map.root.IncreaseIdRecurse(maxId)
      print("Increased IDs in new map by", maxId)

      print("Translating new map with vector", vector, "...")
      otherMap.translate(vector)

      print("Adding new map...")
      self.map.root.AddOtherMap(otherMap.map.root)
      
      for direction in list(otherMap.doors.keys()):
        for portalSolidId in otherMap.doors[direction]:
          portalSolidId[0] = str(int(portalSolidId[0]) + maxId)
          self.doors[direction].append(portalSolidId)
      print("New map merged!")
    
  def detectLoops(self):
    """Detect loops within this map (tiles positioned in such a way that the player can run in circles)"""
    print ("Detecting loops...")
    zeroVector = np.array([0, 0, 0])
    for direction in list(self.doors.keys()):
      for portalSolidId in self.doors[direction]:
        doorNodes = self.map.root.FindRecurse(lambda node : node.name == "solid" and node.properties["id"] == portalSolidId[0])
        for doorNode in doorNodes:
          portal = findPortalOnSolid(doorNode)
          otherDoorNodes = self.map.root.FindRecurse(lambda node : not node == doorNode and node.name == "solid" and node.properties["id"] in self.doors[oppositeDirection(direction)] and np.array_equal(getTranslationVector(portal,findPortalOnSolid(node)),zeroVector))
          if len(otherDoorNodes) == 1:
            otherDoorNode = otherDoorNodes[0]
            # TODO: the wrong door is removed
            self.mend(self,(direction,doorNode.properties["id"],otherDoorNode.properties["id"]), (zeroVector, portal, findPortalOnSolid(otherDoorNode)))
    
  def close(self):
    """Remove remaining door entities from the outside of the map so it becomes compilable."""
    self.detectLoops()
    # TODO: sometimes not all remaining doors are removed
    removed = 0

    for direction in list(self.doors.keys()):
      for portalSolidId in self.doors[direction]:
        doorNodes = self.map.root.FindRecurse(lambda node : node.name == "solid" and node.properties["id"] == portalSolidId[0])
        for doorNode in doorNodes:
          portalBounds = getBounds(findPortalOnSolid(doorNode))
          removed += self.map.root.DeleteRecurse(lambda node : "classname" in node.properties and node.properties["classname"] == "prop_door_rotating" and pointNearPlane(node.origin,portalBounds))
    print("Removed", removed, "doors to close map")
      
  def generateNavMeshScript(self):
    """Generate a config file for generating the nav mesh in game."""
    lines = []
    lines.append(["sv_cheats 1","z_debug 1","director_stop","nb_delete_all","nav_edit 1"])

    start = self.map.root.FindRecurse(lambda node : "classname" in node.properties and node.properties["classname"] == "info_null" and "targetname" in node.properties and node.properties["targetname"] == "start")
    if not len(start) == 2:
      print(("ERROR: Need 2 corners for PLAYER_START nav mesh, got",len(start),"instead"))
    else:
      lines.append(["nav_clear_selected_set","setpos " + start[0].GetOrigin() + "","setang 90 0 0"])
      lines.append(["nav_begin_area","setpos " + start[1].GetOrigin() + "","setang 90 0 0"])
      lines.append(["nav_end_area","nav_toggle_in_selected_set","mark PLAYER_START","nav_clear_selected_sechot","clear_attribute PLAYER_START"])
    
    finale = self.map.root.FindRecurse(lambda node : "classname" in node.properties and node.properties["classname"] == "info_null" and "targetname" in node.properties and node.properties["targetname"] == "finale")
    if not len(finale) == 2:
      print(("ERROR: Need 2 corners for FINALE nav mesh, got",len(finale),"instead"))
    else:
      lines.append(["nav_clear_selected_set","setpos " + finale[0].GetOrigin() + "","setang 90 0 0"])
      lines.append(["nav_begin_area","setpos " + finale[1].GetOrigin() + "","setang 90 0 0"])
      lines.append(["nav_end_area","nav_toggle_in_selected_set","mark FINALE","nav_clear_selected_set","clear_attribute FINALE"])
    
    walkables = self.map.root.FindRecurse(lambda node : "classname" in node.properties and node.properties["classname"] == "info_null" and "targetname" in node.properties and node.properties["targetname"] == "walkable")
    for walkable in walkables:
      lines.append(["setpos " + walkable.GetOrigin() + "","setang 90 0 0"])
      lines.append(["nav_mark_walkable"])
    lines.append(["nav_generate_incremental"])
    
    lines.append(["nav_analyze"])
    lines.append(["nav_save"])
    lines.append(["director_start","sv_cheats 0"])
    
    out = "bind KP_PLUS navgen000\n"
    for num, line in enumerate(lines):
      out += "alias \"navgen%03i\" \"%s;bind KP_PLUS navgen%03i\"\n"%(num,";".join(line),num+1)
    out += "alias \"navgen%03i\" \"echo Finished\"\n"%len(lines)
    return out
  
  def __lt__(self, other):
    return self