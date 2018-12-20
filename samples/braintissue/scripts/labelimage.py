"""
Takes an image path, as well as its corresponding magnet and tissue text files,
and constructs a labelme-compatible json file.

Example calls:
python labelimage.py magnets.txt tissues.txt image.tif
python labelimage.py magnets.txt tissues.txt image.tif -j labels.json -s 3
"""

# Splits list into list of ordered pairs. For example:
# [1, 2, 3, 4] => [[1, 2], [3, 4]]
def to_pairs(l):
    """Yield successive pairs from l"""
    for i in range(0, len(l), 2):
        yield l[i:i + 2]

def main():
    ###################
    # Parsing arguments
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=RawTextHelpFormatter)

    parser.add_argument('m', help='the magnet text file')
    parser.add_argument('t', help='the tissue text file')
    parser.add_argument('i', help='the image file (default = \'labels.json\' in current directory)')
    parser.add_argument('-j', '--json', help='output json file (default = \'labels.json\' in current directory)', default='labels.json')
    parser.add_argument('-s', '--scale', help='scale the image is downsized (default = 3)', default=3)

    args = vars(parser.parse_args())

    magnetPath = os.path.normpath(args['m'])
    tissuePath = os.path.normpath(args['t'])
    imagePath = os.path.normpath(args['i'])
    jsonPath = os.path.normpath(args['json'])
    scale = int(args['scale'])

    # Load text files
    magnet = pd.read_csv(magnetPath, sep="\t|,", header=None,\
                         engine='python') // scale
    tissue = pd.read_csv(tissuePath, sep="\t|,", header=None,\
                         engine='python') // scale
    magnet = magnet.values.tolist()
    tissue = tissue.values.tolist()

    # generate json file
    data = {}
    data["imagePath"] = imagePath
    data["shapes"] = []

    for i in range(len(magnet)):
        shape = {}
        shape["line_color"] = None
        shape["points"] = list(to_pairs(magnet[i]))
        shape["fill_color"] = None
        shape["label"] = "magnet-" + str(i + 1)
        data["shapes"].append(shape)

    for i in range(len(tissue)):
        shape = {}
        shape["line_color"] = None
        shape["points"] = list(to_pairs(tissue[i]))
        shape["fill_color"] = None
        shape["label"] = "tissue-" + str(i + 1)
        data["shapes"].append(shape)

    data["imageData"] = None
    data["lineColor"] = [0, 255, 0, 128]
    data["fillColor"] = [255, 0, 0, 128]

    with open(jsonPath, "w+") as outfile:
        outfile.write(json.dumps(data, indent=4))

if __name__ == "__main__":
    main()
