import sys, os
import Image

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
        pass
        
def main():
    ''' Tiles an image into a k*k grid of seperate images
    Takes in_path, out_path, k (num of partitions is k^2) 
    '''
    if len(sys.argv) > 4 or len(sys.argv) < 2:
        print('Usage: partition.py <in_path> <out_path> <k>, out and k optional')
        sys.exit()
    # Defaults 
    in_path = './' + sys.argv[1]
    out_path = './sub_images/'
    k = 9
    # User Input
    if len(sys.argv) == 3:
        out_path = sys.argv[2]
    if len(sys.argv) == 4:
        out_path = sys.argv[3]
        k = int(sys.argv[4])

    try: 
        print('Partitioning Image')
        for i, sub_img in enumerate(crop(in_path, k)):
            height, width = sub_img.size
            img = Image.new('L', (height, width), 255)
            img.paste(sub_img)
            path = os.path.join(out_path, str(i), '/images/', 'sub-{}.png'.format(i))
            mkdir(out_path.join(str(i), '/images/'))
            img.save(path)
        print('Saved {0} images to {1}'.format(k*k, out_path))
    except ValueError:
        print('Likely bad path')

    try: 
        print('Partitioning Masks')
        for f in next(os.walk(mask_dir))[2]:
            for i, sub_img in enumerate(crop(os.path.join(mask_dir, f), k)):
                height, width = sub_img.size
                img = Image.new('L', (height, width), 255)
                img.paste(sub_img)
                path = os.path.join(out_path, str(i), '/images/', 'sub-{}.png'.format(i))
                mkdir(out_path.join(str(i), '/images/'))
                img.save(path)
        print('Saved {0} images to {1}'.format(k*k, out_path))
    except ValueError:
        print('Likely bad path')

if __name__ == '__main__':
    main()
