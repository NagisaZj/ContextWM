from torch.utils.data import Dataset

from PIL import Image
import os
import os.path
import numpy as np

from .utils import VideoRecord


# NOTE: you can manually select videos with specific labels for training here, by default we use all videos
maunally_selected_labels = {
    "93": "Pushing something from left to right",
    "94": "Pushing something from right to left",
}


class SomethingV2(Dataset):
    def __init__(self, root_path, list_file, segment_len=50, image_tmpl='{:06d}.jpg', manual_labels=False):
        self.root_path = root_path
        self.list_file = list_file
        self.segment_len = segment_len
        self.image_tmpl = image_tmpl

        self._parse_list(self.segment_len, maunally_selected_labels if manual_labels else None)

    def _parse_list(self, minlen, selected_labels=None):
        # check the frame number is large >segment_len:
        # usually it is [video_id, num_frames, class_idx]
        tmp = [x.strip().split(' ') for x in open(self.list_file)]
        tmp = [item for item in tmp if int(item[1]) >= minlen and (
            (selected_labels is None) or (item[2] in selected_labels.keys()))]
        self.video_list = [VideoRecord(item) for item in tmp]
        print('video number:%d' % (len(self.video_list)))

    @property
    def total_steps(self):
        return sum([record.num_frames for record in self.video_list])

    def _load_image(self, directory, idx):
        # TODO: cache
        image = Image.open(os.path.join(self.root_path, directory, self.image_tmpl.format(idx))).convert('RGB')
        return np.array(image)

    def _sample_index(self, record):
        return np.random.randint(1, record.num_frames - self.segment_len + 2)

    def get(self, record, ind):
        images = []
        p = ind
        for i in range(self.segment_len):
            seg_imgs = self._load_image(record.path, p)
            images.append(seg_imgs)
            if p < record.num_frames:
                p += 1
        # images = self.transform(images)
        return np.array(images)

    def __getitem__(self, index):
        record = self.video_list[index]
        # check this is a legit video folder
        while not os.path.exists(os.path.join(self.root_path, record.path, self.image_tmpl.format(1))):
            print(os.path.join(self.root_path, record.path, self.image_tmpl.format(1)))
            index = np.random.randint(len(self.video_list))
            record = self.video_list[index]

        segment_index = self._sample_index(record)
        segment = self.get(record, segment_index)
        return segment

    def __len__(self):
        return len(self.video_list)
