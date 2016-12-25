from collections import namedtuple

boot = namedtuple("boot_record", [
    "oem", "bytePsect", "sectPclus", "reserved", "hidden_sector", "total_sector", "FAT_size", "root_directory_clus",
    "boot_record_backup"
])

directory = namedtuple("dir_entry", ["name", "attr", "cluster", "filesize", "removed"])


def myread(string, start_index, read_bytes):
    return string[start_index:start_index + read_bytes]


def b2h(data):
    ret = 0
    for ch in data[::-1]:
        ret = ret << 8
        if type(ch) != str:
            ret += ch
        else:
            ret += ord(ch)
    return ret


def read_boot(fp):
    fp.seek(0)
    data = fp.read(512)

    oemname = myread(data, 0x03, 8)
    bytes_per_sector = b2h(myread(data, 0X0B, 2))
    sector_per_cluster = b2h(myread(data, 0X0D, 1))
    reserved_sector_count = b2h(myread(data, 0x0E, 2))
    hidden_sector = b2h(myread(data, 0x1C, 4))
    total_sector = b2h(myread(data, 0x20, 4))
    fat_size = b2h(myread(data, 0x24, 4))
    root_directory_cluster = b2h(myread(data, 0x2C, 4))
    boot_record_backup_sector = b2h(myread(data, 0x32, 2))

    return boot(oemname, bytes_per_sector, sector_per_cluster, reserved_sector_count, hidden_sector, total_sector,
                fat_size, root_directory_cluster, boot_record_backup_sector)


def SFNs(data):
    removed = False

    flag = myread(data, 0x00, 1)
    if flag == b'\xE5':
        removed = True
    elif flag == b'\x00':
        return None

    name = myread(data, 0x00, 8)  # read name
    for ch in name[::-1]:  # remove space
        if ch != b'\x20':
            break
        name = name[:-1]

    temp = myread(data, 0x08, 3)  # read extend
    for ch in temp[::-1]:
        if ch != b'\x20':
            name += '.' + temp
            break
        temp = temp[:-1]

    if removed:
        name = "[Deleted] " + name[1:]
    attr = myread(data, 0x0B, 1)
    cluster = b2h(myread(data, 0x14, 2))
    cluster = cluster << 8
    cluster += b2h(myread(data, 0x1A, 2))
    filesize = b2h(myread(data, 0x1C, 4))

    return directory(name, attr, cluster, filesize, removed)


def LFNs(fp):
    lname = ""
    removed = False

    while True:
        data = fp.read(32)
        lname = myread(data, 0x01, 10).decode("utf-16") + myread(data, 0x0E, 12).decode("utf-16") + myread(
            data, 0x1C, 4).decode("utf-16") + lname

        if ord(data[0]) & 0xbf == 0x01:
            break

        if data[0] == b'\xE5':  # if this LFNs is deleted
            removed = True
            break

    if removed:
        while True:
            data = fp.read(32)
            data = SFNs(data)
            if data.attr != '\x0f':
                return data

    for ch in lname[::-1]:
        if ch != u'\uffff':
            break
        lname = lname[:-1]

    ret = SFNs(fp.read(32))
    ret = ret._replace(name=lname)
    return ret


def read_directory_entry(fp):
    data = fp.read(32)
    data = SFNs(data)
    if data == None:
        return None

    if data.attr == b'\x0f':
        fp.seek(-32, 1)
        return LFNs(fp)
    else:
        return data
