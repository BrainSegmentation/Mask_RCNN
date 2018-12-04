import sys, os
from PIL import Image

def crop(in_path, k):
    img = Image.open(in_path)
    img_width, img_height = img.size
    step_width, step_height = img_width // k, img_height // k
    
    for i in range(0, img_width, step_width):
        for j in range(0, img_height, step_height):
            box = (i, j, i + step_width, j + step_height)
            yield img.crop(box)

def mkdir(dir):
    try:
        os.makedirs(dir)
    except FileExistsError:
        ...

def main():
    ''' Takes in_path, out_path, k (num of partitions is k**2) '''
    if len(sys.argv) > 4 or len(sys.argv) < 2:
        print('Usage: partition.py <in_path> <mask_path> <out_path> <k>, out and k optional')
        sys.exit()
    # Defaults 
    in_path = './' + sys.argv[1]
    mask_path = './' + sys.argv[2]
    out_path = './results/'
    k = 9
    # User Input
    if len(sys.argv) == 4:
        out_path = sys.argv[3]
    if len(sys.argv) == 5:
        out_path = sys.argv[3]
        k = int(sys.argv[4])

#   try: 
    mask_paths = []
    print('Making a ton of dirs and files, prepare your ass...')
    for file in os.listdir(mask_path):
        filename = os.fsdecode(file)
        if filename.endswith(".png") or filename.endswith(".bmp"):
            mask_paths.append(os.path.join(mask_path, filename))
        else:
            continue
    counter = 0 
    print('Partitioning Image(s)')
    for i, partitions in enumerate(zip(crop(in_path, k), [crop(path, k) for path in mask_paths])):
        height, width = partitions[0].size
        print(height, width)
        for j, sub_img in enumerate(partitions):
            img = Image.new('RGB', (height, width), 255)
            img.paste(sub_img)
            curr_out_path = out_path + 'section-{}/'.format(i)
            if j == 0:
                path = os.path.join(curr_out_path, 'man-{}.png'.format(i))
            else:
                path = os.path.join(curr_out_path, 'sub-{}.png'.format(i))
            mkdir(curr_out_path)
            img.save(path)
            counter += 1 
        
    print('Saved {0} images to {1}'.format(counter, out_path))
#   except ValueError:
#       print('Likely bad path')

if __name__ == '__main__':
    main()
