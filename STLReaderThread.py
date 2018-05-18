import struct
import math
import threading
import time
import sys
import multiprocessing
from multiprocessing import Process


def read_csv(filename):

    # Records start time for time calculation
    start_time = time.time()

    #Initializes variables
    
    global sem
    sem = threading.Semaphore()

    # Reads header field
    global file
    file = open(filename, 'rb')
    print('File name: %s' % file.read(80).decode('utf-8'))

    # Reads and converts the total number of triangles
    encoded_triangles = file.read(4)
    triangles = int.from_bytes(encoded_triangles, 'little')

    # Will store the total area from each thread
    manager = multiprocessing.Manager()
    return_tot = manager.dict()
    totals = []

    # Will store the min box from each thread
    return_coord = manager.dict()
    coords = []


    # Creates 4 processes
    for index in range (0, 4):
        p = Process(target=thread_compute, args=(index, triangles, return_tot, return_coord))
        totals.append(p)
        coords.append(p)
        p.start()
    
    # Joins the processes when completed
    for index in range (0, 4):
        p.join()

    # Computes the total area by adding the areas returned by each thread
    total_area = 0
    for index in range (0, 4):
        total_area += return_tot[index]

    min_box = find_box(return_coord[0], return_coord[1], return_coord[2], return_coord[3])

    # Computes the total time
    end_time = time.time()
    total_time = end_time - start_time

    return triangles, total_area, min_box, total_time

# Each thread's work happens here
def thread_compute(index, triangles, return_tot, return_coord):
    total_area = 0
    min_max = []

    start = int(index * triangles / 4)
    if int(triangles / 4)  > triangles - 1:
        end = triangles
    else:
        end = start + int(triangles / 4)

    for triangle in range(start, end):
        
        sem.acquire()
        # Reads the normal vector (not used), all 3 points, and the attribute (not used) for this triangle
        normal = [file.read(4), file.read(4), file.read(4)]
        p1 = [file.read(4), file.read(4), file.read(4)]
        p2 = [file.read(4), file.read(4), file.read(4)]
        p3 = [file.read(4), file.read(4), file.read(4)]
        attr = file.read(2)
        sem.release()

        # Converts the points to the proper format and computes the area
        p1, p2, p3 = process_coord(p1, p2, p3)
        tri_area = compute(p1, p2, p3)

        # Updates the total area
        total_area += tri_area

        temp = []
        for i in range(0,3):
            temp.append(min([p1[i], p2[i], p3[i]]))
        for i in range(0,3):
            temp.append(max([p1[i], p2[i], p3[i]]))

        if triangle == start:
            min_max = temp
        else:
            for i in range(0,3):
                if temp[i] < min_max[i]:
                    min_max[i] = temp[i]
            for i in range(3,6):
                if temp[i] > min_max[i]:
                    min_max[i] = temp[i]

    return_coord[index] = min_max
    return_tot[index] = total_area

# Converts the raw input into properly formatted values
def process_coord(p1, p2, p3):
    p1 = convert_values(p1)
    p2 = convert_values(p2)
    p3 = convert_values(p3)
    return p1, p2, p3

# Helper method to convert the values for a single point
def convert_values(point):
    return [struct.unpack('f', point[0])[0],
            struct.unpack('f', point[1])[0],
            struct.unpack('f', point[2])[0]]

# Computes the surface area of a triangle
def compute(p1, p2, p3):
    a = math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2)
    b = math.sqrt((p3[0] - p1[0]) ** 2 + (p3[1] - p1[1]) ** 2 + (p3[2] - p1[2]) ** 2)
    c = math.sqrt((p3[0] - p2[0]) ** 2 + (p3[1] - p2[1]) ** 2 + (p3[2] - p2[2]) ** 2)
    p = (a + b + c) / 2
    area = math.sqrt(p * (p - a) * (p - b) * (p - c))
    return area

def find_box(min_max1, min_max2, min_max3, min_max4):

    min_max = []
    min_max = min_max1

    for i in range(0,3):
        if min_max2[i] < min_max[i]:
            min_max[i] = min_max2[i]
    for i in range(3,6):
        if min_max2[i] > min_max[i]:
            min_max[i] = min_max2[i]
    for i in range(0,3):
        if min_max3[i] < min_max[i]:
            min_max[i] = min_max3[i]
    for i in range(3,6):
        if min_max3[i] > min_max[i]:
            min_max[i] = min_max3[i]
    for i in range(0,3):
        if min_max4[i] < min_max[i]:
            min_max[i] = min_max4[i]
    for i in range(3,6):
        if min_max4[i] > min_max[i]:
            min_max[i] = min_max4[i]
    
    
    line1 = math.sqrt((min_max[3] - min_max[0]) ** 2)
    line2 = math.sqrt((min_max[4] - min_max[1]) ** 2)
    line3 = math.sqrt((min_max[5] - min_max[2]) ** 2)
    #min_max is xyz min then max
    box = "%f by %f by %f" % (line1, line2, line3)
    return box

# Prints the output
def show_output(triangles, total_area, min_box, total_time):
    print('Number of triangles: %d' % triangles)
    print('Total surface area: %f mm^2' % total_area)
    print('Minimum box dimensions: %s' % min_box)
    print('Total time: %f s' % total_time)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise ValueError('Too few arguments. Please enter the file name.')
    filename = str(sys.argv[1])
    triangles, total_area, min_box, total_time = read_csv(filename)
    show_output(triangles, total_area, min_box, total_time)
