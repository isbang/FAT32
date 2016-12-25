#!/usr/bin/env python

import sys
from read_func import *
import time

boot_data = boot(None, None, None, None, None, None, None, None, None)
cluster_size = 0
root_entry = 0
cluster_check = []


def printboot(data):
    print("oem name : %s" % data.oem.decode("utf-8"))
    print("byte per sector : %d bytes" % data.bytePsect)
    print("sector per cluster : %d" % data.sectPclus)
    print("reserved sector count : %d" % data.reserved)
    print("hidden sectors : %d" % data.hidden_sector)
    print("total sectors : %d" % data.total_sector)
    print("fat size : %d" % data.FAT_size)
    print("root directory cluster : %d" % data.root_directory_clus)
    print("boot record backup : %d sector\n" % data.boot_record_backup)


def EOCluster(location):
    global cluster_size
    global root_entry

    location -= root_entry
    location = location % cluster_size
    return not location


def FATABLE_LINK(cur_cluster, fp):
    global boot_data
    temp = fp.tell()

    FAT_ENTRY = boot_data.bytePsect * boot_data.reserved
    fp.seek(FAT_ENTRY, 0)
    fp.seek(cur_cluster * 4, 1)
    ret = b2h(fp.read(4))
    fp.seek(temp, 0)
    if ret == 0x0fffffff:
        return None
    else:
        return ret


def tree(fp):
    global root_entry
    global boot_data

    fp.seek(root_entry, 0)
    print("INDEX      NAME                                       [     FILESIZE     ]      ENTRY")
    print("=====================================================================================")
    rTree(0, boot_data.root_directory_clus, fp)


def rTree(indent, cluster, fp):
    global cluster_size
    global root_entry
    global cluster_check

    if cluster < 2:
        return

    cluster_check.append(cluster)
    fp.seek(root_entry + cluster_size * (cluster - 2), 0)

    while True:
        dir_data = read_directory_entry(fp)
        if dir_data != None:
            print_str = "0x%08X " % (fp.tell() - 32)
            print_str += "%s" % (indent * ' |  ')
            print_str += "%s" % dir_data.name
            print_str += ' ' * (54 - len(print_str))
            print_str += "[%12d bytes] " % dir_data.filesize
            print_str += "0x%08X" % (root_entry + cluster_size * (dir_data.cluster - 2))
            print(print_str)

            if ord(dir_data.attr) & 0x10 and dir_data.cluster not in cluster_check:
                temp = fp.tell()
                rTree(indent + 1, dir_data.cluster, fp)
                fp.seek(temp, 0)

        if EOCluster(fp.tell()):
            if FATABLE_LINK(cluster, fp) != None:
                temp = fp.tell()
                rTree(indent, FATABLE_LINK(cluster, fp), fp)
                fp.seek(temp)
            break


def main(path):
    global boot_data
    global cluster_size
    global root_entry

    f = open(path, 'rb')
    boot_data = read_boot(f)
    cluster_size = boot_data.bytePsect * boot_data.sectPclus
    root_entry = (boot_data.bytePsect * boot_data.reserved) + (2 * boot_data.bytePsect * boot_data.FAT_size)

    printboot(boot_data)

    tree(f)
    f.close()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("How to use : python %s [FAT_Image_File]" % sys.argv[0])
        exit(1)
    main(sys.argv[1])
