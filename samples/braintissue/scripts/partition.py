import sys, os
from PIL import Image


def getPartitionBoxes(img, k):
    img_width, img_height = img.size
    step_width, step_height = img_width // k, img_height // k

    for i in range(0, img_width, step_width):
        for j in range(0, img_height, step_height):
            box = (i, j, i + step_width, j + step_height)
            yield img.crop(box)


def crop(in_path, k):
    img = Image.open(in_path)
    for box in getPartitionBoxes(img, k):
        yield img.crop(box)


def cropToBox(in_path, box)
    img = Image.open(in_path)
    return img.crop(box)


def mkdir(dir):
    try:
        os.makedirs(dir)
    except FileExistsError:
        pass


# Takes partition (Image), path, section number, and file name
def save_partition(img, out_path, i, name):
    height, width = partitions[0].size
    img = Image.new('RGB', (height, width), 255)
    img.paste(partitions[0])
    curr_out_path = out_path + 'section-{}/'.format(i)
    path = os.path.join(curr_out_path, name)
    mkdir(curr_out_path)
    img.save(path)
    

# Takes in_path, out_path, k (num of partitions is k**2)
def main():
    usage = 'Usage: partition.py <in_path> <mask_path> <out_path> <k>, out and k optional'
    if len(sys.argv) > 4 or len(sys.argv) < 2:
        print(usage)
        sys.exit()
    # Defaults 
    in_path = './' + sys.argv[1]
    mask_path = './' + sys.argv[2]
    out_path = './partitions/'
    k = 9
    # User Input
    if len(sys.argv) == 4:
        out_path = sys.argv[3]
    if len(sys.argv) == 5:
        out_path = sys.argv[3]
        k = int(sys.argv[4])

    # Get locations of all mask files
    mask_paths = []
    print('Making a ton of dirs...')
    for file in os.listdir(mask_path):
        filename = os.fsdecode(file)
        if filename.endswith(".png") or filename.endswith(".bmp"):
            mask_paths.append(os.path.join(mask_path, filename))
        else:
            continue

    # Partition all images appropriately
    # -- Get appropriate bounding boxes (each mask is identically sized, as is
    # the original image)
    img = Image.open(in_path)
    bounding_boxes = getPartitionBoxes(img, k)

    # Crop all images according to each bounding box
    counter = 0
    print('Partitioning Image(s)')
    for i, box in enumerate(bounding_boxes):
        wafer_sub = cropToBox(in_path, box)
        name = 'wafer-sub-{}.png'.format(i)
        save_partition(partitions[0], out_path, i, name)
        counter += 1        
        for mask in mask_paths:
            sub = cropToBox(mask, box)
            name = 'sub-{0}-{1}.png'.format(i, j)
            save_partition(sub_img, out_path, i, name)
            counter += 1 

    print('Saved {0} images to {1}'.format(counter, out_path))


if __name__ == '__main__':
    main()
