from struct import calcsize, pack, unpack, unpack_from
from datetime import datetime
from collections import namedtuple
from os import getcwd, path
from tkinter import Tk
from tkinter.filedialog import askopenfile


def openfilecheck(open_mode, file_name="", file_ext="", file_type=""):
    """
    :param open_mode: {str} method to open the file (e.g., 'rb' for binary read only)
    :param file_name: [optional] {str} full path of file to open
    :param file_ext:  [optional] {str} file extension (e.g., '.nev')
    :param file_type: [optional] {str} file type for use when browsing for file (e.g., 'Blackrock NEV Files')
    :return: {file} opened file
    """

    while True:
        if not file_name:
            if not file_ext:
                file_type = "All Files"

            Tk().withdraw()
            file_name = askopenfile(
                title="Select original file",
                initialdir=getcwd(),
                filetypes=[("NSx Files", ("*.ns1", "*.ns2", "*.ns3", "*.ns4", "*.ns5", "*.ns6"))],
                )
            file_name = file_name.name

        # Ensure file exists (really needed for users type entering)
        if path.isfile(file_name):
            # Ensure given file matches file_ext
            if file_ext:
                _, fext = path.splitext(file_name)

                # check for * in extension
                if file_ext[-1] == "*":
                    test_extension = file_ext[:-1]
                else:
                    test_extension = file_ext

                if fext[0 : len(test_extension)] != test_extension:
                    file_name = ""
                    print(
                        "\n*** File given is not a "
                        + file_ext
                        + " file, try again ***\n"
                    )
                    continue
            break
        else:
            file_name = ""
            print("\n*** File given does exist, try again ***\n")

    print("\n" + file_name.split("/")[-1] + " opened")
    return open(file_name, open_mode)


FieldDef = namedtuple("FieldDef", ["name", "formatStr", "formatFnc"])


def processheaders(curr_file, packet_fields):
    """
    :param curr_file:      {file} the current BR datafile to be processed
    :param packet_fields : {named tuple} the specific binary fields for the given header
    :return:               a fully unpacked and formatted tuple set of header information

    Read a packet from a binary data file and return a list of fields
    The amount and format of data read will be specified by the
    packet_fields container
    """

    # This is a lot in one line.  First I pull out all the format strings from
    # the basic_header_fields named tuple, then concatenate them into a string
    # with '<' at the front (for little endian format)
    packet_format_str = "<" + "".join([fmt for name, fmt, fun in packet_fields])

    # Calculate how many bytes to read based on the format strings of the header fields
    bytes_in_packet = calcsize(packet_format_str)
    packet_binary = curr_file.read(bytes_in_packet)

    # unpack the binary data from the header based on the format strings of each field.
    # This returns a list of data, but it's not always correctly formatted (eg, FileSpec
    # is read as ints 2 and 3, but I want it as '2.3'
    packet_unpacked = unpack(packet_format_str, packet_binary)

    # Create an iterator from the data list.  This allows a formatting function
    # to use more than one item from the list if needed, and the next formatting
    # function can pick up on the correct item in the list
    data_iter = iter(packet_unpacked)

    # create an empty dictionary from the name field of the packet_fields.
    # The loop below will fill in the values with formatted data by calling
    # each field's formatting function
    packet_formatted = dict.fromkeys([name for name, fmt, fun in packet_fields])
    for name, fmt, fun in packet_fields:
        packet_formatted[name] = fun(data_iter)

    return packet_formatted


NO_FILTER = 0
BUTTER_FILTER = 1
STRING_TERMINUS = "\x00"


def format_filespec(header_list):
    return str(next(header_list)) + "." + str(next(header_list))  # eg 2.3


def format_timeorigin(header_list):
    year = next(header_list)
    month = next(header_list)
    _ = next(header_list)
    day = next(header_list)
    hour = next(header_list)
    minute = next(header_list)
    second = next(header_list)
    millisecond = next(header_list)
    # return datetime(year, month, day, hour)
    return datetime(year, month, day, hour, minute, second, millisecond * 1000)


def format_stripstring(header_list):
    string = bytes.decode(next(header_list), "latin-1")
    return string.split(STRING_TERMINUS, 1)[0]


def format_none(header_list):
    return next(header_list)


def format_freq(header_list):
    return str(float(next(header_list)) / 1000) + " Hz"


def format_filter(header_list):
    filter_type = next(header_list)
    if filter_type == NO_FILTER:
        return "none"
    elif filter_type == BUTTER_FILTER:
        return "butterworth"


nsx_header_dict = {
    "basic_21": [
        FieldDef("Label", "16s", format_stripstring),  # 16 bytes  - 16 char array
        FieldDef("Period", "I", format_none),  # 4 bytes   - uint32
        FieldDef("ChannelCount", "I", format_none),
    ],  # 4 bytes   - uint32
    "basic": [
        FieldDef("FileType", "8s", format_none),  # 2 bytes   - 2 unsigned char
        FieldDef("FileSpec", "2B", format_filespec),
        FieldDef("BytesInHeader", "I", format_none),  # 4 bytes   - uint32
        FieldDef("Label", "16s", format_stripstring),  # 16 bytes  - 16 char array
        FieldDef("Comment", "256s", format_stripstring),  # 256 bytes - 256 char array
        FieldDef("Period", "I", format_none),  # 4 bytes   - uint32
        FieldDef("TimeStampResolution", "I", format_none),  # 4 bytes   - uint32
        FieldDef("TimeOrigin", "8H", format_timeorigin),  # 16 bytes  - 8 uint16
        FieldDef("ChannelCount", "I", format_none),
    ],  # 4 bytes   - uint32
    "extended": [
        FieldDef("Type", "2s", format_stripstring),  # 2 bytes   - 2 char array
        FieldDef("ElectrodeID", "H", format_none),  # 2 bytes   - uint16
        FieldDef(
            "ElectrodeLabel", "16s", format_stripstring
        ),  # 16 bytes  - 16 char array
        FieldDef("PhysicalConnector", "B", format_none),  # 1 byte    - uint8
        FieldDef("ConnectorPin", "B", format_none),  # 1 byte    - uint8
        FieldDef("MinDigitalValue", "h", format_none),  # 2 bytes   - int16
        FieldDef("MaxDigitalValue", "h", format_none),  # 2 bytes   - int16
        FieldDef("MinAnalogValue", "h", format_none),  # 2 bytes   - int16
        FieldDef("MaxAnalogValue", "h", format_none),  # 2 bytes   - int16
        FieldDef("Units", "16s", format_stripstring),  # 16 bytes  - 16 char array
        FieldDef("HighFreqCorner", "I", format_freq),  # 4 bytes   - uint32
        FieldDef("HighFreqOrder", "I", format_none),  # 4 bytes   - uint32
        FieldDef("HighFreqType", "H", format_filter),  # 2 bytes   - uint16
        FieldDef("LowFreqCorner", "I", format_freq),  # 4 bytes   - uint32
        FieldDef("LowFreqOrder", "I", format_none),  # 4 bytes   - uint32
        FieldDef("LowFreqType", "H", format_filter),
    ],  # 2 bytes   - uint16
    "data": [
        FieldDef("Header", "B", format_none),  # 1 byte    - uint8
        FieldDef("Timestamp", "I", format_none),  # 4 bytes   - uint32
        FieldDef("NumDataPoints", "I", format_none),
    ],  # 4 bytes   - uint32]
}
