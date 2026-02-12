# SPDX-License-Identifier: Apache-2.0
"""
CWL file formats utilities.

For more information, please visit https://www.commonwl.org/user_guide/16-file-formats/
"""


from schema_salad.exceptions import ValidationException
from schema_salad.utils import aslist, json_dumps

from cwl_utils.types import CWLFileType

from rdflib import URIRef, RDFS, OWL, Graph, Namespace
from collections import deque


def find_descendants_fixed(graph, start_uri, mode="include", only_uris=True, include_start=True):
    from collections import deque
    queue = deque([start_uri])
    visited = set([start_uri])
    results = set()
    if include_start:
        results.add(start_uri)

    while queue:
        cur = queue.popleft()
        if include_start or cur != start_uri:
            results.add(cur)

        # Subclasses
        for child in graph.subjects(RDFS.subClassOf, cur):
            if only_uris and not isinstance(child, URIRef):
                continue
            if child not in visited:
                visited.add(child)
                queue.append(child)

        # Equivalents
        if mode in ("traverse", "include"):
            for eq in graph.objects(cur, OWL.equivalentClass):
                if only_uris and not isinstance(eq, URIRef):
                    continue
                if eq not in visited:
                    visited.add(eq)
                    queue.append(eq)
                    if mode == "include":
                        results.add(eq)
            for eq in graph.subjects(OWL.equivalentClass, cur):
                if only_uris and not isinstance(eq, URIRef):
                    continue
                if eq not in visited:
                    visited.add(eq)
                    queue.append(eq)
                    if mode == "include":
                        results.add(eq)

    return results

# test in line for now:
'''

g = Graph()
EX = Namespace("http://example.org/")

rasterfile = EX.rasterfile
geotiff = EX.geotiff
netcdf = EX.netcdf
tiff = EX.tiff

g.add((geotiff, RDFS.subClassOf, rasterfile))
g.add((netcdf, RDFS.subClassOf, rasterfile))
g.add((tiff, OWL.equivalentClass, geotiff))  # bidirectional

subclasses = find_descendants_safe(g, rasterfile, mode="include", include_start=True)
for s in subclasses:
    print(s)
'''


from rdflib import Graph, URIRef, RDFS, OWL, Namespace

# Create RDF graph
g = Graph()
EX = Namespace("http://example.org/")

# Define classes
rasterfile = EX.rasterfile
geotiff = EX.geotiff
netcdf = EX.netcdf
tiff = EX.tiff
png = EX.png
jpeg = EX.jpeg
imagefile = EX.imagefile
tif_variant = EX.tif_variant

# Add subclass hierarchy
g.add((geotiff, RDFS.subClassOf, rasterfile))
g.add((netcdf, RDFS.subClassOf, rasterfile))
g.add((tiff, RDFS.subClassOf, rasterfile))
g.add((png, RDFS.subClassOf, imagefile))
g.add((jpeg, RDFS.subClassOf, imagefile))
g.add((rasterfile, RDFS.subClassOf, imagefile))  # rasterfile is also subclass of imagefile

# Add equivalents (bidirectional cycles)
g.add((tiff, OWL.equivalentClass, geotiff))      # tiff ≡ geotiff
g.add((tif_variant, OWL.equivalentClass, tiff)) # tif_variant ≡ tiff
g.add((geotiff, OWL.equivalentClass, tif_variant)) # creates a 3-way cycle

# Add some unrelated class
vectorfile = EX.vectorfile
shapefile = EX.shapefile
g.add((shapefile, RDFS.subClassOf, vectorfile))

print("rasterfile")
subclasses = find_descendants_fixed(g, rasterfile)
for s in sorted(subclasses):
    print("-", s)
print("imagefile")
subclasses = find_descendants_fixed(g, imagefile)
for s in sorted(subclasses):
    print("-", s)
print("geotiff")
subclasses = find_descendants_fixed(g, geotiff, include_start=True)
for s in sorted(subclasses):
    print("-", s)


'''
Output:
rasterfile
- http://example.org/geotiff
- http://example.org/netcdf
- http://example.org/rasterfile
- http://example.org/tif_variant
- http://example.org/tiff
imagefile
- http://example.org/geotiff
- http://example.org/imagefile
- http://example.org/jpeg
- http://example.org/netcdf
- http://example.org/png
- http://example.org/rasterfile
- http://example.org/tif_variant
- http://example.org/tiff
geotiff
- http://example.org/geotiff
- http://example.org/tif_variant
- http://example.org/tiff

'''