import os
import argparse
import pickle
import numpy as np
from scipy import misc
import cv2

import pycocotools.mask as mask_util

import datasets.dummy_datasets as dummy_datasets
import utils.vis as vis_utils
import utils_ade20k.misc as ade20k_utils


def vis(im_name, im, cls_boxes, cls_segms, cls_keyps):
    dummy_coco_dataset = dummy_datasets.get_coco_dataset()
    out_dir = None

    loaded = vis_utils.vis_one_image_opencv(im, cls_boxes, segms=cls_segms, keypoints=cls_keyps, thresh=0.9, kp_thresh=2,
        show_box=False, dataset=None, show_class=False)
    misc.imsave("loaded.png", loaded)

def create_panoptic_segmentation(cls_boxes, cls_segms, cls_keyps):
    boxes, segms, keypoints, classes = vis_utils.convert_from_cls_format(cls_boxes, cls_segms, cls_keyps)
    dataset = dummy_datasets.get_coco_dataset()

    # Display in largest to smallest order to reduce occlusion
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    sorted_inds = np.argsort(-areas)

    segm_out = np.zeros(im.shape[:2], dtype="uint8")
    inst_out = np.zeros(im.shape[:2], dtype="uint8")

    masks = mask_util.decode(segms)
    cnt = 1
    for i in sorted_inds:
        mask = masks[...,i]
        mask = np.nonzero(mask)
        class_name = dataset.classes[classes[i]]
        idx = ade20k_utils.category_to_idx(class_name)

        segm_out[mask] = idx
        inst_out[mask] = cnt
        cnt += 1

    misc.imsave("test.png", segm_out)
    out = np.stack([segm_out, inst_out], axis=-1)
    return out


def process(pkl_path, out_path):
    cls_boxes, cls_segms, cls_keyps = pickle.load(open(pkl_path, 'rb'))
    out = create_panoptic_segmentation(cls_boxes, cls_segms, cls_keyps)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--project', type=str, required=True, help="Project name")
    args = parser.parse_args()

    config = ade20k_utils.get_config(args.project)
    out_dir = os.path.join(config["predictions"], "maskrcnn")
    pkl_dir = os.path.join(out_dir, "pkl")
    panseg_dir = os.path.join(out_dir, "panseg")

    im_list = [line.rstrip() for line in open(config["im_list"], 'r')]

    for i, im_name in enumerate(im_list):
        img_basename = os.path.splitext(im_name)[0]
        pkl_path = os.path.join(pkl_dir, img_basename + '.pkl')
        panseg_path = os.path.join(panseg_dir, img_basename + '.png')


        print('Processing {}, {} -> {}'.format(i, pkl_path, panseg_path))
        process(pkl_path, panseg_path)


if __name__ == '__main__':
    main()