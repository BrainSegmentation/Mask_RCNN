import sys, os
import glob
from PIL import Image, ImageChops

# Generates boxes which, together, partition the image into ~k**2 parts
def get_partition_boxes(img, k):
    img_width, img_height = img.size
    step_width, step_height = img_width // k, img_height // k

    bounding_boxes = []
    for i in range(0, img_width, step_width):
        for j in range(0, img_height, step_height):
            box = (i, j, i + step_width, j + step_height)
            bounding_boxes.append(box)
    return bounding_boxes

def get_partition_boxes_size(img, size):
    width, height = img.size

    bounding_boxes = []
    for i in range(0, width, size):
        for j in range(0, height, size):
            box = (i, j, i + size, j + size)
            bounding_boxes.append(box)
    return bounding_boxes

def get_overlapping_boxes_size(img, size, overlap):
    if overlap > size:
        exit
    width, height = img.size

    bounding_boxes = []
    for i in range(0, width, size - overlap):
        for j in range(0, height, size - overlap):
            box = (i, j, i + size, j + size)
            bounding_boxex.append(box)
    return bounding_boxes

# Partitions an image
def crop(image_path, k):
    img = Image.open(image_path)
    for box in get_partition_boxes(img, k):
        yield img.crop(box)


def cropToBox(image_path, box):
    img = Image.open(image_path)
    return img.crop(box)


def mkdir(dir):
    try:
        os.makedirs(dir)
    except FileExistsError:
        pass


# Takes partition (Image), path, section number, and file name
def save_partition(img, out_path, name):
    copy = Image.new('RGB', img.size, 255)
    copy.paste(img)         
    path = os.path.join(out_path, name)
    mkdir(out_path)
    copy.save(path)
    

def is_dense(img):
    colors = img.getcolors()
    if len(colors) < 2 or colors[1][0] * 4 < colors[0][0]:
        return False
    else:
        return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Image partitioner')

    parser.add_argument('image',
                        metavar='/path/to/image/')
    parser.add_argument('masks',
                        metavar='/path/to/masks/')
    parser.add-argument('--out', required=False,
                        default='./partitions/',
                        metavar='output directory')
    parser.add-argument('--size', required=False,
                        default=512,
                        metavar='partitioned tile size (px)')
    parser.add_argument('--overlap', required=False,
                        default=0,
                        metavar='partition overlap size (px)')
    args = parser.parse_args()

    image_path = args.image
    mask_path = args.masks

    out_path = args.out
    size = args.size
    overlap = args.overlap

    # Hard Coded (but unused)
    k = 9                           # sqrt of # of partitions

    # Get locations of all mask files
    mask_paths = glob.glob(mask_path + '*.png')
    mask_paths.extend(glob.glob(mask_path + '*.bmp'))
    print('Found {} masks'.format(len(mask_paths)))

    # Generate cropping bounding boxes
    img = Image.open(image_path)
    bounding_boxes = get_partition_boxes_size(img, size)

    # Crop all images according to each bounding box
    counter = 0
    print('Partitioning Image(s) into {} parts'.format(len(bounding_boxes)))
    for i, box in enumerate(bounding_boxes):
        sub_counter = 0;
        # Make paths for current partition
        section_str = 'section-{}'.format(i)
        section_path = os.path.join(out_path, section_str)
        images_path = os.path.join(section_path, 'images')
        masks_path = os.path.join(section_path, 'masks')
        
        cumulative = None
        save_buffer = []
        for j, mask in enumerate(mask_paths):
            mask_sub = cropToBox(mask, box)
            name = section_str + '-mask-{}.png'.format(j)
            save_buffer.append((mask_sub, name))
            # ANDs buffers together into a cumulative image
            if cumulative == None:
                cumulative = Image.new('1', mask_sub.size)
            cumulative = ImageChops.lighter(cumulative, mask_sub)
        
        print(cumulative.getcolors())
        cumulative.save("test{}.png".format(i))
        if is_dense(cumulative):
            for image in save_buffer:
                save_partition(image[0], masks_path, image[1])  # saves to masks/
                counter += 1
                sub_counter += 1
            name = section_str + '.png'
            wafer_sub = cropToBox(image_path, box)
            save_partition(wafer_sub, images_path, name) # saves to images/
            counter += 1        
            sub_counter += 1
             
        print('Wrote {0} images to {1}'.format(sub_counter, section_path))
        sub_counter = 0

    print('Saved {0} images to {1}'.format(counter, out_path))


if __name__ == '__main__':
    main()
