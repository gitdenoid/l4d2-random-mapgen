import MapTile
from VMFNode import vectorToString
import os
import random
import sys

"""
This proof-of-concept random map generator for Left 4 Dead 2 (and other Hammer based maps) loads map tiles from VMF files and puts them together randomly.
"""
SEED = 42 # This random seed affects the selection of tiles and connections. A change leads to a completely different map layout.
NUMBER_OF_TILES = 5 # How many tiles there should be in the map.
TAIL_LENGTH = 3 # The number of portals considered to be the tail of the map. Greater values produce more dead ends.

def chooseConnection(connections):
  """Choses a random connection out of the given ones"""
  if len(connections) > 0:
    choice = random.choice(connections)
    direction = choice[0]
    portal = choice[1]
    otherPortal = choice[2]
    connection = (direction, portal, otherPortal)
    print("Chose connection:", connection)
    return connection
  else:
    return None

def collide(box, blockingBoxes):
  """Checks whether two bounding boxes collide"""
  for blockingBox in blockingBoxes:
    if MapTile.collide(blockingBox,box):
      return True
  return False
    
def addTile(base, tile, blockingBoxes):
  """Adds a tile by trying all possible connections"""

  print("Adding tile for ", tile)
  directions = base.findConnections(tile, TAIL_LENGTH)
  for direction in directions:
    for portal in direction[1]:
      for otherPortal in direction[2]:
        connection = (direction[0],portal,otherPortal)
        vectors = base.findPortalsAndVector(tile, connection)
        vector = vectors[0]
        translatedBounds = MapTile.translateBounds(tile.bounds,vector)
        if not collide(translatedBounds,blockingBoxes):
          blockingBoxes.append(translatedBounds)
          base.append(tile, connection, vectors)
          return True
        else:
          print ("Tiles collide")
  return False
    
def tryAddTile(base, tile, blockingBoxes):
  """Tries to add a tile by trying one random connection"""

  connections = base.findConnections(tile, TAIL_LENGTH)
  connection = chooseConnection(connections)
  if connection == None:
    return False
  vectors = base.findPortalsAndVector(tile, connection)
  vector = vectors[0]
  translatedBounds = MapTile.translateBounds(tile.bounds,vector)
  if collide(translatedBounds, blockingBoxes):
    print ("Tiles collide")
    return False
  else:
    blockingBoxes.append(translatedBounds)
    base.append(tile, connection, vectors)
    return True
    
def selectAndTryToAddTile(base, tiles, blockingBoxes):
  """Selects a random tile and tries to add it to the map"""
  tile = random.choice(tiles)
  print("Chose tile:", os.path.basename(tile.filename))
  success = tryAddTile(base, tile, blockingBoxes)
  if success and tile.getOnce():
    tiles.remove(tile)
    print ("Removed tile from pool because it specified to be addeed only once.")
  return success
    
def loadTiles(path):
  """Loads all tiles from a directory"""
  print("== LOADING MAP FILES ==")
  starts = []
  tiles = []
  finales = []
  listing = os.listdir(path)
  for filename in listing:
    if filename[-3:] == "vmf":
      basename = os.path.basename(filename)
      print("Loading", basename)
      maptile = MapTile.MapTile()
      maptile.fromfile(path+filename)
      if filename[:5] == "start":
        starts.append(maptile)
      elif filename[:6] == "finale":
        finales.append(maptile)
      else:
        if filename[:4] == "once":
          maptile.setOnce(True)
        tiles.append(maptile)
        try: 
          repeat = int(basename.split('_')[0])
          print("NOTE: Tile is", repeat, "times more likely to be chosen.")
          for i in range(repeat):
            tiles.append(maptile)
        except ValueError:
          pass
  return (starts, tiles, finales)
    
if __name__ == "__main__":
  """Main program"""

  if len(sys.argv) >= 2:
    SEED = int(sys.argv[1])
  random.seed(SEED)

  if len(sys.argv) >= 3:
    filename = "./output/" + sys.argv[2] + ".vmf"
  else:
    filename = "./output/map-" + str(SEED) + ".vmf"

  mapStyle = "dev"

  print("+++++ L4D2 LEVEL GENERATOR +++++")
  print("Seed:", SEED)
  print("Tile count:", NUMBER_OF_TILES)
  print("Max tail length:", TAIL_LENGTH)
  print("Map Style:", mapStyle)
  print("Outputting to", filename)

  print()

  tilePath = "tiles/" + mapStyle + "/"
  starts, tiles, finales = loadTiles(tilePath)

  print()

  print("== BEGIN MAP FILE CREATION ==")
  base = random.choice(starts)
  print("Chose starting tile", base.filename)

  finale = random.choice(finales)
  print("Chose ending tile", finale.filename)

  tiles.sort()
  blockingBoxes = [base.bounds]

  tilesAdded = 0
  print("-- TILE 1 --")
  for i in range(NUMBER_OF_TILES * len(tiles)):
    if selectAndTryToAddTile(base, tiles, blockingBoxes):
      tilesAdded += 1
      print("-- TILE", tilesAdded + 1, "--")
    if tilesAdded == NUMBER_OF_TILES:
      break
  print("Total tiles: ", tilesAdded)
      
  if not addTile(base, finale, blockingBoxes):
    print ("ERROR: Failed to append final \"finale\" tile.")
  else:
    pass
    
  base.close()

  file = open(filename, "w")
  file.write(base.map.root.ToStringRecurse(0))
  file.close()

  file = open("../../left4dead2/cfg/combined.cfg","w")
  file.write(base.generateNavMeshScript())
  file.close()